# from scraper_manager.application.extraction.responses import ScrapedResponse
import math
import pdfkit


def find_majority(responses):
    similarity = 0
    max_similarity = -math.inf
    result = -1
    for i in range(len(responses) - 1):
        for j in range(i + 1, len(responses)):
            similarity = 0
            for res_i in responses[i].scraped_data:

                for res_j in responses[j].scraped_data:

                    if list(res_i.values()) == list(res_j.values()):
                        similarity+=1
                
            
            
                similarity-=len(responses[i].scraped_data)-len(responses[j].scraped_data)

                if similarity > max_similarity:
                    max_similarity = similarity
                    result = i
            
    return responses[result]

from bs4 import BeautifulSoup

def clean_by_tag(html_content: str, tags: list[str]):
        """
        Removes specified tags from the provided HTML content.

        Args:
            html_content (str): The HTML content to clean.
            tags (list[str]): A list of tags to be removed from the HTML.

        Returns:
            str: The cleaned HTML content as a string.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        for tag in tags:
            for t in soup.find_all(tag):
                t.decompose()

        cleaned_html = str(soup)
        return cleaned_html

def from_html_to_pdf(html_content, url, output_path, by_url = False):
    
    
    with open('pages/amazon_best_sellers/https-web.archive.org-web-20220116013542-https-www.amazon.com-gp-bestsellers-fashion___1___2022.html', 'r') as file:
        html_content = file.read()
        html_content = clean_by_tag(html_content, ['script', 'style'])
    if not by_url:
        pdfkit.from_string(html_content, output_path)



# from_html_to_pdf(None, None, "x.pdf")
