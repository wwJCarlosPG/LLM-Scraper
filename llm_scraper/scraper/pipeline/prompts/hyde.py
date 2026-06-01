# Domain-specific instructions following Gao et al. (2022) HyDE paper.
# Each instruction guides the LLM to generate a hypothetical document
# in the style of the target corpus, bridging the semantic gap between
# task instructions and web content.
#
# Note: generating N>1 documents and averaging their embeddings reduces
# variance (Equation 6-7 in the paper) but is left as a future improvement
# for cost efficiency.

_INSTRUCTIONS: dict[str, str] = {
    "ecommerce": (
        "Write a short product listing excerpt that would appear on an "
        "e-commerce page and directly answers this extraction query:"
    ),
    "news": (
        "Write a short news article excerpt that directly answers "
        "this extraction query:"
    ),
    "documentation": (
        "Write a short technical documentation excerpt that directly "
        "answers this extraction query:"
    ),
    "web": (
        "Write a short web page excerpt that contains the information "
        "needed to answer this extraction query:"
    ),
}


def get_hyde_system_prompt() -> str:
    return (
        "You are a web content generator. "
        "Generate only the content, no explanation or preamble. "
        "Keep it concise: 3-8 lines maximum. "
        "Use realistic values, names and formats typical of web pages."
    )


def build_hyde_user_prompt(query: str, domain: str = "web") -> str:
    """
    Builds g(q, INST) as described in HyDE paper (Gao et al., 2022).
    INST varies by domain to generate domain-appropriate hypothetical docs.
    """
    instruction = _INSTRUCTIONS.get(domain, _INSTRUCTIONS["web"])
    return f"{instruction}\n\n{query}"
