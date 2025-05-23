from typing import TypedDict
from core.entities.responses import ValidatorResponse

class BasedAgentValidatorSettings(TypedDict):
    """
    Type definition for settings used by the BasedAgentValidator.

    This TypedDict defines the structure and types for configuration settings
    specific to the BasedAgentValidator, such as response format, timeout,
    temperature, and maximum token length.

    Attributes:
        response_format (dict):
            A dictionary defining the desired format for the agent's response.
            It should include the "type" (e.g., "json_object") and the "schema"
            (e.g., `ValidatorResponse.model_json_schema()`) to ensure the response
            is structured according to the expected format.

        timeout (float):
            The maximum amount of time (in seconds) to wait for the agent to
            generate a response. A higher value allows more time for complex
            validations, while a lower value prevents indefinite waiting. Defaults to 60.0.

        temperature (float):
            Controls the randomness and creativity of the agent's response.
            Values range from 0.0 (more deterministic) to 1.0 (more random).
            Defaults to 0.5.

        max_tokens (int):
            The maximum number of tokens (words or subwords) that the agent is
            allowed to generate in its response. This limits the length and
            verbosity of the agent's output. Defaults to 1000.
    """
    response_format =  {"type": "json_object", "schema": ValidatorResponse.model_json_schema()}
    timeout: float = 60.0
    temperature: float = 0.5
    max_tokens: int = 1000