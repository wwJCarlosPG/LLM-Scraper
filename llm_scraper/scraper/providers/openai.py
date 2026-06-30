import logging

from langsmith import traceable
from openai import AsyncOpenAI, OpenAI

from scraper.core.entities.config import ProviderConfig
from scraper.core.entities.token_usage import TokenUsage
from scraper.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = OpenAI(api_key=self.api_key)
        self._async_client = AsyncOpenAI(api_key=self.api_key)

    @traceable(name="OpenAIProvider.invoke", run_type="llm")
    def invoke(self, user_prompt: str, system_prompt: str) -> tuple[str, TokenUsage]:
        response = self._client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=self.temperature,
        )
        usage = TokenUsage(
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return response.choices[0].message.content, usage

    @traceable(name="OpenAIProvider.ainvoke", run_type="llm")
    async def ainvoke(
        self, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        response = await self._async_client.chat.completions.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        usage = TokenUsage(
            input_tokens=response.usage.prompt_tokens if response.usage else 0,
            output_tokens=response.usage.completion_tokens if response.usage else 0,
        )
        return response.choices[0].message.content, usage
