import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

FORMAT_MODEL = "gpt-4o-mini"
# Used only when OPENAI_API_KEY isn't set - small enough to run on CPU.
LOCAL_MODEL = "HuggingFaceTB/SmolLM2-360M-Instruct"

_SYSTEM_PROMPT = (
    "You clean up voice-dictated notes into well-formatted text.\n\n"
    "Rules (you must follow all of these):\n"
    "1. Fix typos and grammar.\n"
    "2. Remove filler words (um, uh, aah, like).\n"
    "3. Remove em dashes.\n"
    "4. Organize the content with headings, bullet points, and paragraphs where appropriate.\n"
    "5. Preserve the speaker's meaning and wording as much as possible.\n"
    "6. Respond with the rewritten note ONLY - no explanations, no list of changes, "
    "no commentary, no closing remarks.\n"
    "7. Never start your reply with phrases like 'Sure', 'Here's the...', 'Certainly', "
    "or 'Okay' - begin directly with the note content itself."
)

_prompt = ChatPromptTemplate.from_messages([("system", _SYSTEM_PROMPT), ("human", "{raw_text}")])


def _build_llm():
    if os.environ.get("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(model=FORMAT_MODEL, temperature=0)

    # No API key - fall back to a small local model (downloaded once, runs on CPU).
    from langchain_huggingface import ChatHuggingFace, HuggingFacePipeline
    from transformers import pipeline

    pipe = pipeline(
        "text-generation", model=LOCAL_MODEL, max_new_tokens=512, return_full_text=False
    )
    return ChatHuggingFace(llm=HuggingFacePipeline(pipeline=pipe))


def build_chain():
    """Build the formatting chain. Expensive (loads/downloads a model) - callers should
    cache the result themselves (e.g. via st.cache_resource) rather than call this per request.
    """
    return _prompt | _build_llm() | StrOutputParser()
