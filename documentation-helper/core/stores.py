from langchain_openai import ChatOpenAI
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore

from core import config


def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=config.EMBEDDING_MODEL, dimensions=config.EMBEDDING_DIMENSIONS
    )


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(model=config.LLM_MODEL, temperature=0.2)


def get_store() -> PineconeVectorStore:
    return PineconeVectorStore(
        index_name=config.require_env("INDEX_NAME"), embedding=get_embeddings()
    )
