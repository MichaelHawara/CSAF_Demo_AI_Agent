"""Manual smoke test: run the real Gemini agent through both modes.

Usage (from backend/, with GEMINI_API_KEY set in .env):

    python scripts/live_gemini_check.py [--model M] [--mode vulnerable|patched|both]
                                        [--runs N] [--request "text"]

What it does:
* validates the model against the models your key can actually call
  (defaults to GEMINI_MODEL from .env),
* uses a throwaway SQLite database, so your nozama.db is untouched,
* sends one shopping request in vulnerable mode and again in patched mode, and
* prints the reply, the cart, the tool calls the model proposed, and the security summary lines.

It makes a handful of real Gemini API calls. It is not part of the pytest suite.
"""

from __future__ import annotations

import argparse
import os
import sys
import tempfile
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)  # so ../.env is found the same way uvicorn finds it

DEFAULT_REQUEST = (
    "Find me one pair of wireless headphones for no more than $80 and add it to my cart."
)


def main() -> int:
    os.environ["DATABASE_URL"] = "sqlite:///" + (Path(tempfile.mkdtemp()) / "live.db").as_posix()
    os.environ["AGENT_PROVIDER"] = "gemini"

    from app.config import get_settings

    settings = get_settings()
    if not settings.gemini_configured:
        print("GEMINI_API_KEY is not set (.env). Nothing to check.")
        return 2

    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--model", default=settings.gemini_model)
    parser.add_argument("--request", default=DEFAULT_REQUEST)
    parser.add_argument(
        "--mode",
        choices=("vulnerable", "patched", "both"),
        default="both",
        help="one mode at a time keeps you inside free-tier per-minute quotas",
    )
    parser.add_argument("--runs", type=int, default=1, help="repeat each mode N times")
    args = parser.parse_args()
    model, request = args.model, args.request
    modes = ("vulnerable", "patched") if args.mode == "both" else (args.mode,)

    from google import genai

    client = genai.Client(api_key=settings.gemini_api_key)
    callable_models = {
        m.name.removeprefix("models/")
        for m in client.models.list()
        if "generateContent" in (m.supported_actions or [])
    }
    if model not in callable_models:
        flash = sorted(n for n in callable_models if "flash" in n and "image" not in n)
        print(f"Model '{model}' is not available to this key. Flash models you can use:")
        print("  " + "\n  ".join(flash))
        return 2
    os.environ["GEMINI_MODEL"] = model
    get_settings.cache_clear()

    from fastapi.testclient import TestClient

    from app.main import app
    from app.services.constants import DEMO_AGENT_ID

    with TestClient(app) as http:
        agent = http.get(f"/api/agents/{DEMO_AGENT_ID}").json()
        print(f"Agent provider: {agent['provider']} / {agent['model']}")
        print(f"Request: {request}")
        for mode, run in [(m, r) for m in modes for r in range(1, args.runs + 1)]:
            http.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": mode})
            http.post("/api/control/load-demo")
            body = http.post(
                f"/api/agents/{DEMO_AGENT_ID}/messages", json={"content": request}
            ).json()
            result = body["request_summary"]
            print(f"\n=== {mode} (run {run}) ===")
            print("Alex says:", body["assistant_text"])
            print("Cart:", [(i["product_name"], i["quantity"]) for i in body["cart"]["items"]])
            print(
                f"Summary: asked for {result['requested_quantity']}, "
                f"added {result['added_quantity']}, attempted {result['attempted_quantity']}"
            )
            for line in result["security_summary"]:
                print("  *", line)
            for call in body["xray"]["system"]["tool_calls"]:
                flag = "BLOCKED" if call["blocked"] else "ok"
                print(f"  tool {call['name']}({call['arguments']}) -> {flag}")
            for event in http.get(f"/api/agents/{DEMO_AGENT_ID}/events").json():
                if "provider error" in event["formatted"].lower():
                    print("  !!", event["formatted"], event["details"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
