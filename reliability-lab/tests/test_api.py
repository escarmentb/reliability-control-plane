from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_order_success_updates_slo() -> None:
    response = client.post("/orders/order-1001?failure_rate=0&latency_ms=0")

    assert response.status_code == 200
    assert response.json()["status"] == "accepted"

    slo = client.get("/slo").json()
    assert slo["total_requests"] >= 1
    assert slo["availability"] <= 1.0


def test_metrics_endpoint_exposes_prometheus_text() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    assert "reliability_lab_requests_total" in response.text
