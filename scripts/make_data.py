"""Generate the synthetic Harbour Bikes dataset (deterministic: the same files every time)."""

from __future__ import annotations

import csv
import random
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / "data"
MONTHS = [f"2026-{m:02d}" for m in range(1, 7)]
STATIONS = {"Harbour": 1.6, "Old Town": 1.2, "University": 1.0, "Riverside": 0.8, "Airport": 0.9}
AIRPORT_OPENS = "2026-03"          # rentals from March
AIRPORT_BUDGET_FROM = "2026-04"    # budgeted from April: March has revenue against no budget
SEASON = {"2026-01": 0.55, "2026-02": 0.6, "2026-03": 0.8, "2026-04": 1.0, "2026-05": 1.25, "2026-06": 1.45}
CORPORATES = {   # customer -> (stations it rides from, rides a month at full season)
    "Acme Logistics": (("Harbour", "Riverside"), 260),
    "Bluefin Hotels": (("Harbour", "Old Town", "Airport"), 210),
    "Corvid Tech": (("University", "Old Town"), 150),
    "City Council": (("Old Town", "Harbour"), 120),
    "Northgate Clinic": (("Riverside",), 70),
}
PRICE = {"individual": 4.5, "corporate": 3.8}


def main() -> None:
    rng = random.Random(7)
    rentals: list[dict[str, object]] = []
    budget: list[dict[str, object]] = []
    for month in MONTHS:
        for station, size in STATIONS.items():
            if station == "Airport" and month < AIRPORT_OPENS:
                continue
            rides = round(900 * size * SEASON[month] * rng.uniform(0.85, 1.15))
            rentals.append({"month": month, "station": station, "customer": "Individual",
                            "customer_type": "individual", "rides": rides,
                            "revenue": round(rides * PRICE["individual"], 2)})
            for customer, (stations, full) in CORPORATES.items():
                if station in stations:
                    n = round(full * SEASON[month] * rng.uniform(0.8, 1.2) / len(stations))
                    rentals.append({"month": month, "station": station, "customer": customer,
                                    "customer_type": "corporate", "rides": n,
                                    "revenue": round(n * PRICE["corporate"], 2)})
            planned = 0.0 if station == "Airport" and month < AIRPORT_BUDGET_FROM else \
                round(4400 * size * SEASON[month] * 1.05, -1)
            budget.append({"month": month, "station": station, "budget_revenue": planned})
    _write(DATA / "rentals.csv", rentals)
    _write(DATA / "budget.csv", budget)


def _write(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
