"""Tier-1 DuckDB fast path for /api/plugins per-plugin invocation counts.

The endpoint historically scanned up to 60 session JSONLs (every line)
on every Plugins-tab render to count tool-call invocations per plugin.
With dozens of active sessions this stage dominates the panel's render
time even though the answer rarely changes minute-to-minute.

This test asserts:
  1. Unit — when the local DuckDB has tool-call events whose name
     contains a plugin key, ``query_tool_call_invocations`` returns
     one row per call with ``{ts, name}``.
  2. E2E — synthetic OpenClaw-shaped events round-trip:
        ingest -> DuckDB -> /api/plugins -> invocations_30d /
        last_used_ts
     Both v3 ``tool.call`` events and assistant ``message`` events with
     legacy ``content[*]`` ``toolCall`` blocks are accepted.
  3. Fallback — empty store + empty workspace -> zero invocations for
     every plugin (no synthetic data, no crash).
  4. Daemon-proxy — when ``local_store_via_daemon`` returns a populated
     row list, the route must use it (and NOT fall through to JSONL).
"""

from __future__ import annotations

import importlib
import json
import os
import time

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app with bp_plugins registered, fresh DuckDB per test, plus
    a synthetic openclaw.json on disk so /api/plugins discovers a real
    plugin set to count against."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)

    # Lay down a synthetic config file so _read_config_plugins finds
    # plugins to count against. The plugin reader walks fixed
    # ~/.openclaw/* paths — point HOME at tmp_path so the test is
    # hermetic.
    monkeypatch.setenv("HOME", str(tmp_path))
    oc_dir = tmp_path / ".openclaw"
    oc_dir.mkdir(parents=True)
    cfg = {
        "plugins": {
            "telegram": {"enabled": True, "version": "1.0"},
            "exec":     {"enabled": True, "version": "1.0"},
            "browser":  {"enabled": True, "version": "1.0"},
        }
    }
    (oc_dir / "openclaw.json").write_text(json.dumps(cfg))

    import dashboard as _d
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "sessions_empty"), raising=False)

    import routes.plugins as plugins_mod
    importlib.reload(plugins_mod)

    # Force-create the writer singleton so direct opens succeed even in
    # the empty-store test (DuckDB read_only=True can't create a missing
    # file). No-op if a test ingests events later — get_store() returns
    # the same singleton.
    ls.get_store()

    a = Flask(__name__)
    a.register_blueprint(plugins_mod.bp_plugins)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _ingest_tool_call(store, *, sid: str, ts: str, name: str,
                      ev_id: str | None = None):
    """Insert one v3 top-level tool.call event."""
    if ev_id is None:
        ev_id = f"tc-{sid}-{ts}-{name}"
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "tool.call",
        "ts":         ts,
        "data":       {"name": name, "input": {}},
    })


def _ingest_legacy_assistant_block(store, *, sid: str, ts: str, name: str,
                                    ev_id: str | None = None):
    """Insert a legacy assistant message whose ``data.message.content``
    carries a raw ``{type:'toolCall', name}`` block — the on-disk shape
    the legacy JSONL walker sees on older OpenClaw transcripts."""
    if ev_id is None:
        ev_id = f"msg-{sid}-{ts}-{name}"
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "message",
        "ts":         ts,
        "data":       {
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "toolCall", "name": name, "input": {}},
                ],
            }
        },
    })


# ── E2E: synthetic events round-trip through DuckDB → /api/plugins ────────


def test_plugins_fast_path_counts_v3_tool_call_events(app):
    """A v3 tool.call event whose name matches a plugin key (substring)
    must increment invocations_30d for that plugin."""
    a, ls = app
    store = ls.get_store()
    # Use a recent ts so it falls inside the 30d window.
    recent_ts = "2026-05-15T10:00:00+00:00"
    _ingest_tool_call(store, sid="s1", ts=recent_ts, name="exec")
    _ingest_tool_call(store, sid="s1", ts="2026-05-15T10:01:00+00:00", name="exec")
    _ingest_tool_call(store, sid="s1", ts="2026-05-15T10:02:00+00:00", name="browser")
    _wait_flush(store)

    body = a.test_client().get("/api/plugins").get_json()
    assert body["_source"] == "local_store"
    by_name = {p["name"]: p for p in body["plugins"]}
    assert by_name["exec"]["invocations_30d"] == 2
    assert by_name["browser"]["invocations_30d"] == 1
    assert by_name["telegram"]["invocations_30d"] == 0
    assert by_name["telegram"]["unused"] is True


def test_plugins_fast_path_counts_legacy_content_blocks(app):
    """Legacy assistant message events whose data.message.content carries
    raw toolCall blocks must also count — closes the gap the legacy
    JSONL walker depended on for older transcripts."""
    a, ls = app
    store = ls.get_store()
    _ingest_legacy_assistant_block(
        store, sid="leg-1", ts="2026-05-15T11:00:00+00:00", name="exec",
    )
    _wait_flush(store)

    body = a.test_client().get("/api/plugins").get_json()
    by_name = {p["name"]: p for p in body["plugins"]}
    assert by_name["exec"]["invocations_30d"] == 1


def test_plugins_fast_path_zero_when_store_empty(app):
    """Empty DuckDB + empty SESSIONS_DIR -> all plugins listed with
    invocations_30d=0 and unused=True. No crash."""
    a, _ls = app
    body = a.test_client().get("/api/plugins").get_json()
    assert body["_source"] == "local_store"
    by_name = {p["name"]: p for p in body["plugins"]}
    for key in ("telegram", "exec", "browser"):
        assert by_name[key]["invocations_30d"] == 0
        assert by_name[key]["unused"] is True
        assert by_name[key]["last_used_ts"] is None


def test_plugins_fast_path_excludes_events_outside_30d_window(app):
    """Events older than 30d must not contribute to invocations_30d, but
    they CAN still drive last_used_ts forward — matches the legacy
    walker's behaviour."""
    a, ls = app
    store = ls.get_store()
    # 60-day-old call: should NOT count, but should still set last_ts.
    old_ts = time.time() - 60 * 86400
    from datetime import datetime, timezone
    old_iso = datetime.fromtimestamp(old_ts, tz=timezone.utc).isoformat()
    # Recent call (1h ago): should count.
    recent_ts = time.time() - 3600
    recent_iso = datetime.fromtimestamp(recent_ts, tz=timezone.utc).isoformat()

    _ingest_tool_call(store, sid="old", ts=old_iso, name="exec")
    _ingest_tool_call(store, sid="new", ts=recent_iso, name="exec")
    _wait_flush(store)

    body = a.test_client().get("/api/plugins").get_json()
    by_name = {p["name"]: p for p in body["plugins"]}
    # Only the recent call counts; the old one drives last_used_ts.
    assert by_name["exec"]["invocations_30d"] == 1


# ── Unit: the LocalStore method itself ─────────────────────────────────────


def test_query_tool_call_invocations_returns_empty_on_empty(app):
    _a, ls = app
    store = ls.get_store()
    rows = store.query_tool_call_invocations(since="2026-05-01T00:00:00Z")
    assert rows == []


def test_query_tool_call_invocations_extracts_v3_tool_call(app):
    _a, ls = app
    store = ls.get_store()
    _ingest_tool_call(store, sid="sx", ts="2026-05-15T13:00:00+00:00", name="MyTool")
    _wait_flush(store)
    rows = store.query_tool_call_invocations(since="2026-05-01T00:00:00Z")
    assert len(rows) == 1
    assert rows[0]["name"] == "MyTool"
    assert rows[0]["ts"].startswith("2026-05-15T13:00:00")


def test_query_tool_call_invocations_respects_since(app):
    """Events older than ``since`` must be excluded — keeps the 30d-window
    contract /api/plugins depends on."""
    _a, ls = app
    store = ls.get_store()
    _ingest_tool_call(store, sid="old", ts="2026-04-01T00:00:00+00:00", name="exec")
    _ingest_tool_call(store, sid="new", ts="2026-05-15T15:00:00+00:00", name="exec")
    _wait_flush(store)
    rows = store.query_tool_call_invocations(since="2026-05-10T00:00:00+00:00")
    assert len(rows) == 1
    assert rows[0]["name"] == "exec"


# ── Daemon-call mocking: route hits the proxy, not direct open ─────────────


def test_plugins_route_uses_daemon_proxy_when_available(app, monkeypatch):
    """When ``local_store_via_daemon`` returns a populated row list, the
    route must use it (and NOT fall through to direct open / JSONL)."""
    a, _ls = app
    canned = [
        {"ts": "2026-05-15T16:00:00+00:00", "name": "exec"},
        {"ts": "2026-05-15T16:01:00+00:00", "name": "exec"},
        {"ts": "2026-05-15T16:02:00+00:00", "name": "browser"},
    ]
    calls = {"n": 0, "method": None}

    def fake_proxy(method_name, **kwargs):
        calls["n"] += 1
        calls["method"] = method_name
        if method_name == "query_tool_call_invocations":
            return canned
        return None

    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", fake_proxy)

    body = a.test_client().get("/api/plugins").get_json()
    by_name = {p["name"]: p for p in body["plugins"]}
    assert calls["n"] == 1, "route did not call the daemon proxy"
    assert calls["method"] == "query_tool_call_invocations"
    assert by_name["exec"]["invocations_30d"] == 2
    assert by_name["browser"]["invocations_30d"] == 1
    assert body["_source"] == "local_store"
