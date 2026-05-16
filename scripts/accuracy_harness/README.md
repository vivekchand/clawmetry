# Accuracy Harness

Synthetic ground-truth verifiers for ClawMetry features. **Tokens is the
proof-of-concept**; the same shape extends to approvals and alerts next.

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
# Default: 3 messages, auto-detect dashboard on 8900/8903/8905
python3 scripts/accuracy_harness/tokens.py

# Custom message count + URL
CLAWMETRY_URL=http://localhost:8903 \
  python3 scripts/accuracy_harness/tokens.py --messages 5

# File a GitHub issue per drift (default: print only)
python3 scripts/accuracy_harness/tokens.py --file-issues
```

### Prerequisites

- `openclaw` CLI on `$PATH` (with `agent main` configured)
- ClawMetry dashboard running locally (any of ports 8900/8903/8905)
- Sync daemon running (so DuckDB gets the new events) — discovery file
  at `~/.clawmetry/local_query.json`
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

| endpoint | window | metrics |
|---|---|---|
| `/api/usage` | today | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | week  | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | month | input / output / cacheRead / cacheWrite / total |
| `/api/usage` | all_14d (full `days[]` array) | input / output / cacheRead / cacheWrite / total |
| `/api/context-anatomy` | live | non-numeric (assert endpoint stays healthy) |

Tolerance: ±1 token per metric; ±3 for cache splits (rounding).

## What's NOT covered yet (next iteration)

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
└── tokens.py       # tokens-first harness (this PoC)
```

Future:
```
├── approvals.py    # same shape, drives approval requests
├── alerts.py       # same shape, trips known thresholds
└── _common.py      # shared discovery + reporting helpers
                    # (factor out once 2+ harnesses exist)
```
