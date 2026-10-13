"""Pydantic schemas for HTTP APIs and tool arguments.

Tool arguments are validated here before any executor runs a handler. That
prevents free-form model output from becoming arbitrary Python calls.
"""

from typing import Any, Literal

from pydantic import BaseModel, Field


class ProductPublic(BaseModel):
    id: str
    name: str
    seller_id: str
    seller_name: str
    trusted_seller: bool
    price: float
    rating: float
    review_count: int
    description: str
    category: str
    accent: str
    image_alt_text_public: str = ""
    url: str = ""


class ReviewPublic(BaseModel):
    id: str
    author: str
    rating: float
    body: str


class ProductDetailPublic(ProductPublic):
    reviews: list[ReviewPublic] = Field(default_factory=list)


class CartItemPublic(BaseModel):
    id: str
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    line_total: float
    image_url: str = ""


class CartPublic(BaseModel):
    id: str
    customer_id: str
    status: str
    demo_checked_out: bool
    items: list[CartItemPublic]
    total: float
    quantity: int


class AgentCreate(BaseModel):
    display_name: str = "Alex"
    customer_id: str | None = None
    # None -> follow AGENT_PROVIDER from the environment.
    provider: Literal["mock", "gemini"] | None = None
    mode: Literal["vulnerable", "patched"] = "vulnerable"
    system_instruction: str | None = None


class AgentPatch(BaseModel):
    display_name: str | None = None
    provider: Literal["mock", "gemini"] | None = None
    mode: Literal["vulnerable", "patched"] | None = None
    system_instruction: str | None = None
    model: str | None = None


class AgentPublic(BaseModel):
    id: str
    customer_id: str
    display_name: str
    provider: str
    model: str
    mode: str
    system_instruction: str
    allowed_tools: list[str]
    # Limits detected in the customer's latest message (None until one is sent
    # or when the customer did not state a budget). Never configured by hand.
    detected_budget: float | None = None
    detected_quantity: int | None = None
    status: str
    created_at: str
    gemini_available: bool = False
    provider_note: str = ""


class MessageCreate(BaseModel):
    content: str


class ConversationMessagePublic(BaseModel):
    id: str
    role: str
    content: str
    tool_name: str
    created_at: str
    # Structured extras shown under the message, e.g. {"products": [...], "quantity": 2}.
    attachments: dict[str, Any] | None = None


class SecurityEventPublic(BaseModel):
    id: str
    actor: str
    message: str
    details: str
    step: int
    created_at: str
    formatted: str


class CheckoutRequestBody(BaseModel):
    customer_id: str
    agent_id: str | None = None


class CheckoutConfirmBody(BaseModel):
    pending_id: str
    customer_id: str
    product_id: str
    seller_id: str
    quantity: int
    unit_price: float
    total: float


class AddCartItemBody(BaseModel):
    product_id: str
    quantity: int = 1
    agent_id: str | None = None


class UpdateCartItemBody(BaseModel):
    quantity: int


class CheckoutApproveBody(BaseModel):
    customer_id: str
    agent_id: str | None = None


class SearchProductsArgs(BaseModel):
    query: str
    maximum_price: float | None = None


class ReadProductPageArgs(BaseModel):
    product_id: str


class GetProductDetailsArgs(BaseModel):
    product_id: str


class AddToCartArgs(BaseModel):
    product_id: str
    quantity: int = 1


class ViewCartArgs(BaseModel):
    pass


class RequestCheckoutArgs(BaseModel):
    pass


class GetCustomerProfileArgs(BaseModel):
    """TODO(STUDENT): used by the private-data task."""


class GetPurchaseHistoryArgs(BaseModel):
    """TODO(STUDENT): used by the private-data task."""


class SendRequestArgs(BaseModel):
    """Submit data to an endpoint. In this demo the only endpoint is a local, in-process sink."""

    destination: str = ""
    data: str = ""


class SendCouponRequestArgs(BaseModel):
    """TODO(STUDENT): local mock coupon endpoint only."""

    destination: str = ""
    note: str = ""


class StoreMemoryArgs(BaseModel):
    """TODO(STUDENT): RAG / memory poisoning."""

    content: str = ""
    source: str = "unknown"


class SearchMemoryArgs(BaseModel):
    """TODO(STUDENT): RAG / memory poisoning."""

    query: str = ""


class ProposedToolCall(BaseModel):
    name: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentTurnResult(BaseModel):
    assistant_text: str | None = None
    tool_calls: list[ProposedToolCall] = Field(default_factory=list)
    provider: str = "mock"


class ToolExecutionResult(BaseModel):
    ok: bool
    tool: str
    data: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    blocked: bool = False
    policy_decision: str | None = None
