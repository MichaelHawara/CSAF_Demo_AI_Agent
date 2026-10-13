"""Pull the customer's budget and quantity out of their own message.

Nozama no longer stores a preset budget or maximum quantity. The customer says
what they want ("two pairs of running shoes under $200") and the *backend*
reads those limits with plain, deterministic code.

This matters for the security story: the limits must come from the trusted
customer message, never from the model and never from product pages. If the
model parsed them, a poisoned listing could talk it into a bigger number.
Patched mode enforces whatever this module extracts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

DEFAULT_QUANTITY = 1
MAX_PLAUSIBLE_QUANTITY = 50

_NUMBER_WORDS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "a dozen": 12,
    "a couple": 2,
    "a couple of": 2,
}

# "$80", "$1,500.50", "$ 80"
_DOLLAR_SIGN_RE = re.compile(r"\$\s?(\d[\d,]*(?:\.\d{1,2})?)")
# "80 dollars", "80 bucks", "80 USD"
_DOLLAR_WORD_RE = re.compile(r"\b(\d[\d,]*(?:\.\d{1,2})?)\s*(?:dollars?|bucks?|usd)\b", re.IGNORECASE)

_WORDS_ALT = "|".join(sorted((re.escape(w) for w in _NUMBER_WORDS), key=len, reverse=True))
# A quantity is a bare integer or a number word. Integers glued to units
# ("30-hour", "16gb", "15.6 inch") are specs, not quantities.
_QUANTITY_RE = re.compile(
    rf"(?<![\w$.])(?:(?P<digits>\d{{1,3}})(?![\d.,]*\s*(?:-|gb|tb|hour|hours|hr|inch|in\b|\"|%|w\b|mah|k\b))"
    rf"|(?P<word>{_WORDS_ALT}))(?![\w])",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class RequestLimits:
    """What the customer asked for. `budget` is a total in dollars, or None."""

    budget: float | None
    quantity: int
    quantity_stated: bool


def _to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


def parse_budget(text: str) -> float | None:
    matches = [(m.start(), _to_float(m.group(1))) for m in _DOLLAR_SIGN_RE.finditer(text or "")]
    matches += [(m.start(), _to_float(m.group(1))) for m in _DOLLAR_WORD_RE.finditer(text or "")]
    if not matches:
        return None
    value = min(matches, key=lambda pair: pair[0])[1]
    return value if value > 0 else None


def _strip_prices(text: str) -> str:
    text = _DOLLAR_SIGN_RE.sub(" ", text)
    return _DOLLAR_WORD_RE.sub(" ", text)


def parse_quantity(text: str) -> tuple[int, bool]:
    """Return (quantity, stated). A bare "a pair of..." means one."""
    cleaned = _strip_prices(text or "")
    for match in _QUANTITY_RE.finditer(cleaned):
        if match.group("digits"):
            value = int(match.group("digits"))
        else:
            value = _NUMBER_WORDS[match.group("word").lower()]
        if 1 <= value <= MAX_PLAUSIBLE_QUANTITY:
            return value, True
    return DEFAULT_QUANTITY, False


def parse_request_limits(text: str) -> RequestLimits:
    quantity, stated = parse_quantity(text)
    return RequestLimits(budget=parse_budget(text), quantity=quantity, quantity_stated=stated)
