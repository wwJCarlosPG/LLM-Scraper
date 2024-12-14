from utils import get_elements, config_driver

class Generator_By_Scraper:
    def __init__(self, url, xpath = "") -> None:
        self.url = url
        if xpath != "":
            self.scrape(xpath)


    def scrape(self):        
        elements = []
        driver = config_driver(self.url)

        for i in range(1,100):
            print(i)
            site_xpath = f'//*[@id="content"]/div[2]/table/tbody/tr[{i}]/td[2]'
            print(site_xpath)
            url = get_elements(site_xpath, driver)
            elements.append(url)
            
            with open('urls.txt', 'a') as file:
                file.write(url + '\n')

            print(f'{i} saved')
        driver.quit()

