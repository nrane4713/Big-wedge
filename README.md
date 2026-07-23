# Oncall Agent

A basic RAG assistant that answers oncall engineers' questions using content
pulled from a wiki. It fetches articles, chunks and embeds them into a local
vector database, and answers chat questions with Claude using only the
retrieved excerpts (with sources cited).

Currently pointed at a single placeholder article
(https://www.wikihow.com/Bad-Side-Profile) so the pipeline can be built and
tested end to end before real wiki credentials are added.

## Architecture

```
fetch_articles.py  -> data/articles/*.json      (scrape wiki pages to plain text)
build_index.py      -> data/chroma/              (chunk + OpenAI embeddings -> Chroma vector DB)
query.py            -> retrieve(question)        (embed question, vector search)
app.py               (Chainlit chat UI, calls query.py then Anthropic Claude)
```

- **LLM (answers):** Anthropic Claude
- **Embeddings:** OpenAI
- **Vector store:** Chroma (local, persisted to disk) — chosen because it
  speaks the same embedding-vector interface most vector DBs use, so swapping
  in Snowflake or another store later is a small change, not a rewrite.
- **Chat UI:** Chainlit

`.env.example` also reserves variables for Confluence (real wiki source) and
Snowflake — not wired into any code yet, just placeholders so the shape is
ready when those credentials are added.

## Setup (PowerShell)

```powershell
git clone <this repo>
cd Big-wedge

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .

Copy-Item .env.example .env
notepad .env   # fill in ANTHROPIC_API_KEY and OPENAI_API_KEY at minimum

python fetch_articles.py
python build_index.py

chainlit run app.py -w
```

Or run everything with the helper script:

```powershell
./run.ps1
```

## Manually testing retrieval

```powershell
python query.py "how do I fix a bad side profile"
```

## Files

| File | Purpose |
|---|---|
| `fetch_articles.py` | Scrapes wiki article URLs into `data/articles/*.json` |
| `build_index.py` | Chunks articles, embeds them (OpenAI), stores in Chroma |
| `query.py` | Embeds a question and retrieves the top-k relevant chunks |
| `app.py` | Chainlit chat app — retrieves context, asks Claude, shows sources |
| `chainlit.md` | Chat UI welcome screen |
| `run.ps1` | One-command setup + launch for PowerShell |
| `.env.example` | Template for all credentials (copy to `.env`, never commit `.env`) |

## Roadmap

- Replace the WikiHow placeholder with real Confluence wiki ingestion
  (`CONFLUENCE_*` vars already reserved in `.env.example`).
- Evaluate moving the vector store to Snowflake once credentials are
  available (`SNOWFLAKE_*` vars already reserved).
- Productionize: auth, logging/observability, scheduled re-indexing,
  deployment target.
