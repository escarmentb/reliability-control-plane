from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass(frozen=True)
class SloSnapshot:
    objective: float
    successful_requests: int
    total_requests: int

    @property
    def availability(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

    @property
    def error_budget_remaining(self) -> float:
        allowed_bad_ratio = 1 - self.objective
        actual_bad_ratio = 1 - self.availability
        return max(0.0, allowed_bad_ratio - actual_bad_ratio)

    @property
    def error_budget_used(self) -> float:
        allowed_bad_ratio = 1 - self.objective
        if allowed_bad_ratio <= 0:
            return 0.0
        actual_bad_ratio = 1 - self.availability
        return min(1.0, max(0.0, actual_bad_ratio / allowed_bad_ratio))

    @property
    def is_burning_budget(self) -> bool:
        return self.availability < self.objective


class InMemoryReliabilityStore:
    def __init__(self, objective: float = 0.995) -> None:
        self.objective = objective
        self.successful_requests = 0
        self.failed_requests = 0
        self.started_at = datetime.now(UTC)

    @property
    def total_requests(self) -> int:
        return self.successful_requests + self.failed_requests

    def record_success(self) -> None:
        self.successful_requests += 1

    def record_failure(self) -> None:
        self.failed_requests += 1

    def snapshot(self) -> SloSnapshot:
        return SloSnapshot(
            objective=self.objective,
            successful_requests=self.successful_requests,
            total_requests=self.total_requests,
        )
