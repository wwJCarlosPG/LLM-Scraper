from scraper.adaptative_scraper import AdaptativeScraper
from fireworks.client import Fireworks
from abc import abstractmethod

class ExternalAdaptativeScraper(AdaptativeScraper):
    def __init__(self, model, api_key, system_prompt):
        super().__init__(model, api_key, system_prompt)
        
    def scrap(self, query: str, html: str):
        # esta deberia llamar a la api_scrap supongo, ver que se hace con esto.
        """Scrap an static HTML based in the natural language input using an external model through API

        Args:
            input (str): Natural language query
            html (str): Raw HTML
        Returns:
            _type_: NO SE TODAVIA
        
        """
        # pensar qué hacer con esto
        
    # @abstractmethod
    # def api_scrap(self):
    #     pass