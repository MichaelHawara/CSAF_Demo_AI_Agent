from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.schemas import AddCartItemBody, UpdateCartItemBody
from app.services.carts import (
    add_item,
    get_or_create_cart,
    remove_item,
    set_item_quantity,
    to_public_cart,
)
from app.services.products import get_product

router = APIRouter(prefix="/api/cart", tags=["cart"])


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
    # This route is the shopper clicking "Add to cart" themselves. The budget
    # and quantity policy governs what the *agent* may propose (see
    # app/tools/handlers.py); a person's own click is not limited by limits
    # parsed from an earlier chat message.
    if body.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1.")
    add_item(db, cart, product, body.quantity)
    db.commit()
    db.refresh(cart)
    return to_public_cart(cart).model_dump()


@router.patch("/{customer_id}/items/{item_id}")
def update_cart_item(
    customer_id: str, item_id: str, body: UpdateCartItemBody, db: Session = Depends(get_db)
):
    if body.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1. Use remove to delete the item.")
    cart = get_or_create_cart(db, customer_id)
    if not set_item_quantity(db, cart, item_id, body.quantity):
        raise HTTPException(404, "Item not found")
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
