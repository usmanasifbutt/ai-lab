import asyncio
import logging
import os
from itertools import batched

import truststore
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone.vectorstores import PineconeVectorStore
from langchain_tavily import TavilyCrawl, TavilyExtract, TavilyMap
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()
truststore.inject_into_ssl()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

BATCH_SIZE = 100
MAX_CONCURRENT_BATCHES = 4

tavily_extract = TavilyExtract()
tavily_map = TavilyMap(max_depth=5, max_breadth=20, max_pages=1000)
tavily_crawl = TavilyCrawl()


async def main(url: str):
    logger.info("Welcome to documentation helper\n" + "=" * 60)

    res = await tavily_crawl.ainvoke(
        {
            "url": url,
            "max_depth": 3,
            "extract_depth": "advanced",
        }
    )

    results = res["results"]
    docs = [
        Document(page_content=doc["raw_content"], metadata={"source": doc["url"]})
        for doc in results
        if doc.get("raw_content")
    ]
    logger.info(
        f"✅ Crawled {url}: {len(docs)} pages with content, {len(results) - len(docs)} skipped as empty."
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=200)
    chunks = splitter.split_documents(docs)
    logger.info(f"Split {len(docs)} pages into {len(chunks)} chunks.")

    batches = list(batched(chunks, BATCH_SIZE))

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)
    store = PineconeVectorStore(
        index_name=os.environ["INDEX_NAME"], embedding=embeddings
    )

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_BATCHES)

    async def index_batch(n: int, batch: list[Document]) -> None:
        async with semaphore:
            try:
                logger.info(f"🔄 Indexing batch {n+1} of size {len(batch)}...")
                await store.aadd_documents(batch)
                logger.info(f"✅ Batch {n+1} indexed successfully.")
            except Exception as e:
                logger.error(f"❌ Error indexing batch {n+1}: {e}")
                raise

    async with store:
        outcomes = await asyncio.gather(
            *(index_batch(n, batch) for n, batch in enumerate(batches)),
            return_exceptions=True,
        )

    failed = sum(isinstance(i, Exception) for i in outcomes)
    logger.info(f"{'='*20} Summary {'='*20}")
    logger.info(
        f"✅ {len(batches) - failed} batches indexed successfully.\n❌ {failed} batches failed."
    )


if __name__ == "__main__":
    url = "https://docs.pinecone.io/guides/get-started/overview"
    asyncio.run(main(url))
