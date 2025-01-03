import os
from gemini import Gemini
from utils import clean_name
from data.consts import DEST_PATH
from data.data_augmenter import Site, Data_Augmenter

if __name__ == "__main__":
    sites: list[Site] = []
    files = os.listdir(DEST_PATH)
    for file in files:
        if file[len(file)-4: len(file)] != 'html':
            continue
        path = os.path.join(DEST_PATH, file)
        file_name, web_name = clean_name(file)
        
        aux_site = Site(web_name)
        if aux_site not in sites:
            sites.append(Site(web_name))
        index = sites.index(Site(web_name))
        sites[index].append(file_name=file_name, path=path)




    llm = Gemini()
    data_augmenter = Data_Augmenter(llm, sites)

    pass