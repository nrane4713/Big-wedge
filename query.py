"""
Retrieve the most relevant wiki chunks for a question from the Chroma vector store.

Usage (manual test):
    python query.py "how do I fix a bad side profile"
"""

import os
import sys

import chromadb
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CHROMA_PERSIST_DIR = os.environ.get("CHROMA_PERSIST_DIR", "./data/chroma")
CHROMA_COLLECTION = os.environ.get("CHROMA_COLLECTION", "wiki_articles")
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")

_openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
_chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)


def retrieve(question: str, k: int = 4) -> list[dict]:
    """Return the top-k chunks most relevant to `question`, each as
    {"text": ..., "title": ..., "url": ...}."""
    collection = _chroma_client.get_or_create_collection(CHROMA_COLLECTION)

    embedding = _openai_client.embeddings.create(
        model=EMBEDDING_MODEL, input=[question]
    ).data[0].embedding

    results = collection.query(query_embeddings=[embedding], n_results=k)

    chunks = []
    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    for text, meta in zip(documents, metadatas):
        chunks.append({"text": text, "title": meta.get("title"), "url": meta.get("url")})
    return chunks


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "how do I fix a bad side profile"
    for chunk in retrieve(question):
        print(f"--- {chunk['title']} ({chunk['url']}) ---")
        print(chunk["text"][:300])
        print()
