"""
Interactive dataset labeling tool.
Run with: poetry run python scripts/label_dataset.py

For each page and query, the script opens the page in your browser
and prompts you to enter the expected extraction results manually.
Results are saved incrementally so you can stop and resume at any time.
"""

import json
import os
import webbrowser
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv()

OUTPUT_PATH = "tests/fixtures/labeled/dataset.json"
QUERIES_PATH = "tests/fixtures/labeled/queries.json"


def load_queries() -> dict:
    with open(QUERIES_PATH) as f:
        return json.load(f)


def load_existing() -> list[dict]:
    if os.path.exists(OUTPUT_PATH):
        with open(OUTPUT_PATH) as f:
            return json.load(f)
    return []


def save(dataset: list[dict]):
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)


def already_labeled(dataset: list[dict], query_id: int, domain: str) -> bool:
    return any(e.get("id") == query_id and e.get("domain") == domain for e in dataset)


def page_name_from_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_")
    name = parsed.netloc.replace("www.", "").replace(".", "_")
    return f"{name}_{path}" if path else name


def prompt_expected(output_format: dict) -> list[dict]:
    fields = list(output_format.keys())
    items = []

    print(f"\n  Fields to fill: {fields}")
    print("  Enter one value per field. Press Enter with no value to finish an item.")
    print("  Press Enter twice in a row to finish all items.\n")

    while True:
        item = {}
        for field in fields:
            value = input(f"    {field}: ").strip()
            if not value:
                break
            item[field] = value

        if not item:
            break

        if len(item) == len(fields):
            items.append(item)
            print(f"  ✓ Added: {item}")
        else:
            print("  ✗ Incomplete item, skipping.")

    return items


def main():
    dataset = load_existing()
    queries_by_domain = load_queries()

    total = sum(len(queries) for queries in queries_by_domain.values())
    labeled = len(dataset)

    print(f"\n{'=' * 60}")
    print("LLM Scraper — Dataset Labeling Tool")
    print(f"Progress: {labeled}/{total} entries labeled")
    print(f"Output: {OUTPUT_PATH}")
    print(f"{'=' * 60}")
    print("\nInstructions:")
    print("  1. The page will open in your browser")
    print("  2. Read the query carefully")
    print("  3. Find the answer IN THE PAGE (not from the model)")
    print("  4. Enter each expected item field by field")
    print("  5. Press Ctrl+C at any time to save and exit\n")

    try:
        for domain, queries in queries_by_domain.items():
            for query_entry in queries:
                query_id = query_entry["id"]
                query = query_entry["query"]
                url = query_entry["url"]
                page = page_name_from_url(url)

                if already_labeled(dataset, query_id, domain):
                    print(f"  [skip] id={query_id} — {query[:50]}...")
                    continue

                print(f"\n{'─' * 60}")
                print(f"  Domain    : {domain}")
                print(f"  ID        : {query_id}")
                print(f"  URL       : {url}")
                print(f"  Query     : {query}")
                print(f"  Format    : {query_entry['output_format']}")
                print(f"  Complexity: {query_entry['complexity']}")
                print(f"{'─' * 60}")

                open_browser = (
                    input("\n  Open page in browser? (y/n): ").strip().lower()
                )
                if open_browser == "y":
                    webbrowser.open(url)

                expected = prompt_expected(query_entry["output_format"])

                if not expected:
                    skip = (
                        input("  No items entered. Skip this entry? (y/n): ")
                        .strip()
                        .lower()
                    )
                    if skip == "y":
                        print("  [skipped]")
                        continue

                entry = {
                    "id": query_id,
                    "page": page,
                    "domain": domain,
                    "url": url,
                    "query": query,
                    "complexity": query_entry["complexity"],
                    "output_format": query_entry["output_format"],
                    "expected": expected,
                }

                dataset.append(entry)
                save(dataset)
                print(f"  ✓ Saved ({len(dataset)}/{total})")

    except KeyboardInterrupt:
        print(f"\n\nInterrupted. Progress saved: {len(dataset)}/{total} entries.")

    print(f"\nDone. Dataset saved to {OUTPUT_PATH}")
    print(f"Total entries: {len(dataset)}/{total}")


if __name__ == "__main__":
    main()
