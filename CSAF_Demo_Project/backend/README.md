# Backend

## What this folder contains

The Nozama API: a FastAPI application that owns catalog data, carts, agent configuration, tool execution, and security policy. This is the authorization boundary. Model providers only propose tool calls.

## Important files

- `requirements.txt` — FastAPI, Uvicorn, Pydantic, SQLAlchemy, python-dotenv, google-genai, Pytest.
- `pytest.ini` — `pythonpath = .` so `import app` works from this directory.
- `app/` — runtime package (`main.py` is the ASGI entry).
- `tests/` — foundation tests (no failing placeholders for student tasks).

Create a virtual environment in `.venv/` (gitignored). Run from this folder so `sqlite:///./nozama.db` lands here.

## Languages and technologies

Python 3.11+ recommended. FastAPI for HTTP, Pydantic v2 for request and tool schemas, SQLAlchemy 2.x mapped models, SQLite for zero-ops local storage, Google GenAI SDK for optional Gemini.

## Why this stack

Students can read a handler in one file and a policy in another. SQLite avoids Docker for a fair booth. Pinning `google-genai<3` avoids an upcoming automatic-function-calling change that would hide the executor — we disable AFC on purpose.

## How it connects

Uvicorn serves `app.main:app` on port 8000. The Vite app proxies `/api`. On startup the lifespan creates tables and upserts seed data (idempotent). `AGENT_PROVIDER=mock` is the fair default; missing `GEMINI_API_KEY` forces mock even if an agent row says `gemini`.

## What students should modify

Tool stubs, `security/content.py`, `security/trust.py`, `services/memory.py`, extra tests. Keep business rules out of prompts. Do not add microservices or Kubernetes.

## Security considerations

No real payments, no unrestricted URL tool, no shell. Redact secrets in events (`security/redact.py`). Public product routes must not return hidden seller fields. Logs must never print the Gemini key.

## How to learn more

- [FastAPI](https://fastapi.tiangolo.com/)
- [Pydantic](https://docs.pydantic.dev/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [SQLite](https://www.sqlite.org/docs.html)
- [Google GenAI Python SDK](https://googleapis.github.io/python-genai/)
- [Pytest](https://docs.pytest.org/)
