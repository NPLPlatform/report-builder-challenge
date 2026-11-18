"""The datasets the report builder can report on, and the metrics it computes from them."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from functools import cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOGUE = ROOT / "data" / "catalogue.json"
NUMERIC = {"rides": int, "revenue": float, "budget_revenue": float}


@dataclass(frozen=True)
class Dataset:
    """A dataset: rentals by month, station and customer, and the budget by month and station."""

    name: str
    title: str
    currency: str
    rentals: list[dict[str, Any]]
    budget: list[dict[str, Any]]
    hidden: list[str] = field(default_factory=list)   # customer names a report must never show


def read_csv(path: Path) -> list[dict[str, Any]]:
    """A CSV file as rows, with the numeric columns converted."""
    with path.open(newline="", encoding="utf-8") as f:
        return [{k: NUMERIC[k](v) if k in NUMERIC else v for k, v in row.items()} for row in csv.DictReader(f)]


@cache
def load(name: str) -> Dataset:
    """The catalogue's dataset of that name."""
    entries = json.loads(CATALOGUE.read_text(encoding="utf-8"))
    if name not in entries:
        raise KeyError(f"unknown dataset {name!r}")
    entry = entries[name]
    return Dataset(name, entry["title"], entry["currency"], read_csv(ROOT / entry["rentals"]),
                   read_csv(ROOT / entry["budget"]), entry.get("hidden", []))


def months(ds: Dataset) -> list[str]:
    """The months with rentals, in order (YYYY-MM)."""
    return sorted({r["month"] for r in ds.rentals})


def month_label(month: str) -> str:
    """2026-06 -> June 2026."""
    return f"{date.fromisoformat(month + '-01'):%B %Y}"


def _in(month: str, ytd: bool) -> Callable[[str], bool]:
    return (lambda m: month[:4] + "-01" <= m <= month) if ytd else (lambda m: m == month)


def revenue(ds: Dataset, month: str, *, ytd: bool = False) -> float:
    """Revenue in the month (or the year to date)."""
    keep = _in(month, ytd)
    return round(sum(r["revenue"] for r in ds.rentals if keep(r["month"])), 2)


def budget(ds: Dataset, month: str, *, ytd: bool = False) -> float:
    """Budgeted revenue in the month (or the year to date)."""
    keep = _in(month, ytd)
    return round(sum(r["budget_revenue"] for r in ds.budget if keep(r["month"])), 2)


def ratio(actual: float, planned: float) -> float | None:
    """Actual over budget (planned); None when there is no budget."""
    raise NotImplementedError("Task 2")


def by_station(ds: Dataset, month: str) -> list[dict[str, Any]]:
    """
    Per-station actual revenue vs budget for the month (Revenue, Budget, A/B = actual/budget).

    A station with revenue but no budget (or a budget but no revenue) still has its row; its A/B is None when the
    budget is zero. Ties in revenue are broken by the station's name.

    Example output::
    [
        {"Station": "North", "Revenue": 488.0, "Budget": 500.0, "A/B": 0.976},
        {"Station": "East", "Revenue": 100.0, "Budget": 0.0, "A/B": None},
        {"Station": "Total", "Revenue": 588.0, "Budget": 500.0, "A/B": 1.176},
    ]
    """
    raise NotImplementedError("Task 2")


def top_customers(ds: Dataset, month: str, n: int = 3) -> list[dict[str, Any]]:
    """
    The month's ``n`` largest corporate customers by revenue, with rides and their share of the month's revenue.

    Individuals are not customers here. Ties in revenue are broken by the customer's name.
    Example (n=2)::
    [
        {"Customer": "Alpha Ltd", "Revenue": 38.0, "Rides": 10, "Share": 0.049},
        {"Customer": "Beta Ltd", "Revenue": 38.0, "Rides": 8, "Share": 0.049},
    ]
    """
    raise NotImplementedError("Task 2")


METRICS: dict[str, Callable[[Dataset, str], Any]] = {
    "revenue_month": lambda ds, m: revenue(ds, m),
    "budget_month": lambda ds, m: budget(ds, m),
    "ratio_month": lambda ds, m: ratio(revenue(ds, m), budget(ds, m)),
    "revenue_ytd": lambda ds, m: revenue(ds, m, ytd=True),
    "budget_ytd": lambda ds, m: budget(ds, m, ytd=True),
    "ratio_ytd": lambda ds, m: ratio(revenue(ds, m, ytd=True), budget(ds, m, ytd=True)),
    "by_station": by_station,
    "top_customers": top_customers,
}
