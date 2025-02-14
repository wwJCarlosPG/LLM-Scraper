from scraper_manager.application.interfaces.extractor_interface import BaseExtractor

class DataExtraction:
    def __init__(self, extractor: BaseExtractor, html_cleaner):
        self.extractor = extractor
        self.html_cleaner = html_cleaner

    
    async def excecute(self, query: str, html: str, selfconsistency: bool, cot: bool, refinement: bool, separated_selfconsistency: bool, context_length, output_format: dict):
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
        html = await self.html_cleaner.clean(html, context_length)
        response = await self.extractor.extract(query, html, selfconsistency, cot, refinement, separated_selfconsistency, context_length, output_format)
        return response