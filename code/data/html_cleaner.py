from charset_normalizer import detect
from consts import ROOT, DEST_PATH
from bs4 import BeautifulSoup
import os

class HTML_Cleaner:
    
    @staticmethod
    def clean_all(pages: list, tags: list, dest_path: str = DEST_PATH):
        """Remove given tags from htmls located in some local paths

        Args:
            pages (list): Local paths of htmls, full path could be ROOT/pages[i].
            tags (list): Tags to remove
            dest_path (str, optional): Path where cleaned html going to be. Defaults to DEST_PATH (pages/pages_without_noise).
        """
        
        for page in pages:
            page_path = os.path.join(ROOT, page)
            try:
                htmls = os.listdir(page_path)
                for html in htmls:
                    html_path = os.path.join(page_path, html)
                    HTML_Cleaner.clean_html(html_path=html_path, file_name=html, tags=tags, dest_path=dest_path)
            except Exception as e:
                print(e)    


    @staticmethod
    def clean_html(html_path: str, file_name: str, tags: list, dest_path: str = DEST_PATH):
        """Remove the given tags from a html file and save the cleaned html in a given path (this method is auxiliar)

        Args:
            html_path (str): Local path where the html is
            file_name (str): Name to save the cleaned html (often it's the previous name)
            tags (list): Tags to remove
            dest_path (str, optional): Path where clened html going to be. Defaults to DEST_PATH (pages/pages_without_noise).
        """
        
        try:
            with open(html_path, 'rb') as file:
                raw_data = file.read()
                # html is empty
                if len(raw_data) < 200:
                    return
            
            encoding = detect(raw_data)['encoding']
            
            with open(html_path, 'r', encoding=encoding) as file:
                html_content = file.read()
            soup = BeautifulSoup(html_content, 'html.parser')

            for tag in tags:
                for t in soup.find_all(tag):
                    t.decompose()

            cleaned_html = str(soup)

            dest = os.path.join(dest_path, f'cleaned_{file_name}.html')
            with open(dest, 'w', encoding='utf-8') as file:
                file.write(cleaned_html)
        
        except Exception as e:
            print(e)

    def clean_by_size(size_limit: int = 11000, path: str = DEST_PATH):
        files = os.listdir(path)
        print(f'before: {len(files)}')
        for file in files:
            file_path = os.path.join(path, file)
            try:
                file_size = os.path.getsize(file_path)
                if file_size <= size_limit:
                    os.remove(file_path)
            except Exception as e:
                print(e)

        print(f'after: {len(os.listdir(path))}')

    def rename_files(root_path: str = DEST_PATH):
        files = os.listdir(root_path)
        for file in files:
            new_file_name = file
            if file.__contains__('?'):
                new_file_name = new_file_name.replace('?','')
            new_file_name = new_file_name.replace('html.html', 'html')
            new_file_name = new_file_name.replace('&','').replace('*','').replace(':','').replace('\"', '')
            new_file_name = new_file_name.replace('#','')
            os.rename(f'{root_path}/{file}', f'{root_path}/{new_file_name}')

                

            
if __name__ == '__main__':
    # urls = os.listdir(ROOT)
    # urls.remove('pages_without_noise')
    
    # HTML_Cleaner.clean_all(urls, ['script', 'style'])
    # cleaned_path = DEST_PATH
    # HTML_Cleaner.clean_by_size()
    HTML_Cleaner.rename_files()