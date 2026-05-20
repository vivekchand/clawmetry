"""Local DuckDB event store — Phase 1 of the local-first refactor (#964).

Switched from SQLite to DuckDB (decision: 2026-05-11). Same public API; the
durability + concurrency model differs (DuckDB MVCC instead of SQLite WAL),
but the surface — ``ingest()``, ``query_events()``, ``query_sessions()``,
``query_aggregates()``, ``health()``, ``vacuum()`` — is unchanged.

Why DuckDB:
* Columnar storage → analytical queries (GROUP BY, time-window aggregates,
  per-tool/per-session/per-day rollups) run an order of magnitude faster than
  on SQLite. The dashboard's Brain/Tokens/Sessions tabs are exactly that
  shape of workload.
* Native Parquet and CSV I/O — future cheap archival + ad-hoc export are a
  one-liner, not a library swap.
* Time-series-friendly query patterns become first-class.
* Trade-off: a real wheel dependency (~14 MB) instead of stdlib sqlite3.
  Considered acceptable: the analytical advantages compound as the local
  store accrues months of data.

NOT in this module (deliberately):
* Network — there is no HTTP server here. Adding endpoints is a follow-up
  blueprint.
* Encryption — events are stored plaintext locally. Cloud sync continues
  to do its own E2E encryption pass before POSTing.
* Cloud sync — independent. Adding the local store does not change what
  ``sync.py`` ships.

Concurrency model:
* DuckDB connections are heavyweight; we keep a process-wide singleton
  connection guarded by a ``threading.Lock`` for writes. Reads are issued
  via ``.cursor()`` instances which are thread-safe.
* DuckDB allows only one *writer* process per file; multiple *readers* are
  allowed. The daemon process owns the writer; future external readers
  (e.g. a separate dashboard process per #960) will open with
  ``read_only=True``.
"""
