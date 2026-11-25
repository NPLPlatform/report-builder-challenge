"""
The agent loop: ask the model, run the tools it calls, hand back their results, until it answers in text.
"""

from __future__ import annotations

from pathlib import Path

from report_builder.data import load
from report_builder.model import Model
from report_builder.models import Message, Session
from report_builder.store import SessionStore
from report_builder.tools import TOOLS, ToolContext, as_text

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "templates" / "monthly_review.md"
MAX_STEPS = 30          # model replies in one run
MAX_TOOL_ERRORS = 3     # tool errors since the user's last message before the run fails

SYSTEM_PROMPT = """You write the monthly review of a dataset with the tools you are given.
Read the template, compute the metrics it needs, write each section with placeholders for every figure, run the
release checks, fix every Fail, then publish. Never type a figure yourself: use a placeholder."""


class Agent:
    """Runs sessions with a model and saves them to a store."""

    def __init__(self, model: Model, store: SessionStore, template: Path = TEMPLATE) -> None:
        self.model = model
        self.store = store
        self.template = template.read_text(encoding="utf-8")
        self.specs = [t.spec() for t in TOOLS.values()]

    def context(self, session: Session) -> ToolContext:
        return ToolContext(session=session, dataset=load(session.dataset), template=self.template,
                           folder=self.store.folder(session.id))

    def run(self, session: Session, text: str) -> Session:
        """Add the user's message and run until the model answers in text."""
        session.messages.append(Message(role="user", content=text))
        session.status = "running"
        ctx = self.context(session)
        for _ in range(MAX_STEPS):
            reply = self.model.respond(SYSTEM_PROMPT, session.messages, self.specs)
            session.messages.append(reply)
            if not reply.tool_calls:
                session.status = "published" if session.status == "published" else "idle"
                break
            for call in reply.tool_calls:
                result = TOOLS[call.name].func(ctx, **call.args)
                session.messages.append(Message(role="tool", tool_call_id=call.id, content=as_text(result)))
        else:
            session.status = "failed"
        self.store.save(session)
        return session
