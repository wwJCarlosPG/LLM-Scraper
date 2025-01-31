import asyncio
from pydantic_ai.exceptions import UnexpectedModelBehavior
from scraper_manager.application.extraction.extractor import DataExtractor
from scraper_manager.application.validation.validators import BasedAgentValidator, ValidatorResponse
from dataset_work.data_augmenter import main
from tester.run import test, collect_errors, sort_txt, remove_duplicates, test2
from typing import Tuple
from dotenv import load_dotenv
import jsonschema
# main()

async def main():
    load_dotenv()
    api_key1 = 'lm-studio'
    api_key2 = "fw_3ZP2t96M71V25QJMKVBWoh1v"
    endpoint1 = 'http://172.20.10.3:1234/v1/chat/completions'
    endpoint2 = "https://api.fireworks.ai/inference/v1/chat/completions"
    # model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    model_name = 'llama-3-8b-instruct'
    d = {"temperature": 0.6, "max_tokens":1000, "timeout":120.0}
    

    x = BasedAgentValidator(model_name=model_name, endpoint = endpoint1, api_key=api_key1)
    b = DataExtractor(model_name=model_name,endpoint=endpoint1, api_key=api_key1, validator=x, settings = d)
    # b = DataExtractor(model_name='gemini:1.5-latest',settings=d, validator=x)
    with open('pages/dataset/bbc/attr_bbc___1___2023.html', 'r') as f:
        html = f.read()
    htmlx = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Sample Web Page</title>
    </head>
    <body>
        <header>
            <h1>Welcome to Our Store</h1>
        </header>

        <section id="product">
            <h2 class="product-name">Wireless Mouse</h2>
            <p class="product-description">A high-quality wireless mouse with ergonomic design.</p>
            <span class="product-price">$29.99</span>
        </section>

        <section id="news">
            <article class="news-item">
                <h2 class="news-title">Tech Industry Booms in 2025</h2>
                <p class="news-content">
                    The technology sector continues to grow rapidly, with new innovations emerging every day.
                </p>
                <span class="news-date">Published on: January 15, 2025</span>
                
            </article>
            <article class="news-item">
            <h2 class="news-title">Messi pass away</h2>
                <p class="news-content">
                    Lionel Messi is die and his wife marries with Rodrigo De Paul.
                </p>
                <span class="news-date">Published on: January 15, 2025</span>
             </article>
        </section>

        <footer>
            <p>Contact us at <a href="mailto:info@ourstore.com">info@ourstore.com</a></p>
        </footer>
    </body>
    </html>


    """
    # # try:
    # x = await b.extract("Extract all news headlines and their tag from the document.", html_content=html, selfconsistency = False, cot=True)
    # # except UnexpectedModelBehavior:
    # #     raise
    # print(x[0])
    # print(x[1])

    from gemini import Gemini
    llm = Gemini()
    x = llm(f'Extract headlines from this {html}')
    # print(x)
    # await test('bbc', b, True, True, 'code/results/bbc/gemini/with_refinement_with_cot', 'code/results/bbc/gemini')
    # await test2('bbc', b)
    # collect_errors('bbc')
    # remove_duplicates()
    # sort_txt()
    # x = BasedAgentValidator(model_name=model_name, endpoint=endpoint2, api_key=api_key2)
    # x = await x.validate(f"Extract for the following HTML each news title \n {html}", "[{'news_title': 'Tech Industry Booms in 2025'}]")
    # # print(x)
    # json_str = """{
    # "explanation": "The extracted data correctly matches the user query, which is to extract all news headlines and their tags from the document. The two news articles with their corresponding headlines and tags ('news') are accurately identified and extracted from the 'section id=\\"news\\"' in the HTML document. The HTML structure analysis confirms that the extracted data corresponds to the specified elements (h2 class=\\"news-title\\", p class=\\"news-content\\", span class=\\"news-date\\") within the news-item article classes.",
    # "is_valid": true
    # }"""

    # import json
    # print(json_str)
    # x = json.loads(json_str)
    # r = ValidatorResponse.model_validate_json(json_str)
asyncio.run(main())
