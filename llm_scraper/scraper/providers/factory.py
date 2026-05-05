from scraper.core.entities.config import PipelineConfig
from scraper.core.ports.llm_port import LLMPort
from scraper.providers.anthropic import AnthropicProvider
from scraper.providers.gemini import GeminiProvider
from scraper.providers.openai import OpenAIProvider
from scraper.providers.openai_compatible import OpenAICompatibleProvider


def get_provider(config: PipelineConfig) -> LLMPort:
    provider_name = config.provider.provider
    max_tokens = config.max_tokens

    if provider_name == "gemini":
        return GeminiProvider(config.provider, max_tokens)
    elif provider_name == "openai":
        return OpenAIProvider(config.provider, max_tokens)
    elif provider_name == "anthropic":
        return AnthropicProvider(config.provider, max_tokens)
    elif provider_name == "openai_compatible":
        return OpenAICompatibleProvider(config.provider, max_tokens)
    else:
        raise ValueError(f"Provider '{provider_name}' is not supported yet.")
