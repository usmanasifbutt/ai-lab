import re
import tempfile
import warnings
from pathlib import Path

# Coqui TTS/transformers internals emit noisy deprecation warnings we can't fix from here
warnings.filterwarnings("ignore", category=FutureWarning)

import streamlit as st
from TTS.api import TTS

from languages import LANGUAGES
from model import load_model as _load_model
from utils import to_wav

VOICES_DIR = Path(__file__).parent / "voices"


@st.cache_resource(show_spinner="Loading voice cloning model (first run only)...")
def load_model() -> TTS:
    return _load_model()


def save_upload(uploaded_file) -> Path:
    dest = Path(tempfile.mkdtemp()) / uploaded_file.name
    dest.write_bytes(uploaded_file.getvalue())
    return dest


def humanize_voice_name(path: Path) -> str:
    # Voice files are prefixed "1-", "2-", ... to control display order.
    name = re.sub(r"^\d+[-_]", "", path.stem)
    return name.replace("-", " ").replace("_", " ").title()


st.set_page_config(page_title="Voice Cloner", page_icon="🗣️")
st.title("🗣️ Voice Cloner")
st.caption("Type some text, provide a reference voice, and generate cloned speech.")

model = load_model()

text = st.text_area("Text to speak", placeholder="Type what you want the cloned voice to say...")
language = st.selectbox(
    "Language",
    model.languages,
    format_func=lambda code: LANGUAGES.get(code, code),
)

st.subheader("Reference voice")
source = st.radio("Voice source", ["Voices", "Upload a voice"], horizontal=True)

speaker_wav_path: Path | None = None
if source == "Voices":
    voice_files = sorted(VOICES_DIR.glob("*"))
    chosen = st.selectbox("Voices", voice_files, format_func=humanize_voice_name)
    speaker_wav_path = to_wav(chosen)
else:
    uploaded_file = st.file_uploader(
        "Upload a voice sample (WAV or MP3)",
        type=["wav", "mp3"],
        help="For best results, use a clean sample 10-15 seconds long.",
    )
    if uploaded_file is not None:
        speaker_wav_path = to_wav(save_upload(uploaded_file))
        st.audio(str(speaker_wav_path))

if st.button("Clone voice", type="primary", disabled=not (text and speaker_wav_path)):
    with st.spinner("Generating voice..."):
        output_path = Path(tempfile.mkdtemp()) / "cloned-voice.wav"
        model.tts_to_file(
            text=text,
            speaker_wav=str(speaker_wav_path),
            language=language,
            file_path=str(output_path),
        )
    st.success("Done!")
    st.audio(str(output_path))
    st.download_button(
        "Download",
        data=output_path.read_bytes(),
        file_name="cloned-voice.wav",
        mime="audio/wav",
    )
