from pydantic import BaseModel, Field
class Model:
    def __init__(self, model_name: str, api_key: str = None):
        self.model_name = model_name
        self.api_key = api_key
        pass


class ScrapedData(BaseModel):
    scraped_data: list[str] = Field(description='Scraped data from HTML')
    xpath: str = Field(description='Xpath where the data is') # esto no me queda claro

