"""
Where sessions live: one folder per session under the store's root.

``session.json`` holds the session (its conversation included); the folder also holds what the tools write, such as
the published ``report.md``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from report_builder.models import Session


class SessionStore(Protocol):
    """Sessions, by id and by user."""

    def create(self, session: Session) -> Session: ...
    def get(self, session_id: str, user_id: str) -> Session | None: ...
    def list(self, user_id: str) -> list[Session]: ...
    def save(self, session: Session) -> None: ...
    def folder(self, session_id: str) -> Path: ...


class JsonSessionStore:
    """Sessions as JSON files."""

    def __init__(self, root: Path) -> None:
        self.root = root
        root.mkdir(parents=True, exist_ok=True)

    def folder(self, session_id: str) -> Path:
        """The session's folder."""
        return self.root / "sessions" / session_id

    def create(self, session: Session) -> Session:
        self.save(session)
        return session

    def get(self, session_id: str, user_id: str) -> Session | None:
        """The user's session."""
        path = self.folder(session_id) / "session.json"
        if not path.exists():
            return None
        return Session.model_validate_json(path.read_text(encoding="utf-8"))

    def list(self, user_id: str) -> list[Session]:
        """The user's sessions, newest first."""
        found = (Session.model_validate_json(p.read_text(encoding="utf-8"))
                 for p in (self.root / "sessions").glob("*/session.json"))
        return sorted((s for s in found if s.user_id == user_id), key=lambda s: s.created_at, reverse=True)

    def save(self, session: Session) -> None:
        """Write the session."""
        path = self.folder(session.id) / "session.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(session.model_dump_json(indent=1), encoding="utf-8")
