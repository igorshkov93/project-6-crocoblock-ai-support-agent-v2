"""Download documentation pages and extract clean text."""
import json
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URLS_FILE = Path("data/doc_urls.json")
OUTPUT = Path("data/docs.json")
HEADERS = {"User-Agent": "crocoblock-support-agent/1.0 (portfolio project)"}
DELAY = 0.5


def extract_page(url: str) -> dict | None:
    """Fetch a page and return its title and main text."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    title = soup.find("h1")
    title = title.get_text(strip=True) if title else url.rstrip("/").split("/")[-1]

    # Select the content container FIRST, then clean inside it.
    main = soup.find("main") or soup.find("div", class_="single-addon")
    if main is None:
        return None

    for tag in main.find_all(["script", "style", "nav", "noscript"]):
        tag.decompose()

    # Remove the "related docs" navigation block found on feature pages.
    for tag in main.find_all(class_="related-docs"):
        tag.decompose()

    text = main.get_text(separator="\n", strip=True)
    lines = [line for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)

    if len(text) < 200:
        return None

    return {"url": url, "title": title, "text": text, "chars": len(text)}


def main():
    urls = json.loads(URLS_FILE.read_text(encoding="utf-8"))
    print(f"Pages to fetch: {len(urls)}\n")

    docs = []
    skipped = []

    for index, url in enumerate(urls, 1):
        try:
            page = extract_page(url)
            if page:
                docs.append(page)
                status = f"{page['chars']:>6} chars  {page['title'][:50]}"
            else:
                skipped.append(url)
                status = "  too short, skipped"
        except Exception as error:
            skipped.append(url)
            status = f"  failed: {type(error).__name__}"

        print(f"  [{index:>3}/{len(urls)}] {status}")
        time.sleep(DELAY)

    OUTPUT.write_text(json.dumps(docs, indent=2, ensure_ascii=False), encoding="utf-8")

    total_chars = sum(d["chars"] for d in docs)
    print(f"\nCollected: {len(docs)} pages, {total_chars:,} characters")
    print(f"Skipped:   {len(skipped)}")
    print(f"Saved:     {OUTPUT}")


if __name__ == "__main__":
    main()