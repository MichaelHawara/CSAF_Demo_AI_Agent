"""Google Gemini provider using the official google-genai SDK.

Automatic function calling is disabled. If the SDK executed tools itself,
this demo could not show the application as the authorization boundary:
Gemini only *proposes* function calls, and the orchestrator / ToolExecutor
decide whether they run.

Conversation shape sent to Gemini on each call:

* earlier customer and assistant messages as plain text, then
* for the request in progress, the model's own function calls and the tool
  results, replayed as real ``function_call`` / ``function_response`` parts.

Intentional weakness (this is a security demo): the text of a product page
is *pasted into the conversation* next to the function result rather than kept
inside it. Many real RAG-style apps are built this way, and it is exactly what
lets seller-written text pass for something the customer or developer said.

The provider object lives for one customer request (the orchestrator builds a
new one per message), so it can safely hold the raw model turns, including any
thought signatures the SDK needs echoed back, in memory while the tool loop runs.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

import httpx

from app.agents.base import AgentProvider
from app.models.entities import AgentInstance, ConversationMessage
from app.models.schemas import AgentTurnResult, ProposedToolCall

# Used only if an agent has no model set. Google retires models regularly;
# set GEMINI_MODEL in .env (scripts/live_gemini_check.py lists what works).
DEFAULT_MODEL = "gemini-3.1-flash-lite"
REQUEST_TIMEOUT_MS = 40_000
MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1.5
RETRYABLE_STATUS_CODES = {500, 502, 503, 504}
# 429 is handled separately: free-tier quotas reset per minute, so we wait only
# when Google says the wait is short. Otherwise the orchestrator tells the
# customer to try again in a minute.
MAX_QUOTA_WAIT_SECONDS = 20.0
_RETRY_IN_RE = re.compile(
    r"retry in\s*(?:(?P<h>\d+)h)?\s*(?:(?P<m>\d+)m)?\s*(?:(?P<s>[\d.]+)s)?", re.IGNORECASE
)


def _quota_retry_seconds(exc: Exception) -> float | None:
    """Parse Google's "Please retry in 2h9m32.9s" hint into seconds."""
    found = _RETRY_IN_RE.search(str(exc))
    if not found or not any(found.group(g) for g in ("h", "m", "s")):
        return None
    return (
        int(found.group("h") or 0) * 3600
        + int(found.group("m") or 0) * 60
        + float(found.group("s") or 0)
    )


def _to_gemini_tools(tools: list[dict[str, Any]]) -> list[Any]:
    from google.genai import types

    declarations = []
    for tool in tools:
        params = tool.get("parameters")
        # Gemini rejects an OBJECT schema with no properties, so tools that
        # take no arguments are declared without a parameters block.
        if not params or not params.get("properties"):
            params = None
        declarations.append(
            types.FunctionDeclaration(
                name=tool["name"],
                description=tool.get("description", ""),
                parameters=params,
            )
        )
    return [types.Tool(function_declarations=declarations)]


def _history_contents(messages: list[ConversationMessage]) -> list[Any]:
    """Customer and assistant text up to and including the latest customer message.

    Tool traffic from the request in progress is replayed separately (with
    signatures intact). Tool traffic from older requests is dropped; the cart
    is always available through the view_cart tool.
    """
    from google.genai import types

    last_user = max((i for i, m in enumerate(messages) if m.role == "user"), default=-1)
    contents: list[Any] = []
    for message in messages[: last_user + 1]:
        if message.role == "user":
            role = "user"
        elif message.role == "assistant":
            role = "model"
        else:
            continue
        if message.content.strip():
            contents.append(types.Content(role=role, parts=[types.Part(text=message.content)]))
    return contents


def _page_text_to_paste(tool_name: str, response: dict[str, Any]) -> str | None:
    """Conversation text for a successfully read product page, else None."""
    if tool_name != "read_product_page" or not response.get("ok"):
        return None
    data = response.get("data") or {}
    page_text = str(data.get("page_text") or "").strip()
    if not page_text:
        return None
    reviews = [
        f"- {r.get('author', 'A shopper')} ({r.get('rating', '?')}/5): {r.get('body', '')}"
        for r in data.get("reviews") or []
    ]
    text = f"Here is the product page you opened:\n\n{page_text}"
    if reviews:
        text += "\nCustomer reviews:\n" + "\n".join(reviews)
    return text


def _json_safe(value: Any) -> dict[str, Any]:
    """function_response needs a JSON object made of plain types."""
    return json.loads(json.dumps(value, default=str))


class GeminiAgentProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str) -> None:
        self.api_key = api_key
        self.model = model
        self._client: Any = None
        # Raw turns of the request in progress, in order.
        self._turn_contents: list[Any] = []
        # The model's latest function-call turn, waiting for its results.
        self._pending_model_content: Any = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
        return self._client

    async def _generate_with_retry(self, **kwargs: Any) -> Any:
        """Call Gemini, retrying the transient failures it is known for.

        503 ("high demand") and other 5xx errors are usually gone a moment
        later. Anything else (bad key, retired model, exhausted quota) fails
        immediately so the operator sees the real cause in the activity feed.
        """
        from google.genai import errors

        last_error: Exception | None = None
        for attempt in range(1, MAX_ATTEMPTS + 1):
            delay = RETRY_BASE_DELAY_SECONDS * attempt
            try:
                return await self._get_client().aio.models.generate_content(**kwargs)
            except errors.APIError as exc:
                if exc.code == 429:
                    # Per-minute quota. Google says how long to wait; a short
                    # wait is worth it, a long one is not.
                    wait = _quota_retry_seconds(exc)
                    if wait is None or wait > MAX_QUOTA_WAIT_SECONDS:
                        raise
                    delay = wait + 0.5
                elif exc.code not in RETRYABLE_STATUS_CODES:
                    raise
                last_error = exc
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_error = exc
            if attempt < MAX_ATTEMPTS:
                await asyncio.sleep(delay)
        assert last_error is not None
        raise last_error

    def _attach_results(self, last_results: list[dict[str, Any]]) -> None:
        from google.genai import types

        if self._pending_model_content is None or not last_results:
            return
        parts: list[Any] = []
        pasted_pages: list[str] = []
        for item in last_results:
            response = item["response"]
            page = _page_text_to_paste(item["name"], response)
            if page is not None:
                # Deliberately insecure (see module docstring): the listing text
                # is pasted into the conversation instead of staying inside the
                # function result, so the model reads seller copy as if it were
                # part of the chat. The function result just acknowledges.
                pasted_pages.append(page)
                response = {"ok": True, "status": "Page loaded. Its content is in the next message."}
            parts.append(
                types.Part.from_function_response(name=item["name"], response=_json_safe(response))
            )
        for page in pasted_pages:
            parts.append(types.Part(text=page))
        self._turn_contents.append(self._pending_model_content)
        self._turn_contents.append(types.Content(role="user", parts=parts))
        self._pending_model_content = None

    async def run_turn(
        self,
        agent: AgentInstance,
        messages: list[ConversationMessage],
        tools: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> AgentTurnResult:
        from google.genai import types

        self._attach_results(context.get("last_results") or [])

        config = types.GenerateContentConfig(
            system_instruction=agent.system_instruction,
            tools=_to_gemini_tools(tools),
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_MS),
        )
        response = await self._generate_with_retry(
            model=self.model or DEFAULT_MODEL,
            contents=_history_contents(messages) + self._turn_contents,
            config=config,
        )

        tool_calls: list[ProposedToolCall] = []
        text_parts: list[str] = []
        for candidate in getattr(response, "candidates", None) or []:
            content = getattr(candidate, "content", None)
            parts = getattr(content, "parts", None) or []
            found_call = False
            for part in parts:
                fn = getattr(part, "function_call", None)
                if fn and getattr(fn, "name", None):
                    found_call = True
                    tool_calls.append(
                        ProposedToolCall(name=fn.name, arguments=dict(getattr(fn, "args", None) or {}))
                    )
                elif getattr(part, "text", None) and not getattr(part, "thought", False):
                    text_parts.append(part.text)
            if found_call:
                self._pending_model_content = content
            # Only the first candidate drives the demo.
            break

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
