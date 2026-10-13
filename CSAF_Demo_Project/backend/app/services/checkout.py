"""Simulated checkout only.

No payment provider is called. Confirmation is bound to an exact snapshot
so a later cart change cannot reuse an old approval.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

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


# --- Customer-approved checkout (whole cart) -------------------------------
# The customer's own click on "Approve checkout" is the confirmation. Nothing
# changes until that request arrives, and every number is recomputed here from
# catalog prices, never taken from the browser or the model.

TAX_RATE = 0.08
FREE_SHIPPING_THRESHOLD = 35.00
SHIPPING_FLAT_RATE = 5.99
DEMO_CHECKOUT_NOTICE = (
    "Checkout approved in the local demonstration. No real payment was processed "
    "and nothing will be shipped."
)


class CheckoutError(ValueError):
    """The cart cannot be checked out (empty, unknown product, bad quantity)."""


def build_receipt(cart: Cart) -> dict:
    """Validate the cart and price it. Does not change any state."""
    if not cart.items:
        raise CheckoutError("Your cart is empty.")
    lines = []
    for item in cart.items:
        product: Product | None = item.product
        if product is None:
            raise CheckoutError("A product in the cart no longer exists.")
        if item.quantity < 1:
            raise CheckoutError(f"Invalid quantity for {product.name}.")
        unit_price = money(product.price)  # catalog price wins over the stored one
        lines.append(
            {
                "product_id": product.id,
                "name": product.name,
                "image_url": product.url,
                "quantity": item.quantity,
                "unit_price": unit_price,
                "line_total": money(unit_price * item.quantity),
            }
        )
    subtotal = money(sum(line["line_total"] for line in lines))
    tax = money(subtotal * TAX_RATE)
    shipping = 0.0 if subtotal >= FREE_SHIPPING_THRESHOLD else SHIPPING_FLAT_RATE
    return {
        "items": lines,
        "item_count": sum(line["quantity"] for line in lines),
        "subtotal": subtotal,
        "tax_rate": TAX_RATE,
        "tax": tax,
        "shipping": money(shipping),
        "total": money(subtotal + tax + shipping),
    }


def approve_checkout(db: Session, cart: Cart) -> dict:
    """Customer approved: record the receipt and empty the cart."""
    receipt = build_receipt(cart)
    receipt["order_id"] = f"DEMO-{uuid.uuid4().hex[:8].upper()}"
    receipt["approved_at"] = datetime.now(timezone.utc).isoformat()
    receipt["status"] = "approved"
    receipt["demo_notice"] = DEMO_CHECKOUT_NOTICE
    receipt["real_purchase"] = False
    for item in list(cart.items):
        db.delete(item)
    cart.items.clear()
    cart.status = "open"
    cart.demo_checked_out = False
    db.flush()
    return receipt
