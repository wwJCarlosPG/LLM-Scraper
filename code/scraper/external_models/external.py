import os
import json
from typing import Literal
from typing import Annotated
from dotenv import load_dotenv
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
    api_key: str

class ExternalResponse(BaseModel):
    explanation: str = Field(
        description="Detailed reasoning or context provided by the system explaining the extracted data or process."
    )
    scraped_data: list[dict[str, str]] = Field(
        description="A list of extracted key-value pairs from the provided source, representing structured data such as product details, article information, or other relevant content.",
        alias='final_answer'
    )

class ExternalAPIMessage(TypedDict):
    role: str
    content: str

class ExternalAPIChoice(TypedDict):
    message: ExternalAPIMessage
    # text: ExternalAPIMessage
    # aqui poner text tambien y hacerlos los dos opcionales, porque algunas API tienen message y otras tienen text

class ExternalAPIResponse(TypedDict):
    choices: list[dict]
    usage: dict[str, int]
    choices: list[ExternalAPIChoice]

_external_response_type_adapter = TypeAdapter(ExternalAPIResponse)

def get_content_and_usage(response: ExternalAPIResponse):
    content = response['choices'][0]['message']['content']
    usage = response['usage']
    return content, usage


class MessageRequest(BaseModel):
    role: str = Literal['user','system']
    content: str


class ExternalRequest(BaseModel):
    model_name: str = Field(alias='model', default='custom_model')
    temperature: float = 0.7
    max_tokens: int = 1000
    messages: list[MessageRequest] = []



class ExternalModel(Model):
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
        return self.model_name

class ExternalAgentModel(AgentModel):

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
        """_summary_

        Args:
            message (list[ModelMessage]): _description_
            model_settings (ModelSettings): _description_
        """
        request: ExternalRequest = ExternalRequest()
        for message in messages:
            for part in message.parts:
                if part.part_kind == 'system-prompt':
                    request.messages.append(MessageRequest(role='system',content=part.content))
                elif part.part_kind == 'user-prompt':
                    request.messages.append(MessageRequest(role='user',content=part.content))

        request.model_name = self.model_name
        request.temperature = 0.7
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
            timeout=60.0
        ) as response:
            if response.status_code != 200:
                print("STATUS CODE != 200")
                await response.aread()
                raise UnexpectedModelBehavior(f'Unexpected response from {self.endpoint} {response.status_code}: {response.text}')
            yield response
        