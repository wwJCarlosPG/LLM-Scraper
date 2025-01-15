def generate_div(website: str):
    prompt = f"""
    I have a website name. For each website name, generate **10 unique HTML <div> elements**.
    Each <div> should have realistic and diverse attributes such as `class`, `id`, `data-*` attributes, and `style` that reflect the theme or functionality of the website. 
    The attributes should be descriptive, plausible, and relevant to the site's name, purpose, or content. 

    ### Format the output as follows:
    - Provide exactly 10 sets of attributes, each in **JSON format**.
    - Separate each JSON object with a semicolon (`;`).
    - Each JSON object should include a varying number of attributes (at least 2, but not necessarily all).
    - Attributes should have meaningful values related to the `{website}`.

    Example Output for `cnn.com`:
    {{
        "class": "news-highlight",
        "id": "headline-12345",
        "data-category": "world-news",
        "style": "background-color: #f9f9f9; margin: 20px; padding: 10px;"
    }};
    {{
        "class": "breaking-news",
        "id": "alert-banner",
        "data-priority": "high",
        "style": "color: red; font-weight: bold;"
    }};
    {{
        "class": "top-story",
        "data-section": "politics",
        "style": "padding: 20px; border: 1px solid #ddd;"
    }};
    ...

    ### Guidelines:
    1. Ensure each JSON object is unique, reflecting a variety of realistic HTML <div> attributes.
    2. The output should contain 10 **separate JSON objects**, not a single JSON object with multiple attributes.
    3. Each JSON object should be related to the theme or purpose of the `{website}`.

    Now, generate the output for the input website `{website}`. Ensure the response is exactly 10 JSON objects, each separated by a semicolon (`;`).
    """
    return prompt

def generate_form():
    pass