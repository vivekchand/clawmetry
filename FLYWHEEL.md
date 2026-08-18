# FLYWHEEL.md — ClawMetry

> 🌀 ClawMetry's adoption of the **[FLYWHEEL.md](https://flywheel.md)** convention — the agent canon: `AGENTS.md` (what to do), `CLAUDE.md` (architecture), `FLYWHEEL.md` (how to ship). ClawMetry is its first adopter. This is our tailored instance; yours will differ — keep the bar.

How an autonomous agent should ship a change in this repo **end to end**: code → PR → green CI → merge → `[RELEASE]` → PyPI → promote to clawmetry-cloud → verify live. Read this with `CLAUDE.md` (architecture) and the cloud repo's `FLYWHEEL.md` (the other half of the loop).

The north star: **don't stop at "code compiles." Stop at "verified working in production, by me, with evidence."** Use `/goal` and keep iterating until that's true.

> ## 💗 The vision — who we build for (read before every UI change)
> **We are building the observability tool for people who have never used one.** Not for SREs who live in dashboards — for everyone. We are entering an era where an ordinary person will run, delegate to, and have to *manage hundreds of AI agents*, and they will need to understand, at a glance and without jargon: *is my agent alive? what is it doing? is it stuck? what did it cost me? can I trust it?* ClawMetry is the calm, human window into that. The person opening it may never have heard the word "observability," may not know what a "span" or "session id" or "event" is, and should never have to.
> - **Design for the newcomer, not the expert.** If a first-timer with zero context can't understand a screen in five seconds, it's not done. Lead with the human story (is it on, what's it doing, what did it cost), not the toolbox. Power tools (compare runs, error triage, raw-id inputs) are demoted and progressively disclosed, never the first thing a beginner sees. No empty box that asks them to paste an ID they don't have.
> - **Empathy is the spec.** Every label, empty state, and default is a small act of care for a real, possibly-overwhelmed human. Plain words over jargon. Reassurance over noise. Beauty and warmth are features, not decoration.
> - **Use the `frontend-design` skill for UI work** — bring real design taste (intentional typography, color, motion) plus the empathy above. Build with care and love for the person on the other side of the screen; never "fix UI like a backend dev."

> ## ⛔ The "done" bar (non-negotiable)
> **Never tell the user a fix is "done" until it is MERGED, RELEASED to PyPI, the cloud has DEPLOYED it, and you have VERIFIED it live (decrypt the snapshot AND/OR a browser screenshot of the actual tab).** "PR is up / CI green / merged" is *not* done — code that isn't deployed helps nobody. A diagnosis is not a fix; a merge is not a deploy; a deploy is not a verification. Land the whole chain, then say done — once, plainly, with the evidence.

> ## 📨 "End to end" means REAL messages (non-negotiable)
> **When the user says "test end to end," they mean: send a real message through a real channel and watch it travel the whole pipeline until a real reply comes back — not a synthetic seed, not a unit test, not "the function returns the right shape."** The only proof a feature works is that an actual message you sent shows up at every stage that should reflect it. For an observability feature like Flow/Brain/Tracing that means: start the real OpenClaw gateway, send a real message via a real channel (WebChat, Telegram, or `openclaw agent --message`), and confirm it appears — with correct attribution — at every link: channel → gateway.log/session JSONL → daemon ingest → DuckDB → the handler → the rendered tab (and, for cloud, the snapshot). If any node stays empty (e.g. Gateway empty, WebChat shows no messages), that is the bug; static data that "looks right" is not a pass. This is the same spirit as the **Live OpenClaw E2E (real gateway)** CI job and the "no synthetic seeds" initiative — synthetic data is acceptable ONLY for isolated unit tests, never to claim a user-facing feature works. Before claiming a data/observability feature works: prove it with a message you actually sent.

> ## ⚡ Performance is a feature — and a cost (non-negotiable)
> **The app must stay snappy and cheap to run. At $9/node/mo we cannot make hundreds of API calls per minute.** Every poller and every fetch is money. Treat request volume like a budget you can blow.
> - **Share, don't duplicate:** one fetch of a shared blob (e.g. the 173 kB `system-snapshot`) serves all consumers — cache it with a TTL + in-flight dedup. Never let N components each re-fetch the same thing (we shipped exactly that bug: 7 interceptors × the snapshot = ~17 fetches/cycle → cut to ~2).
> - **Scope to the screen:** only the active tab polls its own data. Gate heavy pollers on the current tab and pause them off-tab (and when the browser tab is hidden). The Overview fan-out (`loadAll`) must not fire on the LLM Context screen.
> - **Cache + dedup by default:** respect TTLs, dedup in-flight requests, prefer one batched call over many.
> - **Before adding any poller/fetch, ask:** does this need to run on *every* tab? every *N* seconds? can it reuse an existing fetch or the snapshot?
> - **Measure before shipping:** open the Network panel / Resource Timing and confirm no endpoint is fetched N× per cycle and no background poller fires off its own screen. "It works" is not enough — "it works without a request storm" is the bar.

> ## Multi-runtime: ClawMetry observes 22 agent runtimes, not just OpenClaw (non-negotiable)
> **ClawMetry is runtime-neutral. It observes 22 AI agent runtimes, not OpenClaw alone.** Free on every plan: **OpenClaw, NVIDIA NemoClaw**. Also supported: **Aider, Antigravity, Claude Code, Codex, Cursor, Deep Agents, DeepSeek Harness, Exo, GitHub Copilot, Goose, Grok, Hermes, n8n, NanoClaw, opencode, Pi, PicoClaw, QM, Qwen Code**. The enabled set is live at `GET /api/runtimes` (authed); read it, never hardcode a stale copy. The *count* in prose is derived from `FREE_RUNTIMES | PAID_RUNTIMES` and enforced by `scripts/sync_runtime_count.py` (see section 2a).
> - **User-facing copy and UI must never imply OpenClaw-only.** Framing like "designed for OpenClaw agents", "your OpenClaw machine", "No OpenClaw detected", or "Looking for OpenClaw activity" is a bug. Use runtime-neutral language ("your AI agent", "the machine your agent runs on") or name the runtimes ("OpenClaw, NVIDIA NemoClaw + 10 more runtimes", matching the homepage install card). Naming runtimes is public; pricing and tier internals stay private.
> - **Verify across all 22 runtimes, end to end.** Never ship a change verified only on OpenClaw. Use a `/workflow` to fan out a per-runtime E2E check: one agent per runtime that installs or configures it, runs a real turn, and asserts it lands correctly (in Brain by agent_type, in the right tab, with cost and tokens). "Works on OpenClaw" is not "works".
> Burned 2026-06-01: the docs FAQ said "ClawMetry is designed for OpenClaw agents" and the cloud empty-states plus the radar assumed OpenClaw-only. Many surfaces still need this sweep; when you touch a screen, fix its runtime framing.

---

## 0. Before you touch anything

1. **Scan open issues/PRs for human claims.** If a human said "picking this up" / "working on" / "I'll take" in the last 7 days, do NOT open a competing PR. Automation is the night-shift janitor, not the day-shift engineer.
2. **Scan the user's recent comments** on open PRs/issues and address them first.
3. **Re-read the goal.** If invoked via `/goal`, the goal persists until the *outcome* is achieved and verified — not until the code is written.
4. **Work in an isolated worktree.** Multiple Claude Code agents and crons run against this repo at the same time. Editing the main checkout is unsafe: another process can switch branches mid-edit and clobber uncommitted changes (burned 2026-05-28 — `feat/asset-registry` working-tree wiped when a concurrent agent checked out `release/hash-chain-2210` in the same checkout). Always start with `EnterWorktree`, or `git worktree add .claude/worktrees/<slug> -b feat/<slug> origin/main`. The worktree gives you your own branch + working tree; the shared checkout is for the human, not for parallel automation. Use `ExitWorktree` (or `git worktree remove`) once the PR is merged.
5. **Survey what exists, then deep-research the robust way — never reinvent or ship a hack.** Before building detection/integration work (especially anything OS- or runtime-specific), first check for a proven open-source solution and reuse/reference it (e.g. **ccusage** already maps 15+ AI-CLI runtimes' local-data paths cross-platform — reference its source, don't re-derive). When you genuinely must build, deep-research the *authoritative* cross-platform approach — macOS **and** Windows **and** Linux, with cited sources — and design for an `unknown` fallback. A single-platform hack (e.g. a macOS-Keychain-only check) or a fragile heuristic that breaks on another OS/version is **not "done"** — it's a regression waiting to ship. Order of preference: **reuse a maintained project > documented robust cross-platform build > hack (never)**.

## 0a. The bug-free bar: the hosted trial IS the product (HARD GATES)

A trial user converts to paying ONLY if the hosted dashboard is flawless during their trial. One blank card, one wrong number, or one console error reads as "this is broken" and they churn. We are past hacky software. The following are HARD GATES, not suggestions: a change that cannot pass them does not merge.

1. **Cloud parity is mandatory.** The hosted dashboard (app.clawmetry.com) is E2E: the cloud server has NO local DuckDB, so any `/api/X` a card fetches returns EMPTY on cloud unless a `cm-cloud-*` interceptor serves it from the snapshot. Every new card/tab that fetches data MUST ship either (a) a `cm-cloud-*` interceptor reading a snapshot slice the daemon actually emits, OR (b) a deliberate, honest empty/locked state. NEVER a card that silently renders blank / `--` / "no data" on the hosted dashboard. (Burned repeatedly: cards built local-only render blank in the trial.)
2. **Per-runtime honesty (no silent node-wide).** Any number shown while the runtime switcher is set to a specific runtime MUST either scope to that runtime (loader passes `_cmRuntimeFilter()` → snapshot `xByRuntime` slice → interceptor reads `?runtime=`) OR carry a visible "node-wide / all runtimes" label. A card that silently shows node-wide data under a runtime filter is a bug. (Burned 2026-06-06: the Overview outcome tile + activity strip showed identical numbers for every runtime.)
3. **"Done" = verified in the SERVED artifact, not "merged".** Before claiming a frontend change live or pinning cloud, fetch the SERVED file and confirm the change is in it: `curl .../static/js/app.js | grep <marker>`, decrypt the snapshot for a new key, or crack the published wheel (`zipfile`) and grep it. A concurrent `[RELEASE]` can bump the version PAST your feature commit, so the published wheel lacks your change. (Burned 2026-06-06: 0.12.453 shipped WITHOUT the scope banner; it was actually in 0.12.454. Pin cloud to the version whose wheel you verified, not the one whose `[RELEASE]` PR you opened.)
4. **No dead UI.** `dashboard.py` defines `DASHBOARD_HTML` twice; only the SECOND renders (it `{% include %}`s `templates/tabs/*.html` + `partials/*.html`). New UI lives in the LIVE templates and is PROVEN by a Jinja render (or a served-HTML grep), never assumed. An element only in the dead first block never renders.
5. **Verify before you assert (RULE #1, strict).** Never state a number, a config state ("the secret is set"), or "it works" without reading the actual artifact / run log / decrypted data. An unverified claim that turns out false is a bug shipped straight to the user's trust. (Burned 2026-06-06: claimed "CI secrets unset / turns skipped" - they were set and turns ran; and "0.12.453 has the banner" - it did not.)
6. **Walk the trial path before you ship.** For any user-facing change: open the HOSTED dashboard as a trial user, switch runtimes, click the tab, and confirm zero blank/wrong/error states and a clean browser console. If you cannot walk it, you are not done.

## 0b. Desktop installers are a high-priority ROI lever (HARD BAR)

Founder call 2026-08-08: the desktop app (`desktop/`) is one of the highest-ROI things in this repo — one download that observes every AI-CLI runtime on a machine (Claude Code, Codex, Cursor, OpenClaw, Hermes, …), no curl, no terminal. That promise is worthless if the download itself is janky. Each of the three platforms is a HARD BAR, not a nice-to-have:

1. **Every platform ships its own real, native installer/executable — not a bare archive.** Windows gets a proper `.exe` installer (Start Menu shortcut, uninstaller registered in Add/Remove Programs), macOS gets a `.dmg` with a drag-to-`/Applications` affordance, Linux gets a self-contained `.AppImage` (no root, no distro-specific package manager assumption) at minimum, with `.deb`/`.rpm` as a stretch for native package-manager installs. A `.zip` or a bare `.tar.gz` of a PyInstaller one-folder build is **not** a shipped installer — it's a build artifact that leaked onto the download page (this happened: Windows shipped a `.zip` for months, and the Linux CI job is literally named "Linux single-folder + AppImage" but only ever emitted a `.tar.gz` — the AppImage step was never written).
2. **Stable, version-less download URLs per platform** (`desktop/README.md`'s convention: a fixed-name copy alongside the versioned one, both on the same GitHub Release, so `.../releases/latest/download/<fixed-name>` never needs updating). Every new installer format gets its own fixed name and its own row in clawmetry-landing's `_DESKTOP_DOWNLOAD_URLS`.
3. **Build locally before trusting CI.** `makensis` (NSIS) and `appimagetool` can both be exercised in a plain Linux sandbox without a Windows/Linux-GUI machine — compile the script / validate the AppDir structure before pushing, don't find out from a red Windows/Linux runner 8 minutes later.
4. **Stability over speed.** These installers are a stranger's first impression of the product on a machine you don't control — antivirus-flagged, SmartScreen-warned, or "app can't be opened because it is from an unidentified developer" all read as "this is a scam," not "unsigned OSS binary." Code-signing (Windows Authenticode, macOS Developer ID notarization — the pipeline is wired for BOTH; Windows activates when the `WINDOWS_CERT_PFX_BASE64`/`WINDOWS_CERT_PASSWORD` secrets are set) closes that gap; until a cert exists, the installer copy must say so honestly rather than pretend it's signed. On Windows the stakes are higher than a SmartScreen warning: Smart App Control in enforce mode blocks the unsigned NSIS uninstaller's `%TEMP%` relaunch, so the app cannot be uninstalled from Settings > Apps (lab repro 2026-08-10) — and the uninstaller can ONLY be signed at makensis time (`!uninstfinalize`), because `WriteUninstaller` regenerates `Uninstall.exe` from the embedded stub on every (re)install.
5. **Verify the artifact, not the build log.** "CI went green" is not "the installer works" — actually download the produced `.exe`/`.dmg`/`.AppImage` from the release URL and confirm its byte size and (where testable) that it runs, same evidentiary bar as §0a.5.

## 1. The data-flow rule (this is the one that bites)

ClawMetry is **DuckDB-first** (and a control plane that defaults to observation — it is *not* read-only; see CLAUDE.md Conventions):

- Every feature persists to and reads from the local **DuckDB** store. Reading raw JSONL, log files, `sessions.json`, or process stats *inside a request handler* is a violation — it works locally and silently returns empty in cloud (the cloud container has no `~/.openclaw` filesystem). Most "works locally, broken in cloud" bugs are exactly this.
- The blessed path for anything the cloud needs to display:
  ```
  jsonl/gateway  →  daemon ingest  →  DuckDB  →  (sync_system_snapshot)  →  encrypted snapshot  →  Redis  →  cloud decrypts client-side & renders
  ```
- The daemon **owns the DuckDB writer lock**. Build snapshot data on the daemon's **own** store handle (`local_store.get_store()`), never a `read_only=True` re-open — that deadlocks the writer (the `#1771` brick-lock: a cached RO handle blocks every subsequent write; symptom is `cannot open writer — read-only handle already exists`). When you need a read in a separate process, go through the daemon's `/__local_query__/<method>` HTTP proxy (`local_store_via_daemon`), not a direct open.
- If the agent runtime's **model** is needed (e.g. Self-Evolve), don't try to make ClawMetry call an LLM or get gateway write scope — it's read-only by design and its gateway token is `operator.read` only. Shell out to **`openclaw agent --session-id <stable> --message <prompt> --json`**: OpenClaw runs the turn on its own credentials, the transcript lands on disk → DuckDB, and you parse the result. (`openclaw` is a Node script — under the daemon's launchd PATH `node` isn't found, so pass an augmented `PATH` to the subprocess.)

### Snapshot slices the DESK DEVICE consumes are a 4-repo chain

`sync.py::_build_device_summary` builds the **encrypted** `deviceSummary` the ESP32 device decrypts on-device (e.g. `sessionTitles` — keyed by bare session id, content stays out of the cloud plaintext). A new/changed device slice silently no-ops unless the **firmware also renders it**. Device-facing features span FOUR repos and ALL must ship together:
`clawmetry-pro` (adapter derives the value, e.g. claude_code ai-title → `Session.title`) → **this repo** (`sync.py` bakes the encrypted slice) → `clawmetry-cloud` (serves the pro wheel daemons auto-provision + relays the snapshot) → `clawmetry-hardware` (firmware decrypts + renders). Verify BOTH ends: decrypt the live snapshot (§3 verify-live) *and* confirm the firmware renders it (flash/OTA). Burned 2026-06-09: a new device slice showed nothing because the firmware PR was unmerged, and the title was wrong because the pro wheel wasn't rolled to the cloud.

## 1b. Open-core code placement — where does this change go?

ClawMetry is open-core. There are **four repos**, each with a clear remit; agents must pick the right one *before* writing code or the change ships in the wrong tier. Strategy + matrix: `clawmetry-cloud/docs/TIERING_AND_LICENSING.md` (private).

| Repo | Visibility | Holds |
|---|---|---|
| **clawmetry** (this repo) | **Public OSS** | OpenClaw runtime + NeMo governance + 21 chat-channel adapters + entitlement gate (`clawmetry/entitlements.py`) + license client (`clawmetry/license.py`) + **hook points / stubs** for every gated feature. |
| **clawmetry-pro** | **Private** (not on public PyPI; served only to activated installs by the license server) | The gated runtime adapters (Claude Code, Codex, Cursor, Aider, Goose, opencode, Qwen Code, Hermes, PicoClaw, NanoClaw) and the Pro paid CLI / analytical features. Plugs into OSS via the `clawmetry.extensions` entry point. |
| **clawmetry-cloud** | Private | Cloud SaaS server + license server (`/api/license/*`) + Stripe + admin + heartbeat-relay + the closed-wheel hosting (`wheels/` baked into the Cloud Run image). Business + revenue + funnel docs (private). |
| **clawmetry-landing** | Private repo, public site `clawmetry.com` | Marketing + pricing page + public Buy buttons + installer script. Storefront only; no gated code. |

### Decision tree (do this before opening a PR)

1. **A new agent-runtime adapter** (something OpenClaw-shaped that emits sessions/events from a *different* harness — Codex/Cursor/etc.) → **clawmetry-pro** (`clawmetry_pro/adapters/<runtime>.py`), registered in `clawmetry_pro.__init__._PAID_ADAPTERS`. Import only `from clawmetry.adapters.base import …` — never an OSS sibling adapter — so the file stays valid when OSS strips its bundled copies at enforce.
2. **An advanced / paid feature** (custom alerts, multi-node fleet, anomaly detection, Self-Evolve, cost optimizer) → implementation in **clawmetry-pro**; OSS may ship a thin stub route guarded by `entitlements.get_entitlement().allows_feature(<key>)` that defers to the plugin when present and returns an upgrade CTA otherwise.
3. **An Enterprise feature** (OTel export, SSO, audit logs, RBAC, air-gapped license) → OSS route, **entitlement-gated** (`allows_feature('otel_export'|'audit_logs'|'sso'|'rbac'|…)`). Examples already merged: `routes/otel_export.py`, `routes/audit.py`. Grace mode is permissive; enforce returns HTTP 402 `upgrade_required`.
4. **A billing / Stripe / license / wheel-serving endpoint** → **clawmetry-cloud** `routes/`. Cloud-native routes need no `cloud_route_policy` entry; remember to exempt public ones (`/api/license/*`) from the `cm_`-key gate in `dashboard.py:before_request`.
5. **Marketing / pricing / public copy / Buy button** → **clawmetry-landing**. i18n via `data-i18n` (missing keys fall back to English). No em-dashes in user-facing copy. Proactive screenshots on every landing PR.
6. **Core OpenClaw observability** (anything OpenClaw-shaped, NeMo governance, chat-channel adapters, the dashboard tabs that serve OpenClaw data) → **stays in OSS** (this repo). Free in every tier.

### Hard rules that fall out of the split

- **OSS routes for gated features must call `entitlements.allows_feature(...)`** and return HTTP 402 (`upgrade_required`) when blocked. Never silently disable — the upgrade prompt is the conversion moment.
- **Plugin override seam.** `dashboard.py` family-adapter loop must skip when `registry.get(name) is not None` (clawmetry-pro registered it first). Tested by `tests/test_adapter_registry_override.py`. Don't reintroduce a clobber.
- **`load_plugins()` is already wired at `dashboard.py:162`** (import time) and works on Python 3.9+ via `_select_entry_points` — don't roll your own.
- **The signing keypair.** PUBLIC Ed25519 key is embedded in `clawmetry/license.py` *and* `clawmetry-cloud/routes/license.py`. PRIVATE key lives ONLY in `clawmetry-cloud/secrets/license_signing_key.pem` (gitignored) + the `license-signing-key` Cloud Run Secret Manager entry. Rotating means bumping both embedded constants + an OSS release.
- **Closed wheel distribution.** `clawmetry-pro` builds → wheel committed to `clawmetry-cloud/wheels/` (private repo) → `.dockerignore` allowlist must include `wheels/` and `wheels/**` (allowlist-style; new top-level dirs silently 404 without it) → `COPY wheels/ wheels/` in Dockerfile → `/api/license/download` streams it gated by activation. Never expose the wheel via a public URL.
- **Business numbers stay private.** Pricing, MRR, funnel, conversion roadmaps → `clawmetry-cloud/docs/` only. Public OSS docs can mention features but never prices/funnels.

## 1c. The runtime-filter rule (every runtime, every view, server-side)

When the global runtime switcher is set to a runtime, **every view must show ONLY that runtime's data**. The *only* thing that changes between runtimes is the `runtime=<id>` parameter; all numbers, lists, charts, and headers must re-derive from the filtered response. A view that keeps showing node-wide totals while the switcher says "PicoClaw · 1 session" is a **bug**, not a cosmetic note. (Burned 2026-06-03: the node-detail Overview header showed 68 sessions / 3.8M tokens / claude-opus-4-8 with PicoClaw selected.)

- **The public v1 API is the filtering contract.** `https://app.clawmetry.com/api/v1/*` filters server-side by `?runtime=<id>` — verified: `/api/v1/usage?runtime=claude_code` → that runtime's tokens/cost; `/api/v1/sessions?runtime=picoclaw` → only its sessions; `/api/v1/nodes/<id>/runtimes` lists the per-runtime counts. **Prefer sourcing runtime-scoped data from the v1 API** (or a snapshot slice that is *already* per-runtime) over client-side filtering.
- **Client-side filtering of a pre-aggregated blob silently no-ops.** The `_CM_RT_AGGREGATE` tabs (Overview header, Cost, Models, LLM Context, Tool Catalog) can't scope a node-wide snapshot client-side, so they fall back to an honest "all runtimes" note instead of pretending — but the real fix is server-side filtering, not the note. Never ship a new view that "filters" by slicing a merged blob in JS.
- **Two-renderer mirror.** If the same data has two renderers (e.g. a list and a chart), BOTH must apply the runtime filter or the chart fills while the list empties. CI guard: `tests/test_runtime_filter_no_leak.py` (server-side no-leak) + assert both render functions reference the filter.
- **Verify per runtime, not just one.** Picking one runtime and eyeballing it is not enough — a filter that hard-codes the first runtime passes that check. For each runtime in `/api/v1/nodes/<id>/runtimes`, hit the v1 endpoints with `runtime=<id>` and assert the response scopes (counts match the runtimes list; `claude_code` ≠ `picoclaw`; an absent runtime returns zero, not the node total). The helper `scripts/verify_runtime_filtering.py` does this sweep — run it before claiming a runtime-aware view works, and wire it into the per-runtime E2E matrix (see [`feedback_workflows_all_runtimes_e2e`]).

## 1d. Don't let an LLM analyze a fact the code declares — extract it, then judge

When a decision depends on a fact the codebase **declares** (a `Capability` enum, a config constant, a route-policy entry, a DB schema, a pinned version, the pricing table), **EXTRACT it deterministically** — never ask an LLM (or a workflow agent) to "analyse" it from prose. LLMs hallucinate facts. Burned 2026-06-03: a `/workflows` agent called NemoClaw a "NeMo toolkit" when it is **sandboxed OpenClaw** (runs the OpenClaw adapter); the derived per-runtime tab config inherited the error and reached `main` before the founder caught it.

- **Derive from the contract.** The per-runtime sidebar tabs DERIVE from each adapter's declared `Capability` enum (`_CM_RT_CAPS` ← `grep Capability. <adapter>`), so a new runtime/capability flows automatically and nothing can drift it. Prefer "derive from the declared source" over "hand-maintain a list."
- **LLM-as-judge is for JUDGMENT, not facts.** When the question is genuinely judgmental (not extractable), the pattern is: extract the ground-truth facts → the LLM proposes → an **independent judge verifies the proposal against those facts and rejects on contradiction** (e.g. "agent says NemoClaw lacks CRONS, but it runs the OpenClaw adapter which declares `CRONS` → contradiction → reject"). A workflow that fans out analysis MUST add this verify/judge phase; never let an agent's prose be the source of truth for an extractable fact.
- **Guard with an eval.** Add a CI test that re-extracts the fact and asserts the derived artifact matches (`tests/test_runtime_tab_capability_parity.py`), so correctness is mechanical, not "trust me."

## 1e. The CPU budget: the daemon stays light (target <=5-10%)

ClawMetry runs on the user's machine 24/7. It is an observability **sidecar**, not a warehouse, and must be nearly invisible. **Hard budget: the sync daemon idles near 0% and averages no more than ~5-10% of one core.** A daemon that sustains a whole core is a bug, not "busy working." (Burned 2026-06-06: a 12-core box sat at ~200% CPU because DuckDB defaulted to all 12 threads AND the dashboard re-ran a full-table aggregate on every poll. Profile was ~100% inside the DuckDB allocator + `BufferPool::EvictBlocks` thrash.)

Hold the line with:
- **Cap DuckDB.** Every connection passes `config={threads, memory_limit}` (defaults 2 / 2GB; env `CLAWMETRY_DUCKDB_THREADS` / `CLAWMETRY_DUCKDB_MEMORY_LIMIT`). DuckDB's default `threads` equals the core count, so an uncapped query fans across the whole machine. Never ship an uncapped connection.
- **No full-table scan per request.** Hot rollups (`query_aggregates`, snapshot / overview / cost queries) are result-cached with a short TTL (`CLAWMETRY_AGG_CACHE_TTL`, default 20s). The daemon recomputes on a timer; handlers read the cache. The thread cap alone does NOT fix average CPU (same total work, fewer cores), only fewer runs do.
- **Poll in seconds-to-minutes, never sub-second.** The daemon wakes, works, then sleeps.
- **Profile before shipping anything on the ingest / query / snapshot path.** `sample <pid> 4` (macOS) or py-spy. If it sustains more than ~1 core, it does not ship. Guard the caps + cache with a regression test so it stays mechanical.

## 1f. Keep Software Factory in sync (Drift Bot)

This repo (and `clawmetry-cloud` / `clawmetry-pro` / `clawmetry-mac` / `clawmetry-railway`) is tracked in [8090 Software Factory](https://factory.8090.ai) as the "ClawMetry" project: Requirements and Blueprints describing what the product does and how. A `drift-bot` GitHub status check runs on every PR and posts an inline comment when the code says something the Blueprints/Requirements don't. Real example: PR #4599 shipped the installer's stale-duplicate sweep and documented it in `CHANGELOG.md`, but no Blueprint said the installers clean up other Python interpreters on PATH, so Drift Bot failed the PR.

**`CHANGELOG.md` is not enough.** Drift Bot reads Blueprints/Requirements, not the changelog. Before merging a change that alters documented (or should-be-documented) product behavior:
- Check whether an existing Blueprint covers the area you touched; if your change makes it wrong or incomplete, update it.
- If no Blueprint covers it yet, say so in the PR description so a human (or the next agent) creates one — don't let it merge silently undocumented.
- The dashboard's "Sync Blueprint with Code" agent action (or the Software Factory MCP skill, `npx skills add 8090-inc/software-factory-plugin`) can do this for you; point it at the specific PR/CHANGELOG entry rather than asking for a blanket sync of everything.
- A red `drift-bot` check is a real signal like any other CI failure (§4) — fix the documentation gap, don't merge past it.

Separately, **check [Pending Work Orders](https://factory.8090.ai) regularly**, not just when drift-bot fires. Work Orders are the actual tickets Software Factory queues from Requirements/Blueprints; picking them up (not just reacting to drift after the fact) is how the docs and the code stay one thing instead of drifting apart again next week.

## 2. Make the change

- New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. Shared helpers reach back via late `import dashboard as _d`.
- Embedded frontend lives in `dashboard.py` template strings AND in `clawmetry/static/` + `clawmetry/templates/`. Note: `dashboard.py` defines `DASHBOARD_HTML` twice — the **second** wins and loads `static/css/dashboard.css` + `templates/tabs/*.html`. The inline `<style>`/HTML earlier in the file is dead. Edit the static/template files.
- Match surrounding style: `snake_case` funcs, minimal deps (Flask + waitress + cryptography), never crash on bad input (graceful fallbacks + a logged warning).
- **No em-dashes (`—`, U+2014), no double-dashes (`--`), no `X, Y, and Z [emdash] coda` pattern in user-facing copy.** That pattern is an AI-tell, and the user has explicitly banned it. Applies to: landing HTML, dashboard banners, marketing copy, blog posts, CHANGELOG release entries, bounty and job posts (incl. external platforms like rentahuman.ai), public docs, email templates, modal copy, and any PR description users see. Allowed in: code comments, internal notes in `docs/`, commit messages, and internal-only PR bodies. Use a comma, parenthetical, colon, or full stop instead. **Belt-and-braces:** before sending any user-facing text (a PR via someone else's API, a CHANGELOG entry, landing copy, modal text), grep the payload for `—` or `--` and refuse to send if matched. Burned twice: 2026-05-26 on landing PR #211 (em-dashes in marketing copy), 2026-05-28 on the rentahuman.ai bounty redraft (em-dashes everywhere despite the rule being in memory, so the user had to re-flag it).
- **Keep business internals out of this public repo.** This repo is public — investors, competitors, and prospective hires browse it. Any doc with live revenue/MRR/funnel/conversion numbers or monetization/pricing strategy (conversion roadmaps, conversion PRDs, pricing analysis) goes in **`clawmetry-cloud/docs/` (private), NEVER `clawmetry/docs/`**. Same rule as `[intel/*]` issues. Before creating any doc, ask: would this leak positioning, lead pipeline, or revenue if a competitor read it? If yes → private repo. (Burned 2026-05-26: a conversion roadmap + PRDs with the real paying-customer/MRR funnel were written into public `docs/` and had to be relocated.)

## 2a. Adding a runtime: every surface, every repo, ONE sprint (canonical checklist)

A runtime is "supported" only when it exists on **every** surface below, in all four
repos, and is verified live. Half of it shipping is worse than none: the product says
21, the homepage says 20, the README lists it unlinked, and `/runtimes/<slug>` is a 404.
**Burned 2026-08-17 (Exo):** adapter, OSS wiring, `[RELEASE]` 0.12.726, cloud pin,
`/api/runtimes` = 21 — all done — and the storefront never followed for a day. The
product half of the flywheel had run; the storefront half had not. This section is the
canonical list; `clawmetry-pro`, `clawmetry-cloud`, and `clawmetry-landing` FLYWHEELs
point here and carry only their own slice.

Order of operations (each step is a PR that merges before the next starts):

**1. `clawmetry-pro` — the adapter (private).**
`clawmetry_pro/adapters/<runtime>.py` (self-contained, base SDK only), `_PAID_ADAPTERS`
entry, REAL fixture under `tests/fixtures/runtimes/<rt>/REAL/` with a README naming how
it was captured, `RuntimeSpec` + a matrix leg in `runtime-conformance.yml` (the matrix is
hardcoded, not derived), unit tests over the real file shapes (empty, torn tail, dup /
replayed events, fork/subagent lineage, cost ladder). Bump `pyproject` + `__version__`
in lockstep. Verify with an isolated ingest, not the daemon proxy (see memory
`exo-runtime-adapter-shipped`).

**2. `clawmetry` (this repo) — wiring + count + public contract, then `[RELEASE]`.**
| Surface | What to touch |
|---|---|
| Catalogue | `clawmetry/entitlements.py`: `PAID_RUNTIMES` (or `FREE_RUNTIMES`), `RUNTIME_LABELS`, **`RUNTIME_LANDING_PATHS`** (`/runtimes/<slug>`, the public page this runtime WILL have). |
| Ingest | `clawmetry/sync.py` family loop (label map + store-root discovery + `CLAWMETRY_<RT>_*` env override), `clawmetry/runtime_probe.py`, `clawmetry/runtime_memory.py` (memory/skills catalog), `clawmetry/numbat_ingest.py` aliases, `routes/harness.py`, `routes/usage.py`, `routes/attention.py`; a new provider → `clawmetry/providers_pricing.py`. |
| UI | `clawmetry/static/js/app.js`: every runtime map (`_CM_RT_PREFIXES`, labels, icons, `_CM_RT_CAPS`, the harness card map at the `deepseek_harness:` anchors — grep the previous runtime's id and mirror EVERY hit; qm was missed in `_CM_RT_PREFIXES` once). |
| Count | run `python3 scripts/sync_runtime_count.py` and commit what it rewrites (README, translations, FLYWHEEL, ARCHITECTURE, CLI, desktop onboarding, device page). `setup.py` derives the PyPI summary itself. |
| README grid | add `EMOJI **[Label](https://clawmetry.com/runtimes/<slug>)**` to the "Works with N agent runtimes" line — LINKED, never bare bold. |
| Docs | `docs/ENTITLEMENTS.md` runtime list; `docs/RUNTIME_SCREENSHOTS.md` + `screenshots/runtimes/<rt>/` once a real capture exists (staging recipe in memory `runtime-screenshot-gallery-staging-recipe`); `CHANGELOG.md` entry (no em-dashes). |
| Tests (count pins that break) | `tests/test_entitlements.py::test_paid_runtimes_exact_membership`, `tests/test_phase4_adapter_move.py`, `tests/test_advertised_runtimes_match_catalogue.py`, `tests/test_runtime_count_copy_sync.py`, **`tests/test_runtime_public_surfaces.py`** (README grid links every catalogue runtime; `CLAWMETRY_LIVE_CHECKS=1` also asserts each page is 200 on clawmetry.com). |
| Ship | `[RELEASE]` PR → PyPI; crack the wheel and grep for the runtime id before you pin it anywhere. |

**3. `clawmetry-cloud` — serve it.** Roll the pro wheel (`_pro_wheel_path`), bump the
`clawmetry==X` pin, deploy, then verify live: `GET /api/runtimes` includes the id and
`/api/license/download` serves the pro version that carries the adapter.

**4. `clawmetry-landing` + this README — the storefront (same day as step 3).**
`runtimes-<slug>.html` themed to the vendor's own palette/type, `app.py` route,
`sitemap_gen.py`, homepage `.rt-cloud` tile + tooltip enumeration, chip on every other
runtime page, the fleet count everywhere it is quoted (connect, pricing, control tower,
how-it-works, agent-builder, push, device, llms.txt, `locales/en.json`),
`docs/PUBLIC_CLAIMS.md` §3.1 with a dated "Reconciled" line, and the guard
`tests/test_pages.py::test_runtime_surfaces_are_in_lockstep`. Then run
`CLAWMETRY_LIVE_CHECKS=1 pytest tests/test_runtime_public_surfaces.py` here: every
`RUNTIME_LANDING_PATHS` entry must be 200 on clawmetry.com. Also `gh repo edit
--description` if the count is in it, and any awesome-list / directory entries you own.

**5. Verify like the founder will:** open the homepage grid, click the new tile, open
the dashboard with the runtime switcher on the new runtime, screenshot all three, and
put them in the PRs. If you cannot show the tile, the page, and the data, it did not ship.

### The count is derived, never hand-edited

`FREE_RUNTIMES | PAID_RUNTIMES` in `clawmetry/entitlements.py` is the **only**
place the supported-runtime set is declared. Everything that quotes a number
hangs off it:

| Surface | How it stays true |
|---|---|
| PyPI summary (`setup.py`) | **Derived.** `setup.py` parses `entitlements.py` at build time, so it cannot drift. |
| README, translations, FLYWHEEL, ARCHITECTURE, AUDIT, CLI, desktop onboarding, device page | **Rewritten** by `python3 scripts/sync_runtime_count.py`. |
| README runtime grid links | **Enforced** by `tests/test_runtime_public_surfaces.py` against `RUNTIME_LANDING_PATHS`. |
| All of the above | **Enforced** by `tests/test_runtime_count_copy_sync.py`, which fails CI on drift. Also runs via `make lint`. |
| Landing pages | **Enforced in `clawmetry-landing`** by `test_runtime_surfaces_are_in_lockstep` (derives the fleet from `runtimes-*.html`); cross-checked from here by the opt-in live test above. GitHub repo description: `gh repo edit --description` by hand in the same sprint. |

If a number in prose legitimately is *not* the supported-runtime count (a free-tier
count, a dated research note, a capacity estimate), add it to `EXEMPT` in the script
with the reason. Do not reword the prose to dodge the regex.

Burned 2026-08-15: the catalogue said 20 while the README said 14, PyPI said 12, and
FLYWHEEL said 12, across 27 stale mentions in 16 files. Maintainers of external lists
click through, and a PyPI page contradicting the homepage is the kind of thing that
gets a submission closed.

## 3. Verify locally BEFORE the PR (the loop that actually catches bugs)

The daemon does **not** run the repo — it runs a copy in `~/.clawmetry/lib/pythonX.Y/site-packages/clawmetry/` (a venv with no pip). Editing the repo + restarting does nothing. To test daemon code:

```bash
SP=~/.clawmetry/lib/python3.11/site-packages/clawmetry
cp clawmetry/sync.py "$SP/sync.py"          # copy EACH changed file
rm -f "$SP/__pycache__/sync"*.pyc           # clear stale bytecode (it can shadow your .py)
launchctl kickstart -k gui/$(id -u)/com.clawmetry.sync   # restart the sync daemon
```

Then prove the data actually flows by **decrypting the live cloud snapshot** (this is the real E2E check, not a synthetic test):

```python
# reads ~/.clawmetry/config.json for node_id + api_key + encryption_key,
# GETs https://app.clawmetry.com/api/cloud/system-snapshot, AES-256-GCM decrypts
# (nonce = first 12 bytes), and asserts your new key is present + correct.
```

Gotchas that have burned us:
- **Synthetic tests pass while real data flunks.** OpenClaw v3 normalises event types (`message`→`prompt.submitted`/`model.completed`, etc.). Always smoke against the live DuckDB, not hand-crafted fixtures.
- **DuckDB writer-lock contention.** If the daemon logs `ANOTHER PROCESS HOLDS THE DUCKDB WRITER LOCK`, a stray `dashboard.py --port 89xx` dev server grabbed it. Kill the strays, then restart the daemon so it reclaims the writer.
- **Restart BOTH** the dashboard and the sync daemon after an upgrade — the daemon keeps the old wheel in memory otherwise.
- When you claim "works locally," confirm you're testing **repo HEAD on a known port**, not a stale long-running server.

### Ruthless-verify non-negotiables (family-wide rule, synced across all repos)
We ship many products and many features now; "it has tests" is not "it is tested." Hold this bar on
EVERY change:
- **Every fix ships the guard that catches it, in the SAME PR**, and you prove the guard fails on the
  un-fixed code (revert → red → restore → green). A fix without a regression test/guard is half-done.
- **Update tests as fixes/features land** — never "fix and move on." Prefer guards that AUTO-DISCOVER
  their scope over hand-maintained allowlists, which silently drift (a cloud inline-JS allowlist missed
  the /pair page → a JS SyntaxError shipped; the firmware had no stack-size guard → three stack-overflow
  crashes shipped — both now closed with auto/compile-time guards + revert-proofs, 2026-06-09).
- **Build-clean / green-CI ≠ works.** Verify the real behaviour end-to-end (decrypt the live snapshot;
  render the tab in a browser; flash + see it on the device). The worst regressions this session all
  passed their builds and shipped anyway.
- **Audit the whole class, not the one instance.** Fixing one JS-string escape, one stack frame, one
  stale title doesn't fix its siblings — grep the class and verify the family.

## 4. PR → green CI → merge

```bash
git checkout -B feat/<slug> origin/main      # branch off origin/main, never a stale release branch
gh pr create --title "feat: …" --body "…"    # explain WHY + the verification you did
```

- **Never push directly to `main`. No exceptions.** Not for empty re-trigger commits. Not for `Dockerfile` cache-bust comments. Not for one-line CI tweaks. Not for typo fixes. Not even for reverts. Every change goes through a branch + PR + CI, including changes whose only purpose is to nudge CI itself. The 30 seconds a one-line PR costs is the price of every other agent and human being able to trust `main`. If a deploy is stuck and you think the fix is "obvious," that means it is a perfect 1-line PR, not a justification to bypass review. Burned 2026-05-28 on `clawmetry-landing`: I pushed two commits straight to `main` (`a2cfb7b` empty re-trigger and `acfa10e` 2-line Dockerfile cache-bust) framing the urgency of a stuck Cloud Run deploy as license to skip the rule. Both would have taken 30 seconds as PRs. The user rightly called it out.
- End commit messages with the `Co-Authored-By` trailer; end PR bodies with the Claude Code footer.
- **CI must be 100% green before merge — red means it will not deploy.** The matrix includes: Syntax & Lint, API Tests (3 OS), E2E Browser Tests, **Live OpenClaw E2E (real gateway)**, MOAT Verifier + Keystone, Eval Suite Gate, Sync matrix (3 OS × 3 Py), Install/boot/health, wheel/asset presence, pip install, and **`drift-bot`** (Software Factory blueprint/requirement sync, §1f — fix the doc gap, it is not a flaky check to retry).
- A red check is a real signal. **Fix the cause — code or test — never skip or `xfail` to get green.** If a test encodes the wrong expectation (e.g. an IA-v2 rename), fix the test to match reality; read the *rendered* HTML before "fixing" a selector so you don't fix half of it.
- Merge with `gh pr merge <n> --squash --delete-branch`.
- After any cross-cutting fix on main, **rebase every open PR** (`gh pr update-branch`) — "main green" ≠ "PRs green."

## 5. Release to PyPI (`[RELEASE]`)

A feature PR merging to main does **not** publish. Publishing is triggered by merging a **separate PR whose title starts with `[RELEASE]`** — `release-on-merge.yml` then bumps the patch version and uploads to PyPI.

```bash
git checkout -b release/<slug> origin/main
# add a CHANGELOG.md entry under [Unreleased]: why / what / verified
gh pr create --title "[RELEASE] <summary> (carries #<feature-pr>)" --body "…"
```

- **Never** hand-edit `__version__` or push a `v*` tag — the workflow does it.
- `gh pr merge --squash` defaults the commit subject to the *last commit*, dropping the PR title. Pass `--subject "[RELEASE] … (#<n>)"` and **verify** `git log origin/main -1` still starts with `[RELEASE]`, or the release won't fire.
- Wait for `release-on-merge.yml` to finish AND for the new version to appear on PyPI before bumping the cloud pin — there's a propagation race where the cloud Docker build pulls a stale index. Poll `https://pypi.org/pypi/clawmetry/json` for the new version.

## 6. Promote to clawmetry-cloud

Hand off to the cloud repo's `FLYWHEEL.md`. In short: bump `clawmetry==<new>` in the cloud `Dockerfile` *only when the daemon code changed* (a cloud-only render fix that reads an already-shipped snapshot key needs no bump), add the matching `cm-cloud-*` interceptor + route-policy entry, get cloud CI green, and verify the deploy.

## 7. Verify in production (the part that's non-negotiable)

- Decrypt the live cloud snapshot again post-deploy and confirm your data is present.
- Open the actual tab in a browser, confirm it renders, and **attach a screenshot** within ~5 min of merge (especially for any cloud UI surface). The screenshot catches stale-rebase regressions as a bonus.
- Only then say it's done — plainly, with the evidence. If something is partial, say which part and why.

## 8. Judgment

- Decide ship-vs-hold trade-offs yourself; state a one-line rationale and act. Don't bounce routine decisions back to the user.
- When a finding contradicts the premise of a request (e.g. "spawn a gateway session" turns out to need write scope ClawMetry can't have), surface it with evidence and propose the path that actually works.
- Save durable, non-obvious learnings to memory so the next agent doesn't re-burn them.

🤖 Maintained by Claude Code agents. If you discover a new gotcha, add it here.
