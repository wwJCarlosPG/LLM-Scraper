# from dataset_work.data_augmenter import main

# main()


# import gensim.downloader as api
# from gensim.matutils import cossim
# from typing import List, Dict, Any
# import itertools


# word_vectors = api.load("glove-wiki-gigaword-100")


# # vec_hello = 

# similarity = cossim(word_vectors["Hello"], word_vectors["Hi"])
# print(similarity)

from collections import defaultdict
from typing import List, Dict, Any



x = '{\n"explanation": "The query asks to \'Extract all product titles from the best sellers list\'. Upon analyzing the HTML structure, it\'s clear that the product titles are contained within the \'div\' elements with a specific pattern. The extracted data contains 50 product titles, each with a \'ProductTitle\' attribute, which matches the expected information. The titles themselves, such as \'MIHOLL Women’s Long Sleeve Tops Lace Casual Loose Blouses T Shirts\' and \'Hanes Men\'s Pullover EcoSmart Hooded Sweatshirt\', are present in the HTML content under the \'Best Sellers in Clothing, Shoes & Jewelry\' section, confirming that the extraction is correct.",\n"is_valid": true\n}'

import json

json.loads(x)
# x = filter_common_dictionaries([[{"title": "A", "tag": "a"}, {"title": "B", "tag": "b"}], [{"title": "A", "tag":"a"}, {"title": "C", "tag":"c"}], [{"title": "B", "tag": "b"}, {"title": "D", "tag": "d"}]])
# print(x)