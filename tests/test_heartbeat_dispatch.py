"""Tests for heartbeat-piggyback query dispatch (relay-v2 phase 1, #1053).

The cloud may attach `pending_queries` to its `/ingest/heartbeat` response.
For each request the daemon runs the named shape against the local DuckDB,
encrypts the result, and POSTs it back to `/ingest/cache` so the cloud-side
dashboard can serve future requests warm.

These tests mock `clawmetry.sync._post` to intercept HTTP and seed a tmp
DuckDB with a few events so the dispatcher has real rows to return.
"""
from __future__ import annotations

import importlib
import os
import sys
import uuid

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def sync_with_store(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` + `clawmetry.local_store` against a fresh
    DuckDB seeded with a handful of events. Yields (sync_module, config)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    # Fresh imports so the module-level _TRIAL_STATE / store singleton reset.
    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)
    sys.modules.pop("routes.local_query", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    # Seed a few events so query_events / query_sessions return real rows.
    store = ls.get_store()
    for i in range(3):
        store.ingest({
            "id": str(uuid.uuid4()),
            "node_id": "agent+test",
            "agent_id": "main",
            "session_id": "sess-A",
            "event_type": "tool_call",
            "ts": f"2026-05-1{i+1}T10:00:00+00:00",
            "data": {"tool": "Bash"},
            "cost_usd": 0.001,
            "token_count": 12,
            "model": "claude-opus-4-7",
        })
    # Wait for the background flusher to drain the ring buffer so
    # subsequent queries see the seed rows.
    import time
    for _ in range(80):
        if store.health()["ring_depth"] == 0:
            break
        time.sleep(0.05)

    config = {
        "node_id":         "node-test",
        "api_key":         "cm_test",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _hb_response(pending):
    return {"sync_allowed": True, "pending_queries": pending}


# ── 1. happy path: 2 pending queries → 2 cache POSTs ────────────────────────

def test_pending_queries_dispatched(sync_with_store, monkeypatch):
    s, config = sync_with_store
    cache_posts = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            return _hb_response([
                {"id": "q1", "shape": "events",   "args": {"limit": 10},
                 "cache_key": "events:limit=10"},
                {"id": "q2", "shape": "sessions", "args": {"limit": 5},
                 "cache_key": "sessions:limit=5"},
            ])
        if path == "/ingest/cache":
            cache_posts.append(payload)
            return {}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    ok = s.send_heartbeat(config)
    assert ok is True
    assert len(cache_posts) == 2
    ids = {p["id"] for p in cache_posts}
    assert ids == {"q1", "q2"}
    for p in cache_posts:
        assert p["node_id"] == "node-test"
        assert p["ttl"] == 3600
        assert p["shape"] in {"events", "sessions"}
        assert isinstance(p["blob"], str) and len(p["blob"]) > 0
        assert isinstance(p["args_hash"], str) and len(p["args_hash"]) == 64
        # Blob is opaque ciphertext — must NOT contain plaintext markers.
        assert "Bash" not in p["blob"]
        assert "sess-A" not in p["blob"]


# ── 2. unknown shape silently skipped ───────────────────────────────────────

def test_unknown_shape_skipped(sync_with_store, monkeypatch):
    s, config = sync_with_store
    cache_posts = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            return _hb_response([
                {"id": "evil", "shape": "evil_shape",
                 "args": {"q": "DROP TABLE"}, "cache_key": "evil"},
            ])
        if path == "/ingest/cache":
            cache_posts.append(payload)
            return {}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    ok = s.send_heartbeat(config)
    assert ok is True
    assert cache_posts == [], "evil_shape must be filtered before dispatch"


# ── 3. one bad query doesn't kill the rest ──────────────────────────────────

def test_dispatch_failure_doesnt_block_others(sync_with_store, monkeypatch):
    s, config = sync_with_store
    cache_posts = []

    # Make the first query blow up inside _local_dispatch; the second must
    # still POST to /ingest/cache.
    real_dispatch = s._local_dispatch_fallback
    call_count = {"n": 0}

    def boom_then_real(shape, args):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise RuntimeError("synthetic dispatch failure")
        return real_dispatch(shape, args)

    # Force the fallback path (skips routes.local_query) so we can intercept.
    monkeypatch.setattr(s, "_local_dispatch_fallback", boom_then_real)
    # Also break the routes import path so the daemon falls through to the
    # fallback dispatcher.
    sys.modules["routes.local_query"] = None  # type: ignore

    try:
        def fake_post(path, payload, api_key, timeout=45):
            if path == "/ingest/heartbeat":
                return _hb_response([
                    {"id": "boom", "shape": "events",   "args": {},
                     "cache_key": "boom"},
                    {"id": "ok",   "shape": "sessions", "args": {},
                     "cache_key": "ok"},
                ])
            if path == "/ingest/cache":
                cache_posts.append(payload)
                return {}
            raise AssertionError(f"unexpected path {path}")

        monkeypatch.setattr(s, "_post", fake_post)
        monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

        ok = s.send_heartbeat(config)
        assert ok is True
        assert len(cache_posts) == 1
        assert cache_posts[0]["id"] == "ok"
    finally:
        sys.modules.pop("routes.local_query", None)


# ── 4. no pending → no cache posts ──────────────────────────────────────────

def test_no_pending_means_no_extra_posts(sync_with_store, monkeypatch):
    s, config = sync_with_store
    cache_posts = []

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            return _hb_response([])
        if path == "/ingest/cache":
            cache_posts.append(payload)
            return {}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    ok = s.send_heartbeat(config)
    assert ok is True
    assert cache_posts == []


# ── 5. encrypt → decrypt round-trip preserves rows ──────────────────────────

def test_encrypted_blob_decrypts_to_original(sync_with_store, monkeypatch):
    s, config = sync_with_store
    captured = {}

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            return _hb_response([
                {"id": "q1", "shape": "events", "args": {"limit": 50},
                 "cache_key": "events:50"},
            ])
        if path == "/ingest/cache":
            captured["payload"] = payload
            return {}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    ok = s.send_heartbeat(config)
    assert ok is True
    assert "payload" in captured

    blob = captured["payload"]["blob"]
    decoded = s.decrypt_payload(blob, config["encryption_key"])
    assert isinstance(decoded, dict)
    assert "rows" in decoded
    assert decoded["count"] == len(decoded["rows"])
    # The seeded events should be present in the decrypted payload.
    assert decoded["count"] >= 1
    sessions = {r.get("session_id") for r in decoded["rows"]}
    assert "sess-A" in sessions
