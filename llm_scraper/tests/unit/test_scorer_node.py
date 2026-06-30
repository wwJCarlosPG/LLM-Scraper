from scraper.core.consts import EDGE_SCORE, EDGE_SKIP_SCORE
from scraper.core.entities.config import PipelineConfig, ProviderConfig
from scraper.pipeline.graph import _should_score


def make_state(chunks: list[str], top_k_chunks: int) -> dict:
    config = PipelineConfig(
        extractor_provider=ProviderConfig(
            provider="openai_compatible",
            model_name="test-model",
            endpoint="http://localhost",
            env_alias="TEST_KEY",
        ),
        validator_provider=ProviderConfig(
            provider="openai_compatible",
            model_name="test-model",
            endpoint="http://localhost",
            env_alias="TEST_KEY",
        ),
        top_k_chunks=top_k_chunks,
    )
    return {"chunks": chunks, "config": config}


def test_should_score_when_chunks_exceed_top_k():
    state = make_state(chunks=["a", "b", "c", "d", "e", "f"], top_k_chunks=3)
    assert _should_score(state) == EDGE_SCORE


def test_should_skip_when_chunks_lte_top_k():
    state = make_state(chunks=["a", "b", "c"], top_k_chunks=5)
    assert _should_score(state) == EDGE_SKIP_SCORE


def test_should_skip_when_no_chunks():
    state = make_state(chunks=[], top_k_chunks=5)
    assert _should_score(state) == EDGE_SKIP_SCORE


def test_should_skip_when_chunks_equal_top_k():
    state = make_state(chunks=["a", "b", "c"], top_k_chunks=3)
    assert _should_score(state) == EDGE_SKIP_SCORE
