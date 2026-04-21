"""
Basic extraction example using Gemini as the LLM provider.

This example shows how to extract structured data from a URL
with the default pipeline configuration.
"""

import asyncio
import logging

from dotenv import load_dotenv

from scraper.core.entities.config import PipelineConfig, ProviderConfig
from scraper.pipeline.runner import run

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)

load_dotenv()


async def main():
    result = await run(
        query="Extract all news headlines from the page.",
        output_format={"headline": "news headline text"},
        config=PipelineConfig(
            provider=ProviderConfig(
                provider="gemini",
                model_name="gemini-2.5-flash-lite",
                env_alias="GEMINI_API_KEY",
            ),
            refinement=True,
            cot=True,
            max_retries=2,
        ),
        html_url="https://www.bbc.com",
    )

    if result:
        print(f"Extracted {len(result.scraped_data)} items:")
        for item in result.scraped_data:
            print(f"  - {item}")
        print(f"\nValid: {result.is_valid}")
        print(f"Refinement iterations: {result.refinement_count}")
    else:
        print("No results returned.")


asyncio.run(main())
