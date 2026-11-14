# Verification evidence

## Local implementation

- 66 focused collector, store, route, sealed relay, frontend, navigation and existing Guard checks passed after the final cancellation correction.
- Workflow/module verification: 725 passed, 462 skipped. The skipped workflow cases are existing condition-dependent command checks, not node feature failures.
- Acceptance manifest: 24 new Factory criteria mirrored, all referenced by meaningful feature tests. Overall gate: 374/442 covered; remaining 68 are existing uncovered criteria.
- English mechanical subset, daemon method allowlist, Python compilation, app.js syntax, generated module map and diff whitespace checks passed.
- Built a local wheel and inspected it: all collector/store/service/route/template/JS/CSS assets and the psutil dependency are present. This is a pre-release package check, not published-wheel proof.

## Real local data path

An isolated writer daemon and dashboard ran against a scratch DuckDB. The collector read actual psutil measurements and a selected file under an owned temporary verification directory. A harmless real change to that file produced a sensitive settings event. Its public response omitted contents and fingerprints.

The full dashboard rendered the Node activity navigation item and live feature assets. A browser review of that event saved through the actual authenticated daemon RPC and returned an expected review from persisted evidence. A same-value monitoring preference save also returned “Saved on this node” through the actual daemon path. The interface showed the actual source gaps on this account: capped processes and inaccessible listener enumeration. It did not report missing measurements as zero.

Browser checks at 320 and 360 pixels found no page-level horizontal overflow in Observe, Govern or Guard. Source scope was visible separately from its reason. The browser console had no warnings or errors during the feature walk. Server request counts stayed at 17 after leaving the tab, with no new Node activity requests across multiple normal poll windows. The local component regression additionally exercises reduced motion, exact older-event selection, retained findings and corresponding resource samples.

## Remaining release evidence

Feature PR, release PR, published wheel, cloud pin/deploy, released daemon snapshot and hosted browser checks will be added after those steps complete. Local tests do not substitute for release verification.

Relay unit tests explicitly isolate the audit database as well as their store. CI caught two abbreviated module references in the architecture guide; both now use their actual package paths. The module-reference regression was run again after that correction.
