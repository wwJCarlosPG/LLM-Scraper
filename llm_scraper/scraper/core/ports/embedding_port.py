from abc import ABC, abstractmethod


class EmbeddingPort(ABC):
    @abstractmethod
    def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for a list of texts.
        Each text is truncated or pooled internally to fit the model's token limit.

        Args:
            texts: list of texts to embed.

        Returns:
            list of embedding vectors, one per input text.
        """
        raise NotImplementedError()
