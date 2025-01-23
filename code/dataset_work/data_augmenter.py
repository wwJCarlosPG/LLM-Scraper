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
    """
    Represents a website with associated file names and paths.

    Attributes:
        web_name (str): The name of the website.
        __file_names (list[str]): A private list storing the file names associated with the site.
        __paths (list[str]): A private list storing the paths to the files associated with the site.
    """
    def __init__(self, web_name: str):
        """
        Initializes a Site instance with a given website name.

        Args:
            web_name (str): The name of the website.
        """
        self.web_name = web_name
        self.__file_names: list[str] = []
        self.__paths: list[str] = []

    def append(self, file_name, path):
        """
        Appends a file name and its path to the site.

        Args:
            file_name (str): The name of the file.
            path (str): The path to the file.
        """
        self.__file_names.append(file_name)
        self.__paths.append(path)

    @staticmethod
    def site_list_generator(dest_path: str = DEST_PATH):
        """
        Generates a list of Site objects by processing HTML files from the destination path.

        This method iterates through the files in the specified directory, filters out non-HTML files, 
        extracts necessary information, and organizes them into Site objects based on their web names.

        Steps performed:
        1. List all files in the directory specified by `DEST_PATH`.
        2. Filter files to only process those with an `.html` extension.
        3. Extract the file name and web name using the `clean_name` function.
        4. Create a new `Site` object if it does not exist in the list.
        5. Add the file name and path to the appropriate `Site` object.

        Returns:
            list[Site]: A list of `Site` objects with their respective file paths and names.
        """
        sites: list[Site] = []
        files = os.listdir(dest_path)
        for file in files:
            if file[len(file)-4: len(file)] != 'html':
                continue
            path = os.path.join(dest_path, file)
            file_name, web_name = clean_name(file)
            
            aux_site = Site(web_name)
            if aux_site not in sites:
                sites.append(Site(web_name))
            index = sites.index(Site(web_name))
            sites[index].append(file_name=file_name, path=path)
    
    
    def get_paths(self):
        """
        Provides a generator for the paths associated with the site.

        Yields:
            str: The next path in the list.
        """
        yield from self.__paths

    def get_all(self):
        """
        Provides a generator for the paths and file names as tuples.

        Yields:
            tuple[str, str]: A tuple containing a file path and its corresponding file name.
        """
        yield from zip(self.__paths, self.__file_names)

    def get_file_names(self):
        """
        Provides a generator for the file names associated with the site.

        Yields:
            str: The next file name in the list.
        """
        yield from self.__file_names

    def __eq__(self, value):
        """
        Compares two Site instances based on their web_name attribute.

        Args:
            value (Site): Another Site instance to compare.

        Returns:
            bool: True if the web names match, False otherwise.
        """
        return self.web_name == value.web_name
    
    

    def __repr__(self):
        """
        Provides a string representation of the Site instance.

        Returns:
            str: A formatted string showing the web name and the number of associated files.
        """
        return f'\n*Web name: {self.web_name} --> {len(self.__file_names)}'

    def __hash__(self):
        """
        Provides a hash value for the Site instance based on its web name.

        Returns:
            int: The hash value of the web name.
        """
        return hash(self.web_name)

class Data_Augmenter:
    """
    Augments data for multiple websites by generating and modifying HTML elements.

    Attributes:
        llm (Any): The large language model used for generating div attributes.
        sites (list[Site]): A list of Site instances to be processed.
    """

    def __init__(self, llm, sites:list [Site]):
        """
        Initializes the Data_Augmenter with an LLM and a list of sites. It generates
        div attributes and applies modifications to the HTML files.

        Args:
            llm (Any): The large language model to use.
            sites (list[Site]): A list of Site instances.
        """
        self.llm = llm
        attrs = self.generate_divs(sites)
        self.put_divs(attrs)

    def generate_divs(self, sites: list[Site], is_generated: bool = True):
        """
        Generates or loads div attributes for the given sites.

        Args:
            sites (list[Site]): A list of Site instances.
            is_generated (bool): If True, loads div attributes from a JSON file. Otherwise, 
                generates them using the LLM.

        Returns:
            dict[Site, list[dict]]: A dictionary mapping sites to their generated attributes.
        """
        
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
        """
        Generates or loads div attributes for the given sites.

        Args:
            sites (list[Site]): A list of Site instances.
            is_generated (bool): If True, loads div attributes from a JSON file. Otherwise, 
                generates them using the LLM.

        Returns:
            dict[Site, list[dict]]: A dictionary mapping sites to their generated attributes.
        """
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
    
    def change_attribute_name(self):
        """
        Updates the `name` and `id` attributes of HTML tags in the files for the given sites.
        If the attribute contains a hyphen, its parts are reversed. Otherwise, a suffix
        is added to the value.

        """
        all_text_tags = []
        for site in self.sites:
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
    


    llm = Gemini()
    d = Data_Augmenter(llm,sites)
    # Data_Augmenter.change_attrxibute_name(sites)






            

    
    