# ai-lab

A personal collection of AI projects and experiments — agents, RAG, multi-agent systems,
prompt engineering, tools/evals, text-to-speech, voice assistants, and more.

Each subfolder is a **standalone project** with its own dependencies and virtual environment
(no shared root-level environment). [uv](https://docs.astral.sh/uv/) is the standard tool used
across all projects for dependency management and running code.

## Running a project

From inside any project folder:

```bash
uv run <entrypoint>.py
```

or, for a Streamlit app:

```bash
uv run streamlit run app.py
```

`uv` automatically creates the project's `.venv` and installs dependencies from `pyproject.toml`
on first run — no manual `pip install` needed.

See each project's own `README.md` for what it does, prerequisites, and exact run instructions.

## Projects

- [clone-voice](clone-voice/README.md) — voice cloning / text-to-speech using Coqui TTS (xtts_v2)
- [voice-notes](voice-notes/README.md) — record a voice note, transcribe it, and clean it up into
  a formatted note using a LangChain agent (OpenAI, or a local model if no API key is set)
- [jev-dino](jev-dino/README.md) — exploratory script: have TypeSafe AI's Jev model play the
  Chrome dino-runner game, run via OpenRouter
- [documentation-helper](documentation-helper/README.md) — RAG over a documentation site: crawl
  with Tavily, embed with OpenAI, store in Pinecone, and answer questions with cited sources
