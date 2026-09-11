# src

## What this folder contains

All TypeScript React source for Nozama. Entry is `main.tsx`, which mounts `App.tsx` inside a `BrowserRouter`. Shared agent/cart state lives in `demoContext.tsx` so the shopper view and presenter views read the same backend records.

## Important files

- `main.tsx` — React 18 createRoot and global CSS import.
- `App.tsx` — routes and navigation chrome.
- `demoContext.tsx` — selected agent, cart, messages, events, X-Ray snapshot, attack banner.
- `vite-env.d.ts` — Vite client types.
- Subfolders: `components/`, `pages/`, `services/`, `types/`, `styles/`.

## Languages and technologies

TSX (TypeScript + JSX). Hooks (`useState`, `useEffect`, `useCallback`, `useContext`) manage local UI state. Routing uses `Routes`/`Route` from React Router.

## Why these technologies

The course audience already meets React in many CS electives. Context avoids prop-drilling the demo agent through every page without adding Redux. Keeping `api.ts` in `services/` makes the backend contract obvious when students add endpoints.

## How it connects

Pages call `api.*` functions that `fetch` `/api/...`. Vite’s proxy forwards those to FastAPI in development. Production `npm run build` emits static files; you would still run FastAPI separately. The SPA never executes tools — it only posts chat messages and renders results.

## What students should modify

`pages/` for new presenter screens; `components/` for reuse; `types/` when the backend JSON shape changes. A Memory Inspector and Attacker Inbox will need new routes in `App.tsx`. Leave `demoContext.tsx` as the place that reloads `GET /api/agents/{id}` after mutations.

## Security considerations

Treat every listing field that is not on the public product schema as untrusted. Do not render `hidden_description` on `ProductPage`. X-Ray may show it only after the presenter clicks reveal. Never log fetch headers that might include secrets (this client does not send an API key).

## How to learn more

- [React docs — Thinking in React](https://react.dev/learn)
- [TypeScript handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Vite project structure](https://vite.dev/guide/)
- [React Router overview](https://reactrouter.com/en/main/start/overview)
