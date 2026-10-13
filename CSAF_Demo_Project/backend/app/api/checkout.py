import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import AgentInstance
from app.models.schemas import CheckoutApproveBody, CheckoutConfirmBody, CheckoutRequestBody
from app.security.policies import SecurityPolicy
from app.services.carts import get_or_create_cart, to_public_cart
from app.services.events import log_event
from app.services.checkout import (
    CheckoutError,
    approve_checkout,
    complete_demo_checkout,
    create_pending,
    get_pending,
    matches_snapshot,
)

router = APIRouter(prefix="/api/checkout", tags=["checkout"])
policy = SecurityPolicy()


@router.post("/request")
def request_checkout(body: CheckoutRequestBody, db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, body.customer_id)
    agent = db.get(AgentInstance, body.agent_id) if body.agent_id else None
    if agent is None:
        raise HTTPException(404, "Agent not found")
    empty = len(cart.items) == 0
    decision = policy.evaluate_checkout(agent, cart_empty=empty, confirmed=False)
    if agent.mode == "patched":
        pending = None if empty else create_pending(db, body.customer_id, agent.id, cart)
        db.commit()
        return {
            "allowed": False,
            "reason": decision.reason,
            "pending": {
                "id": pending.id,
                "customer_id": pending.customer_id,
                "product_id": pending.product_id,
                "seller_id": pending.seller_id,
                "quantity": pending.quantity,
                "unit_price": pending.unit_price,
                "total": pending.total,
            }
            if pending
            else None,
            "confirmation_received": False,
            "message": "Checkout requires customer confirmation bound to these exact details.",
            "demo_notice": "Demo transaction only—no real purchase occurred.",
        }
    if not decision.allowed:
        raise HTTPException(400, decision.reason)
    complete = complete_demo_checkout(cart)
    db.commit()
    return {
        "allowed": True,
        "confirmation_received": False,
        "cart": to_public_cart(cart).model_dump(),
        **complete,
    }


@router.post("/confirm")
def confirm_checkout(body: CheckoutConfirmBody, db: Session = Depends(get_db)):
    pending = get_pending(db, body.pending_id)
    if pending is None:
        raise HTTPException(404, "Pending checkout not found")
    payload = body.model_dump()
    if not matches_snapshot(pending, payload):
        raise HTTPException(
            400,
            "Confirmation does not match the exact customer, product, seller, quantity, price, and total.",
        )
    pending.confirmed = True
    cart = get_or_create_cart(db, pending.customer_id)
    complete = complete_demo_checkout(cart)
    db.commit()
    return {
        "allowed": True,
        "confirmation_received": True,
        "cart": to_public_cart(cart).model_dump(),
        **complete,
    }


@router.post("/approve")
def approve_checkout_route(body: CheckoutApproveBody, db: Session = Depends(get_db)):
    """The customer clicked "Approve checkout".

    This is the only route that completes a purchase for the whole cart. It
    validates the cart, recomputes every price from the catalog, and only then
    records the receipt and empties the cart.
    """
    try:
        cart = get_or_create_cart(db, body.customer_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    agent = db.get(AgentInstance, body.agent_id) if body.agent_id else None
    try:
        receipt = approve_checkout(db, cart)
    except CheckoutError as exc:
        raise HTTPException(400, str(exc)) from exc
    if agent is not None:
        agent.last_checkout_json = json.dumps(receipt)
        log_event(
            db,
            agent_id=agent.id,
            customer_id=body.customer_id,
            actor="RESULT",
            message=(
                f"Checkout approved: {receipt['item_count']} item(s), total ${receipt['total']:.2f} "
                f"(order {receipt['order_id']}, local demonstration)"
            ),
            details={"order_id": receipt["order_id"], "total": receipt["total"]},
            step=6,
        )
    db.commit()
    return {"approved": True, "receipt": receipt, "cart": to_public_cart(cart).model_dump()}


@router.post("/reject")
def reject_checkout_route(body: CheckoutApproveBody, db: Session = Depends(get_db)):
    """The customer declined. Nothing changes except a monitor line."""
    agent = db.get(AgentInstance, body.agent_id) if body.agent_id else None
    if agent is not None:
        log_event(
            db,
            agent_id=agent.id,
            customer_id=body.customer_id,
            actor="RESULT",
            message="Checkout not approved by the customer; cart left unchanged",
            details={},
            step=6,
        )
        db.commit()
    return {"approved": False, "message": "Checkout not approved. Your cart is unchanged."}
