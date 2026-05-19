# DuckDB UI Coverage Audit — 2026-05-13

Snapshot of every dashboard HTTP surface in `routes/*.py`, the data source it
reads from today, and how hard it would be to flip onto the DuckDB local-store
fast path (`_try_local_store_*` + `CLAWMETRY_LOCAL_STORE_READ=1`).

## Summary

| Metric | 2026-05-12 baseline | 2026-05-13 (this audit) |
|---|---|---|
| Total routes inventoried | 57 | **197** (full sweep across 24 blueprints) |
| Read-data surfaces (relevant denominator) | 57 | **104** |
| DuckDB fast-path wired | 9 (~16%) | **38 (~37%)** |
| Bypass (no DuckDB path) | 44 (~77%) | **52 (~50%)** |
| N/A — POST mutations / system probes / SSE / cloud-only | — | 14 (~13%) |

The denominator widened because earlier audits only counted "tab-level" surfaces.
This audit walks every `@bp_*.route(...)` in `routes/`. The DuckDB-fast-path
share more than doubled (16% → 37%) thanks to the `_try_local_store_*` work
landed under epics #964 and #1032.

## Legend

- **DuckDB-Full** — `_try_local_store_*` exists and is the first path tried.
- **DuckDB-Mixed** — partial: DuckDB fast-path exists but most rows still come from gateway/JSONL.
- **Bypass** — no DuckDB code; reads filesystem, gateway WebSocket, or sqlite directly.
- **N/A** — POST mutation / SSE stream / system probe / cloud-only / static page.
- **Difficulty** — Easy = `query_events`/`query_sessions` already covers it; Medium = needs new query helper; Hard = needs schema work or non-trivial transform.

## Sorted by status (Bypass first), then difficulty

### Bypass — Easy (top migration candidates)

| Endpoint | Source | Difficulty | File:Line |
|---|---|---|---|
| `/api/prompt-errors` | JSONL scan (`customType=openclaw:prompt-error`) | Easy | routes/overview.py:686 |
| `/api/transcripts` | listdir on sessions dir | Easy | routes/sessions.py:1554 |
| `/api/transcript-events/<id>` | JSONL parse for one session | Easy | routes/sessions.py:1810 |
| `/api/sessions/<id>/cost-breakdown` | JSONL parse, per-turn usage | Easy | routes/sessions.py:2165 |
| `/api/sessions/cost-breakdown` | `_compute_transcript_analytics()` | Easy | routes/sessions.py:1474 |
| `/api/sessions/<id>/export` | JSONL parse, JSON/CSV dump | Easy | routes/sessions.py:2297 |
| `/api/heatmap` | log files + JSONL files | Easy | routes/health.py:208 |
| `/api/cron-run-log` | JSONL parse for cron session | Easy | routes/crons.py:591 |
| `/api/agents/<name>/sessions` | adapter `list_sessions()` | Easy | routes/agents.py:43 |
| `/api/sessions/clusters` | JSONL scan + clustering | Easy | routes/usage.py:1028 |
| `/api/version-impact` | `_d._compute_transcript_analytics()` | Easy | routes/meta.py:420 |
| `/api/timeline` (legacy fallback) | gateway + JSONL fan-out | Easy | routes/overview.py:634 |

### Bypass — Medium

| Endpoint | Source | Difficulty | File:Line |
|---|---|---|---|
| `/api/agents` | `registry.detect_all()` | Medium | routes/agents.py:25 |
| `/api/agents/<name>` | `adapter.detect()` | Medium | routes/agents.py:31 |
| `/api/skills` | `~/.openclaw/skills` walker | Medium | routes/skills.py:218 |
| `/api/skills/<name>` | filesystem | Medium | routes/skills.py:355 |
| `/api/skills/<name>/file` | filesystem | Medium | routes/skills.py:440 |
| `/api/plugins` | filesystem walker | Medium | routes/plugins.py:230 |
| `/api/selfconfig` | filesystem | Medium | routes/selfconfig.py:428 |
| `/api/selfconfig/<file>` | filesystem | Medium | routes/selfconfig.py:477 |
| `/api/selfconfig/<file>/diff` | git history of file | Medium | routes/selfconfig.py:513 |
| `/api/task-runs` | sqlite `~/.openclaw/tasks/runs.sqlite` | Medium | routes/sessions.py:787 |
| `/api/delegation-tree` | task_runs sqlite + JSONL | Medium | routes/sessions.py:1275 |
| `/api/subagents` | gateway + sqlite + JSONL | Medium | routes/sessions.py:1050 |
| `/api/compactions` | JSONL scan | Medium | routes/sessions.py:366 |
| `/api/session-tools` | JSONL parse | Medium | routes/sessions.py:473 |
| `/api/cost-split` | analytics + filesystem | Medium | routes/sessions.py:636 |
| `/api/session-model-journey/<id>` | JSONL parse | Medium | routes/sessions.py:2009 |
| `/api/llmfit` | filesystem | Medium | routes/infra.py:714 |
| `/api/cost-optimizer` | analytics merger | Medium | routes/infra.py:734 |
| `/api/cost-optimization` | analytics merger | Medium | routes/infra.py:920 |
| `/api/automation-analysis` | analytics merger | Medium | routes/infra.py:981 |
| `/api/context-anatomy` | JSONL parse | Medium | routes/infra.py:1006 |
| `/api/security/threats` | gateway | Medium | routes/infra.py:650 |
| `/api/security/signatures` | filesystem | Medium | routes/infra.py:680 |
| `/api/security/posture` | composite | Medium | routes/infra.py:700 |
| `/api/component/runtime` | system probes (mostly N/A) | Medium | routes/components.py:488 |
| `/api/component/storage` | `df` (system probe) | N/A | routes/components.py:656 |
| `/api/component/network` | system probes | N/A | routes/components.py:717 |
| `/api/component/machine` | system probes | N/A | routes/components.py:571 |
| `/api/component/gateway` | gateway | Medium | routes/components.py:809 |
| `/api/cron-health` | gateway + analytics | Medium | routes/crons.py:965 |
| `/api/agent-intentions` | gateway + analytics | Medium | routes/crons.py:821 |

### Bypass — Hard

| Endpoint | Source | Difficulty | File:Line |
|---|---|---|---|
| `/api/channel/telegram` | log greps + JSONL | Hard | routes/channels.py:147 |
| `/api/channel/imessage` | log greps + JSONL | Hard | routes/channels.py:369 |
| `/api/channel/whatsapp` | log greps + JSONL | Hard | routes/channels.py:503 |
| `/api/channel/signal` | log greps + JSONL | Hard | routes/channels.py:628 |
| `/api/channel/discord` | log greps + JSONL | Hard | routes/channels.py:751 |
| `/api/channel/slack` | log greps + JSONL | Hard | routes/channels.py:906 |
| `/api/channel/irc` | log greps + JSONL | Hard | routes/channels.py:1062 |
| `/api/channel/webchat` | log greps + JSONL | Hard | routes/channels.py:1211 |
| `/api/channel/googlechat` | log greps + JSONL | Hard | routes/channels.py:1371 |
| `/api/channel/bluebubbles` | log greps + JSONL | Hard | routes/channels.py:1380 |
| `/api/channel/msteams` | log greps + JSONL | Hard | routes/channels.py:1557 |
| `/api/channel/tui` | log greps + JSONL | Hard | routes/channels.py:1566 |
| `/api/channel/matrix` | log greps + JSONL | Hard | routes/channels.py:1687 |
| `/api/channel/mattermost` | log greps + JSONL | Hard | routes/channels.py:1693 |
| `/api/channel/{line,nostr,twitch,feishu,zalo,tlon,synology-chat,nextcloud-talk}` | log greps + JSONL | Hard | routes/channels.py:1702-1744 |
| `/api/component/tool/<name>` (legacy fallback) | JSONL aggregation | Hard | routes/components.py:156 |
| `/api/health` | composite of many sources | Hard | routes/health.py:482 |
| `/api/system-health` | composite | Hard | routes/health.py:328 |
| `/api/diagnostics` / `/api/config-diagnostics` | composite | Hard | routes/health.py:703 |

### DuckDB-Full (already migrated — no work needed)

| Endpoint | Helper | File:Line |
|---|---|---|
| `/api/overview` | `_try_local_store_overview` | routes/overview.py:413 |
| `/api/timeline` | `_try_local_store_timeline` | routes/overview.py:643 |
| `/api/sessions` | `_try_local_store_sessions` | routes/sessions.py:158 |
| `/api/sessions/by-type` | `_try_local_store_sessions_by_type` | routes/sessions.py:255 |
| `/api/transcript/<id>` | `_try_local_store_transcript` | routes/sessions.py:1691 |
| `/api/usage` | `_try_local_store_usage` | routes/usage.py:703 |
| `/api/usage/anomalies` | `_try_local_store_usage_anomalies` | routes/usage.py:818 |
| `/api/anomalies` | `_try_local_store_anomalies` | routes/usage.py:860 |
| `/api/usage/by-plugin` | `_try_local_store_usage_by_plugin` | routes/usage.py:922 |
| `/api/usage/by-plugin/trend` | `_try_local_store_usage_by_plugin_trend` | routes/usage.py:994 |
| `/api/usage/cost-comparison` | `_try_local_store_cost_comparison` | routes/usage.py:1308 |
| `/api/model-attribution` | `_try_local_store_model_attribution` | routes/usage.py:1447 |
| `/api/skill-attribution` | `_try_local_store_skill_attribution` | routes/usage.py:1565 |
| `/api/crons` | `_try_local_store_crons` | routes/crons.py:362 |
| `/api/cron/<id>/runs` | `_try_local_store_cron_runs` | routes/crons.py:550 |
| `/api/cron/health-summary` | `_try_local_store_cron_health_summary` | routes/crons.py:639 |
| `/api/component/tool/<name>` | `_try_local_store_component_tool` | routes/components.py:170 |
| `/api/component/brain` | `_try_local_store_component_brain` | routes/components.py:1252 |
| `/api/reasoning` | `_try_local_store_reasoning` | routes/reasoning.py:289 |
| `/api/autonomy` | `_try_local_store_autonomy` | routes/autonomy.py:443 |
| `/api/advisor/ask` | `_try_local_store_advisor_context` | routes/advisor.py:198 |
| `/api/advisor/status` | `_try_local_store_advisor_status` | routes/advisor.py:463 |
| `/api/reliability` | `_try_local_store_reliability` | routes/health.py:188 |
| `/api/service-status` | `_try_local_store_service_status` | routes/health.py:894 |
| `/api/heartbeat-status` | `_try_local_store_heartbeat_status` | routes/health.py:1066 |
| `/api/sandbox-status` | `_try_local_store_sandbox_status` | routes/health.py:1266 |
| `/api/loop-detection` | `_try_local_store_loop_detection` | routes/health.py:1517 |
| `/api/mcp-stats` | `_try_local_store_mcp_stats` | routes/health.py:1772 |
| `/api/heartbeat` | `_try_local_store_heartbeat` | routes/heartbeat.py:280 |
| `/api/brain-history` | `_try_local_store_brain` | routes/brain.py:142 |
| `/api/nemoclaw/pending-approvals` | `_try_local_store_approvals` | routes/nemoclaw.py:305 |
| `/api/alerts/rules` | `_try_local_store_alert_rules` | routes/alerts.py:232 |
| `/api/memory-files` | `_try_local_store_memory_files` | routes/infra.py:569 |
| `/api/file` (GET) | `_try_local_store_file` | routes/infra.py:581 |
| `/api/memory-analytics` | `_try_local_store_memory_analytics` | routes/infra.py:639 |
| `/api/channels/<provider>/status` | `_channel_config_status_from_local_store` | routes/channels.py:106 |
| `/api/channels/status` | inline DuckDB | routes/channels.py:129 |
| `/api/local/*` (6 endpoints) | direct DuckDB allowlist | routes/local_query.py:210-254 |

### N/A (mutations, SSE, system probes, cloud-only, auth, gateway proxy)

POST/PUT/DELETE on alerts, budget, crons, channels, selfconfig, file write, heartbeat-ping,
nemoclaw approve/reject, anomalies/ack, sessions/<id>/stop, otel ingestion, gateway proxy
RPC, version, update, auth/check, otel-status, cloud-cta/* (cloud), update-check/*, fleet
register/metrics, history snapshots (DuckDB-equivalent already in fleet_history), brain-stream
SSE, logs-stream SSE, health-stream SSE, flow SSE.

## Per-blueprint coverage rollup

| Blueprint | Read surfaces | DuckDB | % covered |
|---|---|---|---|
| usage | 13 | 8 | 62% |
| health | 11 | 8 | 73% |
| sessions | 14 | 5 | 36% |
| crons | 4 | 3 | 75% |
| overview | 4 | 2 | 50% |
| infra | 11 | 3 | 27% |
| components | 7 | 2 | 29% |
| channels | 24 | 2 | 8% (per-provider chat history hard) |
| brain | 1 | 1 | 100% |
| reasoning | 1 | 1 | 100% |
| autonomy | 1 | 1 | 100% |
| advisor | 2 | 2 | 100% |
| heartbeat | 1 | 1 | 100% |
| alerts | 5 | 1 | 20% |
| nemoclaw | 4 | 1 | 25% |
| local_query | 6 | 6 | 100% |
| agents | 3 | 0 | 0% |
| skills | 3 | 0 | 0% |
| plugins | 1 | 0 | 0% |
| selfconfig | 5 | 0 | 0% (configs are file-of-truth) |
| selfevolve | 3 | 0 | 0% |
| fleet_history | 7 | sqlite-backed (counted N/A) | — |
| meta | 5 | 0 | clusters/version-impact migratable |
| update_check | 1 | 0 | config file is truth |

## What's getting migrated this PR

`feat/duckdb-coverage-batch-2026-05-13` adds `_try_local_store_*` fast paths to
the easiest 5 surfaces from the **Bypass — Easy** list above:

1. `/api/prompt-errors` — `_try_local_store_prompt_errors` (overview.py)
2. `/api/transcripts` — `_try_local_store_transcripts` (sessions.py)
3. `/api/heatmap` — `_try_local_store_heatmap` (health.py)
4. `/api/sessions/cost-breakdown` — `_try_local_store_cost_breakdown` (sessions.py)
5. `/api/sessions/<id>/cost-breakdown` — `_try_local_store_session_cost_breakdown` (sessions.py)

After this PR lands, DuckDB-Full coverage moves **38 → 43** (~37% → ~41%).
Remaining Bypass-Easy surfaces are tracked in the follow-up issue.
