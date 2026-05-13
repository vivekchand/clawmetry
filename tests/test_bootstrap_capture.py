"""Tests for the "First Contact" BOOTSTRAP.md capture (issue #690).

Three surfaces:
  1. DuckDB schema — ``bootstrap_archive`` is reachable via
     ``ingest_bootstrap_archive`` + ``query_bootstrap_archive``. Round-trip,
     dedup, and re-capture-on-content-change semantics.
  2. Capture helper — ``clawmetry.sync.capture_bootstrap_if_present`` finds
     BOOTSTRAP.md under the configured workspace, snapshots it into DuckDB,
     and no-ops on a re-tick. A subsequent edit of the file results in a NEW
     row (preserving the full first-contact history when OpenClaw
     re-negotiates).
  3. HTTP routes — ``GET /api/bootstrap`` returns 404 when empty and 200
     with a summary list once a snapshot exists; ``GET /api/bootstrap/main``
     returns the full content row.
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
def fresh_store(tmp_path, monkeypatch):
    """Reload `clawmetry.local_store` against a fresh DuckDB file. Yields
    (module, store); closes on teardown."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)

    store = ls.get_store()
    yield ls, store

    try:
        store.stop(flush=False)
    except Exception:
        pass


@pytest.fixture
def fake_openclaw_workspace(tmp_path, monkeypatch):
    """Build a fake ~/.openclaw layout with a BOOTSTRAP.md present at the
    documented `agents/main/memory/BOOTSTRAP.md` location. Returns the path
    to the file so tests can mutate / delete it."""
    oc_dir = tmp_path / "openclaw"
    memory_dir = oc_dir / "agents" / "main" / "memory"
    memory_dir.mkdir(parents=True)
    bootstrap = memory_dir / "BOOTSTRAP.md"
    bootstrap.write_text(
        "# First Contact\n\n"
        "Hello, agent. You are OpenClaw. Negotiating identity…\n"
    )
    # `sync._get_openclaw_dir()` reads this env var.
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(oc_dir))
    # Also seed a session JSONL so the capture links a first_session_id.
    sessions_dir = oc_dir / "agents" / "main" / "sessions"
    sessions_dir.mkdir(parents=True)
    (sessions_dir / "sess-12345.jsonl").write_text('{"type":"start"}\n')
    return bootstrap


# ── 1. Schema round-trip ───────────────────────────────────────────────────


def test_ingest_and_query_bootstrap_round_trip(fresh_store):
    ls, store = fresh_store
    row = {
        "node_id": "node-1",
        "agent_id": "main",
        "content": "# BOOTSTRAP\n\nidentity payload",
        "first_session_id": "sess-abc",
        "source_path": "/fake/path/BOOTSTRAP.md",
    }
    wrote = store.ingest_bootstrap_archive(row)
    assert wrote is True

    rows = store.query_bootstrap_archive(node_id="node-1")
    assert len(rows) == 1
    r = rows[0]
    assert r["node_id"] == "node-1"
    assert r["agent_id"] == "main"
    assert r["content"].startswith("# BOOTSTRAP")
    assert r["first_session_id"] == "sess-abc"
    assert r["source_path"] == "/fake/path/BOOTSTRAP.md"
    assert r["content_sha256"]  # auto-computed
    assert r["size_bytes"] == len(row["content"].encode("utf-8"))
    assert r["captured_at"]  # auto-filled


def test_ingest_bootstrap_dedups_same_content(fresh_store):
    """Re-capturing the same content for the same (node, agent) is a no-op."""
    ls, store = fresh_store
    payload = {
        "node_id": "node-1",
        "agent_id": "main",
        "content": "# BOOTSTRAP\nv1",
    }
    assert store.ingest_bootstrap_archive(payload) is True
    # Second call with identical content — should NOT write a new row.
    assert store.ingest_bootstrap_archive(payload) is False
    assert len(store.query_bootstrap_archive(node_id="node-1")) == 1


def test_ingest_bootstrap_new_row_on_content_change(fresh_store):
    """A different content (e.g. OpenClaw rewrote BOOTSTRAP.md after re-init)
    yields a NEW row — preserving the full first-contact history."""
    ls, store = fresh_store
    base = {"node_id": "node-1", "agent_id": "main"}
    assert store.ingest_bootstrap_archive({**base, "content": "v1 body"}) is True
    assert store.ingest_bootstrap_archive({**base, "content": "v2 body"}) is True

    rows = store.query_bootstrap_archive(node_id="node-1")
    assert len(rows) == 2
    bodies = sorted(r["content"] for r in rows)
    assert bodies == ["v1 body", "v2 body"]


def test_query_filters_by_agent_id(fresh_store):
    ls, store = fresh_store
    store.ingest_bootstrap_archive({
        "node_id": "node-1", "agent_id": "main", "content": "A",
    })
    store.ingest_bootstrap_archive({
        "node_id": "node-1", "agent_id": "subagent-7", "content": "B",
    })
    main_only = store.query_bootstrap_archive(
        node_id="node-1", agent_id="main",
    )
    assert len(main_only) == 1
    assert main_only[0]["content"] == "A"


def test_ingest_requires_node_id_and_content(fresh_store):
    ls, store = fresh_store
    with pytest.raises(ValueError):
        store.ingest_bootstrap_archive({"agent_id": "main", "content": "x"})
    with pytest.raises(ValueError):
        store.ingest_bootstrap_archive({"node_id": "n", "agent_id": "main"})


# ── 2. Capture helper ──────────────────────────────────────────────────────


def test_capture_writes_to_store_when_bootstrap_present(
    fresh_store, fake_openclaw_workspace, monkeypatch,
):
    """End-to-end: BOOTSTRAP.md exists on disk → capture helper finds it,
    reads it, persists it to the local store."""
    ls, store = fresh_store
    # Make sync.py see this test's reloaded local_store module too. The
    # capture helper does ``from clawmetry import local_store`` internally,
    # which goes through the reloaded module via sys.modules.
    sys.modules["clawmetry.local_store"] = ls

    import clawmetry.sync as sync
    importlib.reload(sync)
    # After reload `sync.capture_bootstrap_if_present` will resolve the
    # patched _get_openclaw_dir via the monkeypatched env var.

    config = {"node_id": "node-test"}
    wrote = sync.capture_bootstrap_if_present(config, paths={}, store=store)
    assert wrote is True

    rows = store.query_bootstrap_archive(node_id="node-test")
    assert len(rows) == 1
    r = rows[0]
    assert "First Contact" in r["content"]
    assert r["source_path"].endswith("BOOTSTRAP.md")
    # We seeded one session JSONL — the helper should link it.
    assert r["first_session_id"] == "sess-12345"


def test_capture_is_noop_when_bootstrap_absent(fresh_store, tmp_path, monkeypatch):
    """No BOOTSTRAP.md on disk → helper returns False, store stays empty."""
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls

    # Point at a directory that has no BOOTSTRAP.md anywhere.
    monkeypatch.setenv("CLAWMETRY_OPENCLAW_DIR", str(tmp_path / "empty-oc"))
    import clawmetry.sync as sync
    importlib.reload(sync)

    config = {"node_id": "node-test"}
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is False
    assert store.query_bootstrap_archive(node_id="node-test") == []


def test_capture_dedups_on_second_tick(
    fresh_store, fake_openclaw_workspace, monkeypatch,
):
    """First tick captures; second tick on unchanged file is a no-op."""
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls
    import clawmetry.sync as sync
    importlib.reload(sync)

    config = {"node_id": "node-test"}
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is True
    # Second tick — same file content.
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is False
    assert len(store.query_bootstrap_archive(node_id="node-test")) == 1


def test_capture_reruns_on_content_change(
    fresh_store, fake_openclaw_workspace, monkeypatch,
):
    """Simulate OpenClaw deleting + re-creating BOOTSTRAP.md with new content
    (re-negotiated identity). Capture helper writes a SECOND row."""
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls
    import clawmetry.sync as sync
    importlib.reload(sync)

    config = {"node_id": "node-test"}
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is True

    # Mimic the self-delete + rewrite cycle.
    fake_openclaw_workspace.unlink()
    fake_openclaw_workspace.write_text(
        "# First Contact (v2)\n\nAgent re-bootstrapped after reset.\n"
    )
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is True
    rows = store.query_bootstrap_archive(node_id="node-test")
    assert len(rows) == 2


def test_capture_skips_without_node_id(fresh_store, fake_openclaw_workspace):
    """No node_id in config → helper short-circuits (can't dedup without it)."""
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls
    import clawmetry.sync as sync
    importlib.reload(sync)

    assert sync.capture_bootstrap_if_present({}, paths={}, store=store) is False


def test_capture_skips_empty_file(fresh_store, fake_openclaw_workspace, monkeypatch):
    """Empty / whitespace-only BOOTSTRAP.md is meaningless — wait for content."""
    fake_openclaw_workspace.write_text("   \n  \n")
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls
    import clawmetry.sync as sync
    importlib.reload(sync)

    config = {"node_id": "node-test"}
    assert sync.capture_bootstrap_if_present(config, paths={}, store=store) is False
    assert store.query_bootstrap_archive(node_id="node-test") == []


# ── 3. HTTP routes ─────────────────────────────────────────────────────────


@pytest.fixture
def flask_client(fresh_store, monkeypatch):
    """A minimal Flask app wired only to bp_bootstrap. Avoids pulling in the
    full dashboard.py so unit tests stay fast."""
    ls, store = fresh_store
    sys.modules["clawmetry.local_store"] = ls

    # Stub load_config so the route's node_id_filter returns a stable value.
    import clawmetry.sync as sync
    monkeypatch.setattr(sync, "load_config", lambda: {"node_id": "node-test"})

    sys.modules.pop("routes.bootstrap", None)
    import routes.bootstrap as bp_module
    importlib.reload(bp_module)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(bp_module.bp_bootstrap)
    with app.test_client() as client:
        yield client, store


def test_api_bootstrap_returns_404_when_empty(flask_client):
    client, _ = flask_client
    resp = client.get("/api/bootstrap")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["snapshots"] == []
    assert body["node_id"] == "node-test"


def test_api_bootstrap_list_returns_summary(flask_client):
    client, store = flask_client
    store.ingest_bootstrap_archive({
        "node_id": "node-test", "agent_id": "main",
        "content": "# hello", "first_session_id": "sess-1",
    })
    resp = client.get("/api/bootstrap")
    assert resp.status_code == 200
    body = resp.get_json()
    assert len(body["snapshots"]) == 1
    snap = body["snapshots"][0]
    # Summary endpoint MUST NOT include the heavy `content` field.
    assert "content" not in snap
    assert snap["first_session_id"] == "sess-1"
    assert snap["agent_id"] == "main"
    assert body["_source"] == "local_store"


def test_api_bootstrap_detail_returns_full_content(flask_client):
    client, store = flask_client
    store.ingest_bootstrap_archive({
        "node_id": "node-test", "agent_id": "main",
        "content": "# DETAILED PAYLOAD",
        "first_session_id": "sess-1",
    })
    resp = client.get("/api/bootstrap/main")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["snapshot"]["content"] == "# DETAILED PAYLOAD"
    assert body["first_session_id"] == "sess-1"


def test_api_bootstrap_detail_missing_agent_returns_404(flask_client):
    client, store = flask_client
    store.ingest_bootstrap_archive({
        "node_id": "node-test", "agent_id": "main", "content": "# main",
    })
    resp = client.get("/api/bootstrap/subagent-99")
    assert resp.status_code == 404
    body = resp.get_json()
    assert body["agent_id"] == "subagent-99"
