from abc import ABC, abstractmethod

from scraper.core.entities.token_usage import TokenUsage


class LLMPort(ABC):
    @abstractmethod
    def invoke(self, user_prompt: str, system_prompt: str) -> tuple[str, TokenUsage]:
        raise NotImplementedError()

    @abstractmethod
    async def ainvoke(
        self, user_prompt: str, system_prompt: str
    ) -> tuple[str, TokenUsage]:
        raise NotImplementedError()
