"""
The report template: sections, placeholders and how values are shown.

A template is Markdown. Its front matter is everything before the first ``## `` heading; each ``## `` heading starts a
section. The agent rewrites sections one at a time; the working report is the template with the written sections in
place of the reference text.

Placeholders: ``{{name}}`` or ``{{name|kind}}`` (kind: pct, money, int) for a value, ``{{table:name}}`` for a table
(a list of rows).
"""

from __future__ import annotations

import re
from typing import Any

PLACEHOLDER = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([^{}]*?)\s*)?\}\}")
HEADING = re.compile(r"(?m)^## (.+)$")
FRONT = "Front matter"
DASH = "\N{EN DASH}"
KINDS = ("pct", "money", "int")
PCT_COLUMNS = ("A/B", "Share")


def split(template: str) -> list[tuple[str, str]]:
    """The template's parts as (heading, body): the front matter first, then each section."""
    parts = HEADING.split(template)
    return [(FRONT, parts[0])] + [(parts[i].strip(), parts[i + 1]) for i in range(1, len(parts) - 1, 2)]


def headings(template: str) -> list[str]:
    """The template's section headings, in order."""
    return [h for h, _ in split(template)[1:]]


def assemble(template: str, written: dict[str, str]) -> str:
    """The template with each written section (heading -> Markdown) in place of its reference body."""
    out = []
    for heading, body in split(template):
        if heading == FRONT:
            out.append(body)
        else:
            text = f"\n\n{written[heading].strip()}\n\n" if heading in written else body
            out.append(f"## {heading}{text}")
    return "".join(out).rstrip("\n") + "\n"


def fmt(value: Any, kind: str | None = None) -> str:
    """
    Format one value for display in the report.

    None and NaN show as an en dash. pct: one decimal (0.1234 -> 12.3%); money: thousands separators, no decimals;
    int: thousands separators; no kind: a float with two decimals, anything else as str. Rounding never shows a
    negative zero ("-0", "-0.0%"). An unknown kind is a ValueError.
    """
    raise NotImplementedError("Task 1")


def column_kind(column: str, values: list[Any]) -> str | None:
    """How a table column is shown: pct for ratios and shares, money for amounts, int for counts."""
    if column in PCT_COLUMNS:
        return "pct"
    present = [v for v in values if v is not None]
    if present and all(isinstance(v, int) and not isinstance(v, bool) for v in present):
        return "int"
    if present and all(isinstance(v, int | float) and not isinstance(v, bool) for v in present):
        return "money"
    return None


def markdown_table(rows: list[dict[str, Any]]) -> str:
    """Rows as a Markdown table; the columns are the first row's keys."""
    if not rows:
        return "_No rows._"
    columns = list(rows[0])
    kinds = {c: column_kind(c, [r.get(c) for r in rows]) for c in columns}
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join("---:" if kinds[c] else "---" for c in columns) + " |",
    ]
    lines += ["| " + " | ".join(fmt(r.get(c), kinds[c]) for c in columns) + " |" for r in rows]
    return "\n".join(lines)


def fill(text: str, values: dict[str, Any]) -> tuple[str, list[str]]:
    """
    Replace placeholders in text using values. Returns the filled text and the names that could not be filled.

    ``{{name}}`` and ``{{name|kind}}`` take ``values[name]`` shown with ``fmt``; ``{{table:name}}`` takes
    ``values[name]`` (a list of rows) as a Markdown table. A placeholder whose name is not in ``values`` stays as
    written and its name is reported once, in the order of first appearance. An unknown kind is a ValueError.
    """
    raise NotImplementedError("Task 1")
