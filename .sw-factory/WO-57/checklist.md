<!--lint disable no-undefined-references strong-marker-->

# Work Order Execution Checklist: WO-57

**Work Order Number:** WO-57
**Work Order Title:** Claude Code native telemetry: instrument command, claude_code.* metric/event/span mapping, session join, status
**Initialized At (UTC):** 2026-09-03T17:25:12Z

## Phase 1: Start / Context Gathering

### Required Steps

- [ ] Review work order description provided by MCP tool output
- [ ] Identify linked requirements and blueprints
- [ ] Review every connected requirements document
- [ ] Review every connected blueprint document
- [ ] Follow `@…` mentions **and links** to other blueprints in linked documents and read each referenced blueprint via MCP
- [ ] Review every referenced blueprint discovered that way; add them to **Referenced Blueprints** in `context.md`
- [ ] Extract acceptance criteria from requirements
- [ ] Identify architecture path from blueprints (components, contracts, composition)
- [ ] `context.md` is filled or updated with `execution/scripts/update-context-index.sh` for Work Order, connected requirements, connected blueprints, referenced blueprints, and known delivery links

- [ ] **Certification: Phase 1 complete. Proceeding to Phase 2.**

## Phase 2: Planning And Implementation

### Implementation Plan

(see `execution/writing-implementation-plans.md`)

- [ ] Implementation plan documented in `implementation-plan.md`
- [ ] Testing section documented in `implementation-plan.md`

### Implementation

- [ ] Implemented changes are scoped to the Work Order
- [ ] Tests added or updated for changed behavior
- [ ] Documentation, generated files, fixtures, migrations, or config updated where relevant

- [ ] **Certification: Phase 2 complete. Proceeding to Phase 3.**

## Phase 3: Review And Verification

### Review

- [ ] Review subagent spawned per `execution/review-phase.md` and returned a verdict
- [ ] All acceptance criteria from the Work Order and linked requirements are satisfied
- [ ] Architecture is aligned with linked blueprints, or documented drift is accepted
- [ ] Exploratory pass on user-visible or external behavior — not only automated tests; for browser apps, use browser-based testing if available. Brief notes in `review-log.md` or evidence.
- [ ] Latest `review-log.md` verdict is `APPROVED`

- [ ] **Certification: Phase 3 complete. Proceeding to Final Completion.**

## Final Completion Check

- [ ] All phase certifications above are complete
- [ ] Checklist is fully filled out with evidence
- [ ] Review log is complete (`review-log.md`)
- [ ] Implementation plan was followed (`implementation-plan.md`)
- [ ] All intended files are present in the working tree
- [ ] Work order status updated to `in_review`
