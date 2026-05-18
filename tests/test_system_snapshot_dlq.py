"""Regression test for the ``sync_system_snapshot`` sibling of #1601.

PR #1624 fixed the silent AES-GCM swallow inside ``_flush_session_batch``
but explicitly called out ``sync_system_snapshot`` (sync.py line ~7451) as
sharing the same anti-pattern at lower severity (snapshot is re-emitted
every cycle, so a single drop doesn't cause cumulative loss). This PR
applies the same DLQ pattern so the *first* encryption failure is also
visible + recoverable instead of silently logged as a network error.

## The bug (pre-fix)

``sync_system_snapshot`` wrapped BOTH ``encrypt_payload`` and ``_post`` in
one ``try/except Exception as e``. A corrupt / rotated key raised inside
``encrypt_payload``, the same ``except`` caught it and logged ``System
snapshot sync error`` — pointing the user at the network instead of the
real cause (the key). The snapshot for that cycle was lost.

## The fix (this PR)

Sister of #1624: split the try/except. Encryption failure → persist to
``sync_dlq`` via ``_dlq_enqueue_encryption_failure`` with
``kind='system_snapshot'``. POST failure → existing log.warning + drop
(acceptable, snapshot re-emitted next cycle). The kind-agnostic
``_dlq_replay`` drainer added in #1624 picks up these rows on the next
sync tick — no drainer change needed.

## Scenarios

1. Happy path → snapshot encrypts + POSTs, no DLQ row.
2. Encrypt fails (mocked) → DLQ row created with ``kind='system_snapshot'``.
3. Replay drains the DLQ on next cycle once the key recovers.
"""
from __future__ import annotations

import importlib
import json

import pytest


# ── Fixture infrastructure (mirrors test_aesgcm_swallow_fix.py) ─────────────

def _reload_local_store(tmp_path, monkeypatch):
    """Isolate the DuckDB file per-test so DLQ counts don't leak across
    test runs / parallel xdist workers."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH",
        str(tmp_path / "clawmetry.duckdb"),
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


def _reload_sync(monkeypatch):
    import clawmetry.sync as sync
    importlib.reload(sync)
    return sync


def _minimal_config():
    """Smallest config that lets ``sync_system_snapshot`` reach the
    encrypt/POST step without bailing on the trial-paused / no-key guards.
    The 64-char hex string is decoded base64-style by ``encrypt_payload``;
    any 32-byte key works for the happy-path test."""
    return {
        "api_key": "k",
        "node_id": "n1",
        "encryption_key":
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcd",
    }


# ── Scenario 1: happy path → snapshot encrypts + POSTs, no DLQ row ──────────

def test_snapshot_happy_path_no_dlq(tmp_path, monkeypatch):
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))
    # Force the trial gate open so the function doesn't early-return.
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)

    rc = sync.sync_system_snapshot(
        _minimal_config(),
        state={"spending": {"today": 0, "week": 0, "month": 0}},
        paths={"workspace": str(tmp_path), "sessions_dir": str(tmp_path)},
    )

    store = ls.get_store()
    try:
        assert rc == 1, "happy path must return 1 (POSTed)"
        assert store.dlq_count() == 0, "happy path must not populate DLQ"
        assert len(posted) == 1
        assert posted[0][0] == "/ingest/system-snapshot"
        assert posted[0][1]["encrypted"] is True
        assert isinstance(posted[0][1]["blob"], str)
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


# ── Scenario 2: encrypt fails → DLQ entry created with system_snapshot ─────

def test_snapshot_encrypt_failure_persists_to_dlq(tmp_path, monkeypatch):
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)

    def _boom(payload, key):
        raise RuntimeError("simulated AESGCM failure (corrupt key)")
    monkeypatch.setattr(sync, "encrypt_payload", _boom)

    before = sync.get_encryption_failure_count()
    rc = sync.sync_system_snapshot(
        _minimal_config(),
        state={"spending": {"today": 0, "week": 0, "month": 0}},
        paths={"workspace": str(tmp_path), "sessions_dir": str(tmp_path)},
    )

    store = ls.get_store()
    try:
        # Pre-fix the rc was still 0, but the snapshot was silently lost.
        # Post-fix the snapshot is durable in DLQ — recoverable on replay.
        assert rc == 0, "encrypt failure path returns 0"
        assert store.dlq_count() == 1, "encrypt failure must persist to DLQ"
        rows = store.dlq_list()
        assert rows[0]["kind"] == "system_snapshot", (
            f"DLQ row must be tagged kind=system_snapshot, got {rows[0]['kind']!r}"
        )
        assert rows[0]["endpoint"] == "/ingest/system-snapshot"
        assert rows[0]["node_id"] == "n1"
        # Payload survives round-trip — the replayer needs it intact.
        payload = json.loads(rows[0]["payload_json"])
        assert "system" in payload, "snapshot payload shape preserved"
        # POST must NOT have been attempted (no blob to send).
        assert posted == [], "POST must be skipped when encryption fails"
        # Counter incremented (ops metric shared with session-batch path).
        assert sync.get_encryption_failure_count() == before + 1
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


# ── Scenario 3: DLQ row drains on next sync cycle once key recovers ─────────

def test_snapshot_dlq_replay_drains_on_next_cycle(tmp_path, monkeypatch):
    """Confirm the kind-agnostic ``_dlq_replay`` from #1624 picks up the
    new ``kind='system_snapshot'`` rows without modification. This is the
    whole reason the drainer is kind-agnostic — sister fixes shouldn't
    each need their own replayer."""
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(sync, "_post", lambda *a, **k: None)

    # Tick 1: encryption fails, snapshot parked in DLQ.
    monkeypatch.setattr(sync, "encrypt_payload",
                        lambda payload, key: (_ for _ in ()).throw(
                            RuntimeError("transient bad-key window")))
    enc_key = (
        "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcd"
    )
    sync.sync_system_snapshot(
        _minimal_config(),
        state={"spending": {"today": 0, "week": 0, "month": 0}},
        paths={"workspace": str(tmp_path), "sessions_dir": str(tmp_path)},
    )
    store = ls.get_store()
    assert store.dlq_count() == 1, "precondition: snapshot parked in DLQ"
    rows = store.dlq_list()
    assert rows[0]["kind"] == "system_snapshot"
    assert rows[0]["endpoint"] == "/ingest/system-snapshot"

    # Tick 2: user rotates the key back. Restore real encrypt_payload by
    # reloading the module, then capture the POST that the drainer fires.
    importlib.reload(sync)
    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))

    replayed = sync._dlq_replay(api_key="k", enc_key=enc_key)
    try:
        assert replayed == 1, f"expected 1 replay, got {replayed}"
        assert store.dlq_count() == 0, "DLQ must be drained after success"
        assert len(posted) == 1
        # Drainer must route the row to its ORIGINAL endpoint, not the
        # session-batch endpoint — that's why the row stores it explicitly.
        assert posted[0][0] == "/ingest/system-snapshot"
        assert posted[0][1]["encrypted"] is True
        assert posted[0][1]["node_id"] == "n1"
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass
