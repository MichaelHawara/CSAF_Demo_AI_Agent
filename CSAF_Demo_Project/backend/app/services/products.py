"""Catalog projections.

Public HTTP responses omit hidden seller fields. Agent tools may request a
full page projection — that split is the core teaching point.
"""

from __future__ import annotations

import re

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


# Words that describe how the customer feels, not what they are buying.
_FILLER_WORDS = {
    "a", "an", "the", "of", "for", "to", "and", "or", "me", "my", "pair", "pairs",
    "best", "good", "great", "highly", "rated", "top", "cheap", "new", "any", "some",
}


def _tokens(text: str) -> set[str]:
    """Lowercase word stems ("Water_Bottles" -> {"water", "bottle"})."""
    words = re.findall(r"[a-z0-9]+", (text or "").lower().replace("_", " "))
    return {w[:-1] if len(w) > 3 and w.endswith("s") and not w.endswith("ss") else w for w in words}


def search_products(db: Session, query: str, maximum_price: float | None) -> list[Product]:
    """Match every meaningful query word, falling back to any word.

    Model-written queries are messy ("running shoes", "water bottles"). Category
    names use underscores and plurals, so both sides are normalized first.
    """
    rows = list_products(db)
    wanted = _tokens(query) - _FILLER_WORDS
    indexed = [
        (
            product,
            _tokens(" ".join([product.name, product.description, product.category, product.seller.name])),
        )
        for product in rows
        if maximum_price is None or product.price - 1e-9 <= maximum_price
    ]
    if not wanted:
        matched = [product for product, _ in indexed]
    else:
        matched = [product for product, words in indexed if wanted <= words]
        if not matched:
            # No product has every word. Keep the closest matches instead of
            # returning nothing, so a slightly-off query still finds something.
            scored = [(len(wanted & words), product) for product, words in indexed]
            best = max((score for score, _ in scored), default=0)
            matched = [product for score, product in scored if best and score == best]
    # Best-rated first, like a storefront's default sort.
    return sorted(matched, key=lambda p: (-p.rating, -p.review_count, p.price, p.name))


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
