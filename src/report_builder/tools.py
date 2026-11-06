"""
The agent's tools.

A tool is a function ``(ctx, **args) -> result`` registered with ``@tool``. Its docstring is the description the model
reads; its signature gives the parameters. A tool that refuses raises ``ToolError``: the message goes back to the
model, which may try again. A tool registered with ``requires_approval=True`` runs only after the user approves it.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from report_builder import checks, template
from report_builder.data import METRICS, Dataset, month_label
from report_builder.models import Check, Session

WORD_BUDGET = 120   # words of prose a section holds


class ToolError(Exception):
    """A tool refused: the message goes back to the model."""


@dataclass
class ToolContext:
    """What a tool works on: the session, its dataset and template, and the session's folder."""

    session: Session
    dataset: Dataset
    template: str
    folder: Path


@dataclass(frozen=True)
class Tool:
    """A registered tool."""

    name: str
    func: Callable[..., Any]
    requires_approval: bool = False

    @property
    def description(self) -> str:
        return inspect.getdoc(self.func) or ""

    def spec(self) -> dict[str, Any]:
        """The tool as a model reads it: name, description and a JSON schema of its parameters."""
        hints = get_type_hints(self.func)
        props: dict[str, Any] = {}
        required: list[str] = []
        for name, param in list(inspect.signature(self.func).parameters.items())[1:]:   # [0] is ctx
            props[name] = _schema(hints.get(name, str))
            if param.default is inspect.Parameter.empty:
                required.append(name)
        return {"name": self.name, "description": self.description,
                "input_schema": {"type": "object", "properties": props, "required": required}}


def _schema(hint: Any) -> dict[str, Any]:
    if get_origin(hint) in (Union, UnionType):
        inner = [a for a in get_args(hint) if a is not type(None)]
        return _schema(inner[0]) if len(inner) == 1 else {}
    return {str: {"type": "string"}, int: {"type": "integer"}, float: {"type": "number"},
            bool: {"type": "boolean"}}.get(hint, {})


TOOLS: dict[str, Tool] = {}


def tool(*, requires_approval: bool = False) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Register a function as a tool under its own name."""

    def register(func: Callable[..., Any]) -> Callable[..., Any]:
        TOOLS[func.__name__] = Tool(func.__name__, func, requires_approval)
        return func

    return register


def base_values(ctx: ToolContext) -> dict[str, Any]:
    """The values every report has, before any metric is computed."""
    return {"dataset": ctx.dataset.title, "month": month_label(ctx.session.month), "currency": ctx.dataset.currency}


def working_report(ctx: ToolContext) -> tuple[str, list[str]]:
    """The report as it stands: the template with the written sections, filled; and the names not filled."""
    text = template.assemble(ctx.template, ctx.session.sections)
    return template.fill(text, {**base_values(ctx), **ctx.session.values})


def run_checks(ctx: ToolContext) -> list[Check]:
    """Run the release checks on the report as it stands and keep them on the session."""
    filled, _ = working_report(ctx)
    ctx.session.checks = checks.check_report(filled, ctx.session.sections, template.headings(ctx.template),
                                             ctx.dataset.hidden, WORD_BUDGET)
    return ctx.session.checks


def as_text(result: Any) -> str:
    """A tool's result as the model reads it."""
    if isinstance(result, str):
        return result
    return json.dumps(result, default=str, indent=1)


# --- tools ---------------------------------------------------------------------------------------------------------

@tool()
def read_template(ctx: ToolContext, heading: str | None = None) -> str:
    """The report template (Markdown), or one section of it by heading."""
    if heading is None:
        return ctx.template
    for h, body in template.split(ctx.template):
        if h == heading:
            return f"## {h}{body}"
    raise ToolError(f"no section {heading!r}: the sections are {', '.join(template.headings(ctx.template))}")


@tool()
def list_metrics(ctx: ToolContext) -> list[str]:
    """The metrics compute_metric can compute."""
    return sorted(METRICS)


@tool()
def compute_metric(ctx: ToolContext, name: str) -> Any:
    """
    Compute a metric for the session's month and keep it for the report: {{name}} or {{table:name}} then shows it.

    Returns the value (a table as Markdown).
    """
    if name not in METRICS:
        raise ToolError(f"unknown metric {name!r}: call list_metrics")
    value = METRICS[name](ctx.dataset, ctx.session.month)
    ctx.session.values[name] = value
    return template.markdown_table(value) if isinstance(value, list) else value


@tool()
def save_section(ctx: ToolContext, heading: str, markdown: str) -> str:
    """
    Write one section of the report (its body, without the heading). Saving a section again replaces it.

    Use placeholders for figures: {{name}}, {{name|pct}}, {{name|money}}, {{name|int}}, {{table:name}}.
    """
    known = template.headings(ctx.template)
    if heading not in known:
        raise ToolError(f"no section {heading!r}: the sections are {', '.join(known)}")
    if template.HEADING.search(markdown):
        raise ToolError("a section's body cannot hold a '## ' heading: write one section per call")
    ctx.session.sections[heading] = markdown
    return f"saved {heading} ({checks.prose_words(markdown)} words)"


@tool()
def check_report(ctx: ToolContext) -> list[dict[str, Any]]:
    """Run the release checks on the report as it stands. Every Fail must be fixed before publish_report."""
    return [c.model_dump() for c in run_checks(ctx)]


@tool(requires_approval=True)
def publish_report(ctx: ToolContext) -> str:
    """Publish the report. Runs the release checks first and refuses while any of them fails. Needs the user's
    approval."""
    failed = [c.name for c in run_checks(ctx) if c.status == "Fail"]
    if failed:
        raise ToolError(f"not published: these checks fail: {', '.join(failed)}")
    filled, _ = working_report(ctx)
    ctx.folder.mkdir(parents=True, exist_ok=True)
    (ctx.folder / "report.md").write_text(filled, encoding="utf-8")
    ctx.session.status = "published"
    return "published report.md"
