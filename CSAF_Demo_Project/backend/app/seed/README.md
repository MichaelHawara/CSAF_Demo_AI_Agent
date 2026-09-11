# seed

## What this folder contains

Repeatable demo data. The catalog, fictional customer, and default Nozi instance are upserted by primary key so starting the app twice cannot duplicate SonicMax Pro.

## Important files

- `__init__.py` — `seed_database(session)` used at lifespan and by `/api/control/load-demo`.
- Catalog literals live in `app/services/constants.py` so tests and tools share the same IDs (`prod_sonicmax`, `cust_demo`, `agent_demo`) and the exact hidden instruction paragraph from the assignment.

## Languages and technologies

SQLAlchemy `session.get` + insert/update. No Alembic in the foundation; `create_all` builds empty tables, then seed fills them.

## Why upsert instead of “delete all”

Presenters reset *agent state* (cart, messages) without wiping student-created agents. Product copy stays stable for the script: $19.99 × 5 = $99.95.

Sellers include trusted (Nozama Direct, Tech Harbor, Audio Nest) and untrusted (Value Galaxy, Bargain Bin) so later allowlists have something to hang on.

## How it connects

`main.py` lifespan calls seed after `create_all`. Tests call seed on a temp SQLite file. Hidden fields on SonicMax are stored here but only the page-reader tool should reveal them.

## What students should modify

Add products for task 5. Add fictional profile/history rows for task 1. Keep SonicMax’s hidden text intact unless you are explicitly adding a second channel on another SKU.

## Security considerations

Names and emails are fake. Do not seed real classmate PII. Do not seed live URLs. Malicious instructions are teaching artifacts, not something to paste into a production catalog.

## How to learn more

- [SQLAlchemy ORM inserting](https://docs.sqlalchemy.org/en/20/tutorial/orm_data_manipulation.html)
- [SQLite](https://www.sqlite.org/docs.html)
- [Pytest tmp_path](https://docs.pytest.org/en/stable/how-to/tmp_path.html)
