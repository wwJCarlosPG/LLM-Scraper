import asyncio
from pydantic_ai.exceptions import UnexpectedModelBehavior
from scraper_manager.application.extraction.extractor import DataExtractor
from scraper_manager.application.validation.validators import BasedAgentValidator, ValidatorResponse
from dataset_work.data_augmenter import main
from tester.run import test, collect_errors, sort_txt, remove_duplicates, test2, make_equal_queries, generate_labeled_dataset
from typing import Tuple
from dotenv import load_dotenv
import jsonschema
# main()

async def main():
    load_dotenv()
    api_key1 = 'lm-studio'
    api_key2 = "fw_3ZTGqYGPQoYjhmgeUGwBztzD"
    endpoint1 = 'http://172.20.10.3:1234/v1/chat/completions'
    endpoint2 = "https://api.fireworks.ai/inference/v1/chat/completions"
    model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    # model_name = 'llama-3-8b-instruct'
    d = {"temperature": 0.6, "max_tokens":1000, "timeout":120.0}
    

    x = BasedAgentValidator(model_name=model_name, endpoint = endpoint2, api_key=api_key2)
    b = DataExtractor(model_name=model_name,endpoint=endpoint2, api_key=api_key2, validator=x)
    # b = DataExtractor(model_name='gemini:1.5-latest',settings=d, validator=x)
    # with open('pages/dataset/bbc/attr_bbc___12___2011.html', 'r') as f:
    #     html = f.read()
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


    # """
    generate_labeled_dataset()
    # # try:
    # x = await b.extract("Extract all news headlines and their tag from the document.", html_content=htmlx, selfconsistency = False, cot=True)
    # # # except UnexpectedModelBehavior:
    # # #     raise
    # print(x[0])
    # print(x[1])
    # from scraper_manager.application.extraction.responses import ScrapedResponse
    # print(ScrapedResponse.model_json_schema())
    # from gemini import Gemini
    # llm = Gemini()
    # x = llm(f'Extract headlines from this {html}')
    # print(x)
    # await test('bbc', b, True, True, True, 'code/results/bbc/llama3.3-70B/with_selfconsistency', 'code/results/bbc/llama3.3-70B')
    # await test2('bbc', b, 'llama3.3-70B', refinement=False, cot=True)
    # make_equal_queries()
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

    # jsosss = {"responses": 
    #             [
    #                 {
    #                 "explanation": "Extracted news headlines from the 'news_id' module. The headlines include 'Last US troops withdraw from Iraq', 'Mass burial for Philippines dead', 'Obama signs funding bill into law', 'Tributes paid after Havel's death', 'Army 'failed' in Wikileaks case', 'Iran TV shows 'US spy confession'', and 'Woman set alight in New York elevator'.",
    #                 "final_answer": [
    #                     {"headline": "Last US troops withdraw from Iraq", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-middle-east-16234723"},
    #                     {"headline": "Mass burial for Philippines dead", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-asia-16239691"},
    #                     {"headline": "Obama signs funding bill into law", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-us-canada-16232716"},
    #                     {"headline": "Tributes paid after Havel's death", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-europe-16239397"},
    #                     {"headline": "Army 'failed' in Wikileaks case", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-us-canada-16239198"},
    #                     {"headline": "Iran TV shows 'US spy confession'", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-middle-east-16239022"},
    #                     {"headline": "Woman set alight in New York elevator", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/world-us-canada-16236866"}
    #             ]
    #                 },
    #                 {
    #                     "explanation": "Extracted news headlines from the 'drawers_id' module under the 'Entertainment & Arts' section. The headlines include 'Barefoot diva' Evora dies at 70, Beach Boys to get back together, Tributes flood in for Hitchens, McFly's Judd wins Strictly crown, Wood and Lee land comedy prizes, Taylor NY auction fetches $150m, Russell Brand lands US TV series, Stern lands US talent show role, Kinks star watches school play, and Bale barred from Chinese activist.",
    #                     "final_answer": [
    #                         {"headline": "Barefoot diva' Evora dies at 70", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16232543"},
    #                         {"headline": "Beach Boys to get back together", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16232009"},
    #                         {"headline": "Tributes flood in for Hitchens", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/uk-16226580"},
    #                         {"headline": "McFly's Judd wins Strictly crown", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16224867"},
    #                         {"headline": "Wood and Lee land comedy prizes", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16229511"},
    #                         {"headline": "Taylor NY auction fetches $150m", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16229983"},
    #                         {"headline": "Russell Brand lands US TV series", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16213869"},
    #                         {"headline": "Stern lands US talent show role", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/entertainment-arts-16213862"},
    #                         {"headline": "Kinks star watches school play", "link": "https://web.archive.org/web/20111219044740/http://www.bbc.co.uk/news/uk-england-cumbria-16230596"},


asyncio.run(main())
