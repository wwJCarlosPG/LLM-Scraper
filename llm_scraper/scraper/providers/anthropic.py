import logging

import anthropic
from langsmith import traceable

from scraper.core.entities.config import ProviderConfig
from scraper.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    def __init__(self, config: ProviderConfig, max_tokens: int = 4096):
        super().__init__(config, max_tokens)
        self._client = anthropic.Anthropic(api_key=self.api_key)
        self._async_client = anthropic.AsyncAnthropic(api_key=self.api_key)

    @traceable(name="AnthropicProvider.invoke", run_type="llm")
    def invoke(self, user_prompt: str, system_prompt: str) -> str:
        message = self._client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text

    @traceable(name="AnthropicProvider.ainvoke", run_type="llm")
    async def ainvoke(self, user_prompt: str, system_prompt: str) -> str:
        message = await self._async_client.messages.create(
            model=self.model_name,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return message.content[0].text
