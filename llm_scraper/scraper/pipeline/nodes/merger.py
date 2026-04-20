from scraper.core.entities.responses import ScrapedResponse
from scraper.core.entities.state import PipelineState


async def merger_node(state: PipelineState) -> dict:
    partial_responses = state["partial_responses"]

    if not partial_responses:
        return {}

    merged = _merge(partial_responses)
    return {"current_response": merged, "partial_responses": []}


def _merge(responses: list[ScrapedResponse]) -> ScrapedResponse:
    if not responses:
        return ScrapedResponse(scraped_data=[], is_valid=False)

    all_items = []
    explanations = []
    is_valid = True
    refinement_count = 0

    for response in responses:
        all_items.extend(response.scraped_data)
        explanations.append(response.explanation)
        refinement_count = max(refinement_count, response.refinement_count)
        if not response.is_valid:
            is_valid = False

    deduplicated = _deduplicate(all_items)

    return ScrapedResponse(
        explanation=" | ".join(explanations),
        scraped_data=deduplicated,
        is_valid=is_valid,
        refinement_count=refinement_count,
    )


def _deduplicate(items: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for item in items:
        try:
            key = frozenset(item.items())
            if key not in seen:
                seen.add(key)
                result.append(item)
        except TypeError:
            result.append(item)
    return result
