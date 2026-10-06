"""Catalog projections.

Public HTTP responses omit hidden seller fields. Agent tools may request a
full page projection — that split is the core teaching point.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.entities import Product
from app.models.schemas import ProductDetailPublic, ProductPublic, ReviewPublic


def to_public_product(product: Product) -> ProductPublic:
    # image_alt_text_public is a safe customer-facing caption, never the
    # hidden injection channel stored on malicious listings.
    safe_alt = product.name if product.is_malicious else (product.image_alt_text or product.name)
    return ProductPublic(
        id=product.id,
        name=product.name,
        seller_id=product.seller_id,
        seller_name=product.seller.name,
        trusted_seller=product.seller.trusted,
        price=round(product.price, 2),
        rating=product.rating,
        review_count=product.review_count,
        description=product.description,
        category=product.category,
        accent=product.accent,
        url=product.url,
        image_alt_text_public=safe_alt,
    )


def to_public_detail(product: Product) -> ProductDetailPublic:
    base = to_public_product(product)
    reviews = [
        ReviewPublic(id=r.id, author=r.author, rating=r.rating, body=r.body)
        for r in product.reviews
    ]
    return ProductDetailPublic(**base.model_dump(), reviews=reviews)


def list_products(db: Session) -> list[Product]:
    return list(
        db.scalars(select(Product).options(joinedload(Product.seller)).order_by(Product.name)).unique()
    )


def search_products(db: Session, query: str, maximum_price: float | None) -> list[Product]:
    rows = list_products(db)
    q = (query or "").strip().lower()
    matched = []
    for product in rows:
        haystack = " ".join(
            [
                product.name,
                product.description,
                product.category,
                product.seller.name,
            ]
        ).lower()
        if q and q not in haystack and not all(part in haystack for part in q.split()):
            continue
        if maximum_price is not None and product.price - 1e-9 > maximum_price:
            continue
        matched.append(product)
    return matched


def get_product(db: Session, product_id: str) -> Product | None:
    return db.scalars(
        select(Product)
        .options(joinedload(Product.seller), joinedload(Product.reviews))
        .where(Product.id == product_id)
    ).unique().one_or_none()


def visible_page(product: Product) -> dict:
    return {
        "product_id": product.id,
        "name": product.name,
        "seller": product.seller.name,
        "trusted_seller": product.seller.trusted,
        "price": round(product.price, 2),
        "rating": product.rating,
        "description": product.description,
        "reviews": [{"author": r.author, "rating": r.rating, "body": r.body} for r in product.reviews],
    }


def hidden_seller_content(product: Product) -> dict:
    return {
        "hidden_description": product.hidden_description,
        "image_alt_text": product.image_alt_text,
        "seller_metadata": product.seller_metadata,
        "seller_review": product.seller_review,
    }
