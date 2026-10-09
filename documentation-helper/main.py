import asyncio
import os
from operator import itemgetter

import truststore
from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

truststore.inject_into_ssl()
load_dotenv()


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(
        f"Content: {doc.page_content}\n\nSource: {doc.metadata.get("source", "Unknown")}"
        for doc in docs
    )


async def rag(question: str) -> str:
    """ "Create a chain using LCEL, that answer based on context."""
    if not (INDEX_NAME := os.environ.get("INDEX_NAME")):
        raise ValueError("INDEX_NAME environment variable is missing or empty")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)
    llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.2)

    store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
    retriever = store.as_retriever(search_kwargs={"k": 3})

    prompt_template = ChatPromptTemplate.from_template("""<system>
You are a helpfull assistant. Your task is to answer user queries strictly using the provided context below. 

RULES:
1. Grounding: Answer ONLY using facts directly mentioned in the <context>. Do not extrapolate, assume, or use outside knowledge.
2. Missing Information: If the answer cannot be found within the <context>, respond strictly with: "I cannot find the answer in the provided documents."
3. Citations: Cite the specific document or source chunk for every major claim you make.
4. Tone: Keep responses objective, clear, and concise.
</system>

<context>
{context}
</context>

<user_query>
{question}
</user_query>
""")

    chain = (
        RunnablePassthrough.assign(
            context=itemgetter("question") | retriever | format_docs
        )
        | prompt_template
        | llm
        | StrOutputParser()
    )

    try:
        return await chain.ainvoke({"question": question})
    finally:
        await store.aclose()


if __name__ == "__main__":
    question = "What is the use of pinecone Claude Code plugin ?"
    print(asyncio.run(rag(question)))
