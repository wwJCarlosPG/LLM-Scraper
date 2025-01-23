from utils import get_elements, config_driver

class Generator_By_Scraper:
    """
    A class to scrape URLs from a web page using Selenium and save them to a file.

    Attributes:
        url (str): The URL of the web page to scrape.
    """

    def __init__(self, url, xpath = "") -> None:
        """
        Initializes the scraper with a given URL and optional XPath for scraping.

        Args:
            url (str): The URL of the web page to scrape.
            xpath (str, optional): The XPath expression to locate elements on the page. 
                                   If provided, the scrape method is called automatically. 
                                   Defaults to an empty string.
        """
        self.url = url
        if xpath != "":
            self.scrape(xpath)

    def scrape(self):     
        """
        Scrapes data from the specified web page using a predefined XPath pattern.
        
        The method iterates over potential table rows in the web page and extracts the 
        content from the second column. The extracted URLs are saved to a file named 
        'urls.txt' and also stored in an internal list.

        The scraping process runs for up to 100 rows, printing progress to the console.

        The Selenium web driver is used to interact with the web page, and it is closed
        after the scraping is complete.

        Saves:
            - A list of extracted URLs to the file 'urls.txt'.
        """   
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

