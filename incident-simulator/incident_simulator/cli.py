from __future__ import annotations

import argparse
from pathlib import Path

from incident_simulator.core import CircuitBreaker, Phase, run_phase, write_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run an incident drill against Reliability Lab.")
    parser.add_argument("--url", default="http://127.0.0.1:8000")
    parser.add_argument("--requests", type=int, default=20, help="Requests per phase.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Per-attempt timeout in seconds.")
    parser.add_argument("--output", type=Path, default=Path("reports"))
    return parser


def main() -> None:
    args = build_parser().parse_args()
    phases = [
        Phase("baseline", args.requests, 0.0, 25),
        Phase("incident", args.requests, 0.8, 250),
        Phase("recovery", args.requests, 0.0, 40),
    ]
    breaker = CircuitBreaker(failure_threshold=4, recovery_seconds=0.5)
    results = []
    for phase in phases:
        print(f"Running {phase.name} phase...")
        results.extend(run_phase(args.url, phase, breaker, timeout=args.timeout))
    json_path, html_path = write_reports(results, args.output)
    print(f"JSON report: {json_path.resolve()}")
    print(f"HTML report: {html_path.resolve()}")


if __name__ == "__main__":
    main()
