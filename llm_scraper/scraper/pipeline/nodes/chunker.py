from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.core.entities.state import PipelineState

default_chunker = DefaultHTMLCleaner()
semantic_chunker = SemanticChunker()


async def chunker_node(state: PipelineState) -> dict:
    cleaned_html = state["cleaned_html"]
    config = state["config"]

    # no chunking needed
    if len(cleaned_html) < config.context_length:
        return {"chunks": []}

    if config.use_markdown_conversion:
        # markdown is plain text, split by character windows with overlap
        chunks = _split_text_with_overlap(
            text=cleaned_html, chunk_size=config.context_length - 500, overlap=200
        )
    else:
        chunks = semantic_chunker.chunk(cleaned_html, config.context_length - 500)

    return {"chunks": chunks}


def _split_text_with_overlap(text: str, chunk_size: int, overlap: int) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks
