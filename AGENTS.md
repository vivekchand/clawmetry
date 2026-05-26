# AGENTS.md — For AI Coding Agents

> **Read [`FLYWHEEL.md`](./FLYWHEEL.md) first.** It is how you ship a change end to end in this repo (code → PR → green CI → `[RELEASE]` → PyPI → cloud → verified live) and the non-negotiable "done" bar. Then [`CLAUDE.md`](./CLAUDE.md) for the architecture deep-dive. This file is the short "what to do"; those two carry the detail.

## Quick context
ClawMetry is an open-source, real-time observability dashboard for OpenClaw (and other) AI agents. `pip install clawmetry && clawmetry` — zero config, read-only by default. It's a Flask app with an embedded, no-build vanilla-JS frontend; a sync daemon ingests filesystem/gateway/OTLP data into a local **DuckDB** store, and the app reads from DuckDB to serve the UI.

## The rules that bite
- **DuckDB-first.** Every feature persists to and reads from the local DuckDB store (`clawmetry/local_store.py`; the daemon owns the writer lock). Reading raw JSONL / logs / `sessions.json` / process stats *inside a request handler* works locally but silently returns empty in cloud — that's a bug, not a shortcut. (FLYWHEEL.md §1.)
- **Per-feature route modules.** New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. The old "single file" rule is dead — it broke down at ~33K lines and caused constant PR conflicts. Shared helpers still in `dashboard.py` are reached via late `import dashboard as _d`.
- **No build step, no npm.** The live frontend is `clawmetry/static/css|js/*` + `clawmetry/templates/tabs/*.html`, vanilla JS only. (`dashboard.py` defines `DASHBOARD_HTML` twice; the second wins and loads the static/template files — the inline `<style>`/HTML earlier is dead code.) No React/Vue/webpack/vite.
- **Minimal dependencies.** Flask + waitress + cryptography + duckdb. Don't add heavy libraries.
- **Read-only by default.** ClawMetry observes; it doesn't modify agent behavior (the exceptions are cron management and enforcement, which go through the gateway RPC or OpenClaw's own credentials, never a new write path).
- **Auto-detect everything.** Users should never have to configure anything manually.
- **Never crash on bad input.** Graceful fallbacks plus a logged warning, always.
- **Performance is a cost.** At $5/node/mo, every poller and fetch is money — cache + dedup shared fetches, scope pollers to the active tab. (FLYWHEEL.md ⚡.)

## Common tasks
- **Add an API endpoint:** add it to `routes/<feature>.py` on the feature Blueprint; reach shared helpers via late `import dashboard as _d`.
- **Change the UI:** edit `clawmetry/static/css/dashboard.css`, `clawmetry/static/js/app.js`, or `clawmetry/templates/tabs/*.html` — never the dead inline HTML in `dashboard.py`.
- **Light up a cloud surface:** the OSS daemon adds the data to `sync_system_snapshot`; the cloud renders it with a client-side `cm-cloud-*` interceptor (the cloud server can't decrypt — data is E2E-encrypted). See the cloud repo's `FLYWHEEL.md`.

## Releasing
- **Never hand-edit `__version__` or push a `v*` tag.** Publishing is triggered by merging a separate PR whose title starts with `[RELEASE]`; the workflow then bumps the patch version and uploads to PyPI. Full procedure in FLYWHEEL.md §5.

## Conventions
- `snake_case` functions, `PascalCase` classes, `SCREAMING_SNAKE_CASE` constants.
- No em-dashes / double-dashes in user-facing copy (banners, marketing). Code comments + PR text are fine.
- Don't store user data outside the local machine; cloud sync is E2E-encrypted and the cloud only ever holds opaque blobs.
- Keep business/revenue/funnel/pricing docs out of this public repo — they go in the private `clawmetry-cloud` repo. (FLYWHEEL.md §2.)
