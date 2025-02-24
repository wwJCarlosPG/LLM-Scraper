
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_html_content(url: str) -> str:
        """
        Retrieves the HTML content from a given URL.

        This function uses the `requests` library to fetch the HTML content from
        the specified URL, with a retry strategy to handle potential network issues.

        Args:
            url (str): The URL of the HTML content to retrieve.

        Returns:
            str: The HTML content as a string.

        Raises:
            Exception: If the request fails after multiple retries.
        """
       
        
        USER_AGENT = "my new app's user agent"
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            connect= 3)
        adapter = HTTPAdapter(max_retries = retry_strategy)


        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            
            response = session.get(url, timeout=10)
            response = response.text
            return response
        except Exception as e:
            print(f"Request failed: {e}")