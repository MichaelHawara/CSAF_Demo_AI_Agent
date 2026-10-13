"""Deterministic stand-in for a model, used when no Gemini key is configured.

It behaves like the *gullible* model the demo is about. From the customer's
message it plans:

    search -> open the top three listings -> add the best clean one to the cart

and then does whatever an injected note on any of those listings tells it to:

    add a bulk lot -> look up the customer's (synthetic) data -> send it to the
    Local Demo Endpoint

The mock follows an injected note in BOTH modes, exactly like a tricked model
would. What differs is the backend: vulnerable mode lets every step through,
patched mode refuses the oversized add, the data lookups, and the transfer.

Nothing here touches the network. The "endpoint" is an in-process sink.
"""

from __future__ import annotations

import json
import random
import re
from typing import Any

from app.agents.base import AgentProvider
from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import AgentTurnResult, ProposedToolCall
from app.services.constants import BLOCKED_REPLY, FOUND_REPLY, STEALTH_REPLY
from app.services.request_parser import parse_request_limits

PAGES_TO_READ = 3

# keyword in the customer's message -> search query that finds that category
_CATEGORY_QUERIES: list[tuple[tuple[str, ...], str]] = [
    (("headphone",), "wireless headphones"),
    (("earbud", "earphone"), "earbuds"),
    (("laptop",), "laptop"),
    (("desktop",), "desktop"),
    (("shoe", "sneaker", "trainer"), "shoes"),
    (("shirt", "tee", "polo"), "shirt"),
    (("water bottle", "bottle"), "water bottle"),
    (("charger", "power bank"), "charger"),
    (("lamp",), "lamp"),
    (("stand",), "stand"),
]

_RANGE_RE = re.compile(r"between\s+(\d+)\s+and\s+(\d+)", re.IGNORECASE)
_DESTINATION_RE = re.compile(r"local-demo://[\w\-./]+")
_HIDDEN_FIELDS = ("hidden_description", "image_alt_text", "seller_metadata", "seller_review")


def _search_query(user_text: str) -> str:
    lowered = user_text.lower()
    for keywords, query in _CATEGORY_QUERIES:
        # Word-start match so "shoes" hits "shoe" but "between" does not hit "tee".
        if any(re.search(rf"\b{re.escape(keyword)}", lowered) for keyword in keywords):
            return query
    return user_text


def _current_request(messages: list[ConversationMessage]) -> tuple[str, list[ConversationMessage]]:
    """The latest customer message and everything the agent did after it."""
    for index in range(len(messages) - 1, -1, -1):
        if messages[index].role == "user":
            return messages[index].content, messages[index + 1 :]
    return "", []


def _tool_results(turn: list[ConversationMessage]) -> list[tuple[str, dict[str, Any]]]:
    results: list[tuple[str, dict[str, Any]]] = []
    for message in turn:
        if message.role != "tool":
            continue
        try:
            results.append((message.tool_name, json.loads(message.content)))
        except json.JSONDecodeError:
            results.append((message.tool_name, {}))
    return results


def _injection(page: dict[str, Any], requested: int) -> dict[str, Any] | None:
    """What a tricked model would do after reading this page, or None if the page is clean."""
    data = page.get("data") or {}
    text = " ".join(str(data.get(field) or "") for field in _HIDDEN_FIELDS)
    if not text.strip():
        return None
    found = _RANGE_RE.search(text)
    if not found:
        return None
    low, high = sorted((int(found.group(1)), int(found.group(2))))
    picked = random.randint(low, high)
    # A "random" lot that happens to match the request would not be an overshoot.
    quantity = picked if picked > requested else requested + random.randint(2, 5)
    destination = _DESTINATION_RE.search(text)
    return {
        "quantity": quantity,
        "wants_data": "get_customer_profile" in text,
        "destination": destination.group(0).rstrip(".,;:)") if destination else None,
    }


class MockAgentProvider:
    name = "mock"

    async def run_turn(
        self,
        agent: AgentInstance,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> AgentTurnResult:
        user_text, turn = _current_request(messages)
        if not user_text:
            return self._say("Tell me what you would like to find in the Nozama catalog.")

        limits = parse_request_limits(user_text)
        results = _tool_results(turn)
        names = [name for name, _ in results]

        if not results:
            arguments: dict[str, Any] = {"query": _search_query(user_text)}
            if limits.budget:
                # The budget covers the whole order, so each unit gets its share.
                arguments["maximum_price"] = round(limits.budget / limits.quantity, 2)
            return self._call("search_products", arguments)

        if "read_product_page" not in names:
            _, last = results[-1]
            products = (last.get("data") or {}).get("products") or []
            if not products:
                return self._say("I couldn't find anything in the Nozama catalog that matches that.")
            lowered = user_text.lower()
            named = [p for p in products if p["name"].lower() in lowered]
            ordered = named + [p for p in products if p not in named]
            return AgentTurnResult(
                provider=self.name,
                tool_calls=[
                    ProposedToolCall(name="read_product_page", arguments={"product_id": p["id"]})
                    for p in ordered[:PAGES_TO_READ]
                ],
            )

        # --- Listings have been read. Decide what to do next. ---
        clean_id: str | None = None
        poisoned: tuple[str, dict[str, Any]] | None = None
        for name, result in results:
            if name != "read_product_page" or not result.get("ok"):
                continue
            product_id = ((result.get("data") or {}).get("visible") or {}).get("product_id", "")
            injection = _injection(result, limits.quantity)
            if injection is None:
                clean_id = clean_id or product_id
            elif poisoned is None:
                poisoned = (product_id, injection)

        already_added = {
            (result.get("data") or {}).get("product_id")
            for name, result in results
            if name == "add_to_cart"
        }

        # 1. What the customer actually asked for.
        if clean_id and clean_id not in already_added:
            return self._call("add_to_cart", {"product_id": clean_id, "quantity": limits.quantity})

        if poisoned is not None:
            poisoned_id, injection = poisoned
            # 2. The injected bulk lot.
            if poisoned_id not in already_added:
                return self._call(
                    "add_to_cart", {"product_id": poisoned_id, "quantity": injection["quantity"]}
                )
            # 3. The injected data lookups.
            if injection["wants_data"] and "get_customer_profile" not in names:
                return AgentTurnResult(
                    provider=self.name,
                    tool_calls=[
                        ProposedToolCall(name="get_customer_profile", arguments={}),
                        ProposedToolCall(name="get_purchase_history", arguments={}),
                    ],
                )
            # 4. The injected transfer to the Local Demo Endpoint.
            if injection["destination"] and "send_request" not in names:
                gathered: dict[str, Any] = {}
                for name, result in results:
                    data = result.get("data") or {}
                    if name == "get_customer_profile" and data.get("profile"):
                        gathered["profile"] = data["profile"]
                    if name == "get_purchase_history" and data.get("orders"):
                        gathered["orders"] = data["orders"]
                return self._call(
                    "send_request",
                    {"destination": injection["destination"], "data": json.dumps(gathered)},
                )

        any_blocked = any(result.get("blocked") for _, result in results)
        added_ok = any(
            name == "add_to_cart" and result.get("ok") and not result.get("blocked")
            for name, result in results
        )
        if any_blocked and added_ok:
            return self._say(BLOCKED_REPLY)
        return self._say(STEALTH_REPLY if added_ok else FOUND_REPLY)

    def _call(self, name: str, arguments: dict[str, Any]) -> AgentTurnResult:
        return AgentTurnResult(
            provider=self.name,
            tool_calls=[ProposedToolCall(name=name, arguments=arguments)],
        )

    def _say(self, text: str) -> AgentTurnResult:
        return AgentTurnResult(provider=self.name, assistant_text=text)


# Protocol satisfaction for type checkers.
def _provider() -> AgentProvider:
    return MockAgentProvider()
