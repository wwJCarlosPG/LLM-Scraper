from pydantic import BaseModel, Field

class ScrapedResponse(BaseModel):
    """
    Represents the structured response obtained from a web scraping process.

    This model captures both the extracted data and an explanation of the process, 
    providing insights into how the data was retrieved and structured.

    Attributes:
        explanation (str): 
            Detailed reasoning or context provided by the system explaining 
            the extracted data or process.
        
        scraped_data (list[dict[str, str]]): 
            A list of extracted key-value pairs from the provided source, 
            representing structured data such as product details, 
            article information, or other relevant content. 
            This field is aliased as 'final_answer' when dealing with external data.
    """
    explanation: str = Field(
        description="Detailed reasoning or context provided by the system explaining the extracted data or process."
    )
    scraped_data: list[dict[str, str]] = Field(
        description="A list of extracted key-value pairs from the provided source, representing structured data such as product details, article information, or other relevant content.",
        alias='final_answer'
    )
