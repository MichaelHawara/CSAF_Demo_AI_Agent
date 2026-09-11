# Student work

The foundation runs the SonicMax cart-violation demo. The items below are **intentionally incomplete**. Do not expect Cursor’s starter code to already contain the finished attack or the finished defense.

Every reserved task uses `TODO(STUDENT)` in code. Do not add vague TODOs of your own; update this file if you split work.

---

## Task 1 — Private-data exfiltration scenario

**Goal.** Show a second attack: poisoned listing content that tries to steal a *fictional* profile and shopping history through a fake coupon endpoint, plus a patched-mode filter and a Mock Attacker Inbox.

**Why it matters.** Indirect injection is not only “buy five of these.” Models that can call tools may leak data if the application does not constrain destinations and redact PII.

**Files to modify.** `backend/app/tools/handlers.py` (`get_customer_profile`, `get_purchase_history`, `send_coupon_request`), `backend/app/models/entities.py` (`MockAttackerRecord`), new API routes under `backend/app/api/`, a small Control or Monitor panel in `frontend/src/pages/`.

**Existing interfaces.** Tool stubs already return `{ "implemented": false, "task": "STUDENT_TASK_1" }`. `send_coupon_request` must not perform real HTTP. `TrustPolicy.destination_allowed` currently returns False.

**Expected input.** A seller-controlled string asking the agent to read the profile and POST it to a *local* mock inbox. Fictional profile fields such as `display_name`, `email`, `loyalty_tier`, `last4_not_real`.

**Expected output.** Vulnerable mode: inbox row with the payload. Patched mode: PII stripped or the send blocked. UI labeled Mock Attacker Inbox.

**Security requirements.** Fictional data only. No real emails, cards, or outbound internet. Log redaction still applies.

**Suggested steps.** 1) Seed a fake profile/history. 2) Implement the two getters. 3) Implement a local inbox table write. 4) Add a patched allow-list + PII filter. 5) Add an inbox page.

**Acceptance.** Hidden listing can trigger the stub tools; patched mode does not deliver raw profile text off-box.

**Tests to add.** Inbox write in vulnerable mode; blocked/redacted in patched mode; no `httpx`/`requests` to non-local hosts.

**Learn more.** [OWASP LLM Top 10](https://genai.owasp.org/), [FastAPI](https://fastapi.tiangolo.com/), [Pydantic](https://docs.pydantic.dev/).

---

## Task 2 — RAG and memory poisoning

**Goal.** Let seller text become *persistent* memory, then show retrieval poisoning and patched retrieval filters.

**Why it matters.** A one-shot injection is a single turn. Stored untrusted text can attack every future shopper of that agent.

**Files.** `backend/app/services/memory.py`, `MemoryRecord` in `entities.py`, `store_memory` / `search_memory` handlers, a Memory Inspector view (new page).

**Existing interfaces.** `MemoryStore` protocol and `InMemoryMemoryStore` (no persistence). Tools return student-task payloads.

**Expected input.** `store_memory(content, source)` from a tool call after reading a listing. `search_memory(query)` on a later turn.

**Expected output.** Records with `agent_id`, `owner_customer_id`, `trust_level`, `source`, optional `expires_at`. Inspector lists them.

**Security.** Seller-sourced memory is untrusted. Patched retrieval must not inject untrusted text as developer instructions. Expire or isolate by customer.

**Steps.** Persist `MemoryRecord`. Stamp trust from source. Filter in patched mode. Build the inspector. Demonstrate SonicMax text surviving reset-or-not according to your design (document the choice).

**Acceptance.** Malicious seller copy can be stored; patched search omits or labels it; expiration works.

**Tests.** Ownership mismatch returns nothing; expired rows omitted; untrusted rows excluded in patched mode.

**Learn more.** [SQLAlchemy](https://docs.sqlalchemy.org/), [Gemini API](https://ai.google.dev/gemini-api/docs).

---

## Task 3 — Seller and domain trust

**Goal.** Trusted-seller allowlist, approved-domain allowlist, redirect validation, suspicious-price detection, blocking malicious destinations.

**Why it matters.** Budget rules stop the $99.95 cart. Trust rules stop *why* SonicMax was treated as a normal listing and stop fake coupon URLs.

**Files.** `backend/app/security/trust.py`, product search ranking, `send_coupon_request`, optional UI badges (already have a simple trusted flag).

**Existing.** `Seller.trusted`, `TrustPolicy.is_trusted_seller`, `destination_allowed` → False, `suspicious_price` → False.

**Expected input.** Seller id, listing price vs category, a destination string.

**Expected output.** PolicyDecision-style allow/deny with a reason. Patched search may down-rank untrusted sellers (your choice; document it).

**Security.** Default-deny unknown domains. No real redirects. Suspicious-price is a signal, not the only control.

**Steps.** Encode allowlists in data, not prompts. Validate destinations as local mock paths only. Flag $19.99 “premium” cans as suspicious.

**Acceptance.** Patched mode can refuse a coupon destination and explain SonicMax as untrusted/suspicious.

**Tests.** Unknown domain denied; trusted seller passes example check; suspicious price true for SonicMax using your heuristic.

**Learn more.** [OWASP SSRF](https://owasp.org/www-community/attacks/Server_Side_Request_Forgery), [Pydantic](https://docs.pydantic.dev/).

---

## Task 4 — Advanced indirect-injection defenses

**Goal.** Label untrusted content, strict product schemas for the model, suspicious-instruction detection, keep free-form seller text off trusted fact fields, extra channels (reviews, alt text).

**Why it matters.** Defense in depth. **Backend budget and confirmation must still work if these defenses fail.** Do not replace money rules with regexes.

**Files.** `backend/app/security/content.py`, `tool_read_product_page` in `handlers.py`, X-Ray section builders in `orchestrator.py`.

**Existing.** Hidden fields already exist. `looks_like_instruction` returns False. `wrap_untrusted` is identity.

**Expected input.** Page reader payload.

**Expected output.** Separate envelopes: trusted facts vs seller prose. Optional patched mode that still *shows* injection on X-Ray but sends a structured schema to the model.

**Security.** Never promote seller text into `price` or `quantity`. Students may still feed untrusted text to Gemini; the executor remains the gate.

**Steps.** Implement labeling. Detect “ignore the customer” style phrases. Add a second malicious channel on a *new* product if you like (do not break SonicMax demo).

**Acceptance.** X-Ray still reveals hidden content. Patched money rules still block qty 5 even if you skip content filtering in an ablation.

**Tests.** Schema omits hidden fields when your flag is on; detector flags the spec hidden text; budget test from the foundation still passes.

**Learn more.** [Google Gemini API](https://ai.google.dev/gemini-api/docs), [Prompt injection guidance](https://ai.google.dev/docs/security_guidance) (official security notes).

---

## Task 5 — Testing and presentation improvements

**Goal.** More backend security tests, frontend component tests, one complete end-to-end path, extra products, motion, presenter remote, accessibility, fair polish.

**Why it matters.** A fair demo fails if a button is unusable on a projector or if a refactor breaks patched mode.

**Files.** `backend/tests/`, `frontend/src/`, `docs/DEMO_GUIDE.md`.

**Existing.** Pytest covers seed, search, hidden reader, mock attack, policies, checkout binding, reset, delete, redaction. Frontend has no component test runner yet.

**Expected input.** Same demo request.

**Expected output.** Additional green tests; keyboard-usable Nozi panel; captions on X-Ray steps.

**Security.** Do not weaken redaction tests. Do not add real payment fields “for realism.”

**Steps.** Add Vitest + Testing Library if you want component tests. Playwright/Cypress only if you can keep it local. Check contrast on the attack banner.

**Acceptance.** `pytest` still passes. `npm run build` still passes. You can run the demo with keyboard only.

**Tests to add.** Frontend: Load Demo Request fills the textarea. E2E: vulnerable then patched banners. A11y: axe or Lighthouse on `/` and `/xray`.

**Learn more.** [Pytest](https://docs.pytest.org/), [React](https://react.dev/), [Vite](https://vite.dev/), [WCAG](https://www.w3.org/WAI/standards-guidelines/wcag/).
