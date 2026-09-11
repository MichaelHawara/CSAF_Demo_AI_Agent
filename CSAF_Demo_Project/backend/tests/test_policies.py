from app.database import get_session_factory
from app.models.entities import AgentInstance, Product
from app.security.policies import SecurityPolicy
from app.services.constants import DEMO_AGENT_ID, SONICMAX_ID


def test_patched_cart_rejects_total_above_budget(client):
    db = get_session_factory()()
    try:
        agent = db.get(AgentInstance, DEMO_AGENT_ID)
        agent.mode = "patched"
        agent.budget = 80.0
        agent.max_quantity = 1
        product = db.get(Product, SONICMAX_ID)
        decision = SecurityPolicy().evaluate_add_to_cart(agent, product, 5, 0, 0.0)
    finally:
        db.close()
    assert decision.allowed is False
    assert "99.95" in decision.reason
    assert "80.00" in decision.reason


def test_vulnerable_cart_allows_over_budget(client):
    db = get_session_factory()()
    try:
        agent = db.get(AgentInstance, DEMO_AGENT_ID)
        agent.mode = "vulnerable"
        product = db.get(Product, SONICMAX_ID)
        decision = SecurityPolicy().evaluate_add_to_cart(agent, product, 5, 0, 0.0)
    finally:
        db.close()
    assert decision.allowed is True
