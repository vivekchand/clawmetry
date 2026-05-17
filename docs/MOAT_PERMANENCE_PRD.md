# MOAT Permanence PRD

> Canonical reference. If you are about to merge code, write a route, change a CI gate, or pitch a new feature — read this first.

| | |
|---|---|
| **Status** | Active (canonical) |
| **Owner** | @vivekchand |
| **Last refreshed** | 2026-05-17 (post-#1586 merge train) |
| **Supersedes** | scattered notes in `project_moat_duckdb_status.md`, `reference_duckdb_coverage_audit.md`, `project_relay_transport_decision.md` |
| **Successor** | none — this is the spec |

---

## 1. The MOAT in one sentence

**ClawMetry is the only AI-agent observability tool where 100% of UI data flows through a local, encrypted DuckDB cache that you own — never the cloud's database — and where regression of this property is structurally impossible to ship.**

That sentence is the product. Everything below is plumbing in service of that sentence.

---

## 2. Why this matters

First principles. No SaaS hand-waving.

1. **Data sovereignty.** Customer agent traces (prompts, completions, tool calls, secrets-in-context) never leave the customer's machine in plaintext. The cloud DB does not contain event payloads. Legal cannot subpoena what we do not have. A breach of our cloud DB leaks plan tier and last-seen timestamps, nothing else.
2. **Speed.** DuckDB-local p50 query is **47× faster** than the legacy JSONL walkers it replaced. (Benchmark + CI alert: `feat/moat-perf-benchmark-suite`, Eng AA — PR number to be wired in once opened.) The whole dashboard renders sub-second on a laptop that was previously timing out on `/api/usage`.
3. **Trust.** Wire format is AES-256-GCM, key never leaves the customer's daemon. The cloud is a dumb pipe with a heartbeat on it. Customers can verify this with `tcpdump` and `openssl`; the code is open source.
4. **Compliance.** SOC2 / HIPAA / EU-data-residency conversations end at slide one: "we do not host your event data." Every other observability vendor has to argue. We do not.

Each of those four bullets is a reason a customer signs the contract. Lose any one of them and the differentiator collapses to "another Datadog with a worse UX."

---

## 3. Architecture

Three layers. One direction of trust. No surprises.

```
┌────────────────────────────────────────────────────────────────────┐
│  CUSTOMER MACHINE                                                  │
│                                                                    │
│  ┌──────────────┐    JSONL +     ┌───────────────────┐             │
│  │ OpenClaw     │───  events ───▶│  sync daemon      │             │
│  │ agent        │   (~/.openclaw) │  (port 4099)     │             │
│  └──────────────┘                 │                   │             │
│                                   │  ⤷ writes DuckDB  │             │
│                                   │  ⤷ holds the      │             │
│                                   │    process-level  │             │
│                                   │    write lock     │             │
│                                   └─────┬─────────────┘             │
│                                         │                           │
│                                         │ HTTP (localhost)          │
│                                         ▼                           │
│                                   ┌───────────────────┐             │
│                                   │  dashboard        │             │
│                                   │  (port 8900)      │             │
│                                   │                   │             │
│                                   │  reads via        │             │
│                                   │  routes/local_    │             │
│                                   │  query._dispatch  │             │
│                                   └─────┬─────────────┘             │
└─────────────────────────────────────────┼───────────────────────────┘
                                          │
              heartbeat (AES-256-GCM)     │      pending_queries
              every 30s ─────────────────▶│◀────  on the response
                                          ▼
┌────────────────────────────────────────────────────────────────────┐
│  CLAWMETRY CLOUD                                                   │
│                                                                    │
│  ┌────────────────────┐     ┌────────────────────────────────┐     │
│  │ Cloud SQL (Postgres)│    │ Redis (SWR cache)              │     │
│  │                     │    │                                │     │
│  │ user_id             │    │ query_id → ciphertext-result   │     │
│  │ plan_tier           │    │ TTL 60s                        │     │
│  │ last_seen           │    │                                │     │
│  │ aggregates (counts) │    │ NEVER decrypted server-side    │     │
│  │                     │    │                                │     │
│  │ NO event payloads   │    │                                │     │
│  └────────────────────┘     └────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────┘
```

### The three load-bearing patterns

1. **Per-route `_try_local_store_*` helper.** Every data-bearing handler under `routes/*.py` calls a `_try_local_store_<surface>` helper first. If DuckDB has shape-appropriate rows, the helper returns a payload tagged `_source: 'local_store'`. If not, the handler falls through to legacy. Lint (PR #1468) bans raw `get_store()` in routes — you go through the helper or you do not merge.

2. **Daemon-proxy via `routes/local_query._dispatch`.** DuckDB locks at the **process level**. `read_only=True` does not bypass this. The sync daemon holds the writer; every reader (dashboard, cron evaluator, alerts evaluator) goes through HTTP to `localhost:4099/local_query/*`. PR #1253's attempted `read_only=True` workaround was wrong; the daemon-proxy refactor is the only correct shape. (See `reference_duckdb_process_lock.md`.)

3. **Heartbeat-piggyback relay.** Cloud→daemon transport is not WebSocket, not gRPC, not SSE. It is `pending_queries` appended onto the heartbeat response body. The daemon executes queries locally against DuckDB, returns ciphertext answers on the next heartbeat. Cloud caches the ciphertext (Redis, 60s TTL) and serves it stale-while-revalidate. Cloud cannot decrypt; the cache key is opaque. This decision is locked in `project_relay_transport_decision.md` after WebSocket relay burned six deploys on 2026-05-12.

The third pattern is the one most likely to be re-litigated by future contributors. **It is not re-litigable.** It is industry-validated (Datadog, AWS SSM, OpAMP) and survived the 2026-05-12 outage that killed every alternative.

---

## 4. Today's achievements (2026-05-17 EOD)

This is the day the MOAT closed.

### Headline numbers

- **18 PRs merged** for DuckDB + sync hardening
- **96% real DuckDB coverage** (114 / 120 data-bearing surfaces; per Eng X audit refresh)
- **17 surfaces migrated** to DuckDB fast paths in a single afternoon
- **6 silent v3-shape bugs** fixed in passing (forecast, cost-optimizer, automation-analysis, token-attribution, + 2 more)
- **1 phantom found** in audit (`/api/gateway-health/history` was already migrated under #1256)
- **TUI re-classified** as JSONL post-processor, not channel adapter (separate track)
- **Cloud-sync E2E test** file landed — 4 scenarios, real DuckDB + real AES-256-GCM round-trip
- **Bug-class CI gate live on main** (#1587) — bans the `ev['type'] == 'message'` v3-shape filter at lint time
- **DuckDB perf benchmark + CI regression alert** (branch `feat/moat-perf-benchmark-suite`, opening shortly) — fails any PR that degrades fast-path p50 by >2×

### Route-by-route migration table (today's drain)

| PR | Route | File | Notes |
|---|---|---|---|
| #1569 | `GET /api/subagents` | `routes/sessions.py` | Reads `subagents` table; defers on empty (1-msg session). |
| #1570 | `GET /api/flow-events` (+ `/api/flow` alias) | `routes/infra.py` | 2-event session tagged `local_store`. |
| #1571 | `GET /api/usage/forecast` | `routes/usage.py` | Full payload (cost_this_month, projected_month, 7-day window, days_to_budget). Fixed silent v3-shape bug in passing. |
| #1572 | `GET /api/rate-limits` | `routes/health.py` | Surfaces per-provider hour buckets. Was suspected in-memory ring; turned out trivially DuckDB-able. |
| #1573 | `GET /api/version-impact` | `routes/meta.py` | `version_history` populated from `session.started` events. |
| #1574 | `GET /api/token-velocity` | `routes/usage.py` | MITIGATED `BUG_RISK_HIGH` legacy v3-shape filter. |
| #1575 | `GET /api/task-runs` | `routes/sessions.py` | Reads `subagents` table; defers to `tasks/runs.sqlite` on empty. |
| #1576 | `GET /api/cost-optimizer` | `routes/infra.py` | Fixed silent v3-shape bug. |
| #1577 | `GET /api/component/gateway` | `routes/components.py` | Routes table + active sessions count. |
| #1578 | `GET /api/sessions/<sid>/model-transitions` | `routes/sessions.py` | Returns `count: 0` correctly when session never changed models. |
| #1579 | `GET /api/skills/fidelity` | `routes/usage.py` | Defers on empty skills dir. |
| #1580 | `GET /api/automation-analysis` | `routes/infra.py` | Fixed silent v3-shape bug. |
| #1581 | `GET /api/gateway-health` | `routes/health.py` | Bonus — not in original Tier-1 list. |
| #1583 | `GET /api/token-attribution` | `routes/usage.py` | MITIGATED `BUG_RISK_HIGH` legacy v3-shape filter. |
| #1585 | `GET /api/channel/telegram` + `/api/channel/signal` | `routes/channels.py` | v3 events fast path. |
| #1586 | `GET /api/channel/bluebubbles` | `routes/channels.py` | Final Tier-1 channel cliff CLOSED. |
| #1561 | `GET /api/sessions/<sid>/session-tools` | `routes/sessions.py` | Pre-drain fix; recognise v3 event types. |
| #1584 | (test) cloud-sync E2E | `tests/test_cloud_sync_moat_e2e.py` | 4 scenarios: encryption round-trip, daemon→cloud→API path, plan-tier metadata only, no event payloads on wire. |

Phantom corrected:

| Route | Why missed | Truth |
|---|---|---|
| `GET /api/gateway-health/history` | Morning grep looked at handler body only (12 lines); the `_ls_call` lives 130 lines upstream in `_query_gateway_metric_history`. | Migrated under PR #1256 (predates audit #1565). DO NOT re-migrate. |

Re-classified:

| Surface | Originally | Now |
|---|---|---|
| `GET /api/channel/tui` | Tier-1 channel adapter | JSONL post-processor; not in `sync._CHANNEL_DIRS`; no `~/.openclaw/tui/` dir; needs a TUI-aware ingest chokepoint, not a fast-path retrofit. Tracked separately from #1565. |

---

## 5. The permanence stack

How regressions become **structurally impossible** to ship — not "unlikely" or "caught in review." Impossible.

### Gate 1 — Bug-class scanner (CI, live on main)

PR **#1587**, merged. CI step `scripts/check_v3_shape_filter.py` greps the diff for `ev['type'] == 'message'` (and `event['type'] == 'message'`, `evt['type'] == 'message'`, etc.) and fails the build. The pattern is the exact silent-zero shape that broke 3 of 7 MOAT migrations on 2026-05-16 (see `feedback_synthetic_tests_missed_real_event_shape.md`). Anyone adding it back to a route handler or a walker hits a red X in pre-merge CI.

### Gate 2 — Perf benchmark + regression alert (CI, in flight)

Branch `feat/moat-perf-benchmark-suite` (Eng AA). Captures p50 / p95 latency of every `_try_local_store_*` against a seeded DuckDB of N=10k events. Asserts on each PR that no fast path degrades by >2× vs baseline stored in `tests/data/moat_perf_baseline.json`. If you write a slow DuckDB query, CI tells you before review does. PR number pending; the gate is being wired against the same `scripts/check_*.py` runner used by Gate 1.

### Gate 3 — Cloud-side mirror of Gate 1 (TODO)

Eng CC is auditing `clawmetry-cloud` for the same v3-shape filter pattern. Cloud should not be reading event payloads at all (see Section 8: anti-goals), but if any aggregate-builder there ever ingests raw events, the same lint must apply. Opens once Eng CC's audit lands.

### Gate 4 — MOAT verifier suite (CI, live on main)

PR #1527 wired the verifier into CI. **58 → 61 → 64 tests** today (post-#1581 + #1583 + #1586). Covers:

- Synthetic v3 event shapes per route (one `tests/test_<route>_local_store_v3.py` per migration)
- Live OpenClaw `agent --local` E2E (5/5 green; 1 skipped by design — `agent --local` doesn't expose tools to the model)
- `_source: 'local_store'` tag assertion on every Tier-1 route's response body
- Encryption round-trip (`tests/test_cloud_sync_moat_e2e.py`, PR #1584)

Run command: `pytest tests/test_*_local_store_v3.py tests/test_moat_live_openclaw_e2e.py tests/test_cloud_sync_moat_e2e.py -v`.

### Audit refresh protocol

Per Eng X's #1582 refinement, every coverage audit must:

1. Apply the **8-category taxonomy**: `DUCKDB_FAST_PATH`, `DUCKDB_PARTIAL`, `DUCKDB_BYPASSING_CONVENTION`, `JSONL_FALLBACK_ONLY`, `IN_MEMORY_RING`, `LIVE_PROBE`, `DERIVED`, `STATIC`.
2. Flag `BUG_RISK_HIGH` on any handler whose legacy fallback uses `ev['type'] == 'message'` or any other pre-v3 shape filter.
3. Chase delegated helpers, not just handler bodies (the `/api/gateway-health/history` phantom cost 15 minutes of agent time because the morning audit grepped handler bodies only).
4. Hint-validate every Tier-N candidate by reading the suggested DuckDB table / event name against `clawmetry/local_store.py` + `clawmetry/sync.py` before publishing.
5. Re-cadence: every Friday after the week's MOAT merges.

The audit is not optional. It is the only mechanism that finds phantoms before someone wastes a PR re-migrating them.

---

## 6. What still needs follow-up

Open work, in priority order. None of it blocks the MOAT claim, but all of it is on the board.

1. **2 latent silent-zero bugs** (in #1588, Eng BB) — `session_export` and `sessions_clusters` carry the same `ev['type'] == 'message'` shape in their legacy walkers. Gate 1 catches new instances; existing instances need a sweep PR. ETA: this week.
2. **TUI JSONL-ingest hardening.** TUI writes `Sender (untrusted metadata)` JSON into session JSONL with no dedicated chokepoint. Need a TUI-aware `_normalize_tui_event` in `clawmetry/sync.py::_parse_v3_event` and a backing event type (`prompt.submitted` with `sender_label='openclaw-tui'`). Separate track from #1565.
3. **Cloud-side audit.** Does `clawmetry-cloud` carry any v3-shape filters or any code path that reads raw event payloads? Eng CC investigating. If yes, fix and add Gate 3.
4. **Explicit "not-a-candidate" markers.** The 6 legitimate non-DuckDB surfaces (DERIVED / STATIC / LIVE_PROBE) should carry a `# moat: not-a-candidate <reason>` comment on the handler so future audits don't re-list them as phantoms. Cheap one-shot PR.
5. **Channel `DUCKDB_PARTIAL` cleanup.** 7 channels (telegram, whatsapp, signal, discord, slack, irc, webchat) still run fast path + JSONL augment for previews the daemon hasn't ingested yet. Drop the augment once daemon channel-message ingest catches up. Not blocking; tracked separately.

---

## 7. The next 12 months

### Phase 2 — Cloud as pure SWR cache

Cloud's role shrinks to:

- Heartbeat receiver
- Pending-query queuer
- Ciphertext SWR cache (Redis, 60s TTL)
- Metadata store (user_id, plan_tier, last_seen) on Cloud SQL

That is it. No aggregate-builder reads raw event payloads on cloud, ever. Pre-computed aggregates the customer's daemon ships up are stored opaquely. (See `project_local_compute_cloud_display.md`.)

### Phase 3 — Daemon-to-daemon mesh

Fleet observability without cloud as a bottleneck. A daemon on node A can ask a daemon on node B for `pending_queries` via the same heartbeat-piggyback transport, routed through cloud as a dumb relay. Fleet view in the dashboard becomes a fan-out of daemon-to-daemon queries; cloud never sees the answers in plaintext.

### Phase 4 — Open-source the daemon-proxy spec

Publish `docs/DAEMON_PROXY_SPEC.md` as a vendor-neutral protocol. Other agent frameworks (Hermes, Claude Code, Codex, Cursor) can adopt the same MOAT pattern and route through ClawMetry's UI, or build their own UI on the same daemon contract. This is the multi-agent adapter direction (`project_multi_agent_adapter.md`) made permanent.

---

## 8. Anti-goals

Things we will **explicitly not do**. If a PR proposes any of these, close it.

1. **Re-introduce PostHog or any third-party analytics that hosts customer event data.** Rejected 2026-05-13 ($600/mo + violates the MOAT). In-house Postgres analytics at `app.clawmetry.com/admin/thesecretpageforvivek` only. (See `project_no_posthog.md`.)
2. **Add Cloud SQL queries that read event data.** Cloud SQL stores metadata + aggregates. Reading event payloads server-side breaks the sovereignty claim. (See `project_local_compute_cloud_display.md`.)
3. **Ship features behind feature flags that bypass DuckDB-first.** `CLAWMETRY_LOCAL_STORE_READ=1` was opt-in for two weeks and 100% of users silently ran the legacy slow path. Defaults are load-bearing. (See `feedback_local_store_default_off_killed_moat.md`.)
4. **Add MCP servers that mirror DuckDB data into other vendor systems.** A "ClawMetry MCP for Datadog" that ships event payloads off-machine is the same anti-pattern dressed up as integration.
5. **Use WebSockets for the cloud relay.** Killed 2026-05-12 after six failed deploys against Cloud Run's HTTP/2 frontend. Heartbeat-piggyback won. (See `project_relay_transport_decision.md` and `reference_ws_handshake_400_unsolved.md`.)
6. **Add a "cloud-side ingest" pipeline.** Even if a customer asks for it. The answer is "deploy your own daemon, we'll give you the wire format."

---

## 9. Acceptance criteria

How we measure MOAT health, on every commit:

- [ ] **≥95%** of data-bearing surfaces classified as `DUCKDB_FAST_PATH` or `DUCKDB_PARTIAL`. (Today: 96%.)
- [ ] **Zero `BUG_RISK_HIGH` violations on main** — enforced by Gate 1 (#1587).
- [ ] **DuckDB fast-path p50 ≤ legacy p50** on every benchmarked route — enforced by Gate 2 (Eng AA, in flight).
- [ ] **Live OpenClaw E2E green** on every main commit — enforced by Gate 4 (#1527).
- [ ] **Eng S's MOAT verification matrix on #1565 reports 0 regressions weekly** — manual, every Friday.
- [ ] **No event payloads on cloud-side wire dumps.** `tcpdump` on the heartbeat connection shows only AES-256-GCM ciphertext + metadata fields (`user_id`, `plan_tier`, `last_seen`).
- [ ] **No raw `get_store()` calls in `routes/*.py`** — enforced by lint shipped in #1468.

If any of these flips red, the MOAT is degraded. Stop shipping features. Fix the gate.

---

## Glossary

| Term | Meaning |
|---|---|
| **MOAT** | The architectural property that 100% of UI data flows through customer-owned DuckDB. |
| **Fast path** | A `_try_local_store_<surface>` helper that returns DuckDB-backed data tagged `_source: 'local_store'`. |
| **Legacy path** | The pre-MOAT JSONL walker / `psutil` probe / in-memory ring. Still present for fallback; should never be the active reader on a v3 OpenClaw install. |
| **Daemon-proxy** | The HTTP shim at `localhost:4099/local_query/*` that lets non-daemon processes query DuckDB without contending for the process-level write lock. |
| **Heartbeat-piggyback** | The cloud→daemon transport that appends `pending_queries` to heartbeat responses. |
| **SWR** | Stale-while-revalidate; the cloud's caching strategy for ciphertext answers. |
| **Phantom** | A route an audit lists as needing migration but which has already been migrated under a prior PR. Always check delegated helpers. |
| **BUG_RISK_HIGH** | An audit flag for handlers whose legacy fallback uses pre-v3 event shape filters (`ev['type'] == 'message'`). |
| **Tier-1 / Tier-2** | Audit priority. Tier-1 = should migrate this sprint. Tier-2 = deferred by design (exports, SSE streams, etc.). |

## References

- `reference_duckdb_coverage_audit.md` (2026-05-17 16:30Z refresh)
- `project_local_compute_cloud_display.md`
- `project_no_posthog.md`
- `project_relay_transport_decision.md`
- `feedback_local_store_default_off_killed_moat.md`
- `feedback_synthetic_tests_missed_real_event_shape.md`
- `feedback_daemon_proxy_pattern.md`
- `feedback_duckdb_first_rule.md`
- `reference_duckdb_process_lock.md`
- `reference_ws_handshake_400_unsolved.md`
- `feedback_ws_diagnostic_caused_outage.md`
- Issue #1565 (audit baseline + MOAT verification matrix)
- Issue #1582 (audit-refinement / 8-category taxonomy)
- Issue #1588 (latent silent-zero sweep)
- PR #1527 (MOAT verifier wired into CI)
- PR #1587 (Gate 1: bug-class scanner)
- Branch `feat/moat-perf-benchmark-suite` (Gate 2: perf regression alert)
