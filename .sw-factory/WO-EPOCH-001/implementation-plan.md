# Preserve epoch timestamp ingestion and day rollups

## Summary
Fix shared calendar-day parsing so finite epoch timestamps cannot poison a DuckDB ingest transaction. A genuine compatibility check against OSS649a and releasedPro65 loses all queued events when a numeric timestamp is mistaken for a compact ISOdate and its raw prefix is cast to DATE. Restore correct node-local day buckets for epochseconds/milliseconds and preserve existing ISOoffset, naive-local and invalid-input behavior.

## Code reuse and package structure
Reuse `clawmetry/cost_windows.py`, already shared by the rollupwriter and SQLcostaggregate. Reuse its timezone semantics and existing `tests/test_day_bucket_local.py` storefixture. The numeric seconds/milliseconds convention follows `clawmetry/self_diagnostics.py` without importing that broader module. No adapter, request, schema, credential, entitlement or physicalcontroller changes; no dependency or version edits.

## Components and flow
Sourceevent timestamp -> existing LocalStore ingest -> shared Python daybucket -> persistent DATE-keyed rollups. SQLliveaggregate uses the paired shared SQLexpression and must produce the same node-local day. Numeric finitevalues represent Unixseconds, or milliseconds when magnitude exceeds1e11; invalid/nonfinite/out-of-range values have no Pythonbucket and retain the existing SQLjunkfallback. ISO and explicitoffsets remain node-local; dateprefixfallback requires canonical YYYY-MM-DD text, never an epoch-like string.

## Steps
1. Record baseline and add finite numericseconds/milliseconds, ISO and invalid-input regressions, including durable actualingest/reopen/live-v-rollup parity.
2. Implement bounded shared Python/SQLcoercion; retain existing fallback contracts and DST.
3. Run new tests against oldsource to demonstrate meaningful failure; run fixed sharedcost/rollup and exact affectedfree-runtime suites under the existing cleanPython3.11 Pro66 compatibility environment.
4. Obtain independent root/English review before featurePR. Follow normal greenCI/squash and separateRELEASE workflow, verifying downloaded wheel before downstreampin. No production changes here.

## Testing
- Existing and new `tests/test_day_bucket_local.py`, costwindow tests and localrollup suites.
- ExactCIselected `tests/test_nemoclaw_runtime_adapter.py`, `tests/test_openclaw_list_events.py`, `tests/test_openclaw_replay_events.py`.
- Verify mixedtimestamp batch actually commits events, model/runtime rollups match SQLliveaggregates, and reopened SQLite-free DuckDB retains results.
- Python/SQL parity under UTC and America/Los_Angeles, finite float/int/numericstring sec/ms, signed/scientificnotation, epochzero, ISOZ/offset/naive, invalid/nonfinite/out-of-range input.
- No browser, model, gateway, credentials or robotcalls; release/liveverification remains coordinated with root.

## Product record scope
No-PRD: This corrects a shared timestamp parsing regression against the existing local-calendar day contract. It introduces no product surface, policy or storage ownership. Risk is changed derived bucketing for previously unparseable numeric timestamps; tests compare both readers and persistent rollups. No historical rewrite or invented fallback to today.

## Reviewed scope adjustment
Root approved the related query fix before implementation: the same numeric events that could not commit also crashed four shared cost/session deduplication readers because they used a strict timestamp cast. Factor one safe SQL timestamp parser and reuse it at exactly those four expressions. Keep joins and matching structure unchanged. Valid instants retain second-based grouping; invalid clocks use an opaque event-ID grouping key, not an invented timestamp, so unrelated unknown-clock costs cannot disappear or be merged as duplicates. Literal infinity and years outside Python datetime's range are unavailable instants. Date-only basic ISO `20260824` retains precedence over numeric-string parsing; Unix zero is valid, booleans are not timestamps. Numeric milliseconds use absolute magnitude above1e11. Hours remain outside this correction.

The expanded actual-store test requires the real query_aggregates reader to retain both costs for malformed same-session assistant/model.completed events, while their day remains the historical SQL unknown bucket and DATE-keyed rollups skip them. Reopening must read the persisted result after clearing the aggregate cache. A separate regression checks actual matching ISO/epoch sibling envelopes still deduplicate. No schema migration, backfill, raw timestamp mutation, new clock source or physical activity is involved.

## CI and dependency verification
Register the new test in the existing DuckDB-backed Python3.11 MOAT job. Keep all dependency locks and setup.py unchanged. Constrain the internal SQL identifier builder to its two existing call pairs and annotate only the fixed CTE's reviewed interpolation. Preserve source values as SQL parameters, never interpolated text. Synchronize SQL/Python clocks explicitly only in timezone-mutating test helpers; fresh-process production clocks were independently verified. Basic ISO dates use a constructor supported on Python3.9.

The pre-existing DuckDB0.10 package-floor incompatibility is not repaired by an unconditional floor increase:1.5.6 itself drops older Python versions. No dependency support-policy change is part of this correction. Verification covers the actual CI lock and current deployed dependency family rather than asserting all historical versions work.
