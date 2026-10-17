# Independent review: Physical AI UI restoration

## Round 1

Reviewer: runtime_gate_diagnosis. Scope: frozen core correction in routes/extensions.py, routes/physical_ai.py, new physical_ai/catalog.py, sync_system_snapshot metadata seam, shared template/CSS/JS, associated guards and updated JUMPER-OSS requirement/blueprint; includes the subsequently added encrypted-snapshot integration assertion. No implementation edits by this reviewer.

### Requirements, architecture and safety

**AC-JUMPER-001.5 / ADR-004 satisfied.** A valid installed workbench declaration remains the primary destination; plain local /physical-ai redirects to it, while explicit run/hardware history links retain the free built-in page. Missing/failed/older metadata retains the free fallback. The template applies the existing dark dashboard palette before paint and supplies an actual recorded-hardware selector from the shared pure catalog. The catalog declares supported recorded sources, not discovery or hardware compatibility.

The metadata helper builds one known Physical AI entry, accepts only bounded same-origin path syntax for installed workbenches, removes duplicate destinations and discards arbitrary plugin fields from the snapshot. It calls the explicit ui.snapshot seam, rather than inferring entitlement from package names or inventing Flask endpoints in the daemon. The metadata travels inside the existing encrypted system snapshot; the new happy-path integration test decrypts the actual captured POST and verifies it is absent from the outer payload. No new database, telemetry read in a request handler, heavy dependency, poller, controller transport, private implementation or plaintext egress path is added.

The Hardware selector filters loaded run identities by their recorded robot_type. Filter changes invalidate in-flight work, clear previous events/cursors and requested-run state, and never silently choose another family. Requested-run selection is constrained by the selected Hardware family. Empty matches explain the history window, with existing older-run pagination retained. Existing event pagination, bounded memory, hidden-page cancellation/deadlines, snapshot account/key reset and source/receipt distinctions remain intact. Unknown hardware input is rejected without reflection. Navigation does not change destination entitlement enforcement.

### Independent verification

- `python3 -m pytest tests/test_physical_ai_routes.py tests/test_extensions_introspection.py tests/test_physical_ai_store.py tests/test_jumper_observer.py tests/test_system_snapshot_dlq.py -q`: **122 passed in 6.34 s**.
- `node tests/test_physical_ai_ui.js`: passed evidence, actual hardware selection, wrong-family deep-link isolation, event clearing and retained lifecycle/polling guards.
- `git diff --check`: passed.
- Independently copied the parent's actual-native qualification script to a fresh scratch path and changed only its output directory and isolated server port. Ran `/private/tmp/physical-ai-independent-06xr55ui/qualify.py`. The original journal remained read-only; user port8900/database/processes were untouched. Fresh writer/proxy pipeline reproduced the legacy pre-support EOF cursor and ingested the real official native run535dbf83af5849969f3e3d34d266d72d: **366 events**, including351observations,3requests,3decisions,6controllerreceipts and1incident. All22named joints survived; permissions remained allowed,allowed,denied.
- Actual Chromium view used the separate daemon-owned DuckDB and dashboard `_ProxyStore`, read both event pages, computed dark background rgb(10,10,11), selected Jumper, switched to empty Asimov with no wrong detail, then returned to Jumper. Zero JavaScript errors and390px no-overflow. Independently inspected desktop/mobile screenshots under that scratch directory. Snapshot size11476bytes. Phone delivery preferences were disabled for qualification; no hardware or real notification-delivery claim is made.

### Integration follow-up and verdict

No blocking or advisory findings in the core source scope. The coordinated cloud renderer must pass the new hardware_choices/selected_hardware template context and consume the owning node's decrypted navigation; this was explicitly handed to the cloud author before repin/deployment. Installed server packages alone remain insufficient evidence of node entitlement. The Pro author separately qualifies actual Jumper support in the retained entitled workbench.

**Verdict: APPROVED for the reviewed core UI correction.** This is source-candidate approval, not release or live completion. Normal current-head CI/native review, separate public release and wheel verification, coordinated Pro/cloud artifacts, and hosted real-node/served-asset checks remain required. No merge, release, deploy or user installation was performed by this reviewer.


## Round 2: independent review of CI-discovered Assistant race repair

Reviewer: root. Author: runtime_gate_diagnosis. Reviewed the frozen four-line Executor.read correction and deterministic receipt-barrier regression against StreamJob cancellation/deadline handling, Job.renew, the consumer persistence/terminal barrier and the HTTP error adapter. The existing deadline test is unchanged. The new test exercises the actual typed RPC and durable receipt, holds completion before terminal publication, and checks the original deadline and lease, absence of a fabricated terminal result, canceled timeout state, unsaved conversation and equality of the final 504 journal and persisted failure.

The correction preserves producer-owned admission and consumer-owned terminal persistence. Catching TimeoutError only around renewal prevents transport misclassification without retrying inference, extending an expired lease or replacing an authoritative result. Existing Cancelled handling and success commit checks remain intact. Existing Assistant requirements/blueprint already require explicit durable failure and daemon ownership, so the repair satisfies the existing contract.

Independent root verification: original deadline regression, new barrier regression and full executor suite: **17 passed in 6.72 seconds**. Inspected the author's controlled pre-fix reproduction and 126-pass lifecycle report. git diff --check passed. No findings. **APPROVED** for the bounded repair; normal fresh-head CI, release and hosted qualification remain required.
