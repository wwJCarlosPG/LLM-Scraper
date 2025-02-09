from typing import TypedDict
from httpx import AsyncClient
from pydantic_ai.agent import Agent
from pydantic_ai.usage import Usage
from dataset_work.html_cleaner import HTML_Cleaner
from scraper_manager.core.exceptions import InvalidResultDuringValidation
from scraper_manager.application.extraction.responses import ScrapedResponse, Response
from scraper_manager.infrastructure.integration.external_models import ExternalModel
from scraper_manager.application.validation.validators import BaseValidator, DefaultValidator
from scraper_manager.application.prompts.prompts import get_full_system_prompt, get_simple_system_prompt, get_system_prompt_with_COT, get_system_prompt_without_COT, get_validator_system_prompt
from typing import Tuple, Union
import pdfkit
import gensim.downloader as api
from gensim.matutils import cossim
from typing import List, Dict, Any
import itertools
from collections import defaultdict
from statistics import mean


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
    temperature: float = 0.3
    max_tokens: int = 10000
    timeout: float = 60.0
    response_format = {"type": "json_object", "schema": ScrapedResponse.model_json_schema()} | {'type': 'json_object', 'schema': Response.model_json_schema()}

SCRAPED_RESPONSE_FORMAT = {"type": "json_object", "schema": ScrapedResponse.model_json_schema()}
RESPONSE_FORMAT = {"type": "json_object", "schema": Response.model_json_schema()}


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
                 context_length: int = 0):

        async_client = AsyncClient()
        self.__context_length = context_length
        self.settings = DataExtractorSettings(
        temperature=0.5, 
        max_tokens=10000, 
        timeout=60.0,
        response_format = SCRAPED_RESPONSE_FORMAT 
    )
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name, model_settings=self.settings
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client)
            )
        if validator is None:
            validator = DefaultValidator()
        self.agent.result_validator(validator.validate)

    def set_system_prompt(self, new_system_prompt):
         @self.agent.system_prompt
         def set():
            return new_system_prompt

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
        if settings is not None:
            self.settings = settings

        if selfconsistency:
            self.settings['response_format'] = RESPONSE_FORMAT
            

        @self.agent.system_prompt
        def set_system_prompt():
            return DataExtractor.__select_system_prompt__(selfconsistency, cot, output_format)
        
        cleaned_html = HTML_Cleaner.clean_without_download(url=html_path, tags=['script', 'style'], html_content=html_content, is_local=is_local, context_length=self.__context_length)
        # print(cleaned_html)
        print(f'HTML Length: {len(cleaned_html)}')
        is_splited = False
        if self.__context_length < len(cleaned_html)+1000:
            splited_html = HTML_Cleaner.split_html_with_beautifulsoup(cleaned_html, self.__context_length - 2000)
            is_splited = True
        retries = 0
        is_valid = False
        chunk_index = 0
        while not is_valid and retries < 3: # poner retries como un parametro
            
    
            try:
                if separated_selfconsistency:
                    response = await self.__with_separated_selfconsistency(query, cleaned_html, selfconsistency, output_format)
                    return response
                else:
                    scraped_data = await self.agent.run(f'{query}:\n{cleaned_html}', model_settings=self.settings, deps=selfconsistency) 
            except Exception as e:
                    return ScrapedResponse(is_valid=False, explanation=e.message, feedback=e.message, final_answer=[], refinement_count=retries), Usage(request_tokens=len(query), response_tokens=0, total_tokens=len(query))

            is_valid = scraped_data.data.is_valid
            
            if not refinement:
                break

            if not is_valid:
                feedback = scraped_data.data.feedback
                query = query + '\n' + feedback
            retries += 1

        scraped_data.data.refinement_count = retries
        return (scraped_data.data, scraped_data.usage())

    @staticmethod
    def __select_system_prompt__(selfconsistency: bool, cot: bool, output_format: dict):
        
        if selfconsistency:
            system_prompt = get_full_system_prompt(output_format)
        elif cot and not selfconsistency:
            system_prompt = get_system_prompt_with_COT(output_format)
        else:
            system_prompt = get_system_prompt_without_COT(output_format)
        return system_prompt
    
    
    async def __with_separated_selfconsistency(self,query: str, cleaned_html: str, selfconsistency: bool, output_format: dict):
        i = 0
        scraped_data_collection = []
        result = ScrapedResponse(final_answer=[])
        usage = Usage()
        usages = []
        while i < 3:
            # try:
                scraped_data = await self.agent.run(f'{query}:\n{cleaned_html}', model_settings=self.settings, deps=selfconsistency) 
                scraped_data_collection.append(scraped_data.data)
                usages.append(scraped_data.usage())
            # except Exception:
                # pass
                i+=1
        
        if scraped_data_collection != []:
            data = [s.scraped_data for s in scraped_data_collection]
            result.scraped_data = self.__merge_collection(data)
            result.is_valid = True
            for d in scraped_data_collection:
                if not d.is_valid:
                    result.is_valid = False
                    break
            result.refinement_count = 0
            usage.request_tokens = len(query) + len(cleaned_html)
            usage.response_tokens = mean([u.response_tokens for u in usages])
            usage.total_tokens = len(query) + usage.response_tokens
            return (result, usage)
        else:
            return ScrapedResponse(is_valid=False, explanation='No valid response', feedback='No valid response', final_answer=[], refinement_count=3), Usage(request_tokens=len(query), response_tokens=0, total_tokens=len(query))

        
    def __merge_collection(self, data: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """
        Filters a list of three lists of dictionaries, keeping only the *dictionaries*
        that appear in at least two of the three lists.

        Args:
            data: A list containing three lists of dictionaries.

        Returns:
            A new list containing only the dictionaries that appear in at least
            two of the input lists.
        """

        if len(data) != 3:
            raise ValueError("The input list must contain exactly three lists.")

        dictionary_counts = defaultdict(int)
        for lst in data:
            for dictionary in lst:
                frozen_dict = frozenset(dictionary.items()) 
                dictionary_counts[frozen_dict] += 1

        # Identify the dictionaries that appear in at least two lists
        common_dictionaries = {froz_dict for froz_dict, count in dictionary_counts.items() if count >= 2}

        # Create a new list containing only the common dictionaries, converting back to dicts
        result = [dict(froz_dict) for lst in data for dictionary in lst for froz_dict in common_dictionaries if frozenset(dictionary.items()) == froz_dict]
        
        # Remove possible duplicates from the result list. The dicts must be converted to tuples to be added to the set.
        seen = set()
        new_result = []
        for d in result:
            frozen = tuple(d.items())
            if frozen not in seen:
                new_result.append(d)
                seen.add(frozen)

        return new_result
       
            




    def __merge_scraped_data(scraped_data_collection: list[ScrapedResponse], usages: list[Usage]):
        result: ScrapedResponse = ScrapedResponse()
        usage: Usage = Usage()
        for partial_response in scraped_data_collection:
            if not partial_response.is_valid:
                result.is_valid = False
            result.scraped_data.extend(partial_response.scraped_data)
            result.explanation += partial_response.explanation
            result.refinement_count=partial_response.refinement_count

        for partial_usage in usages:
            usage.request_tokens+=partial_usage.request_tokens
            usage.response_tokens+=partial_usage.response_tokens
            usage.total_tokens+=partial_usage.total_tokens

        return result, usage

            

            

    
  
    


