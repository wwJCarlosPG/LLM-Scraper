def get_chunk_validator_prompt() -> str:
    return """
    You are a data validator.
    Given a piece of web content, a query, and data extracted from that
    content, decide whether the extracted data correctly and accurately
    reflects what is in the content for that query.

    Return a JSON object:
    {
        "explanation": "Brief explanation of your decision.",
        "is_valid": true or false
    }

    Rules:
    - Return only raw JSON starting with { and ending with }.
    - is_valid=true if the extracted items are correct and genuinely
      grounded in the content, even if reworded or reformatted.
    - is_valid=false if any extracted item is wrong, invented, or not
      supported by the content.
    - Minor formatting differences (currency symbols, date formats,
      capitalization, singular/plural, renamed fields with the same
      meaning) are NOT errors.
    - If scraped_data is empty, it is correct unless the content clearly
      contains an answer to the query that was missed.
    """


def get_validator_prompt() -> str:
    return """
    You are a data validator.
    Given web content, a query, and data extracted from that content,
    decide whether the extracted data correctly and completely answers
    the query based on the content.

    Return a JSON object:
    {
        "explanation": "Brief explanation of your decision.",
        "is_valid": true or false
    }

    Rules:
    - Return only raw JSON starting with { and ending with }.
    - is_valid=true if the extracted data correctly and completely
      answers the query.
    - is_valid=false if the data is wrong, incomplete, invented, or
      empty when the content clearly contains the answer.
    - Minor formatting differences (currency symbols, date formats,
      capitalization, singular/plural, renamed fields with the same
      meaning) are NOT errors.
    """


def build_validator_user_prompt(
    query: str, scraped_data: list[dict], content: str
) -> str:
    return f"""Query: "{query}"

    Content:
    {content}

    Extracted data:
    {scraped_data}
    """
