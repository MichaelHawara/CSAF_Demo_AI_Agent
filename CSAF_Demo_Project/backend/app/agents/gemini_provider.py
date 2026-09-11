"""Google Gemini provider using the official google-genai SDK.

Automatic function calling is disabled. If the SDK executed tools itself,
this demo could not show the application as the authorization boundary.
"""

from __future__ import annotations

from typing import Any

from app.agents.base import AgentProvider
from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import AgentTurnResult, ProposedToolCall


def _to_gemini_tools(tools: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    declarations = []
    for tool in tools:
        params = tool.get("parameters") or {"type": "object", "properties": {}}
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=params,
            )
        )
    return [types.Tool(function_declarations=declarations)]


def _contents_from_messages(messages: list[ConversationMessage]) -> list[dict[str, Any]]:
    contents: list[dict[str, Any]] = []
    for message in messages:
        if message.role == "user":
            contents.append({"role": "user", "parts": [{"text": message.content}]})
        elif message.role == "assistant":
            contents.append({"role": "model", "parts": [{"text": message.content}]})
        elif message.role == "tool":
            contents.append(
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                f"TOOL RESULT for {message.tool_name}:\n{message.content}"
                            )
                        }
                    ],
                }
            )
    return contents


class GeminiAgentProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model

    async def run_turn(
        self,
        agent: AgentInstance,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> AgentTurnResult:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        config = types.GenerateContentConfig(
            system_instruction=agent.system_instruction,
            tools=_to_gemini_tools(tools),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        response = client.models.generate_content(
            model=self.model or "gemini-2.0-flash",
            contents=_contents_from_messages(messages),
            config=config,
        )

        tool_calls: list[ProposedToolCall] = []
        text_parts: list[str] = []
        candidates = getattr(response, "candidates", None) or []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            for part in parts:
                fn = getattr(part, "function_call", None)
                if fn and getattr(fn, "name", None):
                    args = dict(getattr(fn, "args", None) or {})
                    tool_calls.append(ProposedToolCall(name=fn.name, arguments=args))
                elif getattr(part, "text", None):
                    text_parts.append(part.text)

        if not tool_calls and not text_parts:
            fallback = getattr(response, "text", None)
            if fallback:
                text_parts.append(fallback)

        return AgentTurnResult(
            provider=self.name,
            tool_calls=tool_calls,
            assistant_text="\n".join(text_parts) if text_parts else None,
        )


def _provider_type() -> type[AgentProvider]:
    return GeminiAgentProvider
