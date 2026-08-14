"""Tests for the multi-runtime file-catalog heartbeat cache push.

``_build_runtime_files_cache_pushes`` (clawmetry/sync.py) is what makes the
Memory / Skills file browser real on cloud: it snapshots every present
runtime's memory/skills/commands/agents/hooks files from the
``clawmetry.runtime_memory`` catalog, E2E-encrypts them under
``runtime_files:{owner_hash}:{node}:catalog`` and rides the heartbeat.
Without it the cloud browser is an empty shell (founder: "vaporware").

Covers:
  1. Happy path: present runtime → push entry, key/ttl shape, decrypted
     payload holds groups + inline file contents.
  2. Locked paid runtime → label-only stub (honest upsell, no contents).
  3. Absent runtime → excluded entirely.
  4. No encryption key → no push (never plaintext).
  5. Moat side-effect: the same pass ingests plaintext rows into DuckDB
     ``memory_blobs`` with agent_type=<runtime>, agent_id=<category> —
     and the legacy OpenClaw memory push does NOT pick those rows up.
  6. Throttle: rebuilds are cached for RUNTIME_FILES_REBUILD_SEC.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


FAKE_CATALOG = [
    {"id": "claude_code", "label": "Claude Code", "present": True,
     "counts": {"memory": 1, "skills": 1}, "roots": []},
    {"id": "cursor", "label": "Cursor", "present": True,
     "counts": {"memory": 1}, "roots": []},
    {"id": "codex", "label": "Codex", "present": False,
     "counts": {}, "roots": []},
]

FAKE_LISTINGS = {
    "claude_code": {
        "runtime": "claude_code", "label": "Claude Code",
        "groups": [
            {"category": "memory", "root": "/home/u/.claude/CLAUDE.md",
             "label": "Global CLAUDE.md", "scope": "global", "exists": True,
             "files": [{"path": "", "size": 24, "mtime": 1755000000}]},
            {"category": "skills", "root": "/home/u/.claude/skills",
             "label": "Global skills", "scope": "global", "exists": True,
             "files": [{"path": "review/SKILL.md", "size": 30, "mtime": 1755000001}]},
            {"category": "commands", "root": "/home/u/.claude/commands",
             "label": "Global slash commands", "scope": "global", "exists": False,
             "files": []},
        ],
    },
    "cursor": {
        "runtime": "cursor", "label": "Cursor",
        "groups": [
            {"category": "memory", "root": "/home/u/.cursor/rules",
             "label": "Rules", "scope": "global", "exists": True,
             "files": [{"path": "main.mdc", "size": 12, "mtime": 1755000002}]},
        ],
    },
}

FAKE_CONTENTS = {
    ("/home/u/.claude/CLAUDE.md", ""): "# CLAUDE.md\nglobal memory\n",
    ("/home/u/.claude/skills", "review/SKILL.md"): "# review skill\ndo reviews\n",
    ("/home/u/.cursor/rules", "main.mdc"): "cursor rules\n",
}


@pytest.fixture
def sync_with_fake_catalog(tmp_path, monkeypatch):
    """Reload sync + local_store against a fresh DuckDB and monkeypatch the
    runtime_memory catalog to a deterministic fake (no real disk walk).
    ``cursor`` is made to look entitlement-locked. Yields (sync, config)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # A real daemon on the dev machine would otherwise turn get_store()
    # into a _ProxyStore aimed at the daemon's DB (see test_detectors.py).
    ls.mark_writer_owner()
    import clawmetry.sync as s
    importlib.reload(s)

    import clawmetry.runtime_memory as rm
    monkeypatch.setattr(rm, "list_runtimes", lambda: [dict(r) for r in FAKE_CATALOG])
    monkeypatch.setattr(
        rm, "list_files",
        lambda rt, category=None: FAKE_LISTINGS.get(
            rt, {"runtime": rt, "label": rt, "groups": []}),
    )

    def _fake_read(rt, root, path, max_bytes=100_000):
        content = FAKE_CONTENTS.get((root, path))
        if content is None:
            return {"ok": False, "error": "not a file", "status": 404}
        return {"ok": True, "path": path, "content": content,
                "size": len(content), "mtime": 1755000000,
                "language": "markdown", "binary": False}

    monkeypatch.setattr(rm, "read_runtime_file", _fake_read)
    monkeypatch.setattr(
        s, "_runtime_locked_for_push", lambda rt_id: rt_id == "cursor")
    # Fresh throttle cache per test.
    s._runtime_files_push_cache.update(ts=0.0, pushes=None)

    config = {
        "node_id":        "node-rtf-test",
        "api_key":        "cm_rtf_test_token",
        "encryption_key": s.generate_encryption_key(),
    }
    yield s, config


def _decrypt(s, pushes, config):
    return s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])


def test_push_key_ttl_and_shape(sync_with_fake_catalog):
    s, config = sync_with_fake_catalog
    pushes = s._build_runtime_files_cache_pushes(config)
    assert len(pushes) == 1
    owner_hash = s._owner_hash_for_token(config["api_key"])
    assert pushes[0]["key"] == f"runtime_files:{owner_hash}:node-rtf-test:catalog"
    assert pushes[0]["ttl_s"] == s.RUNTIME_FILES_CACHE_TTL_SEC
    payload = _decrypt(s, pushes, config)
    assert payload["_shape"] == "runtime_files"
    ids = [r["id"] for r in payload["runtimes"]]
    assert "claude_code" in ids
    cc = [r for r in payload["runtimes"] if r["id"] == "claude_code"][0]
    mem = [g for g in cc["groups"] if g["category"] == "memory"][0]
    assert mem["files"][0]["content"] == "# CLAUDE.md\nglobal memory\n"
    skills = [g for g in cc["groups"] if g["category"] == "skills"][0]
    assert skills["files"][0]["path"] == "review/SKILL.md"
    assert "do reviews" in skills["files"][0]["content"]
    # Absent group still listed (exists=False, no files) so the UI can show
    # the "looked here" hint.
    cmds = [g for g in cc["groups"] if g["category"] == "commands"][0]
    assert cmds["exists"] is False and cmds["files"] == []


def test_locked_runtime_is_label_only_stub(sync_with_fake_catalog):
    s, config = sync_with_fake_catalog
    payload = _decrypt(s, s._build_runtime_files_cache_pushes(config), config)
    cur = [r for r in payload["runtimes"] if r["id"] == "cursor"][0]
    assert cur["locked"] is True
    assert cur["groups"] == []
    # No cursor content anywhere in the payload.
    import json
    assert "cursor rules" not in json.dumps(payload)


def test_absent_runtime_excluded(sync_with_fake_catalog):
    s, config = sync_with_fake_catalog
    payload = _decrypt(s, s._build_runtime_files_cache_pushes(config), config)
    assert "codex" not in [r["id"] for r in payload["runtimes"]]


def test_no_encryption_key_no_push(sync_with_fake_catalog):
    s, config = sync_with_fake_catalog
    config = dict(config, encryption_key=None)
    assert s._build_runtime_files_cache_pushes(config) == []


def test_moat_ingest_and_legacy_memory_push_isolation(sync_with_fake_catalog):
    s, config = sync_with_fake_catalog
    s._build_runtime_files_cache_pushes(config)
    from clawmetry import local_store
    store = local_store.get_store()
    rows = store.query_memory_blobs(agent_type="claude_code")
    assert rows, "runtime files must land in memory_blobs (moat)"
    by_id = {r["agent_id"] for r in rows}
    assert by_id <= {"memory", "skills", "commands", "agents", "hooks"}
    # The legacy OpenClaw memory push must not pick these rows up.
    mem_pushes = s._build_memory_cache_pushes(config)
    if mem_pushes:  # empty store for openclaw/main → usually []
        decoded = s.decrypt_payload(mem_pushes[0]["blob"], config["encryption_key"])
        paths = [f["path"] for f in decoded["memory_content"]]
        assert not any("/.claude/" in p for p in paths)


def test_rebuild_throttled(sync_with_fake_catalog, monkeypatch):
    s, config = sync_with_fake_catalog
    first = s._build_runtime_files_cache_pushes(config)
    assert first
    import clawmetry.runtime_memory as rm

    def _boom():
        raise AssertionError("catalog re-walked inside throttle window")

    monkeypatch.setattr(rm, "list_runtimes", _boom)
    second = s._build_runtime_files_cache_pushes(config)
    assert second == first
