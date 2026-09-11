"""Model-provider abstraction.

Gemini (or any other vendor) may only propose text and tool calls. The
orchestrator plus ToolExecutor decide what actually happens.
"""

from __future__ import annotations

from typing import Any, Protocol

from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import AgentTurnResult


class AgentProvider(Protocol):
    name: str

    async def run_turn(
        self,
        agent: AgentInstance,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> AgentTurnResult: ...
