"""Task 2: metrics (data.ratio, data.by_station, data.top_customers)."""

from __future__ import annotations

import pytest

from report_builder.data import by_station, load, ratio, top_customers


def test_ratio() -> None:
    assert ratio(50.0, 200.0) == 0.25
    assert ratio(10.0, 0.0) is None
    assert ratio(0.0, 0.0) is None


def test_by_station_order_and_total(tiny) -> None:
    rows = by_station(tiny, "2026-01")
    assert [r["Station"] for r in rows] == ["North", "South", "West", "Total"]
    assert rows[0] == {"Station": "North", "Revenue": 488.0, "Budget": 500.0, "A/B": pytest.approx(0.976)}
    assert rows[2] == {"Station": "West", "Revenue": 0.0, "Budget": 100.0, "A/B": 0.0}   # a budget, no rentals
    assert rows[-1]["Revenue"] == 770.0 and rows[-1]["Budget"] == 900.0


def test_by_station_without_budget(tiny) -> None:
    east = next(r for r in by_station(tiny, "2026-02") if r["Station"] == "East")
    assert east["A/B"] is None   # revenue against a zero budget


def test_top_customers(tiny) -> None:
    rows = top_customers(tiny, "2026-01", n=2)
    # Alpha and Beta tie on revenue: the name breaks the tie; individuals are never customers here
    assert [r["Customer"] for r in rows] == ["Alpha Ltd", "Beta Ltd"]
    assert rows[0]["Rides"] == 10
    assert rows[0]["Share"] == pytest.approx(38.0 / 770.0)


def test_top_customers_month_without_corporates(tiny) -> None:
    assert top_customers(tiny, "2026-02") == []


def test_real_dataset_june() -> None:
    ds = load("harbour_bikes")
    rows = by_station(ds, "2026-06")
    assert rows[-1]["Station"] == "Total"
    assert rows[-1]["Revenue"] == pytest.approx(sum(r["Revenue"] for r in rows[:-1]))
    march = {r["Station"]: r for r in by_station(ds, "2026-03")}
    assert march["Airport"]["Revenue"] > 0 and march["Airport"]["A/B"] is None
