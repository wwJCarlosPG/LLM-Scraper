from typing import TypedDict
from scraper_manager.application.entities.responses import ScrapedResponse, Response

class DataExtractorSettings(TypedDict):
    """
    A type definition for the settings used in the DataExtractor.

    Attributes:
        temperature (float):
            The degree of randomness or creativity in the model's response.
            - A higher value (e.g., 0.9) results in more creative and diverse outputs.
            - A lower value (e.g., 0.2) makes the output more focused and deterministic.

        max_tokens (int):
            The maximum number of tokens (words or characters, depending on the model)
            that the model is allowed to generate in response.
            - Higher values allow for longer responses.
            - Lower values restrict the response length to be more concise.

        timeout (float):
            The maximum amount of time (in seconds) to wait for the model to generate a response.
            - A higher value allows more time for the model to process complex queries.
            - A lower value prevents the system from waiting indefinitely for a response.

        response_format (dict):
            The desired format for the model's response. This should be a dictionary
            specifying the type of response (e.g., "json_object") and the schema
            (e.g., `ScrapedResponse.model_json_schema()` or `Response.model_json_schema()`).
            This helps ensure that the model's output is structured in a predictable way.
    """
    temperature: float = 0.3
    max_tokens: int = 10000
    timeout: float = 60.0
    response_format = {"type": "json_object", "schema": ScrapedResponse.model_json_schema()} | {'type': 'json_object', 'schema': Response.model_json_schema()}