# services

## What this folder contains

Browser-side HTTP helpers. There is one module on purpose: `api.ts` is the entire client for the foundation.

## Important files

- `api.ts` — typed `fetch` wrappers for agents, products, cart, checkout, control, and events. Throws `Error` with FastAPI `detail` text so the UI can show policy denials.

## Languages and technologies

TypeScript and the Fetch API. JSON in, JSON out. No Axios, no GraphQL.

## Why Fetch only

Students can read a single `request()` function and see headers, status checks, and body parsing. Adding another client library would hide that. All mutation methods are explicit (`POST`, `PATCH`, `DELETE`).

## How it connects

Vite proxies `/api` to `http://127.0.0.1:8000`. Relative URLs keep the frontend origin-agnostic in dev. `demoContext.tsx` is the main caller; pages may call `api` directly for one-off actions such as removing a cart line.

Reserved student endpoints (profile, history, attacker inbox, memory) are listed by `GET /api/control/status` as `reserved_endpoints`. Add matching functions here when you implement them — do not pretend they work before the backend does.

## What students should modify

New functions for tasks 1–2. If you add query parameters, use `URLSearchParams` like `searchProducts`. Keep `Content-Type: application/json`.

## Security considerations

Never attach `GEMINI_API_KEY` from the browser. Do not store session cookies for this demo (there is no real auth). When logging errors in the console during development, avoid printing full checkout snapshots if you later add anything that looks like payment data (you should not).

## How to learn more

- [MDN Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API/Using_Fetch)
- [MDN URLSearchParams](https://developer.mozilla.org/en-US/docs/Web/API/URLSearchParams)
- [TypeScript generics](https://www.typescriptlang.org/docs/handbook/2/generics.html)
