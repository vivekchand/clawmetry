"""API surface for agent identity (``routes/govern.py``).

Pins the contracts that matter for a governance primitive:

* the store-less cloud container gets an honest empty 200, never a 500
  (the same cold-fall-through contract ``routes/inventory.py`` carries);
* ownership can only be attached to a principal we have actually observed --
  an inventory that accepts arbitrary keys is an inventory nobody can trust;
* the detail view is filtered from the same derived roster as the list view,
  so the two can never disagree.
"""

from __future__ import annotations

import pytest
from flask import Flask

from routes.govern import bp_govern


def _app():
    app = Flask(__name__)
    app.register_blueprint(bp_govern)
    return app


@pytest.fixture
def client(monkeypatch):
    import routes.govern as g

    monkeypatch.setattr(g, "is_local_store_read_enabled", lambda: True)
    return _app().test_client()


_ROWS = [
    {
        "principal_id": "ap_1111111111111111",
        "node_id": "node-a",
        "runtime": "claude_code",
        "agent_id": "main",
        "sessions": 3,
        "owner": "",
        "owner_source": "",
    },
    {
        "principal_id": "ap_2222222222222222",
        "node_id": "node-a",
        "runtime": "codex",
        "agent_id": "reviewer",
        "sessions": 1,
        "owner": "sre",
        "owner_source": "runtime",
    },
]


def _stub_store(monkeypatch, rows=None, capture=None):
    import routes.govern as g

    def _call(method, **kw):
        if capture is not None:
            capture.append((method, kw))
        if method == "query_agent_principals":
            return list(_ROWS if rows is None else rows)
        return None

    monkeypatch.setattr(g, "_store_call", _call)


# ── cloud cold fall-through ───────────────────────────────────────────────

def test_store_less_cloud_gets_an_honest_empty_200(monkeypatch):
    import routes.govern as g

    monkeypatch.setattr(g, "is_local_store_read_enabled", lambda: False)
    r = _app().test_client().get("/api/govern/principals")
    assert r.status_code == 200
    assert r.get_json() == {"principals": [], "total": 0}


def test_a_dead_store_is_an_empty_roster_not_a_500(client, monkeypatch):
    import routes.govern as g

    monkeypatch.setattr(g, "_store_call", lambda *a, **k: None)
    r = client.get("/api/govern/principals")
    assert r.status_code == 200
    assert r.get_json()["total"] == 0


# ── list ──────────────────────────────────────────────────────────────────

def test_list_returns_the_roster(client, monkeypatch):
    _stub_store(monkeypatch)
    body = client.get("/api/govern/principals").get_json()
    assert body["total"] == 2
    assert {p["agent_id"] for p in body["principals"]} == {"main", "reviewer"}


def test_filters_are_forwarded_to_the_store(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    client.get("/api/govern/principals?runtime=codex&node_id=node-a&limit=7")
    method, kw = seen[0]
    assert method == "query_agent_principals"
    assert kw["runtime"] == "codex"
    assert kw["node_id"] == "node-a"
    assert kw["limit"] == 7


def test_runtime_all_means_no_runtime_filter(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    client.get("/api/govern/principals?runtime=all")
    assert seen[0][1]["runtime"] is None


def test_a_garbage_limit_does_not_500(client, monkeypatch):
    _stub_store(monkeypatch)
    assert client.get("/api/govern/principals?limit=banana").status_code == 200


def test_limit_is_clamped(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    client.get("/api/govern/principals?limit=999999")
    assert seen[0][1]["limit"] == 2000


# ── detail ────────────────────────────────────────────────────────────────

def test_detail_returns_one_principal(client, monkeypatch):
    _stub_store(monkeypatch)
    body = client.get("/api/govern/principals/ap_2222222222222222").get_json()
    assert body["agent_id"] == "reviewer"
    assert body["owner_source"] == "runtime"


def test_detail_404s_for_an_unknown_id(client, monkeypatch):
    _stub_store(monkeypatch)
    assert client.get("/api/govern/principals/ap_nope").status_code == 404


# ── ownership ─────────────────────────────────────────────────────────────

def test_owner_write_targets_the_principal_id(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    r = client.post(
        "/api/govern/principals/ap_1111111111111111/owner",
        json={"owner": "platform-team"},
    )
    assert r.status_code == 200 and r.get_json()["ok"] is True
    writes = [(m, kw) for m, kw in seen if m == "set_agent_meta"]
    assert writes and writes[0][1]["agent_key"] == "ap_1111111111111111"
    assert writes[0][1]["owner"] == "platform-team"


def test_owner_write_is_refused_for_an_unobserved_principal(client, monkeypatch):
    """Accepting any key would write unbounded rows into agent_meta and let an
    owner be attached to an agent that does not exist."""
    seen = []
    _stub_store(monkeypatch, capture=seen)
    r = client.post(
        "/api/govern/principals/ap_not_a_real_agent/owner", json={"owner": "x"}
    )
    assert r.status_code == 404
    assert not [m for m, _ in seen if m == "set_agent_meta"]


def test_an_empty_body_is_rejected_rather_than_clearing_the_owner(client, monkeypatch):
    """None means "leave this field alone"; a bodyless POST must not be read as
    "clear it"."""
    seen = []
    _stub_store(monkeypatch, capture=seen)
    r = client.post("/api/govern/principals/ap_1111111111111111/owner", json={})
    assert r.status_code == 400
    assert not [m for m, _ in seen if m == "set_agent_meta"]


def test_owner_can_be_cleared_explicitly(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    r = client.post(
        "/api/govern/principals/ap_1111111111111111/owner", json={"owner": ""}
    )
    assert r.status_code == 200
    writes = [kw for m, kw in seen if m == "set_agent_meta"]
    assert writes and writes[0]["owner"] == ""


def test_notes_only_update_leaves_owner_untouched(client, monkeypatch):
    seen = []
    _stub_store(monkeypatch, capture=seen)
    client.post(
        "/api/govern/principals/ap_1111111111111111/owner", json={"notes": "on call"}
    )
    writes = [kw for m, kw in seen if m == "set_agent_meta"]
    assert writes and writes[0]["owner"] is None and writes[0]["notes"] == "on call"


def test_owner_write_is_a_noop_when_the_store_is_disabled(monkeypatch):
    import routes.govern as g

    monkeypatch.setattr(g, "is_local_store_read_enabled", lambda: False)
    r = _app().test_client().post(
        "/api/govern/principals/ap_1/owner", json={"owner": "x"}
    )
    assert r.status_code == 200
    assert r.get_json()["ok"] is False
