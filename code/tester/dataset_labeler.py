from fireworks.client import Fireworks
from tester.prompts import labeled_news_data_generator
class FireworksLLMLabeler:
    def __init__(self, api_key: str):
        self.api_key = api_key
        pass

    def labeling_dataset(self, html):
        client = Fireworks(api_key=self.api_key)
        response = client.chat.completions.create(
        model="accounts/fireworks/models/llama-v3p3-70b-instruct",
        messages=[{
        "role": "user",
        "content": labeled_news_data_generator() + '\n' + html,
        }],
        )
        return response.choices[0].message.content



