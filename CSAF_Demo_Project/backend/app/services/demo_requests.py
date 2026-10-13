"""Demo shopping requests generated from the catalog.

Nothing here is hard-coded per product. For every product in the database we
write a few natural requests for its category, with a budget and quantity
derived from that product's own price. Add a product to the catalog and new
requests appear automatically.

The customer's budget and quantity live *inside* the request text. The
backend parses them back out (app/services/request_parser.py) when the
message is sent.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Product

# category -> (singular noun phrase, plural noun phrase)
CATEGORY_PHRASES: dict[str, tuple[str, str]] = {
    "headphones": ("pair of wireless headphones", "pairs of wireless headphones"),
    "earbuds": ("pair of wireless earbuds", "pairs of wireless earbuds"),
    "home": ("desk lamp", "desk lamps"),
    "accessories": ("tablet stand", "tablet stands"),
    "laptops": ("laptop", "laptops"),
    "desktops": ("desktop computer", "desktop computers"),
    "shoes": ("pair of running shoes", "pairs of running shoes"),
    "shirts": ("shirt", "shirts"),
    "water_bottles": ("water bottle", "water bottles"),
    "chargers": ("charger", "chargers"),
}

_NUMBER_WORDS = {1: "one", 2: "two", 3: "three"}

# Templates are picked by position so a product's variants read differently.
_SINGLE_TEMPLATES = (
    "Find me one {noun} for no more than ${budget} and add it to my cart.",
    "I'm looking for a highly rated {noun}, under ${budget}. Please add the best one to my cart.",
    "Can you pick out one {noun} for me? My budget is ${budget}. Add it to my cart when you find it.",
)
_MULTI_TEMPLATES = (
    "Find me {qty} {noun} with a total budget of ${budget} and add them to my cart.",
    "I need {qty} {noun} for under ${budget} total. Please add the best-rated ones to my cart.",
)


@dataclass(frozen=True)
class DemoRequest:
    text: str
    category: str
    product_id: str
    product_name: str
    quantity: int
    budget: int

    def public(self) -> dict:
        return {
            "request": self.text,
            "category": self.category,
            "product_id": self.product_id,
            "product_name": self.product_name,
            "quantity": self.quantity,
            "budget": self.budget,
        }


def _round_budget(amount: float) -> int:
    """Round up to a friendly figure: $5 steps under $100, $10 under $500, else $50."""
    step = 5 if amount < 100 else 10 if amount < 500 else 50
    return int(math.ceil(amount / step) * step)


def _quantities_for(price: float) -> tuple[int, ...]:
    if price < 50:
        return (1, 2, 3)
    if price < 200:
        return (1, 2)
    return (1,)


def _phrases(category: str) -> tuple[str, str]:
    if category in CATEGORY_PHRASES:
        return CATEGORY_PHRASES[category]
    label = category.replace("_", " ")
    return label, f"{label}s"


def build_demo_requests(db: Session) -> list[DemoRequest]:
    """One or more requests per catalog product, de-duplicated by text."""
    products = list(db.scalars(select(Product).order_by(Product.category, Product.id)))
    requests: list[DemoRequest] = []
    seen: set[str] = set()
    for index, product in enumerate(products):
        singular, plural = _phrases(product.category)
        for variant, quantity in enumerate(_quantities_for(product.price)):
            # 20% headroom so the product itself fits, and so do close rivals.
            budget = _round_budget(product.price * quantity * 1.2)
            if quantity == 1:
                template = _SINGLE_TEMPLATES[(index + variant) % len(_SINGLE_TEMPLATES)]
                text = template.format(noun=singular, budget=budget)
            else:
                template = _MULTI_TEMPLATES[(index + variant) % len(_MULTI_TEMPLATES)]
                text = template.format(qty=_NUMBER_WORDS[quantity], noun=plural, budget=budget)
            if text in seen:
                continue
            seen.add(text)
            requests.append(
                DemoRequest(
                    text=text,
                    category=product.category,
                    product_id=product.id,
                    product_name=product.name,
                    quantity=quantity,
                    budget=budget,
                )
            )
    return requests


def pick_random_request(
    db: Session, exclude: str | None = None, rng: random.Random | None = None
) -> DemoRequest | None:
    """Random request, avoiding an immediate repeat of `exclude` when possible."""
    pool = build_demo_requests(db)
    if not pool:
        return None
    candidates = [r for r in pool if r.text != (exclude or "").strip()] or pool
    return (rng or random).choice(candidates)
