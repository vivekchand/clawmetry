"""Tests for Phase 2 of the heartbeat-piggyback relay (epic #1032).

The OSS daemon proactively pushes the top-50 brain events to the cloud cache
on every heartbeat so the cloud Brain page paints in <100ms (cache hit) on
first load instead of waiting for a /api/cloud/subscribe round-trip.

These tests cover:
  1. Happy path: 50 seeded events → `cache_pushes` array with one entry,
     correct key shape, ttl=21600, encrypted blob is bytes-like (str of
     base64url ciphertext from `encrypt_payload`).
  2. Empty store: no events → no `cache_pushes` key in the heartbeat payload.
  3. Missing encryption key: blob would leak plaintext → no push.
  4. Round-trip: blob decrypts back to the brain-history shape so the cloud
     read path gets the same dict the OSS dashboard would render.
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


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def sync_with_seeded_events(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` + `clawmetry.local_store` against a fresh
    DuckDB seeded with 50 brain events. Yields (sync_module, config)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    store = ls.get_store()
    for i in range(50):
        store.ingest({
            "id":           str(uuid.uuid4()),
            "node_id":      "agent+test",
            "agent_id":     "main",
            "session_id":   f"sess-{i % 3}",
            "event_type":   "message",
            "ts":           f"2026-05-12T10:{i:02d}:00+00:00",
            "data":         {"text": f"hello world {i}"},
            "cost_usd":     0.001,
            "token_count":  42,
            "model":        "claude-opus-4-7",
        })

    # Wait for the background flusher.
    import time
    for _ in range(80):
        if store.health()["ring_depth"] == 0:
            break
        time.sleep(0.05)

    config = {
        "node_id":         "node-test",
        "api_key":         "cm_test_token_xyz",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def sync_with_empty_store(tmp_path, monkeypatch):
    """Same as above but no seeded events — covers the "fresh install"
    degenerate case where there's nothing to push yet."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    config = {
        "node_id":         "node-empty",
        "api_key":         "cm_test_token_xyz",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. happy path: 50 events → 1 cache_push entry ───────────────────────────


def test_build_brain_cache_pushes_returns_one_entry(sync_with_seeded_events):
    s, config = sync_with_seeded_events
    pushes = s._build_brain_cache_pushes(config)

    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]

    # Key shape: brain:{owner_hash}:{node}:recent
    expected_owner = s._owner_hash_for_token(config["api_key"])
    assert entry["key"] == f"brain:{expected_owner}:node-test:recent"

    assert entry["ttl_s"] == s.BRAIN_CACHE_TTL_SEC == 21600

    # Blob is the encrypted payload — a base64url-encoded string of
    # nonce||ciphertext. Must be non-empty and not contain plaintext markers
    # from the seeded events ("hello world" / "sess-").
    blob = entry["blob"]
    assert isinstance(blob, str)
    assert len(blob) > 0
    assert "hello world" not in blob
    assert "sess-" not in blob


# ── 2. empty store: no push (heartbeat payload won't carry the key) ─────────


def test_build_brain_cache_pushes_empty_store_returns_empty(sync_with_empty_store):
    s, config = sync_with_empty_store
    pushes = s._build_brain_cache_pushes(config)
    assert pushes == [], "empty local store must produce no cache_pushes"


def test_send_heartbeat_omits_cache_pushes_when_empty(sync_with_empty_store, monkeypatch):
    """End-to-end: send_heartbeat with an empty store must NOT include
    `cache_pushes` in the request payload (or include an empty list — either
    way the cloud's iteration is a no-op)."""
    s, config = sync_with_empty_store
    captured = {}

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured["payload"] = payload
            return {"sync_allowed": True, "pending_queries": []}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    assert s.send_heartbeat(config) is True
    payload = captured["payload"]
    # Either omitted entirely or present-but-empty are both acceptable
    # (cloud iteration is a no-op on []). Default to "omitted" for cleaner
    # wire format.
    pushes = payload.get("cache_pushes", [])
    assert pushes == [] or "cache_pushes" not in payload


# ── 3. missing encryption key: never push plaintext ─────────────────────────


def test_no_encryption_key_no_push(sync_with_seeded_events):
    s, config = sync_with_seeded_events
    config_no_key = dict(config)
    config_no_key["encryption_key"] = None
    pushes = s._build_brain_cache_pushes(config_no_key)
    assert pushes == [], "must not push when encryption key is unset"


# ── 4. round-trip: blob decrypts back to the brain-history shape ────────────


def test_pushed_blob_decrypts_to_brain_history_shape(sync_with_seeded_events):
    s, config = sync_with_seeded_events
    pushes = s._build_brain_cache_pushes(config)
    assert len(pushes) == 1

    decoded = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    assert isinstance(decoded, dict)
    assert decoded["_shape"] == "brain_history"
    assert decoded["_source"] == "local_store"
    assert "events" in decoded
    assert decoded["count"] == len(decoded["events"])
    # We seeded 50 events; the push should carry exactly that.
    assert decoded["count"] == 50

    # Each event must carry the dashboard-expected shape
    # (time/type/detail/src/sessionId/...).
    sample = decoded["events"][0]
    for k in ("time", "type", "detail", "src", "sessionId", "agentId",
              "tokens", "cost", "model"):
        assert k in sample, f"event missing key {k!r}"
    # Type came from event_type=message (uppercased).
    assert sample["type"] == "MESSAGE"


# ── 5. send_heartbeat wires the push into the request payload ───────────────


def test_send_heartbeat_attaches_cache_pushes(sync_with_seeded_events, monkeypatch):
    s, config = sync_with_seeded_events
    captured = {}

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured["payload"] = payload
            return {"sync_allowed": True, "pending_queries": []}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    assert s.send_heartbeat(config) is True
    payload = captured["payload"]
    assert "cache_pushes" in payload
    assert len(payload["cache_pushes"]) == 1
    entry = payload["cache_pushes"][0]
    assert entry["key"].startswith("brain:") and entry["key"].endswith(":node-test:recent")
    assert entry["ttl_s"] == 21600
    assert isinstance(entry["blob"], str) and len(entry["blob"]) > 0
