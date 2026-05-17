"""Regression test for issue #1601 — AES-GCM encryption failure inside
``_flush_session_batch`` silently swallowed the entire batch.

## The bug (pre-fix)

``clawmetry/sync.py::_flush_session_batch`` wrapped BOTH ``encrypt_payload``
and ``_post`` in a single ``try/except``. When encryption raised (corrupt
key, key rotation race, payload contains non-JSON-serialisable bytes), the
same ``except`` caught it and logged ``cloud /ingest/events POST failed`` —
falsely pointing at the network. Local DuckDB was already durable above,
so the caller's cursor advanced normally and the events were permanently
dropped from the cloud side until the user manually rewound state.json.

## The fix (this PR)

1. Split the try/except: encryption failure is a distinct error path with
   a distinct log line and a persistent DLQ enqueue.
2. ``sync_dlq`` table in local_store.py holds the failed payload + ctx.
3. ``_dlq_replay`` drains the queue on every sync tick. Re-encrypt
   succeeds the moment the key is rotated back / patched.
4. DLQ is in DuckDB → survives daemon restart (key requirement from #1601).
5. ``get_encryption_failure_count()`` exposes a per-process counter for
   ops dashboards.

## Scenarios

1. Normal encrypt → no DLQ row (happy path stays untouched).
2. Encrypt fails (mocked) → payload persisted to DLQ.
3. Replay on next sync cycle re-encrypts and POSTs → DLQ drained.
4. DLQ row survives a real subprocess restart of the daemon.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import textwrap

import pytest


# ── Fixture infrastructure ──────────────────────────────────────────────────

def _reload_local_store(tmp_path, monkeypatch):
    """Point local_store at an isolated DuckDB file and reload the module
    so module-level singletons see the new path. Returns the reloaded
    module."""
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


# ── Scenario 1: happy path — no DLQ row ─────────────────────────────────────

def test_normal_encrypt_writes_no_dlq_row(tmp_path, monkeypatch):
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))
    monkeypatch.setattr(sync, "_local_ingest_session_batch", lambda *a, **k: None)

    # Real AES key (any 32-byte base64url string works).
    enc_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcd"

    sync._flush_session_batch(
        [{"id": "ev-1", "type": "message"}],
        "sess-1.jsonl",
        api_key="k",
        enc_key=enc_key,
        node_id="n1",
    )

    store = ls.get_store()
    try:
        assert store.dlq_count() == 0, "happy path should not populate DLQ"
        assert len(posted) == 1
        assert posted[0][0] == "/ingest/events"
        assert posted[0][1]["encrypted"] is True
        assert isinstance(posted[0][1]["blob"], str)
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


# ── Scenario 2: encrypt fails → persisted to DLQ, not lost ──────────────────

def test_encrypt_failure_persists_to_dlq(tmp_path, monkeypatch):
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    monkeypatch.setattr(sync, "_local_ingest_session_batch", lambda *a, **k: None)
    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))

    def _boom(payload, key):
        raise RuntimeError("simulated AESGCM failure (corrupt key)")
    monkeypatch.setattr(sync, "encrypt_payload", _boom)

    before = sync.get_encryption_failure_count()
    sync._flush_session_batch(
        [{"id": "ev-2", "type": "message"}],
        "sess-2.jsonl",
        api_key="k",
        enc_key="any-non-empty-key",
        node_id="n1",
    )

    store = ls.get_store()
    try:
        # Critical: the silent-swallow was a write-path bug. After the fix
        # the batch is durable in the DLQ table — NOT silently dropped.
        assert store.dlq_count() == 1, "encrypt failure must persist to DLQ"
        rows = store.dlq_list()
        assert rows[0]["fname"] == "sess-2.jsonl"
        assert rows[0]["node_id"] == "n1"
        assert rows[0]["endpoint"] == "/ingest/events"
        # Payload round-trips intact — the replayer needs it.
        payload = json.loads(rows[0]["payload_json"])
        assert payload["session_file"] == "sess-2.jsonl"
        assert payload["events"][0]["id"] == "ev-2"
        # POST must NOT have been attempted (no blob to send).
        assert posted == [], "POST must be skipped when encryption fails"
        # Counter incremented (ops metric).
        assert sync.get_encryption_failure_count() == before + 1
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


# ── Scenario 3: replay on next sync tick drains the DLQ ─────────────────────

def test_dlq_replay_drains_on_next_cycle(tmp_path, monkeypatch):
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    # First call: encryption fails → row parked in DLQ.
    monkeypatch.setattr(sync, "_local_ingest_session_batch", lambda *a, **k: None)
    monkeypatch.setattr(sync, "_post", lambda *a, **k: None)
    monkeypatch.setattr(sync, "encrypt_payload",
                        lambda payload, key: (_ for _ in ()).throw(
                            RuntimeError("transient bad-key window")))

    enc_key = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcd"
    sync._flush_session_batch(
        [{"id": "ev-3", "type": "message"}],
        "sess-3.jsonl",
        api_key="k",
        enc_key=enc_key,
        node_id="n1",
    )
    store = ls.get_store()
    assert store.dlq_count() == 1, "precondition: DLQ has the parked batch"

    # Second call: user rotates the key back / patches the bug.
    # Restore the real encryptor + capture the POST.
    importlib.reload(sync)  # gets real encrypt_payload back
    posted: list[tuple] = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key: posted.append((path, body)))

    replayed = sync._dlq_replay(api_key="k", enc_key=enc_key)
    try:
        assert replayed == 1, f"expected 1 replay, got {replayed}"
        assert store.dlq_count() == 0, "DLQ must be drained after success"
        assert len(posted) == 1
        assert posted[0][0] == "/ingest/events"
        assert posted[0][1]["encrypted"] is True
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass


# ── Scenario 4: DLQ row survives a real daemon restart (subprocess) ─────────

def test_dlq_survives_daemon_restart(tmp_path):
    """End-to-end persistence test using two real Python subprocesses.

    Per ``feedback_synthetic_tests_missed_real_event_shape.md`` — a mocked
    "restart" wouldn't exercise the real DuckDB file path. The whole point
    of moving the DLQ from in-memory to DuckDB is that the row survives
    ``kill -9`` + relaunch. Verify that explicitly."""
    db = tmp_path / "clawmetry.duckdb"

    # Process A: enqueue a DLQ row, then exit.
    write_script = textwrap.dedent(f"""
        import importlib, os, sys
        os.environ['CLAWMETRY_LOCAL_STORE_PATH'] = {str(db)!r}
        os.environ['CLAWMETRY_LOCAL_FLUSH_SECS'] = '0.05'
        sys.path.insert(0, {os.getcwd()!r})
        import clawmetry.local_store as ls
        importlib.reload(ls)
        import clawmetry.sync as sync
        importlib.reload(sync)

        def _boom(payload, key):
            raise RuntimeError('subproc encrypt failure')
        sync.encrypt_payload = _boom
        sync._local_ingest_session_batch = lambda *a, **k: None
        sync._post = lambda *a, **k: None

        sync._flush_session_batch(
            [{{'id': 'ev-restart', 'type': 'message'}}],
            'sess-restart.jsonl',
            api_key='k',
            enc_key='any-non-empty-key',
            node_id='n1',
        )
        store = ls.get_store()
        print('DLQ_DEPTH_A=' + str(store.dlq_count()))
        store.stop(flush=True)
    """)
    a = subprocess.run(
        [sys.executable, "-c", write_script],
        capture_output=True, text=True, timeout=30,
    )
    assert a.returncode == 0, f"write subproc failed: {a.stderr}"
    assert "DLQ_DEPTH_A=1" in a.stdout, f"DLQ not enqueued: {a.stdout}"

    # Process B: open the SAME DuckDB file and read the DLQ.
    read_script = textwrap.dedent(f"""
        import importlib, os, sys
        os.environ['CLAWMETRY_LOCAL_STORE_PATH'] = {str(db)!r}
        sys.path.insert(0, {os.getcwd()!r})
        import clawmetry.local_store as ls
        importlib.reload(ls)
        store = ls.get_store()
        rows = store.dlq_list()
        print('DLQ_DEPTH_B=' + str(store.dlq_count()))
        if rows:
            print('FNAME=' + str(rows[0]['fname']))
            print('ENDPOINT=' + str(rows[0]['endpoint']))
        store.stop(flush=False)
    """)
    b = subprocess.run(
        [sys.executable, "-c", read_script],
        capture_output=True, text=True, timeout=30,
    )
    assert b.returncode == 0, f"read subproc failed: {b.stderr}"
    assert "DLQ_DEPTH_B=1" in b.stdout, (
        f"DLQ did NOT survive daemon restart — out:\n{b.stdout}\nerr:\n{b.stderr}"
    )
    assert "FNAME=sess-restart.jsonl" in b.stdout
    assert "ENDPOINT=/ingest/events" in b.stdout


# ── Bonus: DLQ replayer abandons permanently-poisoned rows ──────────────────

def test_dlq_abandons_after_max_attempts(tmp_path, monkeypatch):
    """If encryption keeps failing (truly corrupt key never rotated back),
    the replayer must NOT spin forever on the same row. After
    ``_DLQ_MAX_ATTEMPTS`` it deletes the row and logs an abandonment.
    Prevents the DLQ from becoming a runaway log spammer."""
    ls = _reload_local_store(tmp_path, monkeypatch)
    sync = _reload_sync(monkeypatch)

    monkeypatch.setattr(sync, "_local_ingest_session_batch", lambda *a, **k: None)
    monkeypatch.setattr(sync, "_post", lambda *a, **k: None)
    monkeypatch.setattr(sync, "encrypt_payload",
                        lambda payload, key: (_ for _ in ()).throw(
                            RuntimeError("permanent corrupt key")))

    # Park one row.
    sync._flush_session_batch(
        [{"id": "ev-abandon", "type": "message"}],
        "sess-abandon.jsonl",
        api_key="k",
        enc_key="any-key",
        node_id="n1",
    )
    store = ls.get_store()
    assert store.dlq_count() == 1

    # Shrink max-attempts so the test runs fast.
    monkeypatch.setattr(sync, "_DLQ_MAX_ATTEMPTS", 2)
    # Three replay cycles: first two bump attempts to 2, third sees
    # attempts>=max and abandons.
    for _ in range(3):
        sync._dlq_replay(api_key="k", enc_key="any-key")

    try:
        assert store.dlq_count() == 0, (
            "abandoned row must be deleted after exceeding max attempts"
        )
    finally:
        try:
            store.stop(flush=False)
        except Exception:
            pass
