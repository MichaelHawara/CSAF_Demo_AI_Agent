"""Cart mutations. Prices always come from the catalog, never from the model."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Cart, CartItem, Customer, Product
from app.models.schemas import CartItemPublic, CartPublic
from app.security.policies import money


def get_or_create_cart(db: Session, customer_id: str) -> Cart:
    cart = db.scalars(
        select(Cart).options(joinedload(Cart.items).joinedload(CartItem.product)).where(
            Cart.customer_id == customer_id
        )
    ).unique().one_or_none()
    if cart is None:
        customer = db.get(Customer, customer_id)
        if customer is None:
            raise ValueError("Unknown customer")
        cart = Cart(id=f"cart_{uuid.uuid4().hex[:10]}", customer_id=customer_id, status="open")
        db.add(cart)
        db.flush()
    return cart


def cart_totals(cart: Cart) -> tuple[int, float]:
    qty = sum(item.quantity for item in cart.items)
    total = money(sum(item.unit_price * item.quantity for item in cart.items))
    return qty, total


def to_public_cart(cart: Cart) -> CartPublic:
    items = []
    for item in cart.items:
        name = item.product.name if item.product else item.product_id
        line = money(item.unit_price * item.quantity)
        items.append(
            CartItemPublic(
                id=item.id,
                product_id=item.product_id,
                product_name=name,
                quantity=item.quantity,
                unit_price=round(item.unit_price, 2),
                line_total=line,
            )
        )
    qty, total = cart_totals(cart)
    return CartPublic(
        id=cart.id,
        customer_id=cart.customer_id,
        status=cart.status,
        demo_checked_out=cart.demo_checked_out,
        items=items,
        total=total,
        quantity=qty,
    )


def add_item(db: Session, cart: Cart, product: Product, quantity: int) -> CartItem:
    existing = next((i for i in cart.items if i.product_id == product.id), None)
    if existing:
        existing.quantity += quantity
        existing.unit_price = product.price
        return existing
    item = CartItem(
        id=f"item_{uuid.uuid4().hex[:10]}",
        cart_id=cart.id,
        product_id=product.id,
        quantity=quantity,
        unit_price=product.price,
    )
    db.add(item)
    cart.items.append(item)
    db.flush()
    return item


def remove_item(db: Session, cart: Cart, item_id: str) -> bool:
    item = next((i for i in cart.items if i.id == item_id), None)
    if item is None:
        return False
    db.delete(item)
    db.flush()
    return True


def clear_cart(db: Session, cart: Cart) -> None:
    for item in list(cart.items):
        db.delete(item)
    cart.demo_checked_out = False
    cart.status = "open"
    db.flush()
