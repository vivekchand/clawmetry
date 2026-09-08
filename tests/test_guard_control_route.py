"""``POST /api/guard/control`` acts on the STORED session, never on request
strings.

The handler resolves the caller's ``session_id`` against the local store and
hands the store's own copy of the id and working directory to the actuator.
That is the whole security argument for the endpoint: a request can NAME a
session ClawMetry already knows, but it can never supply the string a
process is located or signalled with.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest  # noqa: E402
from flask import Flask  # noqa: E402

import routes.guard as g  # noqa: E402
import clawmetry.guard_actuator as ga  # noqa: E402
from routes.guard import bp_guard  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    app = Flask(__name__)
    app.register_blueprint(bp_guard)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def store(monkeypatch):
    """A store that knows exactly one session, with a recorded cwd."""
    rows = {"claude_code:abc-123": {"session_id": "claude_code:abc-123",
                                    "cwd": "/tmp/proj", "git_branch": "main",
                                    "metadata": {}}}

    def _call(method, **kw):
        if method == "get_session_location":
            return rows.get(kw.get("session_id"))
        return None

    monkeypatch.setattr(g, "_ls_call", _call)
    return rows


@pytest.fixture
def actuator(monkeypatch):
    calls = []

    def fake(runtime, session_id, cwd, action, trace=None):
        calls.append({"runtime": runtime, "session_id": session_id,
                      "cwd": cwd, "action": action})
        # The real actuator appends its steps to the caller's list as it goes,
        # so the route still holds a partial record when a step fails.
        if trace is not None:
            trace.append({"step": "Send the signal", "ok": True,
                          "detail": "signalled"})
        return {"ok": True, "detail": "signalled"}

    monkeypatch.setattr(ga, "guard_actuate", fake)
    return calls


def test_unknown_session_is_refused_before_any_actuator_call(client, store, actuator):
    r = client.post("/api/guard/control",
                    json={"action": "pause", "session_id": "nope-1",
                          "runtime": "claude_code"})
    assert r.status_code == 404
    assert r.get_json()["detail"] == "session_not_in_store"
    assert actuator == []


def test_actuator_receives_the_stored_id_and_cwd_not_the_request(client, store, actuator):
    r = client.post("/api/guard/control",
                    json={"action": "stop", "session_id": "claude_code:abc-123",
                          "runtime": "claude_code"})
    assert r.status_code == 200, r.get_json()
    assert r.get_json()["ok"] is True
    assert actuator == [{"runtime": "claude_code",
                         "session_id": "claude_code:abc-123",
                         "cwd": "/tmp/proj", "action": "stop"}]


def test_namespaced_family_ids_pass_the_prefilter(client, store, actuator):
    """Family rows are stored as ``<runtime>:<id>``; the pre-filter must not
    refuse the colon or every Claude Code / Codex row loses its buttons."""
    r = client.post("/api/guard/control",
                    json={"action": "pause", "session_id": "claude_code:abc-123"})
    assert r.status_code == 200
    assert actuator[0]["session_id"] == "claude_code:abc-123"


@pytest.mark.parametrize("bad", ["../etc", "a/b", "x..y", "-lead", "", "a b"])
def test_path_like_ids_are_refused_by_the_prefilter(client, store, actuator, bad):
    r = client.post("/api/guard/control",
                    json={"action": "pause", "session_id": bad})
    assert r.status_code == 400
    assert actuator == []


def test_a_cwd_that_disagrees_with_the_record_is_refused(client, store, actuator):
    r = client.post("/api/guard/control",
                    json={"action": "kill", "session_id": "claude_code:abc-123",
                          "cwd": "/somewhere/else"})
    assert r.status_code == 400
    assert "cwd" in r.get_json()["error"]
    assert actuator == []


def test_unknown_action_and_runtime_are_refused(client, store, actuator):
    r = client.post("/api/guard/control",
                    json={"action": "explode", "session_id": "claude_code:abc-123"})
    assert r.status_code == 400
    r = client.post("/api/guard/control",
                    json={"action": "pause", "session_id": "claude_code:abc-123",
                          "runtime": "Bad Runtime"})
    assert r.status_code == 400
    assert actuator == []


def test_actuator_failure_is_a_fixed_token_not_exception_text(client, store, monkeypatch):
    def boom(runtime, session_id, cwd, action):
        raise RuntimeError("secret /Users/x/traceback.py line 12")

    monkeypatch.setattr(ga, "guard_actuate", boom)
    r = client.post("/api/guard/control",
                    json={"action": "pause", "session_id": "claude_code:abc-123"})
    assert r.status_code == 500
    body = r.get_json()
    assert "traceback" not in str(body)
    assert body["error"] == "control action failed; see the server log"


def test_daemon_and_route_share_one_actuator():
    """The policy pass in the daemon and the HTTP route must call the same
    function object — there is no second path to a process."""
    from clawmetry import sync
    assert sync._guard_actuate is ga.guard_actuate
