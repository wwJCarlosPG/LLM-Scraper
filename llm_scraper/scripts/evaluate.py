"""
Phase 2 evaluation: full pipeline vs baseline comparison.

Configs:
  A: Qwen3.5-9B   + no pipeline (trafilatura + single LLM call)
  B: Gemini Flash + no pipeline
  C: Qwen3.5-9B   + full pipeline (CoT + validation + refinement)
  D: Gemini Flash + full pipeline

Run with: poetry run python scripts/evaluate.py
"""

import asyncio
import json
import os
from dataclasses import asdict, dataclass

from dotenv import load_dotenv
from sentence_transformers import util

from scraper.adapters.html.cleaner import DefaultHTMLCleaner
from scraper.core.entities.config import EmbeddingConfig, PipelineConfig, ProviderConfig
from scraper.pipeline.runner import run
from scraper.providers.embeddings.factory import get_embedding_provider

load_dotenv()

DATASET_PATH = "tests/fixtures/labeled/dataset.json"
RESULTS_PATH = "docs/evaluation_results_small_SL_refinement.json"

SIMILARITY_THRESHOLD_C1_C2 = 0.85
# SIMILARITY_THRESHOLD_C3 = 0.75

cleaner = DefaultHTMLCleaner()

SMALL_MODEL = ProviderConfig(
    provider="openai_compatible",
    model_name="google/gemma-3n-E4B-it",
    endpoint="https://api.together.xyz/v1/chat/completions",
    env_alias="TOGETHER_API_KEY",
    context_length=32000,
)

LARGE_MODEL = ProviderConfig(
    provider="openai_compatible",
    model_name="openai/gpt-oss-120b",
    endpoint="https://api.together.xyz/v1/chat/completions",
    env_alias="TOGETHER_API_KEY",
    context_length=128000,
)

HYDE_MODEL = ProviderConfig(
    provider="openai_compatible",
    model_name="Qwen/Qwen2.5-7B-Instruct-Turbo",
    endpoint="https://api.together.xyz/v1/chat/completions",
    env_alias="TOGETHER_API_KEY",
)

CONFIGS = {
    # "A_small_baseline": PipelineConfig(
    #     provider=SMALL_MODEL,
    #     hyde_provider=HYDE_MODEL,
    #     cot=False,
    #     refinement=False,
    #     max_retries=0,
    #     use_markdown_conversion=False,
    #     # markdown_converter="trafilatura",
    #     top_k_chunks=10,
    # ),
    # "B_large_baseline": PipelineConfig(
    #     provider=LARGE_MODEL,
    #     hyde_provider=HYDE_MODEL,
    #     cot=False,
    #     refinement=False,
    #     max_retries=0,
    #     use_markdown_conversion=True,
    #     markdown_converter="trafilatura",
    #     top_k_chunks=9999,
    # ),
    "C_small_pipeline": PipelineConfig(
        provider=SMALL_MODEL,
        hyde_provider=HYDE_MODEL,
        cot=False,
        refinement=True,
        max_retries=3,
        use_markdown_conversion=False,
        markdown_converter="trafilatura",
        top_k_chunks=10,
    ),
    # "D_large_pipeline": PipelineConfig(
    #     provider=LARGE_MODEL,
    #     cot=True,
    #     refinement=True,
    #     max_retries=2,
    #     use_markdown_conversion=True,
    #     markdown_converter="trafilatura",
    #     top_k_chunks=9999,
    # ),
}


@dataclass
class EntryResult:
    id: int
    domain: str
    complexity: int
    query: str
    config_name: str
    expected: list[dict]
    extracted: list[dict]
    precision: float
    recall: float
    f1: float
    error: str = ""


def get_html(entry: dict) -> str:
    if "html_file" in entry:
        with open(entry["html_file"], encoding="utf-8") as f:
            return f.read()
    return cleaner.fetch(entry["url"])


def item_to_text(item: dict) -> str:
    values = []
    for v in item.values():
        if isinstance(v, list):
            values.extend(str(x) for x in v)
        else:
            values.append(str(v))
    return " ".join(values)


def compute_f1(
    expected: list[dict],
    extracted: list[dict],
    embedder,
    threshold: float,
) -> tuple[float, float, float]:
    if not expected and not extracted:
        return 1.0, 1.0, 1.0
    if not extracted:
        return 0.0, 0.0, 0.0
    if not expected:
        return 0.0, 0.0, 0.0

    exp_texts = [item_to_text(e) for e in expected]
    ext_texts = [item_to_text(e) for e in extracted]
    exp_embs = embedder.embed(exp_texts)
    ext_embs = embedder.embed(ext_texts)

    tp_precision = sum(
        1
        for ext_emb in ext_embs
        if max(util.cos_sim(ext_emb, e).item() for e in exp_embs) >= threshold
    )
    tp_recall = sum(
        1
        for exp_emb in exp_embs
        if max(util.cos_sim(exp_emb, e).item() for e in ext_embs) >= threshold
    )

    precision = round(tp_precision / len(extracted), 3)
    recall = round(tp_recall / len(expected), 3)
    f1 = (
        round(2 * precision * recall / (precision + recall), 3)
        if (precision + recall) > 0
        else 0.0
    )

    return precision, recall, f1


async def evaluate_entry(
    entry: dict,
    config_name: str,
    config: PipelineConfig,
    embedder,
    html: str,
) -> EntryResult:
    threshold = SIMILARITY_THRESHOLD_C1_C2

    config.domain = entry["domain"]
    try:
        result = await run(
            query=entry["query"],
            output_format=entry["output_format"],
            config=config,
            html=html,
        )
        extracted = result.scraped_data if result and result.scraped_data else []
    except Exception as e:
        print(f"    [fail] {config_name}: {e}")
        return EntryResult(
            id=entry["id"],
            domain=entry["domain"],
            complexity=entry["complexity"],
            query=entry["query"],
            config_name=config_name,
            expected=entry["expected"],
            extracted=[],
            precision=0.0,
            recall=0.0,
            f1=0.0,
            error=str(e),
        )

    precision, recall, f1 = compute_f1(
        entry["expected"], extracted, embedder, threshold
    )
    print(f"    {config_name}: p={precision} r={recall} f1={f1}")

    return EntryResult(
        id=entry["id"],
        domain=entry["domain"],
        complexity=entry["complexity"],
        query=entry["query"],
        config_name=config_name,
        expected=entry["expected"],
        extracted=extracted,
        precision=precision,
        recall=recall,
        f1=f1,
    )


def print_summary(results: list[EntryResult]):
    config_names = list(CONFIGS.keys())

    print(f"\n{'=' * 70}")
    print("EVALUATION SUMMARY")
    print(f"{'=' * 70}")

    print(f"\n{'─' * 70}")
    print("Overall F1:")
    for name in config_names:
        entries = [r for r in results if r.config_name == name and not r.error]
        if entries:
            avg_f1 = sum(r.f1 for r in entries) / len(entries)
            avg_p = sum(r.precision for r in entries) / len(entries)
            avg_r = sum(r.recall for r in entries) / len(entries)
            print(
                f"  {name:<25} p={avg_p:.3f} r={avg_r:.3f} f1={avg_f1:.3f} (n={len(entries)})"
            )

    print(f"\n{'─' * 70}")
    print("F1 by domain:")
    for domain in sorted({r.domain for r in results}):
        print(f"\n  {domain}:")
        for name in config_names:
            entries = [
                r
                for r in results
                if r.config_name == name and r.domain == domain and not r.error
            ]
            if entries:
                avg_f1 = sum(r.f1 for r in entries) / len(entries)
                print(f"    {name:<25} f1={avg_f1:.3f} (n={len(entries)})")

    print(f"\n{'─' * 70}")
    print("F1 by complexity:")
    for c in [1, 2, 3]:
        c_results = [r for r in results if r.complexity == c]
        if not c_results:
            continue
        print(f"\n  complexity={c}:")
        for name in config_names:
            entries = [r for r in c_results if r.config_name == name and not r.error]
            if entries:
                avg_f1 = sum(r.f1 for r in entries) / len(entries)
                print(f"    {name:<25} f1={avg_f1:.3f} (n={len(entries)})")

    print(f"\n{'─' * 70}")
    print("Pipeline improvement (pipeline F1 - baseline F1):")
    for baseline_name, pipeline_name, label in [
        ("A_small_baseline", "C_small_pipeline", "small model"),
        ("B_large_baseline", "D_large_pipeline", "large model"),
    ]:
        b = {
            (r.id, r.domain): r
            for r in results
            if r.config_name == baseline_name and not r.error
        }
        p = {
            (r.id, r.domain): r
            for r in results
            if r.config_name == pipeline_name and not r.error
        }
        common = set(b.keys()) & set(p.keys())
        if common:
            impr = [p[k].f1 - b[k].f1 for k in common]
            avg = sum(impr) / len(impr)
            better = sum(1 for i in impr if i > 0.05)
            same = sum(1 for i in impr if abs(i) <= 0.05)
            worse = sum(1 for i in impr if i < -0.05)
            print(
                f"  {label:<12} avg={avg:+.3f}  better={better} same={same} worse={worse}"
            )

    print(f"\n{'─' * 70}")
    print("Gap: small+pipeline vs large+baseline (C vs B):")
    b = {
        (r.id, r.domain): r
        for r in results
        if r.config_name == "B_large_baseline" and not r.error
    }
    p = {
        (r.id, r.domain): r
        for r in results
        if r.config_name == "C_small_pipeline" and not r.error
    }
    common = set(b.keys()) & set(p.keys())
    if common:
        gaps = [p[k].f1 - b[k].f1 for k in common]
        avg = sum(gaps) / len(gaps)
        print(f"  avg={avg:+.3f}  (positive = small+pipeline beats large+baseline)")


async def main():
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    print(f"Dataset: {len(dataset)} entries")
    print(f"Configs: {list(CONFIGS.keys())}")

    embedder = get_embedding_provider(
        EmbeddingConfig(
            model_name="text-embedding-ada-002",
            provider="openai",
            env_alias="OPENAI_API_KEY",
        )
    )

    os.makedirs("docs", exist_ok=True)

    results: list[EntryResult] = []
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            results = [EntryResult(**r) for r in json.load(f)]
        processed = {(r.id, r.domain, r.config_name) for r in results}
        print(f"Resuming from {len(results)} results")
    else:
        processed = set()

    try:
        for entry in dataset:
            print(f"\n[{entry['domain']}] id={entry['id']} — {entry['query'][:55]}...")
            try:
                html = get_html(entry)
            except Exception as e:
                print(f"  [fail] HTML: {e}")
                continue

            for config_name, config in CONFIGS.items():
                if (entry["id"], entry["domain"], config_name) in processed:
                    print(f"  [skip] {config_name}")
                    continue

                result = await evaluate_entry(
                    entry, config_name, config, embedder, html
                )
                results.append(result)
                processed.add((entry["id"], entry["domain"], config_name))

                with open(RESULTS_PATH, "w") as f:
                    json.dump(
                        [asdict(r) for r in results], f, indent=2, ensure_ascii=False
                    )

    except KeyboardInterrupt:
        print(f"\n[interrupted] {len(results)} results saved.")

    print_summary(results)
    print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
