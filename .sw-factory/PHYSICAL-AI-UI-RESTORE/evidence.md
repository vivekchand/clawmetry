# Verification evidence

Before implementation, four new route regressions failed on the published source behavior: installed /robotics replaced, missing dark setting, absent hardware metadata and unvalidated hardware selection. The JS hardware test also failed because both families remained visible. After changes those guards pass.

- 59 focused route/extension tests pass.
- Node Physical AI UI harness passes hardware selection, source-specific event clearing, absent-matching-hardware state and requested-run hardware isolation, retaining lifecycle/deadline/privacy checks.
- Actual native recording run535dbf83af5849969f3e3d34d266d72d is replayed through a separate daemon, owned DuckDB and dashboard query proxy. /private/tmp/physical-ai-ui-restored-native/report.json records366actualevents/22namedjoints, dark computed background, Jumper -> emptyAsimov -> Jumper selection, zeroJSerrors and mobile no-overflow. This is source-candidate verification, not a released or hosted claim.
- Original localhost:8900/robotics independently returned200 with dark template/hardware-select. No original assets deleted or user process/database modified.
- Independent core reviewer approved with122tests, Node harness, diff check and fresh native proof at /private/tmp/physical-ai-independent-06xr55ui. Final published/cloud/private workbench artifact qualification remains pending.


## CI-discovered Assistant renewal timeout race
MOAT on fd37fd077f failed the existing deadline assertion with the fixed sync-unavailable text. The pre-repair executor is byte-identical to origin/main (SHA256 bf077f589f4e8569e70f7727f5ba1c54eb407e77ce21945c487df9eac560b8ac); no Assistant files were changed by the UI restoration. Original focused test passed in0.88s and preceding route/stream group passed93 with2skips in19.90s, so ordinary rerun success did not invalidate the timing finding.

A deterministic new test blocks actual Receipts.fail completion with Events. Before the repair, its renewing read through assistant_http.rpc -> LocalStore -> Executor.read failed with TimeoutError at job.renew/job.check, exactly the exception HTTP maps to sync unavailable. A separate scratch pytest hook delaying timeout receipt storage0.4s reproduced the exact original CI error before the repair and the unchanged original deadline test passed under that same delay after the repair. No tracked test sleep, production deadline, expected error, fixture transport or admission limit was increased/weakened.

The four-line source correction catches TimeoutError only around lease renewal and calls abort(timeout=True), then returns the existing journal. It does not mark terminal, synthesize a failure, renew the expired lease, alter receipt state, commit history or release admission. The existing consumer still persists the authoritative failure before publishing the terminal error, and producer completion still owns admission release. Existing Cancelled handling, force-identity/lease commit checks and successful terminal result behavior are unchanged.

Verification:
- New receipt-barrier regression red before product edit: TimeoutError at the exact renewing RPC; green after repair. Its final receipt equality assertions separately passed after addition (0.55s).
- Original deadline plus receipt-barrier regression:2passed in1.15s.
- Route/stream preceding group plus executor, relay and real-store pipeline:126passed,2skipped in31.95s. Includes stale cancel versus renewal, authenticated lease preparation, cancellation while waiting for writer, atomic commit rollback, disconnect after commit, idempotent result replay, restart recovery and bounded admission cases.
- Scratch delayed-storage reproduction with repaired source:1passed in1.04s, with no read RPC exception.
- git diff --check passes. No provider API, production node, database or user process was used; tests own temporary stores and controlled providers.

Repair source/tests/docs frozen for root independent review before a separate commit or push. This evidence does not claim release or hosted delivery.
