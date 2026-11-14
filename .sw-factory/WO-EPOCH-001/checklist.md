# WO-EPOCH-001 execution checklist

- [x] Scope and existing contract reviewed against AGENTS, FLYWHEEL and CLAUDE.
- [x] Existing source, shared normalizers, affected query paths and concurrent PRs inspected.
- [x] Requirement, architecture, exclusions and risks recorded before implementation.
- [x] Implementation plan written before code.
- [x] Meaningful baseline reproduced against unchanged source and released plugin.
- [x] Shared source parser and five related query expressions implemented.
- [x] Raw events, unknown-clock costs, basic dates, numeric seconds/milliseconds and local/DST semantics covered.
- [x] Independent exact-source review approved; findings resolved and recorded.
- [x] Full selected verification complete:281 tests passed, zero skips; Python compilation and whitespace checks passed.
- [x] Fresh-main feature PR6584 opened with evidence.
- [ ] Final feature head has all CI green before merge.
- [ ] Separate RELEASE merged; actual published wheel inspected.
- [ ] Parent receives immutable release evidence for downstream deployment and live verification.
- [SKIP] Direct browser, model, gateway and physical-robot activity in this worktree. Reason: shared persistence fix; production acceptance is owned by the coordinating release task and is not substituted by unit tests.
