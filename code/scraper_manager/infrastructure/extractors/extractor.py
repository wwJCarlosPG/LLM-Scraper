from httpx import AsyncClient
from pydantic_ai.agent import Agent
from pydantic_ai.usage import Usage
from dataset_work.html_cleaner import HTML_Cleaner
from scraper_manager.infrastructure.exceptions.exceptions import InvalidResultDuringValidation
from scraper_manager.application.entities.responses import ScrapedResponse, Response
from scraper_manager.infrastructure.integration.external_models import ExternalModel
from scraper_manager.application.interfaces.validator_interface import BaseValidator
from scraper_manager.infrastructure.prompts.prompts import get_full_system_prompt, get_system_prompt_with_COT, get_system_prompt_without_COT
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from statistics import mean
from scraper_manager.application.entities.extractor_settings import DataExtractorSettings
from scraper_manager.application.interfaces.extractor_interface import BaseExtractor

RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "ScrapedResponse",
        "strict": "true",  
        "schema": Response.model_json_schema()  
    }
}
SCRAPED_RESPONSE_FORMAT = {
    "type": "json_schema",
    "json_schema": {
        "name": "ScrapedResponse",
        "strict": "true",  
        "schema": ScrapedResponse.model_json_schema()  
    }
}

class DataExtractor(BaseExtractor):
    """
        A class for extracting structured data from HTML content using a language model.

        This class initializes an AI agent to process queries and extract relevant data
        from provided HTML pages. A validation mechanism can be optionally applied to
        ensure the quality of the extracted data.

        Attributes:
            settings (DataExtractorSettings): Configuration settings for the data extractor.
            model_name (str): The name of the language model to be used for data extraction.
            agent (Agent): The Pydantic AI agent responsible for executing queries.

        Args:
            model_name (str): The name of the model to be used for data extraction.
            endpoint (str, optional): The API endpoint for the model. Defaults to None.
            api_key (str, optional): The API key for authentication. Defaults to None.
            env_alias (str, optional): The environment alias for the external model. Defaults to None.
            validator (BaseValidator): A validator to verify extracted data.
            settings (dict, optional): Additional settings for the extractor.
    """
    def __init__(self, *, 
                 model_name: str, 
                 endpoint: str | None = None, 
                 api_key: str | None = None, 
                 env_alias: str | None = None,
                 validator: BaseValidator,
                 settings: dict | None = None):
        """
        Initializes a `DataExtractor` instance.

        Configures the data extractor with the specified language model, validator,
        and settings. It sets up the AI agent to process queries and extract data
        from HTML content.

        Args:
            model_name (str): The name of the language model to use.
            endpoint (str, optional): The API endpoint for the external model.
                If provided, an `ExternalModel` is used. Defaults to None.
            api_key (str, optional): The API key to authenticate with the external model.
                If not provided and `ExternalModel` is used then env_alias is required. Defaults to None.
            env_alias (str, optional): An alias for the environment, used for the external model.
                Defaults to None.
            validator (BaseValidator): A validator instance to verify extracted data.
            settings (dict, optional): A dictionary with custom settings for the extractor.
                If not provided, the default settings defined in `DataExtractorSettings` are used.
            context_length (int): The maximum context length.
        Raises:
            `ValueError`: If an invalid setting key is provided in `settings`.
        """

        async_client = AsyncClient()
        
        if settings is None:
            self.settings = DataExtractorSettings(
                temperature=0.5, 
                max_tokens=10000, 
                timeout=60.0,
                response_format = SCRAPED_RESPONSE_FORMAT 
            )
        else:
            for key in settings.keys():
                valid_keys = set(DataExtractorSettings.__annotations__.keys())
                if key not in valid_keys:
                    raise ValueError(f"Invalid setting key: {key}")
            self.settings = settings

        
        self.model_name = model_name
        if endpoint is None:
            self.agent: Agent = Agent(
                model=model_name
            )
        else:
            self.agent: Agent = Agent(
                model = ExternalModel(api_key = api_key,endpoint=endpoint, model_name=model_name, env_alias = env_alias, http_client=async_client)
            )
        self.agent.result_validator(validator.validate)

    def set_system_prompt(self, new_system_prompt):
         """
        Sets a new system prompt for the AI agent.

        This method allows you to dynamically update the system prompt of the agent,
        which can be useful for adapting the agent's behavior based on different
        extraction requirements.

        Args:
            new_system_prompt (str): The new system prompt to be set for the agent.
        """
         @self.agent.system_prompt
         def set():
            return new_system_prompt


    async def extract(self, query: str, *,
                        html_content: str,
                        settings: DataExtractorSettings = None,
                        context: str = None,
                        refinement: bool = True,
                        selfconsistency: bool = False,
                        separated_selfconsistency: bool = False,
                        cot: bool = True,
                        output_format: dict,
                        in_chunks: bool = False,
                        chunks: list) -> Tuple[ScrapedResponse, Usage]:
        
        """
        Extracts structured data from HTML content using a language model and optional chunking.

        This method serves as the main entry point for data extraction. It determines
        whether to process the HTML content in chunks or as a whole, and calls the
        appropriate extraction method.

        Args:
            query (str): A natural language query specifying the data to extract.
            html_content (str): A string containing the raw HTML content to be processed.
            settings (DataExtractorSettings, optional): Custom settings for this extraction.
            refinement (bool, optional): Enables iterative refinement of the extraction. Defaults to True.
            selfconsistency (bool, optional): Enables self-consistency checks. Defaults to False.
            separated_selfconsistency (bool, optional): Enables separated self-consistency. Defaults to False.
            cot (bool, optional): Enables chain-of-thought prompting. Defaults to True.
            output_format (dict): Desired format for the output data.
            in_chunks (bool, optional): If True, the HTML will be processed in chunks. Defaults to False.
            chunks (list): A list of HTML chunks if processing in chunks.

        Returns:
            Tuple[ScrapedResponse, Usage]: A tuple containing the scraped response and usage information.
        """
        
        if in_chunks:
            return await self.__extract_in_chunks(query = query, 
                                                  chunks = chunks, 
                                                  settings = settings, 
                                                  refinement = refinement, 
                                                  selfconsistency = selfconsistency, 
                                                  separated_selfconsistency = separated_selfconsistency, 
                                                  cot = cot, 
                                                  output_format = output_format)
        else:
            return await self.__extract(query, 
                                        html_content = html_content, 
                                        settings = settings, 
                                        refinement = refinement, 
                                        selfconsistency = selfconsistency, 
                                        separated_selfconsistency = separated_selfconsistency, 
                                        cot = cot, 
                                        output_format = output_format)

    async def __extract(self, query: str, *,
                        html_content: str,
                        settings: DataExtractorSettings = None,
                        refinement: bool = True,
                        selfconsistency: bool = False,
                        separated_selfconsistency: bool = False,
                        cot: bool = True,
                        output_format: dict) -> Tuple[ScrapedResponse, Usage]:
        """
        Extract structured data from an HTML document using a natural language query.

        Args:
            query (str):
                A natural language query specifying the data to extract from the HTML.
            html_content (str):
                A string containing the raw HTML content to be processed.

        Returns:
            Tuple[ScrapedResponse, Usage]:
                A tuple containing the extracted data in a structured format and usage information.

        Raises:
            ValueError: If both `html_content` and `html_path` are missing.
            Exception: If an issue occurs during data extraction.
            InvalidResultDuringValidation: If an error occurred during validation.
        """
        if settings is not None:
            self.settings = settings

        if selfconsistency:
            self.settings['response_format'] = RESPONSE_FORMAT
            

        @self.agent.system_prompt
        def set_system_prompt():
            return DataExtractor.__select_system_prompt__(selfconsistency, cot, output_format)
        
        cleaned_html = html_content
        
        print(f'HTML Length: {len(cleaned_html)}')
        retries = 0
        is_valid = False
        while not is_valid and retries < 3: 
            
    
            try:
                if separated_selfconsistency:
                    response = await self.__with_separated_selfconsistency(query, cleaned_html, selfconsistency, output_format)
                    return response
                else:
                    scraped_data = await self.agent.run(f'{query}:\n{cleaned_html}', model_settings=self.settings, deps=selfconsistency) 
            except TimeoutError as t:
                return ScrapedResponse(is_valid=False, explanation='Timeout error', feedback='Timeout error', final_answer=[], refinement_count=retries), Usage(request_tokens=len(query), response_tokens=0, total_tokens=len(query))
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


    async def __extract_in_chunks(self, query, chunks, settings, refinement, selfconsistency, separated_selfconsistency, cot, output_format):
        """
        Extracts data from HTML content by processing it in chunks.

        This method splits the HTML content into smaller chunks and processes each chunk
        separately using the __extract method. It then merges the results from each chunk
        to produce a final result.

        Args:
            query (str): A natural language query specifying the data to extract.
            chunks (list): A list of HTML chunks to be processed.
            settings (DataExtractorSettings, optional): Custom settings for this extraction.
            refinement (bool, optional): Enables iterative refinement of the extraction.
            selfconsistency (bool, optional): Enables self-consistency checks.
            separated_selfconsistency (bool, optional): Enables separated self-consistency.
            cot (bool, optional): Enables chain-of-thought prompting.
            output_format (dict): Desired format for the output data.

        Returns:
            Tuple[ScrapedResponse, Usage]: A tuple containing the scraped response and usage information.
        """
        
        scraped_data_collection = []
        usages = []
        for chunk in chunks:
            scraped_data = await self.__extract(query = query, 
                                                html_content = chunk, 
                                                settings = settings, 
                                                refinement = refinement, 
                                                selfconsistency = selfconsistency, 
                                                separated_selfconsistency = separated_selfconsistency, 
                                                cot = cot, 
                                                output_format = output_format)
            scraped_data_collection.append(scraped_data[0])
            usages.append(scraped_data[1])
        print("MERGING CHUNKS...")
        return self.__merge_chunks(scraped_data_collection, usages)


    def __merge_chunks(self, scraped_data_collection, usages):
        """
        Merges the results from multiple chunks into a single ScrapedResponse.

        This method combines the scraped data and usage information from each chunk
        to create a final result that represents the entire HTML document.

        Args:
            scraped_data_collection (list[ScrapedResponse]): A list of ScrapedResponse objects from each chunk.
            usages (list[Usage]): A list of Usage objects from each chunk.

        Returns:
            Tuple[ScrapedResponse, Usage]: A tuple containing the merged scraped response and usage information.
        """

        result = ScrapedResponse(final_answer=[])
        usage = Usage(request_tokens=0, total_tokens=0, response_tokens=0)
        print(scraped_data_collection)
        print(usages)

        for partial_response in scraped_data_collection:
            if not partial_response.is_valid:
                result.is_valid = False
            result.scraped_data.extend(partial_response.scraped_data)
            result.explanation += partial_response.explanation  # hacer algo con la explicacion
            result.refinement_count=partial_response.refinement_count

        for partial_usage in usages:
            usage.request_tokens+=partial_usage.request_tokens
            print("xxx")

            usage.response_tokens+=partial_usage.response_tokens
            print("xxx")

            usage.total_tokens+=partial_usage.total_tokens
            print("xxx")


        return result, usage


    @staticmethod
    def __select_system_prompt__(selfconsistency: bool, cot: bool, output_format: dict):
        """
        Selects the appropriate system prompt based on the given parameters.

        This method determines which system prompt to use based on whether self-consistency
        is enabled, chain-of-thought prompting is enabled, and the desired output format.

        Args:
            selfconsistency (bool): Indicates whether self-consistency is enabled.
            cot (bool): Indicates whether chain-of-thought prompting is enabled.
            output_format (dict): Desired format for the output data.

        Returns:
            str: The selected system prompt.
        """
        if selfconsistency:
            system_prompt = get_full_system_prompt(output_format)
        elif cot and not selfconsistency:
            system_prompt = get_system_prompt_with_COT(output_format)
        else:
            system_prompt = get_system_prompt_without_COT(output_format)
        return system_prompt
    
    
    async def __with_separated_selfconsistency(self,query: str, cleaned_html: str, selfconsistency: bool, output_format: dict):
        """
        Extracts data with separated self-consistency.

        This method performs data extraction multiple times and merges the results based
        on a majority vote.

        Args:
            query (str): A natural language query specifying the data to extract.
            cleaned_html (str): The HTML content to be processed.
            selfconsistency (bool): Indicates whether self-consistency is enabled.
            output_format (dict): Desired format for the output data.

        Returns:
            Tuple[ScrapedResponse, Usage]: A tuple containing the scraped response and usage information.
        """
        
        i = 0
        scraped_data_collection = []
        result = ScrapedResponse(final_answer=[])
        usage = Usage()
        usages = []
        while i < 3:
                scraped_data = await self.agent.run(f'{query}:\n{cleaned_html}', model_settings=self.settings, deps=selfconsistency) 
                scraped_data_collection.append(scraped_data.data)
                usages.append(scraped_data.usage())
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
        Filters a list of three lists of dictionaries, keeping only the dictionaries
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
       
            




    # def __merge_scraped_data(scraped_data_collection: list[ScrapedResponse], usages: list[Usage]):
    #     """
    #     Merges a collection of ScrapedResponse objects into a single ScrapedResponse object.

    #     This method combines the scraped data, explanations, and refinement counts from
    #     multiple partial responses into a single, comprehensive response.

    #     Args:
    #         scraped_data_collection (list[ScrapedResponse]): A list of ScrapedResponse objects to merge.
    #         usages (list[Usage]): A list of Usage objects to merge.

    #     Returns:
    #         Tuple[ScrapedResponse, Usage]: A tuple containing the merged ScrapedResponse and Usage objects.
    #     """
    #     result: ScrapedResponse = ScrapedResponse()
    #     usage: Usage = Usage()
    #     for partial_response in scraped_data_collection:
    #         if not partial_response.is_valid:
    #             result.is_valid = False
    #         result.scraped_data.extend(partial_response.scraped_data)
    #         result.explanation += partial_response.explanation
    #         result.refinement_count=partial_response.refinement_count

    #     for partial_usage in usages:
    #         usage.request_tokens+=partial_usage.request_tokens
    #         usage.response_tokens+=partial_usage.response_tokens
    #         usage.total_tokens+=partial_usage.total_tokens

    #     return result, usage

            