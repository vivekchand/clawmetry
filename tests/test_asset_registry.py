"""Tests for the asset registry first slice — issue #2201.

Covers:
- LocalStore methods (ingest_asset / update_asset_status / query_assets /
  get_asset) using a raw LocalStore (not get_store(), which may return a
  daemon proxy on a dev box with the sync daemon running).
- The HTTP surface in routes/assets.py and the Self-Evolve "save as asset"
  hook in routes/selfevolve.py — both exercised through Flask's test client
  with the LocalStore daemon-proxy short-circuited to a single in-process
  raw store.
"""
from __future__ import annotations

import importlib
import sys

import pytest


# ── LocalStore-level tests ─────────────────────────────────────────────────

@pytest.fixture
def raw_store(tmp_path, monkeypatch):
    """A fresh LocalStore writing to a temp DuckDB. Use the raw class so
    ``_ring`` / ``_conn`` access works (``get_store()`` may proxy)."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    sys.modules.pop("clawmetry.local_store", None)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    store = ls.LocalStore()
    yield store
    try:
        store.stop(flush=False)
    except Exception:
        pass


def _mk(asset_id="a1", **overrides):
    base = {
        "id": asset_id,
        "asset_type": "prompt",
        "name": "Better refactor prompt",
        "description": "from a real session",
        "source_session_id": "sess-1",
        "tags": ["self-evolve", "prompt-quality"],
        "content": {"body": "...prompt body..."},
    }
    base.update(overrides)
    return base


class TestLocalStoreAssets:
    def test_ingest_and_get(self, raw_store):
        raw_store.ingest_asset(_mk())
        row = raw_store.get_asset("a1")
        assert row is not None
        assert row["id"] == "a1"
        assert row["asset_type"] == "prompt"
        assert row["status"] == "pending"
        assert row["tags"] == ["self-evolve", "prompt-quality"]
        assert row["content"] == {"body": "...prompt body..."}
        assert row["source_session_id"] == "sess-1"

    def test_get_unknown_returns_none(self, raw_store):
        assert raw_store.get_asset("does-not-exist") is None
        assert raw_store.get_asset("") is None

    def test_invalid_type_rejected(self, raw_store):
        with pytest.raises(ValueError):
            raw_store.ingest_asset(_mk(asset_type="nope"))

    def test_invalid_status_rejected(self, raw_store):
        with pytest.raises(ValueError):
            raw_store.ingest_asset(_mk(status="weird"))

    def test_id_required(self, raw_store):
        with pytest.raises(ValueError):
            raw_store.ingest_asset(_mk(asset_id=""))

    def test_upsert_preserves_status_and_reviewer(self, raw_store):
        raw_store.ingest_asset(_mk())
        raw_store.update_asset_status(
            "a1", status="approved", reviewer="vivek", reason="looks good"
        )
        # Re-ingest the same id with new name/content; status must stick.
        raw_store.ingest_asset(_mk(name="Renamed", content={"body": "v2"}))
        row = raw_store.get_asset("a1")
        assert row["status"] == "approved"
        assert row["reviewer"] == "vivek"
        assert row["name"] == "Renamed"
        assert row["content"] == {"body": "v2"}

    def test_update_status_unknown_returns_false(self, raw_store):
        assert raw_store.update_asset_status("missing", status="approved") is False

    def test_query_filters(self, raw_store):
        raw_store.ingest_asset(_mk("a1", asset_type="prompt", source_run_id="r1"))
        raw_store.ingest_asset(_mk("a2", asset_type="skill", source_run_id="r1"))
        raw_store.ingest_asset(_mk("a3", asset_type="prompt", source_run_id="r2"))
        raw_store.update_asset_status("a2", status="approved")
        all_rows = raw_store.query_assets()
        assert {r["id"] for r in all_rows} == {"a1", "a2", "a3"}
        prompts = raw_store.query_assets(asset_type="prompt")
        assert {r["id"] for r in prompts} == {"a1", "a3"}
        approved = raw_store.query_assets(status="approved")
        assert {r["id"] for r in approved} == {"a2"}
        run_r1 = raw_store.query_assets(source_run_id="r1")
        assert {r["id"] for r in run_r1} == {"a1", "a2"}

    def test_query_ordered_newest_first(self, raw_store):
        import time as _t
        raw_store.ingest_asset(_mk("a1"))
        _t.sleep(0.01)
        raw_store.ingest_asset(_mk("a2"))
        _t.sleep(0.01)
        raw_store.update_asset_status("a1", status="approved")  # bumps updated_at
        rows = raw_store.query_assets()
        assert [r["id"] for r in rows][:2] == ["a1", "a2"]


# ── HTTP-surface tests ─────────────────────────────────────────────────────

@pytest.fixture
def client(raw_store, monkeypatch):
    """Flask test client with the daemon-proxy short-circuited to the
    in-process raw store. Avoids spinning up the daemon for unit tests."""
    def _fake_via_daemon(method_name, **kwargs):
        return getattr(raw_store, method_name)(**kwargs)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", _fake_via_daemon, raising=False)
    # Also short-circuit the in-package fallback get_store() that the routes
    # reach for if the daemon proxy returns None. The fixture-loaded raw
    # store is the truth here.
    import clawmetry.local_store as ls
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: raw_store)
    from flask import Flask
    from routes.assets import bp_assets
    from routes.selfevolve import bp_selfevolve
    app = Flask(__name__)
    app.register_blueprint(bp_assets)
    app.register_blueprint(bp_selfevolve)
    return app.test_client()


class TestAssetsHTTP:
    def test_post_creates_asset(self, client):
        r = client.post("/api/assets", json={
            "id": "h1", "asset_type": "prompt", "name": "API-created",
            "source_session_id": "sess-9",
            "content": {"body": "..."},
        })
        assert r.status_code == 201, r.get_json()
        assert r.get_json()["id"] == "h1"

    def test_post_rejects_bad_type(self, client):
        r = client.post("/api/assets", json={
            "id": "x", "asset_type": "bogus", "name": "n",
        })
        assert r.status_code == 400

    def test_post_requires_id_and_name(self, client):
        assert client.post("/api/assets", json={"asset_type": "prompt", "name": "x"}).status_code == 400
        assert client.post("/api/assets", json={"id": "x", "asset_type": "prompt"}).status_code == 400

    def test_get_list_and_detail(self, client):
        client.post("/api/assets", json={
            "id": "h1", "asset_type": "skill", "name": "n1",
        })
        r = client.get("/api/assets")
        body = r.get_json()
        assert r.status_code == 200
        assert body["count"] >= 1
        assert any(a["id"] == "h1" for a in body["assets"])
        detail = client.get("/api/assets/h1").get_json()
        assert detail["id"] == "h1"

    def test_get_detail_404(self, client):
        assert client.get("/api/assets/nope").status_code == 404

    def test_review_approve(self, client):
        client.post("/api/assets", json={
            "id": "h1", "asset_type": "prompt", "name": "n",
        })
        r = client.post("/api/assets/h1/review", json={
            "action": "approve", "reviewer": "vivek", "reason": "ok",
        })
        assert r.status_code == 200
        body = r.get_json()
        assert body["status"] == "approved"
        assert body["reviewer"] == "vivek"

    def test_review_unknown_action(self, client):
        client.post("/api/assets", json={
            "id": "h1", "asset_type": "prompt", "name": "n",
        })
        r = client.post("/api/assets/h1/review", json={"action": "yolo"})
        assert r.status_code == 400

    def test_review_missing_asset(self, client):
        r = client.post("/api/assets/nope/review", json={"action": "approve"})
        assert r.status_code == 404

    def test_selfevolve_save_as_asset(self, client):
        r = client.post("/api/selfevolve/findings/save-as-asset", json={
            "finding_id": "f-abc",
            "session_id": "sess-42",
            "summary": "Drop the redundant retry",
            "body": "...details...",
            "asset_type": "prompt",
        })
        assert r.status_code == 201, r.get_json()
        body = r.get_json()
        assert body["status"] == "pending"
        assert body["source_session_id"] == "sess-42"
        # Self-evolve provenance recorded in tags + content.
        assert "self-evolve" in body["tags"]
        assert body["content"]["finding_id"] == "f-abc"

    def test_selfevolve_save_requires_summary(self, client):
        r = client.post("/api/selfevolve/findings/save-as-asset", json={
            "finding_id": "f-abc",
        })
        assert r.status_code == 400
