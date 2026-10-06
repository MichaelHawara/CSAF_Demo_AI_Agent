from app.services.constants import DEMO_AGENT_ID, DEMO_CUSTOMER_ID, SONICMAX_ID


def test_reset_clears_cart_and_conversation(client):
    client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "vulnerable"})
    client.post(
        f"/api/agents/{DEMO_AGENT_ID}/messages",
        json={"content": "Find wireless headphones under $80"},
    )
    cart = client.get(f"/api/cart/{DEMO_CUSTOMER_ID}").json()
    assert cart["quantity"] == 5
    client.post(f"/api/agents/{DEMO_AGENT_ID}/reset")
    cart = client.get(f"/api/cart/{DEMO_CUSTOMER_ID}").json()
    assert cart["quantity"] == 0
    detail = client.get(f"/api/agents/{DEMO_AGENT_ID}").json()
    assert detail["messages"] == []
    events = client.get(f"/api/agents/{DEMO_AGENT_ID}/events").json()
    assert events == []


def test_backend_startup_clears_demo_conversation(client):
    from fastapi.testclient import TestClient

    from app.main import app

    client.post(
        f"/api/agents/{DEMO_AGENT_ID}/messages",
        json={"content": "Find wireless headphones"},
    )

    with TestClient(app) as restarted_client:
        detail = restarted_client.get(f"/api/agents/{DEMO_AGENT_ID}").json()
        events = restarted_client.get(f"/api/agents/{DEMO_AGENT_ID}/events").json()

    assert detail["messages"] == []
    assert events == []
    assert detail["display_name"] == "Alex"
    assert detail["system_instruction"].startswith("You are Alex,")


def test_backend_startup_migrates_legacy_product_schema(client):
    from fastapi.testclient import TestClient
    from sqlalchemy import text

    from app.database import get_engine
    from app.main import app

    with get_engine().begin() as connection:
        connection.execute(text("ALTER TABLE products DROP COLUMN url"))

    with TestClient(app) as restarted_client:
        response = restarted_client.get("/api/products")

    assert response.status_code == 200


def test_delete_removes_agent_owned_records(client):
    created = client.post(
        "/api/agents",
        json={"display_name": "Temp Nozi", "mode": "vulnerable", "provider": "mock"},
    ).json()
    agent_id = created["id"]
    client.post(
        f"/api/agents/{agent_id}/messages",
        json={"content": "Find wireless headphones under $80"},
    )
    deleted = client.delete(f"/api/agents/{agent_id}")
    assert deleted.status_code == 200
    missing = client.get(f"/api/agents/{agent_id}")
    assert missing.status_code == 404
    events = client.get(f"/api/agents/{agent_id}/events")
    assert events.status_code == 404
