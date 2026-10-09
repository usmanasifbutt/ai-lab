import asyncio
from operator import itemgetter

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough

from core import config  # noqa: F401
from core import stores


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(
        f"Content: {doc.page_content}\n\nSource: {doc.metadata.get('source', 'Unknown')}"
        for doc in docs
    )


async def rag(question: str) -> str:
    """Create a chain using LCEL, that answer based on context."""
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

    async with stores.get_store() as store:
        retriever = store.as_retriever(search_kwargs={"k": 5})

        chain = (
            RunnablePassthrough.assign(
                context=itemgetter("question") | retriever | format_docs
            )
            | prompt_template
            | stores.get_llm()
            | StrOutputParser()
        )

        return await chain.ainvoke({"question": question})


if __name__ == "__main__":
    question = "What is the use of pinecone Claude Code plugin ?"
    print(asyncio.run(rag(question)))
