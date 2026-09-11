# models

## What this folder contains

Persistence entities and API/tool schemas. SQLAlchemy classes describe SQLite tables. Pydantic classes describe JSON the executor and HTTP layer accept.

## Important files

- `entities.py` — `Customer`, `Seller`, `Product` (with hidden seller channels), `Review`, `AgentInstance`, `Cart`, `CartItem`, `ConversationMessage`, `SecurityEvent`, `PendingCheckout`, plus placeholders `MemoryRecord`, `MockAttackerRecord`, `ToolPermission`.
- `schemas.py` — public product projections, cart DTOs, agent CRUD, and per-tool argument models (`AddToCartArgs`, student stub args, `AgentTurnResult`).

## Languages and technologies

SQLAlchemy 2 mapped columns, Pydantic v2 `BaseModel`. Hidden fields are real columns so the *same row* can have two projections: public HTTP vs agent page reader.

## Why both ORMs and Pydantic

The database can store injection strings; the public schema must not. Tool args must fail validation rather than calling `add_to_cart(quantity="all of them")`. Mixing the two keeps students from stuffing `dict` everywhere.

## How it connects

`seed/` upserts entity rows. `services/products.py` maps entities → public schemas. `tools/executor.py` validates tool JSON with the Pydantic arg models before handlers run. Placeholder tables exist so student work does not start from a migration-less whiteboard.

## What students should modify

Fill in usage of placeholder models (tasks 1–3). If you add schema fields to products, update the public DTO so you do not accidentally leak `hidden_description` through `model_dump()`.

## Security considerations

`Product.hidden_*` and `seller_review` are untrusted. `PendingCheckout` is a capability: whoever can POST matching fields confirms a *demo* purchase only. `Customer.email` is fictional (`example.invalid`). Do not add real card columns.

## How to learn more

- [SQLAlchemy ORM](https://docs.sqlalchemy.org/en/20/orm/)
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/)
- [SQLite datatypes](https://www.sqlite.org/datatype3.html)
