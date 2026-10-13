from app.database import get_session_factory
from app.models.entities import AgentInstance, Product
from app.security.policies import SecurityPolicy
from app.services.constants import DEMO_AGENT_ID, SONICMAX_ID


def _agent_and_product(db, mode, budget, quantity):
    agent = db.get(AgentInstance, DEMO_AGENT_ID)
    agent.mode = mode
    # Limits the backend parsed from the customer's message for this request.
    agent.budget = budget
    agent.max_quantity = quantity
    return agent, db.get(Product, SONICMAX_ID)


def test_patched_cart_rejects_total_above_budget(client):
    db = get_session_factory()()
    try:
        agent, product = _agent_and_product(db, "patched", 80.0, 1)
        decision = SecurityPolicy().evaluate_add_to_cart(agent, product, 5, 0, 0.0)
    finally:
        db.close()
    assert decision.allowed is False
    assert "99.95" in decision.reason
    assert "80.00" in decision.reason


def test_patched_counts_what_was_already_added_this_request(client):
    db = get_session_factory()()
    try:
        agent, product = _agent_and_product(db, "patched", 0.0, 2)
        policy = SecurityPolicy()
        assert policy.evaluate_add_to_cart(agent, product, 1, 1, product.price).allowed is True
        assert policy.evaluate_add_to_cart(agent, product, 2, 1, product.price).allowed is False
    finally:
        db.close()


def test_patched_without_a_stated_budget_only_limits_quantity(client):
    db = get_session_factory()()
    try:
        agent, product = _agent_and_product(db, "patched", 0.0, 3)
        decision = SecurityPolicy().evaluate_add_to_cart(agent, product, 3, 0, 0.0)
    finally:
        db.close()
    assert decision.allowed is True


def test_vulnerable_cart_allows_over_budget(client):
    db = get_session_factory()()
    try:
        agent, product = _agent_and_product(db, "vulnerable", 80.0, 1)
        decision = SecurityPolicy().evaluate_add_to_cart(agent, product, 5, 0, 0.0)
    finally:
        db.close()
    assert decision.allowed is True
