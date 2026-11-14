# WO-EPOCH-001 review log

## Independent source review
Verdict: APPROVED.

Root approved the bounded shared Python/SQL timestamp parser, unchanged raw timestamps and joins, event-unique unknown-clock grouping keys, and the fifth alias-qualified subagent query expression. Root independently ran89 epoch/day/subagent regressions without skips.

Independent reviewer approved final five-site source. Covered finite/range guards, preserved basic dates, strict date-prefix fallback, local/DST parity, seconds/milliseconds, unknown-clock costs, source data preservation, no schema/auth/dependency changes. Reviewer independently ran162 day/free-runtime tests on the initial four-site candidate and87 final epoch/subagent/cost/rollup tests, without skips. No blocking findings remain.

Source review approval does not assert release, deployment or live acceptance. Those gates remain pending.

## Final verification
Full selected date/cost/local-store/session/subagent/free-runtime suites passed with zero skips. Actual persistent regression fails unchanged649a at DATE conversion and passes final source. Generated JUnit is retained privately, not committed. Root source approval and peer review remain approved. A reviewer measured roughly60ms per100k distinct ISO timestamps for the guarded dedup expression, compared with roughly7ms for the old strict expression; existing aggregate caching and request behavior are unchanged. No optimization or new polling was added.

## CI feedback and reviewed corrections
The first feature head failed because the new test was not listed in an actual CI command and Bandit flagged the newly interpolated fixed CTE. No gate or baseline was weakened. The regressions now run in the existing Python3.11 MOAT job after its hash-pinned DuckDB dependencies install. The private identifier builder rejects every pair except `ts/id` and `e.ts/e.id`; tests reject injection-shaped identifiers. One narrow B608 annotation is an actual Python comment outside the fixed SQL literal. Full-tree Bandit1.9.4 reports309 medium findings and zero high, matching the existing baseline. Fourteen actual CTE-consumer regressions pass.

Fresh-process DuckDB1.5.6 tests in UTC and America/Los_Angeles confirmed correct actual LocalStore, bare connection, Python bucket, rollup and query behavior without a production timezone setter. Older ICU caches do not necessarily follow tests that mutate TZ after import; only test connections now explicitly match the test's Python clock. There is no production timezone or date-format change. The basic ISO constructor uses date(year,month,day), including on Python3.9.

DuckDB1.5.6 selected tests passed158/158, with no skips. The SDK's historical declared minimum0.10 already fails unchanged-main schema initialization; unconditional alignment to1.5.6 would also break advertised old-Python support. That dependency-policy debt is separate and unchanged. This release does not claim compatibility with every historical dependency version. The actual CI lock's1.5.5 engine is independently checked before push.

Final CI-correction verdict: APPROVED by root and independent reviewer. The reviewer ran118 tests on the actual CI DuckDB1.5.5 engine and93 epoch/day tests on1.5.6, both with zero skips. Source and test changes are frozen. The normal feature CI rerun remains mandatory before merge.
