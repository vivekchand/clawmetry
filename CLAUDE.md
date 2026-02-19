# CLAUDE.md — ClawMetry

## What is this?
ClawMetry is an open-source, real-time observability dashboard for [OpenClaw](https://github.com/openclaw/openclaw) AI agents. `pip install clawmetry && clawmetry` — that's it.

## Architecture
See `ARCHITECTURE.md` for the full deep dive. TL;DR:
- **Single Python file** (`dashboard.py`, ~11,600 lines) — Flask app with embedded HTML/CSS/JS
- **Zero config** — auto-detects OpenClaw workspace, gateway, sessions, logs
- **Read-only** — reads OpenClaw's filesystem + connects to gateway WebSocket
- **No database** — optional `history.py` adds SQLite time-series

## Key Files
- `dashboard.py` — The entire dashboard (server + frontend)
- `history.py` — Optional time-series history module (SQLite)
- `setup.py` — PyPI package config
- `packages/clawmetry/` — pip package wrapper
- `clawmetry-landing/` — Marketing website (clawmetry.com) [legacy, moved to separate repo]
- `ARCHITECTURE.md` — Detailed architecture guide
- `CHANGELOG.md` — Version history
- `CONTRIBUTING.md` — Contribution guidelines

## How it works
1. Reads session transcripts from `~/.openclaw/agents/main/sessions/*.jsonl`
2. Connects to OpenClaw gateway via WebSocket (JSON-RPC) for live data
3. Optionally receives OpenTelemetry metrics/traces on `/v1/metrics` and `/v1/traces`
4. Serves dashboard UI at `http://localhost:8900`

## API Endpoints (key ones)
- `/api/overview` — Main dashboard data (sessions, tokens, crons, health)
- `/api/sessions` — Active session list
- `/api/subagents` — Sub-agent tracker with status and costs
- `/api/transcript/<id>` — Full session transcript
- `/api/usage` — Token and cost analytics
- `/api/crons` — Cron job management
- `/api/system-health` — Disk, memory, uptime, GPU
- `/api/nodes` — Multi-node fleet view
- `/api/budget/*` — Budget monitoring and alerts
- `/api/alerts/*` — Custom alert rules

## Running locally
```bash
pip install flask
python dashboard.py --workspace ~/your-openclaw-workspace
```

## Deploy
PyPI: `pip install clawmetry && clawmetry`
Current version: check `__version__` in dashboard.py

## Testing changes
1. Edit `dashboard.py`
2. Run locally: `python dashboard.py`
3. Open `http://localhost:8900`
4. The frontend is embedded — edit the HTML template strings in the Python file

## Conventions
- **Single file** — don't split dashboard.py into modules. The single-file design is intentional for portability.
- **Minimal dependencies** — Flask only. Don't add heavy libraries.
- **Embedded frontend** — HTML/CSS/JS lives inside Python template strings. No build step.
- **Read-only by default** — ClawMetry observes, it doesn't modify agent behavior (except cron management via gateway RPC).
- **Auto-detect everything** — users should never need to configure anything manually.
