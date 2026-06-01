import logging

from scraper.adapters.html.hyde_scorer import HyDEScorer
from scraper.core.entities.state import PipelineState
from scraper.providers.embeddings.factory import get_embedding_provider
from scraper.providers.factory import get_provider

logger = logging.getLogger(__name__)


async def scorer_node(state: PipelineState) -> dict:
    chunks = state["chunks"]
    config = state["config"]

    logger.info(
        f"[scorer] scoring {len(chunks)} chunks with HyDE (domain={config.domain})"
    )

    hyde_provider = config.hyde_provider or config.provider
    scorer = HyDEScorer(
        llm=get_provider(hyde_provider),
        embedding_provider=get_embedding_provider(config.embedding),
        domain=config.domain,
    )
    ranked_chunks, _ = scorer.rank(
        query=state["query"],
        chunks=chunks,
        top_k=config.top_k_chunks,
    )

    logger.info(f"[scorer] reduced to {len(ranked_chunks)} chunks")
    return {"chunks": ranked_chunks}
