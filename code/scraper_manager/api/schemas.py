from pydantic import BaseModel, Field
from typing import Annotated
class ScrapedResponse(BaseModel):
    """Scraped response model.
    """
    scraped_data: dict = Field(description = "The scraped text content")
    tokens: str = Field(description = "The number of tokens in the scraped data")

class ScrapedRequest(BaseModel):
    """Scraped request model
    """
    url: str = Field(description="The URL to scrape")
    query: str = Field(description="The query to extract specific data from the content of the URL")
    output_format: dict = Field(description="The format of the output")


class User(BaseModel):
    name: str = Field(description="The user's name")
    password: str = Field(description="The user's password")
    id: int = Field(description="The user's id")
    
