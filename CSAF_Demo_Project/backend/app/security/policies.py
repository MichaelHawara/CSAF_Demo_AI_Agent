"""Backend authorization for agent-proposed tools.

The model may request any listed tool. This module is the authority for
whether the action is allowed. Prompts are not a control.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.entities import AgentInstance, Product


@dataclass
class PolicyDecision:
    allowed: bool
    reason: str
    code: str


def money(value: float) -> float:
    return round(float(value) + 1e-9, 2)


class SecurityPolicy:
    """Two fully implemented patched-mode controls: budget and confirmation.

    Quantity is enforced alongside budget because the prepared attack is a
    quantity *and* total violation. Content filtering is left to students.

    The limits are not presets. They are the budget and quantity the backend
    parsed out of the customer's own message for the current request
    (``agent.budget`` / ``agent.max_quantity``, 0 meaning "not stated"), and
    they are checked against what the agent has already added *during that
    request* so older cart contents never count against a new request.
    """

    def evaluate_add_to_cart(
        self,
        agent: AgentInstance,
        product: Product,
        quantity: int,
        request_qty: int,
        request_total: float,
    ) -> PolicyDecision:
        """`request_qty` / `request_total`: units and dollars already added this request."""
        if quantity < 1:
            return PolicyDecision(False, "Quantity must be at least 1.", "invalid_quantity")

        attempted_qty = request_qty + quantity
        attempted_total = money(request_total + product.price * quantity)

        if agent.mode != "patched":
            return PolicyDecision(
                True,
                (
                    f"Vulnerable mode does not independently enforce budget or quantity. "
                    f"Attempted quantity={attempted_qty}, attempted total=${attempted_total:.2f}."
                ),
                "vulnerable_allow",
            )

        reasons: list[str] = []
        max_quantity = int(agent.max_quantity or 0)
        budget = float(agent.budget or 0.0)
        if max_quantity and attempted_qty > max_quantity:
            reasons.append(
                f"Quantity {attempted_qty} exceeds the {max_quantity} the customer asked for."
            )
        if budget and attempted_total - 1e-9 > budget:
            reasons.append(
                f"Independent total ${attempted_total:.2f} exceeds the customer's budget ${budget:.2f}."
            )
        if reasons:
            return PolicyDecision(
                False,
                "Quantity and budget violation detected. " + " ".join(reasons),
                "quantity_budget_violation",
            )
        return PolicyDecision(
            True, "Cart change is within the budget and quantity the customer asked for.", "ok"
        )

    def evaluate_customer_data_access(self, agent: AgentInstance) -> PolicyDecision:
        """Profile / order-history lookups. A shopping request does not need them."""
        if agent.mode != "patched":
            return PolicyDecision(
                True,
                "Vulnerable mode lets the assistant read customer account data on request.",
                "vulnerable_data_access",
            )
        return PolicyDecision(
            False,
            "Customer account data is not available to the shopping assistant for a product search.",
            "customer_data_access_denied",
        )

    def evaluate_outbound(self, agent: AgentInstance, destination: str) -> PolicyDecision:
        """Data leaving the app. Nothing the assistant does needs it."""
        if agent.mode != "patched":
            return PolicyDecision(
                True,
                "Vulnerable mode does not restrict where the assistant sends data.",
                "vulnerable_outbound_allow",
            )
        return PolicyDecision(
            False,
            "Sending customer data to an outside destination is not permitted for the shopping assistant.",
            "outbound_denied",
        )

    def evaluate_checkout(
        self,
        agent: AgentInstance,
        *,
        cart_empty: bool,
        confirmed: bool,
    ) -> PolicyDecision:
        if cart_empty:
            return PolicyDecision(False, "Cart is empty.", "empty_cart")
        if agent.mode != "patched":
            return PolicyDecision(
                True,
                "Vulnerable mode allows checkout without customer confirmation.",
                "vulnerable_checkout",
            )
        if not confirmed:
            return PolicyDecision(
                False,
                "Checkout confirmation missing. The agent cannot approve checkout.",
                "confirmation_missing",
            )
        return PolicyDecision(True, "Customer confirmation matches the pending snapshot.", "ok")
