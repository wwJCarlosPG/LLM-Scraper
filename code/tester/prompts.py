def labeled_data_generator(html):
    prompt = f"""
    You are an expert in web scraping and data extraction from HTML documents.  
    Your task is to analyze the provided HTML document and generate multiple extraction queries along with their expected structured data output.  

    **Steps to follow:**  

    1. **Analyze the provided HTML content:**  
       - Examine the structure, tags, attributes, and text to identify useful data points.  
       - Consider elements such as headlines, links, metadata, tables, product details, etc.  

    2. **Generate diverse extraction queries:**  
       - Create multiple natural language queries targeting different aspects of the content.  
       - Each query should aim to extract unique and meaningful data.  

    3. **Provide the expected structured output:**  
       - Format the extracted data in the required JSON structure.  
       - Ensure that the extracted values represent meaningful attribute-value pairs.  

    Now, the input is:  
    ```  
    {html}  
    ```  

    **Output format (strictly follow this structure):**  

    {{
        "responses": [
            {{
                "query1": "Provide a query to extract the main headlines from the document.",
                "data1": [
                    {{ "headline": "Sample headline 1" }},
                    {{ "headline": "Sample headline 2" }}
                ]
            }},
            {{
                "query2": "Generate a query to extract all hyperlinks present in the document.",
                "data2": [
                    {{ "link": "https://example.com/page1" }},
                    {{ "link": "https://example.com/page2" }}
                ]
            }},
            {{
                "query3": "Write a query to extract product names and prices.",
                "data3": [
                    {{ "product_name": "Product 1", "price": "$10" }},
                    {{ "product_name": "Product 2", "price": "$20" }}
                ]
            }}
        ]
    }}  

    **Important guidelines:**  
    - The JSON response should contain exactly **three dictionaries**, each with a `queryX` and `dataX` field.  
    - Each `dataX` must be a list of dictionaries, with each dictionary representing an extracted attribute-value pair.  
    - Do not include any extra text, comments, or explanations outside of the JSON structure.  
    - Ensure that the JSON is well-formatted and syntactically correct.  

    """
    return prompt


def labeled_news_data_generator():
    prompt = """
    You are an expert in web scraping and data extraction from HTML documents.  
    Your task is to analyze the provided HTML document and generate multiple extraction queries along with their expected structured data output.  

    **Steps to follow:**  

    1. **Analyze the provided HTML content:**  
       - Examine the structure, tags, attributes, and text to identify useful data points.  
       - Consider elements such as headlines, links, metadata, tables, and other relevant information for a news article.  

    2. **Generate diverse extraction queries:**  
       - Create multiple natural language queries targeting different aspects of the news content.  
       - Ensure queries focus on elements like headlines, publication dates, authors, article content, and links.  

    3. **Provide the expected structured output:**  
       - Format the extracted data in the required JSON structure.  
       - Ensure that the extracted values represent meaningful attribute-value pairs.  

    
    The answer must be between curly braces and should follow the format below and should be a valid JSON object:

    {
        "responses": [
            {
                "query1": "Extract all news headlines from the document.",
                "data1": [
                    { "headline": "Breaking News: Example Headline 1" },
                    { "headline": "Sports Update: Example Headline 2" }
                ]
            },
            {
                "query2": "Find the publication dates of all articles.",
                "data2": [
                    { "date": "2024-01-15" },
                    { "date": "2024-01-14" }
                ]
            },
            {
                "query3": "Retrieve the names of authors for each article.",
                "data3": [
                    { "author": "John Doe" },
                    { "author": "Jane Smith" }
                ]
            }
        ]
    }  

    **Important guidelines:**  
    - The response must be a valid JSON object starting strictly with `{` and ending with `}`.  
    - No additional text, explanations, or formatting should be included outside the JSON.  
    - Ensure the JSON is well-formatted and syntactically correct.  
    - Do **not** include markdown formatting, such as triple backticks (` ``` `).  

    Now, the input is the following HTML content:
    """
    return prompt
