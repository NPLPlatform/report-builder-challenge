"""
The HTTP API.

The caller names themselves in the ``X-User`` header: a stand-in for real authentication, which is out of scope.
Run it with ``uv run uvicorn report_builder.api:app --reload``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from report_builder.agent import Agent
from report_builder.data import load, months
from report_builder.model import Model, ScriptedModel
from report_builder.models import Message, Session, Status
from report_builder.store import JsonSessionStore
from report_builder.tools import ToolContext, run_checks, working_report

ROOT = Path(__file__).resolve().parents[2]


class CreateSession(BaseModel):
    dataset: str
    month: str


class UserMessage(BaseModel):
    text: str


class RunResult(BaseModel):
    status: Status
    messages: list[Message]            # the messages this request added


def current_user(x_user: Annotated[str, Header()]) -> str:
    """The caller (a stand-in for authentication)."""
    if not x_user.strip():
        raise HTTPException(401, "X-User is empty")
    return x_user.strip()


User = Annotated[str, Depends(current_user)]


def create_app(root: Path | None = None, model: Model | None = None) -> FastAPI:
    """The API over a store at ``root`` (default ``.sessions/``) and a model (default: the scripted demo run)."""
    store = JsonSessionStore(root or ROOT / ".sessions")
    agent = Agent(model or ScriptedModel.from_file(), store)
    app = FastAPI(title="Report Builder")

    def owned(session_id: str, user: str) -> Session:
        session = store.get(session_id, user)
        if session is None:
            raise HTTPException(404, "no such session")
        return session

    def result(session: Session, before: int) -> RunResult:
        return RunResult(status=session.status, messages=session.messages[before:])

    @app.post("/sessions", status_code=201)
    def create_session(body: CreateSession, user: User) -> Session:
        try:
            ds = load(body.dataset)
        except KeyError:
            raise HTTPException(404, f"unknown dataset {body.dataset!r}") from None
        if body.month not in months(ds):
            raise HTTPException(422, f"no data for {body.month}: the months are {', '.join(months(ds))}")
        return store.create(Session(user_id=user, dataset=body.dataset, month=body.month))

    @app.get("/sessions")
    def list_sessions(user: User) -> list[dict[str, Any]]:
        return [s.model_dump(include={"id", "dataset", "month", "status", "created_at"}) for s in store.list(user)]

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str, user: User) -> Session:
        return owned(session_id, user)

    @app.post("/sessions/{session_id}/messages")
    def send_message(session_id: str, body: UserMessage, user: User) -> RunResult:
        session = owned(session_id, user)
        before = len(session.messages)
        agent.run(session, body.text)
        return result(session, before)

    @app.get("/sessions/{session_id}/report")
    def report(session_id: str, user: User) -> dict[str, Any]:
        session = owned(session_id, user)
        ctx = ToolContext(session=session, dataset=load(session.dataset), template=agent.template,
                          folder=store.folder(session.id))
        markdown, missing = working_report(ctx)
        return {"markdown": markdown, "missing": missing, "checks": [c.model_dump() for c in run_checks(ctx)]}

    return app


app = create_app()
