import numpy as np
import pytest
from sentence_transformers import util

from scraper.adapters.html.relevance_scorer import RelevanceScorer
from scraper.core.entities.config import EmbeddingConfig
from scraper.providers.embeddings.base import BaseEmbeddingProvider
from scraper.providers.embeddings.factory import get_embedding_provider


@pytest.fixture(scope="module")
def scorer():
    config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
    provider = get_embedding_provider(config)
    return RelevanceScorer(provider)


@pytest.fixture(scope="module")
def provider():
    config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return BaseEmbeddingProvider(config)


def test_relevant_chunk_ranked_first(scorer):
    query = "What is the price of the MacBook Pro?"
    chunks = [
        "Navigation: Home About Contact Blog Newsletter Privacy Policy",
        "The MacBook Pro 14-inch starts at $1999 and includes M3 chip.",
        "Follow us on Twitter Facebook Instagram LinkedIn YouTube",
    ]

    ranked, _ = scorer.rank(query=query, chunks=chunks, top_k=1)

    assert len(ranked) == 1
    assert "MacBook Pro" in ranked[0]
    assert "1999" in ranked[0]


def test_top_k_respected(scorer):
    query = "scientific discovery in the Amazon"
    chunks = [
        "Dr. Smith discovered a new frog species in the Amazon rainforest.",
        "Cookie settings: accept all or manage preferences.",
        "Researchers found new plant species during Amazon expedition.",
        "Subscribe to our newsletter for weekly updates.",
    ]

    ranked, _ = scorer.rank(query=query, chunks=chunks, top_k=2)

    assert len(ranked) == 2
    assert all(
        "Amazon" in chunk or "species" in chunk or "discovery" in chunk
        for chunk in ranked
    )


def test_no_ranking_when_chunks_lte_top_k(scorer):
    query = "anything"
    chunks = ["chunk 1", "chunk 2"]

    result, _ = scorer.rank(query=query, chunks=chunks, top_k=3)

    assert result == chunks


def test_scores_are_higher_for_relevant_chunks(scorer):
    query = "product prices and discounts"
    relevant = "MacBook Pro $1999, iPhone $999, iPad $599 - all on sale today."
    irrelevant = "Contact us at support@example.com for any questions."

    chunks = [irrelevant, relevant]
    ranked, _ = scorer.rank(query=query, chunks=chunks, top_k=1)

    assert ranked[0] == relevant


def test_mean_pooling_returns_single_vector(provider):
    """
    Verifies that a text longer than max_tokens still produces
    a single embedding vector of the correct dimension.
    """
    # generate a text that exceeds 256 tokens
    long_text = " ".join(["word"] * 600)
    embedding = provider._embed_single(long_text)

    assert isinstance(embedding, list)
    assert len(embedding) == 384  # MiniLM output dimension


def test_mean_pooling_vs_direct_embed_similar(provider):
    """
    Verifies that the mean pooled embedding of a long text
    is semantically close to the direct embedding of the same
    text truncated, not a random vector.
    """
    short_text = " ".join(["scientists discovered new species"] * 10)
    long_text = short_text * 5
    unrelated_text = " ".join(["football match stadium goals penalty"] * 10)

    short_embedding = provider._embed_single(short_text)
    long_embedding = provider._embed_single(long_text)
    unrelated_embedding = provider._embed_single(unrelated_text)

    similarity_related = util.cos_sim(short_embedding, long_embedding).item()
    similarity_unrelated = util.cos_sim(long_embedding, unrelated_embedding).item()

    # the long embedding should be more similar to the related short text than the unrelated text
    assert similarity_related > similarity_unrelated


def test_short_text_does_not_use_pooling(provider):
    """
    Verifies that a short text bypasses mean pooling
    and is embedded directly.
    """
    short_text = "hello world"
    token_ids = provider._model.tokenizer(short_text, return_tensors="pt")["input_ids"][
        0
    ].tolist()

    assert len(token_ids) <= provider.max_tokens

    embedding = provider._embed_single(short_text)
    assert isinstance(embedding, list)
    assert len(embedding) == 384


def test_mean_is_average_of_sub_embeddings(provider):
    """
    Verifies that the mean pooling result is mathematically
    the average of the sub-chunk embeddings.
    """
    long_text = " ".join(["machine learning natural language processing"] * 50)
    token_ids = provider._model.tokenizer(long_text, return_tensors="pt")["input_ids"][
        0
    ].tolist()

    # manually compute sub-chunks
    sub_chunks = []
    for i in range(0, len(token_ids), provider.max_tokens):
        sub_token_ids = token_ids[i : i + provider.max_tokens]
        sub_text = provider._model.tokenizer.decode(
            sub_token_ids, skip_special_tokens=True
        )
        sub_chunks.append(sub_text)

    sub_embeddings = provider._model.encode(sub_chunks)
    expected_mean = np.mean(sub_embeddings, axis=0).tolist()

    result = provider._embed_single(long_text)

    assert np.allclose(result, expected_mean, atol=1e-5)
