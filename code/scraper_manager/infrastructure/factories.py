from scraper_manager.infrastructure.extractors.extractor import DataExtractor
from scraper_manager.infrastructure.validators.basedagent_validator import BasedAgentValidator
from scraper_manager.infrastructure.html_cleaners.default_html_cleaner import DefaultHTMLCleaner
from scraper_manager.infrastructure.storages.local_storage import LocalStorage # cambiar esto para que haya base de datos.

def get_extractor():
    return DataExtractor(
        model_name="gemini-1.5-pro",
        validator= BasedAgentValidator(
            model_name="gemini-1.5-pro"
        )
    )

def get_htmlcleaner():
    return DefaultHTMLCleaner()

def get_storage():
    return LocalStorage()