import json
import logging
import os
import random
import sys
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from prometheus_client import Counter, Histogram, generate_latest

# ---------- OpenTelemetry tracing ----------
provider = TracerProvider(
    resource=Resource.create({"service.name": os.getenv("OTEL_SERVICE_NAME", "catalog")})
)
if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):  # pragma: no cover
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)


# ---------- Structured JSON logs with trace correlation ----------
class JsonFormatter(logging.Formatter):
    FIELDS = ("http_method", "http_path", "http_status", "duration_ms")

    def format(self, record):
        ctx = trace.get_current_span().get_span_context()
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "trace_id": format(ctx.trace_id, "032x") if ctx.is_valid else None,
            "span_id": format(ctx.span_id, "016x") if ctx.is_valid else None,
        }
        for field in self.FIELDS:
            if hasattr(record, field):
                payload[field] = getattr(record, field)
        return json.dumps(payload)


logger = logging.getLogger("catalog")
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JsonFormatter())
logger.addHandler(_handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# ---------- Prometheus metrics ----------
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["endpoint", "method", "status"]
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration",
    ["endpoint"],
    buckets=(0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10)
)

app = FastAPI(title="TP2 DevOps - Product Catalog")


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    start = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        route = request.scope.get("route")
        endpoint = route.path if route else "unmatched"
        if endpoint != "/metrics":
            duration = time.perf_counter() - start
            REQUEST_COUNT.labels(endpoint, request.method, str(status)).inc()
            REQUEST_LATENCY.labels(endpoint).observe(duration)
            logger.info(
                "request",
                extra={
                    "http_method": request.method,
                    "http_path": endpoint,
                    "http_status": status,
                    "duration_ms": round(duration * 1000, 1),
                },
            )


FastAPIInstrumentor.instrument_app(app, excluded_urls="metrics")

# Simulated product database
products = [
    {"id": 1, "name": "Laptop", "price": 2500},
    {"id": 2, "name": "Mouse", "price": 50},
    {"id": 3, "name": "Keyboard", "price": 120}
]


@app.get("/")
def home():
    return {"message": "Welcome to the Product Catalog API"}


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/checkout")
def checkout():
    start = time.time()

    time.sleep(2)

    duration = time.time() - start

    return {
        "message": "Checkout completed",
        "processing_time": round(duration, 2)
    }


@app.get("/flaky")
def flaky():
    if random.random() < 0.5:
        raise HTTPException(
            status_code=500,
            detail="Simulated intermittent server error"
        )

    return {"message": "Request successful"}


@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
