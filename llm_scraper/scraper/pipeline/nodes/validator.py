import json
from logging import getLogger

from scraper.core.entities.responses import ScrapedResponse, ValidatorResponse
from scraper.core.entities.state import PipelineState
from scraper.core.entities.token_usage import TokenUsage
from scraper.pipeline.prompts.validator import (
    build_validator_user_prompt,
    get_chunk_validator_prompt,
    get_validator_prompt,
)
from scraper.providers.factory import get_provider

logger = getLogger(__name__)


async def validator_node(state: PipelineState) -> dict:
    config = state["config"]
    query = state["query"]
    retry_count = state["retry_count"]
    chunks = state["chunks"]
    partial_responses = state.get("partial_responses") or []
    cleaned_html = state["cleaned_html"]

    logger.info(f"[validator] validating iteration {retry_count + 1}")

    if chunks and partial_responses:
        return await _validate_chunks(
            state, query, chunks, partial_responses, retry_count, config
        )
    else:
        return await _validate_full(state, query, cleaned_html, retry_count, config)


async def _validate_chunks(
    state, query, chunks, partial_responses, retry_count, config
) -> dict:
    """Validates each partial_response against its corresponding chunk."""
    llm = get_provider(config.validator_provider or config.extractor_provider)
    system_prompt = get_chunk_validator_prompt()

    good_partial_responses = []
    bad_chunks = []
    usages: list[TokenUsage] = []

    # zip stops at shortest — partial_responses and chunks should be same length
    for partial_response, chunk in zip(partial_responses, chunks, strict=True):
        if not partial_response.is_valid:
            # already invalid at parsing — mark as bad
            bad_chunks.append(
                (
                    chunk,
                    partial_response.explanation or "Empty or invalid extraction",
                    partial_response.scraped_data,
                )
            )
            continue

        user_prompt = build_validator_user_prompt(
            query=query,
            scraped_data=partial_response.scraped_data,
            content=chunk,
        )
        raw, usage = await llm.ainvoke(
            user_prompt=user_prompt, system_prompt=system_prompt
        )
        usage.role = "validator"
        usages.append(usage)
        validator_response = _parse_validator_response(raw)

        if validator_response.is_valid:
            good_partial_responses.append(partial_response)
        else:
            logger.info(
                f"[validator] chunk failed: {validator_response.explanation[:80]}..."
            )
            bad_chunks.append(
                (chunk, validator_response.explanation, partial_response.scraped_data)
            )

    is_valid = len(bad_chunks) == 0
    logger.info(
        f"[validator] {len(good_partial_responses)} good, {len(bad_chunks)} bad chunks"
    )

    return {
        "partial_responses": good_partial_responses,
        "bad_chunks": bad_chunks,
        "is_valid": is_valid,
        "feedback": None,
        "token_usage": usages,
    }


async def _validate_full(state, query, cleaned_html, retry_count, config) -> dict:
    """Validates current_response against full cleaned_html (no chunks mode)."""
    response_to_validate: ScrapedResponse = state["current_response"]

    if response_to_validate is None:
        logger.warning("[validator] no response to validate")
        return {
            "is_valid": False,
            "feedback": "No response to validate.",
            "retry_count": retry_count + 1,
        }

    if not response_to_validate.is_valid:
        logger.warning("[validator] response already marked invalid at parsing")
        return {
            "is_valid": False,
            "feedback": response_to_validate.explanation,
            "retry_count": retry_count + 1,
        }

    llm = get_provider(config.validator_provider or config.extractor_provider)
    system_prompt = get_validator_prompt()
    user_prompt = build_validator_user_prompt(
        query=query,
        scraped_data=response_to_validate.scraped_data,
        content=cleaned_html or "",
    )

    raw, usage = await llm.ainvoke(user_prompt=user_prompt, system_prompt=system_prompt)
    usage.role = "validator"
    validator_response = _parse_validator_response(raw)

    logger.info(f"[validator] is_valid={validator_response.is_valid}")
    if not validator_response.is_valid:
        logger.info(f"[validator] feedback: {validator_response.explanation[:100]}...")

    updated_response = response_to_validate.model_copy(
        update={
            "is_valid": validator_response.is_valid,
            "feedback": validator_response.explanation,
            "refinement_count": retry_count + 1,
        }
    )

    return {
        "current_response": updated_response,
        "is_valid": validator_response.is_valid,
        "feedback": validator_response.explanation
        if not validator_response.is_valid
        else None,
        "final_response": updated_response if validator_response.is_valid else None,
        "retry_count": retry_count + 1,
        "token_usage": [usage],
    }


def _parse_validator_response(raw: str) -> ValidatorResponse:
    raw = _clean_json_string(raw)
    try:
        data = json.loads(raw)
        return ValidatorResponse(
            explanation=data.get("explanation")
            or "Extracted items do not match source content.",
            is_valid=data.get("is_valid", False),
        )
    except json.JSONDecodeError:
        logger.error(f"[validator] failed to parse response: {raw[:100]}")
        return ValidatorResponse(
            explanation="Retry extraction. Focus only on items explicitly present in the content.",
            is_valid=False,
        )


def _clean_json_string(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[len("```json") :]
    elif raw.startswith("```"):
        raw = raw[len("```") :]
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()
    first = raw.find("{")
    last = raw.rfind("}")
    if first != -1 and last != -1 and last > first:
        raw = raw[first : last + 1]
    elif first != -1:
        raw = raw[first:]
    return raw.strip()
