from scraper.core.entities.config import PipelineConfig
from scraper.core.ports.llm_port import LLMPort
from scraper.providers.gemini import GeminiProvider
from scraper.providers.openai_compatible import OpenAICompatibleProvider


def get_provider(config: PipelineConfig) -> LLMPort:
    provider_name = config.provider.provider

    if provider_name == "gemini":
        return GeminiProvider(config.provider)
    elif provider_name == "openai_compatible":
        return OpenAICompatibleProvider(config.provider)
    else:
        raise ValueError(f"Provider '{provider_name}' is not supported yet.")
