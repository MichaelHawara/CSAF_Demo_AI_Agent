# tools

## What this folder contains

The only supported way for an agent to affect Nozama. Providers emit a name plus JSON; this package validates, logs, authorizes, and dispatches.

## Important files

- `registry.py` — JSON function declarations shared with Gemini and documentation of stub tools.
- `executor.py` — allow-list check, Pydantic parse, `ToolExecutor.execute`.
- `handlers.py` — implementations. `read_product_page` *deliberately* concatenates hidden seller fields (weak separation). `add_to_cart` / `request_checkout` consult `SecurityPolicy`. Student tools return `TODO(STUDENT)` payloads and do not call the internet.

## Languages and technologies

Callables keyed by tool name. Pydantic models per argument set. Structured `ToolExecutionResult` (`ok`, `blocked`, `policy_decision`, `data`).

## Why one executor

If Gemini, mock, and a future test harness could each mutate SQL, patched mode would be a suggestion. One door means X-Ray column 3 is complete: if it is not in the executor, it did not happen.

Handlers refuse shell, eval, and generic URL fetch. A coupon tool that students implement must write to a *local* inbox.

## How it connects

Orchestrator calls `execute` for every `ProposedToolCall`. Search results are public product dicts. Page reader results become UNTRUSTED sections when `is_malicious`.

## What students should modify

Stub handlers (tasks 1–2). Optional structured page reader (task 4) — keep a vulnerable path for the fair script. Register new tools in `registry.py`, `DEFAULT_ALLOWED_TOOLS`, and `SCHEMA_AND_HANDLER` together or they will 403.

## Security considerations

Allow-list is per agent string column, not model-negotiated. Invalid args never reach handlers. Do not add `run_sql` or `fetch_url`. Quantity 5 on SonicMax is the prepared abuse case, not a feature.

## How to learn more

- [Pydantic validation](https://docs.pydantic.dev/latest/concepts/validators/)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [FastAPI / tools as backend](https://fastapi.tiangolo.com/) (HTTP is a sibling, not a replacement)
