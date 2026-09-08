"""The /api/guard/policies contract for escalation ladders.

A ladder authored in the UI must come back exactly as the engine will run it,
and a malformed rung must be REFUSED rather than silently dropped: the store
normalizes by dropping unusable rungs (right for reading old rows), which
would otherwise hand an author a ladder quietly missing a step.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from flask import Flask  # noqa: E402

from routes.guard import bp_guard  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    """Flask test client over an in-memory policy store."""
    saved = {}

    def _write(method, **kw):
        if method == "upsert_session_policy":
            p = kw["policy"]
            saved[p["policy_id"]] = p
        elif method == "delete_session_policy":
            saved.pop(kw.get("policy_id"), None)

    def _call(method, **kw):
        if method == "query_session_policies":
            return list(saved.values())
        return None

    import routes.guard as g
    monkeypatch.setattr(g, "_ls_write", _write)
    monkeypatch.setattr(g, "_ls_call", _call)

    app = Flask(__name__)
    app.register_blueprint(bp_guard)
    with app.test_client() as c:
        yield c, saved


def _post(client, **body):
    return client.post("/api/guard/policies", json=body)


def test_a_ladder_round_trips(client):
    c, saved = client
    r = _post(c, name="stuck", action="pause", steps=[
        {"action": "pause", "after_secs": 0},
        {"action": "kill", "after_secs": 300},
    ])
    assert r.status_code == 200 and r.json["ok"] is True
    steps = r.json["policy"]["steps"]
    assert [s["action"] for s in steps] == ["pause", "kill"]
    assert steps[1]["after_secs"] == 300


def test_an_unknown_step_action_is_refused_not_dropped(client):
    c, _ = client
    r = _post(c, action="pause", steps=[
        {"action": "pause", "after_secs": 0},
        {"action": "terminate", "after_secs": 60},
    ])
    assert r.status_code == 400
    assert "step 2" in r.json["error"]


def test_a_negative_delay_is_refused(client):
    c, _ = client
    r = _post(c, action="pause", steps=[
        {"action": "pause", "after_secs": 0},
        {"action": "kill", "after_secs": -5},
    ])
    assert r.status_code == 400 and "after_secs" in r.json["error"]


def test_a_non_list_ladder_is_refused(client):
    c, _ = client
    r = _post(c, action="pause", steps={"action": "kill"})
    assert r.status_code == 400


def test_an_over_long_ladder_is_refused(client):
    from clawmetry.policy_engine import MAX_LADDER_STEPS
    c, _ = client
    r = _post(c, action="alert",
              steps=[{"action": "alert", "after_secs": 1}] * (MAX_LADDER_STEPS + 1))
    assert r.status_code == 400 and str(MAX_LADDER_STEPS) in r.json["error"]


def test_step_zero_delay_is_normalized_in_the_echo(client):
    """What the operator is shown must equal what the engine will run."""
    c, _ = client
    r = _post(c, action="pause",
              steps=[{"action": "pause", "after_secs": 900},
                     {"action": "kill", "after_secs": 60}])
    assert r.json["policy"]["steps"][0]["after_secs"] == 0


def test_a_plain_policy_still_works(client):
    c, _ = client
    r = _post(c, name="simple", action="kill")
    assert r.status_code == 200 and r.json["ok"] is True
    assert r.json["policy"]["steps"] == [{"action": "kill", "after_secs": 0}]


def test_get_exposes_the_ladder_limits(client):
    c, _ = client
    _post(c, action="monitor")
    r = c.get("/api/guard/policies")
    assert r.status_code == 200
    assert r.json["max_ladder_steps"] >= 2
    assert "kill" in r.json["actions"]
    # Every policy reads back with a ladder, plain ones included.
    assert all(p["steps"] for p in r.json["policies"])
