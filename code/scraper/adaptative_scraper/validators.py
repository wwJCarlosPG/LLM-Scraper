from scraper.external_models.external import ExternalResponse # ver que hacer con esto si el modelo es built-in

def external_validator(response: str):
    validated_response = ExternalResponse.model_validate_json(response)
    return validated_response
    