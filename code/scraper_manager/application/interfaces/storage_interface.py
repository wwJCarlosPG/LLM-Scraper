from abc import ABC, abstractmethod
class BaseStorage(ABC):

    @abstractmethod
    def save(self, data, path_to_save: str) -> None:
        raise NotImplementedError()