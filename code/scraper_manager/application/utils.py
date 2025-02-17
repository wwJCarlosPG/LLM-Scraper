
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

def get_html_content(url: str) -> str:
       
        USER_AGENT = "my new app's user agent"
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            connect= 3

        )
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