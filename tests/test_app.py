import json
import logging

import app as api
from fastapi.testclient import TestClient
from opentelemetry import trace

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


# Test 9: Unknown routes use a bounded label (no cardinality explosion)
def test_unknown_route_label():
    response = client.get("/does-not-exist")
    assert response.status_code == 404
    assert 'endpoint="unmatched"' in client.get("/metrics").text


# Test 10: Metrics are labelled per endpoint and expose the 200 ms bucket
def test_metrics_have_endpoint_labels():
    client.get("/products")
    text = client.get("/metrics").text
    assert 'http_requests_total{endpoint="/products",method="GET",status="200"}' in text
    assert 'le="0.2"' in text


# Test 11: Failed requests are counted with their 5xx status
def test_flaky_error_is_counted(monkeypatch):
    monkeypatch.setattr(api.random, "random", lambda: 0.1)
    client.get("/flaky")
    assert 'endpoint="/flaky",method="GET",status="500"' in client.get("/metrics").text


# Test 12: JSON logs carry trace_id and span_id inside a span, null outside
def test_json_log_contains_trace_id():
    tracer = trace.get_tracer("test")
    record = logging.LogRecord("catalog", logging.INFO, __file__, 1, "hello", None, None)
    with tracer.start_as_current_span("unit-test"):
        inside = json.loads(api.JsonFormatter().format(record))
    outside = json.loads(api.JsonFormatter().format(record))
    assert inside["message"] == "hello"
    assert len(inside["trace_id"]) == 32
    assert len(inside["span_id"]) == 16
    assert outside["trace_id"] is None
