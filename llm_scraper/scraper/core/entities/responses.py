from typing import Any

from pydantic import BaseModel, Field


class ScrapedResponse(BaseModel):
    explanation: str = Field(
        description="Reasoning behind the extraction.", default="No explanation"
    )
    scraped_data: list[dict[str, Any]] = Field(
        description="List of extracted key-value pairs.", default=[]
    )
    feedback: str | None = Field(
        description="Validator feedback on the extracted data.", default=None
    )
    is_valid: bool = Field(
        description="Whether the extracted data is valid.", default=True
    )
    refinement_count: int = Field(
        description="Number of refinement iterations performed.", default=0
    )


class ValidatorResponse(BaseModel):
    explanation: str = Field(description="Reasoning behind the validation result.")
    is_valid: bool = Field(
        description="Whether the extracted data satisfies the query."
    )
