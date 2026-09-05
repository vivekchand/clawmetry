# CLAUDE.md — ClawMetry

> **Read [`FLYWHEEL.md`](./FLYWHEEL.md) first.** It is how you ship a change end to end here (code → PR → green CI → `[RELEASE]` → PyPI → cloud → verified live) and the non-negotiable "done" bar. This file is the architecture reference; FLYWHEEL.md is the shipping loop.

## What is this?
ClawMetry is an open-source, real-time observability and governance layer for **30 AI agent runtimes** — [OpenClaw](https://github.com/openclaw/openclaw), NVIDIA NemoClaw and Goose free in OSS, the other 27 (Claude Code, Codex, Cursor, Copilot, Gemini CLI, Hermes, Aider, opencode, ...) with the optional Pro plugin. `pip install clawmetry && clawmetry` — that's it. Zero config, observation by default.

**Never hardcode the runtime count or the runtime list anywhere new.** The authoritative sources are `entitlements.FREE_RUNTIMES | entitlements.PAID_RUNTIMES` (the catalogue, and what every quoted number is derived from) and `sync._FAMILY_ADAPTER_SPECS` (what the daemon actually loads — a `clawmetry-pro` adapter is inert until it is named there). `scripts/sync_runtime_count.py` rewrites the number in prose and CI fails on drift; the same script checks the chat-channel count against `entitlements.ALL_CHANNELS`.

## Architecture
See `ARCHITECTURE.md` for the full deep dive, and `docs/MODULE_MAP.md` (generated) for every module and blueprint. TL;DR:
- **Flask app** with embedded HTML/CSS/JS frontend (no build step, no npm)
- **Per-feature route modules** under `routes/` — `routes/sessions.py`, `routes/usage.py`, etc. — each owns one or more Blueprints and the endpoints registered on them. New endpoints land in their feature's module so parallel PRs don't stomp on each other.
- **Shared helpers** are migrating out of `dashboard.py` into `helpers/`; route modules reach the ones still in `dashboard.py` via late `import dashboard as _d`.
- **Zero config** — auto-detects runtimes, OpenClaw workspace, gateway, sessions, logs
- **Observation by default, control when asked** — see "Control plane" below. Reads never require permission; writes are always user-initiated or policy-declared
- **DuckDB-first** — the sync daemon ingests filesystem/gateway/OTLP into a local **DuckDB** store (`clawmetry/local_store.py`; the daemon owns the writer lock). Request handlers read from DuckDB via `routes/local_query.py`, **not** raw files — reading raw JSONL/logs inside a handler works locally but returns empty in cloud (the container has no `~/.openclaw`). Optional `history.py` adds a separate SQLite time-series.
- **Five ingest paths** (all land in DuckDB): filesystem (JSONL/logs), gateway WebSocket (JSON-RPC), optional OTLP receiver (`/v1/metrics`, `/v1/traces`, `/v1/logs`), runtime hooks (`clawmetry hook <runtime>`, the only pre-tool path), and the HTTP ingest API (`/api/v1/runs/*`) for a runtime with no adapter

## Key Files

`docs/MODULE_MAP.md` is the **generated** inventory: every module, the blueprints it defines, the URL space it owns, and a coarse size band. `scripts/gen_module_map.py` regenerates it and CI fails when it drifts. The tables below are a short curated index of what you reach for most often, deliberately without line counts (they went stale within weeks every time they were written down).

**Five files are big enough to change how you work on them**: `routes/entitlement.py` (~48k lines), `clawmetry/entitlements.py` (~31k), `clawmetry/sync.py` (~26k), `dashboard.py` (~21k), `clawmetry/local_store.py` (~20k). Drift Bot reads only the head of a long file, so anything added deep inside one is reported as "not implemented" forever. Put new capability in a new short module and re-export it, rather than appending 300 lines to a 20k-line file.

### Core
| File | Purpose |
|------|---------|
| `dashboard.py` | Flask app, blueprint registration, `before_request` auth, the shared helpers that have not moved yet (the live frontend lives in `clawmetry/static/` + `clawmetry/templates/`) |
| `helpers/gateway.py` | OpenClaw gateway WebSocket RPC + HTTP invoke client |
| `helpers/logs.py` | Log directory discovery, tail and grep |
| `helpers/openapi.py` | `bp_openapi` — the OpenAPI 3.1 spec generated from the Flask URL map, served at `/openapi.json` and `/api/docs` |
| `history.py` | Optional time-series collector (SQLite, polls gateway every 60s) |

### Route modules (`routes/`)
All HTTP endpoints live here, organised by feature: 70 modules, 82 blueprints, listed in full in `docs/MODULE_MAP.md`. Handlers do late `import dashboard as _d` to reach shared helpers still in `dashboard.py`.

| File | Blueprints / Purpose |
|------|----------------------|
| `routes/sessions.py` | `bp_sessions` — sessions list, transcripts, compactions, tool timeline, cost split, subagents, exports |
| `routes/usage.py` | `bp_usage` — token/cost analytics, anomaly detection, model + skill attribution, `/api/usage/outcomes` |
| `routes/health.py` | `bp_health` — system-health, reliability, diagnostics, rate-limits, sandbox-status, health-stream (SSE) |
| `routes/overview.py` | `bp_overview` — main dashboard endpoint, channels list, timeline, cloud-CTA OTP |
| `routes/brain.py` | `bp_brain` — `/api/brain-history` + `/api/brain-stream` (SSE) |
| `routes/channels.py` | `bp_channels` — 24 chat-channel adapters (Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, WebChat, …) |
| `routes/components.py` | `bp_components` — Flow-panel detail endpoints (tool / runtime / machine / gateway / brain) |
| `routes/local_query.py` | `bp_local_query` — `/api/local/*` DuckDB read API + the daemon-proxy `_dispatch` (shape→store bridge shared by HTTP and the cloud relay) |
| `routes/guard.py` | `bp_guard` — live session control (Pause/Stop/Kill), Guard policy CRUD, policy decision log, learned baselines. Sessions ranked by **spend at risk**, not severity |
| `routes/policy.py` | `bp_policy` — the *pre-tool* sandbox/permission surface (`/api/tool-policy`). Deliberately a different axis from `routes/guard.py`: different table, no shared state |
| `routes/hooks.py` | `bp_hooks` — hook install / status / uninstall per runtime, and the gate's decision log |
| `routes/infra.py` | `bp_logs` + `bp_memory` + `bp_security` + `bp_config` — logs stream, memory files, security posture, cost-optimizer |
| `routes/meta.py` | `bp_auth` + `bp_gateway` + `bp_otel` + `bp_version` + `bp_version_impact` + `bp_cloud_relay` + `bp_otlp_traces` — auth, gateway proxy, OTLP ingestion, version meta |
| `routes/entitlement.py` | `bp_entitlement` — the resolved entitlement plus the preview / diff / batch family at `/api/entitlement*` |
| `routes/alerts.py` | `bp_alerts` + `bp_budget` — alert rules, webhooks, velocity, budget config |
| `routes/crons.py` | `bp_crons` — cron CRUD + run log + health summary |
| `routes/signals.py` | `bp_signals` — Behaviour Signals read API: `/api/signals` (rate, count, eligible turns, trend, by model and runtime, coverage, plain-words headline), `/api/signals/<name>/sessions` (sessions, never phrases) |
| `routes/tracing.py` | `bp_tracing` — spans and the trace view |
| `routes/trail.py` | `bp_trail` — `/api/trail/coverage`: per runtime, which trail streams it can actually expose |
| `routes/fleet_history.py` | `bp_fleet` + `bp_history` — multi-node fleet + SQLite time-series |
| `routes/nemoclaw.py` | `bp_nemoclaw` — NeMo Guardrails governance + approval queue |
| `routes/runtime_ingest.py` | `bp_runtime_ingest` — custom runtime HTTP ingest API (`/api/v1/runs/*`; Pro feature) |
| `routes/__init__.py` | Package marker plus the `@event_data` / `@source_exempt` route markers the source canary reads |

### Package (`clawmetry/`)
130 modules, listed in full in `docs/MODULE_MAP.md`.

| File | Purpose |
|------|---------|
| `clawmetry/cli.py` | CLI entry point — `clawmetry`, `connect`, `sync`, `status`, `license`, `hook`, `update` |
| `clawmetry/sync.py` | Cloud sync daemon — ingests into DuckDB, owns the writer lock, runs the detectors and Guard policies, streams the E2E-encrypted (AES-256-GCM) snapshot to `ingest.clawmetry.com`. Holds `_FAMILY_ADAPTER_SPECS` (the adapters that actually load) and `_CHANNEL_DIRS` |
| `clawmetry/local_store.py` | **DuckDB store** — the single data layer features read and write (the daemon holds the writer lock). Schema v15 |
| `clawmetry/local_server.py` | Daemon-hosted localhost query server (`/local/query`, discovered through `~/.clawmetry/local_query.json`) so the dashboard reads DuckDB without grabbing the writer lock |
| `clawmetry/query_contract.py` | The declared node query surface (`q/1`), rendered to `docs/QUERY_CONTRACT.md`. Additive-only inside a version |
| `clawmetry/entitlements.py` | Single source of truth for tiers, `FREE_RUNTIMES` / `PAID_RUNTIMES`, `ALL_CHANNELS` and every capacity limit. GRACE by default |
| `clawmetry/license.py` | Offline Ed25519 verification of self-hosted license keys |
| `clawmetry/proxy.py` | Enforcement proxy — budget limits, loop detection, model routing (port 4100) |
| `clawmetry/detectors.py` | Event normalization, the four **trajectory** detectors (is it stuck?), the registry, `run_all` and `session_profile`. Re-exports the modules below, so `clawmetry.detectors` stays the single import |
| `clawmetry/detector_behaviour.py` | The four **behavioural** detectors (is it doing something it does not normally do?): `file_blast_radius`, `credential_access`, `network_egress`, `privilege_change`, with their pattern tables |
| `clawmetry/detector_surface.py` | What a tool call touched (paths, command, hosts, heredoc bodies stripped) and what a finding may repeat back |
| `clawmetry/detector_calibration.py` | Where a threshold comes from: module defaults → `RUNTIME_PROFILES` → the cohort's learned baseline → a per-runtime env override. `resolve_thresholds` reports which layer set each value |
| `clawmetry/detector_money.py` | `spend_at_risk_usd` and the ranking. Only a measured basis may promote a warning to `critical` |
| `clawmetry/policy_engine.py` | **Pure** Guard policy evaluator — detector incident + policies → at most one enforcement decision per session, including the escalation ladder |
| `clawmetry/guard_actuator.py` | The one place a decision becomes a signal. Both the manual and the automatic path go through it |
| `clawmetry/process_control.py` | Signal actuators — pause (SIGSTOP / `NtSuspendProcess`), stop (SIGINT / a console Ctrl+C), kill (SIGTERM→SIGKILL tree / `taskkill /T`), pid-reuse guarded. Owns `runtime_control_support()` |
| `clawmetry/resume_hints.py` | A verified resume command per runtime, with its native session id. Coverage is CI-enforced |
| `clawmetry/approvals.py` | Approval queue and audit table; an approval denial can end a session |
| `clawmetry/hook_ownership.py` | Hook install and removal at **hook** granularity, so ClawMetry never deletes a hook it did not write |
| `clawmetry/behaviour_signals.py` | Six preset judge-free signals over every transcript in the store, persisted to `signal_turns` / `signal_matches` (never the matched text) |
| `clawmetry/git_outcomes.py` | **Read-only** Git reader — commits, merge state, pull-request state via `gh`, line survival, session↔commit correlation. Every subprocess passes one allowlist chokepoint |
| `clawmetry/interceptor.py` | Zero-config HTTP monkey-patching for LLM cost tracking (patches httpx/requests) |
| `clawmetry/providers_pricing.py` | Multi-provider pricing table (Anthropic, OpenAI, Google, OpenRouter, etc.) |
| `clawmetry/runtime_probe.py` | Which runtimes are actually installed on this machine |
| `clawmetry/config.py` | Configuration dataclass |
| `clawmetry/extensions.py` | Plugin/hook system — the `clawmetry.extensions` entry point `clawmetry-pro` registers through |
| `clawmetry/track.py` | Zero-config interceptor shorthand |
| `clawmetry/adapters/` | The FREE runtime adapters (OpenClaw, NemoClaw, Goose) plus the adapter base SDK the paid ones build on |
| `clawmetry/providers/` | Pluggable data provider layer (LocalDataProvider, TursoDataProvider) |

### Config & Build
| File | Purpose |
|------|---------|
| `setup.py` | PyPI package definition (entry point: `clawmetry` CLI). Derives the PyPI summary from `clawmetry/entitlements.py`, so the advertised runtime count cannot drift |
| `requirements.txt` | pip dependencies |
| `Dockerfile` | Docker image (Python 3.11-slim base) |
| `Makefile` | Dev commands: `make dev`, `make test`, `make lint` (which runs every `lint-*` guard) |
| `install.sh` | One-liner installer script |
| `desktop/` | The thin-shell desktop app (`.dmg` / `.exe` / `.deb` / `.AppImage`) that pip-installs clawmetry |
| `scripts/` | The drift guards CI runs: `scripts/sync_runtime_count.py`, `scripts/gen_module_map.py`, `scripts/gen_query_contract_doc.py`, `scripts/check_ac_coverage.py`, `scripts/check_product_record.py`, `scripts/lint_daemon_allowlist.py` |

### Documentation
| File | Purpose |
|------|---------|
| `ARCHITECTURE.md` | Architecture deep dive with C4 diagrams: the five intervention surfaces, the ingest paths, the store, Guard |
| `docs/MODULE_MAP.md` | **Generated** inventory of every module, blueprint and URL prefix (`scripts/gen_module_map.py`) |
| `docs/QUERY_CONTRACT.md` | **Generated** node query surface (`clawmetry/query_contract.py`) |
| `docs/ENTITLEMENTS.md` | Open-core split: FREE runtimes/features, paid tiers, GRACE mode, `/api/entitlement` shape, `clawmetry license` CLI |
| `docs/EGRESS.md` | Every outbound destination, what it carries, and how to verify it on the wire |
| `docs/HOOK_COEXISTENCE.md` | How ClawMetry shares a runtime's hook config with other writers |
| `docs/CUSTOM_RUNTIME_INGEST.md` | The HTTP ingest API for a runtime with no adapter |
| `docs/EVENT_RETENTION.md` | Store growth and trimming |
| `CHANGELOG.md` | Version history |
| `CONTRIBUTING.md` | Contribution guidelines |
| `SECURITY.md` | Security posture |
| `CLOUD_EXTENSION_DESIGN.md` | Cloud feature design |

## How it works
The **sync daemon** (`clawmetry/sync.py`) ingests these sources into the local **DuckDB** store; the Flask app reads DuckDB (via `routes/local_query.py`) to serve the UI:
1. OpenClaw session transcripts from `~/.openclaw/agents/main/sessions/*.jsonl`
2. Every other runtime's own store, read by its adapter and loaded from the
   hardcoded `sync._FAMILY_ADAPTER_SPECS` tuple (Claude Code under
   `~/.claude/projects/<slug>/*.jsonl`, Codex, Cursor, Goose, …). There is no
   dynamic discovery: an adapter absent from that tuple never loads.
3. Chat-channel transcripts from `~/.openclaw/<channel>/*.jsonl` —
   one directory per adapter (`telegram/`, `signal/`, `whatsapp/`,
   `discord/`, `slack/`, `irc/`, `imessage/`, `webchat/`, …). The 23
   adapter directories match the routes in `routes/channels.py`. New
   adapter? Add its dir name to `_CHANNEL_DIRS` in `clawmetry/sync.py`
   (`tests/test_entitlement_channel_catalog.py` pins it to `ALL_CHANNELS`).
4. OpenClaw gateway via WebSocket (JSON-RPC, port 18789) for live data
5. Optional OpenTelemetry metrics/traces/logs on `/v1/metrics`, `/v1/traces`, and `/v1/logs`
6. Runtime hooks (`clawmetry hook <runtime>`), the only path that sees a tool
   call *before* it runs, and the HTTP ingest API (`/api/v1/runs/*`) for a
   runtime with no adapter

Cadence: the daemon's main loop runs every 15s (`sync.POLL_INTERVAL`), family
runtimes and the system snapshot every 60s.

The daemon owns the DuckDB writer lock and runs a localhost query server so the dashboard reads through it. The dashboard serves the UI at `http://127.0.0.1:8900` (loopback by default; `--host` widens it deliberately); for cloud, the daemon also pushes an E2E-encrypted snapshot to `ingest.clawmetry.com` (decrypted client-side in the browser).

## API Endpoints (key ones)
The complete surface is generated at `/openapi.json` and browsable at `/api/docs`; `docs/MODULE_MAP.md` maps each URL prefix to the module that owns it.

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
- `/api/alerts/*` — Custom alert rules (incl. the `signal_rate_above` rule type: a behaviour signal's rate over a window with a minimum sample)
- `/api/signals` — Behaviour signal rates per window (`1d|7d|30d`) and `?runtime=`, with coverage and headline; `/api/signals/<name>/sessions` lists matching sessions, never phrases
- `/api/guard/sessions` — What is running, what a detector thinks has gone off track, and whether each session can be controlled at all; `/api/guard/control` is the Pause / Stop / Kill button and `/api/guard/policies` the autonomous rules
- `/api/entitlement` — The resolved entitlement (tier, allowed runtimes, features, capacity). GRACE mode answers "allowed" for everything until the announced enforce date
- `/api/local/*` — The DuckDB read API, proxied to the daemon. The method set is declared in `clawmetry/query_contract.py`; `make lint-daemon-allowlist` fails when a route calls one the daemon does not serve
- `/v1/metrics`, `/v1/traces`, `/v1/logs` — OTLP receiver (binds `127.0.0.1` by default)

## Dependencies
Minimal by design, and this list had drifted — `setup.py` is the source of truth:
- **flask** (>=2.0,<4) — HTTP server framework
- **waitress** (>=2.0) — WSGI application server
- **cryptography** (>=50.0.0 on 3.10+; >=46.0.0 on 3.9.2–3.9.x, capped there by the py3.9-only `cffi<2` pin; >=3.0 on 3.8/3.9.0/3.9.1) — AES-256-GCM for cloud sync
- **duckdb** (>=0.10) — the local store at `~/.clawmetry/clawmetry.duckdb`
- **websocket-client** (>=1.6) — cloud cold-data relay tunnel
- **truststore** (>=0.8, 3.10+ only) — OS trust store, so corporate TLS-interception root CAs work
- **certifi** (>=2024.2.2) — CA bundle; the trust-store fallback on 3.8/3.9 and on any interpreter whose OpenSSL has no CA store. Without one, every outbound HTTPS call fails `CERTIFICATE_VERIFY_FAILED`, and for the fire-and-forget pings that failure is silent
- **cffi** (`<2` below 3.10, `>=2` on 3.10+) — not a direct import; it is what sets the `cryptography` ceiling above. The `<2` half exists because cffi 2.0.0 has a Python 3.9 finalizer SIGSEGV and cffi 2.1+ ships no cp39 wheels
- **Optional**: `opentelemetry-proto` + `protobuf` for OTLP (`pip install clawmetry[otel]`), `deepeval` for the eval bridge (`clawmetry[deepeval]`, 3.10+)
- `python_requires=">=3.8"`

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

# Syntax + every drift guard (runtime/channel counts, module map,
# daemon allowlist, py3.9 annotations, AC coverage, JS parse)
make lint
```

Tests use `CLAWMETRY_URL` and `CLAWMETRY_TOKEN` env vars. Test matrix in CI: 3 OS (Ubuntu, macOS, Windows) x 2 Python versions (3.9, 3.11).

**CI runs explicit FILE LISTS, not `pytest tests/`.** A new test file that is not named in a workflow step runs in no job at all, which has shipped guards that never once executed. Add yours to `.github/workflows/ci.yml` in the same PR.

## Deploy
- **PyPI**: `pip install clawmetry && clawmetry`
- **Docker**: `docker build -t clawmetry . && docker run -p 8900:8900 -v ~/.openclaw:/root/.openclaw:ro clawmetry`
- **Version**: `__version__` in `dashboard.py`. Don't hand-edit it and don't trust it as "what is released": `release-on-merge.yml` computes `max(PyPI, file) + 1` on a `[RELEASE]` merge, and the write-back bump PR often goes unmerged, so `main` legitimately lags PyPI by tens of releases. `https://pypi.org/pypi/clawmetry/json` is the released number.

## CI/CD (GitHub Actions)
36 workflows; the ones you will actually touch:
- `.github/workflows/ci.yml` — Lint + drift guards + test matrix on push/PR
- `.github/workflows/e2e-gate.yml` — The aggregating merge gate (`E2E Gate (required)`), which counts Drift Bot as a leg
- `.github/workflows/release-on-merge.yml` — Publishes when a `[RELEASE]` PR merges (see FLYWHEEL.md §5)
- `.github/workflows/publish.yml` — PyPI publish on git tag `v*`
- `.github/workflows/sync-test.yml` — Cloud sync daemon tests
- `.github/workflows/install-test.yml` — Cross-platform pip install smoke tests
- `.github/workflows/product-record-gate.yml` — Fails a PR touching product code whose body cites no Factory record or `No-PRD:` line
- `.github/workflows/auto-deploy-cloud.yml` — Cloud deployment
- `.github/workflows/browserstack.yml` — Cross-browser E2E testing
- `.github/workflows/queue-priority.yml` — Cancels queued non-main runs when main moves, so releases are not stuck behind PR jobs

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
CLAWMETRY_SIGNALS=1                    # Behaviour Signals tick on/off; CLAWMETRY_SIGNALS_EVENTS_PER_TICK (2000) and CLAWMETRY_SIGNALS_SCAN_CHARS (2000) bound each pass

# Guard / enforcement. Every one of these defaults to the safe side.
CLAWMETRY_DETECTORS=1                  # Trajectory + behavioural detectors on/off
CLAWMETRY_GUARD_POLICIES=1             # Evaluate Guard policies at all (0 = skip the pass entirely)
CLAWMETRY_POLICY_ENFORCE=0             # Let a policy actually signal a process. Default 0 = dry run; this one env var disables every policy on the node
CLAWMETRY_GUARD_CRITICAL_USD=...       # Spend-at-risk above which a warning becomes critical
CLAWMETRY_NOPROG_TOOLS__<RUNTIME>=40   # Per-runtime threshold override (highest layer in resolve_thresholds)
CLAWMETRY_ENFORCE=1                    # Turn entitlement enforcement on (default: GRACE, everything allowed)

# Resource budget (FLYWHEEL.md 1e: the daemon must stay near-invisible)
CLAWMETRY_DUCKDB_THREADS=2             # DuckDB defaults to every core; never ship an uncapped connection
CLAWMETRY_DUCKDB_MEMORY_LIMIT=...      # Ceiling; derived from store size when unset
CLAWMETRY_AGG_CACHE_TTL=20             # Seconds a hot rollup is reused instead of re-scanned
CLAWMETRY_AUTO_COMPACT=0               # Kill switch for startup compaction

# Egress
CLAWMETRY_OFFLINE=1                    # Air-gapped: no install ping, no version check. See docs/EGRESS.md
DEBUG=1                                # Enable debug logging
```

## Conventions
- **Product record before code (FLYWHEEL.md section 0c).** 8090 Software Factory is the product reviewer, not a lint gate. Write the requirement first -- problem, who is hurt, non-goals, alternatives rejected, risk accepted -- then the blueprint, then the code. A requirement written after the fact reviews nothing, and `scripts/check_product_record.py` gates PRs on citing one (or an explicit `No-PRD: <reason>`).
- **Per-feature route modules** — new endpoints live in `routes/<feature>.py`, registered on a feature Blueprint that `dashboard.py` imports and registers. This replaces the old "single file" rule, which became counterproductive at ~33K lines (illegible to humans, constant PR conflicts on a single anchor point). Helpers are migrating into `helpers/` (gateway RPC, log discovery, pricing, system stats, the OpenAPI spec); the ones still in `dashboard.py` are reached from route modules via late `import dashboard as _d` to avoid circular imports. `docs/MODULE_MAP.md` is the generated index of where everything currently lives.
- **Embedded frontend, no build step** — the live UI is served from `clawmetry/static/` (`clawmetry/static/css/dashboard.css`, `clawmetry/static/js/app.js`) + `clawmetry/templates/tabs/*.html`. (`dashboard.py` defines `DASHBOARD_HTML` twice; the **second** wins and loads the static/template files — the earlier inline `<style>`/HTML is dead, so edit the static/template files.) No npm, no webpack.
- **Minimal dependencies** — Flask + waitress + cryptography. Don't add heavy libraries.
- **Control plane that defaults to observation** — ClawMetry is NOT read-only, and hasn't been for a long time. It already kills, pauses, blocks and reroutes running agents through five surfaces: approval denial → session kill (`clawmetry/approvals.py`), POSIX signals across the agent's descendant tree (`clawmetry/process_control.py`), HITL pause → proxy `503` (`routes/hitl.py`), the enforcement proxy's budget block / loop detection / model routing (`clawmetry/proxy.py`), and cron CRUD via gateway RPC (`routes/crons.py`). Do NOT reject a feature because "we're read-only" — that rule is retired.
  The rule that replaces it is **no surprise writes**: every write is (a) user-initiated or declared in a policy the user wrote, (b) scoped to a single session, (c) reversible where physics allows, and (d) attributed in the approvals audit table. Reads need no permission; writes need all four.
  **Fail open on entitlement, closed on policy.** If a licence/entitlement lookup errors or is ambiguous, the agent KEEPS RUNNING — only a policy the user actually declared may block or kill. A billing bug must never stop a customer's agent. (`clawmetry/entitlements.py` already defaults to GRACE, where every `allows_*` returns `True`; new control features inherit that posture and assert it in a test.)
  **Capability is answered per session, from one place.** `process_control.runtime_control_support(runtime, session_id, cwd)` is the single verdict the Guard tab, the daemon and the actuator all read; never re-derive it. Three axes vary independently and each has bitten us: (1) **OS** — POSIX uses signals, **Windows uses the native equivalents** (`NtSuspendProcess`/`NtResumeProcess`, a console Ctrl+C from a detached helper, `taskkill /T` → `TerminateProcess`). Declare ctypes `argtypes`/`restype` on every Win32 call — the default `c_int` restype truncates a 64-bit `HANDLE` and the whole path fails silently. A Windows Ctrl+C reaches the console, not one pid; say so in the UI. (2) **Session, not runtime** — a Cursor *CLI* session is a real process tree and is controllable; a Cursor *editor* conversation shares the one IDE process and is not. Ask the resolver, don't refuse a runtime wholesale. (3) **OpenClaw pause** — there is no pause primitive; the HITL flag is enforced *only* by `clawmetry/proxy.py`, so with no proxy running a "pause" changes nothing. Probe `enforcement_proxy_status()` and report `advisory_only` rather than claiming the agent was held. A control that cannot work says why next to a disabled button — never ship one that quietly does nothing.
  **Policies escalate over time.** A Guard policy may carry `steps` (`[{action, after_secs}, …]`, capped at `policy_engine.MAX_LADDER_STEPS`) so the response can be *pause now, kill in 5 minutes if still stuck*. Rung 0 fires on the match; rung *n* is due `after_secs` after rung *n-1* **actually fired**; a rung only fires if the session is **still matching** that tick. The durable latch is `(session_id, policy_id, step_index)` — widening it was mandatory, since a two-column latch lets rung 1 overwrite rung 0 and a restart replays a ladder ending in `kill`. Every rung passes the same locks: a ladder can never reach a process a plain policy could not. A policy with no `steps` is a one-rung ladder, which is why every pre-ladder rule is unchanged.
- **Acceptance criteria are traceable to tests** — every criterion in `docs/acceptance_criteria.json` (mirrored from 8090 Software Factory) must be declared by at least one test under `tests/`. CI enforces it as a one-way ratchet; see FLYWHEEL.md §1g. Drift Bot catches "this diff contradicts a Blueprint"; this catches "untouched code stopped satisfying a criterion", which is the class that produced `$0.00` cost windows and ghost sessions. `make ac-report` to see where you stand.
- **Never delete a hook you did not write** — `~/.claude/settings.json` has other writers (GitLens's `gk ai hook install claude-code --force`, `numbat`, the user) and ClawMetry itself writes it from three places. Every removal path goes through `clawmetry/hook_ownership.py` at **hook** granularity, never entry granularity: a foreign writer may have merged its command into the same entry as ours, and the daemon gate's reinstall runs every ~2s, so an entry-level drop deletes someone else's hook within seconds. Installed hook timeouts are clamped (`CLAWMETRY_HOOK_TIMEOUT_MAX_S`, default 8h) — on Copilot, whose `preToolUse` gate is fail-closed, an unbounded wait on a wedged hook is a denial of service against the user's own agent. `docs/HOOK_COEXISTENCE.md`; harness `scripts/hook_collision_matrix.py`.
- **A user's repository is read, never written** — `clawmetry/git_outcomes.py` is the only place ClawMetry runs `git` against a directory the operator chose, and it routes every invocation through one chokepoint that rejects anything outside an allowlist of read-only plumbing subcommands (`log`, `rev-list`, `blame`, `cat-file`, `rev-parse`, `for-each-ref`, `show-ref`, `ls-files`, plus `config --get` and `remote get-url`). A `fetch` added "just to freshen state" raises `UnsafeGitCommand` rather than shipping. Add a new git call by adding it to that allowlist, with a test, or not at all.
- **Auto-detect everything** — users should never need to configure anything manually.
- **Never crash on bad input** — graceful fallbacks for missing data, log warnings but continue.
- **Never starve the heartbeat** — the cloud relay drains and answers `pending_queries` (Brain time-window fetches, transcript reads, approvals) only when the daemon heart-beats, and the heartbeat fires at the end of a main-loop iteration. Any ingest pass that can run long (deep `runtime_backfill`, first-run ingest of hundreds of sessions) must call `_ingest_keepalive_heartbeat(config)` between items, or every hosted relay read sits on `relay_pending` until the browser gives up (2026-07-30 Brain-window RCA: a 465-session backfill blocked heartbeats for ~2m40s).
- **Detector thresholds are resolved, not hard-coded** — `detectors.resolve_thresholds(runtime, baseline)` layers four sources, each overriding the last: module defaults → the runtime profile (write-tool vocabulary, a checkable fact about the adapter, never an invented number) → the cohort's learned baseline from `guard_session_stats` / `guard_egress_hosts` → a per-runtime env override (`CLAWMETRY_NOPROG_TOOLS__CODEX=40`). Every incident carries `threshold_source`, so a reader can tell a measured threshold from a shipped constant. Learned values are clamped to a band around the static default: a cohort where everything loops cannot teach the detectors to go blind, and a cohort of three sessions cannot make them scream.
- **Incident severity maps to money** — detectors attach `spend_at_risk_usd` (the estimated cost of the *flagged stretch*, not the session bill) plus the `spend_basis` that produced it, and a `warning` crossing `CLAWMETRY_GUARD_CRITICAL_USD` becomes `critical`. Where no cost is known the field is `0.0` with basis `unknown`, never a fabricated figure. Surfaces that list incidents (`/api/loop-signals`) rank by it.
- **snake_case** functions, **PascalCase** classes, **SCREAMING_SNAKE_CASE** constants.
