# clone-voice

A voice cloning app: give it some text and a short reference voice sample, and it generates
speech in that voice using [Coqui TTS](https://github.com/coqui-ai/TTS) (`xtts_v2`, multilingual).
Includes a Streamlit UI for uploading/selecting a reference voice and generating cloned audio.

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — used for all dependency management and running code
- Windows: [Microsoft Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)
  (needed to compile one of `tts`'s dependencies from source)
- No system-wide `ffmpeg` needed — MP3 handling uses the `imageio-ffmpeg` package, which vendors
  its own binary

## Setup

```bash
uv sync
```

This creates `.venv` and installs everything pinned in `pyproject.toml` (including `torch`,
`transformers`, and `tts` pinned to versions known to work together — newer versions break
compatibility with this Coqui TTS release).

## Running

**First time only** — pre-download the model (a few GB) so it's cached locally:

```bash
uv run python model.py
```

Then start the app:

```bash
uv run streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501), type some text, pick or upload a
reference voice, and click **Clone voice**.

## Project layout

- `app.py` — Streamlit UI
- `model.py` — loads the TTS model; run directly (`uv run python model.py`) to pre-download/load
  the model ahead of time, e.g. before deploying, so it doesn't block the app's first request
- `utils.py` — audio helpers (MP3→WAV conversion, trimming to a max duration)
- `languages.py` — language code → human-readable name mapping
- `trim_voices.py` — one-off script to trim all voices in `voices/` to a max duration
- `voices/` — reference voice samples (WAV only). Filenames are prefixed `1-`, `2-`, ... to
  control display order in the UI; the prefix and extension are stripped when shown
