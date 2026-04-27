from logging import getLogger

from langchain_text_splitters import (
    HTMLSemanticPreservingSplitter,
    RecursiveCharacterTextSplitter,
)

from scraper.core.consts import (
    DENYLIST_TAGS,
    ELEMENTS_TO_PRESERVE,
    HTML_HEADERS_TO_SPLIT_ON,
)

logger = getLogger(__name__)


class SemanticChunker:
    """
    Splits HTML into semantically meaningful chunks using LangChain's
    HTMLSemanticPreservingSplitter.

    Preserves tables, lists and other structured elements intact,
    never splitting them across chunks. Falls back to
    RecursiveCharacterTextSplitter if no semantic structure is found.
    """

    def chunk(self, html: str, chunk_size: int, overlap: int = 200) -> list[str]:
        splitter = HTMLSemanticPreservingSplitter(
            headers_to_split_on=HTML_HEADERS_TO_SPLIT_ON,
            max_chunk_size=chunk_size,
            elements_to_preserve=ELEMENTS_TO_PRESERVE,
            denylist_tags=DENYLIST_TAGS,
        )

        try:
            sections = splitter.split_text(html)
        except Exception:
            sections = []

        if not sections:
            logger.warning(
                "No semantic sections found, falling back to plain text splitting"
            )
            return self._split_plain(html, chunk_size, overlap)

        logger.info(f"Split into {len(sections)} semantic sections")

        chunks = [s.page_content.strip() for s in sections if s.page_content.strip()]
        return chunks if chunks else self._split_plain(html, chunk_size, overlap)

    def _split_plain(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap,
            length_function=len,
        )
        return splitter.split_text(text)
