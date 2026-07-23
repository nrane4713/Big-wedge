"""
Chunk every article in data/articles/, embed the chunks with OpenAI, and
store them in a local persistent Chroma vector database.

Usage:
    python build_index.py
"""

import json
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

ARTICLES_DIR = Path("data/articles")
CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma")
CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "wiki_articles")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

CHUNK_WORDS = 200
CHUNK_OVERLAP_WORDS = 40


def chunk_text(text: str, chunk_words: int = CHUNK_WORDS, overlap_words: int = CHUNK_OVERLAP_WORDS) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    step = chunk_words - overlap_words
    for start in range(0, len(words), step):
        chunk = " ".join(words[start:start + chunk_words])
        if chunk:
            chunks.append(chunk)
        if start + chunk_words >= len(words):
            break
    return chunks


def main() -> None:
    article_files = sorted(ARTICLES_DIR.glob("*.json"))
    if not article_files:
        print(f"No articles found in {ARTICLES_DIR}. Run fetch_articles.py first.")
        return

    openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma_client.get_or_create_collection(CHROMA_COLLECTION)

    ids, documents, metadatas = [], [], []

    for path in article_files:
        article = json.loads(path.read_text(encoding="utf-8"))
        chunks = chunk_text(article["text"])
        print(f"{article['title']}: {len(chunks)} chunks")
        for i, chunk in enumerate(chunks):
            ids.append(f"{path.stem}-{i}")
            documents.append(chunk)
            metadatas.append({"title": article["title"], "url": article["url"]})

    if not documents:
        print("No text to index.")
        return

    print(f"Embedding {len(documents)} chunks with {EMBEDDING_MODEL} ...")
    response = openai_client.embeddings.create(model=EMBEDDING_MODEL, input=documents)
    embeddings = [item.embedding for item in response.data]

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
    print(f"Indexed {len(documents)} chunks into '{CHROMA_COLLECTION}' at {CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    main()
