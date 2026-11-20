# Report Builder: take-home challenge

Report Builder is a small agent that writes a monthly review for Harbour Bikes, a fictional bike-rental company. A
model reads a Markdown template and computes metrics with tools. It writes the report section by section, runs the checks a report must pass before publish, then publishes it (writes report.md into the session folder).

There is no live LLM here: a scripted model replays fixed replies from `scripts/demo_run.json`. Everything runs offline without
an API key, and the tests are deterministic.

Part of the code is unfinished and part of it has problems. The tasks below get harder as they go.

## Tips

The time is short, so work from the tasks, not from the whole repository:

- **Start from the task, not the codebase.** Each task names the file to change and the test that must pass, and the
  docstrings are the specification. Read what the task touches; you do not need to understand every module first.
  You will pick up how the pieces fit together as you go.
- **Run the task's tests early and often**, for example `uv run pytest tests/test_task1_template.py`.
- **Move on if you are stuck.** Tasks 1 to 3 do not depend on each other.
- **Understand what you hand in.** In the follow-up you will walk us through your code and change it live.

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
templates/monthly_review.md     the report: title, intro and "## " sections with {{placeholders}}
data/                           rentals, budget and the catalogue (including names a report should not show)
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

How the agent loop works (the demo starts this for you and prints the transcript):

1. The user sends a message.
2. The agent asks the model for a reply.
3. The agent runs each tool call in the reply and adds the results to the conversation.
4. Steps 2 and 3 repeat until the model replies with text only.

## Tasks

### Part A

**1. Values and placeholders.** Implement `fmt` and `fill` in `template.py`. The docstrings are the specification, and
`tests/test_task1_template.py` must pass.

**2. Metrics.** Implement `ratio`, `by_station` and `top_customers` in `data.py`. `tests/test_task2_metrics.py` must
pass. Optional: add one test of your own for an edge case the given tests do not cover.

**3. Pre-publish checks.** Implement `check_report` in `checks.py`. `tests/test_task3_checks.py` must pass.

### Part B

**4. Handle tool errors.** Run the demo. A refused tool call currently aborts the whole run. Change the loop in `agent.py`
so that a refusal (`ToolError`), an unknown tool, or bad arguments are returned to the model as error results. The run should fail only after `MAX_TOOL_ERRORS` errors since the user's last message. `tests/test_task4_agent_errors.py`
must pass.

**5. Publish the demo.** After task 4 the run completes but does not write report.md / reach published. Fix that, without:

- weakening any check;
- editing `scripts/demo_run.json`;
- changing the given tests.

`tests/test_task5_demo.py` must pass.

### Part C

**6. Ask before publishing.** `publish_report` is registered with `requires_approval=True`, but the loop ignores the
flag. Make the run stop before such a call and wait for the user's decision, then carry on. This must work in the same
process and after a restart.

Add `POST /sessions/{id}/approval` with `{"approved": bool, "reason": str | null}`. We will talk
through your choices in the interview.

**7. Harden the API.** Review `api.py` and `store.py` as you would a colleague's pull request and fix two things: what one user can see of another user's sessions, and what happens when two requests arrive at once for the same session. If you have time, add a review on what else you would change in those files.

## Using AI tools

We encourage you to use coding agents. We want to see how you work with them. Please copy your whole conversation with the agent to the `AI_LOG.md` and mentioned this:

- the tools you used;
- three to five prompts that mattered;
- at least one place where you rejected or corrected what the tool produced, and why.

We will ask you about it in the follow-up interview.

## Rules

- Do not change the given tests. You may add tests.
- Do not change `scripts/demo_run.json` or the checks' specification in the docstrings.
- Keep the code style of the repository. `uv run ruff check src tests` should pass.
- Do not commit anything.

## What to send us

Send a zip of the repository (or an invitation to a private repository) with your code, `NOTES.md` and `AI_LOG.md`.

The follow-up is a 45-minute call. You will walk us through your solution and make a small change live with your usual
tools, and we will discuss a few design questions.
