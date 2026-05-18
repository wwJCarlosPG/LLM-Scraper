from abc import ABC, abstractmethod


class CleanerPort(ABC):
    @abstractmethod
    def clean(self, html: str, context_length: int) -> str:
        raise NotImplementedError()

    @abstractmethod
    def light_clean(self, html: str) -> str:
        raise NotImplementedError()

    @abstractmethod
    def split(self, html: str, chunk_size: int) -> list[str]:
        raise NotImplementedError()

    @abstractmethod
    def fetch(self, url: str) -> str:
        raise NotImplementedError()
