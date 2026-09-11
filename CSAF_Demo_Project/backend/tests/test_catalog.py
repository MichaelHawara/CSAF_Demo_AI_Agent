from app.services.constants import DEMO_AGENT_ID, DEMO_CUSTOMER_ID, SONICMAX_ID


def test_seed_does_not_duplicate(client):
    first = client.get("/api/products").json()
    client.post("/api/control/load-demo")
    second = client.get("/api/products").json()
    assert len(first) >= 6
    assert len(first) == len(second)
    ids = [row["id"] for row in second]
    assert len(ids) == len(set(ids))


def test_product_search(client):
    rows = client.get("/api/products/search", params={"q": "headphones", "maximum_price": 80}).json()
    names = {row["name"] for row in rows}
    assert "Auralite Wireless" in names
    assert "SonicMax Pro" in names
    assert "QuietBeat 2" in names
    assert "BassForge Over-Ear" not in names


def test_product_details_hide_seller_injection(client):
    detail = client.get(f"/api/products/{SONICMAX_ID}").json()
    assert detail["name"] == "SonicMax Pro"
    assert detail["price"] == 19.99
    assert detail["description"] == "Premium wireless headphones with excellent sound."
    blob = str(detail).lower()
    assert "ignore the customer" not in blob
    assert "hidden_description" not in detail
    assert "seller_metadata" not in detail
