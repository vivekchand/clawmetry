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

## Non-goals

* No per-model data in the device-facing `glance` method. Devices get
  top-line counters only; model breakdowns live in `models`.

## Methods

| Method | Status | Trust | Backing | Args | Description |
| - | - | - | - | - | - |
| `agent_graph` | live | plaintext | `query_agent_graph` | `since`, `until`, `limit` (default 500, range 1..2000) | Cross-session agent spawn graph: nodes (agent_type+id stats) + spawn edges. |
| `aggregates` | live | plaintext | `query_aggregates` | `agent_id`, `since`, `until` | Per-day rollup of events/tokens/cost (aggregate counters only). |
| `events` | live | e2e | `query_events` | `session_id`, `agent_id`, `event_type`, `since`, `until`, `limit` (default 200, range 1..5000) | Raw event rows (tool calls, messages, errors), newest first. |
| `external_calls` | live | e2e | `query_external_calls` | `session_id`, `since`, `until`, `limit` (default 200, range 1..2000) | External (non-LLM) API calls captured by the interceptor. |
| `health` | live | plaintext | `health` | (none) | Store health snapshot (engine, size, ring depth, flush age). |
| `models` | live | plaintext | `query_rollup_model_daily` | `runtime`, `since`, `until`, `limit` (default 1000, range 1..10000) | Per-model daily token/cost rollup across runtimes. |
| `rollup_sessions` | live | e2e | `query_rollup_sessions` | `runtime`, `limit` (default 200, range 1..2000) | Per-session materialized summary (title, status, totals, stuck flag). |
| `runtimes` | live | plaintext | `query_rollup_runtime_daily` | `since`, `until`, `limit` (default 1000, range 1..10000) | Per-runtime daily activity/cost rollup (claude_code, openclaw, ...). |
| `search` | live | e2e | `query_search` | `q` (required), `model`, `status`, `since`, `until`, `limit` (default 50, range 1..500) | Full-text search over session titles and eval reasons. |
| `sessions` | live | e2e | `query_sessions` | `agent_id`, `since`, `until`, `limit` (default 100, range 1..2000) | One row per session_id with start/end, event count, cost. |
| `spans` | live | e2e | `query_spans` | `trace_id`, `session_id`, `agent_type`, `since`, `until`, `limit` (default 200, range 1..2000) | OTel span rows with full filters (trace/session/agent/time). |
| `traces` | live | e2e | `query_traces` | `session_id`, `agent_type`, `since`, `until`, `limit` (default 100, range 1..1000) | One row per trace_id with aggregate span stats. |
| `transcript` | live | e2e | `query_events` | `session_id` (required), `limit` (default 500, range 1..5000) | Alias of events scoped to one required session_id. |
| `approvals` | planned | plaintext | `query_approvals` | `status`, `limit` (default 100, range 1..1000) | Approval queue metadata (ids, states, timestamps; no content). |
| `brain` | planned | e2e | `query_events` | `session_id`, `since`, `limit` (default 200, range 1..2000) | Reasoning/tool event slice powering the Brain feed. |
| `glance` | planned | plaintext | `rollup_glance` | (none) | Device-facing top-line counters (sessions, cost, alerts). Non-goal: no per-model data in glance. |
| `session` | planned | e2e | `query_sessions_table` | `session_id` (required) | Single-session detail row (title, status, outcome, totals). |
| `usage` | planned | plaintext | `rollup_usage_daily` | `runtime`, `since`, `until` | Daily token/cost usage series (input/output/cache splits). |

Live methods: 13. Planned methods: 5.
