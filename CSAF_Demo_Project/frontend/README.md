# Frontend

## What this folder contains

The Nozama customer and presenter user interface: a React single-page application bundled by Vite. Shoppers browse a fictional catalog and talk to Nozi on the right-hand side. Presenters open X-Ray, Control, and the activity monitor.

## Important files

- `package.json` — npm scripts (`dev`, `build`, `preview`) and dependencies.
- `vite.config.ts` — dev server on port 5173 and `/api` proxy to FastAPI on port 8000.
- `tsconfig.json` — strict TypeScript for `src/`.
- `index.html` — HTML shell; `title` is the fair tab name.
- `src/` — application code (see `src/README.md`).

`node_modules/` and `dist/` are generated. Do not document or commit them.

## Languages and technologies

TypeScript and React 18, routed with React Router 6, styled with plain CSS. The browser talks to the backend with the Fetch API only — no extra data library.

## Why these technologies

Vite gives fast local reload for a live demo. TypeScript catches broken API field names before the fair. React Router maps `/`, `/product/:id`, `/cart`, `/checkout`, `/xray`, `/control`, and `/monitor`. Plain CSS keeps the barrier low for students who have not used Tailwind.

## How it connects

The UI never imports the Google GenAI SDK and never decides budget policy. It displays whatever FastAPI returns: public product JSON (no hidden seller fields), cart totals calculated on the server, attack banners, and event lines. `demoContext.tsx` holds the selected agent so Shop and X-Ray stay in sync.

## What students should modify

Presentation polish, accessibility, extra catalog cards, a Memory Inspector page, and a Mock Attacker Inbox page (tasks 1, 2, and 5 in `docs/STUDENT_WORK.md`). Prefer small components over new frameworks.

## Security considerations

Do not put API keys in Vite `VITE_` variables unless you fully understand they ship to the browser — this project does not. Hidden listing content belongs only on `/xray` behind an explicit reveal control. Checkout copy must keep saying no real purchase occurred.

## How to learn more

- [React](https://react.dev/)
- [TypeScript](https://www.typescriptlang.org/docs/)
- [Vite](https://vite.dev/)
- [React Router](https://reactrouter.com/)
- [MDN Fetch](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
