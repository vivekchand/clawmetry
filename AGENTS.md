# AGENTS.md — For AI Coding Agents

> **Before code: write the product record in 8090** (FLYWHEEL.md section 0c). The requirement is where a change is justified, the blueprint is where it is designed, the code is where it is built -- in that order.
>
> **Read [`FLYWHEEL.md`](./FLYWHEEL.md) first.** It is how you ship a change end to end in this repo (code → PR → green CI → `[RELEASE]` → PyPI → cloud → verified live) and the non-negotiable "done" bar. Then [`CLAUDE.md`](./CLAUDE.md) for the architecture deep-dive. This file is the short "what to do"; those two carry the detail.

## Quick context
ClawMetry is an open-source, real-time observability and governance layer for **30 AI agent runtimes** (OpenClaw, NemoClaw and Goose free in OSS; Claude Code, Codex, Cursor and 24 more with the Pro plugin). The catalogue is `entitlements.FREE_RUNTIMES | PAID_RUNTIMES`; never hardcode the list or the count. `pip install clawmetry && clawmetry` — zero config, observation by default. It's a Flask app with an embedded, no-build vanilla-JS frontend; a sync daemon ingests filesystem/gateway/OTLP data into a local **DuckDB** store, and the app reads from DuckDB to serve the UI.

## Where new code goes (open-core split)

ClawMetry is open-core — there are **four repos**. Pick the right one *before* writing code; see `FLYWHEEL.md §1b` for the full decision tree.

- **clawmetry** (this repo, public OSS) — the FREE runtime adapters (OpenClaw, NemoClaw, Goose) + NeMo governance + 24 chat channels + entitlement gate (`clawmetry/entitlements.py`) + license client (`clawmetry/license.py`) + Enterprise feature **endpoints** (entitlement-gated; impl may defer to clawmetry-pro). Examples: `routes/otel_export.py`, `routes/audit.py`.
- **clawmetry-pro** (private; not on public PyPI; shipped via the license-server wheel download) — the 27 gated runtime adapters (Claude Code, Codex, Cursor, …), Pro paid CLI capabilities, advanced-feature implementations. Plugs in via `clawmetry.extensions` entry point.
- **clawmetry-cloud** (private) — cloud SaaS app + license server (`clawmetry-cloud/routes/license.py`) + Stripe + admin + closed-wheel hosting (`wheels/`).
- **clawmetry-landing** (private, public site) — marketing + pricing page + Buy buttons. No gated code.

Quick chooser:
- New runtime adapter → **clawmetry-pro** if the runtime is a commercial vendor product, **this repo** (`clawmetry/adapters/`, `FREE_RUNTIMES`, `sync._FAMILY_ADAPTER_SPECS`) if it is open source. Either way it is inert until it is named in `sync._FAMILY_ADAPTER_SPECS`.
- New Enterprise feature (OTel export, SSO, audit, RBAC) → **OSS** route, gated by `entitlements.allows_feature(...)`.
- New billing/Stripe/license endpoint → **clawmetry-cloud**.
- New pricing/copy/Buy → **clawmetry-landing**.

## The rules that bite
- **Write the PRD in 8090 BEFORE you write code.** Software Factory is the product reviewer -- treat it as the PM on the work, not as a checkbox drift-bot enforces afterwards. Requirement (problem, who is hurt, non-goals, alternatives rejected, risk accepted) -> blueprint (components, contracts, ADRs) -> code, in that order. A PR that touches product code must link the record or say `No-PRD: <reason>`; CI checks that one of the two is there. Burned 2026-08-25: four changes built first and documented after produced accurate mechanism, zero product context, and three defects a reviewer would have caught -- including a one-click irreversible data delete with no confirmation. (FLYWHEEL.md section 0c.)
- **DuckDB-first.** Every feature persists to and reads from the local DuckDB store (`clawmetry/local_store.py`; the daemon owns the writer lock). Reading raw JSONL / logs / `sessions.json` / process stats *inside a request handler* works locally but silently returns empty in cloud — that's a bug, not a shortcut. (FLYWHEEL.md §1.)
- **Per-feature route modules.** New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. The old "single file" rule is dead — it broke down at ~33K lines and caused constant PR conflicts. Shared helpers still in `dashboard.py` are reached via late `import dashboard as _d`.
- **No build step, no npm.** The live frontend is `clawmetry/static/css|js/*` + `clawmetry/templates/tabs/*.html`, vanilla JS only. (`dashboard.py` defines `DASHBOARD_HTML` twice; the second wins and loads the static/template files — the inline `<style>`/HTML earlier is dead code.) No React/Vue/webpack/vite.
- **Minimal dependencies.** Flask + waitress + cryptography + duckdb. Don't add heavy libraries.
- **Control plane that defaults to observation.** ClawMetry is NOT read-only: it already kills sessions on approval denial (`clawmetry/approvals.py`), signals whole descendant process trees (`clawmetry/process_control.py`), pauses via HITL → proxy `503` (`routes/hitl.py`), blocks and reroutes at the enforcement proxy (`clawmetry/proxy.py`), and does cron CRUD. Never reject a feature as "we're read-only". The live rule is **no surprise writes** — user-initiated or policy-declared, session-scoped, reversible, audited — plus **fail open on entitlement, closed on policy**: a licence error must never stop a customer's agent. (CLAUDE.md Conventions.)
- **Auto-detect everything.** Users should never have to configure anything manually.
- **Never crash on bad input.** Graceful fallbacks plus a logged warning, always.
- **Performance is a cost.** At $9/node/mo, every poller and fetch is money: cache + dedup shared fetches, scope pollers to the active tab. (FLYWHEEL.md ⚡.)

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
