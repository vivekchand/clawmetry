# MOAT Bar (canonical PRD)

> One file. Scannable. If you are tired and it is midnight, read this and the 13-row table in Section 2. That is the bar.

| | |
|---|---|
| **Status** | Active (canonical) |
| **Owner** | @vivekchand |
| **Last refreshed** | 2026-05-18 |
| **Companion** | [MOAT_PERMANENCE_PRD.md](MOAT_PERMANENCE_PRD.md) (architecture deep-dive), [MOAT_COVERAGE.md](MOAT_COVERAGE.md) (per-route matrix) |
| **Evidence PRs** | OSS [#1672](https://github.com/vivekchand/clawmetry/pull/1672), [#1673](https://github.com/vivekchand/clawmetry/pull/1673), [#1675](https://github.com/vivekchand/clawmetry/pull/1675), [#1678](https://github.com/vivekchand/clawmetry/pull/1678) — Cloud [#975](https://github.com/vivekchand/clawmetry-cloud/pull/975), [#978](https://github.com/vivekchand/clawmetry-cloud/pull/978) |

---

## Section 1. What is the MOAT

The mandate is one sentence repeated three ways so no future contributor can pretend it is ambiguous.

**Every UI element queries local DuckDB.** Not "most." Not "the migrated ones." Every dashboard panel, every chart, every cron list, every channel feed reads through `_try_local_store_*` and lands on the user's local DuckDB via the daemon-proxy at `localhost:4099/local_query/*`. JSONL walkers, in-memory rings, and direct `psutil` historical samples are bugs, not fallbacks. (See `feedback_duckdb_first_rule.md` — "DuckDB-first hard rule for every feature.")

**Every event writes to DuckDB.** The sync daemon owns the writer lock; OpenClaw v3 events are normalised at the chokepoint in `clawmetry/sync.py::_parse_v3_event` and round-tripped through `query_aggregates` / `query_events`. Synthetic test rows must carry real v3 namespaced types (`model.completed`, `prompt.submitted`, `session.started`) or they pass while production silently flunks. (See `feedback_synthetic_tests_missed_real_event_shape.md` — burned 3 of 7 migrations on 2026-05-15.)

**Cloud is a display layer over E2E-encrypted aggregates.** Cloud SQL stores `user_id`, `plan_tier`, `last_seen`, and opaque aggregates. The wire format is AES-256-GCM; the key never leaves the customer daemon. Cloud cannot decrypt the heartbeat-piggyback `pending_queries` cache. A breach of Cloud SQL leaks plan tier and a timestamp; it does not leak prompts. (See `project_local_compute_cloud_display.md` — "Local compute, cloud display.")

If any of those three sentences becomes false on `main`, the MOAT is broken and shipping stops.

---

## Section 2. The 13-endpoint keystone bar (verified 2026-05-18)

The 13 probes in `scripts/accuracy_harness/keystone_e2e.py` (PR [#1672](https://github.com/vivekchand/clawmetry/pull/1672)) are the bar. The harness drives one real `openclaw agent --message` turn, waits for the event to land in DuckDB via daemon flush, then hits every endpoint a real user reads on page load. Green = MOAT intact. Red = P0.

| # | Endpoint | DuckDB classification | Keystone probe | Last verified PASS |
|---|---|---|---|---|
| 1 | `/api/brain-history` | HYBRID | `events_gt_0` + `types_include_v3` (`MODEL.COMPLETED` / `PROMPT.SUBMITTED` / `SESSION.STARTED`) | 2026-05-18T23:35Z |
| 2 | `/api/sessions` | FAST | `sessions_gt_0` | 2026-05-18T23:35Z |
| 3 | `/api/transcript/<id>` | HYBRID | `messages_gt_0` (uses sid from #2) | 2026-05-18T23:35Z |
| 4 | `/api/usage` | FAST | `days_nonempty` + `nonzero_days > 0` + `modelBreakdown_nonempty` | 2026-05-18T23:35Z |
| 5 | `/api/flow` | HYBRID | `shape_ok` (`.events` + `.ok` keys present, `ok=true`) | 2026-05-18T23:35Z |
| 6 | `/api/component/tool/exec` | HYBRID | `shape_ok` (`.stats` + `.events` present; counts may be 0 today) | 2026-05-18T23:35Z |
| 7 | `/api/component/runtime` | OTHER (live probe) | `items_gt_0` (`.items` or `.routes` non-empty) | 2026-05-18T23:35Z |
| 8 | `/api/component/machine` | OTHER (live probe) | `items_gt_0` | 2026-05-18T23:35Z |
| 9 | `/api/component/gateway` | HYBRID | `items_gt_0` | 2026-05-18T23:35Z |
| 10 | `/api/system-health` | FAST | `sections_present` (any of `channels`/`channel_ingest`/`system`/`crons`/`disk`/`memory`) | 2026-05-18T23:35Z |
| 11 | `/api/subagents` | FAST | `shape_ok` (`.subagents` + `.counts` present; empty list OK) | 2026-05-18T23:35Z |
| 12 | `/api/crons` | FAST | `shape_ok` (`.jobs` present; empty list OK) | 2026-05-18T23:35Z |
| 13 | `/api/memory-files` | FAST | `files_gt_0` (every install ships `AGENTS.md` / `SOUL.md`) | 2026-05-18T23:35Z |

**This table IS the bar.** If any row turns red on nightly run, MOAT is broken and the on-call response is a P0.

On any FAIL the harness prints the DuckDB `event_type` histogram inline, so silent-zero root cause (predicate-vs-shape skew per `feedback_synthetic_tests_missed_real_event_shape.md`) is the very next line in the output.

---

## Section 3. Coverage matrix summary

Pulled from [`docs/MOAT_COVERAGE.md`](MOAT_COVERAGE.md) (PR [#1678](https://github.com/vivekchand/clawmetry/pull/1678)).

| Headline | Number |
|---|---|
| Total `@bp.route` handlers across `routes/*.py` | **248** |
| `FAST` (pure DuckDB fast path) | **68** (27.4%) |
| `HYBRID` (DuckDB fast path + legacy fallback) | **37** (14.9%) |
| `BYPASS_FS` (JSONL / log walker) | **6** (2.4%) |
| `BYPASS_RING` (in-memory OTLP ring) | **2** (0.8%) |
| `SSE` (live tail, deferred by design) | **2** |
| `RPC` (gateway WebSocket proxy) | **10** |
| `OTHER` / STATIC | **123** |
| **DuckDB-genuine coverage** (FAST + HYBRID) | **105 / 248 = 42% of all routes** |
| **DuckDB-genuine coverage** of data-bearing routes (drop STATIC + SSE + RPC + LIVE_PROBE) | **105 / 113 = 93%** |

Full per-file scoreboard + full route table live in `docs/MOAT_COVERAGE.md`. Re-run the classifier against `origin/main` on every audit cadence (weekly, Friday).

---

## Section 4. Known gaps + remediation order

In priority order. None of these block the MOAT claim today; all are tracked.

| # | Gap | Status | Owner |
|---|---|---|---|
| 1 | **Tier-1 remaining real bypass surfaces** — `GET /api/otel-status` (BYPASS_RING by design, receiver-canary) + `GET /api/usage/cache-trends` (schema gap, needs per-model cache split). | 2 real candidates left after PRs [#1673](https://github.com/vivekchand/clawmetry/pull/1673) + [#1675](https://github.com/vivekchand/clawmetry/pull/1675). 4 more are by-design (SSE, LIVE_PROBE, STATIC bootstrap, Apple SQLite). | Principal #2 audit |
| 2 | **Tier-2 schema work for `/api/usage/cache-trends`** — `query_daily_usage_splits` needs per-model rows OR new `query_cache_trends`. | MEDIUM confidence; schema-first PR before route migration. | Principal #2 |
| 3 | **Cloud-side keystone mirror** — `cloud_keystone_e2e.py` equivalent that asserts cloud's display layer never reads event payloads server-side. | In flight as cloud PRs [#975](https://github.com/vivekchand/clawmetry-cloud/pull/975) + [#978](https://github.com/vivekchand/clawmetry-cloud/pull/978) (Principal B). | Principal B |
| 4 | **Failure-mode keystone coverage** — tool-call probes + subagent failure probes to extend the 13-row bar with stress scenarios. | In flight (Principal A). | Principal A |
| 5 | **HYBRID channel cleanup** — drop the JSONL augment from 7 channels (`telegram`, `whatsapp`, `signal`, `discord`, `slack`, `irc`, `webchat`) once daemon channel-message ingest catches up. | Tracked separately; not blocking. | — |

---

## Section 5. Acceptance criteria for "MOAT permanent"

These are the five checkboxes the MOAT lives or dies by. When all five are continuously green on `main`, the MOAT is permanent. Each row needs an automated owner; "manual review" does not count.

- [ ] **1. `keystone_e2e.py --no-drive` exits 0 on every PR.** Wire into CI as a required check on `routes/*.py`, `clawmetry/sync.py`, `clawmetry/local_store.py`, and `dashboard.py` diffs. Blocks merge on red.
- [ ] **2. `keystone_e2e.py` (drive mode) runs nightly + posts to a tracking issue.** Real `openclaw agent --message` turn against a CI-controlled OpenClaw install. If any of the 13 endpoints flaps to FAIL, file P0 and page the on-call.
- [ ] **3. `cloud_keystone_e2e.py` (Principal B) runs nightly + same SLA.** Asserts cloud's display layer never reads event payloads server-side; asserts heartbeat-piggyback ciphertext path is the only data wire.
- [ ] **4. Coverage matrix says >95% of data-bearing routes on DuckDB.** Re-run `docs/MOAT_COVERAGE.md` classifier weekly (Friday). Today: 93%. Gap: 2 surfaces (per Section 4).
- [ ] **5. No new feature ships without adding a keystone probe.** Every new data-bearing endpoint adds one row to Section 2's table AND one probe to `keystone_e2e.py`. Enforced in PR review checklist; lint follows once `_try_local_store_*` lint pattern is stable.

If any of these turns red, **stop shipping features. Fix the gate.**

---

## Section 6. Operational runbook

### How to run the keystone locally

```bash
# Prerequisite: sync daemon must be running (writer lock owner).
launchctl kickstart -k com.clawmetry.sync   # macOS
# OR
clawmetry sync start                         # any platform

# CI smoke mode (no LLM cost; verifies against existing DuckDB rows):
python3 scripts/accuracy_harness/keystone_e2e.py --no-drive

# Full drive mode (sends one real openclaw turn; ~30s wall-clock):
python3 scripts/accuracy_harness/keystone_e2e.py

# Override dashboard URL if not on default 8900:
python3 scripts/accuracy_harness/keystone_e2e.py --dashboard-url http://localhost:8903
```

**Proxy-vs-direct rule (load-bearing):** the harness never opens `clawmetry.duckdb` directly. All DuckDB reads go through the daemon's `/__local_query__/<method>` HTTP proxy. DuckDB locks at the **process level**; `read_only=True` does not bypass this. (See `reference_duckdb_process_lock.md` — PR #1253's `read_only=True` workaround was wrong.)

### How to interpret a FAIL

When the harness prints `FAIL`, the very next line is the DuckDB `event_type` histogram (top 8 of last 500 rows). This is the canonical silent-zero root-cause query.

| Symptom | Likely cause | Fix |
|---|---|---|
| `events>0` fails on `/api/brain-history`, histogram is empty | DuckDB events table is empty; daemon has nothing to serve | Verify daemon is writing: `curl localhost:4099/local_query/event_count` |
| `nonzero_days` fails on `/api/usage`, histogram shows `message=N` | Predicate-vs-shape skew: route is filtering for legacy `'message'` instead of v3 `'model.completed'` | Grep `routes/usage.py` for `'message'` predicate; fix to v3 namespaced type |
| `sessions>0` fails, histogram shows `session.started=N` | Route is filtering for legacy session shape | Check `routes/sessions.py::_try_local_store_sessions` for stale predicate |
| `transcript empty` on a sid that exists | Transcript reader is hitting JSONL, not DuckDB messages table | Audit `routes/sessions.py::api_transcript` for fast-path coverage |
| All 13 probes 500-error | Dashboard not running OR daemon-proxy unreachable | `curl localhost:8900/api/sessions` to triage |

Always check the histogram first. The `feedback_synthetic_tests_missed_real_event_shape.md` failure mode looks like a logic bug but is almost always a predicate-vs-shape skew between the test fixture and real OpenClaw v3 events.

### How to add a new probe

Pattern in `scripts/accuracy_harness/keystone_e2e.py`:

```python
def check_<surface>(dashboard: str) -> Check:
    ep = "/api/<your-endpoint>"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    # 1. Shape assertion: required top-level keys present.
    # 2. Non-zero assertion (only if endpoint is data-bearing on every install).
    # 3. Type-namespace assertion (only if endpoint surfaces event types).
    ...
    return Check(ep, "<assertion-label>", "pass", "<detail-for-diagnostics>")
```

Then:

1. Append the `check_<surface>(dashboard)` call to the `checks` list in `run()`.
2. Add a row to Section 2's 13-endpoint table in this PRD.
3. Smoke locally with `--no-drive` AND a full drive run before opening the PR.
4. Update the PR description's "Test plan" with the keystone summary line.

Reference harness pattern: see the existing 13 probes in `scripts/accuracy_harness/keystone_e2e.py` lines 183-374.

---

## References

- `scripts/accuracy_harness/keystone_e2e.py` — the verifier (PR [#1672](https://github.com/vivekchand/clawmetry/pull/1672))
- `docs/MOAT_COVERAGE.md` — per-route matrix (PR [#1678](https://github.com/vivekchand/clawmetry/pull/1678))
- `docs/MOAT_PERMANENCE_PRD.md` — architecture deep-dive + 4-gate permanence stack
- `feedback_duckdb_first_rule.md` — the hard rule
- `feedback_synthetic_tests_missed_real_event_shape.md` — predicate-vs-shape skew failure mode
- `project_local_compute_cloud_display.md` — cloud is a display layer, not a data store
- `reference_openclaw_v3_event_types.md` — v3 event namespace map
- `reference_duckdb_process_lock.md` — why daemon-proxy is the only correct read path
- `feedback_daemon_proxy_pattern.md` — 5-step migration playbook
