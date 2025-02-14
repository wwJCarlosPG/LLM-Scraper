from scraper_manager.application.entities.responses import ScrapedResponse, Response
from scraper_manager.application.interfaces.validator_interface import BaseValidator
from scraper_manager.infrastructure.exceptions.exceptions import InvalidResultDuringValidation, InvalidValidationFormat


class DefaultValidator(BaseValidator):
    """
    Default implementation of `BaseValidator` that validates scraped data 
    using the `ScrapedResponse` model.

    Methods:
        validate(data: str) -> Union[ValidatorResponse, ScrapedResponse]:
            Validates the given data and returns a `ScrapedResponse` object.
    """
    def __init__(self):
        """
        Initializes the DefaultValidator instance.
        """
        super().__init__()

    def validate(self, response_to_validate: str) -> ScrapedResponse:
        """
        Validate the extracted data by parsing it into a `ScrapedResponse` object.

        Args:
            data (str): JSON formatted string containing the scraped response.

        Returns:
            ScrapedResponse: The parsed and validated scraped data.
        """
        scraped_response = ScrapedResponse.model_validate_json(response_to_validate,strict=False)

        return scraped_response