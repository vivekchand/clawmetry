# WO-EPOCH-001: Preserve epoch timestamp ingestion and day rollups

Status: implementation and independent source review complete; 281 selected tests passed without skips; feature PR pending.

Requirement: existing DuckDB-first event persistence must accept supported numeric source timestamps without rolling back a batch. Calendar buckets must match node-local date semantics in Python and SQL. Invalid clocks must remain unknown without losing raw events or costs.

Architecture: existing `clawmetry/cost_windows.py` owns shared calendar parsing. `clawmetry/local_store.py` calls it for rollup writes and five event-cost deduplication readers. No new components, storage owner, dependency, schema, source-data rewrite or control path.

Product record: No-PRD bug-fix exception under FLYWHEEL section0c, correcting an existing documented timestamp contract.

Evidence:
- Released plugin baseline against exact SDK source649a:26 failed and48 passed in the three affected runtime suites, with failed DATE conversion rolling back ingest.
- New persistent-ingest regression against unchanged649a fails at the same DATE conversion; no synthetic live acceptance claim.
- Root and independent reviewer approved the bounded Python/SQL parsing and five query expressions.

Branch: fix/epoch-rollup-day-20261107
PR: https://github.com/vivekchand/clawmetry/pull/6584; final CI correction pending.
Release: pending normal separate RELEASE workflow; no manual version or tag changes.
