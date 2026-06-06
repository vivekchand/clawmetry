# FLYWHEEL.md — ClawMetry

> 🌀 ClawMetry's adoption of the **[FLYWHEEL.md](https://flywheel.md)** convention — the third file in the agent canon: `AGENTS.md` (what to do), `SOUL.md` (who to be), `FLYWHEEL.md` (how to ship). ClawMetry is its first adopter. This is our tailored instance; yours will differ — keep the bar.

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
> **The app must stay snappy and cheap to run. At $19/node/mo we cannot make hundreds of API calls per minute.** Every poller and every fetch is money. Treat request volume like a budget you can blow.
> - **Share, don't duplicate:** one fetch of a shared blob (e.g. the 173 kB `system-snapshot`) serves all consumers — cache it with a TTL + in-flight dedup. Never let N components each re-fetch the same thing (we shipped exactly that bug: 7 interceptors × the snapshot = ~17 fetches/cycle → cut to ~2).
> - **Scope to the screen:** only the active tab polls its own data. Gate heavy pollers on the current tab and pause them off-tab (and when the browser tab is hidden). The Overview fan-out (`loadAll`) must not fire on the LLM Context screen.
> - **Cache + dedup by default:** respect TTLs, dedup in-flight requests, prefer one batched call over many.
> - **Before adding any poller/fetch, ask:** does this need to run on *every* tab? every *N* seconds? can it reuse an existing fetch or the snapshot?
> - **Measure before shipping:** open the Network panel / Resource Timing and confirm no endpoint is fetched N× per cycle and no background poller fires off its own screen. "It works" is not enough — "it works without a request storm" is the bar.

> ## Multi-runtime: ClawMetry observes 12 agent runtimes, not just OpenClaw (non-negotiable)
> **ClawMetry is runtime-neutral. It observes 12 AI agent runtimes, not OpenClaw alone.** Free on every plan: **OpenClaw, NVIDIA NemoClaw**. Also supported: **Aider, Claude Code, Codex, Cursor, Goose, Hermes, NanoClaw, opencode, PicoClaw, Qwen Code**. The enabled set is live at `GET /api/runtimes` (authed); read it, never hardcode a stale copy.
> - **User-facing copy and UI must never imply OpenClaw-only.** Framing like "designed for OpenClaw agents", "your OpenClaw machine", "No OpenClaw detected", or "Looking for OpenClaw activity" is a bug. Use runtime-neutral language ("your AI agent", "the machine your agent runs on") or name the runtimes ("OpenClaw, NVIDIA NemoClaw + 10 more runtimes", matching the homepage install card). Naming runtimes is public; pricing and tier internals stay private.
> - **Verify across all 12 runtimes, end to end.** Never ship a change verified only on OpenClaw. Use a `/workflow` to fan out a per-runtime E2E check: one agent per runtime that installs or configures it, runs a real turn, and asserts it lands correctly (in Brain by agent_type, in the right tab, with cost and tokens). "Works on OpenClaw" is not "works".
> Burned 2026-06-01: the docs FAQ said "ClawMetry is designed for OpenClaw agents" and the cloud empty-states plus the radar assumed OpenClaw-only. Many surfaces still need this sweep; when you touch a screen, fix its runtime framing.

---

## 0. Before you touch anything

1. **Scan open issues/PRs for human claims.** If a human said "picking this up" / "working on" / "I'll take" in the last 7 days, do NOT open a competing PR. Automation is the night-shift janitor, not the day-shift engineer.
2. **Scan the user's recent comments** on open PRs/issues and address them first.
3. **Re-read the goal.** If invoked via `/goal`, the goal persists until the *outcome* is achieved and verified — not until the code is written.
4. **Work in an isolated worktree.** Multiple Claude Code agents and crons run against this repo at the same time. Editing the main checkout is unsafe: another process can switch branches mid-edit and clobber uncommitted changes (burned 2026-05-28 — `feat/asset-registry` working-tree wiped when a concurrent agent checked out `release/hash-chain-2210` in the same checkout). Always start with `EnterWorktree`, or `git worktree add .claude/worktrees/<slug> -b feat/<slug> origin/main`. The worktree gives you your own branch + working tree; the shared checkout is for the human, not for parallel automation. Use `ExitWorktree` (or `git worktree remove`) once the PR is merged.

## 0a. The bug-free bar: the hosted trial IS the product (HARD GATES)

A trial user converts to paying ONLY if the hosted dashboard is flawless during their trial. One blank card, one wrong number, or one console error reads as "this is broken" and they churn. We are past hacky software. The following are HARD GATES, not suggestions: a change that cannot pass them does not merge.

1. **Cloud parity is mandatory.** The hosted dashboard (app.clawmetry.com) is E2E: the cloud server has NO local DuckDB, so any `/api/X` a card fetches returns EMPTY on cloud unless a `cm-cloud-*` interceptor serves it from the snapshot. Every new card/tab that fetches data MUST ship either (a) a `cm-cloud-*` interceptor reading a snapshot slice the daemon actually emits, OR (b) a deliberate, honest empty/locked state. NEVER a card that silently renders blank / `--` / "no data" on the hosted dashboard. (Burned repeatedly: cards built local-only render blank in the trial.)
2. **Per-runtime honesty (no silent node-wide).** Any number shown while the runtime switcher is set to a specific runtime MUST either scope to that runtime (loader passes `_cmRuntimeFilter()` → snapshot `xByRuntime` slice → interceptor reads `?runtime=`) OR carry a visible "node-wide / all runtimes" label. A card that silently shows node-wide data under a runtime filter is a bug. (Burned 2026-06-06: the Overview outcome tile + activity strip showed identical numbers for every runtime.)
3. **"Done" = verified in the SERVED artifact, not "merged".** Before claiming a frontend change live or pinning cloud, fetch the SERVED file and confirm the change is in it: `curl .../static/js/app.js | grep <marker>`, decrypt the snapshot for a new key, or crack the published wheel (`zipfile`) and grep it. A concurrent `[RELEASE]` can bump the version PAST your feature commit, so the published wheel lacks your change. (Burned 2026-06-06: 0.12.453 shipped WITHOUT the scope banner; it was actually in 0.12.454. Pin cloud to the version whose wheel you verified, not the one whose `[RELEASE]` PR you opened.)
4. **No dead UI.** `dashboard.py` defines `DASHBOARD_HTML` twice; only the SECOND renders (it `{% include %}`s `templates/tabs/*.html` + `partials/*.html`). New UI lives in the LIVE templates and is PROVEN by a Jinja render (or a served-HTML grep), never assumed. An element only in the dead first block never renders.
5. **Verify before you assert (RULE #1, strict).** Never state a number, a config state ("the secret is set"), or "it works" without reading the actual artifact / run log / decrypted data. An unverified claim that turns out false is a bug shipped straight to the user's trust. (Burned 2026-06-06: claimed "CI secrets unset / turns skipped" - they were set and turns ran; and "0.12.453 has the banner" - it did not.)
6. **Walk the trial path before you ship.** For any user-facing change: open the HOSTED dashboard as a trial user, switch runtimes, click the tab, and confirm zero blank/wrong/error states and a clean browser console. If you cannot walk it, you are not done.

## 1. The data-flow rule (this is the one that bites)

ClawMetry is **read-only** and **DuckDB-first**:

- Every feature persists to and reads from the local **DuckDB** store. Reading raw JSONL, log files, `sessions.json`, or process stats *inside a request handler* is a violation — it works locally and silently returns empty in cloud (the cloud container has no `~/.openclaw` filesystem). Most "works locally, broken in cloud" bugs are exactly this.
- The blessed path for anything the cloud needs to display:
  ```
  jsonl/gateway  →  daemon ingest  →  DuckDB  →  (sync_system_snapshot)  →  encrypted snapshot  →  Redis  →  cloud decrypts client-side & renders
  ```
- The daemon **owns the DuckDB writer lock**. Build snapshot data on the daemon's **own** store handle (`local_store.get_store()`), never a `read_only=True` re-open — that deadlocks the writer (the `#1771` brick-lock: a cached RO handle blocks every subsequent write; symptom is `cannot open writer — read-only handle already exists`). When you need a read in a separate process, go through the daemon's `/__local_query__/<method>` HTTP proxy (`local_store_via_daemon`), not a direct open.
- If the agent runtime's **model** is needed (e.g. Self-Evolve), don't try to make ClawMetry call an LLM or get gateway write scope — it's read-only by design and its gateway token is `operator.read` only. Shell out to **`openclaw agent --session-id <stable> --message <prompt> --json`**: OpenClaw runs the turn on its own credentials, the transcript lands on disk → DuckDB, and you parse the result. (`openclaw` is a Node script — under the daemon's launchd PATH `node` isn't found, so pass an augmented `PATH` to the subprocess.)

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

## 2. Make the change

- New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. Shared helpers reach back via late `import dashboard as _d`.
- Embedded frontend lives in `dashboard.py` template strings AND in `clawmetry/static/` + `clawmetry/templates/`. Note: `dashboard.py` defines `DASHBOARD_HTML` twice — the **second** wins and loads `static/css/dashboard.css` + `templates/tabs/*.html`. The inline `<style>`/HTML earlier in the file is dead. Edit the static/template files.
- Match surrounding style: `snake_case` funcs, minimal deps (Flask + waitress + cryptography), never crash on bad input (graceful fallbacks + a logged warning).
- **No em-dashes (`—`, U+2014), no double-dashes (`--`), no `X, Y, and Z [emdash] coda` pattern in user-facing copy.** That pattern is an AI-tell, and the user has explicitly banned it. Applies to: landing HTML, dashboard banners, marketing copy, blog posts, CHANGELOG release entries, bounty and job posts (incl. external platforms like rentahuman.ai), public docs, email templates, modal copy, and any PR description users see. Allowed in: code comments, internal notes in `docs/`, commit messages, and internal-only PR bodies. Use a comma, parenthetical, colon, or full stop instead. **Belt-and-braces:** before sending any user-facing text (a PR via someone else's API, a CHANGELOG entry, landing copy, modal text), grep the payload for `—` or `--` and refuse to send if matched. Burned twice: 2026-05-26 on landing PR #211 (em-dashes in marketing copy), 2026-05-28 on the rentahuman.ai bounty redraft (em-dashes everywhere despite the rule being in memory, so the user had to re-flag it).
- **Keep business internals out of this public repo.** This repo is public — investors, competitors, and prospective hires browse it. Any doc with live revenue/MRR/funnel/conversion numbers or monetization/pricing strategy (conversion roadmaps, conversion PRDs, pricing analysis) goes in **`clawmetry-cloud/docs/` (private), NEVER `clawmetry/docs/`**. Same rule as `[intel/*]` issues. Before creating any doc, ask: would this leak positioning, lead pipeline, or revenue if a competitor read it? If yes → private repo. (Burned 2026-05-26: a conversion roadmap + PRDs with the real paying-customer/MRR funnel were written into public `docs/` and had to be relocated.)

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

## 4. PR → green CI → merge

```bash
git checkout -B feat/<slug> origin/main      # branch off origin/main, never a stale release branch
gh pr create --title "feat: …" --body "…"    # explain WHY + the verification you did
```

- **Never push directly to `main`. No exceptions.** Not for empty re-trigger commits. Not for `Dockerfile` cache-bust comments. Not for one-line CI tweaks. Not for typo fixes. Not even for reverts. Every change goes through a branch + PR + CI, including changes whose only purpose is to nudge CI itself. The 30 seconds a one-line PR costs is the price of every other agent and human being able to trust `main`. If a deploy is stuck and you think the fix is "obvious," that means it is a perfect 1-line PR, not a justification to bypass review. Burned 2026-05-28 on `clawmetry-landing`: I pushed two commits straight to `main` (`a2cfb7b` empty re-trigger and `acfa10e` 2-line Dockerfile cache-bust) framing the urgency of a stuck Cloud Run deploy as license to skip the rule. Both would have taken 30 seconds as PRs. The user rightly called it out.
- End commit messages with the `Co-Authored-By` trailer; end PR bodies with the Claude Code footer.
- **CI must be 100% green before merge — red means it will not deploy.** The matrix includes: Syntax & Lint, API Tests (3 OS), E2E Browser Tests, **Live OpenClaw E2E (real gateway)**, MOAT Verifier + Keystone, Eval Suite Gate, Sync matrix (3 OS × 3 Py), Install/boot/health, wheel/asset presence, pip install.
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
