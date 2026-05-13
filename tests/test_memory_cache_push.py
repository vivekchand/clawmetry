"""Tests for the memory-file heartbeat-piggyback cache push (Memory tab fix).

The OSS daemon proactively pushes the user's memory-file snapshot to the
cloud cache on every heartbeat so the cloud Node Detail → Memory tab paints
from cache. Before this push existed, the cloud handler always returned
``{blob: None}`` and the browser rendered "No memory data synced" even
though the local agent had SOUL.md / USER.md / AGENTS.md etc.

These tests cover:
  1. Happy path: seeded memory_blobs rows → ``cache_pushes`` array with one
     entry, key shape ``memory:{owner_hash}:{node}:files``, ttl=21600,
     encrypted blob (no plaintext leak).
  2. Empty store: no rows → no push (cache_pushes omitted / empty).
  3. Missing encryption key: never push plaintext.
  4. Round-trip: decrypt → ``{memory_state.files, memory_content}`` shape
     that the cloud Memory IDE JS reads in ``_renderIDE`` / ``_selectFile``.
  5. send_heartbeat wires the push into the outgoing request payload.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def sync_with_seeded_memory(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` + `clawmetry.local_store` against a fresh
    DuckDB seeded with the canonical memory files the user reports seeing
    locally (SOUL.md, USER.md, AGENTS.md, IDENTITY.md, TOOLS.md, HEARTBEAT.md).
    Yields (sync_module, config, seeded_paths)."""
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
    seeded = {
        "SOUL.md":      "# Soul\nThe core of the agent.\n",
        "USER.md":      "# User\nvivek@clawmetry.com\n",
        "AGENTS.md":    "# Agents\nmain, subagent, cron\n" * 50,
        "IDENTITY.md":  "# Identity\nopenclaw-main\n",
        "TOOLS.md":     "# Tools\nbash, edit, read\n",
        "HEARTBEAT.md": "# Heartbeat\n2026-05-13T10:00:00Z\n",
    }
    for path, blob in seeded.items():
        store.ingest_memory_blob({
            "agent_type": "openclaw",
            "path":       path,
            "blob":       blob,
            "ts":         "2026-05-13T10:00:00+00:00",
        })

    config = {
        "node_id":         "node-mem-test",
        "api_key":         "cm_mem_test_token",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config, seeded

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def sync_with_empty_memory(tmp_path, monkeypatch):
    """Fresh DuckDB with no memory_blobs rows — fresh-install case."""
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
        "api_key":         "cm_mem_test_token",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. happy path: seeded rows → one cache_push entry ──────────────────────


def test_build_memory_cache_pushes_returns_one_entry(sync_with_seeded_memory):
    s, config, seeded = sync_with_seeded_memory
    pushes = s._build_memory_cache_pushes(config)

    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]

    # Key shape: memory:{owner_hash}:{node}:files — must include
    # owner_hash so cloud-side _accept_cache_pushes accepts it (owner-hash
    # binding check) AND must include node_id so the cloud read endpoint
    # picks the right node's snapshot.
    expected_owner = s._owner_hash_for_token(config["api_key"])
    assert entry["key"] == f"memory:{expected_owner}:node-mem-test:files"

    assert entry["ttl_s"] == s.MEMORY_CACHE_TTL_SEC == 21600

    # Encrypted blob: base64url string, plaintext markers absent.
    blob = entry["blob"]
    assert isinstance(blob, str) and len(blob) > 0
    assert "SOUL" not in blob
    assert "vivek@clawmetry.com" not in blob


# ── 2. empty store: no push ────────────────────────────────────────────────


def test_build_memory_cache_pushes_empty_store_returns_empty(sync_with_empty_memory):
    s, config = sync_with_empty_memory
    pushes = s._build_memory_cache_pushes(config)
    assert pushes == [], "empty memory_blobs table must produce no cache_pushes"


# ── 3. missing encryption key: never push plaintext ────────────────────────


def test_no_encryption_key_no_push(sync_with_seeded_memory):
    s, config, _ = sync_with_seeded_memory
    cfg_no_key = dict(config)
    cfg_no_key["encryption_key"] = None
    pushes = s._build_memory_cache_pushes(cfg_no_key)
    assert pushes == [], "must not push when encryption key is unset"


# ── 4. round-trip: blob decrypts to the memory_files browser shape ─────────


def test_pushed_blob_decrypts_to_memory_files_shape(sync_with_seeded_memory):
    s, config, seeded = sync_with_seeded_memory
    pushes = s._build_memory_cache_pushes(config)
    assert len(pushes) == 1

    decoded = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    assert isinstance(decoded, dict)
    assert decoded["_shape"] == "memory_files"
    assert decoded["_source"] == "local_store"

    # Shape the cloud Memory IDE JS reads in _renderIDE / _selectFile:
    #   data.memory_state.files  → [{name, size}, ...]
    #   data.memory_content      → [{path, content}, ...]
    assert "memory_state" in decoded and "files" in decoded["memory_state"]
    files = decoded["memory_state"]["files"]
    contents = decoded.get("memory_content") or []

    seen_paths = {f["name"] for f in files}
    assert seen_paths == set(seeded.keys()), (
        "every seeded memory file must appear in memory_state.files"
    )
    # size_bytes round-trip (UTF-8 byte length of original content)
    size_by_name = {f["name"]: f["size"] for f in files}
    for path, blob in seeded.items():
        assert size_by_name[path] == len(blob.encode("utf-8"))

    # Content round-trip — pick a small file (SOUL.md) and verify byte-exact.
    soul = next(c for c in contents if c["path"] == "SOUL.md")
    assert soul["content"] == seeded["SOUL.md"]


# ── 5. send_heartbeat attaches the memory push to the outgoing payload ─────


def test_send_heartbeat_attaches_memory_cache_pushes(sync_with_seeded_memory, monkeypatch):
    """End-to-end: the memory push must arrive in the `/ingest/heartbeat`
    POST body so the cloud's _accept_cache_pushes can write it to Redis."""
    s, config, _ = sync_with_seeded_memory
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
    pushes = payload.get("cache_pushes", [])

    mem_entries = [p for p in pushes
                   if isinstance(p, dict)
                   and p.get("key", "").startswith("memory:")
                   and p.get("key", "").endswith(":node-mem-test:files")]
    assert len(mem_entries) == 1, (
        "memory cache_push must land in the heartbeat payload alongside any "
        "brain/alert/approvals pushes"
    )
    entry = mem_entries[0]
    assert entry["ttl_s"] == s.MEMORY_CACHE_TTL_SEC
    assert isinstance(entry["blob"], str) and len(entry["blob"]) > 0
