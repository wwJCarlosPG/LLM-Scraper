from pydantic import BaseSettings
# aqui digamos que hay una fabrica de cómo se debe configurar cada una de las clases, esto puede ser extensible
class ExtractorSettings(BaseSettings):
    model_name: str = "gemini-1.5-pro"
    

    # pensar que hacer con el validator.

    class Config:
        env_file = '.env'


class ValidatorSettings(BaseSettings):
    model_name = "gemini-1.5-pro"