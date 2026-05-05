from unittest.mock import AsyncMock, patch

import pytest

from scraper.core.entities.config import PipelineConfig, ProviderConfig
from scraper.pipeline.runner import run

FIXTURE_PATH = "tests/fixtures/article.html"

with open(FIXTURE_PATH) as f:
    FIXTURE_HTML = f.read()


def make_config() -> PipelineConfig:
    return PipelineConfig(
        provider=ProviderConfig(
            provider="gemini", model_name="gemini-2.0-flash", api_key="test-key"
        ),
        cot=True,
        refinement=True,
        max_retries=3,
        use_markdown_conversion=True,
        markdown_converter="trafilatura",
    )


EXTRACTOR_VALID_RESPONSE = """
{
    "explanation": "Found the author and title in the article.",
    "scraped_data": [
        {"title": "Scientists discover new species in Amazon", "author": "John Doe"}
    ]
}
"""
VALIDATOR_VALID_RESPONSE = """
{
    "explanation": "The extracted title and author match the content in the article.",
    "is_valid": true
}
"""

EXTRACTOR_INVALID_RESPONSE = """
{
    "explanation": "Could not find the data.",
    "scraped_data": []
}
"""

VALIDATOR_INVALID_RESPONSE = """
{
    "explanation": "The extracted data is empty, the title and author are missing.",
    "is_valid": false
}
"""


@pytest.mark.asyncio
async def test_happy_path():
    """
    Full pipeline with valid extraction on first attempt.
    Verifies that the pipeline ends in one iteration with correct data.
    """
    with patch(
        "scraper.providers.gemini.GeminiProvider.ainvoke",
        new=AsyncMock(
            side_effect=[
                EXTRACTOR_VALID_RESPONSE,
                VALIDATOR_VALID_RESPONSE,
            ]
        ),
    ):
        result = await run(
            query="Extract the title and author of the article.",
            output_format={"title": "article title", "author": "author name"},
            config=make_config(),
            html=FIXTURE_HTML,
        )

    assert result is not None
    assert result.is_valid is True
    assert len(result.scraped_data) == 1
    assert (
        result.scraped_data[0]["title"] == "Scientists discover new species in Amazon"
    )
    assert result.scraped_data[0]["author"] == "John Doe"
    assert result.refinement_count == 1


@pytest.mark.asyncio
async def test_refinement_path():
    """
    Full pipeline where extractor fails on first attempt and succeeds on second.
    Verifies that feedback is propagated and retry_count increments correctly.
    """
    with patch(
        "scraper.providers.gemini.GeminiProvider.ainvoke",
        new=AsyncMock(
            side_effect=[
                EXTRACTOR_INVALID_RESPONSE,  # extractor attempt 1
                VALIDATOR_INVALID_RESPONSE,  # validator rejects
                EXTRACTOR_VALID_RESPONSE,  # extractor attempt 2
                VALIDATOR_VALID_RESPONSE,  # validator accepts
            ]
        ),
    ):
        result = await run(
            query="Extract the title and author of the article.",
            output_format={"title": "article title", "author": "author name"},
            config=make_config(),
            html=FIXTURE_HTML,
        )

    assert result is not None
    assert result.is_valid is True
    assert len(result.scraped_data) == 1
    assert result.refinement_count == 2


@pytest.mark.asyncio
async def test_max_retries_reached():
    """
    Pipeline exhausts max_retries without valid extraction.
    Verifies that the pipeline stops and returns the last response.
    """
    with patch(
        "scraper.providers.gemini.GeminiProvider.ainvoke",
        new=AsyncMock(
            side_effect=[
                EXTRACTOR_INVALID_RESPONSE,
                VALIDATOR_INVALID_RESPONSE,
                EXTRACTOR_INVALID_RESPONSE,
                VALIDATOR_INVALID_RESPONSE,
                EXTRACTOR_INVALID_RESPONSE,
                VALIDATOR_INVALID_RESPONSE,
            ]
        ),
    ):
        config = make_config()
        config = config.model_copy(update={"max_retries": 3})
        result = await run(
            query="Extract the title and author of the article.",
            output_format={"title": "article title", "author": "author name"},
            config=config,
            html=FIXTURE_HTML,
        )

    assert result is not None
    assert result.is_valid is False


@pytest.mark.asyncio
async def test_refinement_disabled():
    """
    Pipeline with refinement disabled.
    Verifies that the validator accepts the response without LLM call.
    """
    with patch(
        "scraper.providers.gemini.GeminiProvider.ainvoke",
        new=AsyncMock(
            side_effect=[
                EXTRACTOR_VALID_RESPONSE,  # only one call, no validator LLM call
            ]
        ),
    ):
        config = make_config()
        config = config.model_copy(update={"refinement": False})
        result = await run(
            query="Extract the title and author of the article.",
            output_format={"title": "article title", "author": "author name"},
            config=config,
            html=FIXTURE_HTML,
        )

    assert result is not None
    assert result.is_valid is True
    assert len(result.scraped_data) == 1
