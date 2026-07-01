from app.reliability import SloSnapshot


def test_empty_slo_is_fully_available() -> None:
    snapshot = SloSnapshot(objective=0.995, successful_requests=0, total_requests=0)

    assert snapshot.availability == 1.0
    assert snapshot.is_burning_budget is False


def test_slo_detects_budget_burn() -> None:
    snapshot = SloSnapshot(objective=0.995, successful_requests=99, total_requests=100)

    assert snapshot.availability == 0.99
    assert snapshot.is_burning_budget is True
    assert snapshot.error_budget_remaining == 0.0

