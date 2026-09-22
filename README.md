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
