import logging

from sentence_transformers import util

from scraper.core.ports.embedding_port import EmbeddingPort
from scraper.core.ports.llm_port import LLMPort
from scraper.core.ports.scorer_port import ScorerPort
from scraper.pipeline.prompts.hyde import (
    build_hyde_user_prompt,
    get_hyde_system_prompt,
)

logger = logging.getLogger(__name__)


class HyDEScorer(ScorerPort):
    """
    Hypothetical Document Embeddings scorer (Gao et al., 2022).

    Replaces direct query embedding with the embedding of an LLM-generated
    hypothetical document. This bridges the semantic gap between task
    instruction queries and web content, improving chunk retrieval quality
    for small models.

    The encoder acts as a dense bottleneck that filters hallucinations
    from the hypothetical document, grounding the search vector to the
    actual chunk corpus.

    Reference: arxiv.org/abs/2212.10496
    """

    def __init__(
        self,
        llm: LLMPort,
        embedding_provider: EmbeddingPort,
        domain: str = "web",
    ):
        self.llm = llm
        self.embedding_provider = embedding_provider
        self.domain = domain
        self._cache: dict[str, list[float]] = {}

    def _get_hypothetical_embedding(self, query: str) -> list[float]:
        """
        Implements g(q, INST) → f(hypothetical_doc) from the HyDE paper.
        Result is cached per query to avoid redundant LLM calls
        within the same pipeline execution.
        """
        if query in self._cache:
            logger.info("[hyde] using cached hypothetical embedding")
            return self._cache[query]

        try:
            hypothetical_doc = self.llm.invoke(
                user_prompt=build_hyde_user_prompt(query, self.domain),
                system_prompt=get_hyde_system_prompt(),
            )
            logger.info(
                f"[hyde] hypothetical doc generated: {hypothetical_doc[:100]}..."
            )
        except Exception as e:
            logger.warning(
                f"[hyde] LLM generation failed ({e}), falling back to raw query"
            )
            hypothetical_doc = query

        embedding = self.embedding_provider.embed([hypothetical_doc])[0]
        self._cache[query] = embedding
        return embedding

    def rank(
        self,
        query: str,
        chunks: list[str],
        top_k: int,
        compute_scores: bool = False,
    ) -> tuple[list[str], list[float]]:
        if len(chunks) <= top_k:
            logger.info(
                f"[hyde] {len(chunks)} chunks <= top_k {top_k}, skipping ranking"
            )
            if compute_scores:
                query_emb = self._get_hypothetical_embedding(query)
                chunk_embs = self.embedding_provider.embed(chunks)
                scores = util.cos_sim(query_emb, chunk_embs)[0].tolist()
                ranked = sorted(
                    zip(scores, chunks, strict=True), key=lambda x: x[0], reverse=True
                )
                return [c for _, c in ranked], [round(s, 3) for s, _ in ranked]
            return chunks, [1.0] * len(chunks)

        logger.info(
            f"[hyde] ranking {len(chunks)} chunks with HyDE, "
            f"returning top {top_k} (domain={self.domain})"
        )

        query_emb = self._get_hypothetical_embedding(query)
        chunk_embs = self.embedding_provider.embed(chunks)
        scores = util.cos_sim(query_emb, chunk_embs)[0]

        ranked = sorted(
            zip(scores.tolist(), chunks, strict=True),
            key=lambda x: x[0],
            reverse=True,
        )

        top_scores = [round(s, 3) for s, _ in ranked[:top_k]]
        top_chunks = [c for _, c in ranked[:top_k]]

        logger.info(f"[hyde] top scores: {top_scores}")
        return top_chunks, top_scores
