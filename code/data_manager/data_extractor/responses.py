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

        feedback (str): A detailed justification of the validation outcome, 
            describing why the extracted data is considered correct or incorrect 
            based on the provided HTML content and query.

        is_valid (bool): A boolean flag indicating the validation result.
            - True if the extracted data is accurate and satisfies the query.
            - False if the extracted data does not meet the query requirements.
    """
    explanation: str = Field(
        description="Detailed reasoning or context provided by the system explaining the extracted data or process."
    )
    scraped_data: list[dict[str, str]] = Field(
        description="A list of extracted key-value pairs from the provided source, representing structured data such as product details, article information, or other relevant content.",
        alias='final_answer'
    )
    feedback: str = Field(
        description="A detailed explanation justifying the validity or invalidity of the extracted data based on the query and HTML content.",
        default=None
    )
    is_valid: bool = Field(
        description="A boolean indicating whether the extracted data is correct (True) or incorrect (False) based on the validation.",
        default=True
    )

    
