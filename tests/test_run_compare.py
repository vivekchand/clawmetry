"""Per-run A/B compare with deltas (#2196 item #2)."""
from __future__ import annotations

import importlib
import time

import pytest


def _store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ev.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "2")
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import clawmetry.local_store as ls
    importlib.reload(ls)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    return ls, ls.get_store()


def _wait_flush(store, t=3.0):
    end = time.monotonic() + t
    while time.monotonic() < end and store.health()["ring_depth"] > 0:
        time.sleep(0.02)


def _patch_daemon_proxy(monkeypatch, store):
    """Make routes.local_query.local_store_via_daemon read straight from the
    in-process store, so the route handler runs end-to-end without needing the
    real daemon HTTP server."""
    import routes.sessions as sessions_mod

    def fake_proxy(method, **kwargs):
        fn = getattr(store, method)
        return fn(**kwargs)

    # The route imports lazily inside the function — patch the module it pulls
    # from so both call sites resolve to our fake.
    monkeypatch.setattr(
        "routes.local_query.local_store_via_daemon", fake_proxy, raising=False,
    )
    return sessions_mod


def test_run_compare_stats_basic(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # Baseline run "a": 3 tool calls, no errors, no flags (clean).
        for i in range(3):
            store.ingest({
                "id": f"a:{i}", "node_id": "n", "agent_id": "main",
                "session_id": "claude_code:run-a",
                "event_type": "tool_call",
                "ts": f"2026-05-28T10:00:{i:02d}Z",
                "data": {"name": "Read"},
                "cost_usd": 0.10, "token_count": 100, "model": None,
            })
        # Candidate run "b": 35 tool calls (runaway) + a real error.
        for i in range(35):
            store.ingest({
                "id": f"b:{i}", "node_id": "n", "agent_id": "main",
                "session_id": "claude_code:run-b",
                "event_type": "tool_call",
                "ts": f"2026-05-28T11:00:{i:02d}Z",
                "data": {"name": "Bash"},
                "cost_usd": 0.10, "token_count": 100, "model": None,
            })
        store.ingest({
            "id": "b:result-err", "node_id": "n", "agent_id": "main",
            "session_id": "claude_code:run-b",
            "event_type": "tool_result",
            "ts": "2026-05-28T11:01:00Z",
            "data": {"role": "tool", "_runtime": "claude_code",
                     "content": "Exit code 1\nTraceback ...",
                     "extra": {"isError": True}},
            "cost_usd": 0.0, "token_count": 0, "model": None,
        })
        _wait_flush(store)

        sessions_mod = _patch_daemon_proxy(monkeypatch, store)
        a = sessions_mod._run_compare_stats("claude_code:run-a")
        b = sessions_mod._run_compare_stats("claude_code:run-b")

        # Baseline: clean (3 steps, no errors, no flags).
        assert a["runtime"] == "claude_code"
        assert a["step_count"] == 3
        assert a["error_count"] == 0
        assert a["flag_count"] == 0
        assert a["severity"] == "green"
        assert a["missing"] is False
        # Candidate: runaway flag + 1 real error.
        assert b["step_count"] == 35
        assert b["error_count"] == 1
        assert any(f["type"] == "runaway" for f in b["flags"])
        assert b["severity"] == "red"

        deltas = sessions_mod._run_compare_deltas(a, b)
        # Step count went up — that's a regression (favorable=False for
        # lower-is-better metrics).
        assert deltas["step_count"]["abs"] == 32
        assert deltas["step_count"]["favorable"] is False
        # Error count went up too.
        assert deltas["error_count"]["a"] == 0
        assert deltas["error_count"]["b"] == 1
        assert deltas["error_count"]["favorable"] is False
        # When A is zero, pct is None (no /0).
        assert deltas["error_count"]["pct"] is None
    finally:
        store.stop(flush=True)


def _client_with_route():
    """Mount bp_sessions on a fresh Flask app — dashboard.py only registers
    blueprints inside main(), so plain ``import dashboard`` leaves them off.
    This mirrors the pattern in tests/test_channels_local_store.py."""
    from flask import Flask
    import routes.sessions as sessions_mod
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    return a.test_client()


def test_run_compare_route_missing_params():
    """The HTTP route returns a clean 400 when either id is missing or both
    refer to the same session — sanity test for the API contract."""
    client = _client_with_route()
    resp = client.get("/api/run-compare?a=x")
    assert resp.status_code == 400, resp.get_data(as_text=True)

    resp = client.get("/api/run-compare?a=same&b=same")
    assert resp.status_code == 400


def test_run_compare_route_end_to_end(tmp_path, monkeypatch):
    ls, store = _store(tmp_path, monkeypatch)
    try:
        # Two clean sessions, different cost.
        store.ingest({
            "id": "cheap:1", "node_id": "n", "agent_id": "main",
            "session_id": "openclaw-cheap", "event_type": "tool_call",
            "ts": "2026-05-28T08:00:00Z", "data": {"name": "Read"},
            "cost_usd": 0.05, "token_count": 100, "model": None,
        })
        store.ingest({
            "id": "spendy:1", "node_id": "n", "agent_id": "main",
            "session_id": "openclaw-spendy", "event_type": "tool_call",
            "ts": "2026-05-28T09:00:00Z", "data": {"name": "Read"},
            # cost up, but under the bloated-context token threshold so the
            # severity stays green — we're only asserting the cost delta here.
            "cost_usd": 5.00, "token_count": 1_000, "model": None,
        })
        _wait_flush(store)

        _patch_daemon_proxy(monkeypatch, store)
        client = _client_with_route()
        resp = client.get(
            "/api/run-compare?a=openclaw-cheap&b=openclaw-spendy"
        )
        assert resp.status_code == 200, resp.get_data(as_text=True)
        body = resp.get_json()
        assert body["a"]["session_id"] == "openclaw-cheap"
        assert body["b"]["session_id"] == "openclaw-spendy"
        # B is more expensive -> regression on cost.
        assert body["deltas"]["cost_usd"]["abs"] > 4.0
        assert body["deltas"]["cost_usd"]["favorable"] is False
        # Both clean -> green severity.
        assert body["a"]["severity"] == body["b"]["severity"] == "green"
    finally:
        store.stop(flush=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
