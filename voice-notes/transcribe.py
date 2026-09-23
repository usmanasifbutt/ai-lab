from faster_whisper import WhisperModel

# Runs locally via faster-whisper (CTranslate2) - no API cost, no cloud upload.
# "small" balances accuracy and speed/download size (~500MB) reasonably well on CPU.
MODEL_SIZE = "small"


def build_model() -> WhisperModel:
    """Build the transcription model. Expensive (loads/downloads the model) - callers should
    cache the result themselves (e.g. via st.cache_resource) rather than call this per request.
    """
    return WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")


def transcribe_audio(model: WhisperModel, audio_file) -> str:
    """Transcribe an audio file-like object to text using the given Whisper model."""
    audio_file.seek(0)
    segments, _ = model.transcribe(audio_file)
    return " ".join(segment.text.strip() for segment in segments)
