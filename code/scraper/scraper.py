from abc import ABC
from abc import abstractmethod
from pydantic_ai import Agent, Tool
from dataset_work.html_cleaner import HTML_Cleaner
# from code.scraper.prompts.prompts import SIMPLE_SYSTEM_PROMPT

class AdaptativeScraper(ABC):
    def __init__(self, model_name: str):
        super().__init__()
        self.model = model_name

    @abstractmethod
    def run(self, input: str, html: str):
        """Scrap an static HTML based in the natural language input 

        Args:
            input (str): Natural language query
            html (str): Raw HTML
        """
        pass
    
    @staticmethod
    def clean_html(path, tags: list[str], is_local: bool = False):
        """
        Cleans the specified HTML by removing the provided tags.

        This method processes an HTML document, identified by either a local file path or a URL, 
        and removes the specified tags. If the `path` parameter is a URL, set `is_local` to `False`. 
        Conversely, if `path` points to a local file, set `is_local` to `True`.

        Args:
            path (str): The path to the HTML document. Can be a URL or a local file path.
            tags (list[str]): A list of HTML tags to be removed from the document.
            is_local (bool, optional): Indicates whether the `path` is a local file. 
                Defaults to `False` (assuming the `path` is a URL).

        Returns:
            str: The cleaned HTML content with the specified tags removed.
        """
        return HTML_Cleaner.clean_without_download(path, tags, is_local)