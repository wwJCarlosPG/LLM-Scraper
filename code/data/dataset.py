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
    def __init__(self, url: str, years: list[int], months: list[int]):
        """_summary_

        Args:
            url (str): URL of page to save.
            years (list[int]): Each year which it wants a version
            months (list[int]): Each mont wich it wants a version
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
        """Make a request to URL and save the html

        Args:
            url (str): URL to making the request (?)
            month (int): .
            year (int): .
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
        """Using get_html method it saves each html corresponding to given date

        Args:
            years (list[int]): List of years when  
            months (list[int]): _description_
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
        """Save the html 

        Args:
            url (str): URL where the html provides 
            content (str): Content of the html
            month (int): Month when the html provides.
            year (int): Year when the hmtl provides.
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

    