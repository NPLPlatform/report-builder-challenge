"""The release checks: what must hold before a report may be published."""

from __future__ import annotations

import re

from report_builder.models import Check
from report_builder.template import PLACEHOLDER

WORD = re.compile(r"[^\W_]+(?:[-'.,][^\W_]+)*")
OVER_BUDGET = 1.25  # a section may run this far over its word budget before the check fails


def prose_words(markdown: str) -> int:
    """The words of a section's prose: table lines and placeholders are not counted."""
    count = 0
    for line in markdown.splitlines():
        text = line.strip()
        if not text or text.startswith("|"):
            continue
        count += len(WORD.findall(PLACEHOLDER.sub("", text)))
    return count


def check_report(
    filled: str, written: dict[str, str], headings: list[str], hidden: list[str], budget: int
) -> list[Check]:
    """
    Checks a filled report must pass before it may be published, in this order.

    1. "Placeholders filled": Fail when a placeholder is left in ``filled``; items = the placeholders as written.
    2. "Sections written": Note when a template heading has no written section; items = those headings.
    3. "Length kept": Fail when a written section's prose (``prose_words``) is over ``budget * OVER_BUDGET`` words;
       items = "<heading>: <n> words, about <budget> allowed".
    4. "Anonymised" (only when ``hidden`` is not empty): Fail when a hidden name appears in ``filled``, in any case,
       not as part of a longer word or number ("Bluefin" matches "BLUEFIN" and "Bluefin_q2.png", not
       "Bluefinch"); items = the hidden names found, in the order of ``hidden``.

    Args:
        filled: Full report markdown after placeholders are replaced.
        written: Heading -> section body the agent has saved.
        headings: Template section headings, in order.
        hidden: Customer names that must not appear; if empty, skip Anonymised.
        budget: Max prose words per section.
    """
    raise NotImplementedError("Task 3")
