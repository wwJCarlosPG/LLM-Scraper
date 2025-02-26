from abc import ABC, abstractmethod

class BaseHTMLCleaner(ABC):
    
    @abstractmethod
    def clean_by_tag(html_content: str, tags_to_remove: list[str], context_length: int = 0, level: int = 3) -> str:
        raise NotImplementedError() 
    
    @abstractmethod
    def split_html(html_content: str, chunk_size: int) -> list[str]:
        raise NotImplementedError()
    
    @abstractmethod
    def get_html_content(url: str):
        raise NotImplementedError()