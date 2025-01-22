from fireworks.client import Fireworks
from pydantic_ai import Agent, Tool, RunContext
from dotenv import load_dotenv
from scraper.adaptative_scraper.adaptative_scraper import AdaptativeScraper
import asyncio
# api_key = "fw_3ZKL6bqRbTf3SGtNKBLc9LGM"
# endpoint = "https://api.fireworks.ai/inference/v1/completions"
# model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"
# b = AdaptativeSraper(model_name, '', endpoint, api_key)
# html = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Sample Web Page</title>
# </head>
# <body>
#     <header>
#         <h1>Welcome to Our Store</h1>
#     </header>

#     <section id="product">
#         <h2 class="product-name">Wireless Mouse</h2>
#         <p class="product-description">A high-quality wireless mouse with ergonomic design.</p>
#         <span class="product-price">$29.99</span>
#     </section>

#     <section id="news">
#         <article class="news-item">
#             <h2 class="news-title">Tech Industry Booms in 2025</h2>
#             <p class="news-content">
#                 The technology sector continues to grow rapidly, with new innovations emerging every day.
#             </p>
#             <span class="news-date">Published on: January 15, 2025</span>
#         </article>
#     </section>

#     <footer>
#         <p>Contact us at <a href="mailto:info@ourstore.com">info@ourstore.com</a></p>
#     </footer>
# </body>
# </html>


# """
# x = b.run("Extract for the following HTML each product name", html)


async def main():
    api_key = "fw_3ZKL6bqRbTf3SGtNKBLc9LGM"
    endpoint = "https://api.fireworks.ai/inference/v1/chat/completions"
    model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"

    b = AdaptativeScraper(model_name, '', endpoint, api_key)
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
    x = await b.run("Extract for the following HTML each news title", html)
    print(x)

# Ejecutar la función principal asíncrona
asyncio.run(main())
# print(x.data)
# b = BuilInAdaptativeScraper(None)
# x = b.run("Is this an HTML?", 'HTML')
# print(x.data)

# client = Fireworks(api_key="fw_3ZKL6bqRbTf3SGtNKBLc9LGM")

# response = client.chat.completions.create(
# model="accounts/fireworks/models/llama-v3p3-70b-instruct",
# messages=[{
#    "role": "user",
#    "content": 'Is this an HTML?: \n'+ content,
# }],
# )

# api_key = "fw_3ZKL6bqRbTf3SGtNKBLc9LGM"
# endpoint = "https://api.fireworks.ai/inference/v1/chat/completions"
# model_name = "accounts/fireworks/models/llama-v3p3-70b-instruct"

# headers = {
#     "Authorization": f"Bearer {api_key}",
#     "Content-Type": "application/json",
# }

# payload = {
#     "model": model_name,
#     "messages": [
#         {
#             "role": "user",
#             "content": "Is this an HTML? Answer me with yes or no: \n" + 'html',
#         }
#     ],
# }

# response = requests.post(endpoint, json=payload, headers=headers)

# print(response.json)
# print(response.json()['choices'][0]['message']['content'])



# # p = random_prompt(content)
# # llm = Gemini()

# # x = llm(p)

# # print(x)


# Example: reuse your existing OpenAI setup
# from openai import OpenAI

# # Point to the local server
# client = OpenAI(base_url="http://localhost:1234/v1", api_key="lm-studio")
# html = BuilInAdaptativeScraper.clean_html('code/test.html',['script', 'style'], True)
# path = "pages/augmented_pages/bbc___12___2022.html"
# html = BuilInAdaptativeScraper.clean_html(path, ['script', 'style'], True)
# completion = client.completions.create(
#         model="model-bartowski/Llama-3.2-3B-Instruct-GGUF/Llama-3.2-3B-Instruct-Q8_0",
#         prompt=f'''
#         You are an expert in extracting structured information from HTML. Extract the main news articles from the following static HTML content. 

#         For each article, identify:
#         1. The headline.
#         2. The summary or description.
#         3. The link to the full article.

#         Provide the response in a structured JSON array.

#         Here is the HTML content:
#         {html}
#         ''',
#         temperature=0.4,
#         max_tokens=500  # Ajusta según la longitud esperada de la respuesta
#     )

# print(completion.choices[0].text)