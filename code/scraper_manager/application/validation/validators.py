from httpx import AsyncClient
from pydantic_ai import RunContext
from pydantic_ai.agent import Agent
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from scraper_manager.core.utils import find_majority
from scraper_manager.core.exceptions import InvalidResultDuringValidation
from scraper_manager.infrastructure.integration.external_models import ExternalModel
from scraper_manager.application.extraction.responses import ScrapedResponse, Response
from scraper_manager.infrastructure.prompts.prompts import get_validator_system_prompt, structure_query_to_validate

class ValidatorResponse(BaseModel):
    """
    Represents the response of a validation process that evaluates 
    whether extracted data meets the given user query requirements.

    Attributes:
        explanation (str): A detailed justification of the validation outcome, 
            describing why the extracted data is considered correct or incorrect 
            based on the provided HTML content and query.
        is_valid (bool): A boolean flag indicating the validation result.
            - True if the extracted data is accurate and satisfies the query.
            - False if the extracted data does not meet the query requirements.
    """
    explanation: str = Field(
        description="A detailed explanation justifying the validity or invalidity of the extracted data based on the query and HTML content."
    )
    is_valid: bool = Field(
        description="A boolean indicating whether the extracted data is correct (True) or incorrect (False) based on the validation."
    )

class BaseValidator(ABC):
    """
    Abstract base class for validators that assess the accuracy of extracted data 
    against a user-provided query.

    Methods:
        validate(user_query: str, html_content: str, response_to_validate: str) -> Union[ValidatorResponse, ScrapedResponse]:
            Abstract method to validate extracted data against a query.
    """

    @abstractmethod
    def validate(self, response_to_validate) -> ScrapedResponse:
        """
        Validate the extracted data against the provided user query.
        
        Args:
            response_to_validate (str): The data to be validated, typically in JSON format.

        Returns:
            Union[ValidatorResponse, ScrapedResponse]: 
            - `ValidatorResponse`: Contains validation status and an explanation.
            - `ScrapedResponse`: Represents a successful extraction result.
        """
        raise NotImplementedError()
    
    def self_validator(self, data: str):
        """
        Validates the provided JSON string by converting it to a `ValidatorResponse` object.

        Args:
            data (str): JSON formatted string containing validation data.

        Returns:
            ValidatorResponse: A validated response object.
        """
        response = ValidatorResponse.model_validate_json(data)
        return response
     
class DefaultValidator(BaseValidator):
    """
    Default implementation of `BaseValidator` that validates scraped data 
    using the `ScrapedResponse` model.

    Methods:
        validate(data: str) -> Union[ValidatorResponse, ScrapedResponse]:
            Validates the given data and returns a `ScrapedResponse` object.
    """
    def __init__(self):
        """
        Initializes the DefaultValidator instance.
        """
        super().__init__()

    def validate(self, data: str) -> ScrapedResponse:
        """
        Validate the extracted data by parsing it into a `ScrapedResponse` object.

        Args:
            data (str): JSON formatted string containing the scraped response.

        Returns:
            ScrapedResponse: The parsed and validated scraped data.
        """
        validated_response = Response.model_validate_json(data)
        # return validated_response
        # validated_response = ScrapedResponse.model_validate_json(data)
        return validated_response
    

class BasedAgentValidator(BaseValidator):
    """
    An AI-based validator that uses an external model to assess data accuracy 
    against the user query and HTML content.

    Attributes:
        model_name (str): The name of the model to be used for validation.
        endpoint (str, optional): API endpoint for external model calls.
        api_key (str, optional): API key for authentication.
        env_alias (str, optional): Environment variable alias for the API key.
        agent (Agent): The agent responsible for running validation queries.

    Methods:
        validate(run_context: RunContext, response_to_validate: str) -> Union[ValidatorResponse, ScrapedResponse]:
            Performs validation using an AI model based on the given user query.
    """

    def __init__(self, *,
                 model_name:str,
                 endpoint: str | None = None,
                 api_key: str | None = None,
                 env_alias: str | None = None):
        """
        Initializes the BasedAgentValidator with the provided parameters.

        Args:
            model_name (str): The name of the AI model used for validation.
            endpoint (str, optional): The API endpoint of the validation service.
            api_key (str, optional): API key for authentication.
            env_alias (str, optional): Environment variable alias for retrieving API keys.

        Raises:
            ValueError: If no valid API key is provided or found in environment variables.
        """
        
        async_client = AsyncClient()
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client),
                system_prompt = get_validator_system_prompt(),
            )
            self.agent.result_validator(self.self_validator)
        
    async def validate(self, run_context: RunContext, response_to_validate: str) -> ScrapedResponse:
        """
        Validates the extracted data using an AI-based agent.

        Args:
            run_context (RunContext): The context of the current run, containing user messages.
            response_to_validate (str): JSON formatted response to be validated.

        Returns:
            ScrapedResponse: 
            - A valid scraped response if validation is successful.

        """
        try:
            selfconsistency = run_context.deps
            if selfconsistency:
                scraped_response_collection = Response.model_validate_json(response_to_validate, strict=False)
                scraped_response = find_majority(scraped_response_collection.responses)
            else:
                scraped_response = ScrapedResponse.model_validate_json(response_to_validate,strict=False)
            messages = run_context.messages
            request_parts = [m.parts for m in messages if m.kind == 'request']
            user_query = [request.content for request in request_parts[len(request_parts) - 1] if request.part_kind == 'user-prompt']
            query = structure_query_to_validate(user_query, response_to_validate)
            validator_response = await self.agent.run(query) 
            scraped_response.feedback = validator_response.data.explanation
            scraped_response.is_valid = validator_response.data.is_valid
            return scraped_response
        except Exception:
            raise InvalidResultDuringValidation(message="An error ocurred during validation process.")

