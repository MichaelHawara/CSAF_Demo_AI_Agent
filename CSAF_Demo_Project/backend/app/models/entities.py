"""SQLAlchemy entities for the working foundation plus student placeholders.

Only the models required by the fair demo are fully wired into services.
MemoryRecord, MockAttackerRecord, and ToolPermission exist as documented
extension points — they are not part of the prepared attack path.
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Customer(Base):
    """Fictional shopper. Never store real personal data in this table."""

    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(180))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    agents = relationship("AgentInstance", back_populates="customer")
    cart = relationship("Cart", back_populates="customer", uselist=False)


class Seller(Base):
    __tablename__ = "sellers"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    trusted: Mapped[bool] = mapped_column(Boolean, default=False)
    blurb: Mapped[str] = mapped_column(Text, default="")

    products = relationship("Product", back_populates="seller")


class Product(Base):
    """Catalog row.

    Visible customer fields and hidden seller-controlled fields live on the
    same row so the demo can show two different projections of one listing.
    Public HTTP APIs must never return the hidden_* columns.
    """

    __tablename__ = "products"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    seller_id: Mapped[str] = mapped_column(ForeignKey("sellers.id"))
    price: Mapped[float] = mapped_column(Float)
    rating: Mapped[float] = mapped_column(Float)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(80), default="headphones")
    accent: Mapped[str] = mapped_column(String(40), default="#232f3e")
    is_malicious: Mapped[bool] = mapped_column(Boolean, default=False)
    # Seller-controlled channels. Returned only by the agent page-reader tool.
    hidden_description: Mapped[str] = mapped_column(Text, default="")
    image_alt_text: Mapped[str] = mapped_column(Text, default="")
    seller_metadata: Mapped[str] = mapped_column(Text, default="")
    seller_review: Mapped[str] = mapped_column(Text, default="")

    seller = relationship("Seller", back_populates="products")
    reviews = relationship("Review", back_populates="product")


class Review(Base):
    """Customer-visible reviews. Distinct from Product.seller_review."""

    __tablename__ = "reviews"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    author: Mapped[str] = mapped_column(String(120))
    rating: Mapped[float] = mapped_column(Float)
    body: Mapped[str] = mapped_column(Text)

    product = relationship("Product", back_populates="reviews")


class AgentInstance(Base):
    """A configuration + memory space, not a trained model.

    Creating an agent does not train Gemini. It stores instructions, tool
    allow-lists, and conversation state for one fictional customer.
    """

    __tablename__ = "agent_instances"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"))
    display_name: Mapped[str] = mapped_column(String(160), default="Nozi")
    provider: Mapped[str] = mapped_column(String(32), default="mock")
    model: Mapped[str] = mapped_column(String(80), default="mock-deterministic")
    mode: Mapped[str] = mapped_column(String(32), default="vulnerable")
    system_instruction: Mapped[str] = mapped_column(Text, default="")
    allowed_tools: Mapped[str] = mapped_column(Text, default="")
    budget: Mapped[float] = mapped_column(Float, default=80.0)
    max_quantity: Mapped[int] = mapped_column(Integer, default=1)
    mock_phase: Mapped[int] = mapped_column(Integer, default=0)
    last_xray_json: Mapped[str] = mapped_column(Text, default="{}")
    last_attempt_json: Mapped[str] = mapped_column(Text, default="{}")
    last_result_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(80), default="idle")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    customer = relationship("Customer", back_populates="agents")
    messages = relationship(
        "ConversationMessage",
        back_populates="agent",
        cascade="all, delete-orphan",
    )
    events = relationship(
        "SecurityEvent",
        back_populates="agent",
        cascade="all, delete-orphan",
    )


class Cart(Base):
    __tablename__ = "carts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="open")
    demo_checked_out: Mapped[bool] = mapped_column(Boolean, default=False)

    customer = relationship("Customer", back_populates="cart")
    items = relationship("CartItem", back_populates="cart", cascade="all, delete-orphan")


class CartItem(Base):
    __tablename__ = "cart_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    cart_id: Mapped[str] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[str] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float)

    cart = relationship("Cart", back_populates="items")
    product = relationship("Product")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agent_instances.id"))
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text, default="")
    tool_name: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    agent = relationship("AgentInstance", back_populates="messages")


class SecurityEvent(Base):
    """Activity-monitor row. Payloads must be sanitized before insert."""

    __tablename__ = "security_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(ForeignKey("agent_instances.id"))
    customer_id: Mapped[str] = mapped_column(String(64), default="")
    actor: Mapped[str] = mapped_column(String(32))
    message: Mapped[str] = mapped_column(Text)
    details: Mapped[str] = mapped_column(Text, default="")
    step: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    agent = relationship("AgentInstance", back_populates="events")


class PendingCheckout(Base):
    """Exact-match confirmation snapshot.

    Checkout is valid only when customer, product, seller, quantity, unit
    price, and total all still match this row. Any change invalidates it.
    """

    __tablename__ = "pending_checkouts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[str] = mapped_column(String(64))
    agent_id: Mapped[str] = mapped_column(String(64), default="")
    product_id: Mapped[str] = mapped_column(String(64))
    seller_id: Mapped[str] = mapped_column(String(64))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    total: Mapped[float] = mapped_column(Float)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryRecord(Base):
    """TODO(STUDENT): RAG / memory poisoning. Placeholder table only."""

    __tablename__ = "memory_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), default="")
    owner_customer_id: Mapped[str] = mapped_column(String(64), default="")
    content: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String(40), default="unknown")
    trust_level: Mapped[str] = mapped_column(String(40), default="untrusted")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MockAttackerRecord(Base):
    """TODO(STUDENT): Mock Attacker Inbox for the exfiltration scenario."""

    __tablename__ = "mock_attacker_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    destination: Mapped[str] = mapped_column(String(200), default="")
    payload: Mapped[str] = mapped_column(Text, default="")
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ToolPermission(Base):
    """TODO(STUDENT): Fine-grained per-agent tool grants."""

    __tablename__ = "tool_permissions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[str] = mapped_column(String(64), default="")
    tool_name: Mapped[str] = mapped_column(String(80), default="")
    allowed: Mapped[bool] = mapped_column(Boolean, default=False)
    reason: Mapped[str] = mapped_column(Text, default="")
