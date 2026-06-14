"""Guard for the Command River Phase-2 ``loops[]`` snapshot slice
(``clawmetry/sync.py::_build_loops_slice``).

The cloud Command River needs to bind a red "whirlpool" + the Kill/Pause
alarm to the EXACT looping sub-agent lane by session_id. The legacy
deviceSummary.alert / heartbeat `stuck` payload STRIPS the session_id, so the
whirlpool cannot bind. This slice fixes it: a small, bounded, plaintext
``loops[]`` where every entry CARRIES the canonical session_id.

Invariants pinned here (revert-proof — reverting ``_build_loops_slice`` to a
stub returning ``[]`` or dropping the session_id makes these go RED):

  1. A looping session that wrote a loop_signals row appears in ``loops[]``
     carrying its session_id + kind + count + a plain-words title.
  2. A non-looping session (no loop_signals row) is ABSENT from ``loops[]``.
  3. Self-clearing: once a session's loop_signals row ages out of the 30-min
     window (or is no longer re-emitted), it drops from the slice.
  4. A loop_signals row WITHOUT a session_id is never emitted (it can't bind a
     lane) — honesty: never synthesize.
  5. The slice is bounded by ``_LOOPS_SLICE_MAX`` and dedupes per session.

Driver mirrors ``tests/test_loop_signals_integration.py``: reload
``clawmetry.local_store`` against a fresh tmp DuckDB, ingest controlled
loop_signals rows (the exact shape the detector/stuck pass writes), then call
the real ``_build_loops_slice`` over that store. Synthetic loop_signals rows
are the deterministic STORAGE contract input — appropriate here (the
no-synthetic-seeds rule targets end-to-end feature tests).
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fresh_store(tmp_path, monkeypatch):
    """Reload ``clawmetry.local_store`` against a fresh DuckDB file."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "loops_slice.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    # Construct a real writer DuckDB store against the tmp file DIRECTLY,
    # bypassing ``get_store()`` — on a machine with the daemon running,
    # ``get_store()`` returns an HTTP proxy to the LIVE store (so writes would
    # go nowhere this test can read). A direct ``LocalStore`` is hermetic.
    store = ls.LocalStore(read_only=False)
    store.start()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


def _build_loops_slice():
    """Import the real builder from sync.py (no Flask app, no daemon)."""
    import clawmetry.sync as sync
    return sync._build_loops_slice


# ── 1. A looping session appears, carrying its session_id + kind + count ─────


def test_looping_session_carries_session_id_kind_count(fresh_store):
    ls, store = fresh_store
    # The exact row the detector pass writes for a stuck_loop incident.
    store.ingest_loop_signal(
        session_id="claude_code:1aaf7ca1",
        signature="daemon_detect_stuck_loop",
        repeat_count=6,
        severity="warning",
        agent_type="claude_code",
        details={
            "source": "daemon_detector",
            "kind": "stuck_loop",
            "message": "codex looping: 6x identical Bash calls, no progress",
        },
    )
    loops = _build_loops_slice()(store)
    assert len(loops) == 1, "the looping session must appear in loops[]"
    e = loops[0]
    # CRITICAL: the session_id MUST survive so the cloud can bind a lane.
    assert e["session_id"] == "claude_code:1aaf7ca1"
    assert e["kind"] == "stuck_loop"
    assert e["count"] == 6
    assert "looping" in e["title"].lower()
    assert e["severity"] == "warning"
    assert e["runtime"] == "claude_code"
    # first_bad_step_ts / since are populated from first_seen (ISO string).
    assert e["first_bad_step_ts"] is not None
    assert e["since"] == e["first_bad_step_ts"]


# ── 2. A non-looping session is ABSENT ──────────────────────────────────────


def test_non_looping_session_absent(fresh_store):
    ls, store = fresh_store
    # One looping session.
    store.ingest_loop_signal(
        session_id="sess-looping", signature="daemon_detect_no_progress",
        repeat_count=8, agent_type="openclaw",
        details={"kind": "no_progress",
                 "message": "openclaw: 20 tool calls, not advancing"},
    )
    # A second, non-looping session writes NO loop_signals row at all — so it
    # must never appear in the slice.
    loops = _build_loops_slice()(store)
    sids = {e["session_id"] for e in loops}
    assert "sess-looping" in sids
    assert "sess-calm" not in sids, (
        "a session with no loop_signals row must be ABSENT from loops[]"
    )


# ── 3. Self-clearing: an aged-out row drops from the slice ──────────────────


def test_self_clears_when_loop_ages_out(fresh_store):
    ls, store = fresh_store
    # A fresh loop (now-ish) AND an ancient one outside the 30-min window.
    store.ingest_loop_signal(
        session_id="sess-fresh", signature="daemon_detect_stuck_loop",
        repeat_count=4, agent_type="codex",
        details={"kind": "stuck_loop", "message": "codex looping: 4x Bash"},
    )
    store.ingest_loop_signal(
        session_id="sess-stale", signature="daemon_detect_stuck_loop",
        repeat_count=99, agent_type="codex",
        first_seen="2020-01-01T00:00:00", last_seen="2020-01-01T00:00:00",
        details={"kind": "stuck_loop", "message": "old loop"},
    )
    loops = _build_loops_slice()(store)
    sids = {e["session_id"] for e in loops}
    assert "sess-fresh" in sids, "the live loop must be present"
    assert "sess-stale" not in sids, (
        "a loop whose last_seen is outside the 30-min window must self-clear"
    )


# ── 4. A row WITHOUT a session_id is never emitted ──────────────────────────


def test_row_without_session_id_is_dropped(fresh_store):
    ls, store = fresh_store
    # ingest_loop_signal drops a row with an empty session_id at write time —
    # so even at the source there is nothing to bind. Assert the slice is empty
    # and never raises when only such rows are attempted.
    store.ingest_loop_signal(
        session_id="", signature="daemon_detect_stuck_loop", repeat_count=5,
        details={"kind": "stuck_loop", "message": "no sid"},
    )
    loops = _build_loops_slice()(store)
    assert loops == [], (
        "a loop with no session_id cannot bind a lane and must not appear"
    )


# ── 5. Bounded + deduped per session ────────────────────────────────────────


def test_dedupes_per_session_keeps_loudest(fresh_store):
    ls, store = fresh_store
    # Two DIFFERENT signatures for the SAME session (e.g. stuck_loop +
    # no_progress both fired). The river binds ONE whirlpool per lane, so the
    # slice keeps a single entry per session — the loudest (highest count).
    # Omit first_seen/last_seen so both rows are stamped now-ish (in window).
    store.ingest_loop_signal(
        session_id="sess-x", signature="daemon_detect_no_progress",
        repeat_count=8, agent_type="goose",
        details={"kind": "no_progress", "message": "goose: not advancing"},
    )
    store.ingest_loop_signal(
        session_id="sess-x", signature="daemon_detect_stuck_loop",
        repeat_count=20, agent_type="goose",
        details={"kind": "stuck_loop", "message": "goose looping: 20x"},
    )
    loops = _build_loops_slice()(store)
    xs = [e for e in loops if e["session_id"] == "sess-x"]
    assert len(xs) == 1, "one whirlpool per session — dedupe to a single entry"
    assert xs[0]["count"] == 20, "the loudest loop (highest count) wins"


def test_slice_is_bounded(fresh_store, monkeypatch):
    ls, store = fresh_store
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "_LOOPS_SLICE_MAX", 3)
    for i in range(8):
        # Now-ish (in window) so all 8 rows are candidates for the cap.
        store.ingest_loop_signal(
            session_id=f"sess-{i}", signature="daemon_detect_stuck_loop",
            repeat_count=i + 2, agent_type="openclaw",
            details={"kind": "stuck_loop", "message": f"loop {i}"},
        )
    loops = sync._build_loops_slice(store)
    assert len(loops) == 3, "the slice must be capped at _LOOPS_SLICE_MAX"


# ── 6. Generic title fallback when no detector message is present ────────────


def test_generic_title_when_no_message(fresh_store):
    ls, store = fresh_store
    # Proxy LoopDetector rows carry a request-hash signature and NO
    # details.message — the slice must still classify them as a real loop and
    # synthesize a generic plain-words title (no content leak).
    store.ingest_loop_signal(
        session_id="sess-proxy", signature="deadbeef00112233",
        repeat_count=5, agent_type="openclaw",
    )
    loops = _build_loops_slice()(store)
    e = next((x for x in loops if x["session_id"] == "sess-proxy"), None)
    assert e is not None, "a proxy loop (request-hash signature) is a real loop"
    assert e["kind"] == "stuck_loop"
    assert e["count"] == 5
    assert "looping" in e["title"].lower()
