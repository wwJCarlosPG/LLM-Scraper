"""
Phase 1 evaluation: chunking strategy and top_k analysis.

For each entry in the labeled dataset, tests how many chunking strategies
and top_k values are needed to cover the expected answers.

Run with: poetry run python scripts/chunking_coverage.py
"""

import json
import os

from dotenv import load_dotenv
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sentence_transformers import util

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.adapters.html.relevance_scorer import RelevanceScorer
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.core.entities.config import EmbeddingConfig
from scraper.providers.embeddings.factory import get_embedding_provider

load_dotenv()

DATASET_PATH = "tests/fixtures/labeled/dataset.json"
RESULTS_PATH = "docs/chunking_coverage_results_3.json"

CHUNK_SIZES = {
    "small_8k": 1600,
    "medium_32k": 6400,
}
MAX_K = 15
OVERLAP_RATIO = 0.1  # overlap = 10% of chunk size
SIMILARITY_THRESHOLD = 0.75
STRATEGIES = ["trafilatura", "markdownify", "semantic_light", "recursive_light"]

cleaner = DefaultHTMLCleaner()
converter = MarkdownConverter()
semantic_chunker = SemanticChunker()


def get_html(entry: dict) -> str:
    if "html_file" in entry:
        with open(entry["html_file"], encoding="utf-8") as f:
            return f.read()
    return cleaner.fetch(entry["url"])


def apply_safety_net(chunks: list[str], max_chars: int = 20000) -> list[str]:
    """Splits any chunk that exceeds max_chars using RecursiveCharacterTextSplitter."""
    result = []
    splitter = RecursiveCharacterTextSplitter(chunk_size=max_chars, chunk_overlap=0)
    for chunk in chunks:
        if len(chunk) > max_chars:
            result.extend(splitter.split_text(chunk))
        else:
            result.append(chunk)
    return result


def chunk_with_strategy(html: str, strategy: str, chunk_size: int) -> list[str]:
    overlap = int(chunk_size * OVERLAP_RATIO)

    if strategy == "trafilatura":
        text = converter.convert(html, strategy="trafilatura")
        if not text:
            return []
        if len(text) < chunk_size:
            return [text]
        splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        return splitter.split_text(text)

    elif strategy == "markdownify":
        text = converter.convert(html, strategy="markdownify")
        if len(text) < chunk_size:
            return [text]
        splitter = MarkdownTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        return splitter.split_text(text)

    elif strategy == "semantic_light":
        light = cleaner.light_clean(html)
        if len(light) < chunk_size:
            return [light]
        return semantic_chunker.chunk(light, chunk_size, overlap)

    elif strategy == "recursive_light":
        light = cleaner.light_clean(html)
        if len(light) < chunk_size:
            return [light]
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, chunk_overlap=overlap
        )
        return splitter.split_text(light)

    return []


def expected_to_text(expected: list[dict]) -> list[str]:
    """
    Converts expected items to individual text strings for embedding.
    List values are treated as separate texts to avoid diluting embeddings.
    """
    texts = []
    for item in expected:
        non_list_values = []
        for v in item.values():
            if isinstance(v, list):
                for element in v:
                    texts.append(str(element))
            else:
                non_list_values.append(str(v))
        if non_list_values:
            texts.append(" ".join(non_list_values))
    return texts


def find_best_chunk_per_expected(
    chunk_embs,
    expected_texts: list[str],
    expected_embs,
) -> list[dict]:
    """
    For each expected text, finds the chunk with highest cosine similarity.
    Returns list of {text, best_similarity, rank_before} dicts.
    """
    results = []
    for exp_text, exp_emb in zip(expected_texts, expected_embs, strict=False):
        best_sim = -1.0
        best_idx = 0
        for i, chunk_emb in enumerate(chunk_embs):
            sim = util.cos_sim(chunk_emb, exp_emb).item()
            if sim > best_sim:
                best_sim = sim
                best_idx = i
        results.append(
            {
                "text": exp_text,
                "best_similarity": round(best_sim, 4),
                "rank_before": best_idx,
            }
        )
    return results


def analyze_entry(entry: dict, scorer: RelevanceScorer) -> dict:
    print(f"  [{entry['domain']}] id={entry['id']} — {entry['query'][:55]}...")

    try:
        html = get_html(entry)
    except Exception as e:
        print(f"  [fail] {e}")
        return {
            "id": entry["id"],
            "domain": entry["domain"],
            "query": entry["query"],
            "error": str(e),
        }

    expected_texts = expected_to_text(entry["expected"])
    if not expected_texts:
        return {
            "id": entry["id"],
            "domain": entry["domain"],
            "query": entry["query"],
            "error": "empty expected",
        }

    results = {}
    for size_name, chunk_size in CHUNK_SIZES.items():
        results[size_name] = {}
        for strategy in STRATEGIES:
            chunks = chunk_with_strategy(html, strategy, chunk_size)
            if strategy == "semantic_light":
                chunks = apply_safety_net(chunks)
            if not chunks:
                results[size_name][strategy] = {
                    "coverage_ratio": {k: 0.0 for k in range(1, MAX_K + 1)},
                    "false_positive_ratio": {k: 1.0 for k in range(1, MAX_K + 1)},
                    "num_chunks": 0,
                }
                continue

            # Compute embeddings once for this chunk/strategy combo
            chunk_embs = scorer.embedding_provider.embed(chunks)
            expected_embs = scorer.embedding_provider.embed(expected_texts)

            # For each expected text, find best matching chunk (rank_before)
            expected_items = find_best_chunk_per_expected(
                chunk_embs, expected_texts, expected_embs
            )

            # Rank all chunks with scorer once
            ranked_chunks, _ = scorer.rank(
                query=entry["query"],
                chunks=chunks,
                top_k=MAX_K,
                compute_scores=True,
            )

            # Map chunk text -> position in scorer's ranking
            ranked_index = {chunk: i for i, chunk in enumerate(ranked_chunks)}

            for item in expected_items:
                item["rank_after"] = ranked_index.get(chunks[item["rank_before"]])

            # coverage_ratio[k]: % of expected items with best chunk in top-k (similarity >= threshold)
            coverage_ratio = {
                k: round(
                    sum(
                        1
                        for item in expected_items
                        if item.get("rank_after") is not None
                        and item["rank_after"] < k
                        and item["best_similarity"] >= SIMILARITY_THRESHOLD
                    )
                    / len(expected_items),
                    3,
                )
                for k in range(1, MAX_K + 1)
            }

            # Precompute relevance per chunk for false_positive_ratio
            chunk_is_relevant = [
                any(
                    util.cos_sim(c_emb, e_emb).item() >= SIMILARITY_THRESHOLD
                    for e_emb in expected_embs
                )
                for c_emb in chunk_embs
            ]
            chunk_relevance_map = {
                chunk: chunk_is_relevant[i] for i, chunk in enumerate(chunks)
            }

            false_positive_ratio = {
                k: round(
                    (
                        k
                        - sum(
                            chunk_relevance_map.get(c, False) for c in ranked_chunks[:k]
                        )
                    )
                    / k,
                    3,
                )
                for k in range(1, MAX_K + 1)
            }

            results[size_name][strategy] = {
                "expected_items": expected_items,
                "coverage_ratio": coverage_ratio,
                "false_positive_ratio": false_positive_ratio,
                "num_chunks": len(chunks),
            }

    return {
        "id": entry["id"],
        "domain": entry["domain"],
        "complexity": entry["complexity"],
        "query": entry["query"],
        "strategies": results,
    }


def print_summary(results: list[dict]):
    valid = [r for r in results if "error" not in r]

    print(f"\n{'=' * 70}")
    print("CHUNKING COVERAGE ANALYSIS")
    print(f"{'=' * 70}")
    print(f"Entries: {len(valid)}/{len(results)} valid")
    print(f"Similarity threshold: {SIMILARITY_THRESHOLD}")

    for size_name, chunk_size in CHUNK_SIZES.items():
        print(f"\n{'═' * 70}")
        print(f"Chunk size: {size_name} ({chunk_size} chars)")
        print(f"{'═' * 70}")

        # coverage ratio table
        print("\n  Coverage ratio (avg % of expected items in top-k):")
        print(f"  {'strategy':<22}", end="")
        for k in range(1, MAX_K + 1):
            print(f"  k={k}", end="")
        print()
        print(f"  {'─' * 50}")

        for strategy in STRATEGIES:
            print(f"  {strategy:<22}", end="")
            for k in range(1, MAX_K + 1):
                ratios = []
                for r in valid:
                    items = (
                        r["strategies"]
                        .get(size_name, {})
                        .get(strategy, {})
                        .get("expected_items", [])
                    )
                    if not items:
                        continue
                    covered = sum(
                        1
                        for item in items
                        if item.get("rank_after") is not None
                        and item["rank_after"] < k
                        and item["best_similarity"] >= SIMILARITY_THRESHOLD
                    )
                    ratios.append(covered / len(items))
                avg = sum(ratios) / len(ratios) * 100 if ratios else 0
                print(f"  {avg:4.0f}%", end="")
            print()

        # binary coverage (ratio >= 0.8)
        print("\n  Hard coverage (entries where ≥80% items covered):")
        print(f"  {'strategy':<22}", end="")
        for k in range(1, MAX_K + 1):
            print(f"  k={k}", end="")
        print()
        print(f"  {'─' * 50}")

        for strategy in STRATEGIES:
            print(f"  {strategy:<22}", end="")
            for k in range(1, MAX_K + 1):
                covered = 0
                for r in valid:
                    items = (
                        r["strategies"]
                        .get(size_name, {})
                        .get(strategy, {})
                        .get("expected_items", [])
                    )
                    if not items:
                        continue
                    ratio = sum(
                        1
                        for item in items
                        if item.get("rank_after") is not None
                        and item["rank_after"] < k
                        and item["best_similarity"] >= SIMILARITY_THRESHOLD
                    ) / len(items)
                    if ratio >= 0.8:
                        covered += 1
                pct = covered / len(valid) * 100 if valid else 0
                print(f"  {pct:4.0f}%", end="")
            print()

        # scorer improvement
        print("\n  Scorer improvement (avg rank change per expected item):")
        for strategy in STRATEGIES:
            improvements = [
                item["rank_before"] - item["rank_after"]
                for r in valid
                for item in r["strategies"]
                .get(size_name, {})
                .get(strategy, {})
                .get("expected_items", [])
                if item.get("rank_before") is not None
                and item.get("rank_after") is not None
            ]
            if improvements:
                avg = sum(improvements) / len(improvements)
                positive = sum(1 for i in improvements if i > 0)
                neutral = sum(1 for i in improvements if i == 0)
                negative = sum(1 for i in improvements if i < 0)
                print(
                    f"    {strategy:<22} avg={avg:+.2f}  "
                    f"better={positive} same={neutral} worse={negative}"
                )

        # false positive ratio at k=3
        print("\n  False positive ratio at k=3:")
        for strategy in STRATEGIES:
            ratios = [
                r["strategies"]
                .get(size_name, {})
                .get(strategy, {})
                .get("false_positive_ratio", {})
                .get(3, 1.0)
                for r in valid
            ]
            avg = sum(ratios) / len(ratios) * 100 if ratios else 0
            print(f"    {strategy:<22} {avg:.0f}% irrelevant chunks in top-3")

        # by domain
        domains = sorted({r["domain"] for r in valid})
        for domain in domains:
            domain_results = [r for r in valid if r["domain"] == domain]
            print(f"\n  Domain: {domain} (n={len(domain_results)})")
            for strategy in STRATEGIES:
                print(f"    {strategy:<22}", end="")
                for k in range(1, MAX_K + 1):
                    ratios = []
                    for r in domain_results:
                        items = (
                            r["strategies"]
                            .get(size_name, {})
                            .get(strategy, {})
                            .get("expected_items", [])
                        )
                        if not items:
                            continue
                        covered = sum(
                            1
                            for item in items
                            if item.get("rank_after") is not None
                            and item["rank_after"] < k
                            and item["best_similarity"] >= SIMILARITY_THRESHOLD
                        )
                        ratios.append(covered / len(items))
                    avg = sum(ratios) / len(ratios) * 100 if ratios else 0
                    print(f"  {avg:4.0f}%", end="")
                print()

        # minimum k for 80% coverage ratio
        print("\n  Minimum k for avg coverage ratio ≥80%:")
        for strategy in STRATEGIES:
            for k in range(1, MAX_K + 1):
                ratios = []
                for r in valid:
                    items = (
                        r["strategies"]
                        .get(size_name, {})
                        .get(strategy, {})
                        .get("expected_items", [])
                    )
                    if not items:
                        continue
                    covered = sum(
                        1
                        for item in items
                        if item.get("rank_after") is not None
                        and item["rank_after"] < k
                        and item["best_similarity"] >= SIMILARITY_THRESHOLD
                    )
                    ratios.append(covered / len(items))
                avg = sum(ratios) / len(ratios) * 100 if ratios else 0
                if avg >= 80:
                    print(f"    {strategy:<22} k={k} ({avg:.0f}%)")
                    break
            else:
                max_avg = max(
                    sum(
                        sum(
                            1
                            for item in r["strategies"]
                            .get(size_name, {})
                            .get(strategy, {})
                            .get("expected_items", [])
                            if item.get("rank_after") is not None
                            and item["rank_after"] < k
                            and item["best_similarity"] >= SIMILARITY_THRESHOLD
                        )
                        / max(
                            len(
                                r["strategies"]
                                .get(size_name, {})
                                .get(strategy, {})
                                .get("expected_items", [])
                            ),
                            1,
                        )
                        for r in valid
                        if r["strategies"]
                        .get(size_name, {})
                        .get(strategy, {})
                        .get("expected_items")
                    )
                    / len(valid)
                    * 100
                    for k in range(1, MAX_K + 1)
                )
                print(f"    {strategy:<22} never reaches 80% (max {max_avg:.0f}%)")


def main():
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    print(f"Dataset: {len(dataset)} entries")

    embedding_config = EmbeddingConfig(
        model_name="text-embedding-ada-002",
        provider="openai",
        env_alias="OPENAI_API_KEY",
    )
    provider = get_embedding_provider(embedding_config)
    scorer = RelevanceScorer(provider)

    os.makedirs("docs", exist_ok=True)

    # load existing results to resume
    results = []
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            results = json.load(f)
        processed_ids = {
            (r["id"], r["domain"])
            for r in results
            if "error" not in r or r.get("error") != "skipped"
        }
        print(f"Resuming from {len(results)} already processed entries")
    else:
        processed_ids = set()

    try:
        for entry in dataset:
            if (entry["id"], entry["domain"]) in processed_ids:
                print(f"  [skip] [{entry['domain']}] id={entry['id']}")
                continue
            result = analyze_entry(entry, scorer)
            results.append(result)
            with open(RESULTS_PATH, "w") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
    except KeyboardInterrupt:
        print(f"\n[interrupted] {len(results)}/{len(dataset)} entries processed.")

    if results:
        print_summary(results)
        print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
