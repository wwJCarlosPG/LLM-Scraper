from typing import overload
from pydantic_ai.agent import Agent
from dataset_work.html_cleaner import HTML_Cleaner
from pydantic_ai.tools import ToolFuncContext, Tool
from scraper.external_models.external import ExternalModel, ExternalAgentModel, ExternalResponse
from scraper.adaptative_scraper.validators import external_validator
from httpx import AsyncClient
from scraper.prompts.prompts import SIMPLE_SYSTEM_PROMPT
class AdaptativeScraper:
    def __init__(self, model_name: str, 
                 url: str, 
                 endpoint: str | None = None, 
                 api_key: str | None = None, 
                 env_alias: str | None = None):
        """_summary_

        Args:
            model_name (str): _description_
            url (str): _description_
            endpoint (str | None, optional): _description_. Defaults to None.
            api_key (str | None, optional): _description_. Defaults to None.
            env_alias (str | None, optional): _description_. Defaults to None.
        """

        async_client = AsyncClient()
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client),
                system_prompt = SIMPLE_SYSTEM_PROMPT,
            )
            self.agent.result_validator(external_validator)
        
    @staticmethod     
    def clean_html(path: str, tags: list[str], is_local: bool):
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
    
    
    async def run(self, query: str, html: str) -> dict:
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
        response = await self.agent.run(f'{query}:\n{html}') 
        return response.data.scraped_data  # this is the final_result
    
  
    


