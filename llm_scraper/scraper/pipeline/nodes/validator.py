import json
from logging import getLogger

from scraper.core.entities.responses import ScrapedResponse, ValidatorResponse
from scraper.core.entities.state import PipelineState
from scraper.pipeline.prompts.validator import (
    build_validator_user_prompt,
    get_validator_prompt,
)
from scraper.providers.factory import get_provider

logger = getLogger(__name__)


async def validator_node(state: PipelineState) -> dict:
    config = state["config"]
    query = state["query"]
    retry_count = state["retry_count"]
    cleaned_html = state["cleaned_html"]

    # pick the response to validate
    # if in chunks mode, validate the merged response
    # if single pass, validate current_response
    response_to_validate: ScrapedResponse = state["current_response"]

    logger.info(f"[validator] validating iteration {retry_count + 1}")

    if response_to_validate is None:
        logger.warning("[validator] no response to validate")
        return {
            "is_valid": False,
            "feedback": "No response to validate.",
            "retry_count": retry_count + 1,
        }

    # if extraction already failed at parsing, no point in validating
    if not response_to_validate.is_valid:
        logger.warning("[validator] response already marked invalid at parsing")
        return {
            "is_valid": False,
            "feedback": response_to_validate.explanation,
            "retry_count": retry_count + 1,
        }

    # if refinement is disabled, skip validation and accept the response
    if not config.refinement:
        logger.info("[validator] refinement disabled, accepting response")
        return {
            "is_valid": True,
            "feedback": None,
            "final_response": response_to_validate,
            "retry_count": retry_count,
        }

    llm = get_provider(config)
    system_prompt = get_validator_prompt()
    user_prompt = build_validator_user_prompt(
        query=query,
        scraped_data=response_to_validate.scraped_data,
        content=cleaned_html,
    )

    raw = await llm.ainvoke(user_prompt=user_prompt, system_prompt=system_prompt)

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
    }


def _parse_validator_response(raw: str) -> ValidatorResponse:
    raw = _clean_json_string(raw)
    try:
        data = json.loads(raw)
        return ValidatorResponse(
            explanation=data.get("explanation", "No explanation"),
            is_valid=data.get("is_valid", False),
        )
    except json.JSONDecodeError:
        logger.error(f"[validator] failed to parse validator response: {raw[:100]}")
        return ValidatorResponse(
            explanation=f"Failed to parse validator response: {raw}", is_valid=False
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
