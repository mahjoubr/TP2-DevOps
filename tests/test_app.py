
import app as api
from fastapi.testclient import TestClient

client = TestClient(api.app)


# Test 1: Home endpoint
def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["message"] == "Welcome to the Product Catalog API"


# Test 2: Retrieve all products
def test_get_products():
    response = client.get("/products")
    assert response.status_code == 200
    assert len(response.json()) == 3


# Test 3: Retrieve an existing product
def test_get_existing_product():
    response = client.get("/products/1")
    assert response.status_code == 200
    assert response.json()["name"] == "Laptop"


# Test 4: Retrieve a product that doesn't exist
def test_get_missing_product():
    response = client.get("/products/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


# Test 5: Checkout endpoint
def test_checkout():
    response = client.get("/checkout")
    assert response.status_code == 200
    assert response.json()["message"] == "Checkout completed"
    assert response.json()["processing_time"] >= 2


# Test 6: Flaky endpoint - successful request
def test_flaky_success(monkeypatch):
    monkeypatch.setattr(api.random, "random", lambda: 0.9)

    response = client.get("/flaky")

    assert response.status_code == 200


# Test 7: Flaky endpoint - failed request
def test_flaky_error(monkeypatch):
    monkeypatch.setattr(api.random, "random", lambda: 0.1)

    response = client.get("/flaky")

    assert response.status_code == 500


# Test 8: Prometheus metrics endpoint
def test_metrics():
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
