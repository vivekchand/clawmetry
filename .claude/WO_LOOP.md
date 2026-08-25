# Work Order Loop — hourly runbook

Board: https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/work-orders
API helper: `python3 .claude/wo.py`, run from the repo root.
Auth: `SF_API_KEY` env var (cloud) or macOS keychain `clawmetry-sf-api-key` (laptop).
Ledger: `.claude/wo_ledger.json` — the loop's own memory of what it has attempted.

## One tick = one or two work orders, taken to done

### 1. Pick
```bash
python3 .claude/wo.py pick 2
```
Take the first. Take the second only if the first finishes with real time left in the
tick. Never start a third.

`pick` already applies the order: `in_review` first (nearly done, drain it), then
`in_progress`, `ready`, `backlog`; within a status, by priority then number. It skips
anything the ledger records as `shipped` or `gave_up`, and skips `blocked`.

### 2. Read it
```bash
python3 .claude/wo.py show <number>
```
Then read every linked blueprint / requirement in `connectedContext` via
`python3 .claude/sf_client.py GET /blueprints/<id>` (envelope is
`{"data": {"markdown_content": ...}}`). Follow `@mentions` and links inside those
documents too — the software-factory skill is explicit that this is mandatory.

### 3. Route to the right repo
Work orders span four repos. Decide from the WO text, not from habit:

| Signal in the WO | Repo |
|---|---|
| dashboard, routes/, clawmetry/, adapters, CLI, daemon | `clawmetry` |
| `/api/cloud/*`, accounts, billing, tenants, ingest, SSO/RBAC | `clawmetry-cloud` |
| paid adapters, entitlement-gated features | `clawmetry-pro` |
| marketing site, pricing copy, public claims | `clawmetry-landing` |

On the laptop these are sibling checkouts under `/Users/vivek/projects/`. In a cloud
run they are the `sources` on the routine; if the WO needs a repo that is not checked
out, say so in the WO comment and pick the next one instead of guessing.

Work in a **git worktree**, never on `main`, never by `git stash` (see the standing
BURNs). Use `git -C <path>` for every git call — the shell cwd resets between calls.

### 4. `in_review` work orders are a VERIFY task, not a build task
Five WOs were filed claiming "shipped, ready for review". Do not rebuild them.
Verify each claim against **merged main** — read the code, run the named tests, hit
the named endpoints. Then:

- claim holds → `status <n> completed`, comment with the evidence (file:line, test
  output, endpoint response).
- claim is partly false → comment with exactly what is missing, set `status <n> ready`,
  and fix it on the next tick (or this one, if small).

Never mark something completed you have not looked at. That is the failure mode that
put this board in its current state.

### 5. Execute
Follow `.claude/skills/software-factory/execution/execute-work-order.md` in full:
init `.sw-factory/WO-<n>/`, complete `checklist.md` (every item `[x]` or `[SKIP]` with
a reason), write `implementation-plan.md`, implement, run the acceptance tests named in
the WO's "E2E Acceptance Tests" section, fill `review-log.md`.

Then FLYWHEEL.md's shipping loop for the repo you are in: branch → PR → green CI →
`[RELEASE]` → verified live. A PR that is open and red is not done.

### 6. Close the loop on the board
```bash
python3 .claude/wo.py status <n> in_progress        # when you start
python3 .claude/wo.py comment <n> /path/to/note.md  # evidence: PR link, test output
python3 .claude/wo.py status <n> in_review           # PR open, CI green
python3 .claude/wo.py comment <n> /path/to/note.md  # evidence: merged and verified live
python3 .claude/wo.py status <n> completed           # merged and verified live
```
Every tick must leave a comment on the WO even when the answer is "blocked, here is
why". A silent tick is indistinguishable from no tick — that is how this board died.

### 7. Record it
Append to `.claude/wo_ledger.json`:
```json
{"<number>": {"state": "shipped|in_flight|gave_up", "pr": "<url>", "note": "<one line>", "tick": "<ISO date>"}}
```
`state: in_flight` means pick it again next tick and continue. Only `shipped` and
`gave_up` retire it from the queue.

Commit and push the ledger (`git add .claude/wo_ledger.json`) at the end of every tick.
A cloud tick gets a fresh checkout, so an uncommitted ledger is a lost ledger and the
next tick re-picks the same work order.

## Guardrails
- If a WO needs a product decision only Vivek can make, comment on the WO with the
  question, set it `blocked`, ledger it `gave_up`, and move to the next pick. Do not
  stall the tick waiting for an answer.
- If the tick would touch billing, delete customer data, or push to `main` directly,
  stop and ask instead.
- One WO stuck `in_flight` for three consecutive ticks → ledger it `gave_up` and
  surface it in the tick summary.
