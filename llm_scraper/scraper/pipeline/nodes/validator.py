import json

from scraper.core.entities.responses import ScrapedResponse, ValidatorResponse
from scraper.core.entities.state import PipelineState
from scraper.pipeline.prompts.validator import (
    build_validator_user_prompt,
    get_validator_prompt,
)
from scraper.providers.factory import get_provider


async def validator_node(state: PipelineState) -> dict:
    config = state["config"]
    query = state["query"]
    retry_count = state["retry_count"]

    # pick the response to validate
    # if in chunks mode, validate the merged response
    # if single pass, validate current_response
    response_to_validate: ScrapedResponse = state["current_response"]

    if response_to_validate is None:
        return {
            "is_valid": False,
            "feedback": "No response to validate.",
            "retry_count": retry_count + 1,
        }

    # if extraction already failed at parsing, no point in validating
    if not response_to_validate.is_valid:
        return {
            "is_valid": False,
            "feedback": response_to_validate.explanation,
            "retry_count": retry_count + 1,
        }

    # if refinement is disabled, skip validation and accept the response
    if not config.refinement:
        return {
            "is_valid": True,
            "feedback": None,
            "final_response": response_to_validate,
            "retry_count": retry_count,
        }

    llm = get_provider(config)
    system_prompt = get_validator_prompt()
    user_prompt = build_validator_user_prompt(
        query=query, scraped_data=response_to_validate.scraped_data
    )

    raw = await llm.ainvoke(user_prompt=user_prompt, system_prompt=system_prompt)

    validator_response = _parse_validator_response(raw)

    updated_response = response_to_validate.model_copy(
        update={
            "is_valid": validator_response.is_valid,
            "feedback": validator_response.explanation,
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
