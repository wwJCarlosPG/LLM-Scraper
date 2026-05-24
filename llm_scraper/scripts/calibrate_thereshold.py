"""
Calibration script to measure real similarity scores between
expected values and chunks that contain them.

Run with: poetry run python scripts/calibrate_threshold.py
"""

import json

from dotenv import load_dotenv
from langchain_text_splitters import (
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
)
from sentence_transformers import util

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.adapters.html.markdown_converter import MarkdownConverter
from scraper.adapters.html.semantic_chunker import SemanticChunker
from scraper.core.entities.config import EmbeddingConfig
from scraper.providers.embeddings.factory import get_embedding_provider

load_dotenv()

DATASET_PATH = "tests/fixtures/labeled/dataset.json"
CHUNK_SIZE = 6400
OVERLAP = 640
STRATEGIES = ["trafilatura", "markdownify", "semantic_light", "recursive_light"]

cleaner = DefaultHTMLCleaner()
converter = MarkdownConverter()
semantic_chunker = SemanticChunker()


def get_html(entry: dict) -> str:
    if "html_file" in entry:
        with open(entry["html_file"], encoding="utf-8") as f:
            return f.read()
    return cleaner.fetch(entry["url"])


def chunk_with_strategy(html: str, strategy: str) -> list[str]:
    overlap = int(CHUNK_SIZE * 0.1)
    if strategy == "trafilatura":
        text = converter.convert(html, strategy="trafilatura")
        if not text:
            return []
        if len(text) < CHUNK_SIZE:
            return [text]
        return MarkdownTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=overlap
        ).split_text(text)
    elif strategy == "markdownify":
        text = converter.convert(html, strategy="markdownify")
        if len(text) < CHUNK_SIZE:
            return [text]
        return MarkdownTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=overlap
        ).split_text(text)
    elif strategy == "semantic_light":
        light = cleaner.light_clean(html)
        if len(light) < CHUNK_SIZE:
            return [light]
        return semantic_chunker.chunk(light, CHUNK_SIZE, overlap)
    elif strategy == "recursive_light":
        light = cleaner.light_clean(html)
        if len(light) < CHUNK_SIZE:
            return [light]
        return RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=overlap
        ).split_text(light)
    return []


def expected_to_text(expected: list[dict]) -> list[str]:
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


def string_found_in_any_chunk(expected_text: str, chunks: list[str]) -> bool:
    return any(expected_text.lower().strip() in c.lower() for c in chunks)


def calibrate_entry(entry: dict, provider) -> dict:
    print(f"\n{'=' * 65}")
    print(f"id={entry['id']} | domain={entry['domain']}")
    print(f"query: {entry['query']}")
    print(f"{'=' * 65}")

    try:
        html = get_html(entry)
    except Exception as e:
        print(f"  [fail] {e}")
        return {}

    expected_texts = expected_to_text(entry["expected"])
    print(f"Expected items: {len(expected_texts)}")

    results = {}
    for strategy in STRATEGIES:
        chunks = chunk_with_strategy(html, strategy)
        if not chunks:
            print(f"\n  {strategy}: no chunks generated")
            continue

        print(f"\n  {strategy} ({len(chunks)} chunks):")

        chunk_embs = provider.embed(chunks)
        expected_embs = provider.embed(expected_texts)

        items = find_best_chunk_per_expected(chunk_embs, expected_texts, expected_embs)

        for item in items:
            string_found = string_found_in_any_chunk(item["text"], chunks)
            print(f"    expected      : '{item['text'][:60]}'")
            print(
                f"    best_similarity: {item['best_similarity']:.3f} "
                f"at chunk {item['rank_before'] + 1}/{len(chunks)}"
            )
            print(f"    string_found  : {string_found}")
            print()

            item["string_found"] = string_found

        results[strategy] = items

    return results


def print_global_summary(all_results: list[dict]):
    print(f"\n{'=' * 65}")
    print("GLOBAL CALIBRATION SUMMARY")
    print(f"{'=' * 65}")

    for strategy in STRATEGIES:
        scores = []
        string_found_list = []

        for entry_results in all_results:
            for item in entry_results.get(strategy, []):
                scores.append(item["best_similarity"])
                string_found_list.append(item["string_found"])

        if not scores:
            continue

        print(f"\n  {strategy}:")
        print(
            f"    best_similarity — min={min(scores):.3f}  "
            f"max={max(scores):.3f}  "
            f"avg={sum(scores) / len(scores):.3f}"
        )
        print(
            f"    string_found: "
            f"{sum(string_found_list)}/{len(string_found_list)} "
            f"({sum(string_found_list) / len(string_found_list) * 100:.0f}%)"
        )

        buckets = {"<0.3": 0, "0.3-0.5": 0, "0.5-0.7": 0, "0.7-0.9": 0, ">=0.9": 0}
        for s in scores:
            if s < 0.3:
                buckets["<0.3"] += 1
            elif s < 0.5:
                buckets["0.3-0.5"] += 1
            elif s < 0.7:
                buckets["0.5-0.7"] += 1
            elif s < 0.9:
                buckets["0.7-0.9"] += 1
            else:
                buckets[">=0.9"] += 1
        print(f"    score distribution: {buckets}")

    # threshold recommendation
    print(f"\n{'─' * 65}")
    print("Threshold recommendation (covers 80% of expected items):")
    for strategy in STRATEGIES:
        scores = sorted(
            [
                item["best_similarity"]
                for entry_results in all_results
                for item in entry_results.get(strategy, [])
            ]
        )
        if scores:
            idx_80 = int(len(scores) * 0.2)
            threshold_80 = scores[idx_80]
            print(f"  {strategy:<22} {threshold_80:.3f}")


def main():
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    # use first 5 entries for calibration
    sample = dataset[:5]
    print(f"Calibrating on {len(sample)} entries...")

    embedding_config = EmbeddingConfig(
        model_name="text-embedding-ada-002",
        provider="openai",
        env_alias="OPENAI_API_KEY",
    )
    provider = get_embedding_provider(embedding_config)

    all_results = []
    for entry in sample:
        result = calibrate_entry(entry, provider)
        all_results.append(result)

    print_global_summary(all_results)


if __name__ == "__main__":
    main()
