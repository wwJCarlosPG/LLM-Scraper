import json

from scraper.core.entities.responses import ScrapedResponse
from scraper.core.entities.state import PipelineState
from scraper.pipeline.prompts.extractor import build_user_prompt, get_extractor_prompt
from scraper.providers.factory import get_provider


async def extractor_node(state: PipelineState) -> dict:
    config = state["config"]
    query = state["query"]
    output_format = state["output_format"]
    feedback = state["feedback"]
    chunks = state["chunks"]
    cleaned_html = state["cleaned_html"]

    llm = get_provider(config)
    system_prompt = get_extractor_prompt(
        output_format=output_format,
        cot=config.cot,
        self_consistency=config.self_consistency,
    )
    in_chunks = len(chunks) > 0

    full_query = (
        query
        if (in_chunks or not feedback)
        else f"{query}\n\nFeedback from previous attempt:\n{feedback}"
    )

    if in_chunks:
        partial_responses = []
        for chunk in chunks:
            user_prompt = build_user_prompt(full_query, chunk)
            raw = await llm.ainvoke(
                user_prompt=user_prompt, system_prompt=system_prompt
            )
            response = _parse_response(raw, config.self_consistency)
            partial_responses.append(response)
        return {"partial_responses": partial_responses}
    else:
        user_prompt = build_user_prompt(full_query, cleaned_html)
        raw = await llm.ainvoke(user_prompt=user_prompt, system_prompt=system_prompt)
        response = _parse_response(raw, config.self_consistency)
        return {"current_response": response, "partial_responses": []}


def _parse_response(raw: str, self_consistency: bool) -> ScrapedResponse:
    raw = _clean_json_string(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        return ScrapedResponse(
            explanation=f"Failed to parse LLM response: {e}",
            scraped_data=[],
            is_valid=False,
        )

    if self_consistency:
        return _merge_self_consistency(data)

    return ScrapedResponse(
        explanation=data.get("explanation", "No explanation"),
        scraped_data=data.get("scraped_data", []),
        is_valid=True,
    )


def _merge_self_consistency(data: dict) -> ScrapedResponse:
    responses = data.get("responses", [])
    if not responses:
        return ScrapedResponse(scraped_data=[], is_valid=False)

    all_items = [item for r in responses for item in r.get("scraped_data", [])]
    explanations = [r.get("explanation", "") for r in responses]

    from collections import Counter

    counts = Counter(frozenset(d.items()) for d in all_items)
    majority = [dict(k) for k, v in counts.items() if v >= 2]

    return ScrapedResponse(
        explanation=" | ".join(explanations), scraped_data=majority, is_valid=True
    )


def _clean_json_string(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[len("```json") :]
    elif raw.startswith("```"):
        raw = raw[len("```") :]
    if raw.endswith("```"):
        raw = raw[:-3]
    return raw.strip()
