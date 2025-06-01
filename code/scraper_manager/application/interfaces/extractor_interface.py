from typing import Tuple
from abc import ABC, abstractmethod
from pydantic_ai.usage import Usage
from scraper_manager.core.entities.responses import ScrapedResponse
from scraper_manager.core.entities.extractor_settings import DataExtractorSettings

class BaseExtractor(ABC):
    @abstractmethod
    async def extract(self, query: str, *,
                        html_content: str,
                        settings: DataExtractorSettings = None,
                        context: str, 
                        refinement: bool = True,
                        selfconsistency: bool = False,
                        separated_selfconsistency: bool = False,
                        cot: bool = True,
                        output_format: dict) -> Tuple[ScrapedResponse, Usage]:
        
        raise NotImplementedError()