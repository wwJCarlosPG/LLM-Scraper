from typing import TypedDict
from scraper_manager.application.entities.responses import ValidatorResponse

class BasedAgentValidatorSettings(TypedDict):
    response_format =  {"type": "json_object", "schema": ValidatorResponse.model_json_schema()}
    timeout: float = 60.0
    temperature: float = 0.5
    max_tokens: int = 1000