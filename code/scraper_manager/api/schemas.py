from pydantic import BaseModel

class ScrapedResponse(BaseModel):
    text: str
    tokens: int

class ScrapedRequest(BaseModel):
    url: str
    query: str
    
