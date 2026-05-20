"""MOAT: daemon SIGKILL crash-recovery (zero loss, zero dupes).

Issue #1541.  Invariant #2 from PRD #1540: every event queued to the
daemon must appear in DuckDB exactly once even if the process is
``SIGKILL``'d mid-burst and then restarted with a full source replay.

The guarantee rests on two orthogonal properties:

1. **WAL durability** — events whose ``_flush_now_locked`` transaction
   committed before ``SIGKILL`` survive in DuckDB (DuckDB is fully
   ACID and WAL-backed; on next open, any committed-but-not-checkpointed
   WAL entries are replayed automatically).

2. **At-least-once dedup** — events lost from the in-memory ring buffer
   at crash time are re-ingested on daemon restart via source replay
   (e.g. the JSONL transcript files).  ``INSERT OR IGNORE`` on
   ``events.id`` (the PRIMARY KEY) collapses every duplicate write to
   a no-op, so the final row count is always exactly N.

Why ``multiprocessing.get_context("spawn")`` instead of ``fork``:
  - ``fork`` inherits parent file descriptors, DuckDB connections, and
    logging handlers — a recipe for cross-test contamination and DuckDB
    lock conflicts.
  - ``spawn`` starts a clean Python interpreter; each worker imports its
    own module graph, exactly matching a real daemon restart.
  - ``spawn`` is the default on macOS (``fork`` is deprecated there
    since Python 3.12) and works identically on Linux.

Why drive ``LocalStore.ingest()`` directly instead of the full
``clawmetry sync`` daemon subprocess:
  - ``clawmetry.sync`` ultimately calls ``LocalStore.ingest()`` for
    every event — we exercise the same code path with a simpler harness.
  - Avoids needing a live OpenClaw workspace, JSONL polling cycle, or
    gateway connection.
  - Fully deterministic: no network, no filesystem watchers.

Run::

    pytest -v tests/test_moat_daemon_crash_recovery.py
"""

from __future__ import annotations

import json
import multiprocessing
import os
import signal
import time
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

_FLUSH_BATCH = 50   # small batch so commits happen progressively during burst
_FLUSH_SECS = 300   # long timer — rely on batch-size trigger only


# ---------------------------------------------------------------------------
# Subprocess worker (must be module-level for spawn pickling)
# ---------------------------------------------------------------------------

def _worker_ingest(db_path: str, events_json: str, project_root: str) -> None:
    """Subprocess entry: import LocalStore fresh, ingest all events, exit.

    Intentionally avoids ``store.stop(flush=True)`` so the caller can
    SIGKILL the worker while events are still in the ring buffer.
    If the caller lets the worker run to completion, it exits cleanly.

    ``project_root`` is passed explicitly because ``multiprocessing.spawn``
    does NOT inherit the parent's ``sys.path``.
    """
    import importlib
    import sys

    # Ensure the project root is on sys.path so we can import clawmetry.
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    import os as _os
    _os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = db_path
    _os.environ["CLAWMETRY_LOCAL_FLUSH_BATCH"] = str(_FLUSH_BATCH)
    _os.environ["CLAWMETRY_LOCAL_FLUSH_SECS"] = str(_FLUSH_SECS)

    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    for ev in json.loads(events_json):
        store.ingest(ev)
        # Small sleep ensures events arrive across multiple flush windows
        # so SIGKILL has a non-trivial chance of landing mid-flight.
        time.sleep(0.001)

    # Reached here only when caller did NOT SIGKILL — flush cleanly.
    store.stop(flush=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _project_root() -> str:
    return str(Path(__file__).parent.parent)


def _make_events(n: int, node_id: str) -> list[dict]:
    """Minimal valid ``LocalStore.ingest()`` events (id, node_id, event_type, ts)."""
    return [
        {
            "id": f"crash-recovery-ev-{i:06d}",
            "node_id": node_id,
            "event_type": "test.crash_recovery",
            "ts": f"2026-01-01T{i // 3600:02d}:{(i % 3600) // 60:02d}:{i % 60:02d}Z",
        }
        for i in range(n)
    ]


def _spawn_worker(db_path: str, events: list[dict]) -> multiprocessing.Process:
    ctx = multiprocessing.get_context("spawn")
    p = ctx.Process(
        target=_worker_ingest,
        args=(db_path, json.dumps(events), _project_root()),
        daemon=False,
    )
    p.start()
    return p


def _count(db_path: str) -> tuple[int, int]:
    """Return (total_rows, distinct_ids) from the events table."""
    import duckdb
    # Brief retry to handle the lock release window after SIGKILL.
    for _ in range(6):
        try:
            with duckdb.connect(db_path, read_only=True) as conn:
                total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                distinct = conn.execute(
                    "SELECT COUNT(DISTINCT id) FROM events"
                ).fetchone()[0]
            return total, distinct
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Could not open {db_path} for count after 6 attempts")


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.timeout(90)
class TestDaemonSigkillCrashRecovery:
    """SIGKILL crash-recovery suite — zero loss, zero dupes."""

    def test_zero_loss_zero_dupes_after_sigkill_and_replay(self, tmp_path):
        """Core invariant: SIGKILL mid-burst + full replay → COUNT = DISTINCT = N."""
        db_path = str(tmp_path / "crash-recovery.duckdb")
        node_id = "node-crash-test-1"
        N = 1000
        events = _make_events(N, node_id)

        # Phase 1 — ingest first half, SIGKILL while events are in-flight.
        # Feeding only events[:N//2] ensures the worker doesn't finish
        # cleanly before we kill it (the flush timer is disabled).
        p1 = _spawn_worker(db_path, events[: N // 2])
        time.sleep(0.8)  # let the worker commit several 50-event batches
        os.kill(p1.pid, signal.SIGKILL)
        p1.join(timeout=5)
        # Don't assert intermediate count — OS scheduling determines
        # exactly how many batches committed before SIGKILL.

        # Phase 2 — replay ALL N events (simulates daemon restart + source
        # replay from JSONL).  INSERT OR IGNORE collapses already-committed
        # events to no-ops; missing events are inserted fresh.
        p2 = _spawn_worker(db_path, events)
        p2.join(timeout=60)
        assert p2.exitcode == 0, f"Replay worker exited {p2.exitcode}"

        total, distinct = _count(db_path)
        assert distinct == N, (
            f"Expected {N} distinct IDs after replay; got {distinct}.  "
            "INSERT OR IGNORE dedup may be broken."
        )
        assert total == N, (
            f"Expected {N} total rows; got {total}.  "
            "Duplicate rows present despite INSERT OR IGNORE primary key."
        )

    def test_committed_events_survive_sigkill(self, tmp_path):
        """DuckDB WAL durability: a committed batch persists across SIGKILL."""
        db_path = str(tmp_path / "committed-survive.duckdb")
        node_id = "node-crash-test-2"
        # One complete flush batch — the batch-size trigger commits it
        # synchronously inside _flush_now_locked before returning to the
        # ingest loop.
        events = _make_events(_FLUSH_BATCH, node_id)

        p = _spawn_worker(db_path, events)
        # 1.5 s is comfortably longer than the time to ingest and commit
        # _FLUSH_BATCH events (each has a 1 ms sleep → ~50 ms for the
        # batch, plus DuckDB write time).
        time.sleep(1.5)
        os.kill(p.pid, signal.SIGKILL)
        p.join(timeout=5)

        total, distinct = _count(db_path)
        assert distinct >= _FLUSH_BATCH, (
            f"Expected ≥ {_FLUSH_BATCH} committed events to survive SIGKILL; "
            f"got {distinct}.  DuckDB WAL may not have flushed before kill."
        )
        assert total == distinct, (
            f"total={total} ≠ distinct={distinct}: duplicates in DuckDB."
        )

    def test_no_dupes_from_double_replay(self, tmp_path):
        """Idempotent replay: running the same events twice leaves N rows, not 2N."""
        db_path = str(tmp_path / "double-replay.duckdb")
        node_id = "node-crash-test-3"
        N = 200
        events = _make_events(N, node_id)

        # First full ingest.
        p1 = _spawn_worker(db_path, events)
        p1.join(timeout=30)
        assert p1.exitcode == 0

        # Second ingest of identical events — must all be INSERT OR IGNORE no-ops.
        p2 = _spawn_worker(db_path, events)
        p2.join(timeout=30)
        assert p2.exitcode == 0

        total, distinct = _count(db_path)
        assert total == N, (
            f"Expected {N} rows after double replay; got {total}.  "
            "Duplicate rows written despite INSERT OR IGNORE."
        )
        assert distinct == N, (
            f"Expected {N} distinct IDs; got {distinct}."
        )
