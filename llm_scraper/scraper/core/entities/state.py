from typing_extensions import TypedDict

from scraper.core.entities.config import PipelineConfig
from scraper.core.entities.responses import ScrapedResponse


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
    partial_responses: list[ScrapedResponse]

    # Output
    is_valid: bool
    final_response: ScrapedResponse | None
