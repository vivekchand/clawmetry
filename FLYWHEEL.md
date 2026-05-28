# FLYWHEEL.md — ClawMetry

> 🌀 ClawMetry's adoption of the **[FLYWHEEL.md](https://flywheel.md)** convention — the third file in the agent canon: `AGENTS.md` (what to do), `SOUL.md` (who to be), `FLYWHEEL.md` (how to ship). ClawMetry is its first adopter. This is our tailored instance; yours will differ — keep the bar.

How an autonomous agent should ship a change in this repo **end to end**: code → PR → green CI → merge → `[RELEASE]` → PyPI → promote to clawmetry-cloud → verify live. Read this with `CLAUDE.md` (architecture) and the cloud repo's `FLYWHEEL.md` (the other half of the loop).

The north star: **don't stop at "code compiles." Stop at "verified working in production, by me, with evidence."** Use `/goal` and keep iterating until that's true.

> ## ⛔ The "done" bar (non-negotiable)
> **Never tell the user a fix is "done" until it is MERGED, RELEASED to PyPI, the cloud has DEPLOYED it, and you have VERIFIED it live (decrypt the snapshot AND/OR a browser screenshot of the actual tab).** "PR is up / CI green / merged" is *not* done — code that isn't deployed helps nobody. A diagnosis is not a fix; a merge is not a deploy; a deploy is not a verification. Land the whole chain, then say done — once, plainly, with the evidence.

> ## ⚡ Performance is a feature — and a cost (non-negotiable)
> **The app must stay snappy and cheap to run. At $5/node/mo we cannot make hundreds of API calls per minute.** Every poller and every fetch is money. Treat request volume like a budget you can blow.
> - **Share, don't duplicate:** one fetch of a shared blob (e.g. the 173 kB `system-snapshot`) serves all consumers — cache it with a TTL + in-flight dedup. Never let N components each re-fetch the same thing (we shipped exactly that bug: 7 interceptors × the snapshot = ~17 fetches/cycle → cut to ~2).
> - **Scope to the screen:** only the active tab polls its own data. Gate heavy pollers on the current tab and pause them off-tab (and when the browser tab is hidden). The Overview fan-out (`loadAll`) must not fire on the LLM Context screen.
> - **Cache + dedup by default:** respect TTLs, dedup in-flight requests, prefer one batched call over many.
> - **Before adding any poller/fetch, ask:** does this need to run on *every* tab? every *N* seconds? can it reuse an existing fetch or the snapshot?
> - **Measure before shipping:** open the Network panel / Resource Timing and confirm no endpoint is fetched N× per cycle and no background poller fires off its own screen. "It works" is not enough — "it works without a request storm" is the bar.

---

## 0. Before you touch anything

1. **Scan open issues/PRs for human claims.** If a human said "picking this up" / "working on" / "I'll take" in the last 7 days, do NOT open a competing PR. Automation is the night-shift janitor, not the day-shift engineer.
2. **Scan the user's recent comments** on open PRs/issues and address them first.
3. **Re-read the goal.** If invoked via `/goal`, the goal persists until the *outcome* is achieved and verified — not until the code is written.
4. **Work in an isolated worktree.** Multiple Claude Code agents and crons run against this repo at the same time. Editing the main checkout is unsafe: another process can switch branches mid-edit and clobber uncommitted changes (burned 2026-05-28 — `feat/asset-registry` working-tree wiped when a concurrent agent checked out `release/hash-chain-2210` in the same checkout). Always start with `EnterWorktree`, or `git worktree add .claude/worktrees/<slug> -b feat/<slug> origin/main`. The worktree gives you your own branch + working tree; the shared checkout is for the human, not for parallel automation. Use `ExitWorktree` (or `git worktree remove`) once the PR is merged.

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

## 2. Make the change

- New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. Shared helpers reach back via late `import dashboard as _d`.
- Embedded frontend lives in `dashboard.py` template strings AND in `clawmetry/static/` + `clawmetry/templates/`. Note: `dashboard.py` defines `DASHBOARD_HTML` twice — the **second** wins and loads `static/css/dashboard.css` + `templates/tabs/*.html`. The inline `<style>`/HTML earlier in the file is dead. Edit the static/template files.
- Match surrounding style: `snake_case` funcs, minimal deps (Flask + waitress + cryptography), never crash on bad input (graceful fallbacks + a logged warning).
- No em-dashes / double-dashes in user-facing copy (banners, marketing). Code comments + PR text are fine.
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
