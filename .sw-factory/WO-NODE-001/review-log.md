<!--lint disable strong-marker-->

# Review Log: WO-NODE-001

**Work Order:** WO-NODE-001 — Node activity: observe changes and review risk
**Initialized At (UTC):** 2026-10-15T09:54:47Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Round 1

### Requirements Alignment

**Blocking:**

**Advisory:**

### Blueprint Alignment

**Blocking:**

**Advisory:**

### Architecture And Conventions

**Blocking:**

**Advisory:**

### Tests And Build

**Commands run:**

**Blocking:**

**Advisory:**

### User-Facing Verification

**Skipped:** _yes/no_ - _reason if yes_

**Evidence:**

**Blocking:**

**Advisory:**

### Security, Privacy, And Data Safety

**Skipped:** _yes/no_ - _reason if yes_

**Blocking:**

**Advisory:**

### Round 1 Verdict

- Total blocking:
- Total advisory:
- Files reviewed:
- **Verdict:** _APPROVED or CHANGES_REQUESTED_

---

<!-- Subsequent rounds: copy the structure above and increment the round number. -->

## Round 2: Independent UI bucket review

Reviewer: backend delegate, reviewing UI files it did not implement. Scope includes untracked feature files in this working change. Merge base: `f1dd136931f23c23c16056c583aadde48339b491`.

### Requirements Alignment

**Blocking:** `clawmetry/static/js/node-activity.js:38,140,144`: `events()` cuts to the latest 100 events before Guard and reviewed history filter them. A retained sensitive finding followed by 100 routine changes disappears from Guard, and selecting it resets to the latest event. This contradicts AC-GOV-NODE-005.1 and the shared selected-event contract in AC-OBS-NODE-007.1.

**Blocking:** `clawmetry/static/js/node-activity.js`, `coverageHtml`: `reason || detail || scope` hides explicit `container` scope whenever a reason exists. All backend coverage records have a reason. AC-GOV-NODE-005.3 requires visible scope limits.

**Advisory:** `table()` silently limits process/listener/review tables to 100 rows. Disclose the shown and available counts or provide navigation, in line with the blueprint's visible response-cap contract.

### Blueprint Alignment

The browser reads persisted responses, retains node-wide scope under runtime filters, escapes dynamic evidence, keeps one request in flight and invalidates obsolete node responses. Unknown attribution remains unknown. No arbitrary process controls appear. The two blockers above concern the shared-history and explicit-scope contracts.

### Architecture And Conventions

Vanilla JS, scoped CSS and feature template match the existing architecture. No build dependency or host reads appear in the UI. Reduced-motion CSS suppresses travel animation; hidden and inactive lifecycle paths cancel polling/replay.

### Tests And Build

**Commands run:** `python3 -m pytest --noconftest -q tests/test_node_activity_frontend.py` (1 passed); `node --check clawmetry/static/js/node-activity.js` (passed). Executed the existing VM harness with 101 retained events and container coverage: `retained_finding_hidden=true`, `container_scope_hidden=true`, `older_finding_selection_replaced=true`. These regressions are absent from the original tests.

### User-Facing Verification

**Skipped:** Browser visual inspection is assigned to the parent, which is exercising real recorded data and mobile layouts. This bucket reviewed layout CSS, responsive rules, semantics, empty states and request/replay behavior. It does not claim browser layout verification.

### Security, Privacy, And Data Safety

Dynamic rendered values use HTML escaping. Unsupported identity claims normalize to unattributed. Mutations wait for an explicit saved/applied response and obsolete node responses cannot update the new node view. Original event evidence and review text remain separate. No blocker found in this dimension.

### Round 2 Verdict

- Total blocking: 2
- Total advisory: 1
- Files reviewed: `clawmetry/static/js/node-activity.js`, `clawmetry/static/css/node-activity.css`, `clawmetry/templates/tabs/node-activity.html`, `tests/test_node_activity_frontend.py`, `tests/test_node_activity_js.js`.
- **Verdict:** CHANGES_REQUESTED
- Handoff: Both blockers and the advisory were sent to the UI author before any implementation changes. Parent owns browser verification. Requirements, blueprint and implementation plan were read for this review.


## Round 3: Shared OSS integration and sealed relay

Reviewer: independent integration delegate (cloud implementation excluded from this review).

### Requirements Alignment

Node-wide navigation, observation-only host operations, daemon-owned persistence and encrypted detail flow match the linked requirements. Typed settings and historical reviews preserve the existing host control boundary. No arbitrary process control was added.

### Blueprint Alignment

New feature modules, LocalStore mixin, the independent local-only daemon tick, typed local query proxy and encrypted snapshot slice follow the blueprint. The collection call precedes the cloud snapshot early return. Snapshot construction only queries stored evidence.

### Architecture And Conventions

**Blocking:** The daemon invokes the rate-capped service every cycle, but `clawmetry/node_activity_service.py` returns `store.query_node_activity()` on each skipped collection. The caller ignores that result. This repeatedly reads and decodes up to 2,000 history entries between observations. Return no result, or reuse a memory result, on the cadence fast path. Add a test proving repeated skipped ticks do not query history. This is an integration/performance finding under FLYWHEEL section 1e.

**Advisory:** Generic node setting helpers are bypassed for the nonce ledger because their read errors become an absent setting. The direct fail-closed read is correct; a dedicated store nonce-claim operation could make that safety contract easier to maintain later.

### Tests And Build

**Commands run:** `python3 -m pytest -q tests/test_node_activity_wiring.py tests/test_beginner_nav_phase_a.py --noconftest` (23 passed); prior collector plus wiring run (26 passed); `python3 scripts/lint_daemon_allowlist.py` (passed); `node --check clawmetry/static/js/app.js` (passed); `python3 -m py_compile clawmetry/sync.py clawmetry/local_store.py routes/local_query.py dashboard.py setup.py` (passed).

**Blocking:** `python3 scripts/check_ac_coverage.py --check` fails for 10 new acceptance IDs: AC-GOV-NODE-003.2, AC-GOV-NODE-004.2, AC-GOV-NODE-004.3, AC-GOV-NODE-005.2, AC-GOV-NODE-005.3, AC-OBS-NODE-001.2, AC-OBS-NODE-001.3, AC-OBS-NODE-002.2, AC-OBS-NODE-002.3 and AC-OBS-NODE-002.4. Several existing test comments cite IDs, but the gate requires a test docstring or name. Associate the actual assertions with the right IDs and rerun the gate.

### User-Facing Verification

**Skipped:** Yes, browser verification is assigned to the parent. This review covers shared integration, route registration, runtime-wide scope, daemon ownership, packaging and sealed action validation. It does not certify the visual tab or production deployment.

### Security, Privacy, And Data Safety

Two initial relay blockers were reported during review and fixed by the author before this recorded verdict: the bounded nonce ledger no longer evicts live nonces, database read failures fail closed, and review confirmation now verifies the saved review in read-back evidence. New tests exercise ledger saturation, failed ledger reads and missing review read-back. Sealed actions bind node ID, random request ID and a five-minute request lifetime. The nonce is persisted before mutation. Response detail is encrypted through the existing process-control cache path. Public typed mutations require the actual daemon token on the private RPC surface. No remaining security blocker found in the reviewed integration files.

### Round 3 Verdict

- Total blocking: 2
- Total advisory: 1
- Files reviewed: `clawmetry/sync.py`, `clawmetry/local_store.py`, `routes/local_query.py`, `dashboard.py`, `clawmetry/static/js/app.js`, `setup.py`, `requirements.txt`, `tests/test_node_activity_wiring.py`, shared nav registries and the service cadence boundary.
- **Verdict:** CHANGES_REQUESTED
- Handoff: Security corrections were confirmed in source and focused tests. Performance and acceptance-traceability blockers were sent to their authors. Review only; this delegate did not change OSS implementation files.

## Round 4: Independent backend bucket, fresh review after corrections

### Requirements Alignment

Reviewed the saved requirements, blueprint and implementation plan against the collector, node store, cadence service, feature routes and backend tests. Unknown actors remain unattributed. Source gaps preserve stale evidence and establish a quiet baseline on recovery. Monitoring preferences and event reviews are stored separately from original evidence. No arbitrary process control exists.

**Blocking:** None remaining. Three initial blocking findings were sent to the backend author and resolved before this verdict:

- Routine process changes consumed the old 128-event batch cap and permanently discarded later listener and sensitive-setting findings. The store now persists every change in the source-bounded batch before updating comparison state. A regression creates more than 200 routine changes and proves both findings survive.
- Review revisions could grow without a bound and each read scanned them all. Writes now prune age, orphaned records, per-event revisions and the global revision count. Reads select only the latest review per retained event. Frozen-clock tests prove the most recent review remains deterministic.
- Listener identity changed when process enrichment became unavailable, causing false disappearance and addition findings. Endpoint plus reported PID now defines listener identity; optional process enrichment is excluded from change comparison. A regression proves owner-evidence loss and recovery produce no invented listener changes.

**Advisory:** None.

### Blueprint Alignment

The daemon owns collection and DuckDB writes. HTTP handlers call the typed persisted-store boundary only. Fingerprints and source-comparison state stay private. Collector and source limits are explicit; findings stay separate from session policy/control tables.

**Blocking:** None. **Advisory:** None.

### Architecture And Conventions

Per-feature modules and Blueprint placement match the repository structure. Portable psutil measurements use nullable values and source-specific coverage. The process candidate budget retains recent visible work, sets partial/truncated coverage when capped, and reserves time for later sources. Skipped cadence ticks now return without querying history. Individual psutil calls cannot be interrupted, an explicit limitation in the collector contract.

**Blocking:** None. **Advisory:** None.

### Tests And Build

**Commands run:** `python3 -m pytest tests/test_node_activity.py tests/test_node_activity_frontend.py tests/test_node_activity_browser.py -q` passed with 17 tests. `python3 scripts/check_english.py` passed with zero mechanical findings.

Tests cover quiet baseline, PID reuse, partial scans, namespace changes, listener permission limits, file symlinks, private fingerprints, preserved review evidence, disabled collection, retention, stored-only routes, unconfirmed writes, skipped cadence reads, resource warm-up, finding preservation, process-enrichment changes, review bounds and recent-process selection.

**Blocking:** None. **Advisory:** None.

### User-Facing Verification

**Skipped:** No. The isolated browser check renders a real psutil observation and actual DuckDB governance changes. It verifies three views at 320 pixels, exact selection of an investigation older than 100 routine changes, matching map/evidence/replay/resource measurement, explicit source scope, reduced motion and useful unavailable state. Parent separately owns integrated daemon/browser and release verification.

**Blocking:** None. **Advisory:** None.

### Security, Privacy, And Data Safety

**Skipped:** No. Public observations exclude file content, command arguments, environment values and fingerprints. File reads reject direct symlinks and recheck identity. Reviews scrub entered text and validate an existing event. Collection only reads the node; governance changes ClawMetry settings and historical context. Typed route writes require local origin and an authoritative node. Shared authenticated daemon and hosted encryption wiring are covered by the separate integration bucket.

**Blocking:** None. **Advisory:** None.

### Round 4 Verdict

- Total blocking: 0
- Total advisory: 0
- Files reviewed: `clawmetry/node_activity.py`, `clawmetry/node_activity_store.py`, `clawmetry/node_activity_service.py`, `routes/node_activity.py`, `tests/test_node_activity.py`.
- **Verdict:** APPROVED
- Handoff: Backend author implemented the corrections; this independent reviewer verified the updated source and regressions. Approval covers this bucket and does not replace live, hosted or release verification.


## Round 4: Shared OSS integration re-review

Reviewer: same independent integration delegate, after author corrections.

### Requirements And Blueprint Alignment

Re-read the shared changed-file diff against the requirement, blueprint and implementation plan. The daemon tick, writer-owned stored reads, node-wide navigation, sealed monitoring/review actions and encrypted snapshot boundary remain aligned. Runtime-specific filters do not conceal node activity. No new arbitrary process controls or plaintext cloud detail path were added.

### Architecture And Conventions

The cadence fast path now returns `None` without querying stored history. Its test replaces the query method with a failure and proves a skipped tick does not read it. This resolves the performance blocker from Round 3. The local-only collection call remains separate from the cloud snapshot early return.

### Tests And Build

`python3 -m pytest -q tests/test_node_activity.py tests/test_node_activity_wiring.py tests/test_beginner_nav_phase_a.py --noconftest`: 37 passed. `python3 scripts/check_ac_coverage.py --check`: passed, 374/442 criteria covered, baseline ratchet holding. This resolves the acceptance-traceability blocker. The daemon allowlist lint, shared app.js syntax check and `git diff --check` pass. The reviewed Python integration modules passed compilation in the previous round and the subsequent relay corrections execute in the focused integration tests.

### User-Facing Verification

Skipped in this bucket. Parent owns the real-data browser, mobile, release and hosted checks. This verdict does not replace those gates or the separate frontend review.

### Security, Privacy, And Data Safety

Verified the closed operation schemas, encrypted node/request/time bindings, fail-closed replay ledger read and capacity limit, saved review read-back, explicit daemon-token checks for typed local mutations and encrypted result publication. Regression tests cover refused replay, cross-node and invalid seals, unavailable ledger and missing review confirmation. No blocking finding remains in this bucket.

### Round 4 Verdict

- Total blocking: 0
- Total advisory: 1 (the dedicated nonce-claim helper suggested in Round 3 remains optional).
- Files reviewed: same shared integration files as Round 3, corrected service cadence and focused tests.
- **Verdict:** APPROVED for shared OSS integration and sealed relay only.
- Remaining delivery gates: separate UI/cloud reviews, real browser evidence, green PR checks, release wheel and hosted deployment verification.

## Round 4: Independent UI re-review

Requirements, blueprint and plan remain the review baseline. Re-read all five UI bucket files after author changes. Both Round 2 blockers are resolved: full retained events feed Guard/reviews/selection, while Observe has a disclosed 100-row preview that includes a selected older event; source scope renders independently of reason. Tables disclose their own 100-row display cap. No remaining blocking finding in this bucket.

Commands: `python3 -m pytest --noconftest -q tests/test_node_activity_frontend.py` (passed), plus independent VM reproduction confirming retained finding visibility, explicit container scope and selection of the older finding. Reduced-motion CSS, hidden/inactive cancellation, escaped evidence, unknown values and node-wide scope remain intact. Browser visual verification is still assigned to the parent and is not claimed by this review.

Verdict: **APPROVED** for the UI bucket, with no remaining blockers or advisories from Round 2.

## Round 5: Independent hosted bridge review

Scope: the paired cloud worktree's `routes/node_activity_bridge.py`, route policy additions, dashboard registration/injection, session action-status extension, workflow registration and focused tests. Cloud FLYWHEEL requirements were read. No cloud implementation file was edited by this reviewer.

### Requirements, Blueprint, Security And Data Safety

Selected-node snapshot reads use the shared account/node/key-bound cache. Opaque update requests authorize the presented credential that owns the selected node; preference and review details stay inside node-encrypted seals. Matching request ID, node ID, save/applied flags and decryptable data are required before success. Old collectors disable writes. Plaintext hosted write routes are blocked. No new control over arbitrary processes appears.

**Blocking, lifecycle/performance:** UI `mutate()` supplies no abort signal and `nodeActivityStop()` aborts only its GET controller. Consequently the hosted bridge can continue up to 14 action-status polls while the tab is hidden or inactive. AC-OBS-NODE-006.3 and the active-screen polling budget apply here too. The UI author has been asked to pass a mutation-specific signal, abort confirmation polling on invalidation, and report only an unconfirmed result if the action may already have been queued.

**Advisory, errors:** Update and action-status transport fetches have no independent deadline. Without a caller deadline, a stalled connection can leave the confirmation message waiting indefinitely. Bound the overall confirmation wait without implying that an already queued operation was cancelled.

### Tests And Build

Ran the new hosted bridge suite: 35 passed. Ran the combined node bridge, session-control, Guard interceptor and Guard settings relay suites with `CLAWMETRY_E2E_JS` pointing at the real OSS `cm-e2e.js`: 68 passed. The broader initial command also passed all 133 inline syntax cases; its 12 Guard failures were an unavailable installed OSS package in this interpreter. Pointing that harness at the correct local E2E bundle resolved all 12. Existing invalid-escape warnings in unrelated cloud strings remain.

Browser visual and released hosted end-to-end verification are assigned to the parent and remain outside this source review. No production claim is made.

### Verdict

**CHANGES_REQUESTED** pending the cross-bucket mutation lifecycle fix. No blocker found in the encryption, ownership, selected-node cache, route policy or persisted confirmation checks.

## Round 6: Independent mutation lifecycle re-review

Re-read the UI mutation controller/deadline changes and the hosted bridge abort regressions after the author handoff. A dedicated mutation `AbortSignal` now reaches the hosted interceptor. Invalidation aborts browser confirmation work, clears its deadline, and retains a scoped warning that a queued node operation may still apply. A 45-second overall deadline bounds stalled queue/status transport. Late responses and old `finally` blocks cannot clear a newer request or warning. Confirmed persistence clears the mutation deadline before a separate refresh.

Commands: `python3 -m pytest --noconftest -q tests/test_node_activity_frontend.py tests/test_node_activity_browser.py` (2 passed); cloud `python3 -m pytest --noconftest -q tests/test_node_activity_bridge.py` (37 passed, including queue/status abort and no continued polling). Source review confirms that the cloud forwards the supplied signal to both transport requests and wait intervals.

The Round 5 lifecycle blocker and deadline advisory are resolved. No remaining blocker was found in the reviewed UI/cloud buckets. Verdict: **APPROVED** for source review. Parent retains actual hosted browser, release and deployment verification responsibilities.


## Round 7: Final combined pre-PR review

This round combines the independent backend, UI, shared integration and hosted bridge reviews. The hosted bridge implementation author did not self-approve that bucket: the backend delegate independently approved its source and the corrected cross-bucket lifecycle in Round 6. Earlier backend and UI approvals appear in their labelled Round 4 entries. The shared integration approval appears in the separate Round 4 integration entry.

### Requirements And Blueprint Alignment

The complete feature follows the saved requirement, linked blueprint and implementation plan: daemon-owned bounded observations, explicit source gaps, comparable changes, unknown attribution, independent node findings, durable operator settings and historical reviews. Local handlers query stored evidence, while hosted reads use only the selected node's encrypted snapshot. Hosted mutations use a closed encrypted operation schema and require a persisted matching node response. Node scope stays visible under runtime filters. Short-lived activity and incomplete host visibility are not described as complete capture.

### Architecture, Security And Privacy

Re-reviewed the final mutation controller and relay boundary. Hiding or leaving the tab aborts confirmation network requests and sleeps. A 45-second caller deadline bounds a stalled native fetch. The UI warns that an already queued action may still apply. Confirmed persistence clears its deadline before refresh; obsolete abort/finally paths cannot overwrite a newer node's request or notice. The cloud bridge forwards the signal to both queue and status fetches, and its new regressions prove that aborted queue/status hangs do not keep polling or install a saved overlay.

Nonce claims fail closed on database errors and saturation. Requests bind node, random request ID and encrypted creation time. Successful reviews and preferences are checked against read-back evidence. Public private-RPC mutation entry points reject callers without the actual daemon token. Host collection never runs in a request, and arbitrary process termination remains absent. The skipped collector cadence no longer reads history.

### Tests And Build

Final review commands: 48 OSS collector, relay, frontend, navigation and workflow tests passed. 70 paired cloud bridge, session-control, Guard interceptor and Guard settings tests passed using the actual OSS `cm-e2e.js` bundle. The acceptance gate, daemon allowlist, shared and feature JavaScript syntax checks and diff whitespace check pass. The browser psutil pin exactly matches the existing CI pin, including all 21 approved hashes. The new feature unit suites run in the MOAT job; the real-payload browser regression is included in the critical browser job.

Parent evidence in `evidence.md` records the broader workflow/module checks, English mechanical checks, generated module map, pre-release wheel inspection, actual isolated daemon/DuckDB/dashboard path and real browser review save. Those are pre-release results, not published-wheel or production evidence.

### User-Facing Verification

Reviewed the parent's recorded evidence: an actual harmless selected-file change appears through the real collector and authenticated daemon RPC; sensitive contents/fingerprints are absent; Observe, Govern and Guard fit 320/360-pixel screens; explicit source gaps remain visible; no console warning/error appeared during the walk; leaving the tab produced no further Node activity requests across multiple poll windows. Separate browser regression covers reduced motion and an older retained finding's map/evidence/resource/replay selection. The independent source reviewer did not substitute fixtures for the parent's integrated real-data verification.

### Round 7 Verdict

- Total blocking: 0.
- Total advisory: 1 optional dedicated nonce-store helper from the integration review; no required product work remains from that advisory.
- **Verdict:** APPROVED for feature PR submission and green-CI review.
- This approval is not a shipment claim. Remaining delivery gates are feature PR checks/merges, a separate OSS release PR, published-wheel inspection, cloud pin/deploy and actual hosted-node verification. The cloud feature PR must remain unmerged until the parent confirms its required OSS release is available and the cloud pin is verified.

## Round 8: Independent PID reuse cache correction review

### Scope And Alignment

Reviewed only the uncommitted correction in `clawmetry/node_activity.py` and `tests/test_node_activity.py` against AC-OBS-NODE-002.4 and the blueprint requirement that process identity includes a fresh creation token. The collector obtains the existing iterator and invokes its supported `cache_clear` operation when callable before each process scan. Alternate sensors without that optional method retain their prior behavior. The existing source-level exception handler still reports an incomplete scan if collection fails.

Inspected the installed psutil 7.2.2 source directly: `process_iter` retains Process objects in its module cache, and `Process.create_time` retains its first result. Clearing that cache at this boundary ensures the new scan builds fresh Process identities. The patch adds no process control, private data export, dependency or per-process CPU behavior.

### Tests And Verification

`python3 -m pytest tests/test_node_activity.py tests/test_node_activity_wiring.py -q` passed with 33 tests. The new regression models the actual library cache behavior: creation time remains stale until the iterator cache is cleared, the initial scan stays quiet, and a reused PID then produces a distinct start identity and separate added/removed records. It also verifies clearing happens on each scan. Existing tests cover sensors without `cache_clear`, source gaps and bounded process collection.

### Round 8 Verdict

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the minimal PID cache correction.
- This review covers the two-file source correction and its regression. Prior release and hosted verification gates remain applicable.

## Round 9: Independent relay test audit isolation review

Reviewed the two-line fixture correction in `tests/test_node_activity_wiring.py`. The relay fixture now receives `tmp_path` and sets `CLAWMETRY_AUDIT_DB` to its own temporary database before dispatching any action. Inspected `clawmetry.audit._path` and `_connect`: the override is resolved for each connection, so it remains effective even when the audit module was imported earlier. The fixture still uses the stub node store and changes no production behavior.

Validation: `CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-review-audit.db python3 -m pytest tests/test_node_activity_wiring.py -q` passed with 17 tests. The explicit outer override also isolates any audit work outside the fixture during this review run. No broader unisolated suite was run.

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the test-only audit isolation correction.

## Round 10: Independent private node RPC read authorization review

Reviewed only the pending changes to `routes/local_query.py` and `tests/test_node_activity_wiring.py`. The private daemon-token check now covers `query_node_activity` as well as the two node preference/review mutations. It executes before store dispatch, refuses a missing daemon token, and uses constant-time comparison against the full bearer value. This closes the new host-metadata read bypass on the dashboard's legacy RPC path without changing other legacy methods. The normal node API continues through the existing authenticated dashboard route and daemon proxy, which already supplies the discovery token.

Validation: `CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-round10-audit.db python3 -m pytest --noconftest -q tests/test_node_activity_wiring.py` passed with 19 tests. The relay fixture retains its own temporary audit override. An additional isolated Flask smoke check confirmed that missing and incorrect bearer tokens deny node reads with 401, while the valid daemon bearer reaches the stored query and returns 200. No production host store or audit database was used.

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the minimal private node RPC read authorization correction.
- No implementation edits were made by this reviewer. This approval does not broaden the reviewed legacy RPC surface or replace the release and hosted verification gates.


## Round 11: Independent packaging closure review

Scope: only the pending psutil additions in `.github/requirements/docker-runtime.txt`, `deploy/self-hosted/runtime-requirements.txt`, `.github/requirements/ci-wheel-install.txt`, `.github/requirements/ci-sync-test.txt`, `.github/requirements/overhead-bench.txt`, and the regeneration roots in `scripts/resolve_selfhosted_runtime_pins.py`.

Each lock adds exactly the already approved `psutil==7.2.2` block from `ci-tests.txt`, including all 21 SHA-256 values. A deterministic comparison against HEAD confirmed that those lockfiles contain no other dependency edits, duplicate psutil declarations or changed versions. The resolver root now declares the same psutil floor as setup.py. Installed psutil 7.2.2 metadata declares Python >=3.6 and no runtime dependencies, so this addition does not create an omitted transitive closure.

Validation: `CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-packaging-review-audit.db python3 -m pytest --noconftest -q tests/test_docker_runtime_pin.py tests/test_selfhosted_runtime_pin.py tests/test_python_pin_audit_coverage.py tests/test_unpinned_pip_installs_declared.py tests/test_selfhosted_image_publish.py` passed (39 tests). Resolver compilation and diff whitespace checks pass. The full-runtime CI lock candidates now include psutil. The latency-smoke and OSS golden-path files are explicitly partial environment sets followed by a normal dependency-resolving wheel install, so their omission does not cause the complete-closure or no-deps install failure addressed here. Parent separately verifies the official distribution hashes and target Linux architectures with the existing validator.

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the reviewed packaging correction.
- No implementation edits, commit or push were made by this reviewer. Existing release and hosted verification gates remain required.

## Round 12: Independent read deadline, freshness and navigation expectation review

Reviewed the pending `node-activity.js`, `test_node_activity_js.js` and `test_trail_tab_template.py` diff. Each GET now owns a 15-second deadline on its existing controller. The deadline aborts the request, recomputes retained evidence age immediately, and displays a scoped unavailable message. Ordinary read errors also age the retained observation. Navigation clears the old deadline and changes the generation; obsolete requests cannot paint, clear a newer request or restart stopped polling. The still-owned request clears its deadline in `finally` and schedules the existing recovery poll. No new periodic poller, host read or mutation behavior is added.

The tests model the clock and verify stale evidence during a hung read, its deadline abort, pending-state cleanup, a later successful recovery, ordinary error aging and node-switch deadline cleanup. The Trail test change only adds the already-rendered Node activity tab to the Monitoring order and reachability expectations; it preserves the existing navigation assertions.

Validation with an isolated audit override: `CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-round12-audit.db python3 -m pytest --noconftest -q tests/test_node_activity_frontend.py tests/test_node_activity_browser.py tests/test_trail_tab_template.py` passed (12 tests). `node --check clawmetry/static/js/node-activity.js`, `git diff --check` and `python3 scripts/check_english.py` passed. No production audit database was used, and no implementation edits, commit or push were made by this reviewer.

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the read lifecycle correction and navigation test expectation update.
- Release, deployment and actual hosted verification remain the parent's delivery gates.

## Round 13: Browser harness correction and red/green evidence

The critical browser job reached the Node test after its existing session-scoped Playwright context had started. The Node test incorrectly entered a second `sync_playwright` context. Reproduced that exact failure locally by running `tests/test_assistant_evidence_browser.py` followed by `tests/test_node_activity_browser.py` with pytest plugins active: 1 failed, 3 passed, with the same Sync API inside asyncio loop exception as CI.

The test now receives the existing `_shared_chromium` fixture from `tests/conftest.py`, creates its own 320-pixel reduced-motion browser context, and closes only that context. The separate Playwright manager, browser launch and machine-specific Chrome fallback were removed. All original evidence, coverage, history, replay, unavailable-state and overflow assertions remain unchanged. No production code changed.

The identical two-module invocation passed after the correction (4 tests). A combined invocation of `tests/test_node_activity_frontend.py`, `tests/test_assistant_evidence_browser.py` and `tests/test_node_activity_browser.py` then passed (5 tests). Both runs use explicit scratch audit and DuckDB paths. Evidence is in `/tmp/clawmetry-node-qa/browser-harness-red.log`, `browser-harness-green.log` and `browser-harness-green-final.log`. Whitespace checks pass. An independent reviewer was asked to inspect the test-only change before handoff; this entry records the implementation verification and does not claim independent approval.

## Round 14: Independent shared browser fixture correction review

Reviewed the pending test-only correction in `tests/test_node_activity_browser.py` against the existing session-scoped `_shared_chromium` fixture in `tests/conftest.py`. The test now creates its own isolated 320-pixel, reduced-motion browser context from that shared browser and closes only the context in `finally`. It no longer enters a second Playwright Sync context or closes a browser owned by the session fixture. Data collection and DuckDB evidence remain isolated to the test's temporary paths.

An independent AST comparison against HEAD confirms that all 15 test assertions are preserved exactly. The author-provided scratch-run evidence was inspected: the unchanged test failed in the combined browser invocation with the nested Sync API error (1 failed, 3 passed); the corrected combined browser modules passed (4 passed), and the frontend lifecycle plus both browser modules passed (5 passed). Logs are in `/tmp/clawmetry-node-qa/browser-harness-{red,green,green-final}.log`. `git diff --check -- tests/test_node_activity_browser.py` passed. An attempted reviewer-only `--noconftest` registration omitted the shared fixture and produced fixture-setup errors; this was a separate invocation limitation, not a failure of the reviewed combined fixture run. No live server was started by that invocation.

- Total blocking: 0.
- Total advisory: 0.
- **Verdict:** APPROVED for the shared browser fixture correction.
- No implementation edits, commit or push were made by this reviewer. This approval preserves the component-browser proof and does not claim released hosted verification.
