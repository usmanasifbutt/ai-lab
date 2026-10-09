# documentation-helper

RAG over a documentation website: crawl a docs site with [Tavily](https://tavily.com), split and
embed the pages with OpenAI, store them in [Pinecone](https://www.pinecone.io), then ask
questions and get answers grounded in the docs, with source URLs.

## Prerequisites

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- API keys for OpenAI, Tavily and Pinecone
- A Pinecone index with **1536 dimensions** (matches `text-embedding-3-small`)

## Setup

```bash
uv sync
```

Create a `.env` file in this folder:

```
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
PINECONE_API_KEY=...
INDEX_NAME=your-pinecone-index

# optional: LangSmith tracing
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=documentation-helper
```

## Running

Ingest a site (set the start URL at the bottom of `core/ingestion.py`):

```bash
uv run python -m core.ingestion
```

Ask a question (set the question at the bottom of each file):

```bash
uv run python -m core.chain   # LCEL chain: retrieve, prompt, answer
uv run python -m core.agent   # agent with a retrieval tool, prints answer and sources
```

Delete every vector in the index (cannot be undone):

```bash
uv run python scripts/cleanup_index.py
```

## How it works

- `core/ingestion.py`: Tavily crawl, split into chunks (`RecursiveCharacterTextSplitter`), then index
  in concurrent batches (`BATCH_SIZE`, `MAX_CONCURRENT_BATCHES`) with the async Pinecone client.
- `core/chain.py`: async LCEL chain. The retriever fetches the top 5 chunks, and the model answers
  strictly from that context.
- `core/agent.py`: the same idea as an agent with a `retrieve_context` tool. It returns the answer
  plus the source URLs of the retrieved chunks.

## Known quirks

- **Re-ingesting adds duplicates.** Vector IDs are random, so running `ingestion.py` twice stores
  every chunk twice. Run `scripts/cleanup_index.py` first.
- **Read the Docs sites crawl poorly.** Tavily resolves relative links against the start URL
  without its trailing slash (`/en/latest/` becomes `/en/`), so most discovered pages 404 and come
  back empty.
- **Corporate TLS inspection.** `truststore.inject_into_ssl()` makes Python use the Windows
  certificate store, which fixes `CERTIFICATE_VERIFY_FAILED` errors behind proxies such as
  Zscaler.
