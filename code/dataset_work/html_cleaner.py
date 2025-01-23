import os, requests
from bs4 import BeautifulSoup
from dataset_work.consts import ROOT, DEST_PATH
from urllib3.util.retry import Retry
from charset_normalizer import detect
from requests.adapters import HTTPAdapter

class HTML_Cleaner:
    """
    A class to clean HTML files by removing specified tags and performing operations 
    such as renaming and size-based filtering.
    """
    
    @staticmethod
    def clean_all(pages: list, tags: list, dest_path: str = DEST_PATH):
        """
        Removes specified tags from all HTML files located in the provided local paths.

        Args:
            pages (list): List of local paths where the HTML files are stored.
            tags (list): List of HTML tags to remove from the files.
            dest_path (str, optional): Path to save cleaned HTML files. 
                                       Defaults to DEST_PATH (e.g., pages/pages_without_noise).
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
    def clean_and_save(html_path: str, file_name: str, tags: list, dest_path: str = DEST_PATH):
        """
        Removes the specified tags from an HTML file and saves the cleaned version.

        Args:
            html_path (str): The full path of the HTML file to be cleaned.
            file_name (str): The name to use when saving the cleaned HTML file.
            tags (list): A list of HTML tags to remove.
            dest_path (str, optional): Path where the cleaned HTML file will be saved. 
                                       Defaults to DEST_PATH (e.g., pages/pages_without_noise).
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
            
            cleaned_html = HTML_Cleaner.clean_by_tag(html_content, tags)
            
            dest = os.path.join(dest_path, f'cleaned_{file_name}.html')
            with open(dest, 'w', encoding='utf-8') as file:
                file.write(cleaned_html)
        
        except Exception as e:
            print(e)

    @staticmethod
    def clean_without_download(tags: list[str], url: str = None, html_content: str = None, is_local: bool = False) -> str:
        """
        Cleans an HTML page either from a URL or from a local source without downloading it.

        Args:
            url (str, optional): The URL or local file path of the HTML content.
            tags (list[str]): A list of tags to remove from the HTML.
            html_content (str, optional): The HTML content as a string to clean directly. Defaults to None.
            is_local (bool, optional): Indicates whether the URL is a local file path. Defaults to False.

        Returns:
            str: The cleaned HTML content as a string.
        """
        if html_content is not None:
            return HTML_Cleaner.clean_by_tag(html_content, tags)

        USER_AGENT = "my new app's user agent"
        retry_strategy = Retry(
            total=5,
            backoff_factor=1,
            connect= 3

        )
        adapter = HTTPAdapter(max_retries = retry_strategy)


        session = requests.Session()
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        try:
            if not is_local:
                response = session.get(url, timeout=10)
            else:
                with open(url, 'r') as file:
                    response = file.read()
            return HTML_Cleaner.clean_by_tag(response, tags)
            
        except Exception as e:
            print(f"Request failed: {e}")


    @staticmethod
    def clean_by_size(size_limit: int = 11000, path: str = DEST_PATH):
        """
        Removes HTML files smaller than a specified size limit.

        Args:
            size_limit (int, optional): The minimum file size in bytes to keep. Defaults to 11,000 bytes.
            path (str, optional): The directory path to check for HTML files. Defaults to DEST_PATH.

        Prints:
            Number of files before and after the cleaning process.
        """
        
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
        """
        Renames files in the given directory to remove unwanted characters.

        Args:
            root_path (str, optional): The directory containing the files to rename. Defaults to DEST_PATH.

        The following characters are removed or replaced:
            - '?' is removed
            - 'html.html' is replaced with 'html'
            - Special characters such as '&', '*', ':', '\"', '#' are removed.
        """

        files = os.listdir(root_path)
        for file in files:
            new_file_name = file
            if file.__contains__('?'):
                new_file_name = new_file_name.replace('?','')
            new_file_name = new_file_name.replace('html.html', 'html')
            new_file_name = new_file_name.replace('&','').replace('*','').replace(':','').replace('\"', '')
            new_file_name = new_file_name.replace('#','')
            os.rename(f'{root_path}/{file}', f'{root_path}/{new_file_name}')

    @staticmethod         
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




            
if __name__ == '__main__':
    # urls = os.listdir(ROOT)
    # urls.remove('pages_without_noise')
    
    # HTML_Cleaner.clean_all(urls, ['script', 'style'])
    # cleaned_path = DEST_PATH
    # HTML_Cleaner.clean_by_size()
    HTML_Cleaner.rename_files()