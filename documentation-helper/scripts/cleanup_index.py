import os

import truststore
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()
truststore.inject_into_ssl()

API_KEY = os.environ.get("PINECONE_API_KEY")
INDEX_NAME = os.environ.get("INDEX_NAME")

if not (INDEX_NAME and API_KEY):
    raise ValueError("API KEY or INDEX NAME is not defined")

pc = Pinecone(api_key=API_KEY)
index = pc.Index(name=INDEX_NAME)

# Clear everything in a specific namespace
index.delete(delete_all=True)
