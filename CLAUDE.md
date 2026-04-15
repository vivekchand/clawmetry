# CLAUDE.md — ClawMetry

## What is this?
ClawMetry is an open-source, real-time observability dashboard for [OpenClaw](https://github.com/openclaw/openclaw) AI agents. `pip install clawmetry && clawmetry` — that's it. Zero config, single-file core, read-only by default.

## Architecture
See `ARCHITECTURE.md` for the full deep dive. TL;DR:
- **Flask app** with embedded HTML/CSS/JS frontend (no build step, no npm)
- **Per-feature route modules** under `routes/` — `routes/sessions.py`, `routes/usage.py`, etc. — each owns one Blueprint and the endpoints registered on it. New endpoints land in their feature's module so parallel PRs don't stomp on each other.
- **Shared helpers** stay in `dashboard.py` for now and are accessed from route modules via late `import dashboard as _d`. (Helpers will migrate to `helpers/` over time.)
- **Zero config** — auto-detects OpenClaw workspace, gateway, sessions, logs
- **Read-only** — reads OpenClaw's filesystem + connects to gateway WebSocket
- **No database** — optional `history.py` adds SQLite time-series
- **Three data sources**: filesystem, gateway WebSocket (JSON-RPC), and optional OTLP receiver

## Key Files

### Core
| File | Lines | Purpose |
|------|-------|---------|
| `dashboard.py` | ~31,000 | Flask app, blueprint registration, embedded HTML/CSS/JS, shared helpers |
| `routes/sessions.py` | ~1,500 | `bp_sessions` — sessions list, transcripts, compactions, tool timeline, cost split, subagents, exports |
| `routes/__init__.py` | — | Package marker |
| `dashboard_claudecode.py` | ~1,350 | Claude Code session dashboard variant (standalone or Blueprint) |
| `history.py` | ~555 | Optional time-series collector (SQLite, polls gateway every 60s) |

### Package (`clawmetry/`)
| File | Lines | Purpose |
|------|-------|---------|
| `cli.py` | ~1,900 | CLI entry point — `clawmetry`, `clawmetry connect`, `clawmetry sync`, `clawmetry status` |
| `sync.py` | ~3,000 | Cloud sync daemon — E2E encrypted (AES-256-GCM) session streaming to `ingest.clawmetry.com` |
| `proxy.py` | ~1,290 | Enforcement proxy — budget limits, loop detection, model routing (port 4100) |
| `interceptor.py` | ~465 | Zero-config HTTP monkey-patching for LLM cost tracking (patches httpx/requests) |
| `providers_pricing.py` | ~134 | Multi-provider pricing table (Anthropic, OpenAI, Google, OpenRouter, etc.) |
| `config.py` | ~58 | Configuration dataclass |
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
1. Reads session transcripts from `~/.openclaw/agents/main/sessions/*.jsonl`
2. Connects to OpenClaw gateway via WebSocket (JSON-RPC, port 18789) for live data
3. Optionally receives OpenTelemetry metrics/traces on `/v1/metrics` and `/v1/traces`
4. Serves dashboard UI at `http://localhost:8900`

## API Endpoints (key ones)
- `/api/overview` — Main dashboard data (sessions, tokens, crons, health)
- `/api/sessions` — Active session list
- `/api/subagents` — Sub-agent tracker with status and costs
- `/api/transcript/<id>` — Full session transcript
- `/api/usage` — Token and cost analytics
- `/api/flow` — Message flow visualization (channels -> gateway -> models -> tools)
- `/api/brain` — Live event stream
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
- **Current version**: `0.12.99` (in `dashboard.py` `__version__`)

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
- **Embedded frontend** — HTML/CSS/JS still lives inside Python template strings in `dashboard.py`. No build step, no npm, no webpack.
- **Minimal dependencies** — Flask + waitress + cryptography. Don't add heavy libraries.
- **Read-only by default** — ClawMetry observes, it doesn't modify agent behavior (except cron management via gateway RPC).
- **Auto-detect everything** — users should never need to configure anything manually.
- **Never crash on bad input** — graceful fallbacks for missing data, log warnings but continue.
- **snake_case** functions, **PascalCase** classes, **SCREAMING_SNAKE_CASE** constants.
