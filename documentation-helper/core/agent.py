import asyncio

from langchain.agents import create_agent
from langchain.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool

from core import config  # noqa: F401
from core import stores

NOT_FOUND = "I cannot find the answer in the provided documents."

SYSTEM_PROMPT = f"""
You are a helpful assistant. Answer user queries strictly using the context returned by the retrieval tool.

RULES:
1. Grounding: Answer ONLY using facts directly mentioned in the context. Do not extrapolate, assume, or use outside knowledge.
2. Missing Information: If the answer cannot be found within the context, respond strictly with: "{NOT_FOUND}"
3. Citations: Cite the specific document or source chunk for every major claim you make.
4. Tone: Keep responses objective, clear, and concise.
"""


async def rag(question: str, k: int = 3) -> dict:
    async with stores.get_store() as store:
        retriever = store.as_retriever(search_kwargs={"k": k})

        @tool(response_format="content_and_artifact")
        async def retrieve_context(query: str):
            """Retrieve context to answer user queries about the documentation."""
            docs = await retriever.ainvoke(query)
            context = "\n\n".join(
                f"Content: {d.page_content}\n\nSource: {d.metadata.get('source', 'Unknown')}"
                for d in docs
            )
            return context, docs

        agent = create_agent(
            model=stores.get_llm(),
            tools=[retrieve_context],
            system_prompt=SYSTEM_PROMPT,
        )
        response = await agent.ainvoke({"messages": [HumanMessage(question)]})

    answer = response["messages"][-1].content
    if NOT_FOUND in answer:
        return {"answer": answer, "sources": []}

    sources = list(
        dict.fromkeys(
            doc.metadata.get("source")
            for message in response["messages"]
            if isinstance(message, ToolMessage)
            for doc in (message.artifact or [])
        )
    )
    return {"answer": answer, "sources": sources}


if __name__ == "__main__":
    question = "What is the use of pinecone Claude Code plugin ?"
    result = asyncio.run(rag(question))

    print(f"\nQuestion: {question}\n")
    print(f"Answer:\n{result['answer']}\n")
    print("Sources:")
    for source in result["sources"]:
        print(f"  - {source}")
