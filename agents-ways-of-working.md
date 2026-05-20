# Agents — Ways of Working (ClawMetry OSS)

How an autonomous agent should ship a change in this repo **end to end**: code → PR → green CI → merge → `[RELEASE]` → PyPI → promote to clawmetry-cloud → verify live. Read this with `CLAUDE.md` (architecture) and the cloud repo's `agents-ways-of-working.md` (the other half of the loop).

The north star: **don't stop at "code compiles." Stop at "verified working in production, by me, with evidence."** Use `/goal` and keep iterating until that's true.

> ## ⛔ The "done" bar (non-negotiable)
> **Never tell the user a fix is "done" until it is MERGED, RELEASED to PyPI, the cloud has DEPLOYED it, and you have VERIFIED it live (decrypt the snapshot AND/OR a browser screenshot of the actual tab).** "PR is up / CI green / merged" is *not* done — code that isn't deployed helps nobody. A diagnosis is not a fix; a merge is not a deploy; a deploy is not a verification. Land the whole chain, then say done — once, plainly, with the evidence.

---

## 0. Before you touch anything

1. **Scan open issues/PRs for human claims.** If a human said "picking this up" / "working on" / "I'll take" in the last 7 days, do NOT open a competing PR. Automation is the night-shift janitor, not the day-shift engineer.
2. **Scan the user's recent comments** on open PRs/issues and address them first.
3. **Re-read the goal.** If invoked via `/goal`, the goal persists until the *outcome* is achieved and verified — not until the code is written.

## 1. The data-flow rule (this is the one that bites)

ClawMetry is **read-only** and **DuckDB-first**:

- Every feature persists to and reads from the local **DuckDB** store. Reading raw JSONL, log files, `sessions.json`, or process stats *inside a request handler* is a violation — it works locally and silently returns empty in cloud (the cloud container has no `~/.openclaw` filesystem). Most "works locally, broken in cloud" bugs are exactly this.
- The blessed path for anything the cloud needs to display:
  ```
  jsonl/gateway  →  daemon ingest  →  DuckDB  →  (sync_system_snapshot)  →  encrypted snapshot  →  Redis  →  cloud decrypts client-side & renders
  ```
- The daemon **owns the DuckDB writer lock**. Build snapshot data on the daemon's **own** store handle (`local_store.get_store()`), never a `read_only=True` re-open — that deadlocks the writer (the `#1771` brick-lock: a cached RO handle blocks every subsequent write; symptom is `cannot open writer — read-only handle already exists`). When you need a read in a separate process, go through the daemon's `/__local_query__/<method>` HTTP proxy (`local_store_via_daemon`), not a direct open.
- If the agent runtime's **model** is needed (e.g. Self-Evolve), don't try to make ClawMetry call an LLM or get gateway write scope — it's read-only by design and its gateway token is `operator.read` only. Shell out to **`openclaw agent --session-id <stable> --message <prompt> --json`**: OpenClaw runs the turn on its own credentials, the transcript lands on disk → DuckDB, and you parse the result. (`openclaw` is a Node script — under the daemon's launchd PATH `node` isn't found, so pass an augmented `PATH` to the subprocess.)

## 2. Make the change

- New HTTP endpoints go in `routes/<feature>.py` on that feature's Blueprint, not in `dashboard.py`. Shared helpers reach back via late `import dashboard as _d`.
- Embedded frontend lives in `dashboard.py` template strings AND in `clawmetry/static/` + `clawmetry/templates/`. Note: `dashboard.py` defines `DASHBOARD_HTML` twice — the **second** wins and loads `static/css/dashboard.css` + `templates/tabs/*.html`. The inline `<style>`/HTML earlier in the file is dead. Edit the static/template files.
- Match surrounding style: `snake_case` funcs, minimal deps (Flask + waitress + cryptography), never crash on bad input (graceful fallbacks + a logged warning).
- No em-dashes / double-dashes in user-facing copy (banners, marketing). Code comments + PR text are fine.

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

Hand off to the cloud repo's `agents-ways-of-working.md`. In short: bump `clawmetry==<new>` in the cloud `Dockerfile` *only when the daemon code changed* (a cloud-only render fix that reads an already-shipped snapshot key needs no bump), add the matching `cm-cloud-*` interceptor + route-policy entry, get cloud CI green, and verify the deploy.

## 7. Verify in production (the part that's non-negotiable)

- Decrypt the live cloud snapshot again post-deploy and confirm your data is present.
- Open the actual tab in a browser, confirm it renders, and **attach a screenshot** within ~5 min of merge (especially for any cloud UI surface). The screenshot catches stale-rebase regressions as a bonus.
- Only then say it's done — plainly, with the evidence. If something is partial, say which part and why.

## 8. Judgment

- Decide ship-vs-hold trade-offs yourself; state a one-line rationale and act. Don't bounce routine decisions back to the user.
- When a finding contradicts the premise of a request (e.g. "spawn a gateway session" turns out to need write scope ClawMetry can't have), surface it with evidence and propose the path that actually works.
- Save durable, non-obvious learnings to memory so the next agent doesn't re-burn them.

🤖 Maintained by Claude Code agents. If you discover a new gotcha, add it here.
