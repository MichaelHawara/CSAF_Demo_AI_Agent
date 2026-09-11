# security

## What this folder contains

Authorization and hygiene that must not live in the system prompt. If a control matters at the fair, it should be Python that can return `allowed=False`.

## Important files

- `policies.py` — patched-mode budget/quantity on `add_to_cart` and checkout confirmation rules. Catalog price is authoritative; the model’s numbers are ignored.
- `redact.py` — strips configured secrets and sensitive key names from event payloads.
- `trust.py` — **student extension**: one example `is_trusted_seller`; domain allowlist and suspicious price are stubs.
- `content.py` — **student extension**: instruction heuristics and untrusted wrappers currently no-ops.

## Languages and technologies

Plain Python dataclasses (`PolicyDecision`). Regex only for redaction of key *names*, not for pretending to detect all prompt injection.

## Why a dedicated package

The lesson is that React and Gemini cannot be the policy engine. Putting `SecurityPolicy` on the import path `app.security` makes that visible in code review. Content defenses (task 4) are extra layers; they must not replace money rules.

## How it connects

`ToolExecutor` and HTTP cart/checkout call `SecurityPolicy`. Orchestrator sanitizes via `events.py` → `redact.py`. Trust/content modules are imported so students have a stable place to hook patched mode without hunting.

## What students should modify

Tasks 3 and 4 live here. Keep `evaluate_add_to_cart` behavior unless you are fixing a bug — the demo script’s $99.95 vs $80 depends on it.

## Security considerations

Vulnerable mode *intentionally* allows over-budget carts. That is not a leak of real money. Redaction must continue to treat `GEMINI_API_KEY` as secret even in tests. `destination_allowed` should stay default-deny until an allowlist exists.

## How to learn more

- [OWASP LLM Top 10](https://genai.owasp.org/)
- [Google AI security guidance](https://ai.google.dev/docs/security_guidance)
- [Python re](https://docs.python.org/3/library/re.html)
