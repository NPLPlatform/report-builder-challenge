"""Task 1: showing values and filling the template (template.fmt, template.fill)."""

from __future__ import annotations

import math

import pytest

from report_builder.template import DASH, fill, fmt


@pytest.mark.parametrize(("value", "kind", "shown"), [
    (0.1234, "pct", "12.3%"),
    (1.0, "pct", "100.0%"),
    (-0.0001, "pct", "0.0%"),          # never "-0.0%"
    (35605.5, "money", "35,606"),
    (-0.4, "money", "0"),               # never "-0"
    (1234, "int", "1,234"),
    (None, "pct", DASH),
    (math.nan, "money", DASH),
    (None, None, DASH),
    (2.5, None, "2.50"),
    ("Harbour", None, "Harbour"),
])
def test_fmt(value, kind, shown) -> None:
    assert fmt(value, kind) == shown


def test_fmt_unknown_kind() -> None:
    with pytest.raises(ValueError, match="percent"):
        fmt(0.5, "percent")


def test_fill_values_and_kinds() -> None:
    text, missing = fill("Revenue {{revenue|money}} is {{ratio|pct}} of budget in {{month}}.",
                         {"revenue": 1234.4, "ratio": 0.5, "month": "June 2026"})
    assert text == "Revenue 1,234 is 50.0% of budget in June 2026."
    assert missing == []


def test_fill_tolerates_spaces() -> None:
    assert fill("{{ ratio | pct }}", {"ratio": 0.25})[0] == "25.0%"


def test_fill_leaves_unknown_names_and_reports_them_once() -> None:
    text, missing = fill("{{a}} {{b|pct}} {{a}} {{table:c}}", {})
    assert text == "{{a}} {{b|pct}} {{a}} {{table:c}}"
    assert missing == ["a", "b", "table:c"]


def test_fill_table() -> None:
    rows = [{"Station": "North", "Revenue": 1500.0, "A/B": 0.75}, {"Station": "Total", "Revenue": 1500.0, "A/B": None}]
    text, missing = fill("Before\n\n{{table:by_station}}\n\nAfter", {"by_station": rows})
    assert missing == []
    assert text == ("Before\n\n| Station | Revenue | A/B |\n| --- | ---: | ---: |\n| North | 1,500 | 75.0% |\n"
                    f"| Total | 1,500 | {DASH} |\n\nAfter")


def test_fill_unknown_kind_raises() -> None:
    with pytest.raises(ValueError):
        fill("{{ratio|percent}}", {"ratio": 0.5})
