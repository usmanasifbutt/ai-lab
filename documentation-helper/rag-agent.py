import asyncio
import os

import truststore
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

truststore.inject_into_ssl()
load_dotenv()

if not (INDEX_NAME := os.environ.get("INDEX_NAME")):
    raise ValueError("INDEX_NAME environment variable is missing or empty")

embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=1536)
llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0.2)

store = PineconeVectorStore(index_name=INDEX_NAME, embedding=embeddings)
retriever = store.as_retriever(search_kwargs={"k": 3})


@tool(response_format="content_and_artifact")
async def retrieve_context(query):
    """Retrive context to answer user query related to documentation"""
    docs = await retriever.ainvoke(query)
    context = "\n\n".join(
        f"Content: {doc.page_content}\n\nSource: {doc.metadata.get("source", "Unknown")}"
        for doc in docs
    )

    return context, docs


async def rag(question: str) -> str:
    """ "Create a chain using LCEL, that answer based on context."""

    system_prompt = SystemMessage("""
You are a helpfull assistant. Your task is to answer user queries strictly using the provided context below. 

RULES:
1. Grounding: Answer ONLY using facts directly mentioned in the context. Do not extrapolate, assume, or use outside knowledge.
2. Missing Information: If the answer cannot be found within the context, respond strictly with: "I cannot find the answer in the provided documents."
3. Citations: Cite the specific document or source chunk for every major claim you make.
4. Tone: Keep responses objective, clear, and concise.
""")

    messages = [HumanMessage(question)]

    agent = create_agent(
        model=llm, tools=[retrieve_context], system_prompt=system_prompt
    )
    response = await agent.ainvoke({"messages": messages})

    answer = response["messages"][-1].content
    sources = []

    for message in response["messages"]:
        if isinstance(message, ToolMessage) and hasattr(message, "artifact"):
            for item in message.artifact:
                sources.append(item.metadata.get("source"))

    return {
        "answer": answer, 
        "sources": sources
    }


if __name__ == "__main__":
    question = "What is the use of pinecone Claude Code plugin ?"
    result = asyncio.run(rag(question))

    print(f"\nQuestion: {question}\n")
    print(f"Answer:\n{result['answer']}\n")
    print("Sources:")
    for source in result["sources"]:
        print(f"  - {source}")
