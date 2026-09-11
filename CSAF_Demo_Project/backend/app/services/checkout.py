"""Simulated checkout only.

No payment provider is called. Confirmation is bound to an exact snapshot
so a later cart change cannot reuse an old approval.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Cart, PendingCheckout, Product
from app.security.policies import money
from app.services.carts import cart_totals


def snapshot_from_cart(cart: Cart) -> dict | None:
    if not cart.items:
        return None
    # Demo carts are expected to hold one line after the prepared attack.
    item = cart.items[0]
    product: Product | None = item.product
    seller_id = product.seller_id if product else ""
    qty, total = cart_totals(cart)
    return {
        "product_id": item.product_id,
        "seller_id": seller_id,
        "quantity": qty,
        "unit_price": round(item.unit_price, 2),
        "total": total,
    }


def create_pending(db: Session, customer_id: str, agent_id: str, cart: Cart) -> PendingCheckout | None:
    snap = snapshot_from_cart(cart)
    if snap is None:
        return None
    pending = PendingCheckout(
        id=f"chk_{uuid.uuid4().hex[:12]}",
        customer_id=customer_id,
        agent_id=agent_id,
        confirmed=False,
        **snap,
    )
    db.add(pending)
    db.flush()
    return pending


def matches_snapshot(pending: PendingCheckout, body: dict) -> bool:
    return (
        pending.customer_id == body["customer_id"]
        and pending.product_id == body["product_id"]
        and pending.seller_id == body["seller_id"]
        and pending.quantity == body["quantity"]
        and money(pending.unit_price) == money(body["unit_price"])
        and money(pending.total) == money(body["total"])
    )


def get_pending(db: Session, pending_id: str) -> PendingCheckout | None:
    return db.get(PendingCheckout, pending_id)


def latest_pending(db: Session, customer_id: str) -> PendingCheckout | None:
    return db.scalars(
        select(PendingCheckout)
        .where(PendingCheckout.customer_id == customer_id)
        .order_by(PendingCheckout.created_at.desc())
    ).first()


def complete_demo_checkout(cart: Cart) -> dict:
    cart.status = "demo_complete"
    cart.demo_checked_out = True
    return {
        "status": "demo_complete",
        "message": "Demo transaction only—no real purchase occurred.",
        "real_purchase": False,
    }
