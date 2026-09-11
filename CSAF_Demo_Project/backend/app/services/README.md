# services

## What this folder contains

Domain operations used by both HTTP and tools: catalog search, cart math, checkout snapshots, agent lifecycle, event logging, constants/seed copy, and the memory-store stub.

## Important files

- `constants.py` — demo IDs, hidden instruction text from the spec, catalog dicts, default system instruction, allowed tool names.
- `products.py` — public projections and search. `hidden_seller_content()` is for tools/X-Ray, not for `GET /api/products`.
- `carts.py` — line totals from stored unit prices copied from the catalog at add time.
- `checkout.py` — pending snapshot create/match; `complete_demo_checkout` sets a flag only.
- `agents.py` — create/patch/reset/delete. Reset clears messages, events, pending checkouts, and cart lines.
- `events.py` — activity monitor rows with sanitized details.
- `memory.py` — `MemoryStore` protocol + empty in-memory implementation.

## Languages and technologies

SQLAlchemy queries (`select`, `joinedload`) and small pure functions (`money()` lives with policy rounding). JSON blobs on the agent row cache the last X-Ray.

## Why services vs tools

Tools are the *agent-facing* names. Services are usable from pytest and from a human clicking “Add to cart.” Duplicating total math in both places would let the model’s arithmetic disagree with the UI.

## How it connects

Seed uses `constants.PRODUCTS`. Orchestrator uses carts/products/events. Control `load-demo` resets the demo agent through `agents.reset_agent`.

## What students should modify

`memory.py` for task 2. Profile/history data could live as new service modules. Keep `constants.HIDDEN_INSTRUCTIONS` aligned with the spec unless you add a *second* malicious SKU.

## Security considerations

Totals must not take a price argument from the model. Event messages should stay short and free of secrets. Reset is destructive on purpose for the booth.

## How to learn more

- [SQLAlchemy select](https://docs.sqlalchemy.org/en/20/tutorial/data_select.html)
- [Python decimal / rounding](https://docs.python.org/3/library/decimal.html)
- [Pytest fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html) (how tests reuse these functions)
