"""
The demo: the scripted model writes the June 2026 review of Harbour Bikes.

    uv run python -m report_builder.demo

Exit code 0 when the report is published.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

from report_builder.agent import Agent
from report_builder.model import ScriptedModel
from report_builder.models import Message, Session
from report_builder.store import JsonSessionStore
from report_builder.tools import working_report


def show(message: Message) -> str:
    if message.role == "tool":
        mark = "  !! " if message.is_error else "  <- "
        return mark + message.content.replace("\n", " ")[:100]
    calls = ", ".join(f"{c.name}({', '.join(f'{k}={str(v)[:24]!r}' for k, v in c.args.items())})"
                      for c in message.tool_calls)
    return f"[{message.role}] {message.content}" + (f"\n  -> {calls}" if calls else "")


def run_demo(root: Path) -> Session:
    """Run the scripted demo in a store at ``root``."""
    store = JsonSessionStore(root)
    agent = Agent(ScriptedModel.from_file(), store)
    session = store.create(Session(user_id="demo", dataset="harbour_bikes", month="2026-06"))
    agent.run(session, "Write the June 2026 monthly review.")
    return session


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args(argv)
    with tempfile.TemporaryDirectory() as tmp:
        session = run_demo(Path(tmp))
        for message in session.messages:
            print(show(message))
        agent = Agent(ScriptedModel.from_file(), JsonSessionStore(Path(tmp)))
        print("\n" + "=" * 100 + "\n")
        print(working_report(agent.context(session))[0])
        print("=" * 100)
        for check in session.checks:
            print(f"{check.status:5} {check.name}: {check.detail}" + (f" {check.items}" if check.items else ""))
        print(f"\nstatus: {session.status}")
    return 0 if session.status == "published" else 1


if __name__ == "__main__":
    sys.exit(main())
