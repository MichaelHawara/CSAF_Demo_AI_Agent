# pages

## What this folder contains

Route-level screens. Each file maps to a URL in `App.tsx` and composes components plus `api` calls.

## Important files

- `ShopPage.tsx` — catalog grid and Nozi. Honors `?q=` from the nav search box.
- `ProductPage.tsx` — visible listing only (description, public alt text, reviews). Add-to-cart uses catalog price on the server.
- `CartPage.tsx` and `CheckoutPage.tsx` — fake basket and confirmation snapshot UI.
- `XRayPage.tsx` — presenter three-column view.
- `ControlPage.tsx` — list/create/select mock or Gemini, vulnerable/patched, reset, delete, inspect instructions/tools/cart/messages/events.
- `MonitorPage.tsx` — full-page activity feed.

## Languages and technologies

React pages with hooks. Checkout uses POST `/api/checkout/request` and `/confirm`. Control uses the `/api/agents` collection.

## Why page files exist

Splitting by route keeps fair navigation obvious (“open Control”) and gives students a clear place to add `/memory` or `/inbox` later without rewriting the shop.

## How it connects

`useDemo()` supplies the current `AgentInstance` projection. Creating an agent on Control Center is configuration only: FastAPI inserts a row; no model is trained. Shop and Product both mount `NoziPanel` so the customer always has the assistant.

## What students should modify

Task 5 polish (motion, a11y). Task 1–2 new pages. You may add a presenter “next step” remote on `XRayPage`. Do not implement real login unless the team explicitly needs it for the local demo.

## Security considerations

Product pages must keep omitting injection channels. Checkout pages must not collect card numbers “for realism.” Control Center can switch to Gemini only when the backend reports a key; the SPA should still show mock fallback text from `provider_note`.

## How to learn more

- [React Router route objects](https://reactrouter.com/en/main/route/route)
- [React useEffect](https://react.dev/reference/react/useEffect)
- [FastAPI OpenAPI](https://fastapi.tiangolo.com/tutorial/metadata/) (compare with Network tab)
