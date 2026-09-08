"""Tests for routes/rules.py — Rule Builder REST API (issue #1517)."""

import json
import os
import pathlib
import tempfile

import pytest


@pytest.fixture()
def rules_dir(tmp_path, monkeypatch):
    d = tmp_path / "rules"
    d.mkdir()
    monkeypatch.setenv("CLAWMETRY_RULES_DIR", str(d))
    return d


@pytest.fixture()
def app(rules_dir):
    from flask import Flask
    from routes.rules import bp_rules

    application = Flask(__name__)
    application.register_blueprint(bp_rules)
    application.config["TESTING"] = True
    return application


@pytest.fixture()
def client(app):
    return app.test_client()


# ── helpers ──────────────────────────────────────────────────────────────────

def _put(client, rid, body):
    return client.put(
        f"/api/v2/rules/{rid}",
        data=json.dumps(body),
        content_type="application/json",
    )


def _post_backtest(client, rid, days=7):
    return client.post(f"/api/v2/rules/{rid}/backtest?days={days}")


# ── list ─────────────────────────────────────────────────────────────────────

def test_list_empty(client):
    r = client.get("/api/v2/rules")
    assert r.status_code == 200
    assert r.json["rules"] == []


def test_list_after_put(client):
    _put(client, "rule-a", {"title": "Rule A", "event_type": "tool.call"})
    r = client.get("/api/v2/rules")
    assert r.status_code == 200
    assert len(r.json["rules"]) == 1
    assert r.json["rules"][0]["id"] == "rule-a"
    assert r.json["rules"][0]["title"] == "Rule A"


# ── get ──────────────────────────────────────────────────────────────────────

def test_get_missing(client):
    r = client.get("/api/v2/rules/nonexistent")
    assert r.status_code == 404


def test_get_after_put(client):
    _put(client, "my-rule", {"title": "My Rule", "enabled": False})
    r = client.get("/api/v2/rules/my-rule")
    assert r.status_code == 200
    assert r.json["title"] == "My Rule"
    assert r.json["enabled"] is False
    assert r.json["id"] == "my-rule"


# ── put ──────────────────────────────────────────────────────────────────────

def test_put_creates(client, rules_dir):
    r = _put(client, "rule-1", {"title": "T", "event_type": "llm.call"})
    assert r.status_code == 200
    assert r.json["ok"] is True
    assert (rules_dir / "rule-1.json").exists()


def test_put_invalid_id(client):
    r = _put(client, "../escape", {"title": "x"})
    assert r.status_code == 400


def test_put_non_object_body(client):
    r = client.put(
        "/api/v2/rules/r1",
        data=json.dumps([1, 2, 3]),
        content_type="application/json",
    )
    assert r.status_code == 400


def test_put_stamps_updated_at(client):
    r = _put(client, "ts-rule", {"title": "T"})
    assert "updated_at" in r.json


# ── delete ───────────────────────────────────────────────────────────────────

def test_delete_missing(client):
    r = client.delete("/api/v2/rules/ghost")
    assert r.status_code == 404


def test_delete_removes_file(client, rules_dir):
    _put(client, "del-me", {"title": "bye"})
    assert (rules_dir / "del-me.json").exists()
    r = client.delete("/api/v2/rules/del-me")
    assert r.status_code == 200
    assert not (rules_dir / "del-me.json").exists()


# ── backtest ─────────────────────────────────────────────────────────────────

def test_backtest_missing_rule(client):
    r = _post_backtest(client, "no-such")
    assert r.status_code == 404


def test_backtest_returns_shape(client, monkeypatch):
    _put(client, "bt-rule", {"title": "BT", "event_type": "tool.call"})

    # Patch daemon call to return a controlled list of events
    fake_events = [{"id": f"e{i}", "event_type": "tool.call"} for i in range(5)]

    import routes.rules as rr
    monkeypatch.setattr(
        rr,
        "_store_via_daemon_or_direct",
        lambda *a, **kw: fake_events,
    )

    r = _post_backtest(client, "bt-rule", days=7)
    assert r.status_code == 200
    data = r.json
    assert data["rule_id"] == "bt-rule"
    assert data["window_days"] == 7
    assert data["matched"] == 5
    assert len(data["sampled"]) == 5


def test_backtest_caps_days(client, monkeypatch):
    _put(client, "cap-rule", {"title": "Cap"})
    import routes.rules as rr
    monkeypatch.setattr(rr, "_store_via_daemon_or_direct", lambda *a, **kw: [])
    r = client.post("/api/v2/rules/cap-rule/backtest?days=999")
    assert r.status_code == 200
    assert r.json["window_days"] == 90
