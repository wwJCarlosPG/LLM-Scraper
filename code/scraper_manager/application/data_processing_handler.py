from scraper_manager.application.utils import get_html_content
from scraper_manager.application.interfaces.storage_interface import BaseStorage
from scraper_manager.application.interfaces.extractor_interface import BaseExtractor
from scraper_manager.application.interfaces.html_cleaner_interface import BaseHTMLCleaner

class DataProcessingHandler:
    def __init__(self, extractor: BaseExtractor, html_cleaner: BaseHTMLCleaner, storage: BaseStorage):
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
        """_summary_

        Args:
            query (str): _description_
            html (str): _description_
            selfconsistency (bool): _description_
            cot (bool): _description_
            refinement (bool): _description_
            separated_selfconsistency (bool): _description_
            output_format (dict): _description_
        """
        chunks = []
        if html is None:
            if html_url is not None:
                html = get_html_content(html_url)
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
        print(response[0])
        self.storage.save(str(response[0]), 'xxx')
        return response