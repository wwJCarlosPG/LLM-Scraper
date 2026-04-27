import requests
from bs4 import BeautifulSoup, Comment
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from scraper.core.consts import (
    ALLOWED_ATTRIBUTES,
    INLINE_TAGS,
    LEVEL3_ATTRIBUTES,
    NOISE_TAGS,
)
from scraper.core.ports.cleaner_port import CleanerPort


class DefaultHTMLCleaner(CleanerPort):
    def fetch(self, url: str) -> str:
        retry_strategy = Retry(total=5, backoff_factor=1, connect=3)
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session = requests.Session()
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        response = session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def clean(self, html: str, context_length: int = 0) -> str:
        soup = BeautifulSoup(html, "html.parser")

        # Level 1: remove noise tags
        for tag in NOISE_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        # remove comments
        for comment in soup.find_all(text=lambda t: isinstance(t, Comment)):
            comment.extract()

        # Level 2: remove unnecessary attributes
        for tag in soup.find_all():
            for attr in list(tag.attrs):
                if attr not in ALLOWED_ATTRIBUTES:
                    del tag[attr]

        # remove empty tags
        for tag in soup.find_all():
            if (
                tag.get_text(strip=True) == ""
                and tag.name != "img"
                and not tag.find("img")
            ):
                tag.unwrap()

        # remove whitespace
        for element in soup.find_all(text=True):
            element.replace_with(element.strip())

        cleaned = str(soup)

        if context_length == 0 or len(cleaned) < context_length + 300:
            return cleaned

        # Level 3: unwrap inline tags
        for tag in soup.find_all(INLINE_TAGS):
            if not tag.find("img"):
                tag.unwrap()

        for tag in soup.find_all():
            for attr in LEVEL3_ATTRIBUTES:
                if attr in tag.attrs:
                    del tag[attr]

        cleaned = str(soup)
        if len(cleaned) < context_length + 500:
            return cleaned

        # Level 4: remove class attributes
        for tag in soup.find_all():
            if "class" in tag.attrs:
                del tag["class"]

        cleaned = str(soup)
        if len(cleaned) < context_length + 500:
            return cleaned

        # Level 5: unwrap divs
        for element in soup.find_all("div"):
            if element.get_text(strip=True):
                element.unwrap()
            else:
                element.decompose()

        cleaned = str(soup)
        if len(cleaned) < context_length + 500:
            return cleaned

        # Level 6: plain text fallback
        return soup.get_text("\n", strip=True)

    def split(self, html: str, chunk_size: int) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        fragments = []
        current = ""

        body = soup.body if soup.body else soup
        for element in body.contents:
            element_str = str(element)
            if len(current) + len(element_str) <= chunk_size:
                current += element_str
            else:
                if current:
                    fragments.append(current)
                current = element_str

        if current:
            fragments.append(current)

        return fragments

    def light_clean(self, html: str, context_length: int = 0) -> str:
        """
        Removes only noise tags (scripts, styles, meta) while preserving
        the full semantic structure including headers. Used for chunking.
        """
        soup = BeautifulSoup(html, "html.parser")

        for tag in NOISE_TAGS:
            for el in soup.find_all(tag):
                el.decompose()

        for comment in soup.find_all(text=lambda t: isinstance(t, Comment)):
            comment.extract()

        return str(soup)
