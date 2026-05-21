# CLAUDE.md — ClawMetry

## What is this?
ClawMetry is an open-source, real-time observability dashboard for [OpenClaw](https://github.com/openclaw/openclaw) AI agents. `pip install clawmetry && clawmetry` — that's it. Zero config, read-only by default.

## Architecture
See `ARCHITECTURE.md` for the full deep dive. TL;DR:
- **Flask app** with embedded HTML/CSS/JS frontend (no build step, no npm)
- **Per-feature route modules** under `routes/` — `routes/sessions.py`, `routes/usage.py`, etc. — each owns one Blueprint and the endpoints registered on it. New endpoints land in their feature's module so parallel PRs don't stomp on each other.
- **Shared helpers** stay in `dashboard.py` for now and are accessed from route modules via late `import dashboard as _d`. (Helpers will migrate to `helpers/` over time.)
- **Zero config** — auto-detects OpenClaw workspace, gateway, sessions, logs
- **Read-only** — observes OpenClaw, never modifies it (except cron management via gateway RPC)
- **DuckDB-first** — the sync daemon ingests filesystem/gateway/OTLP into a local **DuckDB** store (`clawmetry/local_store.py`; the daemon owns the writer lock). Request handlers read from DuckDB via `routes/local_query.py`, **not** raw files — reading raw JSONL/logs inside a handler works locally but returns empty in cloud (the container has no `~/.openclaw`). Optional `history.py` adds a separate SQLite time-series.
- **Three ingest sources** (all land in DuckDB): filesystem (JSONL/logs), gateway WebSocket (JSON-RPC), optional OTLP receiver

## Key Files

### Core
| File | Lines | Purpose |
|------|-------|---------|
| `dashboard.py` | ~17,300 | Flask app, blueprint registration, shared helpers (live frontend now lives in `static/` + `templates/`) |
| `dashboard_claudecode.py` | ~1,350 | Claude Code session dashboard variant (standalone or Blueprint) |
| `history.py` | ~555 | Optional time-series collector (SQLite, polls gateway every 60s) |

### Route modules (`routes/`)
All HTTP endpoints live here, organised by feature. Each module owns one or more Flask Blueprints; handlers do late `import dashboard as _d` to reach shared helpers still in `dashboard.py`.

| File | Lines | Blueprints / Purpose |
|------|-------|----------------------|
| `routes/sessions.py` | ~1,560 | `bp_sessions` — sessions list, transcripts, compactions, tool timeline, cost split, subagents, exports |
| `routes/channels.py` | ~1,500 | `bp_channels` — 21 chat-channel adapters (Telegram, Signal, WhatsApp, Discord, Slack, IRC, iMessage, WebChat, …) |
| `routes/components.py` | ~1,040 | `bp_components` — Flow-panel detail endpoints (tool / runtime / machine / gateway / brain) |
| `routes/usage.py` | ~1,070 | `bp_usage` — token/cost analytics, anomaly detection, model + skill attribution |
| `routes/health.py` | ~920 | `bp_health` — system-health, reliability, diagnostics, rate-limits, sandbox-status, health-stream (SSE) |
| `routes/brain.py` | ~1,030 | `bp_brain` — `/api/brain-history` + `/api/brain-stream` (SSE) |
| `routes/local_query.py` | ~585 | `bp_local_query` — `/api/local/*` DuckDB read API + the daemon-proxy `_dispatch` (shape→store bridge shared by HTTP and the cloud relay) |
| `routes/infra.py` | ~785 | `bp_logs` + `bp_memory` + `bp_security` + `bp_config` — logs stream, memory files, security posture, cost-optimizer |
| `routes/overview.py` | ~585 | `bp_overview` — main dashboard endpoint, channels list, timeline, cloud-CTA OTP |
| `routes/crons.py` | ~530 | `bp_crons` — cron CRUD + run log + health summary |
| `routes/meta.py` | ~520 | `bp_auth` + `bp_gateway` + `bp_otel` + `bp_version` + `bp_version_impact` + `bp_clusters` — auth, gateway proxy, OTLP ingestion, version meta |
| `routes/alerts.py` | ~400 | `bp_alerts` + `bp_budget` — alert rules, webhooks, velocity, budget config |
| `routes/fleet_history.py` | ~310 | `bp_fleet` + `bp_history` — multi-node fleet + SQLite time-series |
| `routes/nemoclaw.py` | ~290 | `bp_nemoclaw` — NeMo Guardrails governance + approval queue |
| `routes/__init__.py` | — | Package marker |

### Package (`clawmetry/`)
| File | Lines | Purpose |
|------|-------|---------|
| `cli.py` | ~1,900 | CLI entry point — `clawmetry`, `clawmetry connect`, `clawmetry sync`, `clawmetry status` |
| `sync.py` | ~10,600 | Cloud sync daemon — ingests into DuckDB, owns the writer lock, E2E-encrypted (AES-256-GCM) snapshot streaming to `ingest.clawmetry.com` |
| `local_store.py` | ~7,300 | **DuckDB store** — the single data layer features read/write (daemon holds the writer lock) |
| `local_server.py` | ~200 | Daemon-hosted localhost query server (`/__local_query__/<method>`) so the dashboard/sync read DuckDB without grabbing the writer lock |
| `proxy.py` | ~1,290 | Enforcement proxy — budget limits, loop detection, model routing (port 4100) |
| `interceptor.py` | ~465 | Zero-config HTTP monkey-patching for LLM cost tracking (patches httpx/requests) |
| `providers_pricing.py` | ~134 | Multi-provider pricing table (Anthropic, OpenAI, Google, OpenRouter, etc.) |
| `config.py` | ~80 | Configuration dataclass |
| `extensions.py` | ~109 | Plugin/hook system |
| `track.py` | ~39 | Zero-config interceptor shorthand |
| `providers/` | — | Pluggable data provider layer (LocalDataProvider, TursoDataProvider) |

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

## How it works
The **sync daemon** (`clawmetry/sync.py`) ingests these sources into the local **DuckDB** store; the Flask app reads DuckDB (via `routes/local_query.py`) to serve the UI:
1. Session transcripts from `~/.openclaw/agents/main/sessions/*.jsonl`
2. Chat-channel transcripts from `~/.openclaw/<channel>/*.jsonl` —
   one directory per adapter (`telegram/`, `signal/`, `whatsapp/`,
   `discord/`, `slack/`, `irc/`, `imessage/`, `webchat/`, …). The 21
   adapter directories match the routes in `routes/channels.py`. New
   adapter? Add its dir name to `_CHANNEL_DIRS` in `clawmetry/sync.py`.
3. OpenClaw gateway via WebSocket (JSON-RPC, port 18789) for live data
4. Optional OpenTelemetry metrics/traces on `/v1/metrics` and `/v1/traces`

The daemon owns the DuckDB writer lock and runs a localhost query server so the dashboard reads through it. The dashboard serves the UI at `http://localhost:8900`; for cloud, the daemon also pushes an E2E-encrypted snapshot to `ingest.clawmetry.com` (decrypted client-side in the browser).

## API Endpoints (key ones)
- `/api/overview` — Main dashboard data (sessions, tokens, crons, health)
- `/api/sessions` — Active session list
- `/api/subagents` — Sub-agent tracker with status and costs
- `/api/transcript/<id>` — Full session transcript
- `/api/usage` — Token and cost analytics
- `/api/flow` — Message flow visualization (channels -> gateway -> models -> tools)
- `/api/brain-history` — Recent reasoning/tool events (paginated)
- `/api/brain-stream` — Live event stream (SSE)
- `/api/crons` — Cron job management (full CRUD via gateway RPC)
- `/api/system-health` — Disk, memory, uptime, GPU
- `/api/nodes` — Multi-node fleet view
- `/api/budget/*` — Budget monitoring and alerts
- `/api/alerts/*` — Custom alert rules

## Dependencies
Minimal by design:
- **flask** (>=2.0,<4) — HTTP server framework
- **waitress** (>=2.0) — WSGI application server
- **cryptography** (>=3.0) — AES-256-GCM for cloud sync
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
- **Current version**: `0.12.275` (in `dashboard.py` `__version__`)

## CI/CD (GitHub Actions)
- `ci.yml` — Lint + test matrix on push/PR
- `publish.yml` — PyPI publish on git tag `v*`
- `release-on-merge.yml` — Auto-release when version bumped on main
- `sync-test.yml` — Cloud sync daemon tests
- `install-test.yml` — Cross-platform pip install smoke tests
- `auto-deploy-cloud.yml` — Cloud deployment
- `browserstack.yml` — Cross-browser E2E testing

## Environment Variables
```bash
OPENCLAW_HOME=~/.openclaw              # OpenClaw workspace (auto-detected)
OPENCLAW_GATEWAY_TOKEN=token           # Gateway auth token
CLAWMETRY_PROVIDER=local|turso         # Data backend (default: local)
CLAWMETRY_INTERCEPT=1                  # Enable HTTP interceptor
CLAWMETRY_FLEET_KEY=...               # Multi-node fleet auth key
DEBUG=1                                # Enable debug logging
```

## Conventions
- **Per-feature route modules** — new endpoints live in `routes/<feature>.py`, registered on a feature Blueprint that `dashboard.py` imports and registers. This replaces the old "single file" rule, which became counterproductive at ~33K lines (illegible to humans, constant PR conflicts on a single anchor point). Helpers and shared state stay in `dashboard.py` for now and are accessed from route modules via late `import dashboard as _d` to avoid circular imports.
- **Embedded frontend, no build step** — the live UI is served from `clawmetry/static/` (`static/css/dashboard.css`, `static/js/app.js`) + `clawmetry/templates/tabs/*.html`. (`dashboard.py` defines `DASHBOARD_HTML` twice; the **second** wins and loads the static/template files — the earlier inline `<style>`/HTML is dead, so edit the static/template files.) No npm, no webpack.
- **Minimal dependencies** — Flask + waitress + cryptography. Don't add heavy libraries.
- **Read-only by default** — ClawMetry observes, it doesn't modify agent behavior (except cron management via gateway RPC).
- **Auto-detect everything** — users should never need to configure anything manually.
- **Never crash on bad input** — graceful fallbacks for missing data, log warnings but continue.
- **snake_case** functions, **PascalCase** classes, **SCREAMING_SNAKE_CASE** constants.
