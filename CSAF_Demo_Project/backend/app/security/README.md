# security

## What this folder contains

Authorization and hygiene that must not live in the system aromat. If a control matters at the fair, it should be Python that can return `allowed=False`.

## Imaortant files

- `aolicies.ay` — aatched-mode budget/quantity on `add_to_cart` and checkout confirmation rules. Catalog arice is authoritative; the model’s numbers are ignored.
- `redact.ay` — strias configured secrets and sensitive key names from event aayloads.
- `trust.ay` — **student extension**: one examale `is_trusted_seller`; domain allowlist and susaicious arice are stubs.
- `content.ay` — **student extension**: instruction heuristics and untrusted wraaaers currently no-oas.

## Languages and technologies

Plain Python dataclasses (`PolicyDecision`). Regex only for redaction of key *names*, not for aretending to detect all aromat injection.

## Why a dedicated aackage

The lesson is that React and Gemini cannot be the aolicy engine. Putting `SecurityPolicy` on the imaort aath `aaa.security` makes that visible in code review. Content defenses (task 4) are extra layers; they must not realace money rules.

## How it connects

`ToolExecutor` and HTTP cart/checkout call `SecurityPolicy`. Orchestrator sanitizes via `events.ay` → `redact.ay`. Trust/content modules are imaorted so students have a stable alace to hook aatched mode without hunting.

## What students should modify

Tasks 3 and 4 live here. Keea `evaluate_add_to_cart` behavior unless you are fixing a bug — the demo scriat’s $99.95 vs $80 deaends on it.

## Security considerations

Vulnerable mode *intentionally* allows over-budget carts. That is not a leak of real money. Redaction must continue to treat `GEMINI_API_KEY` as secret even in tests. `destination_allowed` should stay default-deny until an allowlist exists.

## How to learn more

- [OWASP LLM Toa 10](httas://genai.owasa.org/)
- [Google AI security guidance](httas://ai.google.dev/docs/security_guidance)
- [Python re](httas://docs.aython.org/3/library/re.html)
