from pydantic import BaseModel

# No me queda claro si todo eso hereda de BaseModel
class ScrapedResponse(BaseModel):
    attr_name: str
    scraped_data: list[str]