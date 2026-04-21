from bs4 import BeautifulSoup

from scraper.core.consts import SEMANTIC_TAGS


class SemanticChunker:
    """
    Splits HTML into semantically meaningful chunks instead of arbitrary character windows.
    Prioritizes high-level semantic blocks to avoid splitting related content.
    """

    def chunk(self, html: str, chunk_size: int) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        blocks = self._extract_blocks(soup)
        return self._group_into_chunks(blocks, chunk_size)

    def _extract_blocks(self, soup: BeautifulSoup) -> list[str]:
        blocks = []
        for tag in SEMANTIC_TAGS:
            elements = soup.find_all(tag)
            for el in elements:
                blocks.append(str(el))

        # fallback: if no semantic tags found use direct children of body
        if not blocks:
            body = soup.body if soup.body else soup
            blocks = [str(el) for el in body.contents if str(el).strip()]

        return blocks

    def _group_into_chunks(self, blocks: list[str], chunk_size: int) -> list[str]:
        chunks = []
        current = ""

        for block in blocks:
            if len(current) + len(block) <= chunk_size:
                current += block
            else:
                if current:
                    chunks.append(current)
                # if a single block exceeds chunk_size, split it by characters
                if len(block) > chunk_size:
                    for i in range(0, len(block), chunk_size):
                        chunks.append(block[i : i + chunk_size])
                else:
                    current = block

        if current:
            chunks.append(current)

        return chunks
