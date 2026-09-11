"""Single execution path for every agent tool call.

The model proposes a name + JSON arguments. This module:
1. checks the agent allow-list
2. validates arguments with Pydantic
3. logs the attempt
4. runs the handler
5. returns a structured result

There is no eval(), no subprocess, and no generic HTTP fetch.
"""

from __future__ import annotations

from typing import Any, Callable

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from app.models.entities import AgentInstance
from app.models.schemas import (
    AddToCartArgs,
    GetCustomerProfileArgs,
    GetProductDetailsArgs,
    GetPurchaseHistoryArgs,
    ReadProductPageArgs,
    RequestCheckoutArgs,
    SearchMemoryArgs,
    SearchProductsArgs,
    SendCouponRequestArgs,
    StoreMemoryArgs,
    ToolExecutionResult,
    ViewCartArgs,
)
from app.services.events import log_event
from app.tools.handlers import (
    tool_add_to_cart,
    tool_get_customer_profile,
    tool_get_product_details,
    tool_get_purchase_history,
    tool_read_product_page,
    tool_request_checkout,
    tool_search_memory,
    tool_search_products,
    tool_send_coupon_request,
    tool_store_memory,
    tool_view_cart,
)

Handler = Callable[[Session, AgentInstance, BaseModel], ToolExecutionResult]

SCHEMA_AND_HANDLER: dict[str, tuple[type[BaseModel], Handler]] = {
    "search_products": (SearchProductsArgs, tool_search_products),
    "read_product_page": (ReadProductPageArgs, tool_read_product_page),
    "get_product_details": (GetProductDetailsArgs, tool_get_product_details),
    "add_to_cart": (AddToCartArgs, tool_add_to_cart),
    "view_cart": (ViewCartArgs, tool_view_cart),
    "request_checkout": (RequestCheckoutArgs, tool_request_checkout),
    "get_customer_profile": (GetCustomerProfileArgs, tool_get_customer_profile),
    "get_purchase_history": (GetPurchaseHistoryArgs, tool_get_purchase_history),
    "send_coupon_request": (SendCouponRequestArgs, tool_send_coupon_request),
    "store_memory": (StoreMemoryArgs, tool_store_memory),
    "search_memory": (SearchMemoryArgs, tool_search_memory),
}


class ToolExecutor:
    def allowed_names(self, agent: AgentInstance) -> set[str]:
        raw = [part.strip() for part in (agent.allowed_tools or "").split(",") if part.strip()]
        return set(raw)

    def execute(
        self,
        db: Session,
        agent: AgentInstance,
        name: str,
        arguments: dict[str, Any],
    ) -> ToolExecutionResult:
        allowed = self.allowed_names(agent)
        if name not in allowed:
            result = ToolExecutionResult(
                ok=False,
                tool=name,
                blocked=True,
                error=f"Tool {name} is not on this agent's allow-list.",
                policy_decision="tool_not_allowed",
            )
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="POLICY",
                message=f"Rejected unknown or disallowed tool {name}",
                details={"tool": name},
                step=6,
            )
            return result

        spec = SCHEMA_AND_HANDLER.get(name)
        if spec is None:
            return ToolExecutionResult(ok=False, tool=name, error="No handler registered")

        schema, handler = spec
        try:
            parsed = schema.model_validate(arguments or {})
        except ValidationError as exc:
            return ToolExecutionResult(
                ok=False,
                tool=name,
                error="Invalid tool arguments",
                data={"validation": exc.errors()},
            )

        log_event(
            db,
            agent_id=agent.id,
            customer_id=agent.customer_id,
            actor="AGENT",
            message=f"Requested {name}",
            details={"tool": name, "arguments": parsed.model_dump()},
            step=5 if name in {"add_to_cart", "request_checkout"} else 2,
        )

        result = handler(db, agent, parsed)

        if name == "search_products" and result.ok:
            count = len(result.data.get("products") or [])
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="NOZAMA",
                message=f"Returned {count} products",
                details={"count": count},
                step=2,
            )
        if name == "read_product_page" and result.data.get("untrusted_seller_content_present"):
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="SECURITY",
                message="Untrusted seller content entered context",
                details={"product_id": parsed.model_dump().get("product_id")},
                step=4,
            )
        if result.policy_decision:
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="POLICY",
                message=result.policy_decision,
                details={"tool": name, "blocked": result.blocked},
                step=6,
            )
        if result.blocked:
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="RESULT",
                message="Action blocked",
                details={"tool": name},
                step=6,
            )
        elif name == "add_to_cart" and agent.mode != "patched":
            log_event(
                db,
                agent_id=agent.id,
                customer_id=agent.customer_id,
                actor="RESULT",
                message="Action allowed in vulnerable mode",
                details={"tool": name},
                step=6,
            )
        return result
