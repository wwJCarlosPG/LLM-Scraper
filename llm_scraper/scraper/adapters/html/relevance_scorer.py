import logging

from sentence_transformers import util

from scraper.core.ports.embedding_port import EmbeddingPort

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """
    Ranks chunks by semantic similarity against the user query
    using cosine similarity between embeddings.

    Only the top-k most relevant chunks are returned,
    reducing token usage and improving extraction accuracy
    on pages where relevant content is not in the first chunks.
    """

    def __init__(self, embedding_provider: EmbeddingPort):
        self.embedding_provider = embedding_provider

    def rank(self, query: str, chunks: list[str], top_k: int) -> list[str]:
        """
        Rank chunks by relevance to the query and return the top-k.

        Args:
            query: the user extraction query.
            chunks: list of text chunks to rank.
            top_k: number of chunks to return.

        Returns:
            top-k chunks sorted by relevance descending.
        """
        if len(chunks) <= top_k:
            logger.info(
                f"[scorer] {len(chunks)} chunks <= top_k {top_k}, skipping ranking"
            )
            return chunks

        logger.info(f"[scorer] ranking {len(chunks)} chunks, returning top {top_k}")

        query_embedding = self.embedding_provider.embed([query])[0]
        chunk_embeddings = self.embedding_provider.embed(chunks)

        scores = util.cos_sim(query_embedding, chunk_embeddings)[0]

        ranked = sorted(
            zip(scores.tolist(), chunks, strict=True), key=lambda x: x[0], reverse=True
        )

        top_chunks = [chunk for _, chunk in ranked[:top_k]]
        logger.info(f"[scorer] top scores: {[round(s, 3) for s, _ in ranked[:top_k]]}")

        return top_chunks
