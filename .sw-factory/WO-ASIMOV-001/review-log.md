# WO-ASIMOV-001 review log

## Planning record
The local requirements, self-contained feature blueprint and substantive implementation plan were created before implementation on 2026-10-15. Scope covers free local observation with no Pro dependency, bounded compatible journals, official SDK import, explicit instrumentation, Observe-only live collection and encrypted asimov snapshot parity. Hosted publication attempt is documented in factory-status.md; no unrelated records were changed.

Independent implementation review is pending and no APPROVED verdict is claimed. Hardware qualification is outstanding and cannot be satisfied by fixtures.

## Independent implementation review

Reviewer: `asimov_local_view`, acting independently of the SDK, journal, recording, observer, store, daemon and authentication implementations reviewed here.

**Verdict: APPROVED** for the experimental SDK and recording integration code scope.
This verdict permits PR review. It does not establish physical hardware qualification or completion of the release chain.

### Scope and evidence

The review covered `clawmetry/asimov/journal.py`, `sdk.py`, `recording.py`, `observer.py`, `store.py` and `daemon.py`.
It also covered the CLI entry point, daemon startup and shutdown, public store methods, internal RPC authentication, trial exceptions and encrypted snapshot integration.
The reviewer inspected the official Menlo SDK 0.1.0 open, keepalive, close, LiveKit join and recording paths directly.
No collector motion call, media subscription, credential upgrade or replacement of unrelated Pro handlers was found.

The following software checks passed against the actual official SDK source.
They used `PYTHONPATH=/tmp/clawmetry-menlo-sdk-v010/src:.`.
The Pro contract used the separately installed package through `CLAWMETRY_ASIMOV_PRO_SOURCE`.
Private source was not copied into this public repository.

- All six Asimov Python test files: 74 passed.
- The public recorder journal passed the actual Pro parser and store contract test.
- The real SDK offline transport test confirmed zero command sends from the passive observer and one owned connection close.
- Queue bounds, disk limits, explicit losses, immutable replay, transaction rollback and DuckDB reopen tests passed.
- The selected snapshot retained the latest 24 non-observation events in sequence order.
- Large metadata and command details stayed below the 64 KiB snapshot cap with a valid retained-run cursor.
- Unchanged recorder sidecars caused no repeated status-file read or health UPDATE.
- Public route tests confirmed the read-only query boundary. Internal shared-blueprint RPC tests rejected unauthenticated reads.
- A real DuckDB snapshot passed AES-GCM encryption and decryption, then rendered through the actual browser JavaScript with no local API reads.
  This is an encrypted renderer software contract test. It does not exercise a served hosted page.
- Node UI checks passed, including unknown values, source clocks, frozen snapshot freshness, bounded trace labels, same-origin local authorization and canceled provider deadlines.
- Ruff passed for the modified route and review test files. The English mechanical check reported no findings.
- The acceptance ratchet passed at 407 of 475 repository criteria covered. All Asimov declarations are tied to concrete software tests.

### Findings and resolution

The review found a reproducible snapshot selection defect.
The SQL excluded `observation` but retained `observation.raw`.
After 32 raw feedback samples, the snapshot displaced the earlier command and contained only raw telemetry.
The new regression test failed before the fix.
The query now excludes both observation kinds. The regression and recent-window tests pass.

The review also added a bounded deeply nested corrupt-row test and defensive `RecursionError` handling in journal ingestion and health parsing.
The installed Python 3.12 and 3.14 parsers accepted the test nesting, so parser recursion was not classified as a reproduced blocker.
Malformed rows still advance the cursor, preserve later valid evidence and mark the run incomplete.

Follow-up review identified two standalone renderer issues.
Local network API reads did not carry the dashboard's saved gateway token.
They now use the same-origin Authorization header and never put a token in a URL or send it through a cloud provider.
A hung shared snapshot promise could also hold the renderer's loading state forever.
Provider reads now observe the renderer deadline and cancellation signal. The focused checks prove that loading clears and polling can retry.

### Remaining delivery gates

No physical Asimov was connected during this review.
There is no evidence here for real actuator readings, firmware compatibility, real Observe credentials, radio failures or physical command correlation.
Hardware qualification remains pending and must be stated in the UI, documentation and release claims.

The reviewer could not obtain a browser screenshot in this session because local socket binding was denied and direct browser access failed.
The root agent owns served desktop and mobile verification, authenticated hosted rendering, native CI review, merge, PyPI publication and cloud deployment verification.
A passing unit test or this review verdict does not satisfy those delivery gates.

## Native review follow-up and independent boundary review

Native Drift reported six findings on fb4384c955865fe13e9c21b80508a6201d0d3d2c. A separate same-head no-drift comment did not supersede its failure status. The red check remains a merge blocker; no waiver or replacement status was submitted.

1. `require_sdk` already executed its Python floor and optional imports only when explicitly called. Clarified that boundary and added a Python 3.8 import/recording regression that forbids Menlo, LiveKit and NumPy imports, then verifies the explicit live call reports the Python requirement.
2. Daemon startup tails existing local journals only. It does not install application tracing, request credentials or connect to a robot. A real-thread test forbids SDK, observer and Pro imports and network connection attempts during a real empty-directory ingest pass. Repeat startup retains the same worker.
3. Tightened command wrapping from `BaseException` to `Exception`. Actual SDK tests show `KeyboardInterrupt` and `SystemExit` escape unchanged without a failure event; ordinary application failures are recorded and re-raised with the same identity. The two process-control regressions failed before the fix.
4. A terminated real Thread reports not alive and is replaced by start. A transient ingest OSError is logged and retried by the same live worker. Both behaviors now have real-thread tests.
5. `get_store(read_only=True)` expresses read intent through the existing architecture. The dashboard uses `_ProxyStore`, authenticated allowlisted daemon RPC and the existing writer-owned DuckDB. The test exercises the actual Flask RPC and forbids opening another database connection.
6. `AsimovLocalStore.snapshot` intentionally projects persisted DuckDB evidence directly. The view consumes that projection; it does not mediate serialization or shared-envelope encryption. A test forbids journal ingestion or journal directory access during snapshot generation.

Reviewer `asimov_local_view` independently reviewed the complete follow-up and found no blocking code findings. All 83 Asimov Python tests passed against official SDK source and the separately installed published Pro parser. Node renderer checks, Ruff, Python floor, module map, AC traceability, English and CI test-file coverage checks passed. The five daemon tests are wired into both explicit Asimov CI steps.

## Served browser run and harness correction

CI run 38803620708 passed the real SDK/free-evidence job. Its served browser job produced genuine desktop and mobile screenshots and recorded no browser errors or failed responses, then failed the native hidden-tab assertion. Playwright 1.62.0 enables Chromium focus emulation on each page, keeping background pages visible. The harness now disables that automation override through the actual CDP sessions on both tabs before real tab switching. It does not modify document.hidden or dispatch synthetic visibility events. The hidden request-count and resume assertions remain intact, and actual native states are retained on failure. The next CI run must prove this fix; no passing served-browser verdict is claimed yet.

## Native status and original-session capture investigation

Native drift-bot on 2932438776ea09a6481382eeec895287000f04e6 passed: "Drift Bot found no drift (took 47s)". The candidate wheel was rebuilt, with 21 packaged artifacts byte-matched to that commit's tree. Isolated wheel-only Python without site packages passed status, official recording import, 25-joint inspection and replay. This was an unpublished candidate, not a PyPI release.

CI 38804914130 again passed the SDK/free-evidence job and actual desktop/mobile captures, but failed native visibility. Its diagnostic showed both pages visible, one focused and one unfocused. Chromium's EmulationHandler owns a capture handle per CDP session, so disabling focus emulation on a secondary session cannot release the handle held by Playwright's original session. The earlier source-only fix was therefore insufficient; no served-browser pass was claimed.

The native phase now launches the installed Chromium in a new scratch profile on loopback with an ephemeral CDP port and connects using the documented Playwright `no_defaults=True` option. It uses only that default context, so Playwright never installs the original focus/capture override. Two distinct target IDs must report the same actual Browser.getWindowForTarget window ID before native tab activation and visibility assertions. Timer throttling remains disabled: zero requests while hidden must come from application behavior. No document.hidden replacement, synthetic visibility event or lifecycle emulation is used. Process startup, browser disconnect and owned child cleanup are bounded, with real browser logs and visibility/window diagnostics retained. Compilation, Ruff and diff checks pass. Actual native execution remains a required new CI result.

## Actual served-browser result and final independent exploratory review

CI run 38806018012 passed both Asimov jobs on 9d2692b6ca83372d20496ce9c15e442acd993b6a. Native drift-bot passed on that exact head in 39 seconds. Root downloaded the actual browser artifact and inspected desktop/mobile screenshots, report.json and native-visibility-diagnostic.json. The real authenticated application used an empty scratch DuckDB, inserted no telemetry and reported zero browser errors and failed responses. Two distinct target IDs reported actual window ID 1588253730; the native background state was hidden, requests while hidden were zero over 6.5 seconds, foreground state was visible and polling resumed. The published SDK/free-install contract also passed.

Independent reviewer `asimov_local_view` inspected those actual artifacts and the final harness. **Verdict: APPROVED** for the experimental software and actual served empty-view scope. Desktop at 1440 pixels and mobile at 390 pixels were readable without page overflow, had actionable commands, and clearly labeled observation-only operation and pending hardware qualification. No blocking findings were found. This verdict does not establish populated hardware telemetry, live Observe credentials, hosted account unlock, PyPI publication or cloud rollout.

Main subsequently advanced through release PR #6443, changing only FLYWHEEL.md. The main-first queue canceled remaining broader CI. The feature was rebased cleanly onto that fresh main; implementation artifacts remain byte-identical to the reviewed commit. Full CI on the current head, merge, release, published-wheel inspection and cloud deployment remain delivery gates. No canceled check is treated as passing.

## OSS merge and release handoff

All checks on fe0290a4bb396ec74bfa2354d6f65d0f1426cd25 completed successfully, including native drift-bot, both Asimov jobs, product record, visual diff, cross-platform API/install/sync, real gateway, store invariants, entitlement suite and the required aggregate gate. The scheduled-only OpenSSF Scorecard check was skipped by its existing workflow condition. No failure, cancellation or pending check was treated as passing.

The rebased Asimov workflow 38806903046 passed. Root downloaded its exact-head browser artifact: screenshots are byte-identical to the independently inspected captures, and native same-window, hidden zero-request and resume assertions all passed again. The entitlement suite passed after about 14 minutes, consistent with the separately observed green-main baseline; no bypass or test change was needed.

PR #6442 merged at 2026-10-15T21:26:23Z as b763676bd858b37af005335525abc0a6e08ef5fc. This is the OSS source merge, not completion of PyPI publication, cloud deployment or physical qualification. A separate release PR carries the changelog and this handoff; the workflow owns versioning and publication.

Release PR #6447 initially parked queued checks behind main under the existing queue policy. Main then advanced through #6440, adding public runtime compatibility dispatch and a blob-filtered product-record checkout. The release was rebased cleanly onto that merged CI baseline. The packaged Asimov implementation remains byte-identical to the inspected candidate and reviewed feature; canceled checks remain pending delivery work until restored and passed on the current head.
