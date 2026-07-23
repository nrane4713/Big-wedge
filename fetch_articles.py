"""
Fetch wiki articles and save their text content as JSON files in data/articles/.

Usage:
    python fetch_articles.py
    python fetch_articles.py https://www.wikihow.com/Some-Other-Article

If no URL is given on the command line, every URL in the WIKI_ARTICLE_URLS
env var (comma-separated) is fetched.
"""

import json
import os
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

ARTICLES_DIR = Path("data/articles")
HEADERS = {"User-Agent": "Mozilla/5.0 (oncall-agent article fetcher)"}


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return slug or "article"


def fetch_article(url: str) -> dict:
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    title_tag = soup.find("h1")
    title = title_tag.get_text(strip=True) if title_tag else url

    content = (
        soup.find(id="mw-content-text")
        or soup.find(id="bodycontent")
        or soup.find("article")
        or soup.body
    )
    paragraphs = [
        tag.get_text(" ", strip=True)
        for tag in content.find_all(["p", "li"])
    ]
    text = "\n".join(p for p in paragraphs if p)

    return {"url": url, "title": title, "text": text}


def main() -> None:
    urls = sys.argv[1:]
    if not urls:
        raw = os.environ.get("WIKI_ARTICLE_URLS", "")
        urls = [u.strip() for u in raw.split(",") if u.strip()]

    if not urls:
        print("No URLs to fetch. Set WIKI_ARTICLE_URLS in .env or pass URLs as arguments.")
        sys.exit(1)

    ARTICLES_DIR.mkdir(parents=True, exist_ok=True)

    for url in urls:
        print(f"Fetching {url} ...")
        article = fetch_article(url)
        out_path = ARTICLES_DIR / f"{slugify(article['title'])}.json"
        out_path.write_text(json.dumps(article, indent=2), encoding="utf-8")
        print(f"  saved {out_path} ({len(article['text'])} chars)")


if __name__ == "__main__":
    main()
