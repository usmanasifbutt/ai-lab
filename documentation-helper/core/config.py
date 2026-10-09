import logging
import os

import truststore
from dotenv import load_dotenv

truststore.inject_into_ssl()
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
LLM_MODEL = "gpt-4.1-mini"


def require_env(name: str) -> str:
    if not (value := os.environ.get(name)):
        raise ValueError(f"{name} environment variable is missing or empty")
    return value
