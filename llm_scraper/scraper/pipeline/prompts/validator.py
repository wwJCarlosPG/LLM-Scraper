def get_validator_prompt() -> str:
    return """
        You are an expert data validator. Your task is to verify that extracted data
        accurately satisfies a user query based on the original content.

        Your task:
        1. Understand the user query and identify the expected information.
        2. Cross-check the extracted data against the original content.
        3. Return a valid JSON object with exactly two fields:

        {
            "explanation": "Your reasoning here, explaining whether the data matches
                            the query based on the original content. If invalid,
                            specify exactly where in the content the correct data
                            can be found.",
            "is_valid": true or false
        }

        Rules:
        - Return only a raw JSON object, no markdown, no code blocks.
        - The response must begin with { and end with }.
        - Use single quotes inside the explanation to avoid escape characters.
        - is_valid must be a boolean, not a string.
        - If the extracted data is empty but the content contains relevant data,
        return is_valid=false and specify in the explanation where the data is.
        """


def build_validator_user_prompt(
    query: str, scraped_data: list[dict], content: str
) -> str:
    return f"""
        Given the following user query:
        "{query}"

        The original content:
        {content}

        And the extracted data:
        {scraped_data}

        Verify whether the extracted data accurately satisfies the query based on
        the original content. If the extracted data is empty or incorrect, specify
        exactly where in the content the correct data can be found.
        """
