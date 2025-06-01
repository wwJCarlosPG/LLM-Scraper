from pydantic import BaseModel
from typing import Annotated
class ScrapedResponse(BaseModel):
    scraped_data: Annotated[dict, "The scraped text content"] 
    tokens: Annotated[int, "The number of tokens in the scraped data"]

class ScrapedRequest(BaseModel):
    url: Annotated[str, "The URL to scrape"]
    query: Annotated[str, "The query to extract specific data from the content of the URL"]
    
