import logging
import os

import streamlit as st

# Streamlit's file watcher walks every imported module (incl. transformers' many optional
# vision submodules) looking for local sources to hot-reload. Those submodules fail to import
# torchvision, which we don't need - harmless, but noisy. Silence it.
logging.getLogger("streamlit.watcher.local_sources_watcher").setLevel(logging.ERROR)

import agent  # noqa: E402 - loads .env as a side effect, must run before the key check below
import transcribe

st.set_page_config(page_title="Voice Notes", page_icon="📝")
st.title("📝 Voice Notes")
st.caption("Record a voice note and get a cleaned-up, well-formatted version.")

if not os.environ.get("OPENAI_API_KEY"):
    st.info(
        "No OPENAI_API_KEY set - using a small local model for formatting "
        "(slower, lower quality, but free). Add a key to .env to use OpenAI instead."
    )


@st.cache_resource(show_spinner="Loading transcription model (first run only)...")
def get_whisper_model():
    return transcribe.build_model()


@st.cache_resource(show_spinner="Loading formatting model (first run only)...")
def get_chain():
    return agent.build_chain()


audio_file = st.audio_input("Record your note")

if audio_file is not None and audio_file != st.session_state.get("_last_audio"):
    st.session_state["_last_audio"] = audio_file
    st.session_state.pop("pretty_text", None)
    with st.spinner("Transcribing..."):
        st.session_state["raw_text"] = transcribe.transcribe_audio(get_whisper_model(), audio_file)

if "raw_text" in st.session_state:
    with st.expander("Raw transcript"):
        st.write(st.session_state["raw_text"])

    header_col, button_col = st.columns([6, 1])
    header_col.subheader("Formatted note")
    if button_col.button("Reformat", use_container_width=True):
        st.session_state.pop("pretty_text", None)

    if "pretty_text" in st.session_state:
        st.code(st.session_state["pretty_text"], language=None, wrap_lines=True)
    else:
        placeholder = st.empty()
        pretty_text = ""
        for chunk in get_chain().stream({"raw_text": st.session_state["raw_text"]}):
            pretty_text += chunk
            placeholder.code(pretty_text, language=None, wrap_lines=True)
        st.session_state["pretty_text"] = pretty_text
