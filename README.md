[README.md](https://github.com/user-attachments/files/29563114/README.md)
# Reliability Control Plane

Reliability Control Plane provides order-processing health checks, Prometheus telemetry, service-level objective tracking, and controlled fault injection. The repository includes container orchestration, Kubernetes deployment resources, infrastructure definitions, CI enforcement, and incident-response documentation.

## Service Responsibilities

- Accept and track order-processing requests.
- Publish health and Prometheus RED metrics.
- Calculate current availability against a 99.5% SLO.
- Expose controlled failure and latency injection for pre-production validation.
- Support repeatable deployment through Docker, Kubernetes, and Terraform.

## Local Startup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Endpoints:

- API documentation: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health
- Metrics: http://127.0.0.1:8000/metrics
- SLO status: http://127.0.0.1:8000/slo

## Container Stack

```powershell
docker compose -f infra/docker/docker-compose.yml up --build
```

Services:

- Reliability API: http://127.0.0.1:8000
- Prometheus: http://127.0.0.1:9090

## Verification

```powershell
pytest
```

## Repository Structure

```text
app/                    Service implementation
tests/                  Unit and API verification
infra/docker/           Local orchestration and Prometheus configuration
infra/k8s/              Kubernetes deployment resources
infra/terraform/        Infrastructure definitions
docs/                   Architecture and operational runbooks
.github/workflows/      CI quality gates
```

## Production Readiness Roadmap

1. Add Grafana dashboards for latency, traffic, errors, and saturation.
2. Run synthetic health checks from multiple regions.
3. Restrict fault-injection parameters to authorized non-production environments.
4. Add durable SLO storage and multi-window burn-rate alerts.
5. Export distributed traces through OpenTelemetry.
