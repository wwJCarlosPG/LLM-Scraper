from fastapi import APIRouter
from schemas import ScrapedRequest, ScrapedResponse
from config.settings import ExtractorSettings
from infrastructure.factories import get_extractor, get_htmlcleaner, get_storage
from application.data_processing_handler import DataProcessingHandler
# hacer una importación de la configuracion de la extracción
router = APIRouter(tags=["Scraping"], prefix="/scrape")

@router.post("",response_model=ScrapedResponse)
def get_data(request: ScrapedRequest):
    extractor = get_extractor()
    html_cleaner = get_htmlcleaner()
    storage = get_storage()
    data_processing_handler = DataProcessingHandler(extractor=extractor, html_cleaner=html_cleaner, storage=storage)
    data_processing_handler.excecute(query=request.query,html_url=request.url)
    pass
    