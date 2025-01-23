import os
import json
from typing import Literal
from pydantic import TypeAdapter
from dataclasses import dataclass
from pydantic_ai.usage import Usage
from pydantic import BaseModel, Field
from typing_extensions import TypedDict
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models import Model, AgentModel
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import ModelMessage, ModelResponse
from httpx import AsyncClient as AsyncHTTPClient, Response as HTTPResponse

@dataclass
class ApiKeyAuth:
    """Handles API authentication by storing an API key.

    Attributes:
        api_key (str): The API key used for authenticating requests.
    """
    api_key: str

class ExternalAPIMessage(TypedDict):
    """Represents a message structure in the external API response.

    Attributes:
        role (str): The role of the message (e.g., 'user', 'system').
        content (str): The content of the message.
    """
    role: str
    content: str

class ExternalAPIChoice(TypedDict):
    """Represents a choice object in the external API response.

    Attributes:
        message (ExternalAPIMessage): A message dictionary containing role and content.
    """
    message: ExternalAPIMessage

class ExternalAPIResponse(TypedDict):
    """Defines the overall structure of an external API response.

    Attributes:
        choices (list[ExternalAPIChoice]): A list of possible response choices.
        usage (dict[str, int]): Token usage statistics in the response.
    """
    choices: list[dict]
    usage: dict[str, int]
    choices: list[ExternalAPIChoice]

_external_response_type_adapter = TypeAdapter(ExternalAPIResponse)

def get_content_and_usage(response: ExternalAPIResponse):
    """Extracts the message content and token usage from the API response.

    Args:
        response (ExternalAPIResponse): The response received from the external API.

    Returns:
        tuple[str, dict]: The extracted message content and usage statistics.

    Example:
        content, usage = get_content_and_usage(api_response)
    """
    content = response['choices'][0]['message']['content']
    usage = response['usage']
    return content, usage


class MessageRequest(BaseModel):
    """Represents a request message to the external API.

    Attributes:
        role (str): The role of the message (either 'user' or 'system').
        content (str): The content of the message.
    """
    role: str = Literal['user','system']
    content: str


class ExternalRequest(BaseModel):
    """Defines the structure for requests to the external API.

    Attributes:
        model_name (str): The name of the model to use.
        temperature (float): Sampling temperature for response generation.
        max_tokens (int): Maximum number of tokens to generate.
        messages (list[MessageRequest]): A list of conversation messages.
    """
    model_name: str = Field(alias='model', default='custom_model')
    temperature: float = 0.7
    max_tokens: int = 1000
    messages: list[MessageRequest] = []



class ExternalModel(Model):
    """Represents an external model that interacts with an API.

    Args:
        api_key (str | None): API key for authentication.
        model_name (str): The name of the model to be used.
        endpoint (str): The API endpoint URL.
        env_alias (str): The environment variable alias to retrieve the API key.
        http_client (AsyncHTTPClient | None): HTTP client for async requests.

    Raises:
        Exception: If the API key is not provided or set in the environment variable.

    Attributes:
        auth (ApiKeyAuth): API authentication instance.
        model_name (str): The name of the model.
        endpoint (str): The API endpoint URL.
        http_client (AsyncHTTPClient): HTTP client for handling API requests.
    """
    def __init__(self, *,
                 api_key: str | None,  
                 model_name: str,
                 endpoint: str,
                 env_alias: str,
                 http_client: AsyncHTTPClient | None 
                 ):
        
        super().__init__()
        if api_key == None:
            if env_api_key := os.getenv(env_alias):
                api_key = env_api_key
            else:
                raise(f'API key must be provided or set in the {env_alias} environment variable')
        
        self.auth = ApiKeyAuth(api_key=api_key)
        self.model_name = model_name
        self.endpoint = endpoint
        self.http_client = http_client

    async def agent_model(self,
    *,
    function_tools: list[ToolDefinition],
    allow_text_result: bool,
    result_tools: list[ToolDefinition]) -> AgentModel:
        """Creates an instance of the ExternalAgentModel.

        Args:
            function_tools (list[ToolDefinition]): A list of function tools.
            allow_text_result (bool): Flag to allow text-based responses.
            result_tools (list[ToolDefinition]): Tools used to process results.

        Returns:
            AgentModel: An instance of ExternalAgentModel.
        """
        return ExternalAgentModel(
            function_tools = function_tools,
            allow_text_result = allow_text_result,
            result_tools = result_tools,
            endpoint = self.endpoint,  
            model_name = self.model_name,
            http_client= self.http_client,
            auth = self.auth
        )
    
    def name(self):
        """Returns the model name."""
        return self.model_name

class ExternalAgentModel(AgentModel):
    """Handles interactions with the external AI model.

    Args:
        http_client (AsyncHTTPClient): The asynchronous HTTP client for requests.
        model_name (str): The name of the AI model.
        endpoint (str): The API endpoint URL.
        auth (ApiKeyAuth): API authentication details.
        function_tools (list[ToolDefinition]): List of function tools.
        allow_text_result (bool): Whether text results are allowed.
        result_tools (list[ToolDefinition]): List of tools for processing results.

    Attributes:
        http_client (AsyncHTTPClient): The HTTP client.
        model_name (str): The AI model name.
        endpoint (str): The API endpoint.
        auth (ApiKeyAuth): Authentication details.
    """

    def __init__(self,*,
                 http_client: AsyncHTTPClient,   # pa que yo quiero el AsyncHTTPClient
                 model_name: str,
                 endpoint: str,
                 auth: ApiKeyAuth,
                 function_tools: list[ToolDefinition],
                 allow_text_result: bool,
                 result_tools: list[ToolDefinition]):
        
        super().__init__()
        self.http_client = http_client
        self.model_name = model_name
        self.endpoint = endpoint
        self.auth = auth
        self.function_tools = function_tools
        self.allow_text_result = allow_text_result
        self.result_tools = result_tools

    async def request(
    self,
    messages: list[ModelMessage],
    model_settings: ModelSettings | None,
) -> tuple[ModelResponse, Usage]:
        """Sends a request to the external AI model and retrieves the response.

        Args:
            messages (list[ModelMessage]): Messages to send.
            model_settings (ModelSettings | None): Model configuration settings.

        Returns:
            tuple[ModelResponse, Usage]: The model response and token usage statistics.
        """
        async with self._make_request(messages, model_settings) as http_response:
            response = _external_response_type_adapter.validate_json(await http_response.aread(), strict=False)
        
        text_response, usage_response = get_content_and_usage(response)
        
        usage = Usage(
            total_tokens=usage_response['total_tokens'],
            request_tokens=usage_response['prompt_tokens'],
            response_tokens=usage_response['completion_tokens']
        )
        model_response = ModelResponse.from_text(text_response)
        return model_response, usage

    @asynccontextmanager
    async def _make_request(
            self,
            messages: list[ModelMessage],
            model_settings: ModelSettings
    ) -> AsyncIterator[HTTPResponse]:
        """Performs an asynchronous request to the external API.

        Args:
            messages (list[ModelMessage]): List of messages to send.
            model_settings (ModelSettings): Model configuration settings.

        Yields:
            HTTPResponse: The response from the API.
        """
        request: ExternalRequest = ExternalRequest()
        for message in messages:
            for part in message.parts:
                if part.part_kind == 'system-prompt':
                    request.messages.append(MessageRequest(role='system',content=part.content))
                elif part.part_kind == 'user-prompt':
                    request.messages.append(MessageRequest(role='user',content=part.content))

        request.model_name = self.model_name
        request.temperature = model_settings['temperature']
        request.max_tokens = model_settings['max_tokens']
        request_json = request.model_dump_json(by_alias=True)

        headers = {
            "Authorization": f"Bearer {self.auth.api_key}",
            "Content-Type": "application/json",
        }

        async with self.http_client.stream(
            'POST',
            self.endpoint,
            content=request_json,
            headers=headers,
            timeout=30.0
        ) as response:
            if response.status_code != 200:
                print("STATUS CODE != 200")
                await response.aread()
                raise UnexpectedModelBehavior(f'Unexpected response from {self.endpoint} {response.status_code}: {response.text}')
            yield response
        