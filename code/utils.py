from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By 
from selenium.webdriver.chrome.options import Options

SERVICE = Service('/opt/homebrew/Caskroom/chromedriver/131.0.6778.69/chromedriver-mac-arm64/chromedriver')


def config_driver(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(service=SERVICE, options=chrome_options)
    driver.get(url)
    return driver


def get_elements(xpath, driver):
    res = driver.find_element(By.XPATH, value=xpath).text
    
    return res
