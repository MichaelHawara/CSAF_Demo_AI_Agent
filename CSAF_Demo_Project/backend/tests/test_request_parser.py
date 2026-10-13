import pytest

from app.services.request_parser import parse_budget, parse_quantity, parse_request_limits


@pytest.mark.parametrize(
    ("text", "budget"),
    [
        ("Find me headphones for no more than $80", 80.0),
        ("under $1,500 please", 1500.0),
        ("my budget is $24.99", 24.99),
        ("I can spend 60 dollars", 60.0),
        ("around 45 bucks", 45.0),
        ("Find me a laptop", None),
        ("Find me 2 laptops", None),
    ],
)
def test_parse_budget(text, budget):
    assert parse_budget(text) == budget


@pytest.mark.parametrize(
    ("text", "quantity", "stated"),
    [
        ("Find me one pair of running shoes for $150", 1, True),
        ("I need two pairs of running shoes under $300", 2, True),
        ("Get me 3 water bottles", 3, True),
        ("Find me a pair of wireless headphones", 1, False),
        ("Add a laptop to my cart", 1, False),
        ("a couple of shirts please", 2, True),
        # Prices and specs are not quantities.
        ("Find a laptop under $1000", 1, False),
        ("a 16gb laptop under 900 dollars", 1, False),
        ("headphones with a 30-hour battery", 1, False),
        # Implausible counts fall back to the default.
        ("I want 500 chargers", 1, False),
    ],
)
def test_parse_quantity(text, quantity, stated):
    assert parse_quantity(text) == (quantity, stated)


def test_limits_bundle_budget_and_quantity():
    limits = parse_request_limits("I need two shirts for under $90 total.")
    assert limits.quantity == 2
    assert limits.budget == 90.0
    assert limits.quantity_stated is True


def test_limits_default_to_one_item_and_no_budget():
    limits = parse_request_limits("Show me something nice")
    assert limits.quantity == 1
    assert limits.budget is None
    assert limits.quantity_stated is False
