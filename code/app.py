import asyncio
from pydantic_ai.exceptions import UnexpectedModelBehavior
from data_manager.data_extractor.data_extractor import DataExtractor
from data_manager.validators.default_validators import BasedAgentValidator

async def main():
    api_key1 = 'lm-studio'
    api_key2 = "fw_3ZKL6bqRbTf3SGtNKBLc9LGM"
    endpoint1 = 'http://localhost:1234/v1/chat/completions'
    endpoint2 = "https://api.fireworks.ai/inference/v1/chat/completions"
    model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
    # x = BasedAgentValidator(model_name=model_name, endpoint=endpoint2, api_key=api_key2)

    # b = DataExtractor(model_name=model_name,endpoint=endpoint2, api_key=api_key2, validator=x)
    html = """
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
    # try:
    #     x = await b.extract("Extract for the following HTML each news title", html_content=html)
    # except UnexpectedModelBehavior:
    #     raise
    # print(x)
    x = BasedAgentValidator(model_name=model_name, endpoint=endpoint2, api_key=api_key2)
    x = await x.validate(f"Extract for the following HTML each news title \n {html}", "[{'news_title': 'Tech Industry Booms in 2025'}]")
    print(x)
asyncio.run(main())
