from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.embedding_port import EmbeddingPort
from scraper.providers.embeddings.base import BaseEmbeddingProvider
from scraper.providers.embeddings.openai import OpenAIEmbeddingProvider


def get_embedding_provider(config: EmbeddingConfig) -> EmbeddingPort:
    if config.provider == "openai":
        resolved_config = config.model_copy(
            update={"api_key": config.resolve_api_key()}
        )
        return OpenAIEmbeddingProvider(resolved_config)
    return BaseEmbeddingProvider(config)
