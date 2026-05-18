import logging

from langchain_text_splitters import MarkdownTextSplitter

from scraper.adapters.html.relevance_scorer import RelevanceScorer
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.core.entities.state import PipelineState
from scraper.providers.embeddings.factory import get_embedding_provider

logger = logging.getLogger(__name__)

semantic_chunker = SemanticChunker()


async def chunker_node(state: PipelineState) -> dict:
    cleaned_html = state["cleaned_html"]
    config = state["config"]

    if len(cleaned_html) < config.context_length:
        logger.info("[chunker] content fits in context window, no chunking needed")
        return {"chunks": []}

    chunk_size = config.context_length - 500
    overlap = 200

    if config.use_markdown_conversion:
        chunks = _split_markdown(cleaned_html, chunk_size, overlap)
    else:
        chunks = semantic_chunker.chunk(cleaned_html, chunk_size, overlap)

    if len(chunks) > config.top_k_chunks:
        logger.info(
            "[chunker] more chunks than top_k_chunks, keeping only top_k_chunks"
        )
        scorer = RelevanceScorer(get_embedding_provider(config.embedding))
        chunks, _ = scorer.rank(
            query=state["query"], chunks=chunks, top_k=config.top_k_chunks
        )

    logger.info(f"[chunker] split into {len(chunks)} chunks")
    return {"chunks": chunks}


def _split_markdown(text: str, chunk_size: int, overlap: int) -> list[str]:
    splitter = MarkdownTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
    )
    return splitter.split_text(text)
