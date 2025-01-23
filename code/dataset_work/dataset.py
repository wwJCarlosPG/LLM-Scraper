import requests
import os, sys, re
from consts import * 
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from waybackpy import WaybackMachineCDXServerAPI

USER_AGENT = "my new app's user agent"
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    connect= 3

)
adapter = HTTPAdapter(max_retries = retry_strategy)



class HTML_Data:
    """
    A class to retrieve and save historical HTML versions of a given URL using the Wayback Machine CDX Server API.

    This class fetches archived versions of web pages based on specified years and months.
    It handles HTTP requests with retry mechanisms and stores the HTML content locally.

    Attributes:
        seed_url (str): The original URL to retrieve historical versions of.
        cdx_api (WaybackMachineCDXServerAPI): An instance of the Wayback Machine API to fetch archived URLs.

    Args:
        url (str): The target URL for which archived versions are needed.
        years (list[int]): A list of years to retrieve versions from. If empty, defaults to `TEST_YEARS`.
        months (list[int]): A list of months to retrieve versions from. If empty, defaults to `MONTHS`.
    """
    def __init__(self, url: str, years: list[int], months: list[int]):
        """
        Initializes the HTML_Data object and retrieves historical HTML versions based on provided years and months.

        If only one year and one month are provided, a single HTML page is fetched. Otherwise, multiple versions 
        are retrieved based on the given time range.

        Args:
            url (str): The URL of the web page to retrieve.
            years (list[int]): A list of years to fetch versions from.
            months (list[int]): A list of months to fetch versions from.
        """

        is_only = len(years) == 1 and len(months) == 1

        if years == []:
            years = TEST_YEARS
        if months == []:
            months = MONTHS

        self.cdx_api = WaybackMachineCDXServerAPI(url, USER_AGENT)
        self.seed_url = url
        
        if is_only:
            self.get_html(self.seed_url, year=years[0], month=months[0])
        else:
            self.get_by_dates(years, months)
        
    def get_html(self, url: str, month: int, year: int):
        """
        Makes an HTTP request to retrieve the archived HTML page and saves it locally.

        If the response indicates a redirection, it follows the redirect and retries the request.

        Args:
            url (str): The URL to fetch the HTML content from.
            month (int): The month of the archived version.
            year (int): The year of the archived version.
        """
        print(f'URL: {url}')
        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        response = session.get(url, timeout=10)
        if response.is_redirect:
            self.get_html(response.headers['location'])
        elif response.ok:
            self.save_html(url, response.content, month, year)
        else:
            print(f"Something is bad: {response.status_code}")


    def get_by_dates(self, years: list[int], months:list[int]):
        """
        Iterates through the specified years and months to fetch multiple archived HTML pages.

        This method queries the Wayback Machine API to find the nearest available archived URL for the given dates 
        and saves the HTML content.

        Args:
            years (list[int]): A list of years to fetch archived pages.
            months (list[int]): A list of months to fetch archived pages.
        """

        for y in years:
            for m in months:
                try:
                    near = self.cdx_api.near(year=y, month=m)
                    self.get_html(near.archive_url, m, y)
                    print(near.archive_url)
                except Exception as e:
                    print(f"Something is bad: {e}")
    
    
    def save_html(self, url: str, content: str, month: int, year: int):
        """
        Saves the retrieved HTML content to a local file.

        The filename is generated based on the original URL, month, and year. 
        Special characters in the URL are replaced to ensure a valid file name.

        Args:
            url (str): The URL of the archived page.
            content (str): The HTML content to save.
            month (int): The month of the archived page.
            year (int): The year of the archived page.
        """
        url = url.replace('//','-').replace('/','-').replace(':','')
        seed_url = self.seed_url.replace('//','-').replace('/','-').replace(':','')

        dir_path = f'pages/{seed_url}'
        os.makedirs(dir_path, exist_ok=True)

        with open(f'{dir_path}/{url}___{month}___{year}.html', 'wb+') as document:
            document.write(content)

    
if __name__=="__main__":
    index = 0
    sites = []
    while True:
        index += 1
        try:
            sites.append(sys.argv[index])
        except:
            break
    
    for site in sites:
        html_data = HTML_Data(site, [], [])

    