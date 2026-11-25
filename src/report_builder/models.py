"""The records the report builder keeps: sessions, their messages and the release checks."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

Status = Literal["idle", "running", "awaiting_approval", "published", "failed"]


class ToolCall(BaseModel):
    """One call of a tool, as the model asked for it."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:8])
    name: str
    args: dict[str, Any] = Field(default_factory=dict)


class Message(BaseModel):
    """One message of the conversation: the user's, the model's (text and tool calls) or a tool's result."""

    role: Literal["user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None   # a tool message: the call it answers
    is_error: bool = False            # a tool message: the tool refused or failed


class Check(BaseModel):
    """One release check of the report."""

    name: str
    status: Literal["Pass", "Note", "Fail"]
    detail: str
    items: list[str] = Field(default_factory=list)


class Session(BaseModel):
    """One report being written: the dataset and month, what the agent has done so far and the conversation."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_id: str
    dataset: str
    month: str                                              # YYYY-MM
    status: Status = "idle"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    values: dict[str, Any] = Field(default_factory=dict)    # metric name -> value, filled into the template
    sections: dict[str, str] = Field(default_factory=dict)  # template heading -> the section the agent wrote
    checks: list[Check] = Field(default_factory=list)
    messages: list[Message] = Field(default_factory=list)
