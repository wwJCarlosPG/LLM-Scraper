from abc import ABC, abstractmethod

class BaseHTMLCleaner(ABC):
    
    @abstractmethod
    def clean_by_tag(html_content: str, tags_to_remove: list[str], context_length: int = 0, level: int = 3) -> str:
        raise NotImplementedError() 