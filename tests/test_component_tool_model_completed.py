"""Regression guard for /api/component/tool/<name> DuckDB fast path
against the v3 ``model.completed`` event shape.

Silent-zero bug-class fix #5 (2026-05-18). Real OpenClaw v3 installs in
the wild write assistant turns as ``event_type="model.completed"`` (per
``reference_openclaw_v3_event_types.md``). The previous fast path only
queried ``("message", "assistant")``, so today's users with 0 message
rows + only model.completed rows silently fell through to the 8s+
JSONL walker and the Sessions modal stuck on "Loading...".

This file pins:

  1. ``model.completed`` rows whose ``data.toolMetas[]`` carries a v3
     tool call hydrate the fast path (the post-#1135 daemon-normalised
     shape).
  2. ``model.completed`` rows whose nested ``data.message.content[]``
     carries ``tool_use`` blocks also hydrate (legacy nested shape).
  3. Every tool family in ``_TOOL_MAP`` (session / exec / browser /
     search / cron / tts / memory) is reachable through model.completed.
  4. Empty store → helper still returns a populated shell (no caller
     fall-through), per the issue #1291 contract.
  5. The fast path answers within 2 seconds.

See ``feedback_synthetic_tests_missed_real_event_shape.md`` for why the
synthetic-only earlier tests missed this class entirely.
"""

from __future__ import annotations

import importlib
import json
import time
import uuid
from datetime import datetime

import pytest
from flask import Flask


def _today_iso(suffix: str) -> str:
    return f"{datetime.now().strftime('%Y-%m-%d')}T{suffix}"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.components as components_mod
    importlib.reload(components_mod)

    # Isolate fixture from a developer's locally-running daemon, same as
    # ``test_component_gateway_local_store_v3``.
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)

    a = Flask(__name__)
    a.register_blueprint(components_mod.bp_components)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _drain(store):
    store._flush_now()
    for _ in range(20):
        if not store._ring:
            break
        time.sleep(0.05)


def _row(event_id, sid, event_type, ts, data, **extra):
    base = {
        "id":           event_id,
        "node_id":      "node-test",
        "agent_type":   "openclaw",
        "agent_id":     "main",
        "session_id":   sid,
        "workspace_id": None,
        "event_type":   event_type,
        "ts":           ts,
        "data":         json.dumps(data),
    }
    base.update(extra)
    return base


# ── Shape 1: v3 toolMetas[] on model.completed (daemon-normalised) ─────────

@pytest.mark.parametrize("tool_family,tool_name,expected_detail_key", [
    ("session",  "sessions_spawn", "detail"),
    ("exec",     "exec",           "detail"),
    ("browser",  "browser",        "detail"),
    ("search",   "web_search",     "detail"),
    ("cron",     "cron",           "detail"),
    ("tts",      "tts",            "detail"),
    ("memory",   "Read",           "detail"),
])
def test_model_completed_toolmetas_lights_up_every_family(
    app, tool_family, tool_name, expected_detail_key
):
    """v3 model.completed + toolMetas[] is the shape on real installs.
    Every tool family must reach the modal through it."""
    a, ls = app
    store = ls.get_store()

    sample_inputs = {
        "sessions_spawn": {"sessionId": "sess-spawn", "name": "child"},
        "exec":           {"command": "echo MOAT_FAMILY"},
        "browser":        {"action": "navigate",
                            "targetUrl": "https://example.com"},
        "web_search":     {"query": "claude opus"},
        "cron":           {"expr": "0 9 * * *", "action": "list"},
        "tts":            {"text": "hello world", "voice": "alloy"},
        "Read":           {"file_path": "/tmp/notes.md"},
    }

    store.ingest(_row(
        f"e-mc-{tool_name}",
        f"sess-{tool_name}",
        "model.completed",
        _today_iso("10:00:00Z"),
        {
            "_v3_type":      "message",
            "modelId":       "claude-opus-4-7",
            "provider":      "anthropic",
            "completionText": f"using {tool_name}",
            "toolMetas": [
                {"id":    f"toolu_{uuid.uuid4().hex[:8]}",
                 "name":  tool_name,
                 "input": sample_inputs[tool_name]},
            ],
        },
        model="claude-opus-4-7",
    ))
    _drain(store)

    t0 = time.monotonic()
    r = a.test_client().get(f"/api/component/tool/{tool_family}")
    elapsed = time.monotonic() - t0

    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body.get("_source") == "local_store", (
        f"family={tool_family} lost canary tag: {body!r}"
    )
    assert body["stats"]["today_calls"] >= 1, (
        f"family={tool_family} did not surface model.completed call: {body!r}"
    )
    tools_seen = {e.get("tool") for e in body["events"]}
    assert tool_name in tools_seen, (
        f"family={tool_family} did not return tool={tool_name!r}: "
        f"events={body['events']!r}"
    )
    # Hard 2s contract — the fast path must NOT fall back to JSONL.
    assert elapsed < 2.0, (
        f"fast path took {elapsed:.2f}s — should be <2s; family={tool_family}"
    )


# ── Shape 2: legacy nested message.content[] on model.completed ────────────

def test_model_completed_nested_message_content_lights_up(app):
    """Some daemon-emitted model.completed rows still carry the nested
    ``data.message.content[]`` (legacy shape preserved when the daemon
    sees the original ``message`` shape). The fast path must walk both."""
    a, ls = app
    store = ls.get_store()

    store.ingest(_row(
        "e-mc-nested",
        "sess-nested",
        "model.completed",
        _today_iso("10:30:00Z"),
        {
            "_v3_type": "message",
            "modelId":  "claude-opus-4-7",
            "provider": "anthropic",
            "message":  {
                "role":    "assistant",
                "model":   "claude-opus-4-7",
                "content": [
                    {"type": "text", "text": "running it"},
                    {"type": "tool_use", "id": "toolu_nested",
                     "name": "exec",
                     "input": {"command": "ls -la"}},
                ],
            },
        },
        model="claude-opus-4-7",
    ))
    _drain(store)

    body = a.test_client().get("/api/component/tool/exec").get_json()
    assert body.get("_source") == "local_store"
    assert body["stats"]["today_calls"] >= 1, body
    assert any(e.get("tool") == "exec" for e in body["events"]), body


# ── Empty-store: helper still returns populated shell (issue #1291) ────────

def test_empty_store_returns_shell_not_none(app):
    """Empty DuckDB → fast path returns ``{events:[], stats:..., total:0,
    _source:'local_store'}`` so the caller does NOT fall through to the
    7s+ JSONL walker. Per issue #1291 / PR #1266 contract."""
    a, _ls = app
    body = a.test_client().get("/api/component/tool/exec").get_json()
    assert body.get("_source") == "local_store"
    assert body["events"] == []
    assert body["stats"]["today_calls"] == 0
    assert body["stats"]["today_errors"] == 0


# ── Mixed: model.completed + assistant rows coexist, both contribute ───────

def test_mixed_model_completed_and_assistant_both_contribute(app):
    """A real install often has BOTH legacy ``assistant`` rows (older
    days) and v3 ``model.completed`` rows (recent days) — counts must
    union, not skip the newer shape."""
    a, ls = app
    store = ls.get_store()

    store.ingest(_row(
        "e-assistant", "sess-mix-1", "assistant",
        _today_iso("11:00:00Z"),
        {"message": {"role": "assistant", "content": [
            {"type": "toolCall", "name": "exec",
             "arguments": {"command": "uname -a"}},
        ]}},
    ))
    store.ingest(_row(
        "e-mc", "sess-mix-2", "model.completed",
        _today_iso("11:01:00Z"),
        {"_v3_type": "message", "modelId": "claude-opus-4-7",
         "toolMetas": [
             {"id": "toolu_mix", "name": "exec",
              "input": {"command": "df -h"}},
         ]},
    ))
    _drain(store)

    body = a.test_client().get("/api/component/tool/exec").get_json()
    assert body.get("_source") == "local_store"
    assert body["stats"]["today_calls"] >= 2, body
