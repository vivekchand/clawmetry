# MOAT Coverage Matrix

Live tracker for the DuckDB-first MOAT mandate (issue [#1565](https://github.com/vivekchand/clawmetry/issues/1565)). One row per `@bp.route` handler in `routes/*.py`.

## Method

Programmatic classifier walks every `@<bp>.route(...)` in `routes/*.py` and reads the handler body (with docstrings + comments stripped) against these markers:

- **`FAST`** — body calls `_try_local_store_*` / `local_store_via_daemon` / `_ls_call` / `is_local_store_read_enabled` and shows no JSONL / log / psutil / in-memory ring read.
- **`HYBRID`** — both DuckDB fast path AND a fallback to JSONL/log walker (graceful migration during daemon catch-up).
- **`BYPASS_FS`** — reads `.jsonl` files or `_grep_log_file` directly.
- **`BYPASS_PROC`** — reads `psutil` for historical samples (live snapshot is exempt per `feedback_duckdb_first_rule.md`).
- **`BYPASS_RING`** — reads `dashboard.metrics_store` (in-memory OTLP ring; resets on every restart).
- **`SSE`** — `text/event-stream` long-poll endpoints; live tail is the spec (see Tier-2 deferral list in `reference_duckdb_coverage_audit.md`).
- **`RPC`** — proxies to OpenClaw gateway WebSocket (cron mutations etc.); not a read endpoint.
- **`OTHER`** — config / auth / OAuth / HTML / OTLP receiver / mutation / no-data. Treat as STATIC.

## Headline (2026-05-18, against `origin/main @ bb42897`)

| Category | Count | % |
|---|---|---|
| `FAST` | 68 | 27.4% |
| `HYBRID` | 37 | 14.9% |
| `BYPASS_FS` | 6 | 2.4% |
| `BYPASS_PROC` | 0 | 0.0% |
| `BYPASS_RING` | 2 | 0.8% |
| `SSE` | 2 | 0.8% |
| `RPC` | 10 | 4.0% |
| `OTHER` (STATIC) | 123 | 49.6% |
| **TOTAL** | **248** | 100% |

**DuckDB-genuine coverage** (`FAST` + `HYBRID`) = 105 / 248 = **42% of all routes**, or 105 / 113 data-bearing = **93%** after dropping STATIC + SSE + RPC + LIVE_PROBE.

## Migrations shipped this session (worktree `agent-a266fe4b`)

| Route | File:Line | Before | After | PR |
|---|---|---|---|---|
| `/api/cost-optimization` | `infra.py:1300` | `BYPASS_RING` | `HYBRID` | [#1673](https://github.com/vivekchand/clawmetry/pull/1673) |
| `/api/usage/export` | `usage.py:2499` | `BYPASS_FS` | `HYBRID` | [#1675](https://github.com/vivekchand/clawmetry/pull/1675) |

Both follow the `feedback_daemon_proxy_pattern.md` playbook: DuckDB-first via `query_aggregates`, with the legacy in-memory-ring / JSONL walker preserved as the empty-store fallback (no canary on empty store).

## Remaining Tier-1 (real candidates after this session)

| # | Endpoint | File:Line | Reason left | Migration hint | Confidence |
|---|---|---|---|---|---|
| 1 | `GET /api/otel-status` | `meta.py:737` | `BYPASS_RING` by design — `counts` is the receiver-side canary for the live OTLP ring. | Augment with DuckDB row counts only; keep ring counts for "is OTLP receiving right now". | **LOW** — semantic change, defer until OTLP-receiver health redesign. |
| 2 | `GET /api/usage/cache-trends` | `usage.py:3092` | Tier-2 per audit: schema gap (per-model cache split not in DuckDB rollup). | Extend `query_daily_usage_splits` to return per-model rows OR add `query_cache_trends`. | **MEDIUM** — schema work first. |

## Tier-2 (genuinely deferred)

- `GET /api/brain-stream` — SSE live tail; DuckDB equivalent needs LISTEN/NOTIFY.
- `GET /api/health-stream` — same.
- `GET /api/logs-stream` — same.
- `GET /api/health` — LIVE_PROBE (socket + statvfs) by design.
- `GET /api/channel/imessage` — reads Apple's local SQLite `chat.db` directly (out-of-process source). Migration = daemon ingest into `channel_messages`.
- `GET /api/channels` — STATIC (scans `openclaw.json` + `gateway.yaml`).
- `GET /api/auth/detected-token` — STATIC bootstrap (hands token from config to JS).
- `GET /api/export/otlp` — export-shaped, defer.
- `GET /api/component/{runtime,machine,storage,network}` — OS probes; historical samples need `*.metric` event ingest.
- `routes/fleet_history.py` (12 endpoints) — SQLite time-series, out-of-scope for DuckDB migration (separate `history.py` backend).
- `routes/local_query.py` (7 endpoints) — IS the DuckDB API, not a consumer.

## HYBRID channel cleanup (Tier-1 follow-up)

7 channels still run fast-path + JSONL session-file enrichment: `telegram`, `whatsapp`, `signal`, `discord`, `slack`, `irc`, `webchat`. Migration = drop the JSONL augment once daemon channel-message ingest catches up. Tracked separately.

## Per-file scoreboard

| File | Total | FAST | HYBRID | BYPASS_FS | BYPASS_RING | SSE | RPC | OTHER |
|---|---|---|---|---|---|---|---|---|
| `advisor.py` | 2 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| `agents.py` | 3 | 1 | 0 | 0 | 0 | 0 | 0 | 2 |
| `alerts.py` | 24 | 1 | 0 | 0 | 0 | 0 | 0 | 23 |
| `autonomy.py` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `bootstrap.py` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `brain.py` | 3 | 1 | 1 | 1 | 0 | 0 | 0 | 0 |
| `channels.py` | 27 | 17 | 9 | 1 | 0 | 0 | 0 | 0 |
| `components.py` | 7 | 0 | 3 | 0 | 0 | 0 | 0 | 4 |
| `crons.py` | 15 | 5 | 1 | 0 | 0 | 0 | 6 | 3 |
| `evals.py` | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `fleet_history.py` | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 12 |
| `health.py` | 17 | 11 | 2 | 0 | 1 | 1 | 0 | 2 |
| `heartbeat.py` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `infra.py` | 16 | 9 | 3 | 0 | 0 | 1 | 0 | 3 |
| `insights.py` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| `local_query.py` | 7 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| `meta.py` | 16 | 3 | 0 | 1 | 1 | 0 | 3 | 8 |
| `nemoclaw.py` | 7 | 1 | 0 | 0 | 0 | 0 | 0 | 6 |
| `overview.py` | 7 | 3 | 1 | 1 | 0 | 0 | 0 | 2 |
| `plugins.py` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `reasoning.py` | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| `review.py` | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| `selfconfig.py` | 5 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| `selfevolve.py` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| `sessions.py` | 21 | 7 | 10 | 0 | 0 | 0 | 0 | 4 |
| `skills.py` | 3 | 2 | 0 | 0 | 0 | 0 | 0 | 1 |
| `update_check.py` | 6 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| `usage.py` | 17 | 9 | 6 | 2 | 0 | 0 | 0 | 0 |
| `workspaces.py` | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| `heartbeat.py`/etc | … | … | … | … | … | … | … | … |
| **TOTAL** | **248** | **68** | **37** | **6** | **2** | **2** | **10** | **123** |

## Full route table

| File:Line | Route | Classification |
|---|---|---|
| advisor.py:402 | `/api/advisor/ask` | OTHER |
| advisor.py:493 | `/api/advisor/status` | FAST |
| agents.py:95 | `/api/agents` | OTHER |
| agents.py:101 | `/api/agents/<name>` | OTHER |
| agents.py:113 | `/api/agents/<name>/sessions` | FAST |
| alerts.py:181 | `/api/budget/config` | OTHER |
| alerts.py:233 | `/api/budget/status` | OTHER |
| alerts.py:240 | `/api/budget/auto-pause` | OTHER |
| alerts.py:261 | `/api/budget/pause` | OTHER |
| alerts.py:272 | `/api/budget/resume` | OTHER |
| alerts.py:287 | `/api/budget/pause-gateway` | OTHER |
| alerts.py:303 | `/api/budget/resume-gateway` | OTHER |
| alerts.py:313 | `/api/budget/is-over-cap` | OTHER |
| alerts.py:328 | `/api/budget` | OTHER |
| alerts.py:363 | `/api/agents/<agent_id>/budget` | OTHER |
| alerts.py:375 | `/api/agents/<agent_id>/budget` | OTHER |
| alerts.py:414 | `/api/agents/<agent_id>/budget` | OTHER |
| alerts.py:424 | `/api/budget/test-telegram` | OTHER |
| alerts.py:458 | `/api/alerts/rules` | FAST |
| alerts.py:527 | `/api/alerts/rules/<rule_id>` | OTHER |
| alerts.py:564 | `/api/alerts/history` | OTHER |
| alerts.py:572 | `/api/alerts/history/<int:alert_id>/ack` | OTHER |
| alerts.py:587 | `/api/alerts/active` | OTHER |
| alerts.py:594 | `/api/alerts/webhook` | OTHER |
| alerts.py:614 | `/api/alerts/webhook/test` | OTHER |
| alerts.py:652 | `/api/alerts/velocity` | OTHER |
| alerts.py:667 | `/api/alert-channels` | OTHER |
| alerts.py:693 | `/api/alert-channels/test` | OTHER |
| alerts.py:744 | `/api/_harness/inject-cost` | OTHER |
| autonomy.py:439 | `/api/autonomy` | FAST |
| bootstrap.py:69 | `/api/bootstrap` | OTHER |
| bootstrap.py:101 | `/api/bootstrap/<agent_id>` | OTHER |
| brain.py:402 | `/api/brain-history` | HYBRID |
| brain.py:1369 | `/api/llm-call-timeline/<event_id>` | FAST |
| brain.py:1427 | `/api/brain-stream` | BYPASS_FS (SSE) |
| channels.py:119 | `/api/channels/<provider>/status` | FAST |
| channels.py:152 | `/api/channels/status` | FAST |
| channels.py:728 | `/api/channels/<provider>/messages` | FAST |
| channels.py:764 | `/api/channels/<provider>/threads` | FAST |
| channels.py:790 | `/api/channels/summary` | FAST |
| channels.py:805 | `/api/channel/telegram` | HYBRID |
| channels.py:1052 | `/api/channel/imessage` | BYPASS_FS |
| channels.py:1186 | `/api/channel/whatsapp` | HYBRID |
| channels.py:1332 | `/api/channel/signal` | HYBRID |
| channels.py:1474 | `/api/channel/discord` | HYBRID |
| channels.py:1650 | `/api/channel/slack` | HYBRID |
| channels.py:1831 | `/api/channel/irc` | HYBRID |
| channels.py:2008 | `/api/channel/webchat` | HYBRID |
| channels.py:2187 | `/api/channel/googlechat` | FAST |
| channels.py:2207 | `/api/channel/bluebubbles` | HYBRID |
| channels.py:2415 | `/api/channel/msteams` | FAST |
| channels.py:2434 | `/api/channel/tui` | HYBRID |
| channels.py:2571 | `/api/channel/matrix` | FAST |
| channels.py:2584 | `/api/channel/mattermost` | FAST |
| channels.py:2603 | `/api/channel/line` | FAST |
| channels.py:2616 | `/api/channel/nostr` | FAST |
| channels.py:2629 | `/api/channel/twitch` | FAST |
| channels.py:2642 | `/api/channel/feishu` | FAST |
| channels.py:2655 | `/api/channel/zalo` | FAST |
| channels.py:2668 | `/api/channel/tlon` | FAST |
| channels.py:2681 | `/api/channel/synology-chat` | FAST |
| channels.py:2694 | `/api/channel/nextcloud-talk` | FAST |
| components.py:218 | `/api/component/tool/<name>` | HYBRID |
| components.py:550 | `/api/component/runtime` | OTHER |
| components.py:636 | `/api/component/machine` | OTHER |
| components.py:721 | `/api/component/storage` | OTHER |
| components.py:782 | `/api/component/network` | OTHER |
| components.py:1075 | `/api/component/gateway` | HYBRID |
| components.py:1524 | `/api/component/brain` | HYBRID |
| crons.py:377 | `/api/crons` | FAST |
| crons.py:449 | `/api/cron/fix` | OTHER |
| crons.py:466 | `/api/cron/run` | RPC |
| crons.py:483 | `/api/cron/toggle` | RPC |
| crons.py:501 | `/api/cron/delete` | RPC |
| crons.py:514 | `/api/cron/update` | RPC |
| crons.py:530 | `/api/cron/create` | RPC |
| crons.py:563 | `/api/cron/<job_id>/runs` | FAST |
| crons.py:775 | `/api/crons/<job_id>/runs` | FAST (mis-classified by grep — uses `_cron_runs_from_duckdb`) |
| crons.py:845 | `/api/cron/<job_id>/kill` | RPC |
| crons.py:902 | `/api/cron-run-log` | HYBRID |
| crons.py:949 | `/api/cron/health-summary` | FAST |
| crons.py:1099 | `/api/cron/kill-all` | RPC |
| crons.py:1257 | `/api/agent-intentions` | FAST |
| crons.py:1320 | `/api/cron-health` | OTHER |
| health.py:818 | `/api/reliability` | FAST |
| health.py:939 | `/api/heatmap` | HYBRID |
| health.py:1068 | `/api/system-health` | FAST |
| health.py:1421 | `/api/gateway-health` | FAST |
| health.py:1583 | `/api/gateway-health/history` | FAST |
| health.py:1609 | `/api/health` | LIVE_PROBE (by design) |
| health.py:1843 | `/api/config-diagnostics` | OTHER |
| health.py:2012 | `/api/service-status` | FAST |
| health.py:2213 | `/api/heartbeat-status` | FAST |
| health.py:2235 | `/api/agent-presence` | OTHER |
| health.py:2417 | `/api/rate-limits` | HYBRID |
| health.py:2495 | `/api/health-stream` | SSE |
| health.py:2597 | `/api/sandbox-status` | FAST |
| health.py:2841 | `/api/loop-detection` | FAST |
| health.py:2921 | `/api/loop-signals` | FAST |
| health.py:3201 | `/api/mcp-stats` | FAST |
| infra.py:46 | `/api/logs` | OTHER |
| infra.py:333-334 | `/api/flow-events` + `/api/flow` | HYBRID |
| infra.py:575 | `/api/flow/runs` | OTHER |
| infra.py:651 | `/api/logs-stream` | SSE |
| infra.py:922-923 | `/api/memory-files` + `/api/memory` | FAST |
| infra.py:933 | `/api/file` | FAST |
| infra.py:987 | `/api/memory-analytics` | FAST |
| infra.py:1058 | `/api/security/posture` | OTHER |
| infra.py:1072 | `/api/llmfit` | OTHER |
| infra.py:1092 | `/api/cost-optimizer` | FAST |
| infra.py:1300 | `/api/cost-optimization` | **HYBRID after PR #1673** |
| infra.py:1483 | `/api/automation-analysis` | FAST |
| infra.py:1558 | `/api/context-anatomy` | HYBRID |
| meta.py:60 | `/api/version` | OTHER |
| meta.py:461 | `/api/auth/detected-token` | BYPASS_FS (STATIC bootstrap by design) |
| meta.py:687 | `/v1/metrics` | OTHER (OTLP receiver) |
| meta.py:712 | `/v1/traces` | OTHER (OTLP receiver) |
| meta.py:737 | `/api/otel-status` | BYPASS_RING (by design — receiver state) |
| meta.py:953 | `/api/version-impact` | FAST |
| meta.py:1053 | `/api/clusters` | FAST |
| nemoclaw.py:344 | `/api/nemoclaw/pending-approvals` | FAST |
| overview.py:535 | `/api/channels` | BYPASS_FS (STATIC config discovery) |
| overview.py:999 | `/api/overview` | FAST |
| overview.py:1249 | `/api/timeline` | FAST |
| overview.py:1366 | `/api/prompt-errors` | HYBRID |
| plugins.py:319 | `/api/plugins` | FAST |
| reasoning.py:340 | `/api/reasoning` | FAST |
| sessions.py:242 | `/api/sessions` | FAST |
| sessions.py:407 | `/api/sessions/by-type` | FAST |
| sessions.py:590 | `/api/compactions` | HYBRID |
| sessions.py:1012 | `/api/session-tools` | HYBRID |
| sessions.py:1241 | `/api/cost-split` | HYBRID |
| sessions.py:1552 | `/api/task-runs` | FAST |
| sessions.py:1958 | `/api/subagents` | FAST |
| sessions.py:2300 | `/api/export/otlp` | OTHER |
| sessions.py:2446 | `/api/sessions/cost-breakdown` | FAST |
| sessions.py:2575 | `/api/transcripts` | HYBRID |
| sessions.py:3053 | `/api/transcript/<session_id>` | HYBRID |
| sessions.py:3285 | `/api/transcript-events/<session_id>` | HYBRID |
| sessions.py:3626 | `/api/session-model-journey/<session_id>` | HYBRID |
| sessions.py:3909 | `/api/sessions/<session_id>/cost-breakdown` | HYBRID |
| sessions.py:4277 | `/api/sessions/<session_id>/export` | HYBRID |
| sessions.py:4667 | `/api/sessions/<sid>/model-transitions` | HYBRID |
| sessions.py:4716 | `/api/fallbacks` | HYBRID |
| sessions.py:4813 | `/api/spans` | FAST |
| sessions.py:4932 | `/api/outcomes` | FAST |
| sessions.py:4976 | `/api/outcomes/timeline` | FAST |
| sessions.py:5020 | `/api/outcomes/sessions` | FAST |
| skills.py:329 | `/api/skills` | FAST |
| skills.py:483 | `/api/skills/<skill_name>` | FAST |
| usage.py:1583 | `/api/usage` | FAST |
| usage.py:1727 | `/api/usage/anomalies` | FAST |
| usage.py:1759 | `/api/anomalies` | FAST |
| usage.py:1821 | `/api/usage/by-plugin` | FAST |
| usage.py:1887 | `/api/usage/by-plugin/trend` | FAST |
| usage.py:2167 | `/api/sessions/clusters` | HYBRID |
| usage.py:2448 | `/api/usage/cost-comparison` | FAST |
| usage.py:2465 | `/api/usage/forecast` | FAST |
| usage.py:2499 | `/api/usage/export` | **HYBRID after PR #1675** |
| usage.py:2621 | `/api/model-attribution` | HYBRID |
| usage.py:2715 | `/api/skill-attribution` | HYBRID |
| usage.py:2860 | `/api/token-velocity` | HYBRID |
| usage.py:3092 | `/api/usage/cache-trends` | BYPASS_FS (schema gap — Tier-2) |
| usage.py:3261 | `/api/skills/fidelity` | HYBRID |
| usage.py:3435 | `/api/token-attribution` | HYBRID |

(remaining `OTHER` routes — fleet_history, evals, insights, review, selfconfig, selfevolve, update_check, workspaces, alerts mutations, gateway RPC proxies — are config / mutation / SQLite-backend / external-RPC and outside the DuckDB read-path mandate.)

## Audit cadence

Re-run the classifier weekly after each MOAT batch merges; bump the headline numbers + per-file scoreboard. Verify any new `BYPASS_*` lands with an accompanying `_try_local_store_*` follow-up issue.
