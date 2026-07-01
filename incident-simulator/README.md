# Incident Validation Service

Incident Validation Service runs controlled reliability checks against the [Reliability Control Plane](../reliability-lab/README.md). It verifies retry and circuit-breaker behavior across baseline, degraded, and recovery phases, then emits machine-readable and human-readable evidence for release approval and incident-readiness reviews.

## Operational Responsibilities

- Validate availability during controlled dependency degradation.
- Measure median and tail latency across incident phases.
- Confirm circuit-breaker activation and service recovery.
- Produce JSON results for CI quality gates.
- Produce an HTML report for release and reliability reviews.

## Run A Validation

Start Reliability Control Plane in one terminal:

```powershell
cd ..\reliability-lab
.\.venv\Scripts\python.exe -m uvicorn app.main:app
```

Run the validation from another terminal:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\incident-sim.exe --requests 20
```

The command writes `reports/incident-report.json` and `reports/incident-report.html`.

## Validation Phases

1. `baseline`: verifies normal availability and latency.
2. `incident`: injects an 80% dependency failure rate and elevated latency.
3. `recovery`: removes injected faults and verifies service restoration.

Retries can improve request success at the cost of latency and downstream load. The circuit breaker limits pressure during sustained dependency failure. Review the generated report together with the control plane's `/slo` and `/metrics` endpoints before approving a release.

## Planned Controls

- Export OpenTelemetry traces for each validation phase.
- Run automatically against ephemeral release environments.
- Reject releases when recovery availability or P95 latency violates policy.
- Archive signed reports with deployment metadata and source revisions.
