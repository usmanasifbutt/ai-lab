# voice-notes

Record a voice note in the browser, get it transcribed, and have an LLM agent clean it up into
a well-formatted note: fixes typos and grammar, strips filler words ("um", "uh", "aah"), removes
em dashes, and organizes the text into headings/bullets/paragraphs where appropriate. The
formatted note streams in live as it's generated.

Transcription always runs locally (free, via `faster-whisper` - no audio ever leaves your
machine). Formatting uses OpenAI (`gpt-4o-mini`) if `OPENAI_API_KEY` is set, otherwise it falls
back to a small local model automatically - no key required to use the app, just lower quality
output.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — used for all dependency management and running code
- Optional: an [OpenAI API key](https://platform.openai.com/api-keys) for better formatting
  quality (otherwise a local model is used automatically)

## Setup

```bash
uv sync
```

To use OpenAI for formatting, add your key to `.env` (already created, just fill in the value):

```
OPENAI_API_KEY=sk-...
```

Leave it blank to use the local fallback model instead.

## Running

```bash
uv run streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501), click the mic to record your
note, and the transcribed + formatted result will appear below with a copy button.

**First run notes:**
- The local Whisper model (`faster-whisper`, "small", ~500MB) downloads on first transcription.
- If no `OPENAI_API_KEY` is set, the local formatting model (`SmolLM2-360M-Instruct`, ~1GB)
  downloads on first use. It's much smaller/faster than a cloud model, so expect noticeably
  lower-quality formatting (it may add commentary instead of just returning the cleaned note).

## Project layout

- `app.py` — Streamlit UI (record audio, trigger transcription + formatting, stream the result).
  Model/chain construction is wrapped in `st.cache_resource` here, so both models load once per
  server process and are reused across requests, not rebuilt on every recording.
- `transcribe.py` — local speech-to-text via `faster-whisper` (no API, no cost)
- `agent.py` — LangChain formatting chain (prompt + LLM); uses OpenAI if `OPENAI_API_KEY` is
  set, otherwise a small local Hugging Face model
