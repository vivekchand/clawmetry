<!--lint disable strong-marker-->

# Review Log: WO-NODE-CLARITY-001

**Work Order:** WO-NODE-CLARITY-001 — Explain node observations and collect usable CPU and listener evidence
**Initialized At (UTC):** 2026-10-15T20:56:44Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Round 1: Planning and baseline evidence

Author context checkpoint, before implementation; not an independent approval. Read the Factory requirement, blueprint and both referenced blueprint records. The approved addition contains eleven new CLARITY criteria and preserves the prior twelve correctness criteria. The implementation plan predates product edits. The actual installed source reported partial processes with a 512-row cap and macOS listener collection denied, explaining the screenshots. Reviewed authoritative psutil CPU interval and lsof machine-format documentation before choosing bounded permitted polling. Release, package and live hosted acceptance remain pending.

## Round 2: Independent frontend bucket review

Reviewer: node_ui. Scope: live Node JavaScript, template, CSS and focused frontend/browser tests. No product implementation edits by this reviewer.

### Requirements, blueprint and user-facing findings

Reviewed the full bucket against the approved eleven CLARITY criteria, existing twelve criteria, saved blueprint and both fresh referenced feature/composition blueprints. The plain event story removes unsupported actor edges, keeps the original event/time/resource and partial first-sighting limits, and preserves original evidence under a native disclosure. Process CPU presents measured intervals, true zero and unavailable reasons separately. Listener empty states expose a source reason and working coverage navigation. Existing bounded preview/older reviewed event selection, synchronized preceding resource evidence, historical reviews, reduced motion and request/replay lifecycle remain present.

**Blocking B1: legacy source-count fallback can fabricate current positives.** In `observedCount`, missing `coverage.count` falls directly back to a numeric summary total without requiring current complete coverage. An executed legacy-shaped payload with `coverage.processes={state:'partial'}`, `summary.process_count=42`, and only a retained stale row renders `42` with `Observed in this scan; total is not known.` An exact or historical summary value is not evidence of 42 current source rows. This violates AC-OBS-NODE-CLARITY-001.1, AC-OBS-NODE-CLARITY-001.2 and AC-OBS-NODE-CLARITY-006.2. Reproduction: `/tmp/clawmetry-node-qa/clarity-legacy-count-probe.js`. Restrict summary fallback to verifiably complete/current source evidence, otherwise use positively current nonstale rows or an unavailable measurement; add regression for partial/missing count plus numeric summary/stale-only rows and unknown coverage.

### Architecture, escaping and presentation

New external strings are escaped or assigned with textContent. The story does not trust arbitrary actor labels without supported kind and attribution evidence. No new timer, fetch loop, mutation path, privileged operation, dependency or build step is introduced. Native details/summary is keyboard operable and has an explicit focus style. Layout uses existing theme variables and retains narrow-screen and reduced-motion rules. No additional blocker or advisory issue identified in these areas. Root owns visual screenshot verification; this review does not claim the future feature is installed or hosted.

### Independently executed checks

* Focused executed JavaScript/frontend suite: **1 passed** using `--noconftest` and scratch audit/store paths.
* Existing real-collector component browser check: **1 passed**, including 320-pixel overflow across all views, selected evidence/replay correspondence, older review access, progressive evidence and View coverage. The temporary wrapper uses the normal shared Chromium owner and overrides the server fixture; any dashboard readiness probe raises. A dummy token, closed loopback URL and scratch audit/store paths prevent production server use.
* JavaScript syntax, English extraction (4598 messages, zero mechanical findings) and diff whitespace checks passed.
* Independent count probe reproduced B1 exactly; current tests did not cover that legacy combination.

**Verdict: CHANGES_REQUESTED.** Blocking: 1. Advisory: 0. Fresh full-bucket review required after B1 and its regression are resolved. Actual owned-process/listener/CPU local plus encrypted hosted proof remains a separate delivery gate.


## Round 3: Fresh independent full frontend review after B1

Reviewer: node_ui. Re-read the entire live JavaScript/template/CSS and frontend/browser test bucket after the author correction, against all eleven new CLARITY criteria and the existing requirement/blueprint graph. No product edit by reviewer.

### Resolved blocker and requirement alignment

B1 is resolved. Numeric summary totals are now a fallback only when source coverage is complete. Missing positive counts under partial or missing coverage cannot turn historical summary totals or stale-only rows into current observations. The author added regressions for both cases, then verifies that an explicitly current, timestamped nonstale row remains usable as one observation. The independent original reproduction now renders `Not measured` instead of the false 42-observed claim.

Fresh full-bucket review confirms separate observed counts/exact-total limits and source states; measured CPU intervals, multicore convention, actual zero and specific unavailable reasons; plain event stories with conservative unknown attribution; progressively disclosed original before/after/source evidence; source-specific empty reasons and coverage navigation; and legacy snapshots without invented counts or rates. Technical disclosure open state and historical review drafts/focus are retained across same-event updates. Older reviewed events, chronological replay selection and preceding resource measurements remain reachable and synchronized. Original event data is retained rather than rewritten by the narrative.

### Architecture, safety and presentation

No new polling loop, timer, request path, dependency, privileged action or attribution source was added. Existing active/visible/node-generation checks, read/mutation deadlines, confirmed-save semantics and replay stop rules remain unchanged. Dynamic story, actor, source, endpoint and counter strings are escaped or assigned through textContent. Native details/summary preserves keyboard operation with visible focus. Theme variables, narrow layouts and reduced-motion rules remain in force. No remaining blocker or advisory finding was found in this frontend bucket.

### Independent fresh verification

* Executed JavaScript/frontend contract and lifecycle suite: **1 passed** with scratch audit/store and `--noconftest`, including the new missing-count legacy regressions.
* Normal shared Chromium component test: **1 passed** using the server-override wrapper, dummy token, closed loopback URL and scratch audit/store; any production readiness probe raises. This rechecks real collector payload rendering, 320-pixel views/overflow, old investigation access, selected event/resource correspondence, technical details, attribution evidence, reduced motion, unavailable states and working View coverage navigation.
* The original independent count probe now produces `Not measured` and an unavailable-current-count explanation for the exact B1 payload.
* JavaScript syntax, English extraction (4598 messages, zero mechanical findings) and diff whitespace checks passed.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. This is frontend implementation/component approval. Actual owned process/listener CPU evidence through DuckDB, local and encrypted hosted UI, official package inspection and deployed cloud verification remain delivery gates; this review does not claim those future checks complete.

## Round 4: Independent full collector and security review

Reviewer: node_cloud, independent of the collector author. Reviewed the complete owned bucket: `clawmetry/node_activity.py`, `tests/test_node_activity_collector_clarity.py` and the three-line existing test fallback stub. Also inspected the approved saved requirement/design addition and referenced feature/composition contracts, daemon cadence, existing store ingestion/comparison/query projection, encrypted snapshot builder and cloud bridge field preservation. No product implementation edits by reviewer.

### Blocking findings found and resolved before approval

* **Collector CB1, correctness/security:** a malformed new process header missing its NUL terminator left the previous PID active, allowing the next valid file record to inherit that previous process owner. Independently reproduced the incorrect `(PID 10, port 40001)` after malformed `p20`. The author now clears process context on structurally incomplete or unknown record sets. The new regression preserves earlier safe rows, omits rows without a valid owner context and resumes after a later valid process header. Author red-before evidence: `clarity-parser-owner-red.log`.
* **Collector CB2, requirements/validation:** unmatched endpoint brackets were independently stripped into apparently valid measured endpoints, with no malformed flag. The author now requires documented balanced bracketed IPv6 or unbracketed IPv4/wildcard syntax, validates address family and bounds the numeric port. Four new red-before cases cover unmatched brackets, bracketed IPv4 and unbracketed IPv6. Existing safe IPv4, IPv6 and wildcard cases, plus the actual owned listener, remain valid. Author red-before evidence: `clarity-parser-brackets-red.log`.

Fresh full-bucket review after both corrections found no remaining blocker or advisory issue.

### Requirements, architecture and privacy

CPU rates use cumulative user/system counter deltas over actual monotonic time for the same source/PID/start identity. First observation, missing/omitted counters, restart, source/identity changes, disabled collection, counter regression and intervals outside 0.1–120 seconds cannot become an invented zero. Valid measured zero and multicore values above 100 remain distinct. The weak per-sensor cache retains at most 512 public process identities and remains daemon memory only; raw cumulative inputs do not enter public rows, DuckDB or cloud. Existing iterator cache clearing remains in place for PID reuse safety.

The listener helper is Darwin-only after primary permission/unsupported failure. It uses one fixed absolute command, no shell, no escalation, no DNS/service lookup, no inherited credentials and no active network probe. Pipe output is capped at 256 KiB, helper runtime is bounded by 0.75 seconds and the remaining shared budget, cleanup targets only its own spawned child, and listener rows retain the 256 cap. Safe complete records can survive truncation; incomplete evidence remains partial/unavailable and explicitly method-qualified. Wildcard exposure and actors remain unknown, and unverified process_id is null.

Listener method changes qualify the source identity. Store partial/gap rules therefore retain safe evidence without false removals or recovery, and the next comparable complete source starts quietly. CPU/provenance enrichment is outside entity-difference keys, avoiding per-sample change events. Additive public fields survive existing stored JSON, query, encrypted snapshot and shared cloud bridge without a new endpoint, poller, dependency, schema migration or cloud plaintext. New host reads remain in the daemon collector.

### Independent checks and evidence boundaries

* Fresh final focused collector plus existing store/route suite: **67 passed in 2.26 seconds**, with scratch audit/store paths and `--noconftest`. This includes the actual owned process/listener test using the real OS collector and in-memory DuckDB; no skip was reported on this macOS run. The test observed warm-up unavailability and a later measured CPU interval, verified the owned loopback listener, and closed only its child.
* Isolated Ruff E/F checks on the collector and new test module: **passed**. `git diff --check`: **passed**.
* Inspected initial 13-failure implementation red-before evidence, both parser correction red-before logs and sanitized `clarity-owned-component-proof.json`. The proof explicitly limits itself to local component evidence.
* Existing 30-second service cadence, per-source caps, private row projection, store no-negative-on-partial rules and encrypted snapshot/bridge compatibility were inspected directly.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. Both collector findings are resolved and covered by named regressions. This approves implementation and component evidence, not release completion. Official wheel inspection, installed daemon restart and the same owned CPU/listener evidence in local plus encrypted hosted views remain required delivery gates under root ownership.


## Round 5: Independent CI registration bucket review

Reviewer: node_ui. Reviewed the entire new uncommitted bucket: `.github/workflows/ci.yml` and the appended CI follow-up paragraph in this work order's implementation plan. Product source and test assertions are unchanged by this follow-up; prior frontend and collector approvals remain applicable.

The exact workflow diff adds `tests/test_node_activity_collector_clarity.py` to the existing folded Node observation/governance/lifecycle pytest command, between the existing collector/store tests and wiring tests. It does not add a job, alter execution flags, change the unlisted allowance or weaken a gate. The plan truthfully records why the registration was needed and cites the failed CI run as author red-before evidence.

Independently executed `python3 scripts/check_ci_test_coverage.py --check`: **PASS, 384 listed / 902 unlisted, maximum 902 unchanged**. Independently executed the exact amended four-module pytest command with explicit scratch audit/store paths: **95 passed in 3.64 seconds**. The command uses `--noconftest`, preserving the existing isolated test boundary. `git diff --check` passed. The new file is executed by an existing CI step rather than merely added to a parser allowlist.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. This approval covers the CI registration and plan update only; it makes no new installed or hosted release claim. Reviewer made no workflow or product edit.


## Round 6: Independent rebased acceptance-manifest bucket review

Reviewer: node_ui. Reviewed the complete acceptance manifest and coverage-baseline delta against fresh main `b763676bd858b37af005335525abc0a6e08ef5fc` (Asimov PR 6442), and compared every new criterion with the saved, read-back-verified approved Factory addition. No product or acceptance-record edit by reviewer.

Deterministic JSON comparison proves that all 475 fresh-main criteria remain an identical ordered prefix, including the newly merged Asimov criteria. Every existing manifest metadata field, in-repository prefix and external prefix is unchanged. Exactly eleven CLARITY entries are appended, without duplicates; each ID and full text exactly matches `/tmp/clawmetry-node-qa/node-clarity-requirement-addition-approved.md`, with the correct Factory requirement ID.

The baseline changes only `covered_count` from 407 to 418 and `total_count` from 475 to 486. Its comment metadata and exact list of 68 uncovered criterion IDs are unchanged; no existing uncovered item or coverage requirement is removed. Independently ran `python3 scripts/check_ac_coverage.py --check`: **PASS, 418/486 covered, 68 uncovered, ratchet holding**. `git diff --check` passed.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. The fresh-main manifest is preserved intact and the exact approved eleven criteria are added without weakening the ratchet. Prior implementation and CI-registration approvals remain separate; actual installed/hosted release acceptance is still pending its delivery evidence.


## Round 7: Fresh full frontend review after stale-only coverage navigation correction

Reviewer: node_ui. Independently reviewed the full frontend JavaScript/template/CSS and focused frontend/browser tests again, including the new template buttons, browser regression and plan note. No product edit by reviewer.

The concrete AC-OBS-NODE-CLARITY-005.1 gap is resolved: each inventory heading now has a permanently available native `button` with the existing `data-na-coverage` handler. Distinct accessible names identify process and listening-port coverage. The action is present when current rows exist, only stale retained rows exist, or the dynamic empty body is shown. It navigates to the existing Govern coverage view without a new handler, request, timer, CSS or capability claim. The flex heading already wraps at narrow widths; buttons retain normal keyboard activation and existing visible focus.

The regression modifies the real collected/persisted component payload to mark all process rows stale and the process source unavailable, waits until stale evidence is actually rendered, then resolves the process button by its accessible name and verifies Govern is shown. The earlier empty-list coverage navigation and 320-pixel no-overflow checks remain intact. This fixture mutation is a state-boundary regression, not a claim of real permission failure or live delivery proof. Root's red-before browser failure is documented in the implementation plan.

Fresh review also rechecked count fallback, source-state/empty explanations, CPU intervals/reasons, plain selected-event narrative, original evidence disclosure, escaped values, historical review state, reduced motion, replay and unchanged request lifecycles. No new blocker or advisory issue was found; the permanent coverage action closes the stale-only path while preserving these contracts.

Independently reran the executed JavaScript/frontend suite: **1 passed**. Independently reran the real-collector normal shared Chromium component test through the safe server-override wrapper at **320 pixels: 1 passed**, including the stale-only process button and actual view navigation. Scratch audit/store, a dummy token and closed loopback URL were used; dashboard readiness probes are forbidden by the wrapper. JavaScript syntax, English extraction (4652 messages, zero mechanical findings) and diff whitespace passed.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. This is fresh full frontend implementation/component approval, including the stale coverage correction. Official installed package and actual local/encrypted-hosted owned process/listener CPU evidence remain delivery gates; none is claimed by this component review.
