from __future__ import annotations

from typing import Any

import pytest

from report_builder.data import Dataset


@pytest.fixture
def tiny() -> Dataset:
    """A dataset small enough to check by hand."""
    def r(month: str, station: str, customer: str, kind: str, rides: int, revenue: float) -> dict[str, Any]:
        return {"month": month, "station": station, "customer": customer, "customer_type": kind,
                "rides": rides, "revenue": revenue}

    rentals = [
        r("2026-01", "North", "Individual", "individual", 100, 450.0),
        r("2026-01", "North", "Beta Ltd", "corporate", 10, 38.0),
        r("2026-01", "South", "Individual", "individual", 50, 225.0),
        r("2026-01", "South", "Alpha Ltd", "corporate", 10, 38.0),
        r("2026-01", "South", "Gamma Ltd", "corporate", 5, 19.0),
        r("2026-02", "North", "Individual", "individual", 120, 540.0),
        r("2026-02", "East", "Individual", "individual", 20, 90.0),
    ]
    budget = [
        {"month": "2026-01", "station": "North", "budget_revenue": 500.0},
        {"month": "2026-01", "station": "South", "budget_revenue": 300.0},
        {"month": "2026-01", "station": "West", "budget_revenue": 100.0},
        {"month": "2026-02", "station": "North", "budget_revenue": 600.0},
        {"month": "2026-02", "station": "East", "budget_revenue": 0.0},
    ]
    return Dataset("tiny", "Tiny", "EUR", rentals, budget, [])
