# api

## What this folder contains

HTTP routers. Each module is a FastAPI `APIRouter` with prefix `/api/...`. This is a translation layer: parse JSON, load SQLAlchemy rows, call services, return dicts. Policies are not reimplemented here except to invoke `SecurityPolicy` on cart/checkout.

## Important files

- `agents.py` — CRUD, reset, `POST .../messages` (async orchestrator), `GET .../events`.
- `products.py` — list, search, detail. Detail uses `to_public_detail` so hidden fields never serialize.
- `cart.py` — get/add/remove. Add can pass `agent_id` so patched mode applies on the human UI too.
- `checkout.py` — request + confirm with exact-match snapshot.
- `control.py` — `load-demo`, `reset-demo`, `status` (including reserved student endpoint names).

## Languages and technologies

FastAPI path operations, Pydantic bodies (`AgentCreate`, `MessageCreate`, `CheckoutConfirmBody`), `HTTPException` for 404/403/400.

## Why FastAPI routers

OpenAPI at `/docs` helps students see the contract. Splitting files matches the “suggested API” in the project spec without one thousand-line `main.py`.

## How it connects

The SPA’s `api.ts` mirrors these paths. Creating an agent does not call Gemini to train; it inserts `AgentInstance`. Messages are the only path that runs the model loop.

## What students should modify

Add routers for profile, history, attacker inbox, and memory inspector. Document them in `control.py` `reserved_endpoints` until they are real. Do not add an arbitrary fetch-url endpoint.

## Security considerations

Checkout confirm compares every bound field; changing quantity invalidates approval. Product GET must stay a public projection. Agent delete removes agent-owned messages/events, not the shared fictional customer record.

## How to learn more

- [FastAPI path operations](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [FastAPI dependencies](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [Pydantic](https://docs.pydantic.dev/latest/)
- [HTTP status codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
