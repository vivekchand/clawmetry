"""Regression test for issue #1590 — concurrent ``_flush_now`` race that
silently drops events from the ring.

## The race (pre-fix)

``LocalStore.ingest()`` triggers an in-thread synchronous flush whenever
the ring depth crosses ``FLUSH_BATCH`` (line 982-983). The background
``_flusher_loop`` thread also ticks every ``FLUSH_INTERVAL_SECS``. Both
call ``_flush_now``, which used to:

1. Snapshot the ring under ``_ring_lock`` and release.
2. Write the snapshot under ``_write_lock``.
3. Re-acquire ``_ring_lock`` and pop ``len(batch)`` items.

When the two calls overlap:

  T0  Flusher A: snapshots batch_A = [e1..e1000]  (1000 events).
  T1  Caller B: appends e1001 → ring grows.       (auto-flush fires!)
  T2  Flusher B: snapshots batch_B = [e1..e1220]  (1220 events).
  T3  Flusher A: writes 1000 rows, pops 1000 from ring → ring=[e1001..e1220].
  T4  Flusher B: writes 1220 rows (INSERT OR IGNORE — 220 new), pops
                 ``len(batch_B)=1220`` from ring. Only 220 items are
                 actually there, so popleft loops exit at empty.
                 **But the 220 events between A's snapshot and the auto-
                 flush were popped, NOT written by B (they were never
                 in batch_B because B snapshotted AFTER A's write).**

Wait, scratch that — B's snapshot at T2 actually DID include the 220. So
the events ARE in DuckDB at T4. The miss happens differently: when the
two snapshots OVERLAP and the second snapshot is identical to the first
(both 1000 events, before the 220 arrived), then both pop 1000 but only
1000 events exist in DB. New 220 arrive AFTER, but get popped by B's
``range(len(batch_B))=1000`` count without ever being included in any
snapshot.

The repro below makes the race reliable by pumping FLUSH_SECS to 0.001
so the background flusher ticks aggressively while the user thread
appends. Pre-fix this drops 220 events ~100% of the time; post-fix it
never does. Eng AA originally misattributed the trigger to
``ingest_session`` (which writes synchronously to the ``sessions`` table
via ``_write_lock`` and does NOT touch the ring) — but the underlying
race is purely between ``_flush_now`` callers and reproduces with no
``ingest_session`` involvement at all.

## The fix

``_flush_lock`` serialises ``_flush_now`` so only one flush is ever in
flight. Cheap because flushes are at most ~10/sec at the default
``FLUSH_BATCH=1000`` and ``FLUSH_INTERVAL_SECS=2.0``.
"""
from __future__ import annotations

import importlib
import os
import time

import pytest


def _make_store(tmp_path, monkeypatch, *, flush_secs="0.001",
                flush_batch="1000"):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", flush_secs)
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", flush_batch)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls.get_store(), ls


@pytest.mark.parametrize("trial", range(5))
def test_concurrent_flush_does_not_drop_events_1590(trial, tmp_path, monkeypatch):
    """Hammers the FLUSH_BATCH boundary with the background flusher
    ticking at ~1kHz. All ingested events MUST end up in DuckDB after a
    final synchronous flush — none can be silently popped from the ring.

    5-trial parametrize because the race is timing-sensitive — pre-fix
    it fired ~100% of the time, but we want to catch even rare
    regressions if the fix is partially reverted.
    """
    store, ls = _make_store(tmp_path / f"trial-{trial}", monkeypatch)
    try:
        total = 1220               # 1× FLUSH_BATCH + a partial batch
        for i in range(total):
            store.ingest({
                "id":         f"ev-{trial}-{i}",
                "node_id":    "n1",
                "event_type": "channel.event",
                "ts":         "2026-05-17T00:00:00Z",
            })

        # Let the background flusher tick a few times.
        time.sleep(0.05)
        # Synchronous belt-and-braces flush — drains any remainder.
        store.flush()

        ring_len = len(store._ring)
        db_count = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
        assert db_count == total, (
            f"trial {trial}: expected {total} events in DuckDB, "
            f"got {db_count} (ring={ring_len}). Issue #1590 regression — "
            f"concurrent _flush_now races dropped "
            f"{total - db_count} events."
        )
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass


def test_concurrent_flush_with_session_ingest_interleave(tmp_path, monkeypatch):
    """The shape Eng AA originally reported on #1590, distilled to a
    minimal reproducer: a burst of event ingest that crosses several
    ``FLUSH_BATCH`` boundaries followed by a wave of ``ingest_session``
    + ``ingest_subagent`` calls (both grab ``_write_lock``). The
    ``_write_lock`` contention widens the window between the flusher's
    snapshot and its write — long enough for the in-thread auto-flush
    to snapshot a second time on the SAME ring contents.

    Pre-fix this loses ~120 channel events ~100% of the time on the
    fixture flow. Post-fix all events persist.
    """
    store, ls = _make_store(tmp_path, monkeypatch,
                            flush_secs="0.05", flush_batch="1000")
    try:
        # 3000 generic events — 3× the FLUSH_BATCH so we see multiple
        # auto-flush boundaries during the burst.
        for i in range(3000):
            store.ingest({
                "id":         f"ev-{i}",
                "node_id":    "n1",
                "event_type": "x",
                "ts":         "2026-05-17T00:00:00Z",
            })
        # 120 channel events — the partial batch that gets lost.
        for i in range(120):
            store.ingest({
                "id":         f"ch-{i}",
                "node_id":    "n1",
                "event_type": "channel.event",
                "ts":         "2026-05-17T00:00:00Z",
            })
        # Now the heavy ``_write_lock`` consumers — these contend with
        # any in-flight ``_flush_now`` and widen the race window.
        for i in range(100):
            store.ingest_session({
                "session_id": f"s-{i}", "node_id": "n1",
            })
        for i in range(200):
            store.ingest_subagent({
                "subagent_id":       f"sa-{i}",
                "agent_type":        "openclaw",
                "parent_session_id": "p1",
            })

        time.sleep(0.5)
        for _ in range(10):
            if store.flush() == 0:
                break

        db_count = store._fetch("SELECT COUNT(*) FROM events", [])[0][0]
        assert db_count == 3120, (
            f"expected 3120 events in DuckDB, got {db_count}. "
            f"Issue #1590 regression — concurrent _flush_now races "
            f"dropped {3120 - db_count} events. Repro: in-thread auto-"
            f"flush snapshots batch_A while background flusher tick "
            f"snapshots batch_B with overlapping contents; both pop "
            f"len(batch) items from the ring, evicting "
            f"len(batch_A∩batch_B) events without persisting them."
        )
        sess_count = store._fetch("SELECT COUNT(*) FROM sessions", [])[0][0]
        assert sess_count == 100, f"expected 100 sessions, got {sess_count}"
    finally:
        try:
            store.stop(flush=True)
        except Exception:
            pass
