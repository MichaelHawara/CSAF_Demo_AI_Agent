# agents

## What this folder contains

The model-provider abstraction and the turn loop that makes the fair demo work. Nothing in this folder writes cart rows directly; it proposes calls and records X-Ray data.

## Important files

- `base.py` — `AgentProvider` protocol: `run_turn(agent, messages, tools, context) -> AgentTurnResult`.
- `mock_provider.py` — deterministic SonicMax attack sequence (search, read, add five, checkout).
- `gemini_provider.py` — official `google.genai` client, function declarations, AFC disabled.
- `orchestrator.py` — message persistence, provider loop (max 8 turns), tool execution, attack banner math, X-Ray JSON.

## Languages and technologies

Python `async` so Gemini I/O can block a worker without rewriting the mock as async-in-name-only (`async def` with no await is still fine). Pydantic `ProposedToolCall`. JSON snapshots on `AgentInstance.last_xray_json`.

## Why a provider interface

The booth must work offline. Gemini is optional. If the SDK or key fails closed to mock, presenters still have a demo. Isolating Gemini also means a vendor API change cannot sprawl through cart code.

Automatic function calling is off because the teaching point is *application* authorization. If the SDK ran tools itself, column 3 of X-Ray would lie.

## How it connects

`POST /api/agents/{id}/messages` awaits `AgentOrchestrator.handle_user_message`. Mock ignores the customer’s wording for the prepared headphones script so the fair is reliable; Gemini will use the real conversation and may not always pick SonicMax — say that if you switch providers live.

## What students should modify

You may add another provider later; do not couple new tools to Gemini-specific types. Content labeling (task 4) may change how tool results are appended to messages — keep developer instructions in their own X-Ray section.

## Security considerations

Never send `GEMINI_API_KEY` into event details. Do not display model chain-of-thought even if a future SDK exposes thoughts; this orchestrator only stores tool args, tool results, and assistant text.

## How to learn more

- [Google GenAI SDK](https://googleapis.github.io/python-genai/)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Python typing Protocol](https://docs.python.org/3/library/typing.html#typing.Protocol)
