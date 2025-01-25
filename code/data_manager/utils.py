from data_manager.data_extractor.responses import ScrapedResponse
import math

def find_majority(responses: list[ScrapedResponse]) -> ScrapedResponse:
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



