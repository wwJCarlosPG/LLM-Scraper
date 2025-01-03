import os
from llm import LLM
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import *


class Gemini(LLM):
    def __init__(self) -> None:        
        load_dotenv()
        key = os.getenv("GEMINI_KEY")
        print(key)
        genai.configure(api_key=key)

        self.model = genai.GenerativeModel('gemini-pro')


    def __call__(self, query: str, temperature=1.0) -> str:
        safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        }
        
        response = self.model.generate_content(
            query, 
            generation_config=genai.types.GenerationConfig(temperature=temperature),
            safety_settings=safety_settings
        )
        
        return response.text