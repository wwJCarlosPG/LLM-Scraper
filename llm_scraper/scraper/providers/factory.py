from scraper.core.entities.config import ProviderConfig
from scraper.core.ports.llm_port import LLMPort
from scraper.providers.anthropic import AnthropicProvider
from scraper.providers.gemini import GeminiProvider
from scraper.providers.openai import OpenAIProvider
from scraper.providers.openai_compatible import OpenAICompatibleProvider


def get_provider(config: ProviderConfig) -> LLMPort:
    provider_name = config.provider

    if provider_name == "gemini":
        return GeminiProvider(config)
    elif provider_name == "openai":
        return OpenAIProvider(config)
    elif provider_name == "anthropic":
        return AnthropicProvider(config)
    elif provider_name == "openai_compatible":
        return OpenAICompatibleProvider(config)
    else:
        raise ValueError(f"Provider '{provider_name}' is not supported yet.")
