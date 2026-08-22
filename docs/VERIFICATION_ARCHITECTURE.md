# Verification Architecture

How ClawMetry decides that a change is safe to ship, and why the answer is not
"we have tests".

This repository has 948 test files and roughly 306,000 lines of test code. That
was never the constraint. The constraint was that almost none of it was
load-bearing at the moment of merge, and nothing re-verified the surfaces
nobody happened to be working on.

## The two failures this exists to prevent

**1. A guard that does not gate.** Branch protection names exactly one required
context, `E2E Gate (required)`. Before this architecture it aggregated four E2E
checks and nothing else, so `CI` was advisory: a pull request could merge with
`Syntax & Lint`, the three-OS API matrix, the MOAT verifier, the entitlement
suite and the entire `pip install` matrix fully red.

0.12.753 is the worked example. It shipped `-> str | None` at
`clawmetry/cli.py` module scope. PEP 604 unions parse on Python 3.9 but are
*evaluated* at `def` time, so every `clawmetry` subcommand died at import on
every 3.9 install, including the macOS desktop bundle's own 3.9 venv, and
including `clawmetry uninstall`. Affected users had no supported way off the
product. The guard written afterwards, `scripts/check_py39_annotations.py`,
landed in a workflow that gated nothing.

**2. Verification tied to the diff.** CI is change-triggered, so working on one
thing stops verifying everything else. `install-test.yml` fires only on
`paths: [install.sh, install.ps1, install.cmd]`, so a `setup.py` or dependency
change can break `pip install clawmetry` without ever running an install test.
`desktop-artifacts.yml` fires only on `tags: v*.*.*`, so an installer break is
found at release time. Spend a week on the Windows installer and nothing
re-proves the pip path until a user does it for you.

## The layers

### L0 -- the merge gate (`scripts/e2e_gate.py`)

This file *is* branch protection in practice. A check absent from
`REQUIRED_SPECS` cannot block a merge however good the test behind it is.

Two matching modes: an exact check name, or an fnmatch pattern plus `min_count`
for matrix jobs. `min_count` is what stops a *shrinking* matrix from passing
quietly. Drop macOS from the matrix and a bare glob still matches the remaining
legs; the count does not.

Only list checks whose workflow runs on **every** pull request. A path-filtered
workflow never reports on most PRs, so requiring it would hang the gate until
timeout and block every merge. Those surfaces belong to L2 instead.

### L1 -- the product truth matrix (`verification/matrix.json`)

Coverage used to be *implied*: whatever tests happened to exist. That is how
holes open with nobody choosing them. Python 3.9 ran on Linux only; its one leg
executed `tests/test_api.py` and never imported the CLI; the API matrix
installs four dependencies and omits duckdb and cryptography, so it validates a
degraded install.

The matrix *declares* each product x platform x python cell instead, and
`scripts/verification_matrix.py` proves every declaration is real:

- each cell names a verifier that exists, so a cell cannot claim deleted coverage;
- a `gated` cell must be backed by a workflow that runs on every PR with no
  `paths:` filter, because otherwise "gated" asserts protection that does not exist;
- ratchets: known holes may only shrink, gated cells may only grow.

Cell status is `gated` (blocks a merge), `continuous` (verified on a schedule by
L2), or `manual` (no automation yet). `manual` is an honest, counted admission,
and the open-holes ratchet stops it becoming a dumping ground.

### L2 -- the conformance heartbeat (`.github/workflows/conformance-heartbeat.yml`)

Re-verifies the **published** artifact on a schedule, ignoring the diff
entirely. Every 2 hours it installs `clawmetry` from PyPI on Linux for 3.11 and
3.9; every 6 hours across all three operating systems; nightly it also runs the
installer scripts and desktop builds that are otherwise only exercised at tag
time.

It asserts more than a successful install, because a resolvable install is not
a working one: it imports `clawmetry.cli` explicitly and runs `--help` for every
subcommand. A failure here means the product a user installs *right now* is
broken, which is more urgent than any red PR check.

### L3 -- store invariants (`tests/test_store_invariants.py`)

Every other suite checks an example somebody thought of, which is why each new
bug arrives with a bespoke guard written after users hit it. These state
properties and let Hypothesis search for a sequence that breaks them.

The invariants come from the store's own documented contracts and from real
incidents: idempotent ingest by id (adapters replay journals), no acknowledged
event lost under interleaved ingest and flush (issue #1590, where two
concurrent flushes evicted each other's batches), a read-only handle that
neither writes nor wedges the writer (issue #1771), and clean, non-destructive
rejection of a torn record.

Note the scoping on that last one. `ingest` documents four required keys and
raises `ValueError` when one is missing; that is a contract, not a crash, and
correct for a library primitive. CLAUDE.md's "never crash on bad input" binds
the *daemon*, whose job is to catch it and continue.

`local_store.DB_PATH` is resolved at **module import** from
`CLAWMETRY_LOCAL_STORE_PATH`, so that variable must be set before `clawmetry` is
imported at all, and `mark_writer_owner()` must be called first or `get_store()`
returns the daemon proxy and every write silently no-ops.

### L4 -- the mutation ratchet (`scripts/mutation_ratchet.py`)

The agent-proofing layer.

Line coverage cannot detect a weakened test. Change `assert x == 5` to
`assert x is not None` and coverage is byte-for-byte identical while the
assertion stops asserting. Any mechanism relying on a human noticing that diff
is a convention, and an agent under pressure to turn CI green will find the
cheapest path through a convention every time.

Mutation testing measures what actually holds: break the source in small ways
(`>=` to `>`, `and` to `or`, bump a constant) and re-run the tests. A surviving
mutant is a behaviour change no test objected to. Baselines are measured, not
aspirational, and recorded in `verification/mutation_targets.json`; CI fails
when a live score drops below its baseline.

`verification/guards.json` is the companion census: guard files that must exist
and must not be hollowed into stubs, plus ratchets that may only rise.

This does not make weakening impossible. It makes weakening impossible to do
*silently*, which is the achievable goal.

**Why enforcement is mechanical rather than review-based:** GitHub does not let
an author approve their own pull request, and effectively every PR here is
authored by the same account. Enabling "Require review from Code Owners" would
make every PR permanently unmergeable. `CODEOWNERS` is therefore used for review
routing only, and the ratchets do the enforcing.

### L5 -- the release canary (`scripts/canary_verify.py`)

At the current cadence, roughly 5 releases a day each reaching 100% of PyPI
users on upload, escapes are arithmetic rather than bad luck. Perfect
pre-publish testing is not available; a short detection window is.

`release-on-merge.yml` smoke-tests the wheel it just *built*, on one
interpreter, on Linux. The canary tests what users *receive*, from the real
index, on every platform, after publication. The gap between those two covers
upload corruption, index propagation lag, a dependency resolving differently on
a clean machine, and a platform wheel that never got built.

It waits until pip can actually *resolve* the version first: the PyPI JSON API
reports a version before the simple index serves it, and that race has already
broken cloud Docker builds immediately after a release.

It deliberately does **not** auto-yank. FLYWHEEL makes yanking a human
decision, and an automated yank on a false positive is worse than the bad
release. It opens a P0 issue with the evidence, the management link, and the
hotfix-versus-yank choice stated plainly.

## Adding coverage

1. Add the cell to `verification/matrix.json` with a real verifier and an
   honest status.
2. If it should block merges, add the check to `REQUIRED_SPECS` in
   `scripts/e2e_gate.py` and confirm its workflow runs on every PR.
3. If it is a new guard, add it to `verification/guards.json` so removing it is
   caught.
4. Raise the relevant ratchet to lock the new coverage in.

## Known holes

Tracked in `verification/matrix.json` under `open_holes`, each with its impact
and owning repository, and ratcheted so the count may only fall:

| Hole | Impact |
|---|---|
| 8 of 24 paid adapters have no REAL fixture (incl. `claude_code`, `openclaw`) | An upstream format change passes against synthetic fixtures |
| `ci.yml::api-tests` omits duckdb and cryptography | The API matrix validates a degraded install |
| Python 3.9 runs on Linux only | A Windows or macOS 3.9 break ships unseen |
| Firmware verification is cross-repo | A snapshot-schema change here can break the device with nothing failing here |
