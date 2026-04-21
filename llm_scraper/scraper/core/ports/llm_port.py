from abc import ABC, abstractmethod


class LLMPort(ABC):
    @abstractmethod
    def invoke(self, user_prompt: str, system_prompt: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    async def ainvoke(self, user_prompt: str, system_prompt: str) -> str:
        raise NotImplementedError()
