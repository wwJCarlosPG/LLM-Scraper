from sentence_transformers import util

from scraper.core.ports.embedding_port import EmbeddingPort

LEXICAL_THRESHOLD = 0.5
SEMANTIC_THRESHOLD = 0.30
STOPWORDS = {
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "will",
    "would",
    "could",
    "should",
    "to",
    "of",
    "in",
    "on",
    "at",
    "for",
    "with",
    "by",
    "from",
    "it",
    "its",
    "this",
    "that",
    "and",
    "or",
    "but",
}


def is_lexically_grounded(item: dict, content: str) -> bool:
    """Lexical overlap: at least 50% of content words appear in content."""
    item_text = _item_to_text(item)
    words = set(item_text.lower().split()) - STOPWORDS
    if not words:
        return True
    content_lower = content.lower()
    matches = sum(1 for w in words if w in content_lower)
    return matches / len(words) >= LEXICAL_THRESHOLD


def is_semantically_grounded(item: dict, content: str, embedder: EmbeddingPort) -> bool:
    """Semantic similarity: item embedding vs content embedding >= threshold."""
    item_text = _item_to_text(item)
    try:
        item_emb = embedder.embed([item_text])[0]
        content_emb = embedder.embed([content[:3000]])[0]  # limit content size
        sim = util.cos_sim(item_emb, content_emb).item()
        return sim >= SEMANTIC_THRESHOLD
    except Exception:
        return True  # fallback: assume valid if embedding fails


def _item_to_text(item: dict) -> str:
    values = []
    for v in item.values():
        if isinstance(v, list):
            values.extend(str(x) for x in v)
        else:
            values.append(str(v))
    return " ".join(values)
