from abc import ABC, abstractmethod
from typing import Tuple
from scraper_manager.application.entities.responses import ScrapedResponse
from pydantic_ai.usage import Usage
from scraper_manager.application.entities.extractor_settings import DataExtractorSettings

class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, query: str, *,
                        html_content: str,
                        settings: DataExtractorSettings = None,
                        html_path: str = None,
                        is_local: bool = False,
                        refinement: bool = True,
                        selfconsistency: bool = False,
                        separated_selfconsistency: bool = False,
                        cot: bool = True,
                        output_format: dict) -> Tuple[ScrapedResponse, Usage]:
        
        raise NotImplementedError()