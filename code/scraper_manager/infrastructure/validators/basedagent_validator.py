import json
from httpx import AsyncClient
from pydantic_ai import RunContext
from pydantic_ai.agent import Agent
from scraper_manager.infrastructure.utils import find_majority
from scraper_manager.infrastructure.integration.external_models import ExternalModel
from scraper_manager.application.interfaces.validator_interface import BaseValidator
from scraper_manager.application.entities.validator_settings import BasedAgentValidatorSettings
from scraper_manager.application.entities.responses import ScrapedResponse, ValidatorResponse, Response
from scraper_manager.infrastructure.prompts.prompts import get_validator_system_prompt, structure_query_to_validate
from scraper_manager.infrastructure.exceptions.exceptions import InvalidResultDuringValidation, InvalidValidationFormat

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
        self.validator_settings = BasedAgentValidatorSettings(
        temperature=0.5, 
        timeout=60.0, 
        max_tokens=3000, 
        response_format = {
    "type": "json_schema",
    "json_schema": {
        "name": "ValidatorResponse",
        "strict": "true", 
        "schema": ValidatorResponse.model_json_schema()  
    }
}
        # response_format={"type": "json_object", "schema": ValidatorResponse.model_json_schema()} 
)
        async_client = AsyncClient()
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name,
                system_prompt=get_validator_system_prompt()
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client),
                system_prompt = get_validator_system_prompt(),
            )
        self.agent.result_validator(self.self_validate)
        
    def self_validate(self, response_to_validate: str):
        """
        Validates the provided JSON string by converting it to a `ValidatorResponse` object.

        Args:
            data (str): JSON formatted string containing validation data.

        Returns:
            ValidatorResponse: A validated response object.
        """
        try:
            json_response = json.loads(response_to_validate)
        except Exception:
            response_to_validate = response_to_validate.lstrip() 
            if response_to_validate.startswith("```json"):
                response_to_validate = response_to_validate[len("```json"):]  
            elif response_to_validate.startswith("```"):
                response_to_validate = response_to_validate[len("```"):]

            response_to_validate = response_to_validate.rstrip() 
            if response_to_validate.endswith("```"):
                response_to_validate = response_to_validate[:-len("```")]
            response_to_validate = response_to_validate.strip("\n\t")
            start = response_to_validate.find('{')
            reversed_response = response_to_validate[::-1]
            reversed_end = reversed_response.find('}')
            end = len(response_to_validate) - reversed_end - 1 
            response_to_validate[start:end+1]
            if not response_to_validate.startswith('{'):
                response_to_validate = '{' + response_to_validate
            if not response_to_validate.endswith('}'):
                response_to_validate = response_to_validate + '}'
            if response_to_validate.count('"') % 2 != 0:
                response_to_validate = response_to_validate.rstrip('"')
        response = ValidatorResponse.model_validate_json(response_to_validate)
        return response
    
    
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
        # start = response_to_validate.find('{')
        # reversed_response = response_to_validate[::-1]
        # reversed_end = reversed_response.find('}')
        # end = len(response_to_validate) - reversed_end - 1 
        # response_to_validate[start:end+1]

        # response_to_validate = response_to_validate[start:end+1]
        # print(response_to_validate)
        try:
            json_response = json.loads(response_to_validate)
        except Exception:
            response_to_validate = response_to_validate.lstrip() #Quita espacios en blanco al inicio
            if response_to_validate.startswith("```json"):
                response_to_validate = response_to_validate[len("```json"):]  # Elimina "```json" del inicio
            elif response_to_validate.startswith("```"):
                response_to_validate = response_to_validate[len("```"):]

            response_to_validate = response_to_validate.rstrip() #Quita espacios en blanco al final
            if response_to_validate.endswith("```"):
                response_to_validate = response_to_validate[:-len("```")]  # Elimina "```" del final

            response_to_validate = response_to_validate.strip() 
            response_to_validate = response_to_validate.strip("\n\t")
            # response_to_validate = response_to_validate.encode('utf-8').decode('unicode_escape')
            if not response_to_validate.startswith('{'):
                response_to_validate = '{' + response_to_validate
            if not response_to_validate.endswith('}'):
                response_to_validate = response_to_validate + '}'
            if response_to_validate.count('"') % 2 != 0:
                response_to_validate = response_to_validate.rstrip('"')

        try:
            selfconsistency = run_context.deps
            if selfconsistency:
                scraped_response_collection = Response.model_validate_json(response_to_validate, strict=False)
                scraped_response = find_majority(scraped_response_collection.responses)
                # print(scraped_response) 
            else:
                # print(response_to_validate)
                scraped_response = ScrapedResponse.model_validate_json(response_to_validate,strict=False)

            messages = run_context.messages
            request_parts = [m.parts for m in messages if m.kind == 'request']
            user_query = [request.content for request in request_parts[len(request_parts) - 1] if request.part_kind == 'user-prompt']
            query = structure_query_to_validate(user_query, scraped_response.scraped_data)
            try:
                validator_response = await self.agent.run(query, model_settings=self.validator_settings) 
            except Exception as e:
                try:
                    validator_response = await self.agent.run(query, model_settings=self.validator_settings)
                except Exception as e:
                    print("ValidationError: ", e)
                    raise InvalidValidationFormat(message=f'An error ocurred cause the validation format is invalid: {e}.')
            print(validator_response.data)
            scraped_response.feedback = validator_response.data.explanation
            scraped_response.is_valid = validator_response.data.is_valid
            return scraped_response
        except Exception as e:
            # print(response_to_validate)
            print(f"InvalidResultDuringValidation: {e} \nfor response {response_to_validate}" )
            raise InvalidResultDuringValidation(message=f"An error ocurred during validation process: {e}.")

