# types

## What this folder contains

Shared TypeScript shapes that mirror FastAPI/Pydantic JSON. Keeping them in one module prevents Shop, Control, and X-Ray from drifting apart.

## Important files

- `index.ts` — `Product`, `ProductDetail`, `Cart`, `Agent`, `AgentDetail`, `SecurityEvent`, `AttackResult`, `XRayState`, `ControlStatus`, and related nested types.

These are structural types, not runtime validators. The backend remains the authority; the browser trusts HTTPS-local JSON for a classroom demo.

## Languages and technologies

TypeScript `interface` and optional fields (`banner?: string`) because some payloads are empty `{}` before the first agent turn.

## Why a types folder

The fair demo has many similarly named concepts (visible product vs X-Ray shopper product vs tool result). Named types make autocomplete explain which view you are on. Students adding MemoryRecord views should extend this file instead of inlining `any`.

## How it connects

`api.ts` imports these as generic parameters. Components import `Product` for cards. If you change a Pydantic model, update this file in the same pull request or the build may still pass while the UI shows `undefined`.

## What students should modify

Add inbox and memory types for tasks 1–2. When you split trusted vs untrusted product schemas (task 4), add a distinct `TrustedProductFacts` type so you cannot accidentally pass hidden fields into `ProductCard`.

## Security considerations

Do not add a type that includes `api_key`. Hidden listing fields should not appear on `Product` / `ProductDetail` — they belong on `XRayState.hidden_content` only.

## How to learn more

- [TypeScript object types](https://www.typescriptlang.org/docs/handbook/2/objects.html)
- [TypeScript narrowing](https://www.typescriptlang.org/docs/handbook/2/narrowing.html)
- [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/) (backend counterparts)
