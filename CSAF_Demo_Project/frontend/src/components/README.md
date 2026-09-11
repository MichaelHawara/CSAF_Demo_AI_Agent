# components

## What this folder contains

Reusable UI pieces shared by multiple routes: the store navigation bar, product cards and gradient “photos,” the Nozi chat sidebar, attack-result banners, the X-Ray three-column board, and the terminal-style event feed.

## Important files

- `NavBar.tsx` — branding, search box, cart count, presenter links.
- `ProductCard.tsx` — listing tile plus `ProductThumb` placeholder art (no third-party image CDN).
- `NoziPanel.tsx` — budget/quantity/confirmation restrictions, Load Demo Request, send, checkout approve/reject.
- `AttackBanner.tsx` — ATTACK SUCCEEDED vs ATTACK BLOCKED copy from the spec.
- `XRayBoard.tsx` — shopper / model-input / system-action columns and step buttons.
- `EventFeed.tsx` — colored monitor lines.

## Languages and technologies

React function components and TypeScript props. Styling uses class names defined in `styles/global.css` rather than CSS Modules so students can grep one stylesheet.

## Why these technologies

Extracting Nozi into a component lets Shop and Product pages share the same assistant without duplicating the demo script. Keeping policy *display* here (not policy *logic*) matches the architecture: React is a projector for FastAPI decisions.

## How it connects

Components receive data from pages via `useDemo()` or props. `NoziPanel` calls `api.loadDemo`, `api.sendMessage`, and checkout helpers. `XRayBoard` only renders `xray` JSON produced by the orchestrator — it does not reconstruct hidden model chain-of-thought.

## What students should modify

Animations, accessibility (labels, focus rings), extra presenter controls, and new widgets for Memory Inspector / Attacker Inbox. Prefer composition over rewriting `NoziPanel` into a mega-component.

## Security considerations

The reveal button on X-Ray is presenter-only by convention (the route is unauthenticated because this is a local demo). Do not move hidden seller strings into `ProductCard`. Event feed must keep showing sanitized `formatted` lines from the server, not raw `localStorage` dumps.

## How to learn more

- [React components](https://react.dev/learn/your-first-component)
- [React accessibility](https://react.dev/reference/react-dom/components#accessibility)
- [TypeScript for React](https://www.typescriptlang.org/docs/handbook/jsx.html)
