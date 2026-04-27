from scraper.pipeline.graph import build_graph, print_graph

print_graph()


def save_graph_as_png(output_path: str = "graph.png"):
    graph = build_graph()
    image = graph.get_graph().draw_mermaid_png()
    with open(output_path, "wb") as f:
        f.write(image)
    print(f"Graph saved to {output_path}")


save_graph_as_png()
