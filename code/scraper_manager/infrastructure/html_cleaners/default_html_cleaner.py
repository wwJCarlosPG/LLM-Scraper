from bs4 import BeautifulSoup, Comment, NavigableString

class DefaultHTMLCleaner:
    """
    A class to clean HTML files by removing specified tags and performing operations 
    such as renaming and size-based filtering.
    """


    def clean_by_tag(self, html_content: str, tags_to_remove: list[str], context_length: int = 0, level: int = 3) -> str:
            """
            Removes specified tags from the provided HTML content while keeping their inner text.
            Also removes comments and empty text nodes.

            Args:
                html_content (str): The HTML content to clean.
                tags_to_remove (list[str]): A list of tags to be removed from the HTML.

            Returns:
                str: The cleaned HTML content as a string.
            """
            soup = BeautifulSoup(html_content, 'html.parser')
            if context_length != 0:
                tags_to_remove = ['link', 'meta', 'br', 'hr', 'style', 'script']

            # clean level 1
            # remove the specific tags
            for tag in tags_to_remove:
                for script in soup.find_all(tag):
                    script.decompose()
            
            cleaned_html = str(soup)
            # print(f"1: {cleaned_html.index('$27')}")
            # remove comments
            for comment in soup.findAll(text = lambda text: isinstance(text, Comment)):
                comment.extract()

            cleaned_html = str(soup)
            # print(f"2: {cleaned_html.index('$27')}")
            # print(cleaned_html.index('<img'))

            # clean level 2
            # remove unnecesary attributes
            for tag in soup.find_all():
                for attr in ['style', 'onclick', 'onload', 'width', 'height']:
                    del tag[attr]
                for attr in list(tag.attrs):  # Iterate over a copy of the attributes
                    if  attr != 'src' and attr != 'class' and attr != 'id':
                    # if attr.startswith('data-') or attr.startswith('aria-') or attr.startswith('search-') or attr.startswith('value'):
                        del tag[attr]

            cleaned_html = str(soup)
            # print(f"3: {cleaned_html.index('$27')}")
            # print(cleaned_html.index('<img'))
            # print(cleaned_html[472:500])
            
            # remove text tags without texts
            for tag in soup.find_all(): # Check all tags
                if tag.get_text(strip=True) == '' and tag.name != 'img' and not tag.find('img'):
                    # If it's a tag with no text and no <img> children, remove it
                    tag.unwrap()
            
            cleaned_html = str(soup)
            # print(f"4: {cleaned_html.index('$27')}")
            # try:
            #     print(cleaned_html.index('<img'))
            # except Exception as e:
            #     print(e)

            # remove white spaces
            for element in soup.find_all(text = True):
                element.replace_with(element.strip())

            # print(soup.find('img').name)
            
            cleaned_html = str(soup)
            # print(f"5: {cleaned_html.index('$27')}")
            cleaned_html = str(soup)
            # print(len(cleaned_html))
            if context_length == 0:
                print("ZERO")
                return cleaned_html
            
            if len(cleaned_html) < context_length + 300:
                # print(len(cleaned_html))

                return cleaned_html
            
            # clean level 3
            # remove tags with text leaving only the text
            for tag in soup.find_all(['p', 'b', 'span', 'strong', 'i', 'em', 'mark', 'small', 'del', 'ins', 'sub', 'sup', 'a', 'option']):
                if tag.find('img'):
                    continue
                tag.unwrap()


            cleaned_html = str(soup)
            # print(f"7: {cleaned_html.index('$27')}")
            
            for tag in soup.find_all():
                for attr in ['role', 'id', 'alt', 'title']:
                    del tag[attr]


            cleaned_html = str(soup)
            # print(f"8: {cleaned_html.index('$27')}")

            cleaned_html = str(soup)
            if len(cleaned_html) < context_length + 500:
                print(len(cleaned_html))

                return cleaned_html
            

            # clean level 4
            # remove class attributes
            for tag in soup.find_all():
                for attr in ['class']:
                    del tag[attr]

            cleaned_html = str(soup)
            # print(f"9: {cleaned_html.index('$27')}")

            cleaned_html = str(soup)
            if len(cleaned_html) < context_length + 500:
                print(len(cleaned_html))
                return cleaned_html
            
            # clean level 5
            print('level5')
            # remove divs leaving just the text 
            for element in soup.find_all('div'):
                if element.get_text(strip=True):  
                    element.unwrap()  
                else:
                    element.decompose()

            cleaned_html = str(soup)
            # print(f"10: {cleaned_html.index('$27')}")  
            
            cleaned_html = str(soup)
            if len(cleaned_html) < context_length + 500:
                print(len(cleaned_html))

            return cleaned_html
            

    def split_html(self, html: str, chunk_size: int) -> list[str]:
        """
        Divide un HTML en fragmentos, asegurándose de que cada fragmento no exceda un tamaño máximo,
        que se divida al final de una etiqueta y que los fragmentos no se solapen.

        Args:
            html: El HTML a dividir.
            max_length: El tamaño máximo de cada fragmento (en caracteres).

        Returns:
            Una lista de fragmentos HTML.
        """

        soup = BeautifulSoup(html, "html.parser")
        fragments = []
        current_fragment = ""

        for element in soup.body.contents:
            element_string = str(element)

            if len(current_fragment) + len(element_string) <= chunk_size:
                current_fragment += element_string
            else:
                if current_fragment:
                    fragments.append(current_fragment)
                current_fragment = element_string

        if current_fragment:
            fragments.append(current_fragment)

        return fragments