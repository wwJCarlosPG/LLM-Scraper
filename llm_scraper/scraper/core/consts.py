# Graph nodes
NODE_CLEANER = "cleaner"
NODE_CHUNKER = "chunker"
NODE_SCORER = "scorer"
NODE_EXTRACTOR = "extractor"
NODE_MERGER = "merger"
NODE_VALIDATOR = "validator"

# Graph edges
EDGE_SCORE = "score"
EDGE_SKIP_SCORE = "skip_score"
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


# HTML headers for semantic section splitting
HTML_HEADERS_TO_SPLIT_ON = [
    ("h1", "h1"),
    ("h2", "h2"),
    ("h3", "h3"),
]

# Elements to preserve intact during chunking
ELEMENTS_TO_PRESERVE = ["table", "ul", "ol"]

# Tags to remove before chunking
DENYLIST_TAGS = ["script", "style", "head"]
