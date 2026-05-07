from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.embedding_port import EmbeddingPort
from scraper.providers.embeddings.base import BaseEmbeddingProvider


def get_embedding_provider(config: EmbeddingConfig) -> EmbeddingPort:
    return BaseEmbeddingProvider(config)
