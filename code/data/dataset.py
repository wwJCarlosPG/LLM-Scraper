import os, sys, re
import requests
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
from waybackpy import WaybackMachineCDXServerAPI, WaybackMachineSaveAPI
from consts import * 

USER_AGENT = "my new app's user agent"
retry_strategy = Retry(
    total=5,
    backoff_factor=1,
    connect= 3

)

adapter = HTTPAdapter(max_retries = retry_strategy)



class HTML_Data:
    def __init__(self, url: str, years: list[int], months: list[int], is_only: bool = False):
        if years == []:
            years = TEST_YEARS
        if months == []:
            months = TEST_MONTHS

        self.cdx_api = WaybackMachineCDXServerAPI(url, USER_AGENT)
        self.seed_url = url
        
        if is_only:
            self.get_html(self.seed_url)
        else:
            self.get_by_dates(years, months)
        
    def get_html(self, url, month: int = 0, year: int = 0):
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


    def get_by_dates(self, years, months):
        for y in years:
            for m in months:
                try:
                    near = self.cdx_api.near(year=y, month=m)
                    self.get_html(near.archive_url, m, y)
                    print(near.archive_url)
                except Exception as e:
                    print(f"Something is bad: {e}")
    
    
    def save_html(self, url: str, content, month: int = 0, year: int = 0):
        url = url.replace('//','-').replace('/','-').replace(':','')
        seed_url = self.seed_url.replace('//','-').replace('/','-').replace(':','')

        dir_path = f'pages/{seed_url}'
        os.makedirs(dir_path, exist_ok=True)

        with open(f'{dir_path}/{url}___{month}___{year}.html', 'wb+') as document:
            document.write(content)



    
