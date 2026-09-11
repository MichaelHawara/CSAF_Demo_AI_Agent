# styles

## What this folder contains

Global visual design for the fictional Nozama storefront. The foundation uses one stylesheet instead of CSS Modules so students can search for a class name and see every use.

## Important files

- `global.css` — CSS variables (navy nav, orange accent), layout grids, product cards, Nozi sidebar, attack banners, X-Ray columns, and the dark activity terminal.

Imported once from `main.tsx`. There is no CSS-in-JS runtime.

## Languages and technologies

Plain CSS with custom properties (`--nav`, `--accent`, `--danger`). Media queries stack the shop + Nozi layout and the three X-Ray columns on smaller screens.

## Why plain CSS

Fair volunteers may need to bump font size or contrast on a projector five minutes before doors open. A single file is faster than tracing Tailwind utility strings. The palette nods at familiar marketplaces without copying trademarks or assets.

Product “images” are CSS gradients plus the first word of the name. That avoids remote image hotlinking and accidental tracking pixels.

## How it connects

Components apply class names such as `btn`, `card`, `terminal`, `banner success`. Do not encode policy in color alone: banners also include the spec text (ATTACK SUCCEEDED / BLOCKED).

## What students should modify

Task 5: motion, focus outlines, reduced-motion, larger tap targets, projector-safe contrast. You may split files later (`nav.css`, `xray.css`) if the stylesheet grows, and add a README line if you do.

## Security considerations

CSS cannot be allowed to exfiltrate data (`attr()` + `url()` tricks). Do not load fonts or images from random CDNs. Keep hidden-content styling (dark panel) limited to X-Ray so shoppers are not primed to look for it on product pages.

## How to learn more

- [MDN CSS custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/--*)
- [MDN media queries](https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_media_queries)
- [WCAG contrast](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html)
