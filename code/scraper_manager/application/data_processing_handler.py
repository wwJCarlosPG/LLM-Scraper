from scraper_manager.application.interfaces.storage_interface import BaseStorage
from scraper_manager.application.interfaces.extractor_interface import BaseExtractor
from scraper_manager.application.interfaces.html_cleaner_interface import BaseHTMLCleaner
from pprint import pprint
class DataProcessingHandler:
    """
    A class to handle the data processing workflow, including extraction, cleaning, and storage.

    This class orchestrates the extraction of structured data from HTML content,
    cleans the HTML using a specified cleaner, and stores the extracted data
    using a specified storage mechanism.

    Attributes:
        extractor (BaseExtractor): The extractor used to extract data from HTML.
        html_cleaner (BaseHTMLCleaner): The cleaner used to clean the HTML content.
        storage (BaseStorage): The storage used to save the extracted data.
    """
    def __init__(self, extractor: BaseExtractor, html_cleaner: BaseHTMLCleaner, storage: BaseStorage):
        """
        Initializes a DataProcessingHandler instance.

        Args:
            extractor (BaseExtractor): An instance of a class implementing BaseExtractor,
                responsible for extracting data from HTML.
            html_cleaner (BaseHTMLCleaner): An instance of a class implementing BaseHTMLCleaner,
                responsible for cleaning the HTML content.
            storage (BaseStorage): An instance of a class implementing BaseStorage,
                responsible for storing the extracted data.
        """
        self.extractor = extractor
        self.html_cleaner = html_cleaner
        self.storage = storage

    
    async def excecute(self, *,
                       query: str, 
                       html: str | None = None,
                       html_url: str | None = None, 
                       selfconsistency: bool = False, 
                       cot: bool = True, 
                       refinement: bool = False, 
                       separated_selfconsistency: bool = False, 
                       context_length, 
                       output_format: dict):
        """
            Executes the data processing workflow, extracting, cleaning, and storing data.

            This method orchestrates the entire data processing workflow, including:
                1. Retrieving HTML content (either from a string or a URL).
                2. Cleaning the HTML content using the specified HTML cleaner.
                3. Splitting the HTML into chunks if it exceeds the context length.
                4. Extracting data from the HTML (or chunks) using the specified extractor.
                5. Saving the extracted data to the specified storage.

            Args:
                query (str): A natural language query specifying the data to extract.
                html (str, optional): The HTML content as a string. Defaults to None.
                html_url (str, optional): The URL of the HTML content. Defaults to None.
                selfconsistency (bool, optional): Enables self-consistency checks. Defaults to False.
                cot (bool, optional): Enables chain-of-thought prompting. Defaults to True.
                refinement (bool, optional): Enables iterative refinement of the extraction. Defaults to False.
                separated_selfconsistency (bool, optional): Enables separated self-consistency. Defaults to False.
                context_length (int): The maximum context length.
                output_format (dict): The desired output format for the extracted data.

            Returns:
                The result of data extraction
            Raises:
                ValueError: If both `html` and `html_url` are None.
        """
        chunks = []
        if html is None:
            if html_url is not None:
                html = self.html_cleaner.get_html_content(html_url)
            else:
                raise ValueError(f"html parameter and html_url parameter can't be None at the same time.")

        html = self.html_cleaner.clean_by_tag(html, [], context_length)
        print(len(html))
        print(context_length - len(html))
        if (context_length - len(html))<1000:
            chunks = self.html_cleaner.split_html(html, context_length - 500)

        in_chunks = len(chunks) > 1
        response = await self.extractor.extract(
            query = query, 
            html_content= html, 
            selfconsistency = selfconsistency, 
            cot = cot, 
            refinement = refinement, 
            separated_selfconsistency = separated_selfconsistency,  
            output_format = output_format, 
            in_chunks = in_chunks,
            chunks = chunks)
        pprint(response[0])
        self.storage.save(str(response[0]), 'output_folder')
        return response