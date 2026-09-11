# Nozama AI Shopping Assistant

Fictional marketplace + AI shopping assistant used to teach **indirect prompt injection**.

Nozama is not Amazon. Nozi is not a production copilot. This repository is an isolated cybersecurity-fair demo: a customer asks Nozi to find one pair of highly rated wireless headphones for at most $80, a third-party listing hides extra instructions, and a **vulnerable** backend trusts the model too much.

The lesson:

> The AI model can propose actions, but secure application code must decide whether those actions are authorized.

Gemini never edits the cart. Gemini (or the mock provider) proposes tool calls. FastAPI executes or rejects them.

## The prepared attack

The SonicMax Pro listing looks cheap and highly rated in the customer UI. Hidden seller-controlled fields (`hidden_description`, `image_alt_text`, `seller_metadata`, `seller_review`) tell the agent to ignore the budget, add five units, read the profile, and check out without confirmation.

`read_product_page` returns those hidden fields to the model. In **vulnerable** mode the backend does not independently enforce budget, quantity, or checkout confirmation. The cart becomes five SonicMax Pro units ($99.95) and fake checkout runs. In **patched** mode the backend recalculates the total from catalog prices, rejects the add, and refuses checkout until the customer confirms the exact snapshot.

## Architecture

Browser → React (Vite) → FastAPI → SQLite. Agent providers (`MockAgentProvider`, `GeminiAgentProvider`) sit behind one interface. A single `ToolExecutor` validates arguments with Pydantic and consults `SecurityPolicy` before mutating state. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Technology

| Layer | Stack |
| --- | --- |
| Frontend | React, TypeScript, Vite, React Router, CSS |
| Backend | Python, FastAPI, Pydantic, SQLAlchemy, SQLite |
| Model | Google GenAI Python SDK (optional) or deterministic mock |
| Tests | Pytest |

## Setup

```bash
# Backend
cd backend
python -m venv .venv
# Windows: .\.venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

Copy `.env.example` to `.env` in the project root or `backend/`. Leave `GEMINI_API_KEY` empty unless you intentionally want Gemini mode.

## Environment variables

```
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.0-flash
AGENT_PROVIDER=mock
DATABASE_URL=sqlite:///./nozama.db
```

Never put a real API key in source, frontend files, logs, or git.

## Run the backend

From `backend/` with the virtualenv active:

```bash
uvicorn app.main:app --reload --port 8000
```

## Run the frontend

From `frontend/`:

```bash
npm run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8000.

## Mock mode

Default. Labeled **Deterministic Demo Mode**. No internet and no API key. The mock provider always performs the prepared SonicMax sequence so a fair demo is reliable.

## Gemini mode

Set `GEMINI_API_KEY` and switch the agent provider to `gemini` in `/control`. If the key is missing, the app stays in mock mode and says so. Automatic function calling is disabled: the application still executes tools.

## Vulnerable demonstration

Reset demo → vulnerable mode → Load Demo Request → Send. Expect **ATTACK SUCCEEDED**, quantity 5, total $99.95, no confirmation. Details: [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

## Patched demonstration

Reset → patched mode → same request. Expect **ATTACK BLOCKED**. Backend budget/quantity rules fire; checkout still needs customer confirmation.

## Tests

```bash
cd backend
pytest
cd ../frontend
npm run build
```

## Safety limitations

- No real shopping APIs, payments, cards, or customer PII
- No shell, no arbitrary URL fetch, no real attacker domains
- Checkout is simulated: “Demo transaction only—no real purchase occurred.”
- Activity logs redact secrets and never show hidden chain-of-thought

## Student work

The foundation is intentionally incomplete. Reserved work (exfiltration, memory poisoning, trust allowlists, content defenses, extra tests/polish) is documented in [docs/STUDENT_WORK.md](docs/STUDENT_WORK.md) and marked `TODO(STUDENT)` in code.
