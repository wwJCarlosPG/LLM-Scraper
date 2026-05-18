"""
Script to fetch and save HTML pages for chunking benchmark.
Run with: poetry run python scripts/fetch_pages.py
"""

import os
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

PAGES = {
    "news": [
        {
            "name": "bbc_chernobyl",
            "url": "https://www.bbc.com/future/article/20260424-chernobyl-wildlife-forty-years-on",
        },
        {
            "name": "bbc_climate",
            "url": "https://www.bbc.com/news/articles/cyv1zdey7pmo",
        },
        {
            "name": "bbc_ai",
            "url": "https://www.bbc.com/future/article/20260505-how-to-use-ai-without-turning-your-brain-to-mush",
        },
    ],
    "ecommerce": [
        {"name": "books_home", "url": "https://books.toscrape.com"},
        {"name": "scrapeme_shop", "url": "https://scrapeme.live/shop/"},
        {
            "name": "webscraper_computers",
            "url": "https://webscraper.io/test-sites/e-commerce/allinone/computers/laptops",
        },
    ],
    "documentation": [
        {
            "name": "python_functions",
            "url": "https://docs.python.org/3/tutorial/controlflow.html",
        },
        {
            "name": "python_classes",
            "url": "https://docs.python.org/3/tutorial/classes.html",
        },
        {
            "name": "python_exceptions",
            "url": "https://docs.python.org/3/tutorial/errors.html",
        },
    ],
    "unstructured": [
        {
            "name": "stackoverflow_discussion",
            "url": "https://stackoverflow.com/questions/16139712/how-to-design-a-hierarchical-role-based-access-control-system?rq=2",
        },
        {
            "name": "hackernews_comments",
            "url": "https://news.ycombinator.com/newcomments?next=48050039",
        },
        {
            "name": "wikipedia_python",
            "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
        },
    ],
}

OUTPUT_DIR = "tests/fixtures/pages"


def make_session() -> requests.Session:
    retry_strategy = Retry(total=3, backoff_factor=1)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
    )
    return session


def fetch_and_save(session: requests.Session, domain: str, name: str, url: str) -> bool:
    domain_dir = os.path.join(OUTPUT_DIR, domain)
    os.makedirs(domain_dir, exist_ok=True)

    output_path = os.path.join(domain_dir, f"{name}.html")

    if os.path.exists(output_path):
        print(f"  [skip] {name} already exists")
        return True

    try:
        response = session.get(url, timeout=15)
        response.raise_for_status()

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response.text)

        size_kb = len(response.text) / 1024
        print(f"  [ok] {name} — {size_kb:.1f} KB saved to {output_path}")
        return True

    except Exception as e:
        print(f"  [fail] {name}: {e}")
        return False


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    session = make_session()

    total = sum(len(pages) for pages in PAGES.values())
    fetched = 0
    failed = 0

    for domain, pages in PAGES.items():
        print(f"\n── {domain} ──────────────────────────")
        for page in pages:
            success = fetch_and_save(session, domain, page["name"], page["url"])
            if success:
                fetched += 1
            else:
                failed += 1
            time.sleep(1)  # be polite

    print("\n── Summary ──────────────────────────")
    print(f"  Fetched : {fetched}/{total}")
    print(f"  Failed  : {failed}/{total}")
    print(f"  Saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
