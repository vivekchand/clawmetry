# Review log: WO-JUMPER-OSS

Review pending combined implementation and real publisher verification. Independent reviewers own verdicts.


## Independent store/query/snapshot/alerts review, round 1

Reviewer: runtime_gate_diagnosis. Scope: current uncommitted JUMPER-OSS projection bucket relative to HEAD, including asimov/journal.py, asimov/store.py, local_store.py, sync.py, query_contract.py, routes/local_query.py, physical_ai/alerts.py, incident_alerts.py and their focused tests. No implementation edits performed. Requirements/blueprint and existing daemon, notification and query contracts inspected.

### Requirements and blueprint alignment

- AC-JUMPER-001.2 and AC-JUMPER-003.1/2/3: known Jumper sources use the existing daemon writer/projection, generic queries and encrypted snapshot. Legacy Asimov APIs remain strictly source filtered. Alert dispatch occurs after transaction commit and lock release, uses fixed text, existing preferences, persisted cooldown and actual shared channel receipts. No simulator dependency or private paid import enters this bucket.
- Blueprint cursor contract is not fully implemented on the generic query/relay route; see finding R1 below.

### Findings

- **R1, blocking (P2), routes/local_query.py:_coerce_args / AsimovLocalStore.runs; blueprint alignment and input validation.** Generic physical_ai_runs accepts malformed or incomplete cursor values unchanged. For example, before_run_id alone is forwarded and silently ignored by runs(), returning the first page; bad before_ns reaches store access before failure. physical_ai_events with after="garbage" is silently coerced to zero, replaying the beginning. The dedicated Physical AI HTTP routes reject these inputs, so transports disagree, and the blueprint explicitly promises malformed cursors reject before store access. Apply strict common validation for complete run cursors, bounded scalar filters and event continuation across generic q/1 and relay dispatch; cover malformed/half cursor cases without accessing the store. This is bounded to new physical_ai shapes; changing legacy shapes is unnecessary.

### Tests and actual publisher projection

- `python3 -m pytest -q tests/test_physical_ai_store.py tests/test_asimov_store.py tests/test_asimov_daemon.py tests/test_asimov_journal.py tests/test_query_contract_drift.py tests/test_query_contract_goldens.py tests/test_physical_ai_routes.py`: **97 passed, 1 skipped**, 11.24 s. System Python was used because the demo venv lacks requests; no environment packages were changed.
- Copied actual official native run `f47181c983164e779a1382d516fcebc0` and its producer status into an isolated temporary directory and real scratch DuckDB. External notification sender was replaced by an in-process capture, so no message was sent. Bounded ingestion returned 128,128,110,0,0; all **366** events survived, including 351 observations, 3 requests, 3 decisions, 6 controller receipts, 1 incident and start/end.
- Final projected source jumper_native/environment simulation/status ended; recorder active=false, incomplete=false, flushed=true, written 366, errors 0, dropped 0, invalid 0. Old Asimov runs/events both empty for this Jumper run. Generic compact snapshot was **8,562 bytes**, retained all 15 non-observation events with truncated=false. One sanitized Simulation task-denied incident dispatched, with no private source payload. Request decision and controller receipts remain separate; hardware_verified=false and outcome unknown remain intact.
- Bounds and privacy inspection: ingestion remains byte/line/segment bounded, queries clamp limits and use parameterized SQL, generic snapshot reuses the existing 60/62 KiB shedding strategy and 8 run / 24 event limits, raw observation events do not displace trace evidence, E2E trust/traces scope declared, daemon RPC requires private token, pending queries require an encryption key, and no handler opens journals or a second writer.
- UI/browser and production daemon/live relay qualification are assigned to root/other independent reviewers; no live/published or hardware certification claim is made here. Full project lint/build/release remain the parent execution gates, not waived by this focused review.

### Verdict

**CHANGES_REQUESTED** for R1 only. No other blocking finding in the reviewed bucket. Re-review the complete bucket after correction, retaining the original round.

## Round 1: Independent observer, governance, CLI and free view review

Verdict: **APPROVED for the reviewed source scope**. No remaining blocking findings. This review excludes the reviewer's own store, query, snapshot and alert-dispatch implementation, which requires another reviewer. It does not certify release, installed-wheel discovery, real publisher-to-DuckDB-to-view acceptance, or cloud deployment.

Reviewed against requirements.md and blueprint.md: parent-owned `clawmetry/physical_ai` observer, governance, measurements, monitor and CLI; root CLI dispatch and incident deep links; `docs/JUMPER.md`; free Physical AI routes, dashboard registration, navigation and browser view. The observer has no simulator, robot SDK, Pro or new heavy dependency. Named telemetry is bounded and persisted through the shared journal. Full-body geometry is recomputed for workspace decisions; unsupported and stale state withhold permission. Hardware and recordings cannot forward commands, and a decision or notification never asserts a measured physical stop. Routes read the daemon-owned store and expose no actuator endpoint. The browser renders untrusted strings as text, distinguishes source and receipt clocks, cancels hidden polling, and preserves optional advanced workbench links.

Findings resolved and independently rechecked:

- Target coordinates now reject booleans, text and nonfinite values; task scope copies mutable input collections.
- Canonical base positions reach lift monitoring, and explicitly simulated recordings cannot be relabelled hardware.
- Bounded but deeply nested telemetry JSON and malformed status records no longer crash the CLI.
- Incident `?run=` deep links select the requested stored run. A missing requested run gives an explicit window explanation without showing another run's detail.

Validation: 74 Python observer, Physical AI route and legacy Asimov route tests passed; `node tests/test_physical_ai_ui.js` passed including the two-run deep-link regression; English check passed with 4,721 extracted messages and zero mechanical findings; `git diff --check` passed. Tests use local fixtures and mocked notification transport, not a phone delivery claim. Actual native publisher and clean wheel acceptance remain separate delivery gates.


## Independent store/query/snapshot/alerts review, round 2

Reviewer: runtime_gate_diagnosis. Re-reviewed the complete round 1 bucket plus the new stdlib-only physical_ai/query_args.py and malformed-argument regression tests after cloud_guard_review's correction. No implementation edits by this reviewer.

- **R1 resolved.** Both routes.local_query._dispatch and daemon-only sync._local_dispatch_fallback invoke the same strict validator before proxy/store access. Half run cursors, nondecimal values, booleans, floats, invalid run IDs, oversized filters and out-of-range values reject; exact 63-bit cursors remain intact. The new 18-case test asserts neither proxy nor store opens for invalid input. Legacy shapes retain their prior contracts.
- Rechecked requirements/blueprint, source-specific Asimov separation, bounded SQL/snapshot projection, post-commit sanitized alerts, persisted shared delivery cooldown and authenticated/E2E query paths. No additional blocking findings. These changes do not add a database, handler journal read, controller transport, private adapter import or simulator dependency.
- Re-ran the full focused round 1 command: **116 passed, 1 skipped**, 12.23 s. `git diff --check` passed. Previous actual native 366-event projection evidence remains applicable; root owns actual daemon/query/browser and release qualification.
- Separately, the demo host now publishes the real model-addressed joint state, correcting an upstream-host omission rather than a projection defect. Fresh untouched official 35 s run `535dbf83af5849969f3e3d34d266d72d` has 351 observations with 22 named angular joint positions/velocities, 366 events flushed with no errors/drops, 7,000 finite steps and zero resets. Torques are not inferred. Its production daemon/view verification is being performed by root.

**Verdict: APPROVED for the reviewed store/query/snapshot/alerts source scope.** No remaining blocking findings. This does not waive installed-wheel, CI, release or cloud live-verification gates and makes no hardware or phone-delivery claim.


## Independent source-support upgrade review, round 3

Reviewer: runtime_gate_diagnosis. Scope: frozen pre-merge correction in clawmetry/asimov/store.py, tests/test_physical_ai_store.py and corresponding requirements, blueprint and implementation-plan updates. No implementation edits by this reviewer.

- **Requirements and blueprint:** AC-JUMPER-001.4 is satisfied. The additive source-support ledger leaves existing five-column cursors intact. Its canonical sorted source-registry token is stable across process restarts; a missing or changed token resets the affected file cursor once, then persists normal bounded progress. Existing per-pass line/byte/segment budgets and round-robin file selection remain in force.
- **Architecture, data safety and performance:** evidence, cursor and support marker commit atomically through the existing daemon-owned transaction and lock. Ignored-source classification is tied to the cursor identity and registry; inode replacement or observed truncation reclassifies it. Unchanged unsupported files, including appended bytes, avoid reopening/parsing their bodies. No new connection, request-handler file read, heavy dependency, network destination, actuator or source-privacy change is introduced.
- **Deduplication:** immutable run/sequence identities preserve existing observations and Asimov projections during registry replay. Only newly inserted incidents enter post-commit alert dispatch, after the writer lock is released. Existing shared delivery preferences and cooldown continue to apply; the change does not claim a durable delivery retry/outbox guarantee.
- **Tests:** independently ran the full prior store/query/snapshot/alerts focused command: **121 passed, 1 skipped in 10.51 s**. The new tests cover actual legacy database reopen with the ledger absent, restart midway through one-line replay, support-registry expansion, known Asimov/Jumper deduplication and notification counts, unsupported no-open scans after append, failed-transaction retry, inode replacement and truncation. `git diff --check` passed.
- **Additional independent failure probe:** in an isolated scratch DuckDB with external delivery mocked, injected failure after an incident had been read and inserted but before batch commit. Rollback retained zero events and zero ledger entries and sent zero alerts; retry committed all four records and dispatched exactly once; a fresh collector sent no duplicate. No real message was sent.
- **User-facing and delivery boundaries:** this is a persistent migration/ingestion correction; existing actual native publisher-to-daemon/view qualification remains applicable. Root owns required full CI, installed-wheel/release, cloud deployment and served-artifact verification. This approval does not waive those gates or certify hardware/phone delivery.

**Verdict: APPROVED for the source-support upgrade correction.** No blocking findings or outstanding advisory findings in the reviewed scope.
