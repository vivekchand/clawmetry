"""The generic "my agent is waiting" hook receiver.

One tolerant endpoint for every runtime, because their payloads differ only
in spelling: Claude Code / Copilot / Qwen Code all fire a PermissionRequest
carrying ``session_id`` + ``tool_name``; Gemini CLI fires Notification with
camelCase. Wiring a new runtime should be a line in its own hook config, not
an installer we have to ship and verify before anyone can use it.

The contract these tests pin:
  * OBSERVE ONLY -- it records and returns, never answers a prompt, never
    blocks the agent.
  * It cannot 500. A hook that errors is a hook that might make someone's
    agent hesitate, which is a far worse outcome than a missing badge.
  * Loopback only -- a dashboard bound to 0.0.0.0 must not take attention
    state from the network.
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "e.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    ls.mark_writer_owner()
    store = ls.get_store()
    store.ingest_sessions_batch([
        {"agent_type": "qwen_code", "session_id": "qwen_code:abc",
         "status": "active", "title": "Real work"},
        {"agent_type": "gemini_cli", "session_id": "gemini_cli:gem-9",
         "status": "active", "title": "Gemini work"},
    ])

    # Force the single-process path. Otherwise every read is proxied to
    # whatever daemon happens to be running on the dev machine and the test
    # silently asserts against the developer's real DuckDB.
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)

    import routes.attention as ra
    importlib.reload(ra)
    app = Flask(__name__)
    app.register_blueprint(ra.bp_attention)
    app.config["TESTING"] = True
    c = app.test_client()
    c._store = store
    return c


def _row(store, sid):
    for r in store.query_sessions_table(limit=50):
        if r["session_id"] == sid:
            return r
    return None


# ── the shapes real runtimes send ───────────────────────────────────────────

def test_permissionrequest_shape_flags_the_session(client):
    """Claude Code / Copilot / Qwen Code all send this."""
    r = client.post("/api/hooks/attention?runtime=qwen_code",
                    json={"session_id": "abc", "tool_name": "Bash",
                          "hook_event_name": "PermissionRequest"})
    assert r.status_code == 200 and r.get_json()["state"] == "waiting"
    row = _row(client._store, "qwen_code:abc")
    assert row["attention_state"] == "waiting_approval"
    # Ground truth, not a guess -- the runtime told us.
    assert row["attention_signal"] == "hook"
    assert row["attention_tool"] == "Bash"


def test_camelcase_notification_shape(client):
    """Gemini CLI fires Notification with camelCase keys."""
    r = client.post("/api/hooks/attention?runtime=gemini_cli",
                    json={"sessionId": "gem-9", "toolName": "run_shell_command"})
    assert r.get_json()["state"] == "waiting"
    row = _row(client._store, "gemini_cli:gem-9")
    assert row["attention_signal"] == "hook"
    assert row["attention_tool"] == "run_shell_command"


def test_already_namespaced_id_is_not_double_prefixed(client):
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "qwen_code:abc", "tool_name": "Read"})
    assert _row(client._store, "qwen_code:abc")["attention_state"] is not None
    assert _row(client._store, "qwen_code:qwen_code:abc") is None


def test_resolved_event_clears(client):
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "abc", "tool_name": "Bash"})
    r = client.post("/api/hooks/attention?runtime=qwen_code&event=resolved",
                    json={"session_id": "abc"})
    assert r.get_json()["state"] == "cleared"
    assert _row(client._store, "qwen_code:abc")["attention_state"] is None


def test_response_reports_whether_the_write_actually_landed(client):
    """`stored` is the diagnostic someone wiring a hook needs.

    A write can silently no-op — commonest cause being a daemon older than
    the proxy allowlist entry for set_session_attention — and answering "ok"
    regardless would leave them with a hook that reports success and a badge
    that never appears, with nothing to explain the gap. Observed for real on
    a dev box mid-build, which is why it is pinned here.
    """
    r = client.post("/api/hooks/attention?runtime=qwen_code",
                    json={"session_id": "abc", "tool_name": "Bash"})
    body = r.get_json()
    assert body["stored"] is True          # this fixture writes locally
    assert "stored" in body


def test_runtime_may_come_from_the_body(client):
    client.post("/api/hooks/attention",
                json={"runtime": "qwen_code", "session_id": "abc",
                      "tool_name": "Bash"})
    assert _row(client._store, "qwen_code:abc")["attention_state"] is not None


# ── it must never make an agent hesitate ────────────────────────────────────

def test_unknown_runtime_is_rejected(client):
    """Bounded, so a typo cannot create rows under a runtime the rest of the
    app has never heard of."""
    r = client.post("/api/hooks/attention?runtime=notarealthing",
                    json={"session_id": "x"})
    assert r.status_code == 400


def test_missing_session_id_is_rejected(client):
    r = client.post("/api/hooks/attention?runtime=codex",
                    json={"tool_name": "Bash"})
    assert r.status_code == 400


@pytest.mark.parametrize("body", [None, [], "text", {"session_id": {"a": 1}}])
def test_malformed_bodies_never_500(client, body):
    r = client.post("/api/hooks/attention?runtime=codex", json=body)
    assert r.status_code in (200, 400), "a hook that 500s can stall an agent"


def test_empty_post_never_500s(client):
    r = client.post("/api/hooks/attention?runtime=codex",
                    data=b"not json", content_type="application/json")
    assert r.status_code in (200, 400)


# ── the read side ───────────────────────────────────────────────────────────

def test_get_attention_reports_the_hooked_session(client, monkeypatch):
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "abc", "tool_name": "Bash"})
    # Freshness keys off the daemon heartbeat; force it fresh for the read.
    import routes.attention as ra
    monkeypatch.setattr(ra, "_daemon_age_seconds", lambda: 5)
    d = client.get("/api/attention").get_json()
    assert d["fresh"] is True
    assert d["waiting"] == 1
    item = d["items"][0]
    assert item["signal"] == "hook" and item["tool"] == "Bash"


def test_stale_daemon_reports_cant_tell_not_all_clear(client, monkeypatch):
    """The failure that would destroy trust: a wedged detector rendering as
    a confident 'nothing needs you'."""
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "abc", "tool_name": "Bash"})
    import routes.attention as ra
    monkeypatch.setattr(ra, "_daemon_age_seconds", lambda: 99999)
    d = client.get("/api/attention").get_json()
    assert d["fresh"] is False
    assert d["reason"] == "stale"
    assert d["items"] == []          # withheld, not asserted as empty


def test_hook_confirmed_rows_sort_above_guesses(client, monkeypatch):
    """Certainty outranks duration: a row we are sure about deserves the eye
    before one we inferred, even if the guess has waited longer."""
    store = client._store
    store.ingest_sessions_batch([{"agent_type": "codex",
                                  "session_id": "codex:old", "status": "active"}])
    store.apply_session_attention([{
        "session_id": "codex:old", "runtime": "codex", "state": "waiting_approval",
        "signal": "inferred", "tool": "Read", "waiting_seconds": 9999}])
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "abc", "tool_name": "Bash"})
    import routes.attention as ra
    monkeypatch.setattr(ra, "_daemon_age_seconds", lambda: 5)
    items = client.get("/api/attention").get_json()["items"]
    assert [i["signal"] for i in items][0] == "hook"


def test_working_count_excludes_long_idle_sessions(client, monkeypatch):
    """"N agents working" must mean N agents that actually moved recently.

    Sessions routinely never receive an ended_at -- killed process, slept
    machine, crashed runtime -- so a status-only test reports long-dead
    sessions as busy. Measured on a real install: 6 sessions a status-only
    test called "working" had last moved 30 minutes to 24 hours earlier.
    Under a reassuring "nothing needs you", that is confidently wrong in the
    one place this feature must not be.
    """
    import datetime
    import routes.attention as ra
    monkeypatch.setattr(ra, "_daemon_age_seconds", lambda: 5)

    def ago(minutes):
        return (datetime.datetime.now()
                - datetime.timedelta(minutes=minutes)).isoformat()

    client._store.ingest_sessions_batch([
        {"agent_type": "codex", "session_id": "codex:fresh",
         "status": "active", "last_active_at": ago(2)},
        {"agent_type": "codex", "session_id": "codex:zombie",
         "status": "active", "last_active_at": ago(600)},   # 10h, never ended
    ])
    d = client.get("/api/attention?runtime=codex").get_json()
    assert d["working"] == 1, (
        "a session idle for 10 hours with status='active' is not working")


def test_runtime_filter_scopes_the_list(client, monkeypatch):
    """A filtered view must never show node-wide numbers."""
    client.post("/api/hooks/attention?runtime=qwen_code",
                json={"session_id": "abc", "tool_name": "Bash"})
    client.post("/api/hooks/attention?runtime=gemini_cli",
                json={"sessionId": "gem-9", "toolName": "sh"})
    import routes.attention as ra
    monkeypatch.setattr(ra, "_daemon_age_seconds", lambda: 5)
    d = client.get("/api/attention?runtime=qwen_code").get_json()
    assert d["waiting"] == 1
    assert d["items"][0]["runtime"] == "qwen_code"
