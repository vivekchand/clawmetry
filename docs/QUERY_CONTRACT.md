# ClawMetry Query Contract (q/1)

> GENERATED FILE, do not edit by hand. Source of truth:
> `clawmetry/query_contract.py`. Regenerate with
> `python3 scripts/gen_query_contract_doc.py` (CI fails on drift).

The node query surface served by `routes/local_query.py` (`/api/local/*`
plus the daemon proxy and the cloud relay) is declared in
`clawmetry/query_contract.py`. This document is generated from that
registry; CI fails when they disagree.

## Evolution rule

Inside `q/1` evolution is **additive only**: new methods and new
optional args may be added. Renaming or removing a method, an arg, or a
response field requires bumping the contract to `q/2`. A `planned`
method is a declared target that is not served yet; shipping it means
flipping its registry entry to `live` in the same change (the drift
test enforces both directions).

## Trust classes

* `plaintext`: aggregate counters or metadata the server may see in
  cleartext (heartbeat piggyback). Never raw content.
* `e2e`: session/content-bearing payloads. These only ever leave the
  machine AES-256-GCM encrypted via the sync daemon snapshot path and
  must never appear on a plaintext push list.

## Read scopes

Every method declares one scope. An API key issued to a custom UI
(`clawmetry key create --scope read:metrics`) may dispatch only the
methods whose scope it carries, so what a user picks when they create a
key is the same fact the server enforces.

| Scope | Grants | Methods |
| - | - | - |
| `read:metrics` | Counts, tokens, cost and health. No prompts or replies. | `agent_graph`, `aggregates`, `health`, `models`, `runtimes` |
| `read:sessions` | One row per session: title, model, status, totals. | `rollup_sessions`, `search`, `sessions`, `similar_sessions` |
| `read:traces` | Spans, traces and outbound API calls. | `external_calls`, `robotics_events`, `robotics_incidents`, `robotics_runs`, `spans`, `traces` |
| `read:content` | The turns themselves: prompts, replies, tool calls. | `activity`, `error_groups`, `events`, `incidents`, `investigation`, `replay_events`, `session_catalog`, `session_context`, `transcript`, `transcript_page` |

`read:metrics` is exactly the `plaintext` trust class: a metrics-scoped
key can never return a prompt, a reply or a file path. That invariant is
pinned by CI, not by convention.

## Non-goals

* No per-model data in the device-facing `glance` method. Devices get
  top-line counters only; model breakdowns live in `models`.

## Methods

| Method | Status | Trust | Scope | Backing | Args | Description |
| - | - | - | - | - | - | - |
| `activity` | live | e2e | `read:content` | `query_activity` | `node_id`, `runtime`, `session_id`, `cursor`, `limit` (default 100, range 1..200) | Bounded persisted activity upserts, committed replay position and explicit resynchronization. |
| `agent_graph` | live | plaintext | `read:metrics` | `query_agent_graph` | `runtime`, `since`, `until`, `limit` (default 500, range 1..2000) | Cross-session agent spawn graph: nodes (agent_type+id stats) + spawn edges. Optional runtime arg scopes to one runtime ('openclaw' matches legacy NULL agent_type). |
| `aggregates` | live | plaintext | `read:metrics` | `query_aggregates` | `agent_id`, `since`, `until` | Per-day rollup of events/tokens/cost (aggregate counters only). |
| `error_groups` | live | e2e | `read:content` | `query_error_groups` | `node_id`, `runtime`, `session_id`, `days` (default 7, range 1..90), `limit` (default 500, range 1..1000) | Entitled, bounded recurring error groups with per-event resolution and explicit coverage. |
| `events` | live | e2e | `read:content` | `query_events` | `session_id`, `agent_id`, `event_type`, `since`, `until`, `limit` (default 200, range 1..5000) | Raw event rows (tool calls, messages, errors), newest first. |
| `external_calls` | live | e2e | `read:traces` | `query_external_calls` | `session_id`, `since`, `until`, `limit` (default 200, range 1..2000) | External (non-LLM) API calls captured by the interceptor. |
| `health` | live | plaintext | `read:metrics` | `health` | (none) | Store health snapshot (engine, size, ring depth, flush age). |
| `incidents` | live | e2e | `read:content` | `query_incidents` | `runtime`, `node_id`, `session_id`, `state`, `incident_id`, `limit` (default 100, range 1..500) | Durable Guard episodes with stable evidence and independent acknowledgement. |
| `investigation` | live | e2e | `read:content` | `query_investigation` | `session_id` (required), `runtime` (required), `node_id` (required), `incident_id`, `event_id`, `cursor`, `limit` (default 100, range 1..200) | Exact scoped evidence, bounded history continuation, execution state and explicit coverage. |
| `models` | live | plaintext | `read:metrics` | `query_rollup_model_daily` | `runtime`, `since`, `until`, `limit` (default 1000, range 1..10000) | Per-model daily token/cost rollup across runtimes. |
| `replay_events` | live | e2e | `read:content` | `query_replay_events` | `session_id` (required), `limit` (default 2000, range 1..10000) | Canonical replay-event rows for one session (#4813). Rows in kind-agnostic order; the /api/replay-tree endpoint groups them into turns/delegations/workflows/approvals. |
| `robotics_events` | live | e2e | `read:traces` | `robotics_events` | `run_id` (required), `after` (default 0, range 0..1000000000), `limit` (default 500, range 1..1000), `before`, `tail` (default False) | Paid robot trace page, ordered by source sequence with a continuation cursor. |
| `robotics_incidents` | live | e2e | `read:traces` | `robotics_incidents` | `run_id` (required), `before_ns`, `before_id`, `limit` (default 64, range 1..64) | Durable paid robot Guard incident history with a stable page cursor. |
| `robotics_runs` | live | e2e | `read:traces` | `robotics_runs` | `limit` (default 50, range 1..100), `before_ns`, `before_run_id` | Paid robot run summaries and measured state, newest first with a stable page cursor. |
| `rollup_sessions` | live | e2e | `read:sessions` | `query_rollup_sessions` | `runtime`, `limit` (default 200, range 1..2000) | Per-session materialized summary (title, status, totals, stuck flag). |
| `runtimes` | live | plaintext | `read:metrics` | `query_rollup_runtime_daily` | `since`, `until`, `limit` (default 1000, range 1..10000) | Per-runtime daily activity/cost rollup (claude_code, openclaw, ...). |
| `search` | live | e2e | `read:sessions` | `query_search` | `q` (required), `model`, `status`, `since`, `until`, `limit` (default 50, range 1..500) | Full-text search over session titles and eval reasons. |
| `session_catalog` | live | e2e | `read:content` | `query_session_catalog` | `node_id`, `runtime`, `session_id`, `limit` (default 100, range 1..200) | Bounded persisted session discovery, scoped before the limit. |
| `session_context` | live | e2e | `read:content` | `query_session_context` | `session_id` (required), `agent_type`, `limit` (default 200, range 1..1000) | Inputs & context rows for one session: system prompt, first user prompt, tool definitions, MCP servers, context files and runtime setup captured from context.compiled events. Content is redacted + capped; sha256/size describe the full text. |
| `sessions` | live | e2e | `read:sessions` | `query_sessions` | `agent_id`, `since`, `until`, `limit` (default 100, range 1..2000) | One row per session_id with start/end, event count, cost. |
| `similar_sessions` | live | e2e | `read:sessions` | `query_similar_sessions` | `session_id` (required), `window_days` (default 30, range 1..365), `limit` (default 10, range 1..50) | Runs shaped like this one (WO-60): nearest sessions by tool-call n-gram similarity inside a window, same runtime first, with score, runtime, model, cost, outcome. Carries session titles, so content class. |
| `spans` | live | e2e | `read:traces` | `query_spans` | `trace_id`, `session_id`, `agent_type`, `since`, `until`, `limit` (default 200, range 1..2000) | OTel span rows with full filters (trace/session/agent/time). |
| `traces` | live | e2e | `read:traces` | `query_traces` | `session_id`, `agent_type`, `since`, `until`, `limit` (default 100, range 1..1000) | One row per trace_id with aggregate span stats. |
| `transcript` | live | e2e | `read:content` | `query_events` | `session_id` (required), `limit` (default 500, range 1..5000) | Alias of events scoped to one required session_id. |
| `transcript_page` | live | e2e | `read:content` | `query_transcript_page` | `session_id` (required), `before_ts`, `limit` (default 150, range 1..250) | One older-history page of a session's events, newest-first. before_ts is an exclusive ms-epoch cursor (pass the previous page's next_before_ts to walk backward). Returns {rows, count, has_more, next_before_ts}. |
| `approvals` | planned | plaintext | `read:metrics` | `query_approvals` | `status`, `limit` (default 100, range 1..1000) | Approval queue metadata (ids, states, timestamps; no content). |
| `brain` | planned | e2e | `read:content` | `query_events` | `session_id`, `since`, `limit` (default 200, range 1..2000) | Reasoning/tool event slice powering the Brain feed. |
| `glance` | planned | plaintext | `read:metrics` | `rollup_glance` | (none) | Device-facing top-line counters (sessions, cost, alerts). Non-goal: no per-model data in glance. |
| `session` | planned | e2e | `read:sessions` | `query_sessions_table` | `session_id` (required) | Single-session detail row (title, status, outcome, totals). |
| `usage` | planned | plaintext | `read:metrics` | `rollup_usage_daily` | `runtime`, `since`, `until` | Daily token/cost usage series (input/output/cache splits). |

Live methods: 25. Planned methods: 5.
