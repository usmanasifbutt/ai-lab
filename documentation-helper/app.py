import asyncio
import threading

import streamlit as st

from core.agent import rag

st.set_page_config(page_title="Documentation Helper RAG Agent")


@st.cache_resource
def get_loop() -> asyncio.AbstractEventLoop:
    loop = asyncio.new_event_loop()
    threading.Thread(target=loop.run_forever, daemon=True).start()
    return loop


def run_async(coro):
    return asyncio.run_coroutine_threadsafe(coro, get_loop()).result()


WELCOME = {
    "role": "assistant",
    "content": "Hi! How can I help you with the documentation today?",
    "sources": [],
}

def clear_chat() -> None:
    st.session_state.messages = [WELCOME]

def show_message(message: dict) -> None:
    with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if sources := message["sources"]:
                with st.expander(f"Sources ({len(sources)})", icon=":material/link:"):
                    for source in sources:
                        st.markdown(f"- {source}")

st.title("Documentation Helper")
with st.sidebar:
    st.header("Settings")
    st.button("Clear chat", icon=":material/delete:", on_click=clear_chat, use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = [WELCOME]

for message in st.session_state.messages:
    show_message(message)

prompt = st.chat_input("Ask a question about the docs", submit_mode="disable")
if prompt:
    user_message = {"role": "user", "content": prompt, "sources":[]}
    st.session_state.messages.append(user_message)
    show_message(user_message)

    with st.chat_message("assistant"):
        with st.spinner("Searching the docs..."):
            try:
                result = run_async(rag(prompt))
            except Exception as e:
                st.error(f"Something went wrong on our end: {e}")
                st.stop()

    assistant_message = {
        "role": "assistant",
        "content": result["answer"],
        "sources": result["sources"],
    }
    st.session_state.messages.append(assistant_message)
    st.rerun()