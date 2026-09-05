"""#5528 — session_phase and session_context stop rewriting rows that did not
change.

After #5496 the one table on a real node still carrying many dead versions
per live row was ``session_phase`` (12 per row eleven minutes after a
compaction): the daemon records every session's phase on every tick, and an
upsert that changes nothing is still a DELETE plus INSERT on a keyed table.
``session_context`` had the same shape at two versions per row.
"""
from __future__ import annotations

import importlib

import pytest


def _fresh(tmp_path, monkeypatch, name="phase.duckdb", **env):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / name))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "999")
    for k in ("CLAWMETRY_PHASE_REFRESH_SECS", "CLAWMETRY_UPSERT_DEDUPE"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


def _versions(store, table):
    with store._write_lock:
        store._conn.execute("CHECKPOINT")
    return store._conn.execute(
        "SELECT estimated_size FROM duckdb_tables() WHERE table_name = ?", [table]
    ).fetchone()[0]


# ── session_phase ──────────────────────────────────────────────────────────

def test_same_phase_on_the_next_tick_writes_nothing(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        first = s.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                       status="waiting_on_user", cwd="/w")
        v1 = _versions(s, "session_phase")
        for _ in range(5):
            same = s.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                          status="waiting_on_user", cwd="/w")
        assert same["phaseSince"] == first["phaseSince"]
        assert same["phase"] == "waiting"
        assert _versions(s, "session_phase") == v1, "unchanged ticks must not rewrite"
        # return_row=False path skips too and returns {}
        assert s.record_session_phase("codex:a", phase="waiting", runtime="codex",
                                      status="waiting_on_user", cwd="/w", return_row=False) == {}
    finally:
        s.stop(flush=True)


def test_a_changed_phase_is_written_and_moves_phase_since(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        first = s.record_session_phase("codex:a", phase="waiting", runtime="codex", cwd="/w",
                                       observed_at=1_000_000.0)
        v1 = _versions(s, "session_phase")
        moved = s.record_session_phase("codex:a", phase="working", runtime="codex", cwd="/w",
                                       observed_at=1_000_050.0)
        assert moved["phase"] == "working" and moved["phaseSince"] > first["phaseSince"]
        assert _versions(s, "session_phase") > v1
        # A cwd change alone is content too (drift detection reads it).
        v2 = _versions(s, "session_phase")
        drift = s.record_session_phase("codex:a", phase="working", runtime="codex", cwd="/elsewhere",
                                       observed_at=1_000_060.0)
        assert drift["cwd"] == "/elsewhere" and drift["initialCwd"] == "/w"
        assert _versions(s, "session_phase") > v2
    finally:
        s.stop(flush=True)


def test_freshness_floor_refreshes_observed_at(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_PHASE_REFRESH_SECS="0")
    s = ls.LocalStore()
    try:
        a = s.record_session_phase("codex:a", phase="waiting", runtime="codex", observed_at=100.0)
        b = s.record_session_phase("codex:a", phase="waiting", runtime="codex", observed_at=200.0)
        assert a["phaseSince"] == b["phaseSince"]      # still one transition
        assert b["observedAt"] == 200.0                 # but the observation is fresh
    finally:
        s.stop(flush=True)


def test_phase_dedupe_survives_a_restart(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, name="r.duckdb")
    s = ls.LocalStore()
    try:
        s.record_session_phase("codex:a", phase="waiting", runtime="codex", cwd="/w")
        s.record_session_phase("codex:b", phase="working", runtime="codex", cwd="/w")
    finally:
        s.stop(flush=True)
    ls2 = _fresh(tmp_path, monkeypatch, name="r.duckdb")
    s = ls2.LocalStore()
    try:
        v1 = _versions(s, "session_phase")
        s.record_session_phase("codex:a", phase="waiting", runtime="codex", cwd="/w", return_row=False)
        s.record_session_phase("codex:b", phase="working", runtime="codex", cwd="/w", return_row=False)
        assert _versions(s, "session_phase") == v1
        s.record_session_phase("codex:b", phase="ended", runtime="codex", cwd="/w", return_row=False)
        assert _versions(s, "session_phase") > v1
    finally:
        s.stop(flush=True)


# ── session_context ────────────────────────────────────────────────────────

def _ctx(i, **o):
    base = {"agent_type": "claude_code", "session_id": "claude_code:s1", "node_id": "n",
            "kind": "system_prompt", "sha256": f"sha{i:03d}", "size_bytes": 10,
            "content": b"hello", "summary": None, "first_ts": "2026-09-01T00:00:00Z",
            "last_ts": "2026-09-01T00:00:00Z", "source": "context.compiled"}
    base.update(o)
    return base


def test_context_redelivery_writes_nothing(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        rows = [_ctx(i) for i in range(20)]
        assert s.ingest_session_context(rows) == 20
        v1 = _versions(s, "session_context")
        assert s.ingest_session_context([dict(r) for r in rows]) == 0
        assert _versions(s, "session_context") == v1
        turns = s._conn.execute("SELECT DISTINCT turns FROM session_context").fetchall()
        assert turns == [(1,)]
    finally:
        s.stop(flush=True)


def test_context_later_occurrence_still_bumps_turns(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch)
    s = ls.LocalStore()
    try:
        s.ingest_session_context([_ctx(1)])
        assert s.ingest_session_context([_ctx(1, last_ts="2026-09-01T00:05:00Z")]) == 1
        turns, last = s._conn.execute(
            "SELECT turns, last_ts FROM session_context WHERE sha256 = 'sha001'").fetchone()
        assert (turns, last) == (2, "2026-09-01T00:05:00Z")
        # A summary arriving for a row that has none is worth writing.
        assert s.ingest_session_context([_ctx(1, last_ts="2026-09-01T00:05:00Z", summary="sys prompt")]) == 1
        assert s._conn.execute(
            "SELECT summary FROM session_context WHERE sha256 = 'sha001'").fetchone()[0] == "sys prompt"
        # And now it is settled: same row again is a no-op.
        assert s.ingest_session_context([_ctx(1, last_ts="2026-09-01T00:05:00Z", summary="sys prompt")]) == 0
    finally:
        s.stop(flush=True)


def test_kill_switch_restores_always_write(tmp_path, monkeypatch):
    ls = _fresh(tmp_path, monkeypatch, CLAWMETRY_UPSERT_DEDUPE="0")
    s = ls.LocalStore()
    try:
        s.ingest_session_context([_ctx(1)])
        assert s.ingest_session_context([_ctx(1)]) == 1
        s.record_session_phase("codex:a", phase="waiting", runtime="codex", return_row=False)
        v1 = _versions(s, "session_phase")
        s.record_session_phase("codex:a", phase="waiting", runtime="codex", return_row=False)
        assert _versions(s, "session_phase") > v1
    finally:
        s.stop(flush=True)
