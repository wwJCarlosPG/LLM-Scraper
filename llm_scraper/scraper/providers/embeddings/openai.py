from openai import OpenAI

from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.embedding_port import EmbeddingPort


class OpenAIEmbeddingProvider(EmbeddingPort):
    """
    OpenAI embedding provider.
    Supports text-embedding-3-small and text-embedding-3-large.
    No token limit handling needed as the API handles it internally.
    """

    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._client = OpenAI(api_key=config.api_key)
        self.model_name = config.model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model=self.model_name, input=texts)
        return [item.embedding for item in response.data]
