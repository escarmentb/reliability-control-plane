from pathlib import Path

from incident_simulator.core import Attempt, CircuitBreaker, Phase, run_phase, summarize, write_reports


def test_circuit_breaker_opens_and_recovers() -> None:
    breaker = CircuitBreaker(failure_threshold=2, recovery_seconds=5)
    breaker.record(False, now=10)
    breaker.record(False, now=11)
    assert not breaker.allow(now=12)
    assert breaker.allow(now=16)


def test_run_phase_retries_then_succeeds() -> None:
    statuses = iter([503, 200])

    def transport(url: str, timeout: float) -> tuple[int, float]:
        return next(statuses), 10.0

    results = run_phase("http://service", Phase("test", 1, 0, 0), CircuitBreaker(), transport=transport)
    assert results[0].success
    assert results[0].retries == 1
    assert results[0].latency_ms == 20.0


def test_summary_and_reports(tmp_path: Path) -> None:
    results = [Attempt("baseline", True, 200, 10, 0), Attempt("incident", False, 503, 30, 2)]
    summary = summarize(results)
    assert summary["availability"] == 0.5
    assert summary["failures"] == 1
    assert summary["retry_rate"] == 1.0
    assert summary["p95_ms"] == 30
    json_path, html_path = write_reports(results, tmp_path)
    assert json_path.exists()
    assert "50.0%" in html_path.read_text(encoding="utf-8")
