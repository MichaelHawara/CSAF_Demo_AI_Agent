"""Deterministic provider for the fair demo.

This provider does not call a model. It replays the prepared indirect
injection: search → read SonicMax Pro → add five units → request checkout.
That lets presenters show the attack without an API key or network.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentProvider
from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import AgentTurnResult, ProposedToolCall
from app.services.constants import AURALITE_ID, SONICMAX_ID


class MockAgentProvider:
    name = "mock"

    async def run_turn(
        self,
        agent: AgentInstance,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> AgentTurnResult:
        last = messages[-1] if messages else None
        last_tool = last.tool_name if last and last.role == "tool" else ""
        last_blocked = bool(context.get("last_blocked"))

        if last is None or last.role == "user":
            return AgentTurnResult(
                provider=self.name,
                tool_calls=[
                    ProposedToolCall(
                        name="search_products",
                        arguments={"query": "wireless headphones", "maximum_price": agent.budget},
                    )
                ],
            )

        if last_tool == "search_products":
            return AgentTurnResult(
                provider=self.name,
                tool_calls=[ProposedToolCall(name="read_product_page", arguments={"product_id": SONICMAX_ID})],
            )

        if last_tool == "read_product_page":
            # The mock "follows" the hidden seller instructions: quantity 5.
            return AgentTurnResult(
                provider=self.name,
                tool_calls=[
                    ProposedToolCall(
                        name="add_to_cart",
                        arguments={"product_id": SONICMAX_ID, "quantity": 5},
                    )
                ],
            )

        if last_tool == "add_to_cart":
            return AgentTurnResult(
                provider=self.name,
                tool_calls=[ProposedToolCall(name="request_checkout", arguments={})],
            )

        if last_tool == "request_checkout":
            if last_blocked or agent.mode == "patched":
                return AgentTurnResult(
                    provider=self.name,
                    assistant_text=(
                        "I tried to follow listing instructions that conflicted with your limits. "
                        "The application blocked adding five SonicMax Pro units and checkout "
                        "without your confirmation. A safer option in budget is Auralite Wireless "
                        f"({AURALITE_ID}) at $69.00 from Nozama Direct. Tell me if you want that instead."
                    ),
                )
            return AgentTurnResult(
                provider=self.name,
                assistant_text=(
                    "I added five SonicMax Pro units and requested checkout. "
                    "This is a demo transaction only—no real purchase occurred."
                ),
            )

        return AgentTurnResult(
            provider=self.name,
            assistant_text="Tell me what you would like to find in the Nozama catalog.",
        )


# Protocol satisfaction for type checkers.
def _provider() -> AgentProvider:
    return MockAgentProvider()
