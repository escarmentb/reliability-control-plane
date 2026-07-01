from __future__ import annotations

import random
import time
from typing import Annotated

from fastapi import FastAPI, Query, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

from app.reliability import InMemoryReliabilityStore

app = FastAPI(
    title="Reliability Control Plane",
    description="Operational API for order processing, service health, metrics, and SLO enforcement.",
    version="0.1.0",
)

REQUEST_COUNT = Counter(
    "reliability_lab_requests_total",
    "Total API requests by endpoint and status.",
    ["endpoint", "status"],
)
REQUEST_LATENCY = Histogram(
    "reliability_lab_request_latency_seconds",
    "API request latency by endpoint.",
    ["endpoint"],
)

store = InMemoryReliabilityStore()


class HealthResponse(BaseModel):
    status: str
    version: str
    dependency_status: str = Field(description="Current downstream dependency state.")


class OrderResponse(BaseModel):
    order_id: str
    status: str
    processing_ms: int


class SloResponse(BaseModel):
    objective: float
    availability: float
    successful_requests: int
    total_requests: int
    error_budget_remaining: float
    is_burning_budget: bool


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "reliability-lab", "docs": "/docs", "health": "/health", "metrics": "/metrics"}


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    REQUEST_COUNT.labels(endpoint="/health", status="200").inc()
    return HealthResponse(status="ok", version=app.version, dependency_status="ok")


@app.post("/orders/{order_id}", response_model=OrderResponse)
def create_order(
    order_id: str,
    failure_rate: Annotated[
        float,
        Query(ge=0.0, le=1.0, description="Controlled fault-injection probability."),
    ] = 0.0,
    latency_ms: Annotated[
        int,
        Query(ge=0, le=3000, description="Controlled downstream delay in milliseconds."),
    ] = 25,
) -> OrderResponse:
    start = time.perf_counter()
    time.sleep(latency_ms / 1000)

    if random.random() < failure_rate:
        store.record_failure()
        REQUEST_COUNT.labels(endpoint="/orders/{order_id}", status="503").inc()
        REQUEST_LATENCY.labels(endpoint="/orders/{order_id}").observe(time.perf_counter() - start)
        return Response(status_code=503)

    store.record_success()
    REQUEST_COUNT.labels(endpoint="/orders/{order_id}", status="200").inc()
    REQUEST_LATENCY.labels(endpoint="/orders/{order_id}").observe(time.perf_counter() - start)
    return OrderResponse(order_id=order_id, status="accepted", processing_ms=latency_ms)


@app.get("/slo", response_model=SloResponse)
def slo() -> SloResponse:
    snapshot = store.snapshot()
    REQUEST_COUNT.labels(endpoint="/slo", status="200").inc()
    return SloResponse(
        objective=snapshot.objective,
        availability=snapshot.availability,
        successful_requests=snapshot.successful_requests,
        total_requests=snapshot.total_requests,
        error_budget_remaining=snapshot.error_budget_remaining,
        is_burning_budget=snapshot.is_burning_budget,
    )


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
