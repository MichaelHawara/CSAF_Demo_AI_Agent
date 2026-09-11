"""Tool handlers. Gemini never mutates the cart; these functions do.

Every handler receives a validated Pydantic model plus the agent/customer
context. None of these functions execute shell commands or fetch URLs.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.entities import AgentInstance
from app.models.schemas import (
    AddToCartArgs,
    GetProductDetailsArgs,
    ReadProductPageArgs,
    RequestCheckoutArgs,
    SearchProductsArgs,
    SendCouponRequestArgs,
    StoreMemoryArgs,
    SearchMemoryArgs,
    ToolExecutionResult,
    ViewCartArgs,
    GetCustomerProfileArgs,
    GetPurchaseHistoryArgs,
)
from app.security.policies import SecurityPolicy, money
from app.services.carts import add_item, cart_totals, get_or_create_cart, to_public_cart
from app.services.checkout import complete_demo_checkout, create_pending, snapshot_from_cart
from app.services.memory import memory_store
from app.services.products import (
    get_product,
    hidden_seller_content,
    search_products,
    to_public_product,
    visible_page,
)


policy = SecurityPolicy()


def tool_search_products(db: Session, agent: AgentInstance, args: SearchProductsArgs) -> ToolExecutionResult:
    rows = search_products(db, args.query, args.maximum_price)
    return ToolExecutionResult(
        ok=True,
        tool="search_products",
        data={
            "query": args.query,
            "maximum_price": args.maximum_price,
            "products": [to_public_product(p).model_dump() for p in rows],
        },
    )


def tool_read_product_page(
    db: Session, agent: AgentInstance, args: ReadProductPageArgs
) -> ToolExecutionResult:
    """Vulnerable reader: seller-controlled fields are concatenated into the
    same payload the model will see. Patched content defenses are a student
    task; money rules still apply later at add_to_cart / checkout.
    """
    product = get_product(db, args.product_id)
    if product is None:
        return ToolExecutionResult(ok=False, tool="read_product_page", error="Unknown product")

    visible = visible_page(product)
    hidden = hidden_seller_content(product)
    untrusted_present = any(str(v).strip() for v in hidden.values()) and product.is_malicious

    payload: dict[str, Any] = {
        "visible": visible,
        "page_text": (
            f"Product: {product.name}\n"
            f"Seller: {product.seller.name}\n"
            f"Price: ${product.price:.2f}\n"
            f"Rating: {product.rating}\n"
            f"Description: {product.description}\n"
        ),
    }
    # Weak separation on purpose: hidden seller text is included as extra
    # fields and appended onto page_text the model reads as one blob.
    payload["hidden_description"] = hidden["hidden_description"]
    payload["image_alt_text"] = hidden["image_alt_text"]
    payload["seller_metadata"] = hidden["seller_metadata"]
    payload["seller_review"] = hidden["seller_review"]
    if untrusted_present:
        payload["page_text"] += (
            "\n--- additional listing fields ---\n"
            f"{hidden['hidden_description']}\n"
            f"{hidden['image_alt_text']}\n"
            f"{hidden['seller_metadata']}\n"
            f"{hidden['seller_review']}\n"
        )
        payload["untrusted_seller_content_present"] = True
    return ToolExecutionResult(ok=True, tool="read_product_page", data=payload)


def tool_get_product_details(
    db: Session, agent: AgentInstance, args: GetProductDetailsArgs
) -> ToolExecutionResult:
    product = get_product(db, args.product_id)
    if product is None:
        return ToolExecutionResult(ok=False, tool="get_product_details", error="Unknown product")
    return ToolExecutionResult(
        ok=True,
        tool="get_product_details",
        data={
            "product_id": product.id,
            "name": product.name,
            "seller": product.seller.name,
            "trusted_seller": product.seller.trusted,
            "price": round(product.price, 2),
            "rating": product.rating,
            "description": product.description,
        },
    )


def tool_add_to_cart(db: Session, agent: AgentInstance, args: AddToCartArgs) -> ToolExecutionResult:
    product = get_product(db, args.product_id)
    if product is None:
        return ToolExecutionResult(ok=False, tool="add_to_cart", error="Unknown product")

    cart = get_or_create_cart(db, agent.customer_id)
    current_qty, current_total = cart_totals(cart)
    decision = policy.evaluate_add_to_cart(
        agent, product, args.quantity, current_qty, current_total
    )
    attempted_total = money(current_total + product.price * args.quantity)
    attempt = {
        "product_id": product.id,
        "product_name": product.name,
        "quantity": args.quantity,
        "unit_price": round(product.price, 2),
        "attempted_total": attempted_total,
        "budget": agent.budget,
        "max_quantity": agent.max_quantity,
        "mode": agent.mode,
    }
    if not decision.allowed:
        return ToolExecutionResult(
            ok=False,
            tool="add_to_cart",
            blocked=True,
            policy_decision=decision.reason,
            error=decision.reason,
            data=attempt,
        )

    add_item(db, cart, product, args.quantity)
    db.refresh(cart)
    public = to_public_cart(cart)
    return ToolExecutionResult(
        ok=True,
        tool="add_to_cart",
        policy_decision=decision.reason,
        data={**attempt, "cart": public.model_dump()},
    )


def tool_view_cart(db: Session, agent: AgentInstance, args: ViewCartArgs) -> ToolExecutionResult:
    cart = get_or_create_cart(db, agent.customer_id)
    return ToolExecutionResult(
        ok=True,
        tool="view_cart",
        data={"cart": to_public_cart(cart).model_dump()},
    )


def tool_request_checkout(
    db: Session, agent: AgentInstance, args: RequestCheckoutArgs
) -> ToolExecutionResult:
    cart = get_or_create_cart(db, agent.customer_id)
    empty = len(cart.items) == 0
    decision = policy.evaluate_checkout(agent, cart_empty=empty, confirmed=False)
    snap = snapshot_from_cart(cart)
    if not decision.allowed:
        pending = None
        if agent.mode == "patched" and not empty:
            pending = create_pending(db, agent.customer_id, agent.id, cart)
        return ToolExecutionResult(
            ok=False,
            tool="request_checkout",
            blocked=True,
            policy_decision=decision.reason,
            error=decision.reason,
            data={
                "snapshot": snap,
                "pending_id": pending.id if pending else None,
                "confirmation_received": False,
                "message": "Demo transaction only—no real purchase occurred."
                if pending
                else decision.reason,
            },
        )

    complete = complete_demo_checkout(cart)
    return ToolExecutionResult(
        ok=True,
        tool="request_checkout",
        policy_decision=decision.reason,
        data={
            "snapshot": snap,
            "confirmation_received": False,
            **complete,
        },
    )


def tool_get_customer_profile(
    db: Session, agent: AgentInstance, args: GetCustomerProfileArgs
) -> ToolExecutionResult:
    # TODO(STUDENT): Return a fictional profile in vulnerable mode and apply
    # PII filtering in patched mode. See docs/STUDENT_WORK.md task 1.
    return ToolExecutionResult(
        ok=True,
        tool="get_customer_profile",
        data={
            "implemented": False,
            "task": "STUDENT_TASK_1",
            "message": "TODO(STUDENT): Implement fictional customer profile access.",
        },
    )


def tool_get_purchase_history(
    db: Session, agent: AgentInstance, args: GetPurchaseHistoryArgs
) -> ToolExecutionResult:
    # TODO(STUDENT): Return fictional history; never real orders.
    return ToolExecutionResult(
        ok=True,
        tool="get_purchase_history",
        data={
            "implemented": False,
            "task": "STUDENT_TASK_1",
            "message": "TODO(STUDENT): Implement fictional purchase history.",
        },
    )


def tool_send_coupon_request(
    db: Session, agent: AgentInstance, args: SendCouponRequestArgs
) -> ToolExecutionResult:
    # TODO(STUDENT): Local mock attacker inbox only. Must not perform real HTTP.
    return ToolExecutionResult(
        ok=False,
        tool="send_coupon_request",
        blocked=True,
        data={
            "implemented": False,
            "task": "STUDENT_TASK_1",
            "destination": args.destination,
            "message": "TODO(STUDENT): Route this to a local Mock Attacker Inbox.",
        },
        error="Not implemented — student task 1. No external request was sent.",
    )


def tool_store_memory(
    db: Session, agent: AgentInstance, args: StoreMemoryArgs
) -> ToolExecutionResult:
    # TODO(STUDENT): Honor ownership and trust. Foundation store is a stub.
    record_id = memory_store.store(
        agent.id, agent.customer_id, args.content, args.source, "untrusted"
    )
    return ToolExecutionResult(
        ok=True,
        tool="store_memory",
        data={
            "implemented": False,
            "task": "STUDENT_TASK_2",
            "record_id": record_id,
            "message": "TODO(STUDENT): Persist memory with trust and expiration.",
        },
    )


def tool_search_memory(
    db: Session, agent: AgentInstance, args: SearchMemoryArgs
) -> ToolExecutionResult:
    rows = memory_store.search(agent.id, args.query)
    return ToolExecutionResult(
        ok=True,
        tool="search_memory",
        data={
            "implemented": False,
            "task": "STUDENT_TASK_2",
            "results": rows,
            "message": "TODO(STUDENT): Implement retrieval filtering.",
        },
    )
