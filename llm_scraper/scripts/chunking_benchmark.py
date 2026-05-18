"""
Chunking strategy benchmark across different page types.
Run with: poetry run python scripts/chunking_benchmark.py
"""

import json
import os
import statistics
from dataclasses import dataclass, field

from dotenv import load_dotenv
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.adapters.html.relevance_scorer import RelevanceScorer
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.core.entities.config import EmbeddingConfig
from scraper.providers.embeddings.factory import get_embedding_provider

load_dotenv()
FIXTURES_DIR = "tests/fixtures/pages"
CHUNK_SIZE = 8000
OVERLAP = 200
TOP_K = 3

NOISE_SIGNALS = [
    "navigation",
    "cookie",
    "subscribe",
    "newsletter",
    "follow us",
    "privacy policy",
    "terms of service",
    "sign in",
    "log in",
    "register",
    "advertisement",
]

DOMAIN_QUERIES = {
    "news": "Extract the main topic and key findings of the article.",
    "ecommerce": "Extract all product names and prices.",
    "documentation": "Extract the main concepts and code examples.",
    "unstructured": "Extract the main discussion topics and key points.",
}


@dataclass
class ChunkMetrics:
    strategy: str
    domain: str
    page: str
    num_chunks: int
    mean_size: float
    std_size: float
    min_size: int
    max_size: int
    total_chars: int
    top1_score: float
    noise_in_top_k: float
    chunks: list[str] = field(default_factory=list)


def detect_noise(chunk: str) -> bool:
    chunk_lower = chunk.lower()
    return any(signal in chunk_lower for signal in NOISE_SIGNALS)


def compute_metrics(
    strategy: str,
    domain: str,
    page: str,
    chunks: list[str],
    query: str,
    scorer: RelevanceScorer,
) -> ChunkMetrics:
    if not chunks:
        return ChunkMetrics(
            strategy=strategy,
            domain=domain,
            page=page,
            num_chunks=0,
            mean_size=0,
            std_size=0,
            min_size=0,
            max_size=0,
            total_chars=0,
            top1_score=0.0,
            noise_in_top_k=0.0,
        )

    sizes = [len(c) for c in chunks]
    top_k_chunks, top_k_scores = scorer.rank(
        query=query, chunks=chunks, top_k=TOP_K, compute_scores=True
    )
    top1_score = top_k_scores[0] if top_k_scores else 0.0

    noise_in_top_k = sum(1 for c in top_k_chunks if detect_noise(c))
    noise_in_top_k = noise_in_top_k / len(top_k_chunks) if top_k_chunks else 0.0

    return ChunkMetrics(
        strategy=strategy,
        domain=domain,
        page=page,
        num_chunks=len(chunks),
        mean_size=statistics.mean(sizes),
        std_size=statistics.stdev(sizes) if len(sizes) > 1 else 0,
        min_size=min(sizes),
        max_size=max(sizes),
        total_chars=sum(sizes),
        top1_score=round(top1_score, 3),
        noise_in_top_k=round(noise_in_top_k, 3),
        chunks=chunks,
    )


def apply_strategies(
    html: str,
    cleaner: DefaultHTMLCleaner,
    converter: MarkdownConverter,
    semantic_chunker: SemanticChunker,
) -> dict[str, list[str]]:
    results = {}

    # strategy 1: semantic with full clean()
    cleaned = cleaner.clean(html, context_length=CHUNK_SIZE)
    if len(cleaned) >= CHUNK_SIZE:
        results["semantic_clean"] = semantic_chunker.chunk(cleaned, CHUNK_SIZE, OVERLAP)
    else:
        results["semantic_clean"] = [cleaned]

    # strategy 2: semantic with light_clean() (preserves headers and structure)
    light_cleaned = cleaner.light_clean(html)
    if len(light_cleaned) >= CHUNK_SIZE:
        results["semantic_light"] = semantic_chunker.chunk(
            light_cleaned, CHUNK_SIZE, OVERLAP
        )
    else:
        results["semantic_light"] = [light_cleaned]

    # strategy 3: trafilatura + MarkdownTextSplitter
    trafilatura_md = converter.convert(html, strategy="trafilatura")
    if len(trafilatura_md) >= CHUNK_SIZE:
        splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP)
        results["trafilatura"] = splitter.split_text(trafilatura_md)
    else:
        results["trafilatura"] = [trafilatura_md] if trafilatura_md else []

    # strategy 4: markdownify + MarkdownTextSplitter
    markdownify_md = converter.convert(html, strategy="markdownify")
    if len(markdownify_md) >= CHUNK_SIZE:
        splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP)
        results["markdownify"] = splitter.split_text(markdownify_md)
    else:
        results["markdownify"] = [markdownify_md] if markdownify_md else []

    # strategy 5: RecursiveCharacterTextSplitter with light_clean
    if len(light_cleaned) >= CHUNK_SIZE:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=OVERLAP
        )
        results["recursive_light"] = splitter.split_text(light_cleaned)
    else:
        results["recursive_light"] = [light_cleaned]

    return results


def print_metrics(metrics: ChunkMetrics):
    print(
        f"    chunks={metrics.num_chunks:3d} | "
        f"mean={metrics.mean_size:6.0f} | "
        f"std={metrics.std_size:6.0f} | "
        f"min={metrics.min_size:5d} | "
        f"max={metrics.max_size:5d} | "
        f"top1_score={metrics.top1_score:.3f} | "
        f"noise_in_top{TOP_K}={metrics.noise_in_top_k}"
    )


def main():
    cleaner = DefaultHTMLCleaner()
    converter = MarkdownConverter()
    semantic_chunker = SemanticChunker()

    embedding_config = EmbeddingConfig(
        model_name="text-embedding-3-small",
        provider="openai",
        env_alias="OPENAI_API_KEY",
    )

    provider = get_embedding_provider(embedding_config)
    scorer = RelevanceScorer(provider)

    all_metrics: list[ChunkMetrics] = []

    for domain in os.listdir(FIXTURES_DIR):
        domain_path = os.path.join(FIXTURES_DIR, domain)
        if not os.path.isdir(domain_path):
            continue

        query = DOMAIN_QUERIES.get(domain, "Extract the main information.")
        print(f"\n{'=' * 70}")
        print(f"Domain: {domain.upper()}  |  Query: {query}")
        print(f"{'=' * 70}")

        for filename in sorted(os.listdir(domain_path)):
            if not filename.endswith(".html"):
                continue

            page_name = filename.replace(".html", "")
            html_path = os.path.join(domain_path, filename)

            with open(html_path, encoding="utf-8") as f:
                html = f.read()

            print(f"\n  [{page_name}] — original: {len(html):,} chars")

            strategies = apply_strategies(html, cleaner, converter, semantic_chunker)

            for strategy_name, chunks in strategies.items():
                metrics = compute_metrics(
                    strategy=strategy_name,
                    domain=domain,
                    page=page_name,
                    chunks=chunks,
                    query=query,
                    scorer=scorer,
                )
                all_metrics.append(metrics)
                print(f"    {strategy_name:<15}", end="")
                print_metrics(metrics)

    # save raw results
    os.makedirs("docs", exist_ok=True)
    results_path = f"docs/chunking_benchmark_results_{embedding_config.model_name.replace('/', '_')}.json"
    with open(results_path, "w") as f:
        json.dump(
            [
                {k: v for k, v in m.__dict__.items() if k != "chunks"}
                for m in all_metrics
            ],
            f,
            indent=2,
        )
    print(f"\n\nResults saved to {results_path}")
    print("Run scripts/chunking_report.py to generate the markdown summary.")


if __name__ == "__main__":
    main()
