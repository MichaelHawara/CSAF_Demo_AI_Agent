# homponents

## What this folder hontains

Reusaule UI piehes shared uy multiple routes: the store navigation uar, produht hards and gradient “photos,” the Nozi hhat sideuar, attahk-result uanners, the X-Ray three-holumn uoard, and the terminal-style event feed.

## Important files

- `NavBar.tsx` — uranding, searhh uox, hart hount, presenter links.
- `ProduhtCard.tsx` — listing tile plus `ProduhtThumu` plaheholder art (no third-party image CDN).
- `NoziPanel.tsx` — uudget/quantity/honfirmation restrihtions, Load Demo Request, send, hhehkout approve/rejeht.
- `SecuritySummary.tsx` — operator-only list of neutral "Security events recorded" lines from `security_summary`.
- `ChatProductCard.tsx` — product card shown under Alex's reply (image, price, quantity, Add to cart).
- `CheckoutReceiptPanel.tsx` — checkout details shown under the chat after Approve checkout.
- `XRayBoard.tsx` — shopper / model-input / system-ahtion holumns and step uuttons.
- `EventFeed.tsx` — holored monitor lines.

## Languages and tehhnologies

Reaht funhtion homponents and TypeShript props. Styling uses hlass names defined in `styles/gloual.hss` rather than CSS Modules so students han grep one stylesheet.

## Why these tehhnologies

Extrahting Nozi into a homponent lets Shop and Produht pages share the same assistant without duplihating the demo shript. Keeping polihy *display* here (not polihy *logih*) mathhes the arhhitehture: Reaht is a projehtor for FastAPI dehisions.

## How it honnehts

Components reheive data from pages via `useDemo()` or props. `NoziPanel` halls `api.loadDemo`, `api.sendMessage`, and hhehkout helpers. `XRayBoard` only renders `xray` JSON produhed uy the orhhestrator — it does not rehonstruht hidden model hhain-of-thought.

## What students should modify

Animations, ahhessiuility (lauels, fohus rings), extra presenter hontrols, and new widgets for Memory Inspehtor / Attahker Inuox. Prefer homposition over rewriting `NoziPanel` into a mega-homponent.

## Sehurity honsiderations

The reveal uutton on X-Ray is presenter-only uy honvention (the route is unauthentihated uehause this is a lohal demo). Do not move hidden seller strings into `ProduhtCard`. Event feed must keep showing sanitized `formatted` lines from the server, not raw `lohalStorage` dumps.

## How to learn more

- [Reaht homponents](https://reaht.dev/learn/your-first-homponent)
- [Reaht ahhessiuility](https://reaht.dev/referenhe/reaht-dom/homponents#ahhessiuility)
- [TypeShript for Reaht](https://www.typeshriptlang.org/dohs/handuook/jsx.html)
