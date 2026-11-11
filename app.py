
from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
import time
import random

app = FastAPI(title="TP2 DevOps - Product Catalog")

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration"
)

# Simulated product database
products = [
    {"id": 1, "name": "Laptop", "price": 2500},
    {"id": 2, "name": "Mouse", "price": 50},
    {"id": 3, "name": "Keyboard", "price": 120}
]


@app.get("/")
def home():
    REQUEST_COUNT.labels("/", "GET", "200").inc()
    return {"message": "Welcome to the Product Catalog API"}


@app.get("/products")
def get_products():
    REQUEST_COUNT.labels("/products", "GET", "200").inc()
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            REQUEST_COUNT.labels(
                "/products/{product_id}", "GET", "200"
            ).inc()
            return product

    REQUEST_COUNT.labels(
        "/products/{product_id}", "GET", "404"
    ).inc()

    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/checkout")
def checkout():
    start = time.time()

    time.sleep(2)

    duration = time.time() - start
    REQUEST_LATENCY.observe(duration)

    REQUEST_COUNT.labels("/checkout", "GET", "200").inc()

    return {
        "message": "Checkout completed",
        "processing_time": round(duration, 2)
    }


@app.get("/flaky")
def flaky():
    if random.random() < 0.5:
        REQUEST_COUNT.labels("/flaky", "GET", "500").inc()
        raise HTTPException(
            status_code=500,
            detail="Simulated intermittent server error"
        )

    REQUEST_COUNT.labels("/flaky", "GET", "200").inc()
    return {"message": "Request successful"}


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
