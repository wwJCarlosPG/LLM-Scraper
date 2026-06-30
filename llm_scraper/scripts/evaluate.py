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
from scraper.core.entities.token_usage import TokenUsage
from scraper.pipeline.runner import run
from scraper.providers.embeddings.factory import get_embedding_provider

load_dotenv()

DATASET_PATH = "tests/fixtures/labeled/dataset.json"

SIMILARITY_THRESHOLD_C1_C2 = 0.95
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
    temperature=0.6,
    json_mode="none",
)

VALIDATOR_MODEL = ProviderConfig(
    provider="openai_compatible",
    model_name="Qwen/Qwen2.5-7B-Instruct-Turbo",
    endpoint="https://api.together.xyz/v1/chat/completions",
    env_alias="TOGETHER_API_KEY",
    temperature=0.1,
    json_mode="none",
    context_length=120000,
)

CONFIG_NAME = "E_small_baseline"
ACTIVE_CONFIG = PipelineConfig(
    extractor_provider=SMALL_MODEL,
    validator_provider=VALIDATOR_MODEL,
    hyde_provider=HYDE_MODEL,
    cot=False,
    refinement=True,
    max_retries=1,
    use_markdown_conversion=False,  # semantic_light
    context_length=32000,
    top_k_chunks=10,
)

RESULTS_PATH = f"docs/evaluation_results_{CONFIG_NAME}.json"

CONFIGS = {
    "A_small_baseline": PipelineConfig(
        extractor_provider=SMALL_MODEL,
        validator_provider=SMALL_MODEL,
        cot=False,
        refinement=False,
        max_retries=0,
        use_markdown_conversion=False,
        # markdown_converter="trafilatura",
        top_k_chunks=9999,
    ),
    "B_small_baseline": PipelineConfig(
        extractor_provider=SMALL_MODEL,
        validator_provider=SMALL_MODEL,
        cot=False,
        refinement=True,
        max_retries=1,
        use_markdown_conversion=False,  # semantic_light
        context_length=32000,
        top_k_chunks=9999,
    ),
    # "C_small_pipeline": PipelineConfig(
    #     extractor_provider=SMALL_MODEL,
    #     validator_provider=SMALL_MODEL,
    #     hyde_provider=HYDE_MODEL,
    #     cot=False,
    #     refinement=True,
    #     max_retries=2,
    #     use_markdown_conversion=False,
    #     markdown_converter="trafilatura",
    #     top_k_chunks=10,
    # ),
    # "B_large_baseline": PipelineConfig(
    #     extractor_provider=LARGE_MODEL,
    #     validator_provider=LARGE_MODEL,
    #     hyde_provider=HYDE_MODEL,
    #     cot=False,
    #     refinement=False,
    #     max_retries=0,
    #     use_markdown_conversion=True,
    #     markdown_converter="trafilatura",
    #     top_k_chunks=9999,
    # ),
    # "D_large_pipeline": PipelineConfig(
    #     extractor_provider=LARGE_MODEL,
    #     validator_provider=LARGE_MODEL,
    #     hyde_provider=HYDE_MODEL,
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
    # efficiency metrics
    latency_ms: float = 0.0
    scorer_input_tokens: int = 0
    scorer_output_tokens: int = 0
    extractor_input_tokens: int = 0
    extractor_output_tokens: int = 0
    validator_input_tokens: int = 0
    validator_output_tokens: int = 0
    refinement_used: bool = False
    error: str = ""


def _aggregate_tokens(token_usage: list[TokenUsage], role: str) -> tuple[int, int]:
    entries = [u for u in token_usage if u.role == role]
    return sum(u.input_tokens for u in entries), sum(u.output_tokens for u in entries)


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
    if config.domain == "documentation" or config.domain == "news":
        config.use_markdown_conversion = True
    else:
        config.use_markdown_conversion = False
    try:
        result, token_usage = await run(
            query=entry["query"],
            output_format=entry["output_format"],
            config=config,
            html=html,
        )
        extracted = result.scraped_data if result and result.scraped_data else []
        refinement_used = result.refinement_count > 0 if result else False
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
    scorer_in, scorer_out = _aggregate_tokens(token_usage, "scorer")
    extractor_in, extractor_out = _aggregate_tokens(token_usage, "extractor")
    validator_in, validator_out = _aggregate_tokens(token_usage, "validator")
    total_in = scorer_in + extractor_in + validator_in
    total_out = scorer_out + extractor_out + validator_out
    print(
        f"    {config_name}: p={precision} r={recall} f1={f1} "
        f"| tokens in={total_in} out={total_out}"
    )
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
        scorer_input_tokens=scorer_in,
        scorer_output_tokens=scorer_out,
        extractor_input_tokens=extractor_in,
        extractor_output_tokens=extractor_out,
        validator_input_tokens=validator_in,
        validator_output_tokens=validator_out,
        refinement_used=refinement_used,
    )


def print_summary(results: list[EntryResult]):
    valid = [r for r in results if not r.error]

    print(f"\n{'=' * 70}")
    print(f"EVALUATION SUMMARY — {CONFIG_NAME}")
    print(f"{'=' * 70}")
    print(f"Entries: {len(valid)}/{len(results)} valid")

    if not valid:
        return

    avg_f1 = sum(r.f1 for r in valid) / len(valid)
    avg_p = sum(r.precision for r in valid) / len(valid)
    avg_r = sum(r.recall for r in valid) / len(valid)
    avg_latency = sum(r.latency_ms for r in valid) / len(valid)
    scorer_in = sum(r.scorer_input_tokens for r in valid)
    scorer_out = sum(r.scorer_output_tokens for r in valid)
    extractor_in = sum(r.extractor_input_tokens for r in valid)
    extractor_out = sum(r.extractor_output_tokens for r in valid)
    validator_in = sum(r.validator_input_tokens for r in valid)
    validator_out = sum(r.validator_output_tokens for r in valid)
    total_in = scorer_in + extractor_in + validator_in
    total_out = scorer_out + extractor_out + validator_out
    refined = sum(1 for r in valid if r.refinement_used)

    print(f"\n{'─' * 70}")
    print("Overall:")
    print(f"  F1:          {avg_f1:.3f}  (p={avg_p:.3f} r={avg_r:.3f})")
    print(f"  Latency:     {avg_latency:.0f}ms avg")
    print(f"  Refinements: {refined}/{len(valid)} entries used refinement")
    print(f"\n{'─' * 70}")
    print("Token usage (real counts from API):")
    print(f"  {'Role':<12} {'Input':>10} {'Output':>10} {'Total':>10}")
    print(
        f"  {'scorer':<12} {scorer_in:>10,} {scorer_out:>10,} {scorer_in + scorer_out:>10,}"
    )
    print(
        f"  {'extractor':<12} {extractor_in:>10,} {extractor_out:>10,} {extractor_in + extractor_out:>10,}"
    )
    print(
        f"  {'validator':<12} {validator_in:>10,} {validator_out:>10,} {validator_in + validator_out:>10,}"
    )
    print(f"  {'─' * 12}   {'─' * 10}   {'─' * 10}   {'─' * 10}")
    print(
        f"  {'TOTAL':<12} {total_in:>10,} {total_out:>10,} {total_in + total_out:>10,}"
    )

    print(f"\n{'─' * 70}")
    print("F1 by domain:")
    for domain in sorted({r.domain for r in valid}):
        d = [r for r in valid if r.domain == domain]
        avg = sum(r.f1 for r in d) / len(d)
        lat = sum(r.latency_ms for r in d) / len(d)
        print(f"  {domain:<15} f1={avg:.3f}  latency={lat:.0f}ms  (n={len(d)})")

    print(f"\n{'─' * 70}")
    print("F1 by complexity:")
    for c in [1, 2, 3]:
        d = [r for r in valid if r.complexity == c]
        if d:
            avg = sum(r.f1 for r in d) / len(d)
            print(f"  complexity={c}   f1={avg:.3f}  (n={len(d)})")


async def main():
    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    print(f"Dataset: {len(dataset)} entries")
    print(f"Config:  {CONFIG_NAME}")
    print(f"Output:  {RESULTS_PATH}")

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
            raw_results = json.load(f)
        valid_fields = {f.name for f in __import__("dataclasses").fields(EntryResult)}
        results = [
            EntryResult(**{k: v for k, v in r.items() if k in valid_fields})
            for r in raw_results
        ]
        processed = {(r.id, r.domain) for r in results}
        print(f"Resuming from {len(results)} results")
    else:
        processed = set()

    try:
        for entry in dataset:
            if (entry["id"], entry["domain"]) in processed:
                print(f"  [skip] [{entry['domain']}] id={entry['id']}")
                continue

            print(f"\n[{entry['domain']}] id={entry['id']} — {entry['query'][:55]}...")
            try:
                html = get_html(entry)
            except Exception as e:
                print(f"  [fail] HTML: {e}")
                continue

            result = await evaluate_entry(
                entry, CONFIG_NAME, ACTIVE_CONFIG, embedder, html
            )
            results.append(result)
            processed.add((entry["id"], entry["domain"]))

            with open(RESULTS_PATH, "w") as f:
                json.dump([asdict(r) for r in results], f, indent=2, ensure_ascii=False)

    except KeyboardInterrupt:
        print(f"\n[interrupted] {len(results)} results saved.")

    print_summary(results)
    print(f"\nResults saved to {RESULTS_PATH}")


if __name__ == "__main__":
    asyncio.run(main())
