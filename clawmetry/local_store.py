"""Local DuckDB event store — Phase 1 of the local-first refactor (#964).

Switched from SQLite to DuckDB (decision: 2026-05-11). Same public API; the
durability + concurrency model differs (DuckDB MVCC instead of SQLite WAL),
but the surface — ``ingest()``, ``query_events()``, ``query_sessions()``,
``query_aggregates()``, ``health()``, ``vacuum()`` — is unchanged.