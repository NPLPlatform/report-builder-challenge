"""Task 4: a tool that refuses, an unknown tool or bad arguments must not end the run."""

from __future__ import annotations

from report_builder.agent import MAX_TOOL_ERRORS, Agent
from report_builder.model import ScriptedModel
from report_builder.models import Session
from report_builder.store import JsonSessionStore


def run(tmp_path, steps):
    store = JsonSessionStore(tmp_path)
    agent = Agent(ScriptedModel(steps), store)
    session = store.create(Session(user_id="u", dataset="harbour_bikes", month="2026-06"))
    return agent.run(session, "go"), store


def tool_messages(session):
    return [m for m in session.messages if m.role == "tool"]


def test_refusal_goes_back_to_the_model(tmp_path) -> None:
    session, _ = run(tmp_path, [
        {"calls": [{"tool": "save_section", "args": {"heading": "Nope", "markdown": "x"}}]},
        {"calls": [{"tool": "save_section", "args": {"heading": "1. Summary", "markdown": "x"}}]},
        {"text": "done"},
    ])
    first, second = tool_messages(session)
    assert first.is_error and "Nope" in first.content
    assert not second.is_error
    assert session.status == "idle"
    assert session.sections == {"1. Summary": "x"}


def test_unknown_tool_and_bad_arguments(tmp_path) -> None:
    session, _ = run(tmp_path, [
        {"calls": [{"tool": "delete_everything"}, {"tool": "compute_metric", "args": {"metric": "x"}}]},
        {"text": "done"},
    ])
    unknown, bad = tool_messages(session)
    assert unknown.is_error and "delete_everything" in unknown.content
    assert bad.is_error
    assert session.status == "idle"


def test_every_call_is_answered_in_order(tmp_path) -> None:
    session, _ = run(tmp_path, [
        {"calls": [{"tool": "list_metrics"}, {"tool": "nope"}, {"tool": "read_template"}]},
        {"text": "done"},
    ])
    reply = session.messages[1]
    assert [m.tool_call_id for m in tool_messages(session)] == [c.id for c in reply.tool_calls]


def test_too_many_errors_fail_the_run(tmp_path) -> None:
    bad = {"calls": [{"tool": "nope"}]}
    session, store = run(tmp_path, [bad] * (MAX_TOOL_ERRORS + 5))
    assert session.status == "failed"
    assert sum(m.is_error for m in tool_messages(session)) == MAX_TOOL_ERRORS
    assert store.get(session.id, "u").status == "failed"   # saved
