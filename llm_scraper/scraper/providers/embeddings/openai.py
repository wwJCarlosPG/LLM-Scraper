import time
from logging import getLogger

from openai import OpenAI, RateLimitError

from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.embedding_port import EmbeddingPort

BATCH_SIZE = 100
SLEEP_BETWEEN_BATCHES = 0.5  # seconds
logger = getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingPort):
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self._client = OpenAI(api_key=config.api_key)
        self.model_name = config.model_name

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i : i + BATCH_SIZE]
            embeddings.extend(self._embed_batch_with_retry(batch))
            if i + BATCH_SIZE < len(texts):
                time.sleep(SLEEP_BETWEEN_BATCHES)
        return embeddings

    def _embed_batch_with_retry(
        self, batch: list[str], max_retries: int = 5
    ) -> list[list[float]]:
        for attempt in range(max_retries):
            try:
                response = self._client.embeddings.create(
                    model=self.model_name, input=batch
                )
                return [item.embedding for item in response.data]
            except RateLimitError:
                wait = 2**attempt
                logger.warning(
                    f"Rate limit hit, waiting {wait}s (attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait)
        raise RuntimeError(f"Failed after {max_retries} retries due to rate limit")
