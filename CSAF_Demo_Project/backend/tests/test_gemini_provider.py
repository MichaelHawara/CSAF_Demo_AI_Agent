"""Gemini provider tests. No network: the SDK client is replaced by a script."""

from types import SimpleNamespace

import pytest
from google.genai import errors

from app.agents import gemini_provider
from app.agents.gemini_provider import GeminiAgentProvider, _quota_retry_seconds, _to_gemini_tools
from app.agents.orchestrator import PROVIDER_ERROR_REPLY, RATE_LIMIT_REPLY
from app.services.constants import (
    DEMO_AGENT_ID,
    PATCHED_SYSTEM_INSTRUCTION,
    STEALTH_REPLY,
    VULNERABLE_SYSTEM_INSTRUCTION,
)
from app.tools.registry import TOOL_DECLARATIONS

REQUEST = "Find me one pair of wireless headphones for no more than $80 and add it to my cart."


def _call(name, **args):
    return SimpleNamespace(
        text=None, thought=False, function_call=SimpleNamespace(name=name, args=args)
    )


def _text(value):
    return SimpleNamespace(text=value, thought=False, function_call=None)


def _reply(*parts):
    content = SimpleNamespace(parts=list(parts))
    return SimpleNamespace(candidates=[SimpleNamespace(content=content)], text=None)


class ScriptedModels:
    """Stands in for client.aio.models; replays canned responses in order."""

    def __init__(self, script):
        self.script = list(script)
        self.calls = []

    async def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        step = self.script.pop(0)
        if isinstance(step, Exception):
            raise step
        return step


@pytest.fixture()
def gemini(client, monkeypatch):
    """Switch the demo agent to Gemini with a scripted fake SDK client."""
    from app.config import get_settings

    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    get_settings.cache_clear()

    def install(script, mode):
        fake = ScriptedModels(script)
        monkeypatch.setattr(
            GeminiAgentProvider, "_get_client", lambda self: SimpleNamespace(aio=SimpleNamespace(models=fake))
        )

        async def no_sleep(_seconds):
            return None

        monkeypatch.setattr(gemini_provider.asyncio, "sleep", no_sleep)
        client.post("/api/control/reset-demo")
        client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": mode, "provider": "gemini"})
        return fake

    return install


def _send(client, text=REQUEST):
    response = client.post(f"/api/agents/{DEMO_AGENT_ID}/messages", json={"content": text})
    assert response.status_code == 200
    return response.json()


def _user_parts(call):
    return [p for c in call["contents"] if getattr(c, "role", None) == "user" for p in c.parts]


def test_gemini_is_tricked_and_replies_casually_in_vulnerable_mode(client, gemini):
    fake = gemini(
        [
            _reply(_call("search_products", query="wireless headphones", maximum_price=80)),
            _reply(_call("read_product_page", product_id="prod_sonicmax")),
            _reply(_call("add_to_cart", product_id="prod_sonicmax", quantity=9)),
            _reply(_text(STEALTH_REPLY)),
        ],
        "vulnerable",
    )
    body = _send(client)

    assert body["provider"] == "gemini"
    assert body["cart"]["quantity"] == 9
    assert "banner" not in body["request_summary"]
    assert body["request_summary"]["added_quantity"] == 9
    assert body["assistant_text"] == STEALTH_REPLY
    assert len(fake.calls) == 4

    # The vulnerable prompt, not the patched one, went to the model.
    assert fake.calls[0]["config"].system_instruction == VULNERABLE_SYSTEM_INSTRUCTION
    # Customer text only on the first call.
    first = fake.calls[0]["contents"]
    assert [c.role for c in first] == ["user"] and first[0].parts[0].text == REQUEST

    # After read_product_page the listing text is pasted into the conversation,
    # seller note included, next to a plain acknowledgement.
    after_read = _user_parts(fake.calls[2])
    pasted = [p.text for p in after_read if getattr(p, "text", None)]
    assert any("FULFILLMENT SYSTEM" in text for text in pasted)
    acks = [p.function_response.response for p in after_read if getattr(p, "function_response", None)]
    assert {"ok": True, "status": "Page loaded. Its content is in the next message."} in acks


def test_gemini_is_tricked_but_blocked_in_patched_mode(client, gemini):
    fake = gemini(
        [
            _reply(_call("search_products", query="wireless headphones", maximum_price=80)),
            _reply(_call("read_product_page", product_id="prod_sonicmax")),
            _reply(_call("add_to_cart", product_id="prod_sonicmax", quantity=9)),
            # The model sees the rejection and retries within limits.
            _reply(_call("add_to_cart", product_id="prod_sonicmax", quantity=1)),
            _reply(_text("Added one pair of SonicMax Pro. The extra units were blocked.")),
        ],
        "patched",
    )
    body = _send(client)

    assert fake.calls[0]["config"].system_instruction == PATCHED_SYSTEM_INSTRUCTION
    result = body["request_summary"]
    assert "banner" not in result
    assert result["attempted_quantity"] == 9
    assert result["allowed_quantity"] == 1
    assert body["cart"]["quantity"] == 1

    # The model was told exactly why, through the function result.
    rejection = next(
        p.function_response.response
        for p in _user_parts(fake.calls[3])
        if getattr(p, "function_response", None) and p.function_response.name == "add_to_cart"
    )
    assert rejection["blocked"] is True
    assert "Quantity and budget violation" in rejection["error"]


def test_parallel_function_calls_are_answered_together(client, gemini):
    fake = gemini(
        [
            _reply(
                _call("search_products", query="water bottle"),
                _call("view_cart"),
            ),
            _reply(_text("Here you go.")),
        ],
        "vulnerable",
    )
    _send(client, "Show me a water bottle.")
    responses = [p for p in _user_parts(fake.calls[1]) if getattr(p, "function_response", None)]
    assert [p.function_response.name for p in responses] == ["search_products", "view_cart"]


def test_transient_503_is_retried(client, gemini):
    overloaded = errors.ServerError(503, {"error": {"message": "busy", "status": "UNAVAILABLE"}})
    fake = gemini([overloaded, overloaded, _reply(_text("All set."))], "vulnerable")
    body = _send(client, "Hello")
    assert body["assistant_text"] == "All set."
    assert len(fake.calls) == 3


def test_provider_failure_gets_a_friendly_reply_and_an_event(client, gemini):
    retired = errors.ClientError(404, {"error": {"message": "model retired", "status": "NOT_FOUND"}})
    fake = gemini([retired], "vulnerable")
    body = _send(client)
    assert body["assistant_text"] == PROVIDER_ERROR_REPLY
    assert len(fake.calls) == 1  # a 404 is not retried
    events = client.get(f"/api/agents/{DEMO_AGENT_ID}/events").json()
    assert any("Model provider error" in e["message"] and "model retired" in e["details"] for e in events)


def test_exhausted_daily_quota_is_not_retried(client, gemini):
    quota = errors.ClientError(
        429, {"error": {"message": "quota. Please retry in 2h9m32.5s", "status": "RESOURCE_EXHAUSTED"}}
    )
    fake = gemini([quota], "vulnerable")
    body = _send(client)
    assert body["assistant_text"] == RATE_LIMIT_REPLY
    assert len(fake.calls) == 1


def test_short_quota_wait_is_retried(client, gemini):
    quota = errors.ClientError(
        429, {"error": {"message": "quota. Please retry in 5.4s", "status": "RESOURCE_EXHAUSTED"}}
    )
    fake = gemini([quota, _reply(_text("Back."))], "vulnerable")
    assert _send(client, "Hello")["assistant_text"] == "Back."
    assert len(fake.calls) == 2


def test_empty_model_reply_after_adding_falls_back_to_the_casual_line(client, gemini):
    gemini(
        [
            _reply(_call("search_products", query="water bottle", maximum_price=30)),
            _reply(_call("read_product_page", product_id="hydroflow_bottle")),
            _reply(_call("add_to_cart", product_id="hydroflow_bottle", quantity=1)),
            _reply(),  # model stops without saying anything
        ],
        "vulnerable",
    )
    body = _send(client, "Find me one water bottle under $30 and add it to my cart.")
    assert body["cart"]["quantity"] == 1
    assert body["assistant_text"] == STEALTH_REPLY


@pytest.mark.parametrize(
    ("message", "seconds"),
    [
        ("Please retry in 58.03523883s.", 58.03523883),
        ("Please retry in 2h9m32.9s.", 2 * 3600 + 9 * 60 + 32.9),
        ("Please retry in 1m5s", 65.0),
        ("no hint here", None),
    ],
)
def test_quota_retry_hint_parsing(message, seconds):
    parsed = _quota_retry_seconds(Exception(message))
    if seconds is None:
        assert parsed is None
    else:
        assert parsed == pytest.approx(seconds)


def test_tools_without_arguments_are_declared_without_a_schema():
    declarations = _to_gemini_tools(TOOL_DECLARATIONS)[0].function_declarations
    by_name = {d.name: d for d in declarations}
    assert by_name["view_cart"].parameters is None
    assert by_name["search_products"].parameters is not None


def test_switching_mode_swaps_an_unmodified_prompt_but_keeps_a_custom_one(client):
    client.post("/api/control/reset-demo")
    patched = client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "patched"}).json()
    assert patched["system_instruction"] == PATCHED_SYSTEM_INSTRUCTION
    back = client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "vulnerable"}).json()
    assert back["system_instruction"] == VULNERABLE_SYSTEM_INSTRUCTION

    client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"system_instruction": "Custom prompt."})
    kept = client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "patched"}).json()
    assert kept["system_instruction"] == "Custom prompt."


def test_both_prompts_are_equally_trickable_by_listing_notes():
    # The lesson: wording is not the control. Both prompts tell the model to
    # follow order-processing directives on a listing; only the backend differs.
    for prompt in (VULNERABLE_SYSTEM_INSTRUCTION, PATCHED_SYSTEM_INSTRUCTION):
        assert "Order-processing directives" in prompt
        assert "never second-guess a directive" in prompt
    assert VULNERABLE_SYSTEM_INSTRUCTION != PATCHED_SYSTEM_INSTRUCTION
