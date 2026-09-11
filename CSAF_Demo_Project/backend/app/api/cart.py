from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import AgentInstance
from app.models.schemas import AddCartItemBody
from app.security.policies import SecurityPolicy
from app.services.carts import (
    add_item,
    cart_totals,
    get_or_create_cart,
    remove_item,
    to_public_cart,
)
from app.services.products import get_product

router = APIRouter(prefix="/api/cart", tags=["cart"])
policy = SecurityPolicy()


@router.get("/{customer_id}")
def get_cart(customer_id: str, db: Session = Depends(get_db)):
    try:
        cart = get_or_create_cart(db, customer_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return to_public_cart(cart).model_dump()


@router.post("/{customer_id}/items")
def add_cart_item(customer_id: str, body: AddCartItemBody, db: Session = Depends(get_db)):
    product = get_product(db, body.product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    cart = get_or_create_cart(db, customer_id)
    agent = None
    if body.agent_id:
        agent = db.get(AgentInstance, body.agent_id)
    if agent is not None:
        qty, total = cart_totals(cart)
        decision = policy.evaluate_add_to_cart(agent, product, body.quantity, qty, total)
        if not decision.allowed:
            raise HTTPException(403, decision.reason)
    add_item(db, cart, product, body.quantity)
    db.commit()
    db.refresh(cart)
    return to_public_cart(cart).model_dump()


@router.delete("/{customer_id}/items/{item_id}")
def delete_cart_item(customer_id: str, item_id: str, db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, customer_id)
    if not remove_item(db, cart, item_id):
        raise HTTPException(404, "Item not found")
    db.commit()
    db.refresh(cart)
    return to_public_cart(cart).model_dump()
