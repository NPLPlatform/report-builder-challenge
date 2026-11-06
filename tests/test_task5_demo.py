"""Task 5: the demo publishes, and no check was weakened to get there."""

from __future__ import annotations

from report_builder.agent import Agent
from report_builder.checks import check_report
from report_builder.model import ScriptedModel
from report_builder.models import Session
from report_builder.store import JsonSessionStore
from report_builder.tools import working_report


def test_demo_publishes(tmp_path) -> None:
    store = JsonSessionStore(tmp_path)
    agent = Agent(ScriptedModel.from_file(), store)
    session = store.create(Session(user_id="demo", dataset="harbour_bikes", month="2026-06"))
    agent.run(session, "Write the June 2026 monthly review.")
    if session.status == "awaiting_approval":    # after task 6 publishing waits for the user
        agent.resume(session, approved=True)
    assert session.status == "published"
    assert all(c.status != "Fail" for c in session.checks)
    report = (store.folder(session.id) / "report.md").read_text()
    for name in ("Acme Logistics", "Bluefin Hotels", "Corvid Tech"):
        assert name.lower() not in report.lower()
    assert working_report(agent.context(session))[0] == report


def test_the_check_still_catches_a_leak() -> None:
    checks = check_report("Our largest client is Acme Logistics.", {}, [], ["Acme Logistics"], budget=100)
    assert checks[-1].name == "Anonymised" and checks[-1].status == "Fail"
