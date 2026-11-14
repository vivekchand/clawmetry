# Implementation Plan: WO-NODE-CLARITY-001

## Scope and authorization

The user's actual 0.12.923 screenshots show an unknown process total despite retained observations, all process CPU values unknown, an unclear category diagram, and no explanation for empty listener data. Fix measured data and explanations together. Preserve unknown actor identity, bounded polling, read-only default, old snapshots and E2E cloud parity. The task is the local work-order authorization; no Work Orders API is exposed. Root approved eleven new OBS-NODE-CLARITY acceptance criteria before implementation; record-owning delegate is persisting/readback-verifying the connected requirement and blueprint. Product edits wait for that verification.

## Reuse and flow

Reuse daemon collector -> daemon-owned DuckDB -> encrypted snapshot -> existing local/hosted vanilla-JS renderer. No host stats in HTTP handlers. Existing coverage.processes.count/listeners.count describe fresh positive observations; nullable summary totals remain exact totals. Do not count stale retained rows as current or add a duplicate count field.

Keep process_iter.cache_clear. Request cpu_times in the existing nonblocking one-shot scan and derive 100*delta(user+system)/monotonic elapsed for the same source/PID/start identity. Cache at most 512 retained processes per sensor/source. First sample, invalid/omitted counter, PID reuse, restart, disable, source change, regressed counters, elapsed below 0.1s or above120s return null with cpu_reason. Expose valid cpu_interval_seconds. 100% is one logical CPU; values above100% are valid. Private cumulative inputs stay outside public rows and DuckDB. Reference: https://psutil.readthedocs.io/stable/#psutil.Process.cpu_percent and Process.cpu_times.

Keep psutil as cross-platform listener source. Only after denied/unsupported Darwin collection, attempt /usr/sbin/lsof -nP -a -iTCP -sTCP:LISTEN -F0pftnT, no shell/elevation/DNS/service lookups. Bound output256KiB, runtime0.75s and remaining shared budget preserving file reserve, rows256. Parse complete safe numeric TCP LISTEN fields only. Always partial method=lsof_polling/account scope, source identity qualified by listener method; no false removals across method change. Actor unknown; process_id null absent independent verification; wildcard exposure unknown. Explicit unavailable on missing tool/permissions/budget. No active network/OT probes. Reference: upstream https://github.com/lsof-org/lsof/blob/master/Lsof.8.

## UI design and critique before implementation

Inherit app font and theme. Palette dark page#0a0a0b, panel#0f0f11, divider#232329, text#f2f2f3, secondary#c9c9ce, warning#fbbf24 with matching existing light-theme variables. Left-align prose and tables; retain tabular numerals, keyboard focus, mobile layout and reduced motion. Keep headings20/14px, explanation13px and metadata11px.

Use one selected-event story rather than a speculative actor/node graph. The reader should immediately understand: gh was seen running here; who started it is not identified. Put time, process/resource and machine alongside the explanation and observation limits. Original before/after/source details are a collapsed native disclosure. Keep measured resource history, historical review/draft/focus preservation and recorded-event replay. Critique: the old three actor categories look causal without evidence; remove them, not add more arrows. Repeated Unknown hides distinct conditions: show observed counts, measured CPU intervals or their specific reason, and source-specific empty-list explanations with a working View coverage button. Animation only follows recorded replay, never implies continuous capture or safety.

## Files, sequence and ownership

1. Factory delegate verifies additive criteria/blueprint and referenced graph before product edits; copy exact criteria into local records.
2. Backend delegate authors collector and focused collector tests only. Root authors live template/CSS/JS and frontend/browser regressions in separate files. All test execution uses scratch HOME/audit/store and suppresses production logging before sync imports.
3. Root mirrors exact criteria in docs/acceptance_criteria.json and ratchet, integrates, runs relevant checks and updates this execution record.
4. Independent cloud delegate reviews collector/security bucket; UI delegate reviews frontend/requirements bucket. Resolve every blocker and repeat full bucket review until APPROVED.
5. Root ships feature PR/fullCI/fresh-main merge, separate RELEASE PR, publisher, inspected official wheel, actual local install and service restarts. Cloud delegate promotes that verified wheel through a fresh pin/fullCI/all candidate gates/100% traffic. Root verifies actual local and hosted views.

## Verification

Meaningful regressions: observed vs exact/stale/empty counts; two-sample CPU identity/gaps/counter reset/restart/bounds; lsof parsing/timeout/output/row limits and no fallback on other OS; source transitions and partial data do not create negative events; plain escaped selected-event stories with progressive details and preserved review/replay; legacy snapshots render without invention. Preserve prior partial-observation/nonce guards. Run targeted Python lint/syntax/3.9 checks, focused collector/store/wiring suites and JS/browser suites. No new dependencies/build step/timers.

Final live proof: owned harmless process plus loopback TCP listener, actual measured process CPU interval, daemon -> DuckDB -> encrypted snapshot -> local and hosted UI, then close only owned process/listener. Confirm served assets and installed files match official wheel, zero new browser console errors and explicit source limits. Until those pass release acceptance is pending; no synthetic fixture can substitute.


## Author verification checkpoint

* New count/story/CPU/empty-state JavaScript contracts pass, including red-before observed-count and legacy stale-total reproductions.
* Focused collector/store/frontend checks: 63 passed before the final parser hardening; the collector author subsequently verified its malformed-header and endpoint regressions red before correction and all focused checks green.
* Normal shared Chromium component check: 1 passed after setting the installed browser-cache path under scratch HOME. Its first attempted run failed only because scratch HOME hid the existing Chromium executable; no product change was made for that harness issue.
* Existing daemon/API/cloud wiring checks: 27 passed in scratch HOME/audit/DuckDB.
* Author Chrome exploration of an actual collector plus in-memory DuckDB preview showed 512 positive process observations, 30 accessible listener observations and measured per-process CPU intervals. The plain selected story, historical-context form and coverage reasons rendered in the inherited light theme. Preview server and tab were closed afterward. This is component evidence, not installed or hosted delivery proof.
* Exact eleven Factory criteria mirrored without rewording. Coverage ratchet remains at 68 pre-existing uncovered criteria, with all eleven additions referenced by meaningful tests. Actual installed and encrypted hosted acceptance is a separate mandatory release gate.

Final combined pre-PR suite after all review fixes: **96 passed**. Independent collector and frontend buckets both APPROVED; official installed/hosted acceptance remains pending.

CI follow-up: the test-file coverage ratchet found that the new collector regression module was not explicitly named in a workflow. Added it to the existing Node observation/governance/lifecycle job, without changing assertions, gates or the unlisted baseline. The failing CI log supplies the red-before evidence. Product source is unchanged.

Rebased onto fresh main b763676bd8 after Asimov merged. Only the shared acceptance manifest/baseline conflicted; retained every main criterion and prefix unchanged, then appended the exact eleven approved CLARITY criteria. Coverage is418/486 with the same68uncovered. Independent manifest review APPROVED (Round6). Re-ran all96 focused checks including normal shared Chromium successfully. Packaged product bytes are unchanged by rebase.

Final exploratory requirement audit reproduced an AC-OBS-NODE-CLARITY-005.1 edge case: inventories containing only retained stale rows showed the collection reason but lacked a direct coverage link. Added permanent View coverage buttons to both inventory headings through the existing delegated handler. A real-payload browser regression failed before the template correction and verifies stale rows plus navigation afterward. No new handler, request, timer or attribution claim.
