import numpy as np
from sentence_transformers import SentenceTransformer

from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.embedding_port import EmbeddingPort


class BaseEmbeddingProvider(EmbeddingPort):
    def __init__(self, config: EmbeddingConfig):
        self.config = config
        self.max_tokens = config.max_tokens
        self._model = SentenceTransformer(config.model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        embeddings = []
        for text in texts:
            embedding = self._embed_single(text)
            embeddings.append(embedding)
        return embeddings

    def _embed_single(self, text: str) -> list[float]:
        token_ids = self._model.tokenizer(text, return_tensors="pt")["input_ids"][
            0
        ].tolist()

        if len(token_ids) <= self.max_tokens:
            return self._model.encode(text).tolist()

        sub_chunks = []
        for i in range(0, len(token_ids), self.max_tokens):
            sub_token_ids = token_ids[i : i + self.max_tokens]
            sub_text = self._model.tokenizer.decode(
                sub_token_ids, skip_special_tokens=True
            )
            sub_chunks.append(sub_text)

        sub_embeddings = self._model.encode(sub_chunks)
        mean_embedding = np.mean(sub_embeddings, axis=0)
        return mean_embedding.tolist()
