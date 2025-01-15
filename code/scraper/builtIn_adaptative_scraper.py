from scraper.adaptative_scraper import AdaptativeScraper
from pydantic_ai.tools import ToolFuncContext, Tool


class BuilInAdaptativeScraper(AdaptativeScraper):
    def __init__(self, model):
        super().__init__(model)

        self.agent.model = model.model_name

    def run(self, query: str, html: str):
        """ 
            Use an agent to perform scraping on the provided static HTML based on a natural language query.
            This method sends a query and a static HTML document to an agent, which processes the input and extracts the requested information. 
            The agent is responsible for interpreting the query and returning structured data based on the HTML content.

        Args:
            input (str): A natural language description of the data to extract from the HTML
            html (str): A string containing the static HTML document to be scraped
        Returns:
            _type_: NO SE TODAVIA
        """
        response = self.agent.run_sync(f'{query}:\n{html}') # puedo hacer algo para extraer el dominio
        return response
    
    def __scrap(self, query: str, html: str):
        """Scrap an static HTML based in the natural language input using a built-in model

        Args:
            query (str): A natural language description of the data to extract from the HTML.
            html (str): A string containing the static HTML document to be scraped.
        """
        
        pass
    


