import operator
from typing import Annotated

from typing_extensions import TypedDict

from scraper.core.entities.config import PipelineConfig
from scraper.core.entities.responses import ScrapedResponse
from scraper.core.entities.token_usage import TokenUsage


def _replace(old, new):
    """Always use the newest value (replace semantics)."""
    return new


class PipelineState(TypedDict):
    # Input
    query: str
    html: str | None
    html_url: str | None
    output_format: dict[str, str]
    config: PipelineConfig

    # Processing
    cleaned_html: str | None
    chunks: list[str]
    current_response: ScrapedResponse | None
    feedback: str | None
    retry_count: int
    partial_responses: Annotated[list[ScrapedResponse], _replace]
    bad_chunks: Annotated[list[tuple[str, str, list[dict]]], _replace]

    # Token usage accumulated across all nodes
    token_usage: Annotated[list[TokenUsage], operator.add]

    # Output
    is_valid: bool
    final_response: ScrapedResponse | None
