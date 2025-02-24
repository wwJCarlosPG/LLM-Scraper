import asyncio
from dotenv import load_dotenv
from scraper_manager.infrastructure.extractors.extractor import DataExtractor
from scraper_manager.infrastructure.storages.local_storage import LocalStorage
from scraper_manager.application.data_processing_handler import DataProcessingHandler
from scraper_manager.infrastructure.validators.basedagent_validator import BasedAgentValidator
from scraper_manager.infrastructure.html_cleaners.default_html_cleaner import DefaultHTMLCleaner

# "query2": "Find all news headlines about sports.",
#             "data2": [
#                 {
#                     "headline": "Federer through after Simon care"
#                 },
#                 {
#                     "headline": "Prior in England World Cup squad"
#                 },
#                 {
#                     "headline": "Pakistan earn draw to win series"
#                 },
#                 {
#                     "headline": "Cantona takes New York"
#                 },
#                 {
#                     "headline": "Robinson adds new faces to squad"
#                 },
#                 {
#                     "headline": "McCarthy name in Ireland squad"
#                 },
#                 {
#                     "headline": "Gullit handed Russian club role"
#                 },
#                 {
#                     "headline": "Mapusua to leave Exiles for Japan"
#                 }
#             ],

# api_key1 = "fw_3ZRMs9d6Uh296J917sxT4W14"
async def main():
    load_dotenv()
    
    settings = {"temperature": 0.5, "max_tokens":10000, "timeout":120.0}
    # query = "Find all news headlines about sports."
    query = "Extrae la fecha del articulo y el título."
    
    link = 'http://www.cubadebate.cu/especiales/2025/02/17/la-hora-de-las-criptomonedas-en-cuba/'
    link = 'https://elorbe.com/al-instante/2025/02/16/detienen-a-5-presuntos-responsables-de-homicidio-en-ixtapa-fge.html'

    with open('pages/dataset/bbc/bbc___1___2011.html', 'r') as f:
        html = f.read()



    endpoint1 = "https://api.fireworks.ai/inference/v1/chat/completions"
    model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    # model_name = "accounts/sentientfoundation/models/dobby-mini-leashed-llama-3-1-8b"
    # model_name = 'accounts/fireworks/models/mistral-small-24b-instruct-2501'

    validator = BasedAgentValidator(model_name=model_name, endpoint=endpoint1)
    extractor = DataExtractor(model_name=model_name, validator=validator, endpoint=endpoint1)
    html_cleaner = DefaultHTMLCleaner()
    local_storage = LocalStorage()


    dph = DataProcessingHandler(extractor = extractor, html_cleaner = html_cleaner, storage = local_storage)
    await dph.excecute(
        query = query, 
        # html=html,
        html_url= link,
        selfconsistency = False,
        cot=True, 
        refinement=False,
        separated_selfconsistency=False, 
        context_length=32000,
        output_format={"Fecha": "Valor del campo de fecha", "Titulo":"Valor del titulo de la noticia"})
    
    

asyncio.run(main())