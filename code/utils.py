from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.options import Options

SERVICE = Service('/opt/homebrew/Caskroom/chromedriver/131.0.6778.69/chromedriver-mac-arm64/chromedriver')


def config_driver(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-web-security")
    chrome_options.add_argument("--allow-file-access-from-files")
    chrome_options.add_argument("--allow-file-access")
    chrome_options.add_argument("--allow-cross-origin-auth-prompt")
    driver = webdriver.Chrome(service=SERVICE, options=chrome_options)
    driver.get(url)
    return driver


def get_elements(xpath, driver):
    res = driver.find_element(By.XPATH, value=xpath).text
    
    return res

def clean_name(name: str):
    try:
        
        start_web_name_index: int = name.find('http-') + 5
        if start_web_name_index == 4:
            print("HIZO ESTO")
            start_web_name_index = name.find('https-', 13) + 6
        end_web_name_index: int = name.find('.com')
        if end_web_name_index == -1:
            end_web_name_index = name.find('.org', 30)
        
        web_name = name[start_web_name_index: end_web_name_index]
        if web_name.startswith("www."):
            web_name = web_name[4:] if web_name[4] != '@' else web_name[5:]
        elif web_name.startswith("www"): 
            web_name = web_name[5:] if web_name[5] != '@' else web_name[6:]
        
        start_date_index = name.index('___')
        end_date_index = name.index('___', start_date_index + 1)
        date = name[start_date_index: end_date_index + 7]   
        print(f'Name: {name}')
        print(f'Web_name {web_name}')
        print(f'Date {date}')

        result = web_name+date+'.html'
        print(f'Result: {result}')
        return result,web_name
    except Exception as e:
        print(f'{e} --> {name}')


