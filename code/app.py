from data.dataset import HTML_Data
from data.seed_generator import Generator_By_Scraper
# url = "https://cnn.com"
# urls = []
# with open('urls.txt', 'r') as file:
#     for line in file:
#         urls.append(line.strip())
urls = ['cnn.com', 'bbc.com','as.com']
for url in urls:
    html_data = HTML_Data(url, [], [])

# # hacer algo para quitar los comentarios

# g = Generator_By_Scraper("https://backlinko.com/most-popular-websites")
# g.scrape()