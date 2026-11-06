# Report Builder: take-home challenge

Report Builder is a small agent that writes a monthly review for Harbour Bikes, a fictional bike-rental company. A
model reads a Markdown template and computes metrics with tools. It writes the report section by section, runs
release checks and publishes.

The model here is **scripted**: it replays a fixed run from `scripts/demo_run.json`. Everything runs offline without
an API key, and the tests are deterministic.

Part of the code is unfinished and part of it has problems. The tasks below get harder as they go.

| Role | Tasks | Time box |
| --- | --- | --- |
| Junior AI engineer | 1 to 5 | about 3 hours |
| Senior backend developer | 1 to 8, with the weight on 6 to 8 | about 5 hours |

Please stop at the time box. A clear note of what you would do next is worth more than a rushed finish.

## Setup

You need Python 3.12 and [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run pytest                          # most tests fail until you finish the tasks
uv run python -m report_builder.demo   # the scripted run, end to end
uv run uvicorn report_builder.api:app --reload   # the HTTP API (callers name themselves in X-User)
```

## How it fits together

```
templates/monthly_review.md     the report: front matter and "## " sections with {{placeholders}}
data/                           rentals, budget and the catalogue (including names a report must never show)
src/report_builder/
  models.py      Session, Message, ToolCall, Check
  data.py        loading datasets; the metrics the tools compute
  template.py    sections, placeholders, number formats, Markdown tables
  checks.py      the release checks a report must pass before it is published
  tools.py       the tools the model can call (registered with @tool)
  model.py       the Model interface and the ScriptedModel
  agent.py       the agent loop
  store.py       sessions as JSON files
  api.py         the FastAPI app
  demo.py        runs the scripted model end to end
```

A run works like this:

1. The user sends a message.
2. The agent asks the model for a reply.
3. The agent runs each tool call in the reply and adds the results to the conversation.
4. Steps 2 and 3 repeat until the model replies with text only.

The model writes each figure as a placeholder (`{{revenue_month|money}}`, `{{table:by_station}}`). The report fills the
placeholders from the metrics the model computed, so no number is ever typed by the model.

## Tasks

### Part A: everyone

**1. Values and placeholders.** Implement `fmt` and `fill` in `template.py`. The docstrings are the specification, and
`tests/test_task1_template.py` must pass.

**2. Metrics.** Implement `ratio`, `by_station` and `top_customers` in `data.py`. `tests/test_task2_metrics.py` must
pass. Then add at least one test of your own for an edge case the given tests do not cover, and say in `NOTES.md` why it
matters.

**3. Release checks.** Implement `check_report` in `checks.py`. `tests/test_task3_checks.py` must pass.

### Part B: everyone

**4. The run falls over.** Run the demo. When a tool refuses a call, the whole run ends. Change the loop in `agent.py`
so that a refusal (`ToolError`), an unknown tool or bad arguments go back to the model as an error result it can act
on. The run should fail only after `MAX_TOOL_ERRORS` errors since the user's last message. `tests/test_task4_agent_errors.py`
must pass.

**5. Publish the demo.** After task 4 the demo runs to the end but still does not publish. Make it publish, without:

- weakening any check;
- editing `scripts/demo_run.json`;
- changing the given tests.

`tests/test_task5_demo.py` must pass. In `NOTES.md`, say where you made the fix and why there.

### Part C: senior role

**6. Ask before publishing.** `publish_report` is registered with `requires_approval=True`, but the loop ignores the
flag. Make the run stop before such a call and wait for the user's decision, then carry on. This must work in the same
process and after a restart.

Add `POST /sessions/{id}/approval` with `{"approved": bool, "reason": str | null}`. You decide, and should explain:

- what happens to the other calls in the same reply;
- what the model is told when the user declines;
- what a second approval does;
- what a new message does while a decision waits.

Write the tests.

**7. Harden the API.** Review `api.py` and `store.py` as you would a colleague's pull request before many users rely on
it. Fix what matters most. At least cover what one user can see of another user's sessions, and what happens when two
requests arrive at once for the same session. List the rest in `NOTES.md` in order of importance. Write the tests.

**8. Design note.** In `DESIGN.md` (one page at most), explain how you would run this for real. Cover:

- many users and several API workers;
- a real LLM;
- streaming a long run to a browser;
- letting the model run its own Python on the data (the next feature on the roadmap) safely;
- keeping cost under control;
- how you would know the reports are good.

## Using AI tools

You may use coding agents and AI assistants (Claude Code, Cursor, Copilot, ChatGPT or others), and we encourage it. We
want to see how you work with them. Keep a short `AI_LOG.md`:

- the tools you used;
- three to five prompts that mattered;
- at least one place where you rejected or corrected what the tool produced, and why.

We will ask you about it in the follow-up interview.

Optional, and not scored for the junior role: put a real LLM behind the `Model` interface in `model.py`. Never commit a
key.

## Rules

- Do not change the given tests. You may add tests.
- Do not change `scripts/demo_run.json` or the checks' specification in the docstrings.
- Keep the code style of the repository. `uv run ruff check src tests` should pass.

## What to send us

Send a zip of the repository (or an invitation to a private repository) with your code, `NOTES.md` and `AI_LOG.md`.
Senior candidates also send `DESIGN.md`.

The follow-up is a 60-minute call. You will walk us through your solution and make a small change live with your usual
tools, and we will discuss a few design questions.
