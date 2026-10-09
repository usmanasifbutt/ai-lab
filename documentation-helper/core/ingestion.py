import asyncio
import logging
from collections.abc import Callable
from itertools import batched

from langchain_core.documents import Document
from langchain_tavily import TavilyCrawl
from langchain_text_splitters import RecursiveCharacterTextSplitter

from core import config  # noqa: F401
from core import stores

logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MAX_CONCURRENT_BATCHES = 4

ProgressCallback = Callable[[str, float], None]  # (message, fraction 0..1)


async def crawl(url: str, max_depth: int = 3) -> tuple[list[Document], int]:
    res = await TavilyCrawl().ainvoke(
        {"url": url, "max_depth": max_depth, "extract_depth": "advanced"}
    )
    results = res["results"]
    docs = [
        Document(page_content=r["raw_content"], metadata={"source": r["url"]})
        for r in results
        if r.get("raw_content")
    ]
    return docs, len(results)


def split(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    return splitter.split_documents(docs)


async def index_chunks(
    chunks: list[Document], on_progress: ProgressCallback | None = None
) -> tuple[int, int]:
    """Index chunks in concurrent batches. Returns (succeeded, failed) batch counts."""
    batches = list(batched(chunks, BATCH_SIZE))
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)
    finished = 0

    async with stores.get_store() as store:

        async def index_batch(batch):
            nonlocal finished
            async with semaphore:
                try:
                    await store.aadd_documents(list(batch))
                finally:
                    finished += 1
                    if on_progress:
                        on_progress(
                            f"Indexed {finished}/{len(batches)} batches",
                            0.1 + 0.9 * finished / len(batches),
                        )

        outcomes = await asyncio.gather(
            *(index_batch(b) for b in batches), return_exceptions=True
        )

    for outcome in outcomes:
        if isinstance(outcome, Exception):
            logger.error("Batch failed: %r", outcome)
    failed = sum(isinstance(o, Exception) for o in outcomes)
    return len(batches) - failed, failed


async def ingest(
    url: str, max_depth: int = 3, on_progress: ProgressCallback | None = None
) -> dict:
    def report(message: str, fraction: float) -> None:
        if on_progress:
            on_progress(message, fraction)
        else:
            logger.info(message)

    report(f"Crawling {url}...", 0.0)
    docs, total_pages = await crawl(url, max_depth)

    report(f"Splitting {len(docs)} pages...", 0.1)
    chunks = split(docs)

    ok, failed = await index_chunks(chunks, on_progress)
    return {
        "pages": len(docs),
        "empty_pages": total_pages - len(docs),
        "chunks": len(chunks),
        "batches_ok": ok,
        "batches_failed": failed,
    }


def show(message: str, fraction: float) -> None:
    print(f"[{fraction:>4.0%}] {message}")


if __name__ == "__main__":
    print(
        asyncio.run(
            ingest(
                "https://docs.pinecone.io/guides/get-started/overview", on_progress=show
            )
        )
    )
