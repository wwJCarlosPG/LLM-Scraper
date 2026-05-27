"""
Custom provider example using an OpenAI-compatible endpoint.

This example shows how to use a local model via LM Studio or Ollama,
or a third-party provider like Fireworks AI.
"""

import asyncio

from dotenv import load_dotenv

from scraper.core.entities.config import PipelineConfig, ProviderConfig
from scraper.pipeline.runner import run

load_dotenv()


# ── Example 1: LM Studio (local) ──────────────────────────────────────────
lmstudio_config = PipelineConfig(
    provider=ProviderConfig(
        provider="openai_compatible",
        model_name="llama-3-8b-instruct",
        api_key="lm-studio",  # LM Studio accepts any key
        endpoint="http://localhost:1234/v1/chat/completions",
    ),
    cot=True,
    refinement=False,  # disable refinement for faster local inference
    context_length=8000,  # smaller context for lightweight models
)

# ── Example 2: Fireworks AI ───────────────────────────────────────────────
fireworks_config = PipelineConfig(
    provider=ProviderConfig(
        provider="openai_compatible",
        model_name="accounts/fireworks/models/llama-v3p3-70b-instruct",
        env_alias="FIREWORKS_API_KEY",
        endpoint="https://api.fireworks.ai/inference/v1/chat/completions",
    ),
    cot=True,
    refinement=True,
    self_consistency=False,
    context_length=32000,
)

# ── Example 3: Markdown conversion for article pages ─────────────────────
article_config = PipelineConfig(
    provider=ProviderConfig(
        provider="gemini", model_name="gemini-2.0-flash", env_alias="GEMINI_API_KEY"
    ),
    use_markdown_conversion=True,
    markdown_converter="trafilatura",  # best for news/blog pages
    cot=True,
    refinement=True,
    context_length=32000,
)

# ── Example 4: Self-consistency for high-accuracy extractions ────────────
self_consistency_config = PipelineConfig(
    provider=ProviderConfig(
        provider="gemini", model_name="gemini-1.5-pro", env_alias="GEMINI_API_KEY"
    ),
    cot=True,
    self_consistency=True,
    self_consistency_samples=3,
    refinement=False,  # self_consistency + refinement is expensive
    context_length=32000,
)


async def main():
    # swap config to try different providers/strategies
    config = fireworks_config

    result = await run(
        query="Extract the article title and publication date.",
        output_format={"title": "article title", "date": "publication date"},
        config=config,
        html_url="https://www.bbc.com/news/articles/cjr5lrg5x2go",
    )

    if result:
        print(f"Extracted {len(result.scraped_data)} items:")
        for item in result.scraped_data:
            print(f"  - {item}")
        print(f"\nValid: {result.is_valid}")
        print(f"Feedback: {result.feedback}")
        print(f"Refinement iterations: {result.refinement_count}")
    else:
        print("No results returned.")


asyncio.run(main())
