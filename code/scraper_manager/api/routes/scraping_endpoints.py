from fastapi import APIRouter
from scraper_manager.api.schemas import ScrapedRequest, ScrapedResponse
# from config.settings import ExtractorSettings
from scraper_manager.infrastructure.factories import get_extractor, get_htmlcleaner, get_storage
from scraper_manager.application.data_processing_handler import DataProcessingHandler
# hacer una importación de la configuracion de la extracción
router = APIRouter(tags=["Scraping"], prefix="/scrape")

@router.post("",response_model=ScrapedResponse)
async def get_data(request: ScrapedRequest):
    extractor = get_extractor()
    html_cleaner = get_htmlcleaner()
    storage = get_storage()
    data_processing_handler = DataProcessingHandler(extractor=extractor, html_cleaner=html_cleaner, storage=storage)
    response = await data_processing_handler.execute(query=request.query,html_url=request.url)
    return response
    