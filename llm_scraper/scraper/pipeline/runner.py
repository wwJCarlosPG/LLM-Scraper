from scraper.core.entities.config import PipelineConfig
from scraper.core.entities.responses import ScrapedResponse
from scraper.core.entities.state import PipelineState
from scraper.pipeline.graph import build_graph


async def run(
    *,
    query: str,
    output_format: dict[str, str],
    config: PipelineConfig,
    html: str | None = None,
    html_url: str | None = None,
) -> ScrapedResponse:
    if html is None and html_url is None:
        raise ValueError("Either html or html_url must be provided.")

    initial_state: PipelineState = {
        "query": query,
        "html": html,
        "html_url": html_url,
        "output_format": output_format,
        "config": config,
        "cleaned_html": None,
        "chunks": [],
        "partial_responses": [],
        "current_response": None,
        "feedback": None,
        "retry_count": 0,
        "is_valid": False,
        "final_response": None,
    }

    graph = build_graph()
    final_state = await graph.ainvoke(initial_state)

    return final_state["final_response"] or final_state["current_response"]
