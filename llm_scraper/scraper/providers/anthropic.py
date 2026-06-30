import logging

import anthropic
from langsmith import traceable

from scraper.core.entities.config import ProviderConfig
from scraper.core.entities.token_usage import TokenUsage
from scraper.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    def __init__(self, config: ProviderConfig):
        super().__init__(config)
        self._client = anthropic.Anthropic(api_key=self.api_key)
        self._async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

    @traceable(name="AnthropicProvider.invoke", run_type="llm")
    def invoke(self, user_prompt: str, system_prompt: str) -> tuple[str, TokenUsage]:
        message = self._client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        usage = TokenUsage(
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
        return message.content[0].text, usage

    @traceable(name="AnthropicProvider.ainvoke", run_type="llm")
    async def ainvoke(
        self, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        message = await self._async_client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        usage = TokenUsage(
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
        return message.content[0].text, usage
