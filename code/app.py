import asyncio
from pydantic_ai.exceptions import UnexpectedModelBehavior
from scraper_manager.application.extraction.extractor import DataExtractor
from scraper_manager.application.validation.validators import BasedAgentValidator, ValidatorResponse, DefaultValidator
from dataset_work.data_augmenter import main
from tester.run import test, collect_errors, sort_txt, remove_duplicates, test2, make_equal_queries, generate_labeled_dataset
from typing import Tuple
from dotenv import load_dotenv
# main()

async def main():
    load_dotenv()
    # hf = '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'
    # endpoint = "https://api-inference.huggingface.co/models/Qwen/Qwen2-VL-7B-Instruct/v1/chat/completions"
    # key = "AIzaSyDysReK_sh0Iwfra7do4b1Jgi6KdGr6PKY"
    # model_name = "gemini-1.5-pro"
    # api_key1 = 'lm-studio'
    api_key1 = "fw_3ZhXjgfYtEzM31Su9CHTrLFx"
    # endpoint1 = 'http://172.20.10.3:1234/v1/chat/completions'
    endpoint1 = "https://api.fireworks.ai/inference/v1/chat/completions"
    model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    # model_name = 'accounts/fireworks/models/mistral-7b'
    # model_name = "accounts/fireworks/models/mistral-7b"
    # model_name = 'llama-3-8b-instruct'
    # model_name = 'yarn-mistral-7b-128k'
    # model_name = "Qwen2-VL-7B-Instruct"
    # model_name = "accounts/sentientfoundation/models/dobby-mini-leashed-llama-3-1-8b"
    # model_name = 'accounts/fireworks/models/mistral-small-24b-instruct-2501'
    d = {"temperature": 0.5, "max_tokens":10000, "timeout":120.0}
    

    x = BasedAgentValidator(model_name=model_name,api_key=api_key1, endpoint=endpoint1 )
    # # x = DefaultValidator()
    b = DataExtractor(model_name=model_name, endpoint=endpoint1, api_key=api_key1, validator=x, context_length=128000)


    # await test('amazon_best_sellers', b, cot = True, refinement = False, self_consistency=False, separated_selfconsistency=True, root_path='code/results/amazon_best_sellers/llama3.3-70B')
    # collect_errors('code/results/amazon_best_sellers/llama3.3-70B/with_separated_selfconsistency')
    
    #CAMBIAR LAS COSAS CUANDO USE EL TEST2
    # await test2('amazon_best_sellers',b, 'code/results/amazon_best_sellers/llama3.3-70B', refinement=False, cot=True, selfconsistency = False, separated_selfconsistency = True)

    # with open('pages/dataset/amazon_best_sellers/amazon-gp-bestsellers-fashion___10___2022.html', 'r') as f:
    #     html = f.read()
    # x = await b.extract("Extract all product with price more than $25.00 from the document.", html_content=html, selfconsistency = False, cot=True, refinement=False, separated_selfconsistency=False, output_format={"ProductTitle": "Value of product title"})
    # print("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    # print(x[0])

    
    

asyncio.run(main())
