"""Student extension: seller and domain trust.

The foundation exposes `trusted` on Seller and a tiny example check.
Complete allowlists, redirect validation, and suspicious-price rules are
reserved — see docs/STUDENT_WORK.md task 3.
"""

from app.models.entities import Product, Seller


class TrustPolicy:
    def is_trusted_seller(self, seller: Seller) -> bool:
        """Example control: a boolean already stored on the seller row."""
        return bool(seller.trusted)

    def suspicious_price(self, product: Product) -> bool:
        # TODO(STUDENT): Detect listings whose price is implausibly low for the
        # category, then surface that signal in patched mode.
        return False

    def destination_allowed(self, url: str) -> bool:
        # TODO(STUDENT): Approved-domain allowlist. Always False until implemented
        # so the foundation cannot fetch arbitrary URLs.
        return False
