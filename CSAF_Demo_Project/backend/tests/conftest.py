"""Shared pytest fixtures.

Each test gets a throwaway SQLite file so seed and cart mutations cannot
leak between cases.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_path = tmp_path / "nozama-test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("AGENT_PROVIDER", "mock")
    monkeypatch.setenv("GEMINI_MODEL", "gemini-2.0-flash")

    from app.config import get_settings
    from app.database import Base, get_engine, reset_engine

    get_settings.cache_clear()
    reset_engine()

    from app.main import app
    from app.seed import seed_database
    from app.database import get_session_factory

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    session = get_session_factory()()
    try:
        seed_database(session)
    finally:
        session.close()

    with TestClient(app) as test_client:
        yield test_client

    reset_engine()
    get_settings.cache_clear()
    if os.path.exists(db_path):
        os.remove(db_path)
