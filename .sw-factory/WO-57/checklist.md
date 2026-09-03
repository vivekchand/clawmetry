<!--lint disable no-undefined-references strong-marker-->

# Work Order Execution Checklist: WO-57

**Work Order Number:** WO-57
**Work Order Title:** Claude Code native telemetry: instrument command, claude_code.* metric/event/span mapping, session join, status
**Initialized At (UTC):** 2026-09-03T17:25:12Z

## Phase 1: Start / Context Gathering

### Required Steps

- [x] Review work order description provided by MCP tool output
  Evidence: WO-57 read via create_work_order/read; scope = instrument cmd + mappings + join + status + docs
- [x] Identify linked requirements and blueprints
  Evidence: Req a4bd3c7e (AC-RSO-CCT-001.1..9) + REQ-OBS-006 (d518c6c3); BP 9ae95403
- [x] Review every connected requirements document
  Evidence: read a4bd3c7e (authored this session) + d518c6c3 L100-160 (REQ-OBS-006)
- [x] Review every connected blueprint document
  Evidence: read 9ae95403 (authored) + e42834c9 L90-220 (WO-7 intake) + 40e35d24 L940-1003 (OTLP materializer)
- [x] Follow `@…` mentions **and links** to other blueprints in linked documents and read each referenced blueprint via MCP
  Evidence: followed to Local Agent Observability + Runtime and Session Observability + Extended Runtime Support L555-580 (Gemini OTel lane)
- [x] Review every referenced blueprint discovered that way; add them to **Referenced Blueprints** in `context.md`
  Evidence: context.md updated via update-context-index.sh
- [x] Extract acceptance criteria from requirements
  Evidence: AC-RSO-CCT-001.1..9 mirrored into docs/acceptance_criteria.json
- [x] Identify architecture path from blueprints (components, contracts, composition)
  Evidence: instrument_claude.py (CLI) -> settings env; dashboard.py live OTLP handlers -> put_otlp_batch (kwargs, one hop/batch); routes/meta.py status; turn_anatomy wait spans
- [x] `context.md` is filled or updated with `execution/scripts/update-context-index.sh` for Work Order, connected requirements, connected blueprints, referenced blueprints, and known delivery links
  Evidence: done (branch cc-native-otel; PR link added at handoff)

- [x] **Certification: Phase 1 complete. Proceeding to Phase 2.**

## Phase 2: Planning And Implementation

### Implementation Plan

(see `execution/writing-implementation-plans.md`)

- [x] Implementation plan documented in `implementation-plan.md`
  Evidence: 10 steps, verified facts section
- [x] Testing section documented in `implementation-plan.md`
  Evidence: step 10 + test files named

### Implementation

- [x] Implemented changes are scoped to the Work Order
  Evidence: 22 files; no UI tab; hosted-cloud receiver untouched (out of scope)
- [x] Tests added or updated for changed behavior
  Evidence: tests/test_instrument_claude.py (13), tests/test_otlp_claude_code_signals.py (7); 4 existing tests retargeted to the new contract (prefixed events key, JSON metrics 200)
- [x] Documentation, generated files, fixtures, migrations, or config updated where relevant
  Evidence: docs/enterprise.md, docs/OPENTELEMETRY.md, CHANGELOG.md, acceptance_criteria.json + ac_coverage_baseline.json (92/162)

- [x] **Certification: Phase 2 complete. Proceeding to Phase 3.**

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
