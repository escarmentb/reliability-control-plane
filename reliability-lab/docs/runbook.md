# Runbook: High API Error Rate

## Alert

`HighApiErrorRate` fires when 5xx responses exceed 2 percent for 5 minutes.

## Customer Impact

Order creation may fail or become unreliable.

## Triage

1. Check current API health.

   ```powershell
   curl http://127.0.0.1:8000/health
   ```

2. Check recent SLO state.

   ```powershell
   curl http://127.0.0.1:8000/slo
   ```

3. Check Prometheus for error rate and latency.

   ```promql
   sum(rate(reliability_lab_requests_total{status=~"5.."}[5m]))
   histogram_quantile(0.95, sum(rate(reliability_lab_request_latency_seconds_bucket[5m])) by (le))
   ```

## Mitigation

- Roll back the latest deployment if errors started after a release.
- Scale replicas if latency and CPU saturation are both elevated.
- Disable or reduce controlled `failure_rate` if an authorized fault-injection run caused the alert.

## Follow-Up

- Write a postmortem with timeline, impact, root cause, detection, and prevention.
- Add a regression test or alert if the incident exposed a missing control.
