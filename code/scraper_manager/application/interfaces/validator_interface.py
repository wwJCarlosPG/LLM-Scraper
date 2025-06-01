from abc import ABC, abstractmethod
from scraper_manager.core.entities.responses import ScrapedResponse, ValidatorResponse
import json

class BaseValidator(ABC):
    """
    Abstract base class for validators that assess the accuracy of extracted data 
    against a user-provided query.

    Methods:
        validate(user_query: str, html_content: str, response_to_validate: str) -> Union[ValidatorResponse, ScrapedResponse]:
            Abstract method to validate extracted data against a query.
    """

    @abstractmethod
    def validate(self, response_to_validate) -> ScrapedResponse:
        """
        Validate the extracted data against the provided user query.
        
        Args:
            response_to_validate (str): The data to be validated, typically in JSON format.

        Returns:
            Union[ValidatorResponse, ScrapedResponse]: 
            - `ValidatorResponse`: Contains validation status and an explanation.
            - `ScrapedResponse`: Represents a successful extraction result.
        """
        raise NotImplementedError()
    
    def self_validate(self, response_to_validate: str):
        """
        Validates the provided JSON string by converting it to a `ValidatorResponse` object.

        Args:
            data (str): JSON formatted string containing validation data.

        Returns:
            ValidatorResponse: A validated response object.
        """
        raise NotImplementedError()