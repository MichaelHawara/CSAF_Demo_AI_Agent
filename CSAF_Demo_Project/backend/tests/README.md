# tests

## What this folder contains

Pytest coverage for the *finished foundation only*. Student-reserved features are described in `docs/STUDENT_WORK.md` and must not land here as skipped/failing tests.

## Important files

- `conftest.py` — temp SQLite, cleared settings cache, `TestClient` with lifespan seed.
- `test_catalog.py` — seed idempotency, search under $80, public detail hides injection.
- `test_agent_demo.py` — hidden reader, mock vulnerable success, mock patched block.
- `test_policies.py` — independent total vs budget.
- `test_checkout.py` — confirmation required; wrong quantity rejected.
- `test_agent_lifecycle.py` — reset clears cart/conversation; delete removes agent routes.
- `test_redaction.py` — configured secret strings cannot appear in sanitized payloads.

## Languages and technologies

Pytest, FastAPI `TestClient`, monkeypatch for env vars. Async message endpoint is called synchronously through the test client.

## Why this subset

The mock provider makes the attack deterministic, so CI does not need a Gemini key. Tests that required live Google APIs would fail on student laptops and at the fair.

## How it connects

Run `pytest` from `backend/` with requirements installed. `pythonpath = .` is set in `pytest.ini`. Do not point tests at the developer `nozama.db` file.

## What students should modify

Add tests listed under each task in `STUDENT_WORK.md`. Frontend/e2e tests belong in the frontend toolchain you choose (task 5). Keep redaction tests green if you add logging.

## Security considerations

`test_redaction` uses a fake key `secret_test_key_xyz`. Never substitute a real key. Vulnerable-mode tests assert that over-budget carts *are* allowed — that documents the broken mode, it does not authorize shipping it.

## How to learn more

- [Pytest](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Starlette TestClient](https://www.starlette.io/testclient/)
