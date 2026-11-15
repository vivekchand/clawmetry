# Guard security boundaries and timely incident handling

## Summary

Close verified gaps on current main: exact approval binding, timely durable security detection, single workspace crossings, security priority and precise protection evidence. Reuse existing runtime gates, policy and incident stores, native isolation and scanner provenance. Observation stays default. Release and hosted verification are required.

## Code Reuse And Package Structure

- Identity: add import-light `clawmetry/approval_binding.py`; integrate `approvals.py`, `routes/hooks.py`, `claude_code_gate.py` and `runtime_gates.py`.
- Detection: reuse `detectors.py`, `detector_behaviour.py`, `detector_money.py`, signature tables, incident persistence and policy latches. Share ranking across route and browser consumers.
- Ingest: add `clawmetry/security_ingest.py`; reuse the committed event-change journal, daemon-owned store, bounded incident windows, post-commit wakeups and node settings.
- Coverage: extend existing Guard session responses and encrypted snapshots. Separate observation, hook decisions, containment, sandbox and scanner states.
- Tests: add regressions to CI lists. Use real runtime drills for behavior claims.

## Components And Flow

`ApprovalBinding` creates a versioned strict canonical JSON digest over complete arguments and context. Resume and dedupe compare runtime, session, exact tool, cwd, call ID and source/kind. Changed remembered grants require review. Known pending protected calls deny on verification or transport failure. No-policy and entitlement behavior keep existing authority.

`SecurityIngestService` pages committed event changes by monotone journal position and epoch. It groups exact node/runtime/session scopes and checks bounded windows, including completed sessions. Progress persists after durable handling; failed evidence retries. Operational trajectory scans retain their timer. Ended sessions receive no new controls.

`SecurityBoundaryDetection` checks lexical POSIX and Windows path components. It reports declared mutations without claiming syscall or symlink evidence. Critical security outranks operational spend; operational order remains. Legacy signatures share the durable incident and explicit-policy path without HTTP requests.

`ProtectionEvidence` separates installation, observed decisions, containment and independent native sandbox/scanner evidence. Unknown remains unknown. Cloud transport stays encrypted with browser decryption.

## Steps

1. Write Factory requirement and blueprint before product code. Record current-main audit and existing work.
2. Repair approval binding and protected pending-call failure behavior. Independent from detector paths/ranking.
3. Repair workspace scope and security ordering across daemon/API/browser.
4. Add bounded incremental security processing and pure legacy-signature reuse with durable persistence.
5. Add precise coverage evidence to existing Guard and encrypted hosted views. Reuse native sandbox/scanner mechanisms.
6. Run regressions red before fixes and green after. Run focused suites, resource checks and real harmless runtime drills.
7. Obtain delegated independent review and resolve blocking findings.
8. Rebase, PR, green CI, merge, separate release, verify wheel, promote cloud and verify served artifact, decrypted snapshot and Guard surface.

## Testing

- Approval substitution: runtime/session/tool/content/cwd/call/source mismatches; JSON key equivalence, array/type differences, legacy grants miss.
- Transport, malformed response and persistence failure during protected wait never allow. Native question and permission retain human review.
- Incremental processing: completed sessions, delayed timestamps, tied pages, restart, retry, dedup, bounded idle work, no ended-session controls.
- Paths: sibling prefixes, traversal, root, relative paths, missing cwd, Windows drives/case/UNC, read-only calls, redaction and unknown symlinks.
- Ranking: critical security over expensive operations, operational behavior, malformed/NaN/infinite values, consumer parity and workspace headlines.
- Signature scanning without Flask and durable redacted findings across retries and page reads.
- Coverage: install is not verified; absent independent source stays unknown; runtime filtering and encrypted snapshot parity.
- Run focused pytest, English checker, module-map regeneration, acceptance coverage, syntax/lint and required CI. Register new test files.
- Real drills use isolated runtime homes, harmless temporary targets, absence of denied side effects, and recorded runtime/store/UI evidence.

## Completion Evidence

Keep the full objective active until every requirement, independent review, release, deployment and live verification is evidenced. Partial progress is not completion.

## Scoped policy-latch follow-up

Acceptance criteria AC-GOV-SBG-002.2/.4 require exact node/runtime/session response state across both producers. Store schema19 uses readable node_id/runtime/session_id/policy_id/step_index as the policy_actions primary key. Startup rebuild/copy/stamp occurs atomically; old unknown node scope stays explicit and blocks compatible complete ladders instead of authorizing a restart or escalation. Scope-aware methods preserve strict read failure propagation and never drop exact scope for older method signatures. The pure policy engine evaluates per scope using exact facts; persisted first-seen memo keys are readable tagged JSON arrays. Audit rows and the Guard history retain native IDs and show node/runtime or unknown labels.

Verification includes the actual-store node/runtime red regressions, migration of known/NULL runtime history, long native identities, independent rung state across restart, failed-copy rollback and retry, scoped facts/duration collisions, strict/periodic shared latch, and JavaScript audit rendering. Independent review remains the completion gate for this follow-up.

## Load-review refinement

A retained 100,000-change journal can defer fresh completed-session evidence beyond its freshness window under the CPU budget. Per Factory ADR-004, inspect one bounded priority page before FIFO backfill, retain complete FIFO ownership of skipped intervals, atomically commit both positions, and show pending history. Startup/recovery handoff is explicit; healthy drains never repeatedly jump on a moving head. Seven independent actual-store regressions prove early detection, complete later coverage, restart, failure rollback, policy/outbox deduplication and aging overlap.
