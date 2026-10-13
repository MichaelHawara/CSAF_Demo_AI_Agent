"""Synthetic customer data for the security demo.

Everything returned here is randomly generated from small lists of made-up
parts. None of it describes a real person: names are invented, e-mail uses the
reserved ".invalid" TLD, phone numbers use the fictional 555-01xx block,
addresses use a placeholder town and ZIP, and the "payment method" is only a
label with random digits. Nothing is read from, or written to, any real system.
"""

from __future__ import annotations

import random
from typing import Any

_FIRST = ["Maya", "Jonas", "Priya", "Tobias", "Lena", "Mateo", "Noor", "Elias", "Sana", "Felix"]
_LAST = ["Okafor", "Lindqvist", "Marchetti", "Haddad", "Ferreira", "Nakamura", "Albrecht", "Quinn"]
_STREETS = ["Maple Ave", "Harbor Lane", "Cedar Court", "Willow Street", "Juniper Road", "Orchard Way"]
_ORDER_ITEMS = [
    ("Notebook set", 14.50),
    ("Desk organizer", 22.00),
    ("Ceramic mug", 11.25),
    ("Phone stand", 17.80),
    ("Reusable tote", 9.90),
]

SYNTHETIC_NOTICE = "Synthetic data generated for the demo. No real person is described."


def generate_customer_record(rng: random.Random | None = None) -> dict[str, Any]:
    """A fresh, fictional customer profile."""
    rng = rng or random
    first, last = rng.choice(_FIRST), rng.choice(_LAST)
    return {
        "full_name": f"{first} {last}",
        "email": f"{first}.{last}{rng.randint(10, 99)}@example.invalid".lower(),
        "phone": f"555-01{rng.randint(0, 99):02d}",
        "shipping_address": (
            f"{rng.randint(100, 9999)} {rng.choice(_STREETS)}, Demoville, ZZ 00000"
        ),
        "date_of_birth": f"{rng.randint(1970, 2004)}-{rng.randint(1, 12):02d}-{rng.randint(1, 28):02d}",
        "payment_method": f"Demo Visa ending {rng.randint(0, 9999):04d}",
        "loyalty_id": f"DEMO-{rng.randint(100000, 999999)}",
    }


def generate_order_history(rng: random.Random | None = None) -> list[dict[str, Any]]:
    """A few fictional past orders."""
    rng = rng or random
    orders = []
    for index in range(rng.randint(2, 3)):
        name, price = rng.choice(_ORDER_ITEMS)
        orders.append(
            {
                "order_id": f"DEMO-ORD-{rng.randint(1000, 9999)}",
                "item": name,
                "quantity": rng.randint(1, 3),
                "unit_price": price,
            }
        )
    return orders


def summarize_record(record: dict[str, Any]) -> str:
    """One readable line for the monitor."""
    return "; ".join(f"{key}={value}" for key, value in record.items())
