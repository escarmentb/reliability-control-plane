from __future__ import annotations

import json
import math
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Phase:
    name: str
    requests: int
    failure_rate: float
    latency_ms: int


@dataclass(frozen=True)
class Attempt:
    phase: str
    success: bool
    status: int
    latency_ms: float
    retries: int
    circuit_open: bool = False


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_seconds: float = 2.0) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_seconds = recovery_seconds
        self.failures = 0
        self.opened_at: float | None = None

    def allow(self, now: float | None = None) -> bool:
        if self.opened_at is None:
            return True
        current = time.monotonic() if now is None else now
        if current - self.opened_at >= self.recovery_seconds:
            self.opened_at = None
            self.failures = 0
            return True
        return False

    def record(self, success: bool, now: float | None = None) -> None:
        if success:
            self.failures = 0
            return
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.opened_at = time.monotonic() if now is None else now


Transport = Callable[[str, float], tuple[int, float]]


def http_post(url: str, timeout: float) -> tuple[int, float]:
    started = time.perf_counter()
    request = Request(url, method="POST")
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, (time.perf_counter() - started) * 1000
    except HTTPError as error:
        return error.code, (time.perf_counter() - started) * 1000
    except (TimeoutError, URLError):
        return 0, (time.perf_counter() - started) * 1000


def run_phase(
    base_url: str,
    phase: Phase,
    breaker: CircuitBreaker,
    retries: int = 2,
    timeout: float = 4.0,
    transport: Transport = http_post,
) -> list[Attempt]:
    results: list[Attempt] = []
    for index in range(phase.requests):
        if not breaker.allow():
            results.append(Attempt(phase.name, False, 0, 0, 0, circuit_open=True))
            time.sleep(0.05)
            continue

        url = (
            f"{base_url.rstrip('/')}/orders/{phase.name}-{index}"
            f"?failure_rate={phase.failure_rate}&latency_ms={phase.latency_ms}"
        )
        total_latency = 0.0
        status = 0
        used_retries = 0
        for attempt_number in range(retries + 1):
            status, latency = transport(url, timeout)
            total_latency += latency
            used_retries = attempt_number
            if 200 <= status < 300:
                break
            if attempt_number < retries:
                time.sleep(0.05 * (2**attempt_number))

        success = 200 <= status < 300
        breaker.record(success)
        results.append(Attempt(phase.name, success, status, total_latency, used_retries))
    return results


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = math.ceil((percent / 100) * len(ordered)) - 1
    return ordered[max(0, index)]


def summarize(results: list[Attempt]) -> dict[str, object]:
    completed = [result for result in results if not result.circuit_open]
    latencies = [result.latency_ms for result in completed]
    successes = sum(result.success for result in results)
    total = len(results)
    phases: dict[str, dict[str, object]] = {}
    for phase_name in dict.fromkeys(result.phase for result in results):
        phase_results = [result for result in results if result.phase == phase_name]
        phase_successes = sum(result.success for result in phase_results)
        phases[phase_name] = {
            "requests": len(phase_results),
            "availability": phase_successes / len(phase_results) if phase_results else 1.0,
            "circuit_rejections": sum(result.circuit_open for result in phase_results),
        }
    return {
        "requests": total,
        "successes": successes,
        "availability": successes / total if total else 1.0,
        "p50_ms": percentile(latencies, 50),
        "p95_ms": percentile(latencies, 95),
        "retries": sum(result.retries for result in results),
        "circuit_rejections": sum(result.circuit_open for result in results),
        "phases": phases,
    }


def write_reports(results: list[Attempt], output_dir: Path) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize(results)
    json_path = output_dir / "incident-report.json"
    json_path.write_text(
        json.dumps({"summary": summary, "attempts": [asdict(item) for item in results]}, indent=2),
        encoding="utf-8",
    )
    phase_rows = "".join(
        f"<tr><td>{name}</td><td>{data['requests']}</td>"
        f"<td>{data['availability']:.1%}</td><td>{data['circuit_rejections']}</td></tr>"
        for name, data in summary["phases"].items()
    )
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Incident Report</title>
<style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px;color:#17202a}}
h1{{border-bottom:4px solid #e74c3c;padding-bottom:12px}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}}
.metric{{border:1px solid #ccd1d1;padding:18px;border-radius:6px}}.metric strong{{display:block;font-size:28px}}
table{{width:100%;border-collapse:collapse;margin-top:24px}}th,td{{padding:10px;text-align:left;border-bottom:1px solid #ddd}}
</style></head><body><h1>Reliability Incident Report</h1><div class="metrics">
<div class="metric"><strong>{summary['availability']:.1%}</strong>Availability</div>
<div class="metric"><strong>{summary['p95_ms']:.0f} ms</strong>P95 latency</div>
<div class="metric"><strong>{summary['retries']}</strong>Retries</div></div>
<h2>Timeline</h2><table><thead><tr><th>Phase</th><th>Requests</th><th>Availability</th><th>Circuit rejections</th></tr></thead>
<tbody>{phase_rows}</tbody></table><p>Generated by Incident Simulator.</p></body></html>"""
    html_path = output_dir / "incident-report.html"
    html_path.write_text(html, encoding="utf-8")
    return json_path, html_path
