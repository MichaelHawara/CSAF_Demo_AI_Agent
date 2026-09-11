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
    """

    def evaluate_add_to_cart(
        self,
        agent: AgentInstance,
        product: Product,
        quantity: int,
        current_qty: int,
        current_total: float,
    ) -> PolicyDecision:
        if quantity < 1:
            return PolicyDecision(False, "Quantity must be at least 1.", "invalid_quantity")

        attempted_qty = current_qty + quantity
        attempted_total = money(current_total + product.price * quantity)

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
        if attempted_qty > agent.max_quantity:
            reasons.append(
                f"Quantity {attempted_qty} exceeds allowed maximum {agent.max_quantity}."
            )
        if attempted_total - 1e-9 > agent.budget:
            reasons.append(
                f"Independent total ${attempted_total:.2f} exceeds budget ${agent.budget:.2f}."
            )
        if reasons:
            return PolicyDecision(
                False,
                "Quantity and budget violation detected. " + " ".join(reasons),
                "quantity_budget_violation",
            )
        return PolicyDecision(True, "Cart change is within stored budget and quantity.", "ok")

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
