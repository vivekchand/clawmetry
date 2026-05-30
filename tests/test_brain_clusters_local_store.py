"""Hermetic tests for GET /api/brain/clusters (issue #1650).

Verifies that the Brain-tab clustering endpoint:
  1. Returns the documented JSON shape when DuckDB has session data.
  2. Returns an empty-but-valid payload when DuckDB has no data.
  3. Sets capped_at_24h=True for non-Pro users and caps the look-back to 1 day.
  4. Sets capped_at_24h=False for Pro users and honours the ?days= param.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


def _iso(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def _seed(store, n: int = 3):
    now = time.time()
    for i in range(n):
        store.ingest({
            "id":          f"ev-clust-{i}",
            "node_id":     "node-test",
            "agent_type":  "openclaw",
            "agent_id":    "main",
            "session_id":  f"sess-clust-{i}",
            "event_type":  "tool_call",
            "ts":          _iso(now - i * 60),
            "data":        {"tool": "Bash", "input": f"echo hi-{i}"},
            "cost_usd":    0.001,
            "token_count": 20,
            "model":       "claude-opus-4-7",
        })
    # One additional event with a known tool so cluster label is deterministic.
    store.ingest({
        "id":          "ev-clust-tool",
        "node_id":     "node-test",
        "agent_type":  "openclaw",
        "agent_id":    "main",
        "session_id":  "sess-clust-0",
        "event_type":  "tool_call",
        "ts":          _iso(now),
        "data":        {"tool": "exec", "input": "ls"},
        "cost_usd":    0.05,
        "token_count": 100,
        "model":       "claude-opus-4-7",
    })
    _wait_flush(store)


def _wait_flush(store, t: float = 3.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.05)


def _build_app(tmp_path, monkeypatch, *, is_pro: bool = True):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "bc.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.usage as usage_mod
    importlib.reload(usage_mod)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.brain as br
    importlib.reload(br)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: is_pro)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    app = Flask(__name__)
    app.register_blueprint(br.bp_brain)
    return app, ls


@pytest.fixture
def pro_app(tmp_path, monkeypatch):
    app, ls = _build_app(tmp_path, monkeypatch, is_pro=True)
    yield app, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def oss_app(tmp_path, monkeypatch):
    app, ls = _build_app(tmp_path, monkeypatch, is_pro=False)
    yield app, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_brain_clusters_shape(pro_app):
    """With data in DuckDB the endpoint returns the documented contract."""
    app, ls = pro_app
    _seed(ls.get_store())

    body = app.test_client().get("/api/brain/clusters?days=30").get_json()

    assert body["_shape"] == "brain_clusters"
    assert body["_source"] == "local_store"
    assert body["capped_at_24h"] is False
    assert isinstance(body["clusters"], list)
    assert body["total_sessions"] >= 1

    for c in body["clusters"]:
        required = {
            "cluster_id", "label", "session_count",
            "total_tokens", "total_cost_usd", "avg_cost_usd",
            "error_count", "tool_category", "cost_tier",
            "has_errors", "model_family", "top_tools",
        }
        missing = required - c.keys()
        assert not missing, f"cluster missing keys {missing}: {c}"
        assert c["session_count"] >= 1


def test_brain_clusters_empty_store(pro_app):
    """With an empty DuckDB the endpoint still returns a valid payload."""
    app, _ls = pro_app

    body = app.test_client().get("/api/brain/clusters").get_json()

    assert body["_shape"] == "brain_clusters"
    assert body["clusters"] == []
    assert body["total_sessions"] == 0


def test_brain_clusters_oss_cap(oss_app):
    """Non-Pro users get capped_at_24h=True regardless of the days param."""
    app, _ls = oss_app

    body = app.test_client().get("/api/brain/clusters?days=90").get_json()

    assert body["capped_at_24h"] is True
    assert body["days"] == 1  # clamped for OSS users
