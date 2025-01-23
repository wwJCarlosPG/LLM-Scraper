from typing import Union
from httpx import AsyncClient
from pydantic_ai.agent import Agent
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from pydantic_ai import RunContext
from data_manager.external_models.external import ExternalModel
from data_manager.data_extractor.responses import ScrapedResponse
from data_manager.prompts.prompts import get_validator_system_prompt, structure_query_to_validate


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
    @abstractmethod
    def validate(self, user_query: str, html_content: str, response_to_validate: str) -> Union[ValidatorResponse, ScrapedResponse]:
        raise NotImplementedError()
     
class DefaultValidator(BaseValidator):
    def __init__(self):
        super().__init__()

    def validate(self, data: str) -> Union[ValidatorResponse, ScrapedResponse]:
        validated_response = ScrapedResponse.model_validate_json(data)
        return validated_response
    

class BasedAgentValidator(BaseValidator):
    def __init__(self, *,
                 model_name:str,
                 endpoint: str | None = None,
                 api_key: str | None = None,
                 env_alias: str | None = None):
        
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
        
    def self_validator(self, data: str):
        response = ValidatorResponse.model_validate_json(data)
        return response

    async def validate(self, run_context: RunContext, response_to_validate: str) -> Union[ValidatorResponse, ScrapedResponse]:
        messages = run_context.messages
        request_parts = [m.parts for m in messages if m.kind == 'request']
        user_query = [request.content for request in request_parts[len(request_parts) - 1] if request.part_kind == 'user-prompt']
         
        query = structure_query_to_validate(user_query, response_to_validate)
        validator_response = await self.agent.run(query)
        if validator_response.data.is_valid == True:
            return ScrapedResponse.model_validate_json(response_to_validate)
        else:
            return validator_response