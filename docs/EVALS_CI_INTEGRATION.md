# Gating releases on ClawMetry golden evals

This is the 2-minute guide for wiring `clawmetry eval` into a CI pipeline so
a prompt regression blocks the PR before it ships.

## What you get

- One YAML file (`evals/golden.yaml`) in your agent repo describes the
  inputs you want your agent to handle correctly.
- One workflow file (`.github/workflows/clawmetry-evals.yml`, copied from
  [`docs/github-action-template.yml`](github-action-template.yml)) runs
  the suite on every PR.
- Results land in your ClawMetry dashboard so you can chart regression
  rate over time. Phase 1 scores production traffic; Phase 2 scores the
  golden bench.

## Step 1: write a golden suite

Save this as `evals/golden.yaml` in your repo:

```yaml
suite: customer_support
judge_model: claude-haiku-4-5
tests:
  - name: refund_question
    input: "I need a refund for order #12345"
    expected_tools: [lookup_order, process_refund]
    expected_outcome: success
    expected_min_score: 4

  - name: out_of_scope
    input: "What's the weather?"
    expected_tools: []
    expected_outcome: escalated
    expected_min_score: 3
```

Field reference:

| Field | Required | Notes |
|-------|----------|-------|
| `suite` | yes | Logical name. Surfaces in the dashboard tile. |
| `judge_model` | no | Defaults to `claude-haiku-4-5`. Use `gpt-4o-mini` or any model the Phase 1 judge supports. |
| `tests[].name` | yes | Unique per suite. |
| `tests[].input` | yes | The user message your agent receives. |
| `tests[].expected_tools` | no | List of tool names the agent must invoke. `[]` means "must not call any tool". |
| `tests[].expected_outcome` | no | `success`, `escalated`, `failed`, or `any` (default). |
| `tests[].expected_min_score` | no | Minimum LLM-as-judge score (0-5). `0` disables the check. |

## Step 2: drop in the workflow

Copy [`docs/github-action-template.yml`](github-action-template.yml) to
`.github/workflows/clawmetry-evals.yml` in your repo. Two things you need
to customise:

1. Set `CLAWMETRY_EVALS_AGENT_CMD` to the command that invokes your agent
   in eval mode. The default is `openclaw agent --once --json`. Your
   command must read the test input on stdin and print one JSON line on
   stdout:

   ```json
   {"text": "Refund processed", "tools_used": ["lookup_order", "process_refund"], "outcome": "success"}
   ```

2. Add `ANTHROPIC_API_KEY` (or `OPENAI_API_KEY`, depending on
   `judge_model`) to your repo Secrets.

## Step 3: interpret a failure

A failed run prints a table to the workflow log:

```
TEST            STATUS  SCORE  REASON
--------------  ------  -----  ----------------------------------------------------
refund_question PASS    4.5    Found order and refunded as expected.
out_of_scope    FAIL    2.0    score 2.0 < required 3; outcome='success', expected 'escalated'

1 passed, 1 failed of 2 tests
```

The exit code is `1`, which blocks the merge. The full result JSON is
uploaded as a workflow artefact (`clawmetry-eval-result`) so you can
download it, inspect each turn, and decide whether to fix the prompt or
update the test.

Three failure shapes to recognise:

- `score X < required Y`. The LLM-as-judge thought the response was
  worse than your bar. Read the `REASON` text; it's the judge's
  one-sentence verdict.
- `missing tools: [...]`. The agent skipped a tool the test required.
  Usually a prompt regression or a tool description change.
- `outcome='X', expected 'Y'`. The agent classified the turn
  differently than expected. Often means the test needs updating after
  an intentional product change.

## Local dev loop

```bash
# Run once
clawmetry eval --suite golden

# Re-run on every save (dev loop while iterating on a prompt)
clawmetry eval --suite golden --watch

# See what suites are installed
clawmetry eval --list

# Skip DuckDB persistence (good for noisy iteration)
clawmetry eval --suite golden --no-persist
```

`clawmetry eval` uses the same judge plumbing as Phase 1's automatic
scoring, so the rubric + rate limit guards still apply: 100 judge calls
per hour, sessions under 10 tokens skipped. A 20-test suite costs ~$0.02
with the default Haiku judge.

## Trend analysis

Every run writes one row per test to the local DuckDB `eval_suite_runs`
table. The dashboard's eval tile reads it alongside Phase 1's
production-traffic scores so you can see regression-rate per suite over
time without standing up a separate analytics stack.

## What this replaces

If you were previously running evals through LangSmith, Langfuse, or
Phoenix: same shape (judge model + rubric + a test bench) but the
prompts, responses, and rubric never leave your machine. Your existing
LLM API key drives the judge; ClawMetry's cloud only sees the aggregate
pass/fail counts via the normal heartbeat relay.

See PR #1623 for the Phase 1 design rationale; this Phase 2 PR (refs
#1619) layers the golden-bench surface on top.
