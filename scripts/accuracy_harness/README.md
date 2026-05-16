# Accuracy Harness

Synthetic ground-truth verifiers for ClawMetry features. **Tokens** was the
proof-of-concept (PR #1395); **approvals** is the second harness;
**alerts** is the third; **all.py** is the meta-runner skeleton that wraps
every sub-harness and produces ONE scoreboard. The same shape extends to
channels / crons next.

## Why

The dashboard sources its numbers from three pipelines (transcript scan,
OTLP, DuckDB local-store fast path) and three time windows (today / week
/ month). Bugs creep in at every join: timezone bucketing, cache TTLs,
event-type whitelists, session-start vs event-timestamp drift. Manual
spot-checking by reading the UI doesn't catch silent regressions.

A harness that **drives known traffic, then asserts the dashboard
matches** is the cheapest way to keep all those joins honest.

## The shape (this extends to approvals + alerts)

```
1. baseline   = scrape feature endpoints, snapshot current totals
2. ground     = drive N synthetic events with known properties
                (record what we sent — that's the source of truth)
3. flush      = poll the sync daemon until our N events have landed
                (event-count delta, not wall-clock guess)
4. probe      = re-scrape feature endpoints across every window
                (1h / 24h / 7d / 30d — whatever the feature exposes)
5. assert     = (after - before) == ground, within tolerance, per metric
6. report     = clean PASS table, OR file a GitHub issue per drift with
                the ground-truth log + a reproducer snippet
```

Every step is feature-agnostic. Approvals will swap step 2 for
`gateway.approvals.request(...)`; alerts will swap it for tripping a
threshold. Steps 1/3/4/5/6 stay identical — that's the harness shape.

## Running it

```bash
# Meta-runner: shell out to every sub-harness, aggregate scoreboard.
python3 scripts/accuracy_harness/all.py

# Subset.
python3 scripts/accuracy_harness/all.py --harnesses tokens,alerts

# Smoke-test the runner without touching OpenClaw / spending LLM budget.
python3 scripts/accuracy_harness/all.py --dry-run --no-issue

# Or run individual harnesses ─────────────────────────────────────────
# Tokens: default 3 messages, auto-detect dashboard on 8900/8903/8905
python3 scripts/accuracy_harness/tokens.py

# Approvals: drives 1 approve + 1 deny round
python3 scripts/accuracy_harness/approvals.py

# Alerts: drives 1 threshold rule + verifies fire + dispatch round-trip.
# The natural eval cadence is 60s and the evaluator reads an OTLP-fed
# in-memory buffer, NOT DuckDB — so the harness installs a synchronous
# test hook (gated by CLAWMETRY_HARNESS_HOOKS=1) that injects a cost
# entry + runs one eval pass immediately.
CLAWMETRY_HARNESS_HOOKS=1 python3 scripts/accuracy_harness/alerts.py

# Custom message count + URL
CLAWMETRY_URL=http://localhost:8903 \
  python3 scripts/accuracy_harness/tokens.py --messages 5

# File a GitHub issue per drift (default: print only)
python3 scripts/accuracy_harness/tokens.py --file-issues
python3 scripts/accuracy_harness/approvals.py --file-issues
CLAWMETRY_HARNESS_HOOKS=1 python3 scripts/accuracy_harness/alerts.py --file-issues
```

### Meta-runner (`all.py`)

`all.py` is a thin runner: it shells out to each registered sub-harness
(`tokens.py`, `approvals.py`, `alerts.py`) with a 180s per-harness
timeout, parses each one's `summary: N pass / N drift` line, prints a
single scoreboard, and exits with the worst observed status. **It does
not re-implement any harness logic** — sub-harnesses already own
ground-truth driving and per-endpoint assertions.

| flag | meaning |
|---|---|
| `--harnesses tokens,approvals,alerts` | comma-separated subset (default: all registered) |
| `--no-issue` | skip the (future) consolidated drift-issue filer |
| `--dry-run` | short-circuit before shelling out — proves the runner skeleton without spending LLM budget. **Not passed through**: sub-harnesses don't yet support `--dry-run`. |

Exit codes:

| code | meaning |
|---:|---|
| 0 | every sub-harness PASS-ed |
| 1 | at least one drift, no errors |
| 2 | at least one harness errored or timed out |

The consolidated GitHub-issue filer is intentionally **not** implemented
in this PR — `file_consolidated_issue` only PRINTS what it would file
(`Would file consolidated issue: N drifts across M harnesses`). Live
filing lands in the follow-up iteration once the runner is proven in
production. Wire to a cloud cron once that lands.

### Prerequisites

- `openclaw` CLI on `$PATH` (with `agent main` configured)
- ClawMetry dashboard running locally (any of ports 8900/8903/8905)
- Sync daemon running (so DuckDB gets the new events) — discovery file
  at `~/.clawmetry/local_query.json`
- For `alerts.py`: dashboard must be started with
  `CLAWMETRY_HARNESS_HOOKS=1` so the synchronous test hook
  (`/api/_harness/inject-cost`) is wired. Without it the harness falls
  back to the 90s natural eval cadence (still works, just slower).
- For `--file-issues`: `gh` CLI authenticated to `vivekchand/clawmetry`

### What it costs

Each run sends ~3 real LLM calls (short prompt: "Say PONG"). Typical
total: <100 input + <50 output tokens per turn, so **well under $0.10
per full run** on opus-4-7.

### Exit codes

| code | meaning |
|---:|---|
| 0 | every check passed within tolerance |
| 1 | one or more drifts (issue filed if `--file-issues`) |
| 2 | harness itself failed (dashboard down, no openclaw, etc.) |

## What's covered today

### Tokens (`tokens.py`)

| endpoint | window | metrics |
|---|---|---|
| `/api/usage` | today | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | week  | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | month | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | all_14d (full `days[]` array) | input / output / cacheRead / cacheWrite / total |
| `/api/context-anatomy` | live | non-numeric (assert endpoint stays healthy) |

Tolerance: ±1 token per metric; ±3 for cache splits (rounding).

### Approvals (`approvals.py`)

| surface | stage | assertions |
|---|---|---|
| `daemon.query_approvals(status='pending')` | pending | row appears with matching `id`, `action`, `args`, `session_id`, `status='pending'`, `created_at` |
| `/api/nemoclaw/pending-approvals` | pending | dashboard endpoint includes the row + same fields (legacy NemoClaw shape) |
| `daemon.query_approvals(status='approved'\|'denied')` | decided | `status` flips, `decision` matches, `resolver` reflects caller, `decision_reason` round-trips, `resolved_at` is within 30s of now |
| `/api/nemoclaw/pending-approvals` | post-decide | row no longer appears in pending list |

Two rounds per run — one `approve`, one `deny`. The synthetic row uses
`action='harness:noop'` and an `harness-AUDIT_<run_id>-…` id so it can't
collide with a real approval policy or with another harness run.

### Alerts (`alerts.py`)

| surface | stage | assertions |
|---|---|---|
| `POST /api/alerts/rules` | create | rule id surfaces back in `GET /api/alerts/rules`; `type`, `threshold` (±0.001), `enabled` round-trip |
| `GET /api/budget/status` | spend_visibility | `daily_spent` reflects the real openclaw turn we just drove (≥50% of estimated cost). Asserts the OTLP→evaluator pipeline. |
| `POST /api/_harness/inject-cost` (gated hook) | trip | injects $0.01 + runs ONE synchronous eval pass; bypasses the natural 60s `_budget_monitor_loop` tick |
| `GET /api/alerts/history` | fire | row appears with matching `rule_id` / `type='threshold'` / `channel ∈ {banner, webhook}` / message mentions `$0.00` threshold / `triggered_value` within ±5% of the captured `daily_spent` / `fired_at` within 60s of now |
| local webhook listener | dispatch | the generic webhook POST landed with `type='threshold'`, non-empty `message`, severity in `{warning, info, critical}` |
| `DELETE /api/alerts/rules/<id>` | cleanup | rule absent from `GET` after delete (idempotent re-runs) |

The synthetic rule uses a unique UUID-tagged `rule_name_tag`
(`ACCURACY_AUDIT_<run_id>_alert`) and a 1-min cooldown so back-to-back
runs don't suppress each other. The webhook target is a localhost
listener (random port, started in-thread, torn down on exit) — NEVER a
real Slack/Discord/PagerDuty — and the prior webhook config is restored
on every run.

## What's NOT covered yet (next iteration)

### Tokens

- **1-hour window** — `/api/usage` doesn't expose hourly granularity;
  Tokens tab only buckets per-day. To verify "last hour" you need
  `/api/local/events?since=...` direct DuckDB queries. Add as a
  separate check rather than fudging it into `days[]`.
- **/api/usage/by-plugin** — per-plugin cost split (probably correct,
  but not asserted).
- **/api/model-attribution and /api/skill-attribution** — per-model and
  per-skill breakdowns; the harness records `models` in ground truth but
  doesn't assert against these endpoints yet.
- **/api/token-velocity** — needs >1 sample to assert; add a multi-run
  variant in the next iteration.
- **/api/overview** — the headline number on the main tab. Worth
  asserting; it pulls from the same daily buckets so should match
  trivially.
- **Per-session context anatomy** — currently observational only; needs
  a numeric assertion that the new session's bucket reflects the
  ground-truth `cacheRead`.
- **Cost (USD) drift** — we assert tokens. Cost is `tokens × pricing`,
  which can drift independently if pricing tables are stale. Add a
  separate cost check using `providers_pricing.py`.
- **Cloud (`app.clawmetry.com`) round-trip** — the OSS dashboard is the
  source of truth here; the cloud view is downstream. Add a cloud
  variant that asserts the same numbers appear on the encrypted upload
  side within N minutes.

### Approvals

- **No `/api/approvals` endpoint** — the legacy `/api/nemoclaw/pending-approvals`
  is the only public HTTP surface today, and it's `status=pending` only.
  There's no public endpoint to list `decided` rows; the harness asserts
  that path via the daemon proxy (`query_approvals`) instead. **Product
  gap surfaced** by this harness.
- **No `/api/approvals/decide` endpoint** — decisions are made via
  cloud-relay heartbeat (cloud → daemon `_apply_approval_decision`) or
  this harness (direct daemon-proxy `update_approval_decision`). There is
  no OSS-side button for the user to decide an approval. **Product gap.**
- **Policy-watcher trigger path** — the harness writes the approval row
  directly via `ingest_approval`, bypassing `clawmetry/approvals.py`'s
  policy-match → cloud-POST → poll loop. A separate harness needs to
  drive a real policy match end-to-end.
- **`decided_by`/`decided_at` field naming** — the spec uses these names
  but the schema columns are `resolver`/`resolved_at`. Harness asserts
  the schema names; if the dashboard ever exposes the spec names through
  a renderer, add an assertion there.
- **History-row `reason` rendering** — the harness verifies the
  `decision_reason` column round-trips; it does not (yet) verify the
  reason renders in any UI surface, because there's no dashboard tab
  that shows decided approvals today.

### Alerts

- **POST→GET schema split** — `POST /api/alerts/rules` writes to the
  fleet-DB (`SQLite alert_rules` table); `GET /api/alerts/rules` reads
  from the local DuckDB fast path when `CLAWMETRY_LOCAL_STORE_READ=1`.
  Rules created via POST silently vanish from the listing on those
  installs. **Product gap surfaced** by this harness (drift on
  `create/row_present` when LOCAL_STORE_READ=1).
- **OTLP-only evaluator input** — the alert evaluator reads
  `metrics_store["cost"]`, an in-process ring buffer fed ONLY by OTLP
  ingestion. Installs without OTLP traffic flowing have `daily_spent=0`
  forever, so no `threshold` rule can ever fire on real spend.
  **Product gap surfaced** as `spend_visibility/real_spend_visible`
  drift. The fix is to mirror DuckDB cost rows into `metrics_store` on
  a tick.
- **No `alert_dispatch_attempts` table** — webhook dispatch is fire-and-
  forget (`urllib.request.urlopen` wrapped in `except: pass`). There's
  no persistent log of "we tried to POST this payload to this URL at
  this time"; failures are silent. Harness verifies dispatch via a
  local capture listener, but a real audit log would let users debug
  Slack/Discord delivery problems.
- **`spike` and `token_spike` rule types** — only `threshold` is
  exercised today; `spike` needs hourly cost history and `token_spike`
  needs the velocity sliding window. Both can be force-tripped via
  extensions to the harness hook.
- **Cooldown semantics drift** — `_fire_alert` enforces a hard-coded
  1800s cooldown that's distinct from the per-rule `cooldown_min`
  field. The harness uses fresh UUIDs each run so it never hits the
  cooldown; a separate test should exercise the cooldown path
  explicitly.
- **Severity + per-type webhook filters** — `_dispatch_alert` checks
  `_severity_passes_filter` and `_should_send_webhook_for_type` before
  POSTing. Harness uses default config (warning passes); a matrix run
  with `min_severity=critical` should assert the filter actually
  suppresses.

## Idempotency

Safe to re-run. Each run uses a fresh `ACCURACY_AUDIT_<uuid>` tag, so:
- previous runs don't double-count (we measure DELTA, not absolute)
- nothing is written back to the dashboard or DuckDB except real
  OpenClaw traffic the user implicitly authorized by running this
- if a run fails mid-flight, the partial messages stay in OpenClaw
  state but the harness restarts from a fresh baseline next run.

## File layout

```
scripts/accuracy_harness/
├── README.md       # this file
├── __init__.py     # package marker
├── _lib.py         # shared discovery + HTTP + drift-issue helpers
├── tokens.py       # tokens harness (PR #1395)
├── approvals.py    # approvals queue harness (PR #1397)
├── alerts.py       # alert-rule round-trip harness (PR #1399)
└── all.py          # meta-runner skeleton — sub-runs + aggregate scoreboard
```

Shared shims live in `_lib.py` (`discover_dashboard_url`,
`discover_daemon`, `daemon_call`, `drive_openclaw_message`,
`file_drift_issue_per_endpoint`, …) so each new harness can land in a
single self-contained file. Refactor: extract another helper into
`_lib.py` whenever a second harness needs it — no copy-paste.

Future:
```
├── crons.py        # same shape, schedules + verifies a run
└── channels.py     # same shape, drives a channel send + flow
```
