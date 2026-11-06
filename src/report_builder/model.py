"""
The model behind the agent.

The agent only needs ``Model.respond``: given the system prompt, the conversation and the tools, the next assistant
message (text, tool calls or both). ``ScriptedModel`` replays a fixed run from a JSON file, so the whole agent runs
and is tested without an API key. A real LLM can be put behind the same interface.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Protocol

from report_builder.models import Message, ToolCall

ROOT = Path(__file__).resolve().parents[2]
DEMO_SCRIPT = ROOT / "scripts" / "demo_run.json"


class Model(Protocol):
    """Anything that answers the conversation with the next assistant message."""

    def respond(self, system: str, messages: list[Message], tools: list[dict[str, Any]]) -> Message:
        """The next assistant message."""
        ...


class ScriptedModel:
    """
    Replays a script: a list of steps, each ``{"text": ..., "calls": [{"tool": ..., "args": {...}}]}``.

    The step played is the number of assistant messages in the conversation so far, so a run that stops (for an
    approval, say) and resumes later carries on where it was. A tool result does not change the script: the script
    already knows which calls will be refused.
    """

    def __init__(self, steps: list[dict[str, Any]]) -> None:
        self.steps = steps

    @classmethod
    def from_file(cls, path: Path = DEMO_SCRIPT) -> ScriptedModel:
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def respond(self, system: str, messages: list[Message], tools: list[dict[str, Any]]) -> Message:
        position = sum(1 for m in messages if m.role == "assistant")
        if position >= len(self.steps):
            return Message(role="assistant", content="[end of script]")
        step = self.steps[position]
        calls = [ToolCall(id=f"call_{position}_{i}", name=c["tool"], args=c.get("args", {}))
                 for i, c in enumerate(step.get("calls", []))]
        return Message(role="assistant", content=step.get("text", ""), tool_calls=calls)
