"""Tests for the bp_memory routes' local-store fast path.

Mirrors test_sessions_local_fastpath.py — opt-in via
CLAWMETRY_LOCAL_STORE_READ=1; falls through to the legacy filesystem path
when the flag is unset OR the local memory_blobs table is empty.

Routes covered:
  - /api/memory-files (also /api/memory alias) — list memory files
  - /api/file?path=... (GET only — POST writes still go to disk)
  - /api/memory-analytics — aggregate stats with bloat detection

Schema-method coverage:
  - clawmetry.local_store.LocalStore.query_memory_blobs() — newest-first,
    filter by agent_type/agent_id/path_prefix, decoded blob payload.
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app with bp_memory registered, fresh DuckDB per test, fast-path
    flag enabled."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_memory)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def app_no_flag(tmp_path, monkeypatch):
    """Same wiring as ``app`` but with the fast-path flag DELETED so the
    handler must fall through to the filesystem path. WORKSPACE pointed
    at an empty tmp dir so the legacy code returns an empty list rather
    than reading the developer's real ~/.openclaw."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import dashboard as _d
    monkeypatch.setattr(_d, "WORKSPACE", str(tmp_path), raising=False)
    monkeypatch.setattr(_d, "MEMORY_DIR", str(tmp_path / "memory"), raising=False)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_memory)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed_blob(store, path: str, content: str = "hello world\n",
               agent_type: str = "openclaw", agent_id: str = "main",
               ts: str = "2026-05-12T10:00:00+00:00") -> None:
    """Seed one memory_blobs row. Default content/timestamp keeps tests
    terse — pass overrides where the test cares."""
    store.ingest_memory_blob({
        "agent_type": agent_type,
        "agent_id": agent_id,
        "path": path,
        "blob": content,
        "ts": ts,
    })


# ── /api/memory-files (and /api/memory alias) ──────────────────────────────


def test_memory_files_fast_path_returns_local_rows(app):
    a, ls = app
    store = ls.get_store()
    _seed_blob(store, "MEMORY.md", "vivek's memory\n")
    _seed_blob(store, "SOUL.md", "i am claude\n")
    _seed_blob(store, "memory/2026-05-12.md", "today's notes\n" * 10)

    body = a.test_client().get("/api/memory-files").get_json()
    assert body.get("_source") == "local_store"
    paths = {f["path"] for f in body["files"]}
    assert paths == {"MEMORY.md", "SOUL.md", "memory/2026-05-12.md"}
    by_path = {f["path"]: f for f in body["files"]}
    # size = byte length of the seeded blob
    assert by_path["MEMORY.md"]["size"] == len("vivek's memory\n".encode("utf-8"))
    assert by_path["memory/2026-05-12.md"]["size"] == len(("today's notes\n" * 10).encode("utf-8"))


def test_memory_alias_route_also_fast_paths(app):
    """/api/memory is documented as an alias of /api/memory-files."""
    a, ls = app
    _seed_blob(ls.get_store(), "AGENTS.md")
    body = a.test_client().get("/api/memory").get_json()
    assert body.get("_source") == "local_store"
    assert {f["path"] for f in body["files"]} == {"AGENTS.md"}


def test_memory_files_disabled_without_flag(app_no_flag):
    """Flag unset → no fast path even if writes would land in the store.
    Falls through to the filesystem helper, but the response is still
    wrapped in the ``{files: [...]}`` envelope so the on-the-wire shape is
    stable across both paths (refs #1763 — keystone E2E verifier expects
    a dict, not the bare list the legacy helper used to return)."""
    a, _ls = app_no_flag
    body = a.test_client().get("/api/memory-files").get_json()
    assert isinstance(body, dict), f"expected dict envelope, got {type(body).__name__}"
    assert body.get("_source") != "local_store"
    assert isinstance(body.get("files"), list)


# ── /api/file (GET) ────────────────────────────────────────────────────────


def test_file_get_fast_path_returns_local_content(app):
    a, ls = app
    _seed_blob(ls.get_store(), "MEMORY.md", "the answer is 42\n",
               ts="2026-05-12T10:00:00+00:00")

    body = a.test_client().get("/api/file?path=MEMORY.md").get_json()
    assert body.get("_source") == "local_store"
    assert body["path"] == "MEMORY.md"
    assert body["content"] == "the answer is 42\n"
    assert body["size"] == len("the answer is 42\n".encode("utf-8"))
    # mtime should be epoch seconds parsed from the ISO ts
    assert body["mtime"] > 0


def test_file_get_fast_path_misses_when_path_not_in_store(app, tmp_path, monkeypatch):
    """Local store has SOUL.md but not USER.md → fast path returns None →
    falls through to filesystem path. With WORKSPACE pointed at an empty
    tmp dir we expect a 404 (not a misdirected 200)."""
    a, ls = app
    _seed_blob(ls.get_store(), "SOUL.md")
    import dashboard as _d
    monkeypatch.setattr(_d, "WORKSPACE", str(tmp_path), raising=False)

    r = a.test_client().get("/api/file?path=USER.md")
    assert r.status_code == 404


def test_file_get_disabled_without_flag(app_no_flag, tmp_path):
    """Flag unset → fast path never runs; even with a populated store,
    the handler reads filesystem (which is empty here → 404)."""
    a, ls = app_no_flag
    _seed_blob(ls.get_store(), "MEMORY.md", "should-not-be-served")
    r = a.test_client().get("/api/file?path=MEMORY.md")
    # Fell through to filesystem — empty WORKSPACE → 404 not 200 with body.
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"


# ── /api/memory-analytics ──────────────────────────────────────────────────


def test_memory_analytics_fast_path_uses_local_blobs(app):
    a, ls = app
    store = ls.get_store()
    # 3 root files + 2 daily files; one of the daily files is bloated
    _seed_blob(store, "MEMORY.md", "x" * 100)
    _seed_blob(store, "SOUL.md", "x" * 200)
    _seed_blob(store, "AGENTS.md", "x" * 50)
    _seed_blob(store, "memory/2026-05-11.md", "y" * 9_000)   # > 8KB warn
    _seed_blob(store, "memory/2026-05-12.md", "z" * 17_000)  # > 16KB crit

    body = a.test_client().get("/api/memory-analytics").get_json()
    assert body.get("_source") == "local_store"
    assert body["fileCount"] == 5
    assert body["rootFileCount"] == 3
    assert body["dailyFileCount"] == 2
    assert body["totalBytes"] == 100 + 200 + 50 + 9_000 + 17_000
    # Bloat detection should have flagged the >16KB daily file
    assert body["hasBloat"] is True
    assert body["hasWarnings"] is True
    crit_files = [r["file"] for r in body["recommendations"]
                  if r["severity"] == "critical"]
    assert "memory/2026-05-12.md" in crit_files
    # Daily growth bucketed by date
    growth_dates = {g["date"] for g in body["dailyGrowth"]}
    assert growth_dates == {"2026-05-11", "2026-05-12"}
    # Context budgets present for all three model sizes
    assert set(body["contextBudgets"].keys()) == {
        "claude_200k", "gpt4_128k", "gemini_1m",
    }


def test_memory_analytics_threshold_overrides_via_querystring(app):
    """warn_kb / crit_kb querystring args must still flow through the
    fast path — the analytics builder doesn't care which source fed it."""
    a, ls = app
    _seed_blob(ls.get_store(), "tiny.md", "x" * 600)
    body = a.test_client().get(
        "/api/memory-analytics?warn_kb=0&crit_kb=1"
    ).get_json()
    assert body.get("_source") == "local_store"
    assert body["thresholds"] == {"warnKB": 0, "critKB": 1}
    assert body["hasWarnings"] is True


def test_memory_analytics_disabled_without_flag(app_no_flag):
    """Flag unset → falls through to filesystem path (which sees an empty
    workspace and returns zero files). Confirm no `_source` tag."""
    a, _ls = app_no_flag
    body = a.test_client().get("/api/memory-analytics").get_json()
    assert body.get("_source") != "local_store"
    assert body["fileCount"] == 0


# ── direct LocalStore.query_memory_blobs() coverage ────────────────────────


@pytest.fixture
def store(tmp_path, monkeypatch):
    """Fresh isolated DuckDB per test for direct query_memory_blobs() tests
    (no Flask wiring)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=False)


def test_query_memory_blobs_round_trip(store):
    store.ingest_memory_blob({
        "agent_type": "openclaw",
        "path": "MEMORY.md",
        "blob": "the moat mandate\n",
        "ts": "2026-05-12T10:00:00+00:00",
    })
    rows = store.query_memory_blobs()
    assert len(rows) == 1
    r = rows[0]
    assert r["agent_type"] == "openclaw"
    assert r["agent_id"] == "main"  # default
    assert r["path"] == "MEMORY.md"
    # blob decoded back to UTF-8 string
    assert r["blob"] == "the moat mandate\n"
    assert r["sha256"]
    assert r["size_bytes"] == len("the moat mandate\n".encode("utf-8"))
    assert r["updated_at"] > 0


def test_query_memory_blobs_newest_first(store):
    """Sort order: most-recently-updated first. Mirrors query_subagents /
    query_crons / query_heartbeats."""
    import time as _t
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "a.md", "blob": "first"})
    _t.sleep(0.01)
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "b.md", "blob": "second"})
    _t.sleep(0.01)
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "c.md", "blob": "third"})
    rows = store.query_memory_blobs()
    assert [r["path"] for r in rows] == ["c.md", "b.md", "a.md"]


def test_query_memory_blobs_filter_by_agent_type(store):
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "MEMORY.md", "blob": "oc"})
    store.ingest_memory_blob({"agent_type": "claude_code", "path": "CLAUDE.md", "blob": "cc"})
    oc = store.query_memory_blobs(agent_type="openclaw")
    cc = store.query_memory_blobs(agent_type="claude_code")
    assert {r["path"] for r in oc} == {"MEMORY.md"}
    assert {r["path"] for r in cc} == {"CLAUDE.md"}


def test_query_memory_blobs_filter_by_path_prefix(store):
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "MEMORY.md", "blob": "x"})
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "memory/2026-05-11.md", "blob": "y"})
    store.ingest_memory_blob({"agent_type": "openclaw", "path": "memory/2026-05-12.md", "blob": "z"})
    daily = store.query_memory_blobs(path_prefix="memory/")
    assert {r["path"] for r in daily} == {
        "memory/2026-05-11.md", "memory/2026-05-12.md",
    }


def test_query_memory_blobs_limit(store):
    for i in range(10):
        store.ingest_memory_blob({
            "agent_type": "openclaw", "path": f"p{i}.md", "blob": "x",
        })
    assert len(store.query_memory_blobs(limit=3)) == 3
