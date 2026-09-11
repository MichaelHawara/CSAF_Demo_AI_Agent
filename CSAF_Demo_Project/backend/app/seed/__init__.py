"""Repeatable catalog and demo-agent seed.

Rows are upserted by stable primary keys so running seed twice never creates
duplicate products, sellers, or the demo customer.
"""

from sqlalchemy.orm import Session

from app.models.entities import (
    AgentInstance,
    Cart,
    Customer,
    Product,
    Review,
    Seller,
)
from app.services.constants import (
    DEFAULT_ALLOWED_TOOLS,
    DEFAULT_SYSTEM_INSTRUCTION,
    DEMO_AGENT_ID,
    DEMO_CUSTOMER_ID,
    HIDDEN_INSTRUCTIONS,
    PRODUCTS,
    REVIEWS,
    SELLERS,
)


def _upsert(session: Session, model, key: str, **fields):
    obj = session.get(model, key)
    if obj is None:
        obj = model(id=key, **fields)
        session.add(obj)
    else:
        for name, value in fields.items():
            setattr(obj, name, value)
    return obj


def seed_database(session: Session) -> None:
    for seller in SELLERS:
        _upsert(session, Seller, seller["id"], **{k: v for k, v in seller.items() if k != "id"})

    for product in PRODUCTS:
        fields = {k: v for k, v in product.items() if k != "id"}
        _upsert(session, Product, product["id"], **fields)

    for review in REVIEWS:
        fields = {k: v for k, v in review.items() if k != "id"}
        _upsert(session, Review, review["id"], **fields)

    _upsert(
        session,
        Customer,
        DEMO_CUSTOMER_ID,
        display_name="Alex Rivera",
        email="alex.rivera@example.invalid",
    )
    _upsert(session, Cart, f"cart_{DEMO_CUSTOMER_ID}", customer_id=DEMO_CUSTOMER_ID, status="open")

    existing = session.get(AgentInstance, DEMO_AGENT_ID)
    if existing is None:
        session.add(
            AgentInstance(
                id=DEMO_AGENT_ID,
                customer_id=DEMO_CUSTOMER_ID,
                display_name="Nozi",
                provider="mock",
                model="mock-deterministic",
                mode="vulnerable",
                system_instruction=DEFAULT_SYSTEM_INSTRUCTION,
                allowed_tools=",".join(DEFAULT_ALLOWED_TOOLS),
                budget=80.0,
                max_quantity=1,
            )
        )

    session.commit()


# Re-export so tests can assert the hidden payload is the spec text.
MALICIOUS_HIDDEN_TEXT = HIDDEN_INSTRUCTIONS
