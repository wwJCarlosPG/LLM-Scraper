from extractors.extractor import DataExtractor
from validators.basedagent_validator import BasedAgentValidator
from html_cleaners.default_html_cleaner import DefaultHTMLCleaner
from storages.local_storage import LocalStorage # cambiar esto para que haya base de datos.

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