# Architecture

Reliability Lab is intentionally small, but shaped like a real service.

## Components

- FastAPI service exposes health, order processing, controlled fault injection, SLO, and Prometheus metrics endpoints.
- Prometheus scrapes `/metrics` and evaluates alert rules.
- Kubernetes manifests define deployment, probes, resource requests, and a service.
- Terraform creates the namespace foundation for cluster deployment.
- GitHub Actions runs linting and tests on every push.

## SRE Signals

- Latency: `reliability_lab_request_latency_seconds`
- Traffic: `reliability_lab_requests_total`
- Errors: `reliability_lab_requests_total{status=~"5.."}`
- Saturation: Kubernetes CPU and memory requests/limits are defined for extension with cluster metrics.
