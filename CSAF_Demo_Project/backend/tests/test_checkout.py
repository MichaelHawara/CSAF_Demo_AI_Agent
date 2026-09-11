from app.services.constants import DEMO_AGENT_ID, DEMO_CUSTOMER_ID, SONICMAX_ID


def _patched_pending(client):
    client.post("/api/control/reset-demo")
    client.patch(f"/api/agents/{DEMO_AGENT_ID}", json={"mode": "patched"})
    # Human UI path: add a legal quantity, then request checkout.
    client.post(
        f"/api/cart/{DEMO_CUSTOMER_ID}/items",
        json={"product_id": SONICMAX_ID, "quantity": 1, "agent_id": DEMO_AGENT_ID},
    )
    return client.post(
        "/api/checkout/request",
        json={"customer_id": DEMO_CUSTOMER_ID, "agent_id": DEMO_AGENT_ID},
    ).json()


def test_patched_checkout_requires_confirmation(client):
    payload = _patched_pending(client)
    assert payload["allowed"] is False
    assert payload["confirmation_received"] is False
    assert payload["pending"] is not None
    cart = client.get(f"/api/cart/{DEMO_CUSTOMER_ID}").json()
    assert cart["demo_checked_out"] is False


def test_confirmation_is_tied_to_exact_details(client):
    payload = _patched_pending(client)
    pending = payload["pending"]
    bad = client.post(
        "/api/checkout/confirm",
        json={
            "pending_id": pending["id"],
            "customer_id": pending["customer_id"],
            "product_id": pending["product_id"],
            "seller_id": pending["seller_id"],
            "quantity": pending["quantity"] + 4,
            "unit_price": pending["unit_price"],
            "total": 99.95,
        },
    )
    assert bad.status_code == 400

    good = client.post(
        "/api/checkout/confirm",
        json={
            "pending_id": pending["id"],
            "customer_id": pending["customer_id"],
            "product_id": pending["product_id"],
            "seller_id": pending["seller_id"],
            "quantity": pending["quantity"],
            "unit_price": pending["unit_price"],
            "total": pending["total"],
        },
    )
    assert good.status_code == 200
    body = good.json()
    assert body["confirmation_received"] is True
    assert "Demo transaction only" in body["message"]
