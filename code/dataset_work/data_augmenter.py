import os
import json
import random
from gemini import Gemini
from utils import clean_name
from bs4 import BeautifulSoup
from dataset_work.consts import DEST_PATH
from dataset_work.consts import AUG_PAGES, TEXT_LABELS
from dataset_work.augmentation_prompts import generate_div

class Site:
    def __init__(self, web_name: str):
        self.web_name = web_name
        self.__file_names: list[str] = []
        self.__paths: list[str] = []

    def append(self, file_name, path):
        self.__file_names.append(file_name)
        self.__paths.append(path)

    def get_paths(self):
        yield from self.__paths

    def get_all(self):
        yield from zip(self.__paths, self.__file_names)

    def get_file_names(self):
        yield from self.__file_names

    def __eq__(self, value):
        return self.web_name == value.web_name
    
    def __repr__(self):
        return (f'\n*Web name: {self.web_name} --> {len(self.__file_names)}')
    
    def __hash__(self):
        return hash(self.web_name)

class Data_Augmenter:

    def __init__(self, llm, sites:list [Site]):
        self.llm = llm
        attrs = self.generate_divs(sites)
        self.put_divs(attrs)

    def generate_divs(self, sites: list[Site], is_generated: bool = True):
        result: dict[Site, list[dict]] = {}
        if is_generated:
            with open("divs_output.json", "r", encoding="utf-8") as json_file:
                loaded_data = json.load(json_file)

            for index in range(len(loaded_data)):
                result[sites[index]] = loaded_data[sites[index].web_name]
                print(len(result[sites[index]]))

            return result
        
        for site in sites:
            print(site.web_name)
            result[site] = []
            prompt = generate_div(site.web_name)
            try:
                while True:
                    response = self.llm(prompt)
                    r = response.replace(';',',')[:-1]
                    cleaned_response = f'[{r}]'
                    dict_list = json.loads(cleaned_response)
                    break
            except json.JSONDecodeError:
                    continue
             
            result[site].extend(dict_list)
            serializable_result = {
                site.web_name: divs for site, divs in result.items()
            }

        with open("divs_output.json", "w", encoding="utf-8") as json_file:
            json.dump(serializable_result, json_file, indent=4, ensure_ascii=False)
        return result

        
    def put_divs(self, attributes: dict[Site, list[dict]]):
        for site in list(attributes.keys()):
            
            for path, file_name in site.get_all():
                with open(f'{path}', 'r') as file:
                    content = file.read()

                    if not os.path.exists(f'{AUG_PAGES}/{file_name}'):
                        with open(f'{AUG_PAGES}/{file_name}', 'w') as file:
                            file.write(content)
                    
                    if os.path.exists(f'{AUG_PAGES}/div_{file_name}'):
                        continue
                    
                    without_text = False
                    soup: BeautifulSoup = BeautifulSoup(content, 'html.parser')
                    aux_labels = TEXT_LABELS.copy()
                    while True:
                        
                        try:
                            tag_to_find = random.choice(aux_labels)
                        except Exception as e:
                            without_text = True
                        tags = soup.find_all(tag_to_find) # tirar el random aqui para que sea cualquier tag.
                        if len(tags) > 1:
                            selected_tag = tags[random.randint(0,len(tags)-1)]
                            selected_div = random.randint(0,10) 
                            try:
                                new_div = soup.new_tag('div', attrs=dict(attributes[site][selected_div]))
                                selected_tag.wrap(new_div)
                                break
                            except Exception as e:
                                pass
                        else:
                            if not without_text:
                                aux_labels.remove(tag_to_find)
                 
                if not os.path.exists(f'{AUG_PAGES}/div_{file_name}') and not without_text:
                    with open(f'{AUG_PAGES}/div_{file_name}', 'w') as file:
                        file.write(str(soup))
    
    @staticmethod        
    def change_attribute_name(sites: list[Site]):
        all_text_tags = []
        for site in sites:
            for path, file_name in site.get_all():
                with open(f'{path}', 'r') as file:
                    content = file.read()
                    soup = BeautifulSoup(content, 'html.parser')
                    for label in TEXT_LABELS:
                        tags = soup.find_all(label)
                        all_text_tags.extend(tags)

                    for text_tag in all_text_tags:
                        for attr in ['name', 'id']:
                            if attr in text_tag.attrs:
                                value = text_tag.attrs[attr]
                                
                                if '-' in value:
                                    parts = value.split('-')
                                    new_value = '-'.join(parts[::-1])  
                                else:
                                    suffix = '_x' if attr == 'name' else '_id'
                                    new_value = value + suffix

                                text_tag.attrs[attr] = new_value
                with open(f'{AUG_PAGES}/attr_{file_name}', 'w') as file:
                    file.write(str(soup))





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

    Data_Augmenter.change_attribute_name(sites)
    

    # llm = Gemini()
    # data_augmenter = Data_Augmenter(llm, sites)

    pass


def main():
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
    d = Data_Augmenter(llm,sites)
    # Data_Augmenter.change_attrxibute_name(sites)






            

    
    