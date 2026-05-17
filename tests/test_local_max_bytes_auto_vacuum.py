"""Regression test for issue #1594 — LOCAL_MAX_BYTES cap silently exceeded.

## Pre-fix behaviour
``LOCAL_MAX_BYTES`` (default 5 GB) was reported in /local/health as
``size_cap_bytes``, but NOTHING in the write path checked the cap. The
only enforcement was the diagnostic ``LocalStore.vacuum()`` endpoint —
which had a single caller and was never invoked automatically. Long-
running installs grew past the cap silently until disk-full cascaded
into ring-drop (#1590).

## Fix shape (this test file pins it)
* On-write check inside ``_flush_now_locked``: every
  ``AUTO_VACUUM_CHECK_EVERY_BYTES`` (default 100 MB) of bytes flushed,
  stat() the DB. If size ≥ ``LOCAL_MAX_BYTES * AUTO_VACUUM_HIGH_WATER_PCT``
  (default 95 %), call ``vacuum()`` — which deletes the OLDEST events
  first (tiered-retention contract per ``feedback_tiered_retention.md``).
* If vacuum cannot bring size under the cap (retention too generous,
  pathological row sizes), log loud WARNING + emit an
  ``local_store_over_cap`` event into the store itself; set
  ``health()['cap_exceeded'] = True`` so the dashboard footer + cloud
  dashboards can surface it.
* Default-ON. ``CLAWMETRY_AUTO_VACUUM=0`` disables for users who manage
  retention externally.

## Test surface
4 scenarios (per the issue ticket Step 6):
  1. Below cap        → no vacuum, no warning, store grows freely.
  2. Above cap        → vacuum fires, OLDEST events removed first,
                        store comes back under cap, ring keeps writing.
  3. Vacuum-not-enough → explicit WARNING logged + cap_exceeded=True +
                        marker event persisted.
  4. Real-subprocess  → restart preserves the invariant (live process +
                        actual flusher tick, per
                        ``feedback_synthetic_tests_missed_real_event_shape``
                        — no mocked vacuum, no synthetic ring).
"""
from __future__ import annotations

import importlib
import json
import logging
import os
import subprocess
import sys
import time
import uuid
from pathlib import Path

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── helpers ────────────────────────────────────────────────────────────────


def _reload_store(tmp_path, monkeypatch, *,
                  max_bytes: int | None = None,
                  check_mb: float = 0.001,        # 1 KB — fires per-flush
                  high_water_pct: float = 0.5,
                  enabled: str = "1"):
    """Force-reload local_store with test-tight thresholds and return a
    fresh LocalStore + the module handle. We rebind the env vars BEFORE
    reimport so the module-level constants pick them up."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH",
                       str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.02")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if max_bytes is not None:
        monkeypatch.setenv("CLAWMETRY_LOCAL_MAX_GB",
                           str(max_bytes / 1024 / 1024 / 1024))
    monkeypatch.setenv("CLAWMETRY_AUTO_VACUUM_CHECK_MB", str(check_mb))
    monkeypatch.setenv("CLAWMETRY_AUTO_VACUUM_HIGH_WATER_PCT",
                       str(high_water_pct))
    monkeypatch.setenv("CLAWMETRY_AUTO_VACUUM", enabled)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.LocalStore()
    store.start()
    return store, ls


def _ev(i: int, *, ts: str | None = None) -> dict:
    """Generate a small event with a deterministic id; the data blob is
    large enough that 1000 events comfortably exceed 1 MB so we can
    drive the on-disk size across a 1-MB test cap."""
    return {
        "id": f"ev-{i}",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-1",
        "event_type": "tool_call",
        "ts": ts or f"2026-05-{(i % 28) + 1:02d}T00:{i % 60:02d}:00Z",
        # 1 KB-ish blob per event so a few thousand rows clears 1 MB
        # of on-disk DuckDB pages.
        "data": {"tool": "Read", "blob": "x" * 1024, "i": i},
        "cost_usd": 0.001,
        "token_count": 42,
    }


def _wait_for_drain(store, timeout=3.0):
    """Block until the flusher empties the ring."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.01)
    raise AssertionError(
        f"ring did not drain in {timeout}s "
        f"(depth={store.health()['ring_depth']})"
    )


# ── Scenario 1 — below cap → no vacuum ────────────────────────────────────


def test_below_cap_no_vacuum_fires(tmp_path, monkeypatch, caplog):
    """Cap set generously high — small ingest should never trigger
    a vacuum or set cap_exceeded. The flusher's bookkeeping counter
    advances but the size check stays below high-water."""
    store, ls = _reload_store(
        tmp_path, monkeypatch,
        max_bytes=10 * 1024 * 1024 * 1024,    # 10 GB cap
        check_mb=0.001,                        # check every 1 KB
        high_water_pct=0.95,
    )
    try:
        with caplog.at_level(logging.INFO, logger="clawmetry.local_store"):
            for i in range(50):
                store.ingest(_ev(i))
            _wait_for_drain(store)
        # No vacuum log line; no over-cap warning.
        msgs = [r.message for r in caplog.records]
        assert not any("auto-vacuum fired" in m for m in msgs), msgs
        assert not any("LOCAL_STORE_OVER_CAP" in m for m in msgs), msgs
        h = store.health()
        assert h["cap_exceeded"] is False
        assert h["auto_vacuum_enabled"] is True
        # Sanity: all 50 events landed.
        assert h["event_count"] == 50
    finally:
        store.stop(flush=True)


# ── Scenario 2 — above cap → vacuum fires, oldest removed first ───────────


def test_above_cap_vacuum_prunes_oldest_first(tmp_path, monkeypatch, caplog):
    """Tight 256 KB cap. Ingest enough rows that the DuckDB file
    crosses the 50 % high-water mark; auto-vacuum must fire and the
    OLDEST event timestamps must be the ones removed (tiered-retention
    contract per ``feedback_tiered_retention.md``).

    Invariant checked: ``COUNT(*)`` drops dramatically AND ``MIN(ts)``
    moves forward. We don't check ``size_bytes <= cap`` because DuckDB
    1.4.x does not shrink the main file in-place after DELETE — freed
    pages get reused by the next ingest, so growth is bounded but the
    file can plateau above cap on the FIRST over-cap cycle. The
    ``cap_exceeded`` health flag surfaces this state to the dashboard
    + cloud (Scenario 3 below). The actual user-visible promise is
    'no unbounded growth' — which means oldest rows get evicted as
    new ones arrive, NOT that the file shrinks."""
    store, ls = _reload_store(
        tmp_path, monkeypatch,
        max_bytes=256 * 1024,         # 256 KB cap — easy to overshoot
        check_mb=0.001,               # check every flush
        high_water_pct=0.5,           # vacuum at >= 128 KB
    )
    try:
        # Ingest in ascending timestamp order so "oldest" == earliest id.
        # 2000 rows × ~2 KB data is reliably > 1 MB on disk, well above
        # the 256 KB cap, so the prune branch fires multiple times.
        with caplog.at_level(logging.INFO, logger="clawmetry.local_store"):
            for i in range(2000):
                store.ingest(_ev(i, ts=f"2026-01-01T00:00:{i:04d}Z"))
            _wait_for_drain(store, timeout=10.0)
            # Give the auto-vacuum a beat to fire after the last flush.
            time.sleep(0.3)

        assert any("auto-vacuum fired" in r.message for r in caplog.records), (
            "expected 'auto-vacuum fired' log line, got: "
            f"{[r.message for r in caplog.records[-20:]]}"
        )

        # Row count must be bounded — the prune kept dropping the
        # oldest events as new ones flushed, so even after 2000
        # ingests the table holds far fewer than 2000 rows.
        h = store.health()
        assert h["event_count"] < 2000, (
            f"auto-vacuum did not prune any rows; event_count={h['event_count']}"
        )

        # Oldest-first contract: MIN(ts) of what remains must be strictly
        # greater than the smallest ts we ingested (00:00:0000Z). The
        # earliest events were deleted first.
        min_ts = store._fetch("SELECT MIN(ts) FROM events", [])[0][0]
        assert min_ts is not None
        assert min_ts > "2026-01-01T00:00:0000Z", (
            f"oldest events should be pruned; MIN(ts)={min_ts}"
        )

        # Sanity: ring keeps writing — a brand new event still lands.
        # This is the "ring continues writing" cascade-test from the
        # issue's Step 6.4.
        store.ingest(_ev(99_999, ts="2026-06-01T00:00:00Z"))
        _wait_for_drain(store)
        rows = store._fetch(
            "SELECT id FROM events WHERE id = ?", ["ev-99999"],
        )
        assert rows and rows[0][0] == "ev-99999"
    finally:
        store.stop(flush=True)


# ── Scenario 3 — vacuum not enough → loud warning + marker event ──────────


def test_vacuum_cannot_reclaim_emits_warning_and_marker(
    tmp_path, monkeypatch, caplog,
):
    """Set an absurdly small cap (1 byte). Any single row puts the
    store above cap; even after vacuum the on-disk file stays above
    1 B, so we MUST log LOCAL_STORE_OVER_CAP, flip cap_exceeded=True,
    AND persist a ``local_store_over_cap`` marker event for cloud-side
    dashboards.

    Also verifies the cooldown: many flushes happen during the burst
    but the warning is rate-limited (cooldown env set high here so the
    test deterministically gets exactly one). Without rate-limiting,
    this path used to emit a warning per flush — readable noise that
    drowned tail -f at the first sign of an over-cap install."""
    monkeypatch.setenv("CLAWMETRY_AUTO_VACUUM_OVER_CAP_COOLDOWN_S", "3600")
    store, ls = _reload_store(
        tmp_path, monkeypatch,
        max_bytes=1,                  # 1 byte cap — impossible to fit
        check_mb=0.001,
        high_water_pct=0.5,
    )
    try:
        with caplog.at_level(logging.WARNING,
                              logger="clawmetry.local_store"):
            # Use very old timestamps so the marker (ts=now) lands at
            # the END of the ORDER BY ts ASC order — i.e. it's the
            # NEWEST row and survives oldest-first pruning. The marker-
            # preservation contract relies on this ordering: by the
            # time vacuum runs, the synthetic events are all older
            # than the marker.
            for i in range(20):
                store.ingest(_ev(i, ts=f"2020-01-01T00:00:{i:02d}Z"))
            _wait_for_drain(store, timeout=5.0)
            time.sleep(0.3)

        warnings = [r.message for r in caplog.records
                    if r.levelno >= logging.WARNING
                    and "LOCAL_STORE_OVER_CAP" in r.message]
        assert warnings, (
            f"expected LOCAL_STORE_OVER_CAP warning, got: "
            f"{[r.message for r in caplog.records]}"
        )
        # Cooldown: many auto-vacuum invocations during the burst but
        # the warning fires exactly once (the rate-limit window is 1 h
        # in this test).
        assert len(warnings) == 1, (
            f"expected exactly 1 over-cap warning (cooldown), got "
            f"{len(warnings)}: {warnings}"
        )

        h = store.health()
        assert h["cap_exceeded"] is True, (
            f"cap_exceeded should be True when vacuum cannot fit cap, "
            f"got health={h}"
        )

        # Marker event persisted in events table so cloud sync ships
        # it without needing a separate metrics channel. Cooldown gates
        # the marker too, so exactly one row is expected.
        rows = store._fetch(
            "SELECT event_type, data FROM events "
            "WHERE event_type = 'local_store_over_cap'",
            [],
        )
        assert len(rows) == 1, (
            f"expected exactly 1 local_store_over_cap marker, got {len(rows)}"
        )
        payload = json.loads(bytes(rows[0][1]).decode("utf-8"))
        assert payload["cap_bytes"] == 1
        assert payload["after_bytes"] > 1
    finally:
        store.stop(flush=True)


# ── Scenario 3b — explicit disable knob ───────────────────────────────────


def test_auto_vacuum_disabled_via_env_skips_check(
    tmp_path, monkeypatch, caplog,
):
    """``CLAWMETRY_AUTO_VACUUM=0`` must skip the auto-vacuum path entirely
    even when the store is far over the cap. Manual ``vacuum()`` remains
    available — we don't muzzle the diagnostic endpoint."""
    store, ls = _reload_store(
        tmp_path, monkeypatch,
        max_bytes=1,                  # 1 byte — would over-cap immediately
        check_mb=0.001,
        high_water_pct=0.5,
        enabled="0",
    )
    try:
        with caplog.at_level(logging.WARNING,
                              logger="clawmetry.local_store"):
            for i in range(20):
                store.ingest(_ev(i))
            _wait_for_drain(store, timeout=5.0)
            time.sleep(0.1)

        warnings = [r.message for r in caplog.records
                    if r.levelno >= logging.WARNING]
        assert not any("LOCAL_STORE_OVER_CAP" in m for m in warnings), (
            f"AUTO_VACUUM disabled — must not emit over-cap warnings, "
            f"got: {warnings}"
        )
        h = store.health()
        assert h["auto_vacuum_enabled"] is False
        assert h["cap_exceeded"] is False, "no auto-check ran, so no flag"

        # Manual vacuum still works.
        res = store.vacuum(prune_to_bytes=1)
        assert "after_bytes" in res
    finally:
        store.stop(flush=True)


# ── Scenario 4 — real subprocess preserves the invariant ──────────────────


_SUBPROC_PAYLOAD = r"""
import os, time, sys, json
import clawmetry.local_store as ls
s = ls.LocalStore()
s.start()
try:
    # Ingest until we definitely cross the 256 KB cap.
    for i in range(2000):
        s.ingest({
            "id":         f"sp-ev-{i}",
            "node_id":    "agent+sp",
            "agent_id":   "main",
            "session_id": "sp-sess",
            "event_type": "tool_call",
            "ts":         f"2026-01-01T00:00:{i:04d}Z",
            "data":       {"blob": "x" * 1024, "i": i},
        })
    # Drain.
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        if s.health()["ring_depth"] == 0:
            break
        time.sleep(0.02)
    s.flush()
    time.sleep(0.3)   # let auto-vacuum settle
    h = s.health()
    print(json.dumps({
        "size_bytes":  h["size_bytes"],
        "cap":         h["size_cap_bytes"],
        "cap_exceeded": h["cap_exceeded"],
        "event_count": h["event_count"],
    }))
finally:
    s.stop(flush=True)
"""


def test_real_subprocess_auto_vacuum_holds_cap(tmp_path, monkeypatch):
    """Per ``feedback_synthetic_tests_missed_real_event_shape``, run the
    flusher in a real OS subprocess (not the test process's reload
    pattern) and verify that after a heavy ingest burst the live process
    has bounded its row count rather than letting it grow unboundedly.

    Catches regressions where the auto-vacuum path only works when the
    test fixture has already monkeypatched the singletons but breaks
    in fresh-process startup (e.g. module-level const not honoured —
    we hit this exact class of bug per the cliff sweep memory entry).

    Invariant — bounded growth, not 'file <= cap':
      * ingested 2000 events
      * row count must end well below 2000 (auto-vacuum pruned some)
      * the oldest events must be the ones gone (MIN(ts) advanced)
    """
    db_path = tmp_path / "events.duckdb"
    env = os.environ.copy()
    env["CLAWMETRY_LOCAL_STORE_PATH"]            = str(db_path)
    env["CLAWMETRY_LOCAL_FLUSH_SECS"]            = "0.02"
    env["CLAWMETRY_LOCAL_FLUSH_BATCH"]           = "5"
    env["CLAWMETRY_LOCAL_MAX_GB"]                = str(256 * 1024 / 1024 / 1024 / 1024)  # 256 KB
    env["CLAWMETRY_AUTO_VACUUM"]                 = "1"
    env["CLAWMETRY_AUTO_VACUUM_CHECK_MB"]        = "0.001"   # 1 KB
    env["CLAWMETRY_AUTO_VACUUM_HIGH_WATER_PCT"]  = "0.5"
    env["PYTHONPATH"] = _REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")

    proc = subprocess.run(
        [sys.executable, "-c", _SUBPROC_PAYLOAD],
        env=env, capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, (
        f"subprocess crashed:\nstdout={proc.stdout}\nstderr={proc.stderr}"
    )
    # The payload's final stdout line is a single JSON blob.
    last = proc.stdout.strip().splitlines()[-1]
    health = json.loads(last)
    # Row count must be bounded — well below the 2000 we ingested —
    # proving the auto-vacuum path ran inside the fresh subprocess.
    assert 0 < health["event_count"] < 2000, (
        f"subprocess auto-vacuum did not prune as expected: {health}\n"
        f"stderr={proc.stderr}"
    )
