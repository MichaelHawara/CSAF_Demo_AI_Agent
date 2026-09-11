from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import AgentInstance
from app.models.schemas import CheckoutConfirmBody, CheckoutRequestBody
from app.security.policies import SecurityPolicy
from app.services.carts import get_or_create_cart, to_public_cart
from app.services.checkout import (
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
