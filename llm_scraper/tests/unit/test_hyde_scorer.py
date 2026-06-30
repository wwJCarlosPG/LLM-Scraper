import pytest

from scraper.adapters.html.hyde_scorer import HyDEScorer
from scraper.core.entities.config import EmbeddingConfig
from scraper.core.ports.llm_port import LLMPort
from scraper.providers.embeddings.factory import get_embedding_provider


class MockLLM(LLMPort):
    """
    Mock LLM that returns a predefined hypothetical document.
    Avoids real API calls in unit tests while still exercising
    the HyDE embedding logic with real embeddings.
    """

    def __init__(self, response: str):
        self.response = response

    def invoke(self, user_prompt: str, system_prompt: str) -> str:
        return self.response

    async def ainvoke(self, user_prompt: str, system_prompt: str) -> str:
        return self.response


class FailingLLM(LLMPort):
    """LLM that always fails, to test the fallback behavior."""

    def invoke(self, user_prompt: str, system_prompt: str) -> str:
        raise RuntimeError("LLM unavailable")

    async def ainvoke(self, user_prompt: str, system_prompt: str) -> str:
        raise RuntimeError("LLM unavailable")


@pytest.fixture(scope="module")
def embedder():
    config = EmbeddingConfig(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return get_embedding_provider(config)


@pytest.fixture(scope="module")
def scorer(embedder):
    llm = MockLLM("MacBook Pro 14-inch $1999, MacBook Air $1099, iPhone 15 Pro $999")
    return HyDEScorer(llm=llm, embedding_provider=embedder, domain="ecommerce")


def test_relevant_chunk_ranked_first(scorer):
    query = "What is the price of the MacBook Pro?"
    chunks = [
        "Navigation: Home About Contact Blog Newsletter Privacy Policy",
        "The MacBook Pro 14-inch starts at $1999 and includes M3 chip.",
        "Follow us on Twitter Facebook Instagram LinkedIn YouTube",
    ]

    ranked, _, _ = scorer.rank(query=query, chunks=chunks, top_k=1)

    assert len(ranked) == 1
    assert "MacBook Pro" in ranked[0]


def test_top_k_respected(scorer):
    query = "laptop prices"
    chunks = [
        "MacBook Pro 14-inch $1999, M3 chip, 18GB RAM.",
        "Subscribe to our newsletter for weekly updates.",
        "MacBook Air 13-inch $1099, M2 chip, 8GB RAM.",
        "Cookie policy: we use cookies to improve your experience.",
    ]

    ranked, _, _ = scorer.rank(query=query, chunks=chunks, top_k=2)

    assert len(ranked) == 2


def test_no_ranking_when_chunks_lte_top_k(scorer):
    query = "anything"
    chunks = ["chunk 1", "chunk 2"]

    result, scores, _ = scorer.rank(query=query, chunks=chunks, top_k=3)

    assert result == chunks
    assert scores == [1.0, 1.0]


def test_compute_scores_sorts_when_chunks_lte_top_k(scorer):
    """When compute_scores=True, chunks are sorted even if len <= top_k."""
    query = "MacBook price"
    chunks = [
        "Cookie policy: we use cookies.",
        "MacBook Pro 14-inch starts at $1999.",
    ]

    ranked, scores, _ = scorer.rank(
        query=query, chunks=chunks, top_k=5, compute_scores=True
    )

    assert len(ranked) == 2
    assert "MacBook" in ranked[0]
    assert scores[0] >= scores[1]


def test_hypothetical_embedding_is_cached(embedder):
    """LLM should only be called once for the same query."""
    call_count = {"n": 0}

    class CountingLLM(LLMPort):
        def invoke(self, user_prompt, system_prompt):
            call_count["n"] += 1
            return "some hypothetical content"

        async def ainvoke(self, user_prompt, system_prompt):
            call_count["n"] += 1
            return "some hypothetical content"

    scorer = HyDEScorer(llm=CountingLLM(), embedding_provider=embedder)
    chunks = ["chunk a", "chunk b", "chunk c", "chunk d", "chunk e", "chunk f"]

    scorer.rank(query="same query", chunks=chunks, top_k=2)
    scorer.rank(query="same query", chunks=chunks, top_k=2)

    assert call_count["n"] == 1


def test_fallback_to_query_when_llm_fails(embedder):
    """If LLM fails, scorer falls back to raw query embedding without crashing."""
    scorer = HyDEScorer(llm=FailingLLM(), embedding_provider=embedder)
    chunks = [
        "MacBook Pro $1999",
        "Cookie policy",
        "MacBook Air $1099",
        "Newsletter signup",
    ]

    ranked, scores, _ = scorer.rank(query="laptop prices", chunks=chunks, top_k=2)

    assert len(ranked) == 2
    assert len(scores) == 2


def test_domain_instruction_used(embedder):
    """
    Documentation domain should surface documentation-style chunks
    over unrelated content.
    """
    llm = MockLLM(
        "Installation: run pip install mypackage. "
        "Configuration: set the API_KEY environment variable."
    )
    scorer = HyDEScorer(llm=llm, embedding_provider=embedder, domain="documentation")

    query = "How do I install and configure the package?"
    chunks = [
        "pip install mypackage. Set API_KEY=your_key in your environment.",
        "Follow us on Twitter and LinkedIn for updates.",
        "Copyright 2024 MyCompany. All rights reserved.",
        "Contact support at help@mycompany.com",
    ]

    ranked, _, _ = scorer.rank(query=query, chunks=chunks, top_k=1)

    assert "pip install" in ranked[0] or "API_KEY" in ranked[0]
