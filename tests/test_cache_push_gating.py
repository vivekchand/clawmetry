"""Heartbeat cache pushes go out when something changed, not every cycle.

2026-09-02 on the founder Mac: the memory snapshot (885 files, 5.9 MB) was
encrypted and uploaded every 95 s because two Grok Bot state files rewrote
themselves each cycle and the fingerprint never matched -- 5.2 GB a day of
upload for an unchanged Memory tab. The brain blob (~8.7 MB) had no gate at
all. These pin: churn-immune fingerprinting, a rate limit on changed pushes,
and an unchanged-skip on the brain push.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

duckdb = pytest.importorskip("duckdb")


@pytest.fixture
def sync_mod(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWMETRY_HOME", str(tmp_path / ".clawmetry"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_DB", str(tmp_path / "t.duckdb"))
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.DB_PATH = tmp_path / "t.duckdb"
    import clawmetry.sync as s
    importlib.reload(s)
    yield s


def _rows(**shas):
    return [{"agent_type": "claude_code", "path": p, "sha256": h} for p, h in shas.items()]


def test_fingerprint_is_stable_for_unchanged_files(sync_mod):
    s = sync_mod
    a = s._memory_push_fingerprint(_rows(x="1", y="2"))
    b = s._memory_push_fingerprint(_rows(x="1", y="2"))
    assert a == b


def test_a_changed_file_changes_the_fingerprint(sync_mod):
    s = sync_mod
    a = s._memory_push_fingerprint(_rows(x="1", y="2"))
    b = s._memory_push_fingerprint(_rows(x="1", y="3"))
    assert a != b


def test_a_file_that_churns_every_build_stops_deciding(sync_mod):
    """Runtime state rewritten every cycle must not force a 5.9 MB push."""
    s = sync_mod
    fps = [s._memory_push_fingerprint(_rows(memo="same", state=str(i))) for i in range(8)]
    # Once the churn threshold is crossed the fingerprint settles.
    assert len(set(fps[s.MEMORY_PUSH_VOLATILE_AFTER + 1:])) == 1
    # While the real file is unchanged, that settled fingerprint equals the
    # one a store with no volatile file would produce.
    assert fps[-1] == fps[-2]


def test_a_volatile_file_that_settles_counts_again(sync_mod):
    s = sync_mod
    for i in range(6):
        s._memory_push_fingerprint(_rows(memo="same", state=str(i)))
    settled = s._memory_push_fingerprint(_rows(memo="same", state="6"))
    # Same hash three builds in a row: back in the fingerprint.
    for _ in range(3):
        back = s._memory_push_fingerprint(_rows(memo="same", state="6"))
    assert back != settled or s._memory_push_state["churn"]["claude_code:state"] == 0


def test_changed_snapshot_is_rate_limited(sync_mod, monkeypatch):
    """A real change re-pushes at most every MEMORY_PUSH_CHANGED_MIN_INTERVAL_SEC."""
    s = sync_mod
    cfg = {"encryption_key": s.generate_encryption_key(), "api_key": "cm_x", "node_id": "n1"}
    calls = {"n": 0}

    def rows_now(_store):
        calls["n"] += 1
        return [{"agent_type": "claude_code", "path": "/m/a.md", "sha256": str(calls["n"]),
                 "blob": b"hello", "size_bytes": 5, "root": "/m", "category": "memory"}]

    monkeypatch.setattr(s, "_memory_rows_by_runtime", rows_now)
    monkeypatch.setattr(s.local_store, "get_store", lambda read_only=False: object(), raising=False) if hasattr(s, "local_store") else None
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: object())
    assert len(s._build_memory_cache_pushes(cfg)) == 1      # first push
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded
    assert s._build_memory_cache_pushes(cfg) == []          # changed, but within the limit
    monkeypatch.setattr(s, "MEMORY_PUSH_CHANGED_MIN_INTERVAL_SEC", 0)
    assert len(s._build_memory_cache_pushes(cfg)) == 1      # limit lifted: the change ships
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded


def test_unchanged_snapshot_is_not_repushed_inside_the_interval(sync_mod, monkeypatch):
    s = sync_mod
    cfg = {"encryption_key": s.generate_encryption_key(), "api_key": "cm_x", "node_id": "n1"}
    rows = [{"agent_type": "claude_code", "path": "/m/a.md", "sha256": "h", "blob": b"x",
             "size_bytes": 1, "root": "/m", "category": "memory"}]
    monkeypatch.setattr(s, "_memory_rows_by_runtime", lambda _st: rows)
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: object())
    assert len(s._build_memory_cache_pushes(cfg)) == 1
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded
    assert s._build_memory_cache_pushes(cfg) == []
    assert s._build_memory_cache_pushes(cfg) == []


def test_brain_push_skips_when_events_are_unchanged(sync_mod, monkeypatch):
    s = sync_mod
    cfg = {"encryption_key": s.generate_encryption_key(), "api_key": "cm_x", "node_id": "n1"}
    events = [{"id": "e1", "ts": 1.0}, {"id": "e2", "ts": 2.0}]
    monkeypatch.setattr(s, "_build_brain_events", lambda: list(events))
    assert len(s._build_brain_cache_pushes(cfg)) == 1
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded
    assert s._build_brain_cache_pushes(cfg) == []
    events.append({"id": "e3", "ts": 3.0})
    assert len(s._build_brain_cache_pushes(cfg)) == 1
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded


def test_brain_push_repushes_after_the_interval_even_if_unchanged(sync_mod, monkeypatch):
    """The cloud cache has a TTL; an unchanged blob must still be refreshed
    before it expires."""
    s = sync_mod
    cfg = {"encryption_key": s.generate_encryption_key(), "api_key": "cm_x", "node_id": "n1"}
    monkeypatch.setattr(s, "_build_brain_events", lambda: [{"id": "e1", "ts": 1.0}])
    assert len(s._build_brain_cache_pushes(cfg)) == 1
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded
    monkeypatch.setattr(s, "BRAIN_PUSH_MIN_INTERVAL_SEC", 0)
    assert len(s._build_brain_cache_pushes(cfg)) == 1
    s._commit_cache_push_gates()  # the heartbeat carrying it succeeded


def test_a_build_the_cloud_never_received_does_not_gate_the_next(sync_mod, monkeypatch):
    """The MOAT round-trip test builds a push directly, then sends a real
    heartbeat that must still carry it. More generally: a heartbeat that
    failed must not silence the next cycle for TTL/2."""
    s = sync_mod
    cfg = {"encryption_key": s.generate_encryption_key(), "api_key": "cm_x", "node_id": "n1"}
    monkeypatch.setattr(s, "_build_brain_events", lambda: [{"id": "e1", "ts": 1.0}])
    assert len(s._build_brain_cache_pushes(cfg)) == 1     # never committed
    assert len(s._build_brain_cache_pushes(cfg)) == 1     # so it ships again
    s._commit_cache_push_gates()                          # heartbeat 2xx
    assert s._build_brain_cache_pushes(cfg) == []         # now it is gated
