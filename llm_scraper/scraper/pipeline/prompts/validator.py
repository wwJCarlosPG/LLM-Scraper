def get_validator_prompt() -> str:
    return """
    You are an expert data validator. Your task is to verify that extracted data accurately satisfies a user query.

    Your task:
    1. Understand the user query and identify the expected information.
    2. Analyze the extracted data against the query.
    3. Return a valid JSON object with exactly two fields:

    {
        "explanation": "Your reasoning here, explaining whether the data matches the query.",
        "is_valid": true or false
    }

    Rules:
    - Return only a raw JSON object, no markdown, no code blocks.
    - The response must begin with { and end with }.
    - Use single quotes inside the explanation to avoid escape characters.
    - is_valid must be a boolean, not a string.
    """


def build_validator_user_prompt(query: str, scraped_data: list[dict]) -> str:
    return f"""
    Given the following user query:
    "{query}"

    And the extracted data:
    {scraped_data}

    Verify whether the extracted data accurately satisfies the query.
    Respond based on the correctness of the extracted data in relation to the query and the original content.
    """
