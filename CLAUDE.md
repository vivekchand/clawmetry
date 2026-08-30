# CLAUDE.md — ClawMetry

> **Read [`FLYWHEEL.md`](./FLYWHEEL.md) first.** It is how you ship a change end to end here (code → PR → green CI → `[RELEASE]` → PyPI → cloud → verified live) and the non-negotiable "done" bar. This file is the architecture reference; FLYWHEEL.md is the shipping loop.

## What is this?
ClawMetry is an open-source, real-time observability dashboard for [OpenClaw](https://github.com/openclaw/openclaw) AI agents. `pip install clawmetry && clawmetry` — that's it. Zero config, observation by default.

## Architecture
See `ARCHITECTURE.md` for the full deep dive. TL;DR:
- **Flask app** with embedded HTML/CSS/JS frontend (no build step, no npm)
- **Per-feature route modules** under `routes/` — `routes/sessions.py`, `routes/usage.py`, etc. — each owns one Blueprint and the endpoints registered on it. New endpoints land in their feature's module so parallel PRs don't stomp on each other.
- **Shared helpers** stay in `dashboard.py` for now and are accessed from route modules via late `import dashboard as _d`. (Helpers will migrate to `helpers/` over time.)
- **Zero config** — auto-detects OpenClaw workspace, gateway, sessions, logs
- **Observation by default, control when asked** — see "Control plane" below. Reads never require permission; writes are always user-initiated or policy-declared
- **DuckDB-first** — the sync daemon ingests filesystem/gateway/OTLP into a local **DuckDB** store (`clawmetry/local_store.py`; the daemon owns the writer lock). Request handlers read from DuckDB via `routes/local_query.py`, **not** raw files — reading raw JSONL/logs inside a handler works locally but returns empty in cloud (the container has no `~/.openclaw`). Optional `history.py` adds a separate SQLite time-series.
- **Three ingest sources** (all land in DuckDB): filesystem (JSONL/logs), gateway WebSocket (JSON-RPC), optional OTLP receiver

## Key Files

### Core
| File | Lines | Purpose |
|------|-------|---------|
| `dashboard.py` | ~17,300 | Flask app, blueprint registration, shared helpers (live frontend now lives in `static/` + `templates/`) |
| `history.py` | ~555 | Optional time-series collector (SQLite, polls gateway every 60s) |

### Route modules (`routes/`)
All HTTP endpoints live here, organised by feature. Each module owns one or more Flask Blueprints; handlers do late `import dashboard as _d` to reach shared helpers still in `dashboard.py`.

| File | Lines | Blueprints / Purpose |
|------|-------|----------------------|
| `routes/sessions.py` | ~7,300 | `bp_sessions` — sessions list, transcripts, compactions, tool timeline, cost split, subagents, exports |
| `routes/channels.py` | ~2,800 | `bp_channels` — 21 chat-channel adapters (Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, WebChat, …) |
| `routes/components.py` | ~2,100 | `bp_components` — Flow-panel detail endpoints (tool / runtime / machine / gateway / brain) |
| `routes/usage.py` | ~4,500 | `bp_usage` — token/cost analytics, anomaly detection, model + skill attribution |
| `routes/health.py` | ~3,500 | `bp_health` — system-health, reliability, diagnostics, rate-limits, sandbox-status, health-stream (SSE) |
| `routes/brain.py` | ~1,900 | `bp_brain` — `/api/brain-history` + `/api/brain-stream` (SSE) |
| `routes/local_query.py` | ~850 | `bp_local_query` — `/api/local/*` DuckDB read API + the daemon-proxy `_dispatch` (shape→store bridge shared by HTTP and the cloud relay) |
| `routes/infra.py` | ~2,400 | `bp_logs` + `bp_memory` + `bp_security` + `bp_config` — logs stream, memory files, security posture, cost-optimizer |
| `routes/overview.py` | ~1,900 | `bp_overview` — main dashboard endpoint, channels list, timeline, cloud-CTA OTP |
| `routes/crons.py` | ~1,500 | `bp_crons` — cron CRUD + run log + health summary |
| `routes/meta.py` | ~1,600 | `bp_auth` + `bp_gateway` + `bp_otel` + `bp_version` + `bp_version_impact` + `bp_cloud_relay` + `bp_otlp_traces` — auth, gateway proxy, OTLP ingestion, version meta |
| `routes/alerts.py` | ~980 | `bp_alerts` + `bp_budget` — alert rules, webhooks, velocity, budget config |
| `routes/fleet_history.py` | ~240 | `bp_fleet` + `bp_history` — multi-node fleet + SQLite time-series |
| `routes/nemoclaw.py` | ~125 | `bp_nemoclaw` — NeMo Guardrails governance + approval queue |
| `routes/runtime_ingest.py` | ~87 | `bp_runtime_ingest` — custom runtime HTTP ingest API (`/api/v1/runtimes`, `/api/v1/runs/*`; Pro feature) |
| `routes/__init__.py` | — | Package marker |

### Package (`clawmetry/`)
| File | Lines | Purpose |
|------|-------|---------|
| `clawmetry/cli.py` | ~6,100 | CLI entry point — `clawmetry`, `clawmetry connect`, `clawmetry sync`, `clawmetry status` |
| `clawmetry/sync.py` | ~20,200 | Cloud sync daemon — ingests into DuckDB, owns the writer lock, E2E-encrypted (AES-256-GCM) snapshot streaming to `ingest.clawmetry.com` |
| `clawmetry/local_store.py` | ~12,000 | **DuckDB store** — the single data layer features read/write (daemon holds the writer lock) |
| `clawmetry/local_server.py` | ~200 | Daemon-hosted localhost query server (`/__local_query__/<method>`) so the dashboard/sync read DuckDB without grabbing the writer lock |
| `clawmetry/proxy.py` | ~2,700 | Enforcement proxy — budget limits, loop detection, model routing (port 4100) |
| `clawmetry/detectors.py` | ~870 | Event normalization, the four **trajectory** detectors (is it stuck?), the registry, `run_all` and `session_profile`. Keeps its original shape; the new capability lives in the four modules below and is re-exported here, so `clawmetry.detectors` stays the single import |
| `clawmetry/detector_surface.py` | ~290 | What a tool call touched (paths, command, hosts, heredoc bodies stripped) and what a finding may repeat back. Every function here is new in this change |
| `clawmetry/detector_behaviour.py` | ~470 | The four **behavioural** detectors (is it doing something it does not normally do?): `file_blast_radius`, `credential_access`, `network_egress`, `privilege_change`, with their pattern tables |
| `clawmetry/detector_calibration.py` | ~280 | Where a threshold comes from: module defaults → `RUNTIME_PROFILES` → the cohort's learned baseline → a per-runtime env override. `resolve_thresholds` reports which layer set each value |
| `clawmetry/detector_money.py` | ~130 | `spend_at_risk_usd` and the ranking. Only a measured basis may promote a warning to `critical` |
| `clawmetry/git_outcomes.py` | ~660 | **Read-only** Git reader (REQ-OBS-CEA-022) — commits, merge state by default-branch reachability, pull-request state via `gh` when present, line survival for rework, and session↔commit correlation with a recorded confidence. Every subprocess passes one chokepoint that rejects anything outside an allowlist of read-only plumbing subcommands |
| `clawmetry/interceptor.py` | ~630 | Zero-config HTTP monkey-patching for LLM cost tracking (patches httpx/requests) |
| `clawmetry/providers_pricing.py` | ~430 | Multi-provider pricing table (Anthropic, OpenAI, Google, OpenRouter, etc.) |
| `clawmetry/config.py` | ~200 | Configuration dataclass |
| `clawmetry/extensions.py` | ~300 | Plugin/hook system |
| `clawmetry/track.py` | ~60 | Zero-config interceptor shorthand |
| `clawmetry/providers/` | — | Pluggable data provider layer (LocalDataProvider, TursoDataProvider) |

### Config & Build
| File | Purpose |
|------|---------|
| `setup.py` | PyPI package definition (entry point: `clawmetry` CLI) |
| `requirements.txt` | pip dependencies |
| `Dockerfile` | Docker image (Python 3.11-slim base) |
| `Makefile` | Dev commands: `make dev`, `make test`, `make lint` |
| `install.sh` | One-liner installer script |

### Documentation
| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Detailed architecture guide with diagrams |
| `CHANGELOG.md` | Version history (~11,600 lines) |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security posture |
| `CLOUD_EXTENSION_DESIGN.md` | Cloud feature design |
| `docs/ENTITLEMENTS.md` | Open-core split: FREE runtimes/features, paid tiers, GRACE mode, `/api/entitlement` shape, `clawmetry license` CLI |

## How it works
The **sync daemon** (`clawmetry/sync.py`) ingests these sources into the local **DuckDB** store; the Flask app reads DuckDB (via `routes/local_query.py`) to serve the UI:
1. Session transcripts from `~/.openclaw/agents/main/sessions/*.jsonl`
2. Chat-channel transcripts from `~/.openclaw/<channel>/*.jsonl` —
   one directory per adapter (`telegram/`, `signal/`, `whatsapp/`,
   `discord/`, `slack/`, `irc/`, `imessage/`, `webchat/`, …). The 21
   adapter directories match the routes in `routes/channels.py`. New
   adapter? Add its dir name to `_CHANNEL_DIRS` in `clawmetry/sync.py`.
3. OpenClaw gateway via WebSocket (JSON-RPC, port 18789) for live data
4. Optional OpenTelemetry metrics/traces/logs on `/v1/metrics`, `/v1/traces`, and `/v1/logs`

The daemon owns the DuckDB writer lock and runs a localhost query server so the dashboard reads through it. The dashboard serves the UI at `http://localhost:8900`; for cloud, the daemon also pushes an E2E-encrypted snapshot to `ingest.clawmetry.com` (decrypted client-side in the browser).

## API Endpoints (key ones)
- `/api/overview` — Main dashboard data (sessions, tokens, crons, health)
- `/api/sessions` — Active session list
- `/api/subagents` — Sub-agent tracker with status and costs
- `/api/transcript/<id>` — Full session transcript
- `/api/usage` — Token and cost analytics
- `/api/usage/outcomes` — Cost per merged change, rework rate, abandoned-session spend (REQ-OBS-CEA-022). Every figure carries its basis; one that cannot be derived is `available: false` with a reason, never a fabricated zero, and the coverage block says how many sessions could not be attributed
- `/api/flow` — Message flow visualization (channels -> gateway -> models -> tools)
- `/api/brain-history` — Recent reasoning/tool events (paginated)
- `/api/brain-stream` — Live event stream (SSE)
- `/api/crons` — Cron job management (full CRUD via gateway RPC)
- `/api/system-health` — Disk, memory, uptime, GPU
- `/api/nodes` — Multi-node fleet view
- `/api/budget/*` — Budget monitoring and alerts
- `/api/alerts/*` — Custom alert rules

## Dependencies
Minimal by design, and this list had drifted — `setup.py` is the source of truth:
- **flask** (>=2.0,<4) — HTTP server framework
- **waitress** (>=2.0) — WSGI application server
- **cryptography** (>=50.0.0 on 3.9.2+; >=3.0 on 3.8/3.9.0/3.9.1, which have no advisory-clean release) — AES-256-GCM for cloud sync
- **duckdb** (>=0.10) — the local store at `~/.clawmetry/clawmetry.duckdb`
- **websocket-client** (>=1.6) — cloud cold-data relay tunnel
- **truststore** (>=0.8, 3.10+ only) — OS trust store, so corporate TLS-interception root CAs work
- **certifi** (>=2024.2.2) — CA bundle; the trust-store fallback on 3.8/3.9 and on any interpreter whose OpenSSL has no CA store. Without one, every outbound HTTPS call fails `CERTIFICATE_VERIFY_FAILED`, and for the fire-and-forget pings that failure is silent
- **Optional**: `opentelemetry-proto` for OTLP support (`pip install clawmetry[otel]`)

## Running locally
```bash
# From source (dev mode)
make dev
# Or manually:
pip install flask waitress cryptography
python3 dashboard.py --port 8900

# As installed package
pip install clawmetry
clawmetry --port 8900 --workspace ~/your-openclaw-workspace
```

## Testing
```bash
# Full test suite (needs running server)
make test

# API tests only
make test-api

# E2E browser tests (Playwright)
make test-e2e

# Syntax + lint check
make lint
```

Tests use `CLAWMETRY_URL` and `CLAWMETRY_TOKEN` env vars. Test matrix in CI: 3 OS (Ubuntu, macOS, Windows) x 2 Python versions (3.9, 3.11).

## Deploy
- **PyPI**: `pip install clawmetry && clawmetry`
- **Docker**: `docker build -t clawmetry . && docker run -p 8900:8900 -v ~/.openclaw:/root/.openclaw:ro clawmetry`
- **Current version**: `0.12.650` (in `dashboard.py` `__version__`)

## CI/CD (GitHub Actions)
- `.github/workflows/ci.yml` — Lint + test matrix on push/PR
- `.github/workflows/publish.yml` — PyPI publish on git tag `v*`
- `.github/workflows/release-on-merge.yml` — Auto-release when version bumped on main
- `.github/workflows/sync-test.yml` — Cloud sync daemon tests
- `.github/workflows/install-test.yml` — Cross-platform pip install smoke tests
- `.github/workflows/auto-deploy-cloud.yml` — Cloud deployment
- `.github/workflows/browserstack.yml` — Cross-browser E2E testing

## Environment Variables
```bash
OPENCLAW_HOME=~/.openclaw              # OpenClaw workspace (auto-detected)
OPENCLAW_GATEWAY_TOKEN=token           # Gateway auth token
CLAWMETRY_PROVIDER=local|turso         # Data backend (default: local)
CLAWMETRY_INTERCEPT=1                  # Enable HTTP interceptor
CLAWMETRY_FLEET_KEY=...               # Multi-node fleet auth key
CLAWMETRY_FAMILY_SESSION_LIMIT=50      # Max sessions/runtime to ingest for Claude Code/Codex/Cursor/… (most-recent N; raise for deeper history)
CLAWMETRY_UPDATE_CHECK_SECS=60         # Daemon PyPI update-check cadence (default 60s; fleet tracks the latest release within minutes)
CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS=0   # Stability window before a silent install (default 0 = absolute latest; raise to be conservative)
CLAWMETRY_AUTO_UPDATE=0                # Hard kill switch for unattended upgrades
CLAWMETRY_HOOK_TIMEOUT_MAX_S=28800     # Ceiling on an INSTALLED hook timeout (8h; 0 = unbounded). Bounds how long a runtime waits on a wedged gate — docs/HOOK_COEXISTENCE.md
CLAWMETRY_GIT_OUTCOMES=0               # Turn OFF repository reading entirely (default on)
CLAWMETRY_GIT_SCAN_INTERVAL=900        # Seconds between repo scans (merges are not tool calls)
CLAWMETRY_GIT_MAX_REPOS=5              # Repos per tick, least-recently-scanned first
CLAWMETRY_GIT_LOOKBACK_DAYS=90         # Furthest back a scan may read history
CLAWMETRY_GIT_MAX_COMMITS=500          # Commit ceiling per scan (keeps the NEWEST; truncation is reported)
CLAWMETRY_GIT_MAX_BLAME_FILES=40       # Files blamed for line survival (rework), most-changed first
CLAWMETRY_GIT_BLAME_BUDGET=10          # Seconds the whole blame pass may take
CLAWMETRY_GIT_REPO_BUDGET=25           # Seconds one repository's whole scan may take
DEBUG=1                                # Enable debug logging
```

## Conventions
- **Product record before code (FLYWHEEL.md section 0c).** 8090 Software Factory is the product reviewer, not a lint gate. Write the requirement first -- problem, who is hurt, non-goals, alternatives rejected, risk accepted -- then the blueprint, then the code. A requirement written after the fact reviews nothing, and `scripts/check_product_record.py` gates PRs on citing one (or an explicit `No-PRD: <reason>`).
- **Per-feature route modules** — new endpoints live in `routes/<feature>.py`, registered on a feature Blueprint that `dashboard.py` imports and registers. This replaces the old "single file" rule, which became counterproductive at ~33K lines (illegible to humans, constant PR conflicts on a single anchor point). Helpers and shared state stay in `dashboard.py` for now and are accessed from route modules via late `import dashboard as _d` to avoid circular imports.
- **Embedded frontend, no build step** — the live UI is served from `clawmetry/static/` (`clawmetry/static/css/dashboard.css`, `clawmetry/static/js/app.js`) + `clawmetry/templates/tabs/*.html`. (`dashboard.py` defines `DASHBOARD_HTML` twice; the **second** wins and loads the static/template files — the earlier inline `<style>`/HTML is dead, so edit the static/template files.) No npm, no webpack.
- **Minimal dependencies** — Flask + waitress + cryptography. Don't add heavy libraries.
- **Control plane that defaults to observation** — ClawMetry is NOT read-only, and hasn't been for a long time. It already kills, pauses, blocks and reroutes running agents through five surfaces: approval denial → session kill (`clawmetry/approvals.py`), POSIX signals across the agent's descendant tree (`clawmetry/process_control.py`), HITL pause → proxy `503` (`routes/hitl.py`), the enforcement proxy's budget block / loop detection / model routing (`clawmetry/proxy.py`), and cron CRUD via gateway RPC (`routes/crons.py`). Do NOT reject a feature because "we're read-only" — that rule is retired.
  The rule that replaces it is **no surprise writes**: every write is (a) user-initiated or declared in a policy the user wrote, (b) scoped to a single session, (c) reversible where physics allows, and (d) attributed in the approvals audit table. Reads need no permission; writes need all four.
  **Fail open on entitlement, closed on policy.** If a licence/entitlement lookup errors or is ambiguous, the agent KEEPS RUNNING — only a policy the user actually declared may block or kill. A billing bug must never stop a customer's agent. (`clawmetry/entitlements.py` already defaults to GRACE, where every `allows_*` returns `True`; new control features inherit that posture and assert it in a test.)
- **Acceptance criteria are traceable to tests** — every criterion in `docs/acceptance_criteria.json` (mirrored from 8090 Software Factory) must be declared by at least one test under `tests/`. CI enforces it as a one-way ratchet; see FLYWHEEL.md §1g. Drift Bot catches "this diff contradicts a Blueprint"; this catches "untouched code stopped satisfying a criterion", which is the class that produced `$0.00` cost windows and ghost sessions. `make ac-report` to see where you stand.
- **Never delete a hook you did not write** — `~/.claude/settings.json` has other writers (GitLens's `gk ai hook install claude-code --force`, `numbat`, the user) and ClawMetry itself writes it from three places. Every removal path goes through `clawmetry/hook_ownership.py` at **hook** granularity, never entry granularity: a foreign writer may have merged its command into the same entry as ours, and the daemon gate's reinstall runs every ~2s, so an entry-level drop deletes someone else's hook within seconds. Installed hook timeouts are clamped (`CLAWMETRY_HOOK_TIMEOUT_MAX_S`, default 8h) — on Copilot, whose `preToolUse` gate is fail-closed, an unbounded wait on a wedged hook is a denial of service against the user's own agent. `docs/HOOK_COEXISTENCE.md`; harness `scripts/hook_collision_matrix.py`.
- **A user's repository is read, never written** — `clawmetry/git_outcomes.py` is the only place ClawMetry runs `git` against a directory the operator chose, and it routes every invocation through one chokepoint that rejects anything outside an allowlist of read-only plumbing subcommands (`log`, `rev-list`, `blame`, `cat-file`, `rev-parse`, `for-each-ref`, `show-ref`, `ls-files`, plus `config --get` and `remote get-url`). A `fetch` added "just to freshen state" raises `UnsafeGitCommand` rather than shipping. Add a new git call by adding it to that allowlist, with a test, or not at all.
- **Auto-detect everything** — users should never need to configure anything manually.
- **Never crash on bad input** — graceful fallbacks for missing data, log warnings but continue.
- **Never starve the heartbeat** — the cloud relay drains and answers `pending_queries` (Brain time-window fetches, transcript reads, approvals) only when the daemon heart-beats, and the heartbeat fires at the end of a main-loop iteration. Any ingest pass that can run long (deep `runtime_backfill`, first-run ingest of hundreds of sessions) must call `_ingest_keepalive_heartbeat(config)` between items, or every hosted relay read sits on `relay_pending` until the browser gives up (2026-07-30 Brain-window RCA: a 465-session backfill blocked heartbeats for ~2m40s).
- **Detector thresholds are resolved, not hard-coded** — `detectors.resolve_thresholds(runtime, baseline)` layers four sources, each overriding the last: module defaults → the runtime profile (write-tool vocabulary, a checkable fact about the adapter, never an invented number) → the cohort's learned baseline from `guard_session_stats` / `guard_egress_hosts` → a per-runtime env override (`CLAWMETRY_NOPROG_TOOLS__CODEX=40`). Every incident carries `threshold_source`, so a reader can tell a measured threshold from a shipped constant. Learned values are clamped to a band around the static default: a cohort where everything loops cannot teach the detectors to go blind, and a cohort of three sessions cannot make them scream.
- **Incident severity maps to money** — detectors attach `spend_at_risk_usd` (the estimated cost of the *flagged stretch*, not the session bill) plus the `spend_basis` that produced it, and a `warning` crossing `CLAWMETRY_GUARD_CRITICAL_USD` becomes `critical`. Where no cost is known the field is `0.0` with basis `unknown`, never a fabricated figure. Surfaces that list incidents (`/api/loop-signals`) rank by it.
- **snake_case** functions, **PascalCase** classes, **SCREAMING_SNAKE_CASE** constants.
