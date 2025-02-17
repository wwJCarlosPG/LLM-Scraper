import asyncio
# main()
from scraper_manager.infrastructure.validators.basedagent_validator import BasedAgentValidator
from scraper_manager.infrastructure.extractors.extractor import DataExtractor
from scraper_manager.application.data_processing_handler import DataProcessingHandler
from scraper_manager.infrastructure.html_cleaners.default_html_cleaner import DefaultHTMLCleaner
from scraper_manager.infrastructure.storages.local_storage import LocalStorage
from dotenv import load_dotenv

async def main():
    load_dotenv()
    html = ""
    # LM Studio section
    # api_key1 = 'lm-studio'
    # endpoint1 = 'http://localhost:1234/v1/chat/completions'
    # model_name = 'llama-3-8b-instruct'
    # model_name = 'bartowski/Llama-3.2-3B-Instruct-GGUF'
    # endpoint1 = 'http://172.20.10.3:1234/v1/chat/completions'
    # model_name = 'quantfactory/meta-llama-3-8b-instruct-gguf/meta-llama-3-8b-instruct.q3_k_m.gguf'
    # api_key1 = "fw_3ZRMs9d6Uh296J917sxT4W14"
    # endpoint1 = "https://api.fireworks.ai/inference/v1/chat/completions"
    # model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    # # model_name = 'accounts/fireworks/models/mistral-7b'
    # # model_name = "accounts/fireworks/models/mistral-7b"
    # # model_name = 'yarn-mistral-7b-128k'
    # # model_name = "Qwen2-VL-7B-Instruct"
    # # model_name = "accounts/sentientfoundation/models/dobby-mini-leashed-llama-3-1-8b"
    # # model_name = 'accounts/fireworks/models/mistral-small-24b-instruct-2501'
    # model_name = 'accounts/fireworks/models/llama-v3-8b-instruct'
    model_name = "gemini-1.5-pro"
    # with open('pages/dataset/bbc/bbc___1___2011.html', 'r') as f:
    #     html = f.read()

    # print(len(html))
    settings = {"temperature": 0.5, "max_tokens":10000, "timeout":120.0}
    validator = BasedAgentValidator(model_name=model_name)
    extractor = DataExtractor(model_name=model_name, validator=validator, settings={"max_tokens":10000})
    # data = await extractor.extract("Extract all product with price more than $25.00 from the document.", html_content=html, selfconsistency = False, cot=True, refinement=False, separated_selfconsistency=False, output_format={"ProductTitle": "Value of product title"})
    html_cleaner = DefaultHTMLCleaner()
    local_storage = LocalStorage()
    dph = DataProcessingHandler(extractor = extractor, html_cleaner = html_cleaner, storage = local_storage)
    await dph.excecute(
        query = "Find all offers from this html.", 
        html=html, 
        selfconsistency = False,
        cot=True, 
        refinement=True,
        separated_selfconsistency=False, 
        context_length=8000,
        output_format={"Offer": "Value of offer"})
    
    

asyncio.run(main())





