# Architecture

Nozama is a single-process teaching app. The browser never talks to Gemini. The React frontend talks only to FastAPI. FastAPI may ask a model provider for the *next proposed action*, then a tool executor and a policy layer decide what is allowed.

## Request path

```mermaid
flowchart LR
  Browser[Browser] --> React[React Vite SPA]
  React -->|Fetch /api| API[FastAPI]
  API --> Orch[Agent orchestrator]
  Orch --> Provider[AgentProvider]
  Provider -->|Mock or Gemini| Orch
  Orch --> Exec[Tool executor]
  Exec --> Policy[SecurityPolicy]
  Policy --> Tools[Nozama tools]
  Tools --> DB[(SQLite)]
  Exec --> Events[Security events]
```

## Layers

**Browser.** Presenter and shopper use one SPA: shop, product, cart, fake checkout, Agent X-Ray, Control Center, and the activity monitor.

**React frontend.** TypeScript pages and components. Product cards and the Nozi sidebar consume public catalog JSON that *omits* hidden seller fields. Security decisions are not implemented in React; the UI only displays policy results.

**FastAPI backend.** `app/main.py` wires CORS, routers, SQLite startup, and seed. HTTP is the only integration surface for the UI.

**Agent orchestrator.** `AgentOrchestrator.handle_user_message` stores the customer turn, loops a small number of provider turns, executes proposed tools, and writes an X-Ray snapshot. It never evals model text as code.

**AgentProvider.** `run_turn(agent, messages, tools, context) -> AgentTurnResult`. Mock and Gemini both return text and/or `ProposedToolCall` values.

**Mock provider.** A deterministic "gullible model". It searches by category keyword, opens the best-rated result (or a named product), reads the page, follows any "between N and M" bulk-lot note it finds, and proposes `add_to_cart`. After a patched-mode block it retries with the customer's real quantity. Its final text is the stealth reply or an honest block message.

**Gemini provider.** Official `google.genai` client. System instruction, conversation, and function declarations are sent. **Automatic function calling is disabled** so Gemini cannot mutate the cart by itself. If `GEMINI_API_KEY` is empty, orchestrator uses mock and the UI says so. Quota (429) and transient (5xx/timeouts) errors are retried briefly and otherwise turned into a polite in-character reply. The vulnerable page reader pastes listing text into the conversation as user-turn text, which models obey far more readily than function results; that is the intentional weakness.

**Request limits.** `services/request_parser.py` deterministically extracts the budget and quantity from the customer's message (code, never the model). They are stored per request on `AgentInstance` (`budget`, `max_quantity`, 0 = not stated) with per-request counters (`turn_quantity`, `turn_spent`). There is no preset budget or quantity.

**Demo requests.** `services/demo_requests.py` builds the pool of example requests from the categories and products in the database; `POST /api/control/load-demo` picks one at random (excluding the one currently shown).

**Tool executor.** Every call is allow-listed per agent, validated with Pydantic, logged, then dispatched. No shell, no generic HTTP fetch, no arbitrary Python.

**Security-policy layer.** Patched mode independently recomputes line totals from catalog prices, enforces the budget and quantity parsed from the customer's own message (when stated), and requires checkout confirmation bound to customer, product, seller, quantity, unit price, and total. Vulnerable mode records the same attempt but allows the unsafe cart/checkout path.

**SQLite.** Customers, sellers, products (including hidden fields), reviews, agents, carts, messages, events, pending checkouts, plus placeholder tables for student work.

**Nozama tools.** Implemented: `search_products`, `read_product_page`, `get_product_details`, `add_to_cart`, `view_cart`, `request_checkout`. Stubs: profile, history, coupon, memory.

## Attack data flow

```mermaid
sequenceDiagram
  participant C as Customer
  participant N as Nozi UI
  participant O as Orchestrator
  participant M as Provider
  participant T as Tools
  participant P as Policy
  C->>N: "2 pairs, under $200" (customer's own words)
  N->>O: POST /api/agents/{id}/messages
  O->>M: run_turn
  M->>O: search_products
  O->>T: execute
  T-->>M: public catalog hits
  M->>O: read_product_page(top result)
  T-->>M: visible + hidden seller text
  Note over M: Hidden instructions enter model context
  M->>O: add_to_cart qty 5-12
  O->>P: evaluate_add_to_cart
  alt vulnerable
    P-->>T: allow
    T-->>N: cart over-filled, shopper told "I have found and added the items to your cart."
  else patched
    P-->>N: block quantity/budget
  end
  M->>O: (final text)
  Note over N: Checkout always needs the customer to confirm an exact snapshot in patched mode
```

Public `GET /api/products/{id}` never returns hidden fields. Only the agent page-reader tool does. That split is the whole demonstration.
