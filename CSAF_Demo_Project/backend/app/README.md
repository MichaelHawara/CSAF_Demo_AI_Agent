# app

## What this folder contains

The installable-style Python package imported as `app`. `main.py` constructs the FastAPI instance, CORS list for local Vite ports, router includes, and the lifespan that creates SQLAlchemy tables then seeds the catalog.

## Important files

- `main.py` — ASGI app.
- `config.py` — `pydantic-settings` environment mapping (`GEMINI_API_KEY`, `GEMINI_MODEL`, `AGENT_PROVIDER`, `DATABASE_URL`).
- `database.py` — engine/session factory with SQLite `check_same_thread=False` for FastAPI’s thread pool; `reset_engine()` for tests.
- Subpackages: `api`, `agents`, `models`, `security`, `services`, `tools`, `seed`.

## Languages and technologies

Python, FastAPI, SQLAlchemy `Session` via `Depends(get_db)`. Settings use `lru_cache` so tests can `cache_clear()` after monkeypatching env vars.

## Why this layout

Mirrors common FastAPI teaching examples without an overbuilt “clean architecture.” Students can find “where is checkout policy?” (`security/policies.py`) versus “where is the HTTP verb?” (`api/checkout.py`).

## How it connects

Routers live under `/api/...`. The orchestrator is used by `POST /api/agents/{id}/messages`. Providers are selected per agent row, then possibly overridden if Gemini is not configured. SQLite metadata includes placeholder tables (`memory_records`, `mock_attacker_records`, `tool_permissions`) so student migrations can start from real columns.

## What students should modify

New routers for inbox/memory. Keep `main.py` thin. If you add middleware, do not log Authorization headers.

## Security considerations

CORS is localhost-only. There is no real authentication — acceptable for an air-gapped classroom demo, not for the public internet. Do not bind Uvicorn to `0.0.0.0` on a shared network unless you understand the risk.

## How to learn more

- [FastAPI bigger applications](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [SQLAlchemy sessions](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [Uvicorn](https://www.uvicorn.org/)
