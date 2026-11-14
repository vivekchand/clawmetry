<!--lint disable strong-marker-->

# Review Log: WO-NODE-PART-001

**Work Order:** WO-NODE-PART-001 — Keep partial node observations current and record positive sightings
**Initialized At (UTC):** 2026-10-15T12:05:52Z

This file records review and verification rounds. Append new rounds; do not overwrite prior rounds.

---

## Round 1: Independent integrated review

Reviewer: root (verdict relayed to the implementation delegate for recording).

### Requirements and blueprint alignment

APPROVED against the follow-up requirement and design, including incoming-first per-source caps, row times, separate private persistent positive ledger, quiet epochs, sticky saturation/reset and unchanged no-removal rules for partial sources. Root's first review remained provisional after the frontend delegate found the disabled identity seam. Final review independently re-read the shared readable-source identity helper and disabled/unavailable/unsupported/empty-partial sentinel regressions.

### Architecture, conventions, security and privacy

The correction stays inside daemon-owned store projection and metadata. The ledger persists atomically with events, remains bounded and private, and does not add host reads to routes or expand attribution/control. Root found no blockers or additional advisory issues beyond declared polling limits.

### Tests and build

Root independently ran the final backend/wiring/frontend set with scratch audit/store paths: **56 passed**. The combined frontend + Node browser + assistant evidence browser command passed **5 tests**. An initial browser command had a filename typo and ran no tests; the corrected command produced the reported five passes. Diff whitespace check was clean.

### User-facing verification

The shared-browser checks cover the 320-pixel surface and actual collector payload rendering, existing replay/older-review behavior and unavailable evidence. Actual owned-process visibility on an already capped monitored node remains a post-release validation task; local component tests do not claim that deployment result.

### Verdict

**APPROVED.** Blocking: 0. Advisory: 0. This review authorizes preparing the feature PR; root retains merge and release ownership.

---

<!-- Subsequent rounds: copy the structure above and increment the round number. -->

## Round 2: Independent frontend review

Reviewer: node_backend, reviewing the frontend delegate's files only.

### Requirements and blueprint alignment

Reviewed the eight follow-up criteria and design addendum against the JavaScript/template/frontend-test changes. Per-row observation times use the stored row timestamp; stale legacy rows state that time is unknown. Mixed-age inventories use observation headings. Process history saturation is visible in both status and coverage, independently of the collection reason. Informational sightings are counted as events. No collection, process-control or attribution behavior was added.

### Architecture, lifecycle, security and privacy

Changed values are escaped before insertion into HTML; the new note text uses textContent. Existing polling, read deadlines, mutation scopes and replay lifetimes are unchanged. No new timer, host read or cloud metadata path exists. No blocking or advisory findings.

### Tests and user-facing verification

Independently ran the executed JavaScript lifecycle/render suite, JavaScript syntax and English checks successfully. Independently ran the normal shared Chromium fixture with Node activity frontend + Node browser + assistant evidence browser: **5 passed**. The test process used an empty scratch HOME, scratch audit/store paths, no gateway token, a loopback port with no server, and the existing Playwright browser cache. This avoided production discovery and preserved the shared fixture owner. Existing 320-pixel layout, replay, old review access and unknown-data assertions remain intact. This is local component/browser proof; actual capped-node probe validation remains a release task owned by root.

Files reviewed: `clawmetry/static/js/node-activity.js`, `clawmetry/templates/tabs/node-activity.html`, `tests/test_node_activity_frontend.py`, `tests/test_node_activity_js.js`, `tests/test_node_activity_browser.py`.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0.

## Round 3: Independent backend review after readable-source correction

Reviewer: node_ui, reviewing backend store, tests, acceptance manifest and execution design.

### Requirements and blueprint alignment

Reviewed all eight follow-up criteria against the Factory requirement, saved design addendum, implementation plan and final store diff. Incoming rows win each source's cap, stale evidence preserves its prior time and legacy times remain unknown. The private process-sighting ledger is separate from full-comparison state, bounded by retained history and 16,384 identities, and saved atomically with events. Initial and post-gap scans remain quiet. Repeated known identities survive cap rotation, restart, re-enable and coverage transitions. Saturation suppresses untrackable positives, remains sticky and resets only at the declared safe boundary. First-observed events qualify retained history and do not invent starts, removals, recovery or attacker identity.

### Resolved finding and fresh review

The first review found a blocking seam: a real disabled collector batch uses a sentinel source identity, which initially cleared retained dedup and saturation as if a new namespace had been observed. The author corrected identity transitions to require a readable complete scan or a data-bearing partial scan. Disabled, unavailable, unsupported and empty-partial gaps now preserve prior inventory and unexpired identity knowledge while resetting quiet initialization. Fresh regressions include actual disabled collector batches with ordinary and saturated ledgers, plus every sentinel gap state. The final empty-partial boundary was re-read and tested before this verdict. No remaining blocker or advisory finding was found.

### Architecture, security and privacy

Collection limits, cadence, routes, cloud transport, attribution and control boundaries are unchanged. Public projection removes private fields; ledger state stays in daemon-owned DuckDB metadata. The writer transaction rolls back events and identity knowledge together on failure. Focused tests cover that rollback and prove the ledger is absent from public responses. No production credential or node was used for this review.

### Tests and verification

Independently ran `CLAWMETRY_AUDIT_DB=/tmp/clawmetry-node-qa/partial-review-audit.db CLAWMETRY_LOCAL_STORE_PATH=/tmp/clawmetry-node-qa/partial-review.duckdb python3 -m pytest --noconftest tests/test_node_activity.py tests/test_node_activity_wiring.py tests/test_node_activity_frontend.py -q`: **56 passed** on the final boundary correction. Disabling conftest for these self-contained suites prevents live-server discovery. The acceptance traceability gate passed at 382/450 covered criteria with the ratchet holding. JavaScript syntax and diff whitespace checks passed. The requested accessible replay fallback now says `Recorded event`, and its existing executed JavaScript suite passed in this focused run.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0. Actual capped-node process visibility remains a post-release verification task owned by root. Reviewer made no backend implementation edit, commit or push.

## Exploratory Component Evidence

After the independent verdicts, node_backend collected actual host observations into an isolated in-memory DuckDB store and a temporary selected-file home, then started an owned harmless Python child and collected again. Coverage remained partial with 512 retained rows. PID 24992 was current and generated exactly one `process_observed` event. No synthetic telemetry was inserted. Only that owned child was terminated afterward; the production daemon and stores were untouched.

The resulting actual stored payload was rendered through the feature template and JavaScript in an isolated browser page. Screenshot `/tmp/clawmetry-node-qa/node-partial-exploratory.png` was visually inspected: qualified first-observed detail, Unattributed actor, current process row/time, unknown capped total and collection warning are visible. This is exploratory component evidence, not proof of the published daemon or cloud deployment. Final review verdict remains **APPROVED**.


## Round 4: Actor connection correction and author verification

Author: node_ui. This is a correction record and author verification, not an independent approval.

### Concrete finding

Root inspected `/tmp/clawmetry-node-qa/node-partial-exploratory.png` and found a blocking visual attribution error after the earlier reviews: the generic left map edge was vertically centered on the Agent row even when Unattributed was selected. Highlighting the selected actor did not prevent the edge from implying an evidenced Agent relationship. The same placement could mislead for a Human event.

### Narrow correction

The left grid slot now remains invisible for every actor kind and contains no animated travel element. This preserves the existing layout while removing the unsupported actor edge. Recorded actor highlights and evidence remain available. The node-to-event-target link remains visible, and the accompanying text explains its meaning. No geometry calculations, resize listeners, polling or attribution logic were added.

### Red and green evidence

The browser regression failed before the CSS correction with actual computed visibility `visible` instead of `hidden` for an Unattributed selected event. After correction it passes for the real persisted test-store event, then explicitly exercises Human and Agent UI contract highlights and proves the actor slot stays hidden while the node-to-target link remains visible. These contract assertions do not claim actual collector attribution. Existing 320-pixel overflow, replay, selected evidence and unavailable-data assertions remain intact.

The isolated component invocation used the existing shared Chromium owner with a temporary wrapper overriding the live-server fixture. The wrapper makes any dashboard readiness probe raise an assertion; scratch audit/store paths and a closed loopback URL were also supplied. Red log: `/tmp/clawmetry-node-qa/partial-map-red.log` (one expected failure). Green log: `/tmp/clawmetry-node-qa/partial-map-green.log` (**1 passed**). The focused executed JavaScript/frontend suite passed (**1 passed**). English extraction passed with zero mechanical findings, and `git diff --check` passed.

Status: author verification complete; root and node_backend independent review requested before commit or PR.

## Round 5: Independent actor-map correction review

Reviewer: node_backend, reviewing only the frontend delegate's actor-map correction. Root independently reviewed the same correction and approved it.

### Requirements, architecture and privacy

The prior fixed left connector aligned with Agent regardless of the highlighted actor. The correction keeps its grid spacer hidden for every actor kind and removes its travel span, so no actor-to-node relationship is invented. The remaining visible link connects the node with the selected event target; the new caption states this explicitly. Actor highlighting and evidence remain unchanged. CSS visibility preserves layout without geometry reads, timers, requests or attribution inference. No remaining blocker or advisory finding.

### Independent verification

Ran the normal shared Chromium fixture under a scratch HOME/audit/store, empty token and intentionally closed loopback port: Node frontend + Node browser + assistant evidence browser **5 passed**. The rendered regression asserts the actor gap is hidden for unknown, human and agent selections while the target connector remains visible. Existing selection, old-review, reduced-motion and 320-pixel assertions still pass. JavaScript syntax, English extraction and whitespace checks pass. This closes the concrete screenshot finding; released-daemon and hosted verification remain root-owned.

Files reviewed: `clawmetry/static/css/node-activity.css`, `clawmetry/templates/tabs/node-activity.html`, `tests/test_node_activity_browser.py`.

**Verdict: APPROVED.** Blocking: 0. Advisory: 0.
