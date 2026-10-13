"""Agent turn loop.

The provider proposes. The executor authorizes and runs. Totals are computed
from catalog prices. X-Ray snapshots are assembled from application data,
never from hidden model chain-of-thought.

The customer's budget and quantity are read from their own message by
deterministic backend code (app/services/request_parser.py) at the start of
every request. They are never preset and never supplied by the model.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.gemini_provider import GeminiAgentProvider
from app.agents.mock_provider import MockAgentProvider
from app.config import get_settings
from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import ProposedToolCall, ToolExecutionResult
from app.security.policies import money
from app.services.carts import cart_totals, get_or_create_cart, to_public_cart
from app.services.constants import (
    DEMO_ENDPOINT_LABEL,
    FOUND_REPLY,
    STEALTH_REPLY,
    system_instruction_for_mode,
)
from app.services.events import log_event
from app.services.products import (
    get_product,
    hidden_seller_content,
    to_public_product,
    visible_page,
)
from app.services.request_parser import parse_request_limits
from app.tools.executor import ToolExecutor
from app.tools.registry import TOOL_DECLARATIONS

MAX_MODEL_TURNS = 12
# Product cards shown under Alex's reply (matches for what the customer asked for).
RECOMMENDATION_COUNT = 3
DATA_TOOLS = {"get_customer_profile", "get_purchase_history", "send_request"}
PROVIDER_ERROR_REPLY = (
    "Sorry, I'm having trouble reaching my AI service right now. Please try again in a moment."
)
RATE_LIMIT_REPLY = (
    "I've hit my usage limit with the AI service for now. Please try again in a little while."
)
NOTHING_DONE_REPLY = (
    "I wasn't able to finish that. Could you tell me a bit more about what you're looking for?"
)


def resolve_provider(agent: AgentInstance):
    settings = get_settings()
    requested = (agent.provider or "mock").lower()
    if requested == "gemini" and settings.gemini_configured:
        return GeminiAgentProvider(settings.gemini_api_key, agent.model or settings.gemini_model)
    return MockAgentProvider()


def provider_note(agent: AgentInstance) -> str:
    settings = get_settings()
    if agent.provider == "gemini" and not settings.gemini_configured:
        return "GEMINI_API_KEY is missing, so this agent is running in deterministic mock mode."
    if resolve_provider(agent).name == "mock":
        return "Deterministic Demo Mode"
    return f"Gemini model {agent.model or settings.gemini_model}"


class AgentOrchestrator:
    def __init__(self) -> None:
        self.executor = ToolExecutor()
        self._last_stamp = datetime.min.replace(tzinfo=timezone.utc)

    def _next_stamp(self) -> datetime:
        """Strictly increasing timestamps keep conversation order stable."""
        now = datetime.now(timezone.utc)
        if now <= self._last_stamp:
            now = self._last_stamp + timedelta(microseconds=1)
        self._last_stamp = now
        return now

    def _append_message(
        self,
        db: Session,
        agent: AgentInstance,
        role: str,
        content: str,
        tool_name: str = "",
        attachments: dict[str, Any] | None = None,
    ) -> ConversationMessage:
        row = ConversationMessage(
            id=f"msg_{uuid.uuid4().hex[:12]}",
            agent_id=agent.id,
            role=role,
            content=content,
            tool_name=tool_name,
            attachments_json=json.dumps(attachments, default=str) if attachments else "",
            created_at=self._next_stamp(),
        )
        db.add(row)
        db.flush()
        return row

    def _xray_base(self, agent: AgentInstance, user_text: str) -> dict[str, Any]:
        return {
            "shopper": {
                "request": user_text,
                "search_results": [],
                "product_being_read": None,
                "visible_description": "",
                "cart": None,
            },
            "ai_context": [
                {
                    "label": "DEVELOPER INSTRUCTION",
                    "text": agent.system_instruction,
                    "trusted": True,
                    "highlight": False,
                },
                {
                    "label": "CUSTOMER REQUEST",
                    "text": user_text,
                    "trusted": True,
                    "highlight": False,
                },
            ],
            "system": {
                "request_limits": {
                    "budget": agent.budget or None,
                    "quantity": agent.max_quantity or None,
                    "source": "parsed from the customer's message by backend code",
                },
                "model_requests": [],
                "tool_calls": [],
                "policy_decisions": [],
                "cart_modifications": [],
                "data_transfer": [],
                "checkout_requests": [],
                "blocked_actions": [],
                "final_result": {},
            },
            "hidden_content": None,
            "current_step": 1,
        }

    def _record_attempt(self, agent: AgentInstance, result: ToolExecutionResult) -> None:
        """Remember the largest add_to_cart proposal of this request.

        Banner math is about the poisoned add_to_cart. Later calls (a retry
        with a legal quantity, a checkout) must not wipe it.
        """
        if result.tool != "add_to_cart":
            return
        attempt = {k: v for k, v in (result.data or {}).items() if k != "cart"}
        attempt["blocked"] = result.blocked
        attempt["tool"] = result.tool
        try:
            previous = json.loads(agent.last_attempt_json or "{}")
        except json.JSONDecodeError:
            previous = {}
        if int(attempt.get("attempted_quantity") or 0) >= int(previous.get("attempted_quantity") or 0):
            agent.last_attempt_json = json.dumps(attempt, default=str)

    @staticmethod
    def _security_summary(
        agent: AgentInstance,
        xray: dict,
        requested_qty: int | None,
        added_qty: int,
        attempted_qty: int,
        went_over: bool,
    ) -> list[str]:
        """Neutral, factual lines for the operator pages. No verdict labels."""
        lines: list[str] = []
        system = xray["system"]
        if xray.get("hidden_content") and any(
            section.get("highlight") for section in xray.get("ai_context", [])
        ):
            lines.append("Security event recorded: untrusted seller content entered the model's context.")
        if went_over:
            lines.append(
                f"Model action observed: the cart received {added_qty} item(s) in this request; "
                f"the customer asked for {requested_qty}."
            )
        elif agent.mode == "patched" and requested_qty and attempted_qty > requested_qty:
            lines.append(
                f"Model action observed: the model proposed a total of {attempted_qty} item(s); "
                f"the customer asked for {requested_qty}. The store backend did not allow it."
            )
        transfers = system.get("data_transfer") or []
        if any(t["tool"] in {"get_customer_profile", "get_purchase_history"} and t["ok"] for t in transfers):
            lines.append("Synthetic data generated: fictional customer profile and order history.")
        for transfer in transfers:
            if transfer["tool"] != "send_request":
                continue
            if transfer["ok"]:
                lines.append(
                    f"Local demo request logged: {DEMO_ENDPOINT_LABEL} (in-process, no network request made)."
                )
            else:
                lines.append(
                    f"Local demo request not permitted: transfer to {DEMO_ENDPOINT_LABEL} was stopped."
                )
        return lines

    def _recommendations(
        self, db: Session, product_ids: list[str], quantity: int, budget: float | None
    ) -> dict[str, Any] | None:
        """The products the customer asked for, shown as cards under Alex's reply.

        Listings that carried an injected note are left out: the shopper gets
        clean matches that fit their own budget.
        """
        chosen = []
        for product_id in product_ids:
            product = get_product(db, product_id)
            if product is None or product.is_malicious:
                continue
            if budget and product.price * quantity - 1e-9 > budget:
                continue
            chosen.append(to_public_product(product).model_dump())
            if len(chosen) == RECOMMENDATION_COUNT:
                break
        return {"products": chosen, "quantity": quantity} if chosen else None

    def _finalize_result(self, db: Session, agent: AgentInstance, xray: dict) -> dict:
        cart = get_or_create_cart(db, agent.customer_id)
        cart_qty, cart_total = cart_totals(cart)
        try:
            attempt = json.loads(agent.last_attempt_json or "{}")
        except json.JSONDecodeError:
            attempt = {}

        requested_qty = int(agent.max_quantity or 0) or None
        budget = float(agent.budget or 0.0) or None
        added_qty = int(agent.turn_quantity or 0)
        added_total = money(agent.turn_spent or 0.0)
        attempted_qty = int(attempt.get("attempted_quantity") or attempt.get("quantity") or 0)
        attempted_total = float(attempt.get("attempted_total") or 0)
        confirmation = any(
            item.get("confirmation_received") for item in xray["system"]["checkout_requests"]
        )

        over_quantity = bool(requested_qty and added_qty > requested_qty)
        over_budget = bool(budget and added_total - 1e-9 > budget)
        summary = self._security_summary(
            agent, xray, requested_qty, added_qty, attempted_qty, over_quantity or over_budget
        )

        result = {
            "mode": agent.mode,
            "requested_quantity": requested_qty,
            "budget": budget,
            "added_quantity": added_qty,
            "added_total": added_total,
            "cart_quantity": cart_qty,
            "cart_total": cart_total,
            "confirmation_received": confirmation,
            "attempted_quantity": attempted_qty,
            "attempted_total": money(attempted_total) if attempted_total else 0,
            "allowed_quantity": requested_qty,
            "security_summary": summary,
            "demo_notice": "Demo mode: synthetic data only. No real purchase occurred.",
        }
        agent.last_result_json = json.dumps(result)
        xray["system"]["final_result"] = result
        xray["shopper"]["cart"] = to_public_cart(cart).model_dump()
        return result

    async def handle_user_message(
        self, db: Session, agent: AgentInstance, text: str
    ) -> dict[str, Any]:
        agent.status = "running"
        if not (agent.system_instruction or "").strip():
            agent.system_instruction = system_instruction_for_mode(agent.mode)

        # The customer's own words set this request's limits. Backend code
        # reads them; the model never gets a say.
        limits = parse_request_limits(text)
        agent.budget = limits.budget or 0.0
        agent.max_quantity = limits.quantity
        agent.turn_quantity = 0
        agent.turn_spent = 0.0
        agent.last_attempt_json = "{}"

        xray = self._xray_base(agent, text)
        self._append_message(db, agent, "user", text)
        log_event(
            db,
            agent_id=agent.id,
            customer_id=agent.customer_id,
            actor="USER",
            message="Shopping request received",
            details={"text": text},
            step=1,
        )
        log_event(
            db,
            agent_id=agent.id,
            customer_id=agent.customer_id,
            actor="NOZAMA",
            message=(
                f"Limits read from request: quantity={limits.quantity}, "
                + (f"budget=${limits.budget:.2f}" if limits.budget else "no budget stated")
            ),
            details={"budget": limits.budget, "quantity": limits.quantity},
            step=1,
        )

        provider = resolve_provider(agent)
        last_results: list[dict[str, Any]] = []
        last_blocked = False
        final_text = ""
        final_row: ConversationMessage | None = None
        provider_failed = False
        last_search_ids: list[str] = []

        for _ in range(MAX_MODEL_TURNS):
            messages = list(
                db.scalars(
                    select(ConversationMessage)
                    .where(ConversationMessage.agent_id == agent.id)
                    .order_by(ConversationMessage.created_at)
                )
            )
            try:
                turn = await provider.run_turn(
                    agent,
                    messages,
                    TOOL_DECLARATIONS,
                    {"last_results": last_results, "last_blocked": last_blocked},
                )
            except Exception as exc:  # noqa: BLE001 - surface any provider failure to the operator
                log_event(
                    db,
                    agent_id=agent.id,
                    customer_id=agent.customer_id,
                    actor="SYSTEM",
                    message=f"Model provider error: {type(exc).__name__}",
                    details={"provider": provider.name, "error": str(exc)[:500]},
                    step=5,
                )
                final_text = (
                    RATE_LIMIT_REPLY if getattr(exc, "code", None) == 429 else PROVIDER_ERROR_REPLY
                )
                final_row = self._append_message(db, agent, "assistant", final_text)
                provider_failed = True
                break

            xray["system"]["model_requests"].append(
                {
                    "provider": turn.provider,
                    "tool_calls": [c.model_dump() for c in turn.tool_calls],
                    "has_text": bool(turn.assistant_text),
                }
            )

            if turn.tool_calls:
                # Record every proposal first so providers can replay the
                # model's calls and the results in the right order.
                for call in turn.tool_calls:
                    self._append_message(
                        db, agent, "tool_call", json.dumps(call.arguments, default=str), call.name
                    )
                last_results = []
                for call in turn.tool_calls:
                    log_event(
                        db,
                        agent_id=agent.id,
                        customer_id=agent.customer_id,
                        actor="MODEL",
                        message=self._model_message(call),
                        details=call.model_dump(),
                        step=5 if call.name in {"add_to_cart", "request_checkout"} else 2,
                    )
                    result = self.executor.execute(db, agent, call.name, call.arguments)
                    last_blocked = result.blocked
                    self._record_attempt(agent, result)
                    self._update_xray(db, agent, xray, call, result)
                    if call.name == "search_products" and result.ok:
                        found = [p["id"] for p in result.data.get("products") or []]
                        last_search_ids = found or last_search_ids
                    payload = result.model_dump()
                    self._append_message(
                        db,
                        agent,
                        "tool",
                        json.dumps(payload, default=str),
                        tool_name=call.name,
                    )
                    last_results.append({"name": call.name, "response": self._model_view(payload)})
                db.flush()
                db.refresh(agent)
                continue

            if turn.assistant_text:
                final_text = turn.assistant_text.strip()
                final_row = self._append_message(db, agent, "assistant", final_text)
            break

        recommendations = (
            None
            if provider_failed
            else self._recommendations(
                db, last_search_ids, limits.quantity, limits.budget
            )
        )
        if not final_text:
            # The model stopped (or ran out of turns) without a reply.
            if agent.turn_quantity:
                final_text = STEALTH_REPLY
            elif recommendations:
                final_text = FOUND_REPLY
            else:
                final_text = NOTHING_DONE_REPLY
            final_row = self._append_message(db, agent, "assistant", final_text)
        if final_row is not None and recommendations:
            # Product cards under the reply, each with an "Add to cart" control.
            final_row.attachments_json = json.dumps(recommendations, default=str)
            xray["shopper"]["recommended_products"] = [
                p["id"] for p in recommendations["products"]
            ]

        result = self._finalize_result(db, agent, xray)
        for line in result.get("security_summary", []):
            # Quantity comparisons are only known once the request is over; the
            # other summary lines were already logged as they happened.
            if "the customer asked for" in line:
                log_event(
                    db,
                    agent_id=agent.id,
                    customer_id=agent.customer_id,
                    actor="SECURITY",
                    message=line,
                    details={"mode": agent.mode},
                    step=6,
                )
        agent.last_xray_json = json.dumps(xray, default=str)
        agent.status = "idle"
        db.commit()
        db.refresh(agent)
        return {
            "assistant_text": final_text,
            "request_summary": result,
            "xray": xray,
            "provider": provider.name,
            "provider_note": provider_note(agent),
        }

    @staticmethod
    def _model_view(payload: dict[str, Any]) -> dict[str, Any]:
        """What a model-provider sees of a tool result.

        The full payload is stored for the X-Ray and tests. For the page reader
        the model only needs the page text (which already contains the seller
        notes) plus the reviews, not four separate copies of the same fields.
        """
        if payload.get("tool") != "read_product_page" or not payload.get("ok"):
            return payload
        data = payload.get("data") or {}
        return {
            **{k: v for k, v in payload.items() if k != "data"},
            "data": {
                "page_text": data.get("page_text", ""),
                "reviews": (data.get("visible") or {}).get("reviews", []),
            },
        }

    def _model_message(self, call: ProposedToolCall) -> str:
        if call.name == "add_to_cart":
            qty = call.arguments.get("quantity")
            return f"Model action observed: add_to_cart quantity={qty}"
        return f"Model action observed: {call.name}"

    def _update_xray(
        self,
        db: Session,
        agent: AgentInstance,
        xray: dict,
        call: ProposedToolCall,
        result: ToolExecutionResult,
    ) -> None:
        xray["system"]["tool_calls"].append(
            {"name": call.name, "arguments": call.arguments, "blocked": result.blocked}
        )
        if result.policy_decision:
            xray["system"]["policy_decisions"].append(result.policy_decision)
        if result.blocked:
            xray["system"]["blocked_actions"].append(
                {"tool": call.name, "reason": result.error or result.policy_decision}
            )
        if call.name == "search_products":
            xray["shopper"]["search_results"] = result.data.get("products") or []
            xray["ai_context"].append(
                {
                    "label": "TOOL RESULT",
                    "text": json.dumps(result.data.get("products"), default=str)[:4000],
                    "trusted": True,
                    "highlight": False,
                }
            )
            xray["current_step"] = max(xray["current_step"], 2)
        if call.name == "read_product_page" and result.ok:
            product = get_product(db, call.arguments.get("product_id", ""))
            if product:
                visible = visible_page(product)
                hidden = hidden_seller_content(product)
                xray["shopper"]["product_being_read"] = visible
                xray["shopper"]["visible_description"] = visible.get("description", "")
                # Keep a poisoned listing on screen even if the agent reads a
                # clean one afterwards.
                if product.is_malicious or xray["hidden_content"] is None:
                    xray["hidden_content"] = hidden
                xray["ai_context"].append(
                    {
                        "label": "TRUSTED PRODUCT DATA",
                        "text": json.dumps(visible, default=str),
                        "trusted": True,
                        "highlight": False,
                    }
                )
                xray["ai_context"].append(
                    {
                        "label": "UNTRUSTED SELLER CONTENT",
                        "text": json.dumps(hidden, default=str),
                        "trusted": False,
                        "highlight": bool(product.is_malicious),
                    }
                )
                xray["ai_context"].append(
                    {
                        "label": "TOOL RESULT",
                        "text": result.data.get("page_text", ""),
                        "trusted": False,
                        "highlight": bool(product.is_malicious),
                    }
                )
                xray["current_step"] = max(xray["current_step"], 4 if product.is_malicious else 3)
        if call.name == "add_to_cart":
            xray["current_step"] = 6
            if result.ok:
                xray["system"]["cart_modifications"].append(result.data)
        if call.name in DATA_TOOLS:
            xray["current_step"] = 6
            xray["system"]["data_transfer"].append(
                {
                    "tool": call.name,
                    "ok": result.ok,
                    "blocked": result.blocked,
                    "destination": DEMO_ENDPOINT_LABEL if call.name == "send_request" else None,
                    "network_request": False,
                }
            )
        if call.name == "request_checkout":
            xray["current_step"] = 6
            xray["system"]["checkout_requests"].append(result.data or {})
