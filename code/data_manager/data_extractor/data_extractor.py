from typing import TypedDict
from httpx import AsyncClient
from pydantic_ai.agent import Agent
from dataset_work.html_cleaner import HTML_Cleaner
from data_manager.external_models.external import ExternalModel
from data_manager.data_extractor.responses import ScrapedResponse
from data_manager.validators.default_validators import BaseValidator
from data_manager.prompts.prompts import get_extractor_system_prompt
from data_manager.validators.default_validators import DefaultValidator
from data_manager.exceptions import InvalidResultDuringValidation

class DataExtractorSettings(TypedDict):
    """
    A type definition for the settings used in the DataExtractor.

    Attributes:
        temperature (float): 
            The degree of randomness or creativity in the model's response.
            - A higher value (e.g., 0.9) results in more creative and diverse outputs.
            - A lower value (e.g., 0.2) makes the output more focused and deterministic.

        max_tokens (int): 
            The maximum number of tokens (words or characters, depending on the model) 
            that the model is allowed to generate in response.
            - Higher values allow for longer responses.
            - Lower values restrict the response length to be more concise.
    """
    temperature: float
    max_tokens: int


class DataExtractor:
    """
        A class for extracting structured data from HTML content using a language model.

        This class initializes an AI agent to process queries and extract relevant data 
        from provided HTML pages. A validation mechanism can be optionally applied to 
        ensure the quality of the extracted data.

        Attributes:
            agent (Agent): The Pydantic AI agent responsible for executing queries.
        
        Args:
            model_name (str): The name of the model to be used for data extraction.
            endpoint (str, optional): The API endpoint for the model. Defaults to None.
            api_key (str, optional): The API key for authentication. Defaults to None.
            env_alias (str, optional): The environment alias for the external model. Defaults to None.
            validator (BaseValidator, optional): An optional validator to verify extracted data.
            settings (DataExtractor): 
     """
    def __init__(self, *, 
                 model_name: str, 
                 endpoint: str | None = None, 
                 api_key: str | None = None, 
                 env_alias: str | None = None,
                 validator: BaseValidator | None = None,
                 settings: DataExtractorSettings = None):
     
        async_client = AsyncClient()
        self.settings = settings
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name,
                system_prompt=get_extractor_system_prompt()
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client),
                system_prompt = get_extractor_system_prompt(),
            )
        if validator is None:
            validator = DefaultValidator()
        self.agent.result_validator(validator.validate)

    async def extract(self, query: str, *,
                        html_content: str,
                        html_path: str = None,
                        is_local: bool = False,
                        refinement: bool = True) -> ScrapedResponse:
        """ 
            Extract structured data from an HTML document using a natural language query.

            This method processes an HTML document (provided as content or a file path), 
            cleans unnecessary elements such as `<script>` and `<style>` tags, and uses 
            an AI agent to extract relevant data based on the given query.

            Args:
                query (str): 
                    A natural language query specifying the data to extract from the HTML.
                html_content (str): 
                    A string containing the raw HTML content to be processed.
                html_path (str, optional): 
                    Path to the HTML file if available. If provided, the content will be read from the file. 
                    Defaults to None.
                is_local (bool, optional): 
                    Indicates whether the provided HTML path points to a local file. 
                    If True, the file will be read locally; otherwise, it will be treated as a URL. 
                    Defaults to False.

            Returns:
                dict: 
                    A dictionary containing the extracted data in a structured format.

            Raises:
                ValueError: If both `html_content` and `html_path` are missing.
                Exception: If an issue occurs during data extraction.
                InvalidResultDuringValidation: If an error ocurred during validation.

            Example:
                ```python
                extractor = DataExtractor(model_name="gpt-4")
                extracted_data = await extractor.extract(
                    query="Extract all news headlines",
                    html_content="<html><body><h1>News</h1></body></html>"
                )
                print(extracted_data)
                ```
        """
        cleaned_html = HTML_Cleaner.clean_without_download(url=html_path, tags=['script', 'style'], html_content=html_content, is_local=is_local)
        retries = 0
        is_valid = False
        while not is_valid and retries < 3:
            
            try:
                scraped_data = await self.agent.run(f'{query}:\n{cleaned_html}', model_settings=self.settings) # creo que esto vale porque es un diccionario. 
            except InvalidResultDuringValidation as e:
                return ScrapedResponse(is_valid=False, explanation=e.message, feedback=e.message, scraped_data=[])
            
            is_valid = scraped_data.data.is_valid
            
            if not refinement:
                break

            if not is_valid:
                feedback = scraped_data.data.feedback
                query = query + '\n' + feedback
            retries += 1
        
        return scraped_data.data

       
    
  
    


