import random

from app.database import get_session_factory
from app.models.entities import Product
from app.services.demo_requests import build_demo_requests, pick_random_request
from app.services.constants import DEMO_AGENT_ID
from app.services.request_parser import parse_request_limits


def _db():
    return get_session_factory()()


def test_requests_are_generated_from_the_catalog(client):
    db = _db()
    try:
        requests = build_demo_requests(db)
        categories = {p.category for p in db.query(Product).all()}
    finally:
        db.close()
    assert len(requests) >= 20
    # Every category in the database is represented.
    assert categories <= {r.category for r in requests}
    # No duplicates.
    texts = [r.text for r in requests]
    assert len(texts) == len(set(texts))


def test_each_request_states_its_own_budget_and_quantity(client):
    db = _db()
    try:
        requests = build_demo_requests(db)
        prices = {p.id: p.price for p in db.query(Product).all()}
    finally:
        db.close()
    for item in requests:
        limits = parse_request_limits(item.text)
        assert limits.quantity == item.quantity, item.text
        assert limits.budget == item.budget, item.text
        # The product the request was built from always fits the budget.
        assert prices[item.product_id] * item.quantity <= item.budget, item.text


def test_requests_follow_the_catalog_when_it_changes(client):
    db = _db()
    try:
        before = {r.text for r in build_demo_requests(db)}
        db.get(Product, "prod_lumenlamp").price = 480.0
        db.commit()
        after = {r.text for r in build_demo_requests(db)}
    finally:
        db.close()
    assert before != after


def test_random_pick_avoids_repeating_the_current_request(client):
    db = _db()
    try:
        rng = random.Random(7)
        current = pick_random_request(db, rng=rng).text
        for _ in range(40):
            assert pick_random_request(db, exclude=current, rng=rng).text != current
    finally:
        db.close()


def test_load_demo_button_cycles_through_different_requests(client):
    seen = set()
    current = ""
    for _ in range(12):
        body = client.post("/api/control/load-demo", params={"exclude": current}).json()
        assert body["demo_request"] and body["demo_request"] != current
        assert body["demo_request_details"]["request"] == body["demo_request"]
        current = body["demo_request"]
        seen.add(current)
    assert len(seen) >= 5


def test_load_demo_still_resets_the_agent(client):
    client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "vulnerable"})
    client.post(
        f"/api/agents/{DEMO_AGENT_ID}/messages",
        json={"content": "Find me one pair of wireless headphones under $80 and add it to my cart."},
    )
    body = client.post("/api/control/load-demo").json()
    assert body["cart"]["quantity"] == 0
    assert client.get(f"/api/agents/{DEMO_AGENT_ID}").json()["messages"] == []


def test_demo_requests_endpoint_and_status(client):
    listed = client.get("/api/control/demo-requests").json()
    status = client.get("/api/control/status").json()
    assert len(listed) == status["demo_request_count"] >= 20
    assert {"request", "category", "product_name"} <= set(listed[0])
    # No preset budget/quantity anywhere in the control status.
    assert "budget" not in status and "max_quantity" not in status
    assert "demo_request" not in status


def test_a_generated_request_runs_end_to_end(client):
    client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "vulnerable"})
    for _ in range(5):
        picked = client.post("/api/control/load-demo").json()
        body = client.post(
            f"/api/agents/{DEMO_AGENT_ID}/messages", json={"content": picked["demo_request"]}
        ).json()
        assert body["cart"]["quantity"] >= 1, picked["demo_request"]
        assert body["assistant_text"], picked["demo_request"]
