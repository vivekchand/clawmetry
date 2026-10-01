<!--lint disable no-undefined-references strong-marker-->

# Work Order Execution Checklist: WO-DEC-002

**Work Order Number:** WO-DEC-002
**Work Order Title:** Mandatory local assessment masking and scoped restoration
**Initialized At (UTC):** 2026-10-01T09:10:32Z

## Phase 1: Start / Context Gathering

### Required Steps

- [x] Review work order description via GitHub CLI (Factory MCP unavailable)
- [x] Identify linked requirements and blueprints
- [x] Review every connected requirements document
- [x] Review every connected blueprint document
- [x] Follow `@…` mentions **and links** to other blueprints in linked documents and read referenced contracts through the signed-in Factory browser (retained context)
- [x] Review every referenced blueprint discovered that way; add them to **Referenced Blueprints** in `context.md`
- [x] Extract acceptance criteria from requirements
- [x] Identify architecture path from blueprints (components, contracts, composition)
- [x] `context.md` is filled or updated with `execution/scripts/update-context-index.sh` for Work Order, connected requirements, connected blueprints, referenced blueprints, and known delivery links

- [x] **Certification: Phase 1 complete. Proceeding to Phase 2.**

## Phase 2: Planning And Implementation

### Implementation Plan

(see `execution/writing-implementation-plans.md`)

- [x] Implementation plan documented in `implementation-plan.md`
- [x] Testing section documented in `implementation-plan.md`

### Implementation

- [x] Implemented changes are scoped to the Work Order
- [x] Tests added or updated for changed behavior
- [x] Documentation, generated files, fixtures, migrations, or config updated where relevant

- [x] **Certification: Phase 2 complete. Proceeding to Phase 3.**

## Phase 3: Review And Verification

### Review

- [x] Review subagent spawned per `execution/review-phase.md` and returned a verdict
- [SKIP] All acceptance criteria from the Work Order and linked requirements are satisfied
  Skip reason: The seven mirrored local primitive criteria pass. Real evidence selection, first-hop/provider integration, persisted job/snapshot inspection and provider E2E remain in DEC-003 and issue #2549. No managed assessment is activated by this staged delivery.
- [x] Architecture is aligned with linked blueprints, or documented drift is accepted
- [x] Exploratory pass on user-visible or external behavior — not only automated tests; for browser apps, use browser-based testing if available. Brief notes in `review-log.md` or evidence.
- [x] Latest `review-log.md` verdict is `APPROVED`

- [x] **Certification: Phase 3 local implementation review complete with the explicit integration deferral above. Proceeding to staged handoff.**

## Final Completion Check

- [x] All phase certifications above are complete for this staged handoff
- [x] Checklist is fully filled out with evidence
- [x] Review log is complete (`review-log.md`)
- [x] Implementation plan was followed (`implementation-plan.md`)
- [x] All intended files are present in the working tree
- [x] Work order status updated to `in_review` in context.md; GitHub #2549 remains open for the integration evidence above

## Evidence

Context reused from the completed assessment/managed-mode Factory read and saved ADR-004 amendment in WO-63/DEC-001. Read the actual current redaction validators, strict/fallback boundaries, endpoints egress controls, judge caller, privacy tests and egress disclosure. No human claim for this component; related advisory #6122/#6077 have planning comments only and are unchanged. Isolated worktree starts at origin/main 0e213af336. Pure local component only; no provider call or live assessment claim.

Parent verified 104 existing redaction/PII/egress tests passing before new-module tests. Factory blueprint now contains the explicit initial ASCII-English/identifier-only coverage and integration gates; saved text verified after browser reload. Added four OS/Python privacy CI cells using the existing marker-aware hash-pinned dependency set.

Final local verification: parent independently reproduced **240 passing tests**, no skips, covering assessment privacy, shared redaction, egress suppression, enterprise endpoints, OTLP redaction and opt-in cloud egress. The isolated cloud venv lacks optional opentelemetry-proto (225 passed, one module skipped); the full run used the existing Python environment with that optional dependency installed. No test was weakened. The scanner suite includes 6,656 exact boundary-offset cases within those tests.

Dedicated review returned APPROVED after resolving secret suffix, regex resource, scan-window, IBAN boundary/case and ambiguous numeric-tail findings. Parent Ruff passes for the new module/test; Python 3.9 annotation guard passes 316 files. Module map and AC ratchet pass (299/367 covered; existing 68 uncovered unchanged). Workflow/metadata checks passed previously; the AC guard exposed a missing pre-existing AC-GUX prefix, corrected in metadata and verified without changing assertions.

This records a reviewed implementation handoff, not live delivery. Green CI and required Drift review, merge, separate release, published-wheel inspection and cloud promotion remain delivery steps. Browser testing is not applicable to this pure local component; independent fake-transport/adversarial exploratory probes are recorded in review-log.md.
