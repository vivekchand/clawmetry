"""Tests for routes/runtime_ingest.py — the Pro custom-runtime HTTP API.

Pins the auth contract (localhost or token header), the entitlement gate
(402 in enforce mode), the run-then-events happy path, and the basic
shape validation. Uses a stub LocalStore so we don't need a daemon.
"""
from __future__ import annotations

import importlib
import time
from unittest.mock import MagicMock

import pytest
from flask import Flask


class _StubStore:
    def __init__(self):
        self.events: list[dict] = []
        self.sessions: list[dict] = []

    def ingest(self, ev: dict):
        self.events.append(ev)

    def ingest_session(self, sess: dict):
        self.sessions.append(sess)


@pytest.fixture
def app(monkeypatch, tmp_path):
    """Flask app with the runtime_ingest blueprint + a stub store. Auth
    defaults to localhost mode (no token configured)."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_TOKEN", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))

    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()

    from routes import runtime_ingest as _ri
    importlib.reload(_ri)

    stub = _StubStore()
    monkeypatch.setattr(_ri, "_store", lambda: stub)

    app = Flask(__name__)
    app.register_blueprint(_ri.bp_runtime_ingest)
    app.config["TESTING"] = True
    app._ri_store = stub  # type: ignore[attr-defined]
    return app


def test_runtimes_list_is_public_and_lists_known(app):
    with app.test_client() as c:
        r = c.get("/api/v1/runtimes")
        assert r.status_code == 200
        body = r.get_json()
        assert isinstance(body["runtimes"], list)
        # openclaw is in the catalog under the FREE bucket.
        ids = [row["id"] for row in body["runtimes"]]
        assert "openclaw" in ids


def test_start_run_happy_path(app):
    with app.test_client() as c:
        r = c.post("/api/v1/runs", json={"runtime": "my_engine", "metadata": {"k": "v"}})
        assert r.status_code == 200, r.get_data(as_text=True)
        body = r.get_json()
        assert body["ok"] is True
        assert body["run_id"].startswith("run_")
        assert body["runtime"] == "my_engine"
    sessions = app._ri_store.sessions  # type: ignore[attr-defined]
    assert len(sessions) == 1
    assert sessions[0]["agent_type"] == "my_engine"


def test_start_run_accepts_client_supplied_id(app):
    with app.test_client() as c:
        r = c.post("/api/v1/runs", json={"run_id": "my-run-42"})
        assert r.status_code == 200
        assert r.get_json()["run_id"] == "my-run-42"


def test_append_events_single(app):
    with app.test_client() as c:
        c.post("/api/v1/runs", json={"run_id": "r1"})
        r = c.post("/api/v1/runs/r1/events", json={
            "event": {
                "id": "evt_1", "ts": time.time(),
                "event_type": "model.completed", "model": "claude-3.5",
            }
        })
        assert r.status_code == 200, r.get_data(as_text=True)
        body = r.get_json()
        assert body["accepted"] == 1
        assert body["ids"] == ["evt_1"]
    evs = app._ri_store.events  # type: ignore[attr-defined]
    assert len(evs) == 1
    assert evs[0]["event_type"] == "model.completed"
    assert evs[0]["session_id"] == "r1"


def test_append_events_bulk_and_fills_required_keys(app):
    with app.test_client() as c:
        c.post("/api/v1/runs", json={"run_id": "r2"})
        r = c.post("/api/v1/runs/r2/events", json={
            "events": [
                {"event_type": "prompt.submitted"},  # id + ts filled in
                {"event_type": "model.completed", "model": "gpt-5"},
            ],
        })
        assert r.status_code == 200
        body = r.get_json()
        assert body["accepted"] == 2
        assert len(body["ids"]) == 2
    evs = app._ri_store.events  # type: ignore[attr-defined]
    assert {e["event_type"] for e in evs} == {"prompt.submitted", "model.completed"}
    # Each event should have an id, ts, node_id, agent_type filled in.
    for e in evs:
        assert e["id"]
        assert e["ts"]
        assert e["node_id"]
        assert e["agent_type"]


def test_append_events_rejects_oversized_batch(app):
    with app.test_client() as c:
        c.post("/api/v1/runs", json={"run_id": "r3"})
        events = [{"event_type": "x"} for _ in range(1001)]
        r = c.post("/api/v1/runs/r3/events", json={"events": events})
        assert r.status_code == 400
        assert r.get_json()["error"] == "bad_request"


def test_append_events_validates_event_shape(app):
    with app.test_client() as c:
        c.post("/api/v1/runs", json={"run_id": "r4"})
        # ts that isn't a number
        r = c.post("/api/v1/runs/r4/events", json={
            "event": {"event_type": "x", "ts": "not-a-number"},
        })
        assert r.status_code == 400
        assert "ts" in r.get_json()["detail"]


def test_end_run_stamps_ended_at(app):
    with app.test_client() as c:
        c.post("/api/v1/runs", json={"run_id": "r5"})
        r = c.post("/api/v1/runs/r5/end", json={})
        assert r.status_code == 200
    # ingest_session was called twice: once for start, once for end.
    sessions = app._ri_store.sessions  # type: ignore[attr-defined]
    end_calls = [s for s in sessions if s.get("ended_at_ms")]
    assert len(end_calls) == 1
    assert end_calls[0]["session_id"] == "r5"


# ── auth ───────────────────────────────────────────────────────────────────────


def test_token_required_when_configured(app, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_INGEST_TOKEN", "secret-token")
    # The route reads the env var at request time, not module load, so just
    # set it and call.
    with app.test_client() as c:
        # No header → 401
        r = c.post("/api/v1/runs", json={})
        assert r.status_code == 401
        # Wrong header → 401
        r = c.post("/api/v1/runs", json={}, headers={"X-ClawMetry-Token": "wrong"})
        assert r.status_code == 401
        # Right header → 200
        r = c.post("/api/v1/runs", json={}, headers={"X-ClawMetry-Token": "secret-token"})
        assert r.status_code == 200


# ── entitlement gate ──────────────────────────────────────────────────────────


def test_gate_returns_402_when_enforced(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as _ent
    importlib.reload(_ent)
    _ent.invalidate()

    from routes import runtime_ingest as _ri
    importlib.reload(_ri)

    app = Flask(__name__)
    app.register_blueprint(_ri.bp_runtime_ingest)

    with app.test_client() as c:
        r = c.post("/api/v1/runs", json={})
        assert r.status_code == 402
        body = r.get_json()
        assert body["feature"] == "custom_runtime_ingest"
