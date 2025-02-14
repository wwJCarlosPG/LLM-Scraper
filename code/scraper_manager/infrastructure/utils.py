# from scraper_manager.application.extraction.responses import ScrapedResponse
import math
import pdfkit
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

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

def html_to_raw_text_pdf(html_content, output_file):

    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter
    c.setFont('Helvetica', 10)
    
    lines = html_content.split('\n')
    y = height - 50  # Start from top of the page
    
    for line in lines:
        if y <= 50:  # Check if we need a new page
            c.showPage()
            y = height - 50
        c.drawString(50, y, line)
        y -= 12  # Move to next line

    c.save()

# with open('pages/dataset/bbc/attr_bbc___12___2011.html', 'r') as f:
#         html = f.read()

# html_to_raw_text_pdf(html, 'output.pdf')