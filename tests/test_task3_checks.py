"""Task 3: the release checks (checks.check_report)."""

from __future__ import annotations

from report_builder.checks import check_report

HEADINGS = ["1. Summary", "2. Stations"]


def by_name(checks):
    return {c.name: c for c in checks}


def test_all_pass() -> None:
    written = {"1. Summary": "Revenue rose.", "2. Stations": "| a |\n| --- |\n| 1 |\n\nHarbour leads."}
    checks = check_report("Revenue rose. Harbour leads.", written, HEADINGS, ["Bluefin"], budget=10)
    assert [c.name for c in checks] == ["Placeholders filled", "Sections written", "Length kept", "Anonymised"]
    assert all(c.status == "Pass" for c in checks)


def test_placeholders_left() -> None:
    c = by_name(check_report("Revenue {{revenue|money}} and {{table:x}}", {}, [], [], budget=10))
    assert c["Placeholders filled"].status == "Fail"
    assert c["Placeholders filled"].items == ["{{revenue|money}}", "{{table:x}}"]


def test_sections_not_written_is_a_note() -> None:
    c = by_name(check_report("text", {"1. Summary": "x"}, HEADINGS, [], budget=10))
    assert c["Sections written"].status == "Note"
    assert c["Sections written"].items == ["2. Stations"]


def test_no_anonymised_check_without_hidden_names() -> None:
    assert "Anonymised" not in by_name(check_report("text", {}, [], [], budget=10))


def test_length_counts_prose_only() -> None:
    table = "\n".join(["| a | b |", "| --- | --- |"] + ["| many words in this table row | 1 |"] * 50)
    within = {"1. Summary": table + "\n\n" + " ".join(["word"] * 12)}     # 12 words: within 10 * 1.25
    over = {"1. Summary": " ".join(["word"] * 13)}                        # 13 words: over
    assert by_name(check_report("x", within, HEADINGS[:1], [], budget=10))["Length kept"].status == "Pass"
    c = by_name(check_report("x", over, HEADINGS[:1], [], budget=10))["Length kept"]
    assert c.status == "Fail" and c.items == ["1. Summary: 13 words, about 10 allowed"]


def test_placeholders_are_not_words() -> None:
    written = {"1. Summary": "{{a|money}} {{b|money}} " + " ".join(["word"] * 12)}
    assert by_name(check_report("x", written, HEADINGS[:1], [], budget=10))["Length kept"].status == "Pass"


def test_hidden_names_any_case() -> None:
    c = by_name(check_report("Our client BLUEFIN rode most.", {}, [], ["Bluefin", "Corvid Tech"], budget=10))
    assert c["Anonymised"].status == "Fail" and c["Anonymised"].items == ["Bluefin"]


def test_hidden_names_between_underscores() -> None:
    c = by_name(check_report("![chart](charts/Bluefin_q2.png)", {}, [], ["Bluefin"], budget=10))
    assert c["Anonymised"].status == "Fail"


def test_hidden_names_not_inside_longer_words() -> None:
    c = by_name(check_report("Bluefinch Cafe and Bluefin2 rode too.", {}, [], ["Bluefin"], budget=10))
    assert c["Anonymised"].status == "Pass"


def test_hidden_names_with_spaces_and_order() -> None:
    c = by_name(check_report("corvid tech and bluefin", {}, [], ["Bluefin", "Corvid Tech"], budget=10))
    assert c["Anonymised"].items == ["Bluefin", "Corvid Tech"]
