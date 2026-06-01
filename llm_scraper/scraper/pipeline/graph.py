from langgraph.graph import END, StateGraph

from scraper.core.consts import (
    EDGE_END,
    EDGE_REFINE,
    EDGE_SCORE,
    EDGE_SKIP_SCORE,
    NODE_CHUNKER,
    NODE_CLEANER,
    NODE_EXTRACTOR,
    NODE_MERGER,
    NODE_SCORER,
    NODE_VALIDATOR,
)
from scraper.core.entities.state import PipelineState
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
    graph.add_edge(NODE_MERGER, NODE_VALIDATOR)

    graph.add_conditional_edges(
        NODE_VALIDATOR,
        _should_continue,
        {EDGE_REFINE: NODE_EXTRACTOR, EDGE_END: END},
    )

    return graph.compile()


def _should_score(state: PipelineState) -> str:
    chunks = state["chunks"]
    config = state["config"]
    if chunks and len(chunks) > config.top_k_chunks:
        return EDGE_SCORE
    return EDGE_SKIP_SCORE


def _should_continue(state: PipelineState) -> str:
    config = state["config"]
    is_valid = state["is_valid"]
    retry_count = state["retry_count"]

    if is_valid:
        return EDGE_END
    if not config.refinement:
        return EDGE_END
    if retry_count >= config.max_retries:
        return EDGE_END

    return EDGE_REFINE


def print_graph():
    graph = build_graph()
    print(graph.get_graph().draw_ascii())
