from typing import Literal

import trafilatura
from markdownify import markdownify


class MarkdownConverter:
    """
    Converts HTML to Markdown before passing it to the LLM.
    Reduces token usage while preserving content semantics.

    - trafilatura: best for article/blog pages, extracts main content only.
    - markdownify: best for structured pages (e-commerce, listings).
    """

    def convert(
        self, html: str, strategy: Literal["trafilatura", "markdownify"] = "trafilatura"
    ) -> str:
        if strategy == "trafilatura":
            return self._use_trafilatura(html)
        return self._use_markdownify(html)

    def _use_trafilatura(self, html: str) -> str:
        result = trafilatura.extract(
            html,
            include_links=False,
            include_images=False,
            include_tables=True,
            no_fallback=False,
        )
        if result:
            return result
        # fallback if trafilatura returns nothing
        return self._use_markdownify(html)

    def _use_markdownify(self, html: str) -> str:
        return markdownify(html, strip=["script", "style", "meta", "link"])
