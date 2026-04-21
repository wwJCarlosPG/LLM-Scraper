from abc import ABC, abstractmethod
from typing import Any


class StoragePort(ABC):
    @abstractmethod
    def save(self, data: Any, path: str) -> None:
        raise NotImplementedError()
