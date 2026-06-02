from langgraph.graph import END, StateGraph

from scraper.core.consts import (
    EDGE_MERGE,
    EDGE_REFINE,
    EDGE_SCORE,
    EDGE_SKIP_SCORE,
    EDGE_SKIP_VALIDATE,
    EDGE_VALIDATE,
    NODE_CHUNKER,
    NODE_CLEANER,
    NODE_EXTRACTOR,
    NODE_MERGER,
    NODE_SCORER,
    NODE_VALIDATOR,
)
from scraper.core.entities.state import PipelineState
from scraper.pipeline.groundedness import (
    is_lexically_grounded,
    is_semantically_grounded,
)
from scraper.pipeline.nodes.chunker import chunker_node
from scraper.pipeline.nodes.cleaner import cleaner_node
from scraper.pipeline.nodes.extractor import extractor_node
from scraper.pipeline.nodes.merger import merger_node
from scraper.pipeline.nodes.scorer import scorer_node
from scraper.pipeline.nodes.validator import validator_node


def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    graph.add_node(NODE_CLEANER, cleaner_node)
    graph.add_node(NODE_CHUNKER, chunker_node)
    graph.add_node(NODE_SCORER, scorer_node)
    graph.add_node(NODE_EXTRACTOR, extractor_node)
    graph.add_node(NODE_MERGER, merger_node)
    graph.add_node(NODE_VALIDATOR, validator_node)

    graph.set_entry_point(NODE_CLEANER)
    graph.add_edge(NODE_CLEANER, NODE_CHUNKER)

    graph.add_conditional_edges(
        NODE_CHUNKER,
        _should_score,
        {EDGE_SCORE: NODE_SCORER, EDGE_SKIP_SCORE: NODE_EXTRACTOR},
    )

    graph.add_edge(NODE_SCORER, NODE_EXTRACTOR)
    graph.add_edge(NODE_EXTRACTOR, NODE_MERGER)
    graph.add_edge(NODE_MERGER, END)

    graph.add_conditional_edges(
        NODE_VALIDATOR,
        _should_refine,
        {EDGE_REFINE: NODE_EXTRACTOR, EDGE_MERGE: NODE_MERGER},
    )
    graph.add_conditional_edges(
        NODE_EXTRACTOR,
        _should_validate,
        {EDGE_VALIDATE: NODE_VALIDATOR, EDGE_SKIP_VALIDATE: NODE_MERGER},
    )

    return graph.compile()


def _should_validate(state: PipelineState) -> str:
    config = state.get("config")
    if not config.refinement:
        return EDGE_SKIP_VALIDATE
    return EDGE_VALIDATE


def _should_validate_v2(state: PipelineState) -> str:
    config = state.get("config")
    current_response = state.get("current_response")
    chunks = state.get("chunks")
    partial_responses = state.get("partial_responses")

    if not config.refinement:
        return EDGE_SKIP_VALIDATE

    if current_response and not current_response.is_valid:
        return EDGE_VALIDATE

    if not current_response or not current_response.scraped_data:
        return EDGE_VALIDATE

    # heuristic: lexical check per partial_response/chunk pair
    if chunks and partial_responses:
        for resp, chunk in zip(partial_responses, chunks, strict=True):
            for item in resp.scraped_data or []:
                if not is_lexically_grounded(item, chunk):
                    return EDGE_VALIDATE
    elif not chunks:
        cleaned_html = state.get("cleaned_html") or ""
        for item in current_response.scraped_data:
            if not is_lexically_grounded(item, cleaned_html):
                return EDGE_VALIDATE

    # heuristic: semantic similarity
    try:
        from scraper.providers.embeddings.factory import get_embedding_provider

        embedder = get_embedding_provider(config.embedding)

        if chunks and partial_responses:
            for resp, chunk in zip(partial_responses, chunks, strict=True):
                for item in resp.scraped_data or []:
                    if not is_semantically_grounded(item, chunk, embedder):
                        return EDGE_VALIDATE
        elif not chunks:
            cleaned_html = state.get("cleaned_html") or ""
            for item in current_response.scraped_data:
                if not is_semantically_grounded(item, cleaned_html, embedder):
                    return EDGE_VALIDATE
    except Exception:
        return EDGE_VALIDATE

    return EDGE_SKIP_VALIDATE


def _should_score(state: PipelineState) -> str:
    chunks = state["chunks"]
    config = state["config"]
    if chunks and len(chunks) > config.top_k_chunks:
        return EDGE_SCORE
    return EDGE_SKIP_SCORE


def _should_refine(state: PipelineState) -> str:
    config = state["config"]
    is_valid = state["is_valid"]
    retry_count = state["retry_count"]

    if is_valid:
        return EDGE_MERGE
    if not config.refinement:
        return EDGE_MERGE
    if retry_count >= config.max_retries:
        return EDGE_MERGE

    return EDGE_REFINE


def print_graph():
    graph = build_graph()
    png_bytes = graph.get_graph().draw_mermaid_png()
    with open("pipeline_graph.png", "wb") as f:
        f.write(png_bytes)
    print("Saved pipeline_graph.png")


print_graph()
