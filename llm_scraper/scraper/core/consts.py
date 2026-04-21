# Graph nodes
NODE_CLEANER = "cleaner"
NODE_CHUNKER = "chunker"
NODE_EXTRACTOR = "extractor"
NODE_MERGER = "merger"
NODE_VALIDATOR = "validator"

# Graph edges
EDGE_REFINE = "refine"
EDGE_END = "end"

# Semantic tags for chunking
SEMANTIC_TAGS = [
    "article",
    "section",
    "main",
    "aside",
    "header",
    "footer",
    "ul",
    "ol",
    "table",
]

# HTML tags to remove during cleaning
NOISE_TAGS = ["script", "style", "link", "meta", "br", "hr"]

# HTML inline tags to unwrap at level 3 cleaning
INLINE_TAGS = [
    "p",
    "b",
    "span",
    "strong",
    "i",
    "em",
    "mark",
    "small",
    "del",
    "ins",
    "sub",
    "sup",
    "a",
    "option",
]

# Attributes to keep during cleaning
ALLOWED_ATTRIBUTES = ("src", "class", "id")

# Attributes to remove at level 3
LEVEL3_ATTRIBUTES = ["role", "id", "alt", "title"]
