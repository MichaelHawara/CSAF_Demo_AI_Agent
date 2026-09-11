from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.products import get_product, list_products, search_products, to_public_detail, to_public_product

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("")
def all_products(db: Session = Depends(get_db)):
    return [to_public_product(p).model_dump() for p in list_products(db)]


@router.get("/search")
def product_search(
    q: str = Query(""),
    maximum_price: float | None = Query(None),
    db: Session = Depends(get_db),
):
    rows = search_products(db, q, maximum_price)
    return [to_public_product(p).model_dump() for p in rows]


@router.get("/{product_id}")
def product_detail(product_id: str, db: Session = Depends(get_db)):
    product = get_product(db, product_id)
    if product is None:
        raise HTTPException(404, "Product not found")
    # Public catalog never includes hidden seller-controlled fields.
    return to_public_detail(product).model_dump()
