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


def _add(client, product_id, quantity):
    return client.post(
        f"/api/cart/{DEMO_CUSTOMER_ID}/items",
        json={"product_id": product_id, "quantity": quantity, "agent_id": DEMO_AGENT_ID},
    ).json()


def test_cart_quantity_can_be_adjusted_and_items_removed(client):
    client.post("/api/control/reset-demo")
    cart = _add(client, "hydroflow_bottle", 1)
    item = cart["items"][0]
    assert item["image_url"]

    cart = client.patch(
        f"/api/cart/{DEMO_CUSTOMER_ID}/items/{item['id']}", json={"quantity": 3}
    ).json()
    assert cart["items"][0]["quantity"] == 3

    bad = client.patch(f"/api/cart/{DEMO_CUSTOMER_ID}/items/{item['id']}", json={"quantity": 0})
    assert bad.status_code == 400

    cart = client.delete(f"/api/cart/{DEMO_CUSTOMER_ID}/items/{item['id']}").json()
    assert cart["items"] == []


def test_approve_checkout_totals_empties_cart_and_stores_receipt(client):
    client.post("/api/control/reset-demo")
    _add(client, "hydroflow_bottle", 2)  # 2 x 24.99 = 49.98 (free shipping)
    _add(client, "aquavault_bottle", 1)  # 21.50

    response = client.post(
        "/api/checkout/approve", json={"customer_id": DEMO_CUSTOMER_ID, "agent_id": DEMO_AGENT_ID}
    )
    assert response.status_code == 200
    receipt = response.json()["receipt"]
    assert receipt["item_count"] == 3
    assert receipt["subtotal"] == 71.48
    assert receipt["shipping"] == 0
    assert receipt["tax"] == round(71.48 * 0.08, 2)
    assert receipt["total"] == round(receipt["subtotal"] + receipt["tax"], 2)
    assert receipt["real_purchase"] is False
    assert {line["quantity"] for line in receipt["items"]} == {2, 1}

    assert client.get(f"/api/cart/{DEMO_CUSTOMER_ID}").json()["items"] == []
    detail = client.get(f"/api/agents/{DEMO_AGENT_ID}").json()
    assert detail["checkout_receipt"]["order_id"] == receipt["order_id"]

    client.post("/api/control/reset-demo")
    assert client.get(f"/api/agents/{DEMO_AGENT_ID}").json()["checkout_receipt"] is None


def test_approve_checkout_rejects_an_empty_cart(client):
    client.post("/api/control/reset-demo")
    response = client.post(
        "/api/checkout/approve", json={"customer_id": DEMO_CUSTOMER_ID, "agent_id": DEMO_AGENT_ID}
    )
    assert response.status_code == 400
