import json
from logging import getLogger

from scraper.core.entities.config import PipelineConfig
from scraper.core.entities.responses import ScrapedResponse
from scraper.core.entities.state import PipelineState
from scraper.pipeline.prompts.extractor import (
    build_refinement_user_prompt,
    build_user_prompt,
    get_extractor_prompt,
)
from scraper.providers.factory import get_provider

logger = getLogger(__name__)


async def extractor_node(state: PipelineState) -> dict:
    config = state["config"]
    query = state["query"]
    output_format = state["output_format"]
    chunks = state["chunks"]
    cleaned_html = state["cleaned_html"]
    bad_chunks = state.get("bad_chunks") or []
    feedback = state.get("feedback")
    retry_count = state["retry_count"]

    logger.info(f"[extractor] iteration {retry_count + 1}")

    llm = get_provider(config.provider)
    system_prompt = get_extractor_prompt(
        output_format=output_format,
        cot=config.cot,
        self_consistency=config.self_consistency,
    )

    in_chunks = len(chunks) > 0

    if in_chunks:
        if bad_chunks:
            # retry mode: only process chunks that failed validation
            logger.info(
                f"[extractor] retry mode: processing {len(bad_chunks)} bad chunks"
            )
            new_partial_responses = []
            for chunk_text, chunk_feedback, previous_scraped_data in bad_chunks:
                user_prompt = build_refinement_user_prompt(
                    query=query,
                    content=chunk_text,
                    feedback=chunk_feedback,
                    previous_extraction=previous_scraped_data,
                )
                response = await _get_response(llm, user_prompt, system_prompt, config)
                new_partial_responses.append(response)

            # append new responses to the existing good ones
            existing = state.get("partial_responses") or []
            return {
                "partial_responses": existing + new_partial_responses,
                "bad_chunks": [],
            }

        else:
            # first pass: process all chunks
            logger.info(f"[extractor] first pass: processing {len(chunks)} chunks")
            partial_responses = []
            for chunk in chunks:
                user_prompt = build_user_prompt(query, chunk)
                response = await _get_response(llm, user_prompt, system_prompt, config)
                partial_responses.append(response)

            return {"partial_responses": partial_responses, "bad_chunks": []}

    else:
        # no chunks: full content, include global feedback if retry
        if feedback:
            current_response = state.get("current_response")
            previous_extraction = (
                current_response.scraped_data if current_response else []
            )
            user_prompt = build_refinement_user_prompt(
                query=query,
                content=cleaned_html,
                feedback=feedback,
                previous_extraction=previous_extraction,
            )
        else:
            user_prompt = build_user_prompt(query, cleaned_html)

        response = await _get_response(llm, user_prompt, system_prompt, config)
        logger.info(f"[extractor] extracted {len(response.scraped_data)} items")
        return {"current_response": response, "partial_responses": []}


async def _get_response(
    llm, user_prompt: str, system_prompt: str, config: PipelineConfig
) -> ScrapedResponse:
    raw = await llm.ainvoke(user_prompt=user_prompt, system_prompt=system_prompt)
    response = _parse_response(raw, config.self_consistency)
    return response


def _parse_response(raw: str, self_consistency: bool) -> ScrapedResponse:
    raw = _clean_json_string(raw)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"[extractor] failed to parse response: {e}")
        return ScrapedResponse(
            explanation=f"Failed to parse LLM response: {e}",
            scraped_data=[],
            is_valid=False,
        )

    if self_consistency:
        return _merge_self_consistency(data)

    return ScrapedResponse(
        explanation=data.get("explanation", "No explanation"),
        scraped_data=[
            item for item in data.get("scraped_data", []) if isinstance(item, dict)
        ],
        is_valid=True,
    )


def _merge_self_consistency(data: dict) -> ScrapedResponse:
    responses = data.get("responses", [])
    if not responses:
        return ScrapedResponse(scraped_data=[], is_valid=False)

    all_items = [
        item
        for r in responses
        for item in r.get("scraped_data", [])
        if isinstance(item, dict)
    ]
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
