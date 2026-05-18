"""MOAT E2E: synthesised v3 ``model.completed`` ingest → /api/component/tool
fast-path readback.

Sister of ``tests/test_moat_send_message_e2e.py`` but laser-focused on
the silent-zero bug-class regression fixed 2026-05-18: the Sessions
modal stuck on "Loading..." because ``_try_local_store_component_tool``
only queried ``("message", "assistant")`` and missed the
daemon-normalised ``model.completed`` shape every real OpenClaw v3
install writes (per ``reference_openclaw_v3_event_types.md``).

What this file pins, end-to-end:

  * Seed a real v3 ``model.completed`` row through the public
    ``LocalStore.ingest`` API.
  * Hit ``/api/component/tool/exec`` over the in-process Flask client.
  * Assert the call lands in events[] AND ``_source=local_store``.
  * Assert the response shape mirrors the legacy JSONL parser.

If a future PR drops ``model.completed`` from the fast-path query list
again (the 5th instance of this class today), this test goes red.
"""

from __future__ import annotations

import importlib
import json
import time
import uuid
from datetime import datetime, timezone

import pytest
from flask import Flask


def _now_today_iso() -> str:
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.components as components_mod
    importlib.reload(components_mod)

    # Force the daemon-discovery file to a path that doesn't exist so the
    # in-process Flask client always punts to our hermetic DuckDB.
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"),
        raising=True,
    )
    lq._invalidate_daemon_cache()

    a = Flask(__name__)
    a.register_blueprint(components_mod.bp_components)

    yield {"ls": ls, "client": a.test_client()}

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_drained(store, timeout: float = 3.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            depth = store.health()["ring_depth"]
        except Exception:
            depth = 0
        if depth == 0:
            return
        time.sleep(0.02)


def _seed_model_completed(store, tool_name: str, args: dict) -> str:
    """Push one v3 ``model.completed`` row carrying a single tool call
    through the public ingest API. Returns the row id so the test can
    cross-check."""
    eid = f"mc-{uuid.uuid4().hex[:10]}"
    store.ingest({
        "id":           eid,
        "node_id":      "node-moat-tool",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   "sess-moat-tool",
        "workspace_id": None,
        "event_type":   "model.completed",
        "ts":           _now_today_iso(),
        "data":         json.dumps({
            "_v3_type":       "message",
            "modelId":        "claude-opus-4-7",
            "provider":       "anthropic",
            "completionText": f"calling {tool_name}",
            "stopReason":     "tool_use",
            "toolMetas": [
                {"id":    f"toolu_{uuid.uuid4().hex[:8]}",
                 "name":  tool_name,
                 "input": args},
            ],
        }),
        "model":        "claude-opus-4-7",
        "cost_usd":     0.001,
        "token_count":  162,
    })
    _wait_drained(store)
    return eid


def test_model_completed_lands_in_api_component_tool_exec(env):
    """Public ingest → /api/component/tool/exec readback.

    Asserts the canary: v3 model.completed rows surface in events[] AND
    the fast path tagged ``_source: local_store``. The synthetic shape
    used here matches the post-daemon-normalisation tree real installs
    write (verified against the prompt's DuckDB probe output)."""
    ls = env["ls"]
    client = env["client"]
    store = ls.get_store()

    _seed_model_completed(store, "exec", {"command": "echo MOAT_TOOL_E2E"})

    r = client.get("/api/component/tool/exec")
    assert r.status_code == 200
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"v3 model.completed lost fast-path canary: {body!r}"
    )
    assert body["stats"]["today_calls"] >= 1, body
    tools = {e.get("tool") for e in body.get("events") or []}
    assert "exec" in tools, f"exec not in events: {body!r}"
    # Detail extraction (matches the legacy parser's name=='exec' branch).
    exec_events = [e for e in body["events"] if e.get("tool") == "exec"]
    assert exec_events, body
    assert "MOAT_TOOL_E2E" in exec_events[0].get("detail", ""), exec_events


def test_model_completed_session_tool_lands_in_api_component_tool_session(env):
    """Same E2E for the session family — Sessions modal is the actual
    user-visible regression the prompt called out."""
    ls = env["ls"]
    client = env["client"]
    store = ls.get_store()

    _seed_model_completed(
        store, "sessions_spawn",
        {"sessionId": "child-sess-1", "name": "child"},
    )

    body = client.get("/api/component/tool/session").get_json()
    assert body.get("_source") == "local_store"
    tools = {e.get("tool") for e in body["events"]}
    assert "sessions_spawn" in tools, body
