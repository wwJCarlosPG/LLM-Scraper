"""
Script to inspect semantic chunking behavior on real-world HTML pages.
Run with: poetry run python scripts/inspect_chunking.py
"""

import asyncio
from dataclasses import dataclass

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.pipeline.nodes.chunker import _split_markdown

URLS = {
    "news_article": "https://www.bbc.com/future/article/20260424-chernobyl-wildlife-forty-years-on",
    "ecommerce": "https://books.toscrape.com",
}

CHUNK_SIZE = 8000
OVERLAP = 200


@dataclass
class ChunkReport:
    url: str
    page_type: str
    original_length: int
    cleaned_length: int
    num_chunks: int
    chunk_sizes: list[int]
    previews: list[dict]


def inspect_chunks(
    chunks: list[str], url: str, page_type: str, original: str, cleaned: str
) -> ChunkReport:
    previews = []
    for i, chunk in enumerate(chunks):
        preview = {
            "index": i + 1,
            "size": len(chunk),
            "start": chunk[:200].replace("\n", " ").strip(),
            "end": chunk[-200:].replace("\n", " ").strip(),
        }
        # check overlap with next chunk
        if i < len(chunks) - 1:
            next_chunk = chunks[i + 1]
            overlap_content = chunk[-OVERLAP:].strip()
            # check if any 50-char substring of overlap appears in next chunk
            overlap_found = any(
                overlap_content[j : j + 50] in next_chunk
                for j in range(0, min(len(overlap_content), OVERLAP), 10)
                if len(overlap_content[j : j + 50]) == 50
            )
            preview["overlap_found_in_next"] = overlap_found
            preview["overlap_content"] = overlap_content[:100].replace("\n", " ")
        previews.append(preview)

    return ChunkReport(
        url=url,
        page_type=page_type,
        original_length=len(original),
        cleaned_length=len(cleaned),
        num_chunks=len(chunks),
        chunk_sizes=[len(c) for c in chunks],
        previews=previews,
    )


def print_report(report: ChunkReport):
    print(f"\n{'=' * 70}")
    print(f"Page type : {report.page_type}")
    print(f"URL       : {report.url}")
    print(f"Original  : {report.original_length:,} chars")
    print(f"Cleaned   : {report.cleaned_length:,} chars")
    print(f"Chunks    : {report.num_chunks}")
    print(f"Sizes     : {report.chunk_sizes}")
    print(f"{'─' * 70}")

    for preview in report.previews:
        print(f"\n  Chunk {preview['index']} ({preview['size']:,} chars)")
        print(f"  START : {preview['start'][:120]}...")
        print(f"  END   : ...{preview['end'][-120:]}")
        if "overlap_found_in_next" in preview:
            status = "✓" if preview["overlap_found_in_next"] else "✗"
            print(f"  OVERLAP {status} : {preview['overlap_content'][:80]}...")


async def main():
    cleaner = DefaultHTMLCleaner()
    semantic_chunker = SemanticChunker()
    markdown_converter = MarkdownConverter()

    for page_type, url in URLS.items():
        print(f"\nFetching {page_type}: {url}")
        try:
            html = cleaner.fetch(url)
        except Exception as e:
            print(f"  Failed to fetch: {e}")
            continue

        # ── Semantic chunking on cleaned HTML ──
        cleaned = cleaner.light_clean(html, context_length=CHUNK_SIZE)
        print("\n  ── Semantic version ──")
        if len(cleaned) < CHUNK_SIZE:
            print(
                f"  [semantic] content fits in one chunk ({len(cleaned):,} chars), no chunking needed."
            )
        else:
            chunks = semantic_chunker.chunk(cleaned, chunk_size=CHUNK_SIZE)
            report = inspect_chunks(chunks, url, page_type, html, cleaned)
            print_report(report)

        # ── Trafilatura markdown version ──
        print("\n  ── Markdown version (trafilatura) ──")
        markdown = markdown_converter.convert(html, strategy="trafilatura")
        if len(markdown) >= CHUNK_SIZE:
            md_chunks = _split_markdown(markdown, CHUNK_SIZE - 500, 200)
            md_report = inspect_chunks(
                md_chunks, url, f"{page_type}_markdown", html, markdown
            )
            print_report(md_report)
        else:
            print(
                f"  Trafilatura fits in one chunk ({len(markdown):,} chars), no chunking needed."
            )

        # ── Markdownify version ──
        print("\n  ── Markdown version (markdownify) ──")
        markdown_mf = markdown_converter.convert(html, strategy="markdownify")
        if len(markdown_mf) >= CHUNK_SIZE:
            mf_chunks = _split_markdown(markdown_mf, CHUNK_SIZE - 500, 200)
            mf_report = inspect_chunks(
                mf_chunks, url, f"{page_type}_markdownify", html, markdown_mf
            )
            print_report(mf_report)
        else:
            print(
                f"  Markdownify fits in one chunk ({len(markdown_mf):,} chars), no chunking needed."
            )


asyncio.run(main())
