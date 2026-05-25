# PRD — Closing ClawMetry's OpenClaw Observability Gaps

> **Status:** Draft for review · **Author:** Claude Code agent · **Date:** 2026-05-25
> **Source of truth:** [OpenClaw architecture docs](https://docs.openclaw.ai/concepts/architecture) crawled in depth (architecture, agent-loop, queue, gateway/protocol, multi-agent, subagents, memory, skills, tools, compaction, sandbox/tool-policy/elevated, presence) cross-referenced against the current ClawMetry codebase (`routes/`, `clawmetry/sync.py`, `clawmetry/local_store.py`, `frontend/`).

## TL;DR

ClawMetry observes OpenClaw's **outputs** well (sessions, transcripts, tokens, cost, channel messages, crons, health) but is largely blind to OpenClaw's **runtime control plane** — the parts that explain *why* the agent is doing what it's doing and *whether it's healthy right now*. The gateway exposes a protocol-v4 RPC surface of ~150 methods and ~30 event types; we ingest a thin slice. The biggest leverage is in five areas OpenClaw emits rich signals for and we surface ~nothing:

1. **Queue & lane concurrency** — the FIFO lane scheduler (`main`/`subagent`/`cron`/`nested`) that decides what runs and what waits. **Zero observability today.**
2. **Sub-agent live fan-out** — `sessions_spawn` depth tree, the task ledger (`tasks.*`), artifacts, the announce chain. **Tab is a "Coming soon" stub; task ledger not ingested.**
3. **Agent-turn lifecycle as a span waterfall** — `lifecycle`/`tool`/`compaction` streams, hook decision points, and the `session.long_running`/`stalled`/`stuck` diagnostics. **Brain feed shows events, not a turn anatomy; diagnostics not tapped.**
4. **Governance: tool-policy + exec-approval audit** — which tools were filtered and *why*, the `exec.approval.*` lifecycle, sandbox mode per agent, elevation events. **Not modeled (this is our moat vs. offline trace tools).**
5. **Context economics** — context-window utilization over time, compaction triggers (proactive vs. overflow), tokens reclaimed, pruning. **We list compaction events but not the economics.**

Every proposal below respects the three hard constraints: **DuckDB-first** (daemon ingests → DuckDB → encrypted snapshot → cloud renders client-side), **E2E encryption** (cloud computes nothing on OpenClaw data), and the **per-node cost/perf budget** (share one snapshot fetch, no request storms).

---

## 1. Method

For each OpenClaw subsystem I extracted (a) the exact observable signals OpenClaw emits — RPC methods, event names, stream phases, log lines, diagnostic states — and (b) what ClawMetry surfaces today, verified by grep against `routes/*.py`, `sync.py`, `local_store.py`, and `frontend/`. The gap is the delta. Proposals are scoped to signals OpenClaw *actually exposes* (no speculative instrumentation of OpenClaw internals), reachable via the gateway WS tap (`clawmetry/gateway_tap.py`), JSON-RPC polling, JSONL/log ingest, or OTLP.

---

## 2. Coverage scorecard

| OpenClaw subsystem | Signals OpenClaw exposes | ClawMetry today | Grade |
|---|---|---|---|
| Sessions & transcripts | `sessions.*`, `chat.history`, JSONL | Sessions list, transcript, cost-split, compaction list | 🟢 Strong |
| Token usage & cost | `usage.cost`, `usage.status`, `sessions.usage.*` | Usage tab, cost breakdown, model/skill attribution, anomalies | 🟢 Strong |
| Channels (messages) | `channels.status`, per-channel JSONL | 21 adapters, messages, delivery-health | 🟢 Strong |
| Crons | `cron.*` (CLI writes) | Cron CRUD, runs, health | 🟢 Strong |
| System health | `health`, `status`, OTLP | system-health, reliability, heatmap | 🟢 Strong |
| **Queue / lane concurrency** | lane scheduler, `/queue` modes, depth, `drop` policy, "waited >2s" | Only static `maxConcurrent` config echo (`components.py:1225`) | 🔴 **Blind** |
| **Sub-agent fan-out** | `sessions_spawn`, depth 0/1/2, `tasks.*`, `artifacts.*`, announce chain | subagents table + delegation tree; **task ledger not ingested; tab is stub** | 🟠 Partial |
| **Agent-turn lifecycle** | `lifecycle`(start/end/error), `tool`(start/update/end), hook points, `deliveryStatus` | Brain feed (flat event list), llm-call-timeline | 🟠 Partial |
| **Stuck/stalled diagnostics** | `session.long_running` / `stalled` / `stuck`, `diagnostics.stability` | ClawMetry's own heuristic alerts only; `diagnostics.stability` **not tapped** | 🔴 **Blind** |
| **Tool policy & provenance** | `tools.catalog` (provenance), `tools.effective`, `agents/tool-policy` audit logs | Tool call counts + flow lanes; **no provenance, no policy audit** | 🟠 Partial |
| **Exec approvals / sandbox / elevated** | `exec.approval.*`, `plugin.approval.*`, `sandbox explain`, `/elevated` | approvals table; Nemoclaw approvals stub; sandbox **inferred** | 🟠 Partial |
| **Context / compaction economics** | `compaction` stream, overflow-error patterns, `Compactions:<n>`, pruning | `/api/compactions` event list only | 🟠 Partial |
| **Memory subsystem** | `doctor.memory.status`, backends (SQLite/QMD/Honcho/LanceDB), dreaming, index status | memory_blobs + memory-access timeline (as a tool) | 🟠 Partial |
| **Skills runtime** | `skills.status` eligibility, ClawHub scan state, per-session snapshot, token cost | skill attribution; **tab is stub; no eligibility/why-not-loaded** | 🟠 Partial |
| **Channel routing / bindings** | binding rules (peer/guildId/teamId/accountId), `deliveryStatus` | message lists per channel; **no routing explainer** | 🟠 Partial |
| **Nodes / presence topology** | `system-presence` (modes, Active/Idle/Stale), `node.*`, caps, `node.invoke` | heartbeat gauge, fleet nodes | 🟠 Partial |
| **Config / update / secrets** | `config.*` + `reloadKind`, `update.*`, `secrets.reload` | config snapshot, version/update check | 🟠 Partial |
| **Talk / TTS / voice** | large `talk.*` surface (realtime/transcription/managed-room/telephony) | — | 🔴 **Blind** |
| **Payload/transport diagnostics** | `payload.large` events (oversized frames, slow buffers) | — | 🔴 **Blind** |

---

## 3. Cross-cutting foundation (do this first — it unblocks everything)

Most gaps share a root cause: **we only tap a thin slice of the gateway WS protocol and don't persist the control-plane events.** Before building tabs, widen the pipe.

### F1. Subscribe to the full gateway event family in `gateway_tap.py`
OpenClaw broadcasts these events to any client with `operator.read`: `session.operation`, `session.tool`, `sessions.changed`, `exec.approval.requested|resolved`, `plugin.approval.*`, `cron`, `payload.large`, `node.pair.*`, `device.pair.*`, plus `presence`/`health`/`heartbeat`/`tick`. We currently consume a subset. **Action:** subscribe to the full allowlist, normalize each into a typed DuckDB row (`control_events` table with `kind`, `seq`, `state_version`, `payload_json`, `ts_ms`), and respect per-connection `seq` to detect dropped frames.

### F2. Poll the read-only diagnostic RPCs on the daemon's existing tick
These need a single `operator.read` call each and are pure gold:
- `diagnostics.stability` — OpenClaw's own bounded diagnostic recorder.
- `tasks.list` / `tasks.get` — the **sub-agent/background task ledger** (filter by `status`, `agentId`, `sessionKey`).
- `tools.catalog` — runtime tool catalog **with provenance** (builtin vs. plugin vs. MCP).
- `skills.status` — skill inventory with eligibility/config checks.
- `usage.status` — provider quota windows (rate-limit headroom).
- `system-presence` — client/node presence with mode + recency.

**Action:** add a `_poll_gateway_diagnostics()` pass (cheap, ~6 RPCs, 30–60s cadence, gated like other pollers) writing to new DuckDB tables. All of it rides the existing snapshot → Redis → client-render path.

### F3. New snapshot keys
Add top-level snapshot keys so cloud interceptors can light up tabs without server compute: `laneState`, `taskLedger`, `turnSpans`, `toolPolicy`, `execApprovals`, `contextEconomics`, `memoryHealth`, `skillEligibility`, `routingTrace`, `presenceTopology`. Each must be **bounded** (cap rows, strip heavy fields per the snapshot-bloat lesson) and reuse `window.__cmSnap` on the cloud side.

---

## 4. Prioritized initiatives

Each initiative: **Gap → Signals available → Proposed visualization → Data path → Effort → Success metric.**

### 🔴 P0 — "What is OpenClaw doing right now"

#### P0-1. Lane & Queue Monitor *(new tab: "Scheduler")*
- **Gap:** We show static `maxConcurrent`/`maxSubagents` config but nothing about live scheduling. Users can't see *why a reply is slow* or *that a lane is saturated*.
- **Signals:** Lane model — `session:<key>` serialized, global lanes `main`(cap 4)/`subagent`(cap 8)/`cron`/`cron-nested`/`nested`; `/queue` modes `steer|followup|collect|interrupt`; `drop` policy `summarize|old|new`; `debounceMs`(500), `cap`(20); verbose "queued run waited >2s" notices; `session.operation` events for in-flight ops.
- **Visualization:** Live lane-saturation bars (running / cap per lane), a queue-depth-over-time sparkline per lane, a "waiting" list with wait-time-so-far, and a per-session badge showing active `/queue` mode. Highlight backpressure when a lane is at cap with a growing queue.
- **Data path:** `session.operation` + lane state from `diagnostics.stability` → `lane_state` table → `laneState` snapshot key → client renders.
- **Effort:** M (ingest + one tab). **Metric:** user can answer "is my agent queue-bound and which lane?" in <5s; backpressure visible before the user notices lag.

#### P0-2. Live Sub-agent Fan-out Tree *(complete the stubbed "Sub agents" tab)*
- **Gap:** `subagents` table + a delegation tree exist, but the v2 tab is a "Coming soon" stub and **the task ledger (`tasks.*`) and artifacts are not ingested at all.** No live depth, no lane-8-cap saturation, no announce-chain, no orphan/tombstone recovery.
- **Signals:** `sessions_spawn` → `{runId, childSessionKey}`; session-key depth shape `agent:<id>:main` → `:subagent:<uuid>` → `:subagent:<uuid>:subagent:<uuid>` (max `maxSpawnDepth` 1–5); `maxChildrenPerAgent`(5), subagent lane cap (8); announce status `success|error|timeout|unknown` with runtime + I/O/total tokens + est. cost; `context: isolated|fork`; `tasks.list/get/cancel`; `artifacts.list/get/download`; `archiveAfterMinutes`(60); orphan recovery tombstones; `ANNOUNCE_SKIP`/`NO_REPLY` suppression.
- **Visualization:** Live tree (depth 0→2) with per-node status pill, runtime, tokens, cost; a "subagent lane: 6/8" saturation header; the announce chain as upward edges; an artifacts drawer per run; a "stuck/orphaned" filter. Cost rolls up to the parent turn.
- **Data path:** `tasks.*` poll + spawn/announce events → extend `subagents` table + new `task_ledger`/`artifacts_index` tables → `taskLedger` snapshot key.
- **Effort:** M–L. **Metric:** every active spawn visible within one snapshot cycle with correct depth, status, and cost rollup; verified against `/subagents list`.

#### P0-3. Turn Anatomy waterfall + stuck/stalled detector *(upgrade Brain → "Live trace")*
- **Gap:** Brain renders a flat event feed. OpenClaw's turn is a structured lifecycle with streams and hook decision points, and it emits explicit stuck/stalled diagnostics we ignore.
- **Signals:** Streams `lifecycle`(phase start/end/error), `assistant`(deltas), `tool`(start/update/end), `compaction`; hook points `before_model_resolve`, `before_prompt_build`, `before_agent_reply`, `before_tool_call`(can `block:true`), `after_tool_call`, `before/after_compaction`, `tool_result_persist`; diagnostics `session.long_running`/`stalled`/`stuck` (`diagnostics.stuckSessionWarnMs`); reply `deliveryStatus` = `sent|suppressed|partial_failed|failed`; `agent.wait` terminal `{status, startedAt, endedAt}`.
- **Visualization:** Per-turn waterfall — prompt-assembly → model-resolve (with hook overrides flagged) → model stream → each tool call as a span (start→end, latency, sanitized result size) → compaction (if any) → reply (with `deliveryStatus`). A red marker where a hook **blocked** a tool call (governance signal). A persistent "Stalled/Stuck" strip listing sessions OpenClaw flagged.
- **Data path:** `lifecycle`/`tool`/`session.tool` events + `diagnostics.stability` → `turn_spans` table → `turnSpans` snapshot key.
- **Effort:** L. **Metric:** a turn's wall-clock decomposes into visible spans summing to total; stalled sessions surface within `stuckSessionWarnMs`; hook-block events are countable.

### 🟠 P1 — Governance & economics (the moat)

#### P1-1. Tool-policy & Exec-approval audit *(complete "Approvals" + new "Policy" panel)*
- **Gap:** Approvals exist as a table but the rich lifecycle + the *reason* tools were filtered isn't surfaced. This is exactly the enforcement/governance story that differentiates us from offline trace+eval tools.
- **Signals:** `exec.approval.requested|resolved`, `plugin.approval.requested|resolved`, `exec.approval.waitDecision`, `systemRunPlan` (canonical argv/cwd/rawCommand); three controls — sandbox (`off|non-main|all`), tool policy (allow/deny, `group:*`, "deny wins", "non-empty allow blocks rest"), elevated (`/elevated on`, `tools.elevated.allowFrom.<provider>`); audit logs `agents/tool-policy` (rule label, config key, affected tool); `sandbox explain` effective mode/scope/source.
- **Visualization:** Approval timeline (requested → decided, who/scope/latency-to-decision); a "tools filtered this turn and why" panel (rule label + config key, sourced from tool-policy audit); a per-agent sandbox-mode matrix; elevation-event log. Tie each blocked exec to its `systemRunPlan`.
- **Data path:** approval events + tool-policy audit log lines → extend `approvals` table + new `tool_policy_audit` table → `toolPolicy`/`execApprovals` snapshot keys. Keep cloud route `oss-passthrough`.
- **Effort:** M. **Metric:** every approval decision and every policy-blocked tool is attributable to a rule + config key; verified against `openclaw logs`.

#### P1-2. Context Economics *(upgrade Context tab)*
- **Gap:** We list compaction *events* but not the economics that drive cost and quality.
- **Signals:** auto-compaction proactive (near limit) vs. reactive (overflow patterns: `request_too_large`, `context length exceeded`, `input is too long`, …); `compaction` stream start/complete; `Compactions:<count>`; `maxActiveTranscriptBytes`, `keepRecentTokens`, `identifierPolicy`, `truncateAfterCompaction`; compaction-vs-pruning distinction; memory-flush turn before compaction.
- **Visualization:** Context-window utilization gauge over the turn timeline (% of model limit), compaction markers tagged proactive/overflow, tokens-before/after (reclaimed), and a pruning-vs-compaction split. Flag sessions that overflow-then-retry repeatedly (a cost/quality smell).
- **Data path:** compaction stream events + token deltas from `model.completed` → `context_economics` table → snapshot key.
- **Effort:** M. **Metric:** each compaction is classified proactive/overflow with reclaimed-token delta; repeated-overflow sessions are flagged.

#### P1-3. Tool Catalog & Provenance + per-tool latency
- **Gap:** We count tool calls but can't answer "where did this tool come from?" or "which tools are even available in this session?" or "what's the p95 latency of `exec`?"
- **Signals:** `tools.catalog` (provenance: builtin/plugin/MCP, provider-prefixed names like `outlook__send_mail`), `tools.effective` (per-`sessionKey`), tool groups (`group:runtime|fs|web|memory|sessions|automation|plugins`), deferred/dynamic tools (Codex), `tool` stream start→end timing.
- **Visualization:** A tool catalog grouped by provenance with enabled/filtered state per session; per-tool latency p50/p95 and error rate; "effective tools for this session" inspector.
- **Data path:** `tools.catalog`/`tools.effective` poll + tool-stream timing → `tool_catalog` + `tool_latency` tables → snapshot key.
- **Effort:** M. **Metric:** every tool the agent calls maps to a provenance source; p95 latency available per tool.

### 🟡 P2 — Depth & coverage

#### P2-1. Memory subsystem health *(complete "Memory" tab)*
- **Signals:** `doctor.memory.status` (embedding/vector readiness, `probe`/`deep`), `doctor.memory.remHarness`; backends builtin-SQLite/QMD/Honcho/LanceDB; hybrid search (vector + keyword); `memory_search`/`memory_get` (we already track as tools); dreaming (cron consolidation, `DREAMS.md`, score/recall/diversity gates); index status (`openclaw memory status/index`); `MEMORY.md` truncation when over bootstrap budget; memory-flush before compaction.
- **Visualization:** Embedding-provider readiness badge, backend identity, search hit/miss + retrieval latency, dreaming activity (items promoted), index freshness, and a **truncation warning** when `MEMORY.md` exceeds budget.
- **Data path:** `doctor.memory.status` poll + memory-tool timing → `memory_health` table → snapshot key. **Effort:** M.

#### P2-2. Skill eligibility & cost *(complete "Skills" tab)*
- **Signals:** `skills.status` (eligibility/config checks); gates `requires.bins|anyBins|env|config`, `os`, `always`; precedence (workspace > project-agent > personal > managed > bundled > extraDirs); per-agent allowlist (non-empty list is final); per-session skill snapshot + watcher refresh; token cost (~24 tokens/skill, 195-char base + 97/skill); ClawHub security scan state (VirusTotal/ClawScan); install/update tracking.
- **Visualization:** Per-session loaded-skills list with **"why not loaded"** (failed gate: missing bin/env/config/os); skill token-cost contribution to the system prompt; ClawHub scan state per installed skill.
- **Data path:** `skills.status` poll → `skill_eligibility` table → snapshot key. **Effort:** M.

#### P2-3. Channel routing / binding explainer + delivery status
- **Signals:** binding rules in priority order (peer → parentPeer → guildId+roles → guildId → teamId → accountId → channel `*` → default agent), AND semantics, multi-account `accountId`/`defaultAccount`; `agent` `deliveryStatus` = `sent|suppressed|partial_failed|failed`.
- **Visualization:** Per inbound message, "routed to agent X because binding rule Y matched"; a multi-account map; delivery-status breakdown per channel.
- **Data path:** message metadata + routing events → extend `channel_messages` → `routingTrace` snapshot key. **Effort:** M.

#### P2-4. Node topology & presence
- **Signals:** `system-presence` (modes ui/webchat/cli/backend/probe/test/node; Active/Idle/Stale; 5-min TTL; `lastInputSeconds`); `node.list/describe`, caps (camera/canvas/screen/location/voice/talk), `commands`, `node.invoke`/`node.invoke.result`, `node.presence.alive` triggers (background/silent_push/significant_location/bg_app_refresh/manual/connect).
- **Visualization:** Node/operator topology with capability chips, Active/Idle/Stale state, last-input recency, and a `node.invoke` activity log. Extends the existing fleet view from "list" to "topology + capabilities."
- **Data path:** `system-presence` + `node.*` poll/events → `presence_topology` table → snapshot key. **Effort:** M.

#### P2-5. Config-change audit trail
- **Signals:** `config.set/patch/apply`, `config.schema.lookup` `reloadKind` (`restart|hot|none`), `update.run/status`, `secrets.reload`. **Visualization:** timeline of config changes with hot-vs-restart classification and config-hash diffs; update-restart events. **Data path:** `config.get` hash polling + config events → `config_audit` table. **Effort:** S–M.

#### P2-6 (stretch). Voice/Talk observability
- The `talk.*` surface (realtime/transcription/STT-TTS/managed-room/telephony/meeting) is entirely unobserved. Lower priority unless a node user runs voice. Track turn lifecycle, barge-in, TTS provider/fallback, tool-results-in-voice. **Effort:** L. **Note:** revisit only if usage data shows voice adoption.

---

## 5. Sequencing

```
Phase 0 (foundation):  F1 widen WS tap  →  F2 diagnostic RPC poll  →  F3 snapshot keys
Phase 1 (ship the "now"):  P0-1 Scheduler  ·  P0-2 Sub-agent tree  ·  P0-3 Turn anatomy
Phase 2 (moat):  P1-1 Policy/Approvals audit  ·  P1-2 Context economics  ·  P1-3 Tool provenance
Phase 3 (depth):  P2-1 Memory  ·  P2-2 Skills  ·  P2-3 Routing  ·  P2-4 Topology  ·  P2-5 Config
Phase 4 (stretch):  P2-6 Voice
```

Phase 0 is the unlock — once the daemon taps the full event family + diagnostic RPCs and writes typed DuckDB tables, each tab is mostly a snapshot key + a `cm-cloud-*` interceptor mirroring `cm-cloud-models`.

---

## 6. Constraints & risks (carry into every PR)

- **DuckDB-first.** No handler reads `~/.openclaw`/JSONL/process stats directly — daemon ingests → DuckDB → snapshot. Build on the daemon's own writer handle, never a `read_only=True` re-open (the #1771 brick-lock).
- **E2E encryption.** Cloud computes nothing on OpenClaw data; all new tabs render client-side from the decrypted snapshot via `window.__cmSnap`. New routes default to `oss-passthrough` (never a 410 the OSS JS calls).
- **Cost/perf budget.** New diagnostic polls share one cadence and one snapshot fetch — no per-tab pollers, no per-interceptor snapshot fetches. Gate heavy polls on the active tab. Bound every new snapshot key and strip heavy fields (the snapshot-bloat lesson).
- **Read-only.** ClawMetry observes; it must not change scheduling, approvals, or policy (cron writes via the CLI remain the sole exception). Approval/policy tabs are *views*, not controls — unless we deliberately add the relay-backed write path later, gated behind `operator.approvals`.
- **Gateway token scope.** Our token is `operator.read`. Every RPC in F2 (`diagnostics.stability`, `tasks.list`, `tools.catalog`, `skills.status`, `usage.status`, `system-presence`) is read-scoped — confirmed against the protocol scope table. Anything needing `operator.admin`/`approvals` is out of scope for observation.
- **Verify against live data, not fixtures.** OpenClaw v3 normalizes event types; smoke every ingest against live DuckDB + decrypt the cloud snapshot before claiming done.

---

## 7. Open questions

1. **Tap vs. poll for the control plane** — does subscribing to the full WS event family (F1) give us enough, or do we still need the periodic diagnostic RPCs (F2)? Likely both: events for real-time, RPCs for snapshot/state. Validate WS volume against the cost budget first.
2. **One "Scheduler"/"Control plane" tab vs. enriching existing tabs?** Lane+queue is genuinely new (P0-1 new tab); sub-agent/turn/context map onto existing surfaces. Lean toward enriching where a home exists.
3. **How much of the v2 React rebuild do we target?** Several proposals (Sub-agents, Approvals, Skills, Fleet sonar) are already stubbed-out nav entries in `frontend/` — confirm whether v2 ships before building these, or whether to land them in the live v1 template/static frontend first.
4. **Voice (P2-6) — is there any real-world usage to justify it?** Defer until node telemetry shows voice/talk sessions in the wild.

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
