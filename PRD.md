# ClawMetry — Product Requirements Document

**Status:** living document · last updated 2026-05-20
**Scope:** every shipped feature across OSS (`pip install clawmetry`) and Cloud (`app.clawmetry.com`)
**Purpose:** the contract that any refactor (most urgently the local-first refactor in #964) must not silently break

This document does not propose new work. It describes what exists today.

---

## 1. Vision in one paragraph

ClawMetry is a real-time observability dashboard for AI agents. A user runs `pip install clawmetry && clawmetry` on the same machine as their agent (OpenClaw, Claude Code, Hermes, etc.) and gets a zero-config web dashboard at `http://localhost:8900` showing live sessions, token spend, agent reasoning, cron jobs, memory state, and message flow. Optional Cloud Pro subscription adds remote viewing at `app.clawmetry.com`, multi-node fleet aggregation, human-in-the-loop approvals for risky tool calls, and multi-channel alerting.

Three product pillars: **zero config**, **read-only by default** (we observe agents, we don't modify them), **end-to-end encrypted** when data leaves the device.

---

## 2. Target users and plans

### Personas
- **Solo OSS dev** — runs one agent on one laptop. Pip-installs, opens dashboard, never touches cloud. Free forever.
- **Cloud Free** — same as above but signed up for an account. Gets remote-view at `app.clawmetry.com` for the dashboard but no team features.
- **Cloud Pro (paid)** — multi-node fleets, team alerts, human-approval workflows, longer retention, channel integrations.
- **NemoClaw operator** — runs N sandboxed OpenClaw boxes; each registers as a separate node automatically.

### Plan matrix

| Plan | Cost | Local dashboard | Remote dashboard | Cloud sync | Alerts | Approvals | Notifications | Multi-node | Trial-flag |
|---|---|---|---|---|---|---|---|---|---|
| **OSS only** | $0 | ✓ | — | — | local only | — | — | local only | n/a |
| **Cloud Free** | $0 | ✓ | ✓ (heartbeat only) | heartbeat only | 1 alert visible | empty queue | — | — | `free` |
| **Cloud Trial** | $0 / 14 d | ✓ | ✓ | full | unlimited | full | unlimited | full | `trial` |
| **Cloud Pro** | paid | ✓ | ✓ | full | unlimited | full | unlimited | full | `cloud_pro` |
| **Trial-Expired** | $0 | ✓ | dashboard frozen at last sync | paused | view only | view only | view only | partial | `trial_expired` |

Plan transitions are driven by Stripe webhooks and the `users.plan` column in Cloud SQL. Trial auto-starts on first signup, no card required.

---

## 3. Architecture in three sentences

A user's machine runs the **OSS Flask app** (`dashboard.py` + `routes/*.py`), which auto-detects the OpenClaw workspace, tails session JSONLs, talks to the OpenClaw gateway over WebSocket, and serves a single-page dashboard. An optional **sync daemon** (`clawmetry/sync.py`) ships an E2E-encrypted subset of that telemetry to the **Cloud** (`clawmetry-cloud/dashboard.py` + Cloud Run + Cloud SQL Postgres + PgBouncer sidecar), which is itself a hosted instance of the same dashboard rendered with `CLOUD_MODE=1`. End-to-end encryption uses AES-256-GCM with a per-user key that never leaves the device; cloud stores ciphertext, browser decrypts.

For the canonical architecture diagram, see `ARCHITECTURE.md`. For the local-first refactor that will reshape this, see issue #964.

---

## 4. Feature catalog

Each row describes one user-visible feature. **Surface** is where the user encounters it. **Where** is OSS / Cloud / both. **Gate** is the plan boundary.

### 4.1 Dashboard tabs

| Feature | What it does | Surface | Where | Gate | Code |
|---|---|---|---|---|---|
| **Overview** | KPIs: live sessions, tokens today, cost today, active crons, system health, recent activity timeline | Default landing tab | Both | free | `routes/overview.py` |
| **Brain** | Unified real-time stream of every reasoning event, tool call, error, channel message; filter by source/type/channel | Tab + SSE stream | Both | free | `routes/brain.py`, `templates/tabs/brain.html` |
| **Sessions / Transcripts** | Full JSONL transcript replay, per-session token + cost split, sub-agent tree, compaction view, per-message attribution | Tab + per-session detail page | Both | free | `routes/sessions.py` |
| **Tokens / Usage** | Daily token + cost charts by model, provider, skill; anomaly detection; reset-archive aware | Tab | Both | free | `routes/usage.py` |
| **Crons** | List + create + pause + delete agent cron jobs via gateway RPC; calendar view; Active/Paused tabs | Tab | Both | free | `routes/crons.py` |
| **Memory** | Browse + edit agent's markdown memory files (USER.md, IDENTITY.md, etc.); preview shows raw markdown | Tab + editor | Both | free | `routes/infra.py:bp_memory` |
| **Flow** | Real-time bubble visualization: channels → gateway → models → tools | Tab | Both | free | `routes/components.py` |
| **Context** | Inspect what's currently in the LLM's context window (system prompt, tools, conversation) | Tab | Both | free | `templates/tabs/context.html` |
| **Approvals** | Human-in-the-loop queue for policy-guarded tool calls; visual policy builder (no YAML); approve/deny via Slack/email/phone | Tab + browser approve page | Both UI / Cloud-only delivery | **Pro** | `routes/nemoclaw.py`, `clawmetry-cloud/routes/cloud.py` |
| **Alerts** | Rule-based alerts on cost spike, session duration, token velocity, node offline, sub-agent depth | Tab + write API | Both UI / Cloud-only evaluator | **Pro** (free sees 1) | `routes/alerts.py` |
| **Notifications** | Configure delivery channels (Slack, email, PagerDuty, Telegram, phone) for alerts + approvals | Tab | Cloud only | **Pro** | `clawmetry-cloud/routes/channels.py` |
| **Fleet** | Multi-node aggregation: per-node status, today_cost, active_sessions across N machines | Tab | Both | free for OSS local · **Pro** for cloud-aggregated | `routes/fleet_history.py` |
| **System Health** | Disk/CPU/memory/GPU; reliability score; gateway latency; OTLP ingest rate | Tab | Both | free | `routes/health.py` |
| **Self-Evolve / Advisor** | NL Q&A about agent behaviour ("why did spend spike yesterday?"); recommended config changes | Tab + chat panel | Both | free (Pro polish) | `routes/advisor.py`, `routes/selfevolve.py` |
| **Skills** | Tool/skill inventory with invocation counts | Sub-tab | Both | free | `templates/tabs/skills.html` |
| **Models** | Model usage by token count + cost attribution | Sub-tab | Both | free | `templates/tabs/models.html` |
| **Limits** | API rate limit monitor from OTLP traces | Sub-tab | Both | free | `templates/tabs/limits.html` |
| **Logs** | Real-time log tail + search across log files | Sub-tab | Both | free | `routes/infra.py:bp_logs` |
| **History** | Time-series metrics over 1h/6h/24h/7d/30d (requires SQLite history backend) | Sub-tab | Both | free | `history.py`, `routes/fleet_history.py` |
| **Version Impact** | Diff agent behaviour between two model versions | Sub-tab | Both | free | `routes/meta.py:bp_version_impact` |
| **NemoClaw** | Per-sandbox governance, policy editor, sandbox health | Tab | Cloud only | **Pro** | `routes/nemoclaw.py` |
| **Clusters** | Cluster sessions by behavioural similarity | Sub-tab | Both | free | `templates/tabs/clusters.html` |

### 4.2 Sync daemon — what gets shipped to cloud

| Stream | Cadence | Endpoint | Encrypted | Notes |
|---|---|---|---|---|
| Heartbeat | every 15 s | `/ingest/heartbeat` | no | always sent regardless of plan; carries `sync_allowed` answer back |
| Events (Brain) | batches of 200 | `/ingest/events` | E2E (AES-256-GCM) | gated by `sync_allowed` |
| Sessions | on-change | `/ingest/sessions` | E2E | metadata only; transcript content is in events |
| Logs (real-time) | every 2 s, ≤50 lines | `/ingest/stream` | E2E | gated |
| Logs (batch backfill) | per cycle, ≤5000 events | `/ingest/logs` | E2E | gated |
| Memory snapshots | hourly + on-change | `/ingest/memory` | E2E | gated |
| System snapshot | every 5–10 min | `/ingest/system-snapshot` | E2E | hardware + security posture |
| Crons | on-change | (via events) | E2E | cron_state event type |
| Autonomy daily roll-up | nightly, 1/node/day | `/ingest/autonomy` | no | small aggregate |
| Claude Code transcripts | when detected | `/ingest/events` (parsed first) | E2E | reads `~/.claude/projects/*/sessions/*.jsonl` |

For the design that will move most of these from "ship to cloud" to "store locally + relay-on-demand", see #964.

### 4.3 CLI surface

| Command | Purpose |
|---|---|
| `clawmetry` | start local dashboard (default port 8900) |
| `clawmetry connect` | sign in / pair with Cloud Pro, register sync daemon as launchd or systemd service |
| `clawmetry setup` | retry `connect` (after install-time cloud reach failure) |
| `clawmetry status` | daemon status, API key validity, node ID, last sync |
| `clawmetry status --show-key` | print the E2E encryption key (for browser unlock) |
| `clawmetry sync` | run sync daemon in foreground (debugging) |
| `clawmetry account` | manage API key, referral code, subscription |
| `clawmetry disconnect` | revoke cloud sync, keep local dashboard |
| `clawmetry uninstall` | remove daemon + clean config |
| `clawmetry proxy` | start budget-enforcement + loop-detection proxy on port 4100 |

CLI auto-detects NemoClaw sandboxes during `connect` and registers a separate daemon per sandbox.

### 4.4 Channel adapters

ClawMetry observes (and in most cases sends to) **22 chat channels** through `routes/channels.py`. Each adapter is a Flask blueprint that:
- Parses inbound messages from the channel into Brain events
- Optionally implements an outbound `send` (for replying through the agent)

Read+send: Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, WebChat, Google Chat, BlueBubbles, MS Teams, Matrix, Mattermost, LINE, Feishu, Synology Chat, Nextcloud Talk, Tlon (Urbit), Zalo, CLI, TUI.

Read-only: Nostr, Twitch.

Each appears as a filterable lane in the Brain tab and a chip in the Flow tab.

### 4.5 Cloud-only features

These do not exist in OSS and require a `cm_…` token + a Cloud account.

- **Auth + signup:** `/api/otp/send`, `/api/otp/verify`, `/api/auth/email-otp`, `/api/account/connect-otp`
- **Billing:** `/api/billing/start-trial`, `/api/billing/upgrade`, `/api/billing/checkout`, `/api/billing/portal`, `/api/billing/apply-coupon`, `/api/billing/webhook`
- **Cloud read API:** `/api/cloud/nodes`, `/api/cloud/sessions`, `/api/cloud/events`, `/api/cloud/brain`, `/api/cloud/brain/stream`, `/api/cloud/system-snapshot`, `/api/cloud/transcripts`, `/api/cloud/account`
- **Approvals delivery:** Slack webhook, Resend email, PagerDuty routing key, Telegram bot, Twilio phone (fallback)
- **Cron job analytics across nodes**
- **Admin dashboard** at `/admin/thesecretpageforvivek` (auth-by-obscurity URL): revenue, MRR, churn, signup funnel, per-user diagnostics, DB introspection, slow-query view, synthetic event injection, bulk email send

### 4.6 OSS-only / default-on features

- **Zero-config workspace detection** — finds `~/.openclaw`, gateway port, sessions dir without any config file
- **Gateway WebSocket polling** — JSON-RPC over WS for cron CRUD, session metadata
- **OTLP receiver** — `/v1/metrics` and `/v1/traces` for ingesting from OpenClaw or remote OTLP-emitting agents
- **HTTP interceptor** — `clawmetry/interceptor.py` monkey-patches `httpx` and `requests` to log every LLM API call with cost; opt-in via `CLAWMETRY_INTERCEPT=1`
- **NeMo Guardrails integration** — policy YAML parsing + visual policy builder UI
- **Multi-node local fleet** — `/api/nodes/register` accepts remote OTLP-emitting nodes when `CLAWMETRY_FLEET_KEY` is set

### 4.7 Plan gates worth knowing

- `requirePro(feature)` JS helper at `dashboard.py:12381` shows the upsell modal when a user clicks a Pro feature on Free
- Server-side guard: `_validate_cm_token` returns plan, individual endpoints enforce
- Free users with linked accounts see **1 teaser alert** (Cloud `routes/alerts.py`) and an **empty Approvals queue** with an upsell CTA
- Trial-expired users have `sync_allowed=false`; daemon receives this in heartbeat response and pauses cloud uploads (events still write to local files)

---

## 5. Data model summary

### Local (on the user's machine)
- `~/.openclaw/agents/main/sessions/*.jsonl` — agent transcript files (read-only)
- `~/.openclaw/agents/main/sessions/sessions.json` — session index
- `~/.openclaw/memory/*.md` — agent memory files (read+write)
- `~/.openclaw/clawmetry.db` — SQLite, currently `anomalies` table only
- `~/.clawmetry/history.db` — optional 90-day time-series SQLite (only if history.py active)
- `~/.clawmetry/config.json` — `api_key`, `encryption_key`, `node_id`
- `~/.clawmetry/sync.log` — daemon log
- `~/.clawmetry/sync-state.json` — last_event_ids per file, backfill cursors

### Cloud storage policy (2026-05-20)
**Principle:** Cloud SQL holds *account / cloud-product data only*. Everything OpenClaw (events, logs, model names, sessions, snapshots, memory, crons) is **read from local files into the daemon's DuckDB, cached to Redis via heartbeat `cache_pushes`, and the UI reads only Redis** — so the UI indirectly reads from the local DuckDB. This keeps the cloud a lightweight cache, preserves E2E privacy (cloud holds ciphertext only), and lets new harnesses (OpenClaw, Hermes, Claude Code, Codex, …) plug in via daemon adapters with no cloud/UI hardcoding.

### Redis cache — the OpenClaw data layer (`routes/heartbeat_relay.py`)
Daemon `cache_pushes` (clawmetry/sync.py `_build_*_cache_pushes`) write encrypted blobs the browser decrypts with the per-account key:
- `brain:{owner_hash}:{node_id}:recent` — recent reasoning / tool events
- `memory:{owner_hash}:{node_id}:files` — memory files
- `snapshot:{owner_hash}:{node_id}:latest` — system snapshot (system rows, subagents, cronJobs, **diagnostics**, memoryFiles, toolStats, …)
- channel-config / alert-rules / approvals cache entries

`owner_hash = sha256(token)`; the browser `cm_token` equals the daemon api key, so ingest-side and read-side hashes match.

### Cloud SQL Postgres — account / cloud-product only (behind PgBouncer sidecar)
- `users` — email, api_key, api_key_hash, plan, stripe_customer_id, trial_end, status
- `nodes`, `node_registry`, `installs` — node registry + machine-id dedup + install tracking
- `notification_channels`, `approvals`, `approval_policies`, `approval_integrations`, `alerts`, `alert_history`, `budget_config` — cloud-mediated features (config + queues)
- `otp_store`, `connect_otps`, `push_tokens`, `trial_emails` — auth / lifecycle
- `analytics_events` — ClawMetry's *own* product analytics (admin page); not OpenClaw data
- `sessions` — **still present (76 MB), still active**: written by ingest, read by `alerts.py` / admin / `api_v1`. OpenClaw data → slated to move to the Redis/DuckDB path then deprecate. Not dropped (load-bearing today).

**Retired:**
- `events` (was **1.36 TB** — encrypted_events 1.14 TB, encrypted_logs 130 GB, cron_state 15.8 M rows, encrypted_memory, system_snapshot) — **DROPPED 2026-05-20**. It had been 100% write-only since epic #1032 removed every read; all of it now flows via Redis. `db_write` carries a guard that skips any `events` write. (cron + logs had no tables of their own — they were event_types *inside* `events`, so they went with it.)
- Dormant 0-row tables (`metrics`, `node_metrics`, `chat_messages`, `autonomy_snapshots`, `brain_blobs`, `alert_rules`, `*_pre_drift_fix`) — drop candidates after their remaining code refs are removed.

---

## 6. Integrations

| Integration | Purpose | Where |
|---|---|---|
| **Stripe** | subscriptions, customer portal, webhooks | Cloud only |
| **Resend** | transactional email (OTP, trial, churn) | Cloud only |
| **OpenClaw gateway** | WebSocket JSON-RPC for cron CRUD + session metadata | OSS daemon + dashboard |
| **OTLP** | Receive metrics + traces over HTTP | OSS dashboard |
| **NeMo Guardrails** | Policy YAML + sandbox detection | OSS + Cloud |
| **Claude Code (Claude CLI)** | Reads `~/.claude/projects/*/sessions/*.jsonl` | OSS daemon |
| **Hermes** | Reads `~/.hermes/state.db` (planned, partial) | OSS daemon |
| **Twilio** | Phone-call delivery for high-priority approvals (stub) | Cloud only |
| **PostHog** | Marked deprecated; in-house Postgres analytics replaced it | Cloud only (legacy refs) |

---

## 7. Roadmap (open work, in priority order)

### Cloud-storage migration: Cloud SQL → Redis/DuckDB (active, 2026-05-20)
Goal: Cloud SQL holds account/cloud-product data only; all OpenClaw data flows DuckDB → Redis → UI; harness-agnostic, no hardcoding.

**Done:** system snapshot → Redis (cloud #1010); Diagnostics rendered from snapshot (OSS 0.12.254 + cloud); `events` table writes stopped + **DROPPED** (1.36 TB reclaimed, cloud #1011); brain + memory already on Redis cache_push.

**Next (each = OSS daemon cache_push + cloud serve-from-Redis + UI):**
1. **Logs** — daemon pushes recent logs (from DuckDB) to `logs:{owner}:{node}:recent`; cloud serves from Redis; replace the "Full logs are not available in cloud view" dead-end. (logs were never their own table — they were `encrypted_logs` rows in the dropped `events`.)
2. **Models** — model-mix per session from DuckDB → Redis (works locally, empty in cloud today).
3. **Transcript + Replay** — per-session transcript → `transcript:{owner}:{node}:{session}` → client decrypt (fixes Embodied "No messages" + replay scrubber).
4. **Deprecate dead Postgres** — remove the write code + DROP the dormant 0-row tables (`metrics`, `node_metrics`, `chat_messages`, `autonomy_snapshots`, `brain_blobs`, `alert_rules`, `*_pre_drift_fix`) and the `cron_state` / `encrypted_logs` ingest paths. Keep `analytics_events` (ClawMetry product analytics).
5. **`sessions` table** — migrate its readers (`alerts.py`, admin, `api_v1`) to the Redis/DuckDB path, then drop.

### Other open work
The active roadmap lives under the `roadmap-now` GitHub label. Top items:

- **#964 [EPIC] Local-first telemetry** — the cluster (#957–#963) that flips storage onto the node, with cloud as hot-cache + relay. Cost-driven; reduces cloud `events` table by 10–50× per user.
- **#27 [P0] Daemon device-pairing** — replace shared gateway token with per-device pairing
- **#21 [P1] Visualization set** — six umbrella issues (#316–#321) for Brain/Flow upgrades
- **#79 E2E test for policy-from-UI → daemon enforcement**
- **#108 Real-HTTP integration tests for Slack / PagerDuty / Telegram / Phone**
- **#110 Admin activity digest emails (counter-proposal in flight)**
- **#122 Slow-query top-10 from pg_stat_statements** (now actually possible — extension was enabled today)
- **#131 Supervisord exit-on-PgBouncer-fail hardening**
- **#142 Synthetic deploy-gate regression test**

Items above are all open in the OSS repo at `vivekchand/clawmetry`. Cloud-side roadmap items live in `vivekchand/clawmetry-cloud`.

---

## 8. Hard constraints (the things any refactor must preserve)

1. **Zero config remains true** — `pip install && clawmetry` must keep working with no flags, no editing.
2. **Read-only by default** — ClawMetry observes; the only mutation surfaces are cron CRUD (gateway-mediated) and memory-file editing (explicit user action).
3. **E2E encryption stays in place** — for any data leaving the device, AES-256-GCM with the user's per-account key. Cloud stores ciphertext, browser decrypts.
4. **No external account required for OSS** — the dashboard, sync daemon (cloud-disabled), and gateway integration must all work offline.
5. **Plan gates are the only differentiator** — same dashboard binary serves OSS-local, Cloud-Free, and Cloud-Pro; Pro features hide behind `requirePro()` not separate builds.
6. **Daemon survives transient cloud failures** — heartbeat retries with backoff; trial expiration pauses, never crashes; cold-start `429`s and `5xx`s are retried (PRs #135, #928).
7. **Channel adapters are pluggable** — adding a new channel must require only a new entry in `routes/channels.py`, no schema changes.
8. **Multi-node fleet must scale linearly** — adding the 4th node to a user's account must not require re-architecting (the local-first refactor preserves this via fan-out).

---

## 9. Glossary

- **Node** — one machine running the OSS daemon. Identified by `node_id` (e.g. `agent+Macbook-Pro-local`).
- **Session** — one continuous agent conversation, identified by a UUID; backed by a `.jsonl` file on disk.
- **Owner** — the user who owns a set of nodes; keyed by `owner_hash = SHA-256(api_key)`.
- **Sandbox** (NemoClaw) — an isolated OpenClaw runtime; each registers as a separate node.
- **Hot data / cold data** — recent (last 24 h after #959) vs older. Local-first puts cold on the node.
- **Brain event** — any item that appears in the Brain tab stream: a tool call, a user/assistant message, a cron run, a memory write, a log line.
- **Cloud Mode** — when the OSS dashboard binary is run with `CLOUD_MODE=1` env, it serves the Cloud variant (`app.clawmetry.com` is this).

---

This PRD is the **shared mental model**, not a spec. When in doubt about a feature's behaviour, the source of truth is the code. When the code disagrees with this document, update this document.
