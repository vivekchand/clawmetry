# Implementation Plan: WO-NODE-PART-001

## Summary

Keep current positive observations visible when a source remains partial. Add private durable process-sighting deduplication, with quiet initialization, bounded retained history and explicit saturation. Existing full-comparison removal and recovery rules remain unchanged.

Requirement `d33e1d0b-43c1-4d3f-8d0d-8de6628d0583` and design `2dffd534-2073-4af2-b943-d6dbed701ee1` were persisted and read back before this plan or implementation. Root approved the contract. The original Node activity composition and feature blueprint remain the architecture baseline.

## Code Reuse And Package Structure

Reuse the existing daemon-owned `NodeActivityStoreMixin`, metadata JSON helpers, writer lock and transaction, stable source/PID/start identities, event retention and generic encrypted response. No collector limit, cadence, endpoint, dependency or cloud transport changes are required.

Backend changes belong in `clawmetry/node_activity_store.py` and focused tests in `tests/test_node_activity.py`. Mirror the eight acceptance criteria into `docs/acceptance_criteria.json` and tighten the existing coverage ratchet. UI delegate owns only the feature JavaScript/template/CSS and its focused frontend/browser checks. Execution records live in `.sw-factory/WO-NODE-PART-001/`.

## Components And Flow

`NodeActivityCollector` remains unchanged. `record_node_activity` receives its existing source-qualified observation and updates source state, public rows, sightings and events in one writer transaction.

All partial entity sources deduplicate incoming rows first, stamp `observed_at` and `stale=false`, then append only unseen prior rows with `stale=true`. Prior row times remain unchanged; missing legacy times become null. Respect the current process, listener, selected-file and login caps.

Private `process_sightings` metadata keeps source identity, initialized flag, sticky history-limit flag and stable identity to last-positive-time mapping. It is separate from the existing complete-comparison baseline. Its retention follows the event window and its capacity is 16,384 identities. Same-source collection gaps and disable/re-enable reset initialization but preserve unexpired known IDs. A genuinely changed source identity establishes a quiet new context. Restart preserves persisted knowledge.

On the first readable data-bearing scan, retain identities quietly. A later partial scan can create only a retainable informational `process_observed` event for an unknown identity. The title is `A process was first observed`; detail and evidence qualify retained history, partial coverage, unknown attribution and absence of proof of an actual start. Complete-comparison events must not duplicate a sighting already retained through partial coverage. Partial-to-complete comparison rebaselines remain quiet.

Saturation preserves unexpired identities and suppresses unknown positive events. Public process coverage adds `sighting_history_limited` and a factual visible reason. Pruning, restart, ordinary gaps and re-enable do not clear this state. Only a quiet complete scan with a fitting full dedup set or a genuinely new source identity can reset it safely.

The existing stored API and encrypted `nodeActivity` snapshot expose only safe current/stale rows and qualified events. The private sighting ledger is never added to query responses or snapshots. UI changes show observation ages and the explicit history limit using existing polls and clocks.

## Steps

1. Mirror verified Factory records, create execution context and save this plan before editing product files.
2. Add failing regression tests for the 512-row freeze, current-first per-source merge, positive partial sightings, durable dedup and sticky saturation. Record red results before implementation.
3. Implement current-first row projection and the independent bounded sighting state machine. Preserve full-comparison gap behavior and private data boundaries.
4. Add source transition, migration, retention, saturation reset and preference re-enable tests. Mirror eight criteria and tighten the coverage ratchet.
5. UI delegate implements explicit row ages, mixed-age headings and coverage-limit display with executed rendering tests.
6. Obtain independent root/backend/UI review, resolve blockers and run focused verification plus repository drift checks. Update execution checklist and review log.
7. Create an isolated correctness PR after refreshing against main. Root owns final release, actual-node probe and hosted deployment verification. No production node changes occur during implementation.

## Testing

Use scratch audit/store paths for every local test invocation. Unit tests exercise a full stale cap followed by rotating incoming observations for processes and the other sources; unknown legacy row times; quiet migrated/initial partial baselines; distinct PID/start identities; no inferred removals; partial/full transitions; cap rotation; restart; same-source gaps and re-enable; source changes; retention expiry; sticky saturation and safe complete rebaseline; atomic dedup/event state; and absence of private ledger fields in public responses.

Run `python3 -m pytest --noconftest -q tests/test_node_activity.py tests/test_node_activity_wiring.py tests/test_node_activity_frontend.py`, the combined shared-browser fixture checks under isolated audit/store paths, `python3 scripts/check_ac_coverage.py`, the English checker, syntax checks, daemon allowlist and module-map drift checks as relevant. First demonstrate the focused new guards fail on unchanged code, then pass after the fix. Parent will verify a new harmless process on an already capped real node after the corrected wheel is released; unit data and local component tests do not substitute for that proof.

## Implementation Evidence

The nine focused new regressions failed before the store change (log `/tmp/clawmetry-node-qa/node-partial-backend-red.log`). The corrected backend, existing wiring and frontend runner then passed 50 tests. Additional backend guards cover measured PID/start reuse during a real collector's capped scan, the full 512-row rotation, migration, transaction rollback and sticky saturation across store restart and preference changes. These are isolated component checks, not real-node release proof.

Acceptance coverage now includes all eight exact Factory criteria: 382 of 450 covered, with the original 68 uncovered unchanged. Product Python lint, Python 3.9 annotation compatibility, daemon allowlist, module-map drift, CI test-file coverage, JavaScript syntax and executed lifecycle checks pass. The English checker reports 4,601 extracted messages with no mechanical findings. Direct lint of the existing backend test file additionally reports two pre-existing single-line `with` statements outside this correction; the repository product lint scope does not include tests.

Root confirmed the approved strict saturation reset; timed partial recovery remains out of scope. Factory MCP is not exposed to this execution agent. Verified requirement/design readbacks supplied by the record-owning delegate are copied into this work order, and the linked original blueprints were read from the delegate's fresh Factory readback and the original checked-in execution record.

## Independent Review Correction

The frontend delegate's independent backend review identified that a real disabled collector batch uses a sentinel source identity. Two real disabled-batch guards first failed, including the saturated-ledger case (`/tmp/clawmetry-node-qa/node-partial-disabled-red.log`). Namespace changes now require a complete source or a data-bearing partial source. Disabled, unavailable, unsupported and empty partial gaps preserve prior inventory/sighting namespaces, unexpired identity knowledge and sticky history limits while resetting quiet initialization. The final focused suite passes **56 tests**. Root independently approved the integrated correction; delegated frontend review also passed the normal shared-browser fixture with **5 tests**.

Before PR preparation, open PRs and recent non-bot issue comments were surveyed; no competing Node activity partial-observation work was found. Fresh `origin/main` remains the release base `319e7910198be7ebf4cad91f52ad9f817f266d27`.

The exploratory screenshot exposed a misleading fixed actor connector. The frontend delegate removed that visual inference with a hidden spacer and explicit node-to-target link copy. Its rendered guard reproduced red before correction, then passed for unknown, human and agent selections. Independent root and frontend-bucket review approved the final UI; the shared browser group again passed five tests.
