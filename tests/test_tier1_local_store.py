"""Tests for the Tier-1 DuckDB fast paths added to four route modules.

Covers the routes the migration touched under
``CLAWMETRY_LOCAL_STORE_READ=1``:

  * routes/components.py — /api/component/tool/<name>, /api/component/brain
    (other component routes intentionally NOT migrated — see PR body)
  * routes/autonomy.py   — /api/autonomy
  * routes/advisor.py    — /api/advisor/ask, /api/advisor/status
  * routes/reasoning.py  — /api/reasoning?session=<id>

Each route gets:
  1. positive case — env flag set + populated store → response carries
     ``_source: "local_store"`` and the legacy contract fields are non-empty.
  2. negative case (one per Blueprint) — env flag UNSET → fast path skipped
     (response lacks the ``_source`` tag).

Pattern lifted from ``test_sessions_local_fastpath.py`` /
``test_brain_local_fastpath.py``.
"""

from __future__ import annotations

import importlib
import time
from datetime import datetime, timezone

import pytest
from flask import Flask


# ── shared helpers ─────────────────────────────────────────────────────────


def _iso(epoch_seconds: float) -> str:
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).isoformat()


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _reload_local_store(monkeypatch, tmp_path, *, fast_path: bool):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    if fast_path:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    else:
        monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "0")  # force legacy path
    import clawmetry.local_store as ls
    importlib.reload(ls)
    return ls


# ── components: /api/component/tool/<name>, /api/component/brain ───────────


@pytest.fixture
def components_app(tmp_path, monkeypatch):
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=True)
    import routes.components as comp_mod
    importlib.reload(comp_mod)
    a = Flask(__name__)
    a.register_blueprint(comp_mod.bp_components)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_component_tool_fast_path_returns_local_rows(components_app):
    a, ls = components_app
    store = ls.get_store()
    today = datetime.now().strftime("%Y-%m-%d")
    # Two exec tool_call events today, one Read (memory family) today
    store.ingest({
        "id": "ev-tool-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-x", "event_type": "tool_call",
        "ts": f"{today}T10:00:00Z",
        "data": {"name": "exec", "arguments": {"command": "ls -la"}},
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "ev-tool-2", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-x", "event_type": "tool_call",
        "ts": f"{today}T10:01:00Z",
        "data": {"name": "exec", "arguments": {"command": "echo hi"}},
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    store.ingest({
        "id": "ev-tool-3", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-x", "event_type": "tool_call",
        "ts": f"{today}T10:02:00Z",
        "data": {"name": "Read", "arguments": {"file_path": "/tmp/x"}},
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/component/tool/exec")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["name"] == "exec"
    assert body["stats"]["today_calls"] == 2
    assert len(body["events"]) == 2
    assert body["events"][0]["tool"] == "exec"
    assert body["events"][0]["action"] == "exec"


def test_component_brain_fast_path_returns_local_rows(components_app):
    a, ls = components_app
    store = ls.get_store()
    today = datetime.now().strftime("%Y-%m-%d")
    store.ingest({
        "id": "ev-brain-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-llm", "event_type": "message",
        "ts": f"{today}T11:00:00Z",
        "data": {
            "message": {
                "role": "assistant",
                "model": "claude-opus-4-7",
                "usage": {"input": 1200, "output": 350,
                          "cacheRead": 100, "cacheWrite": 0,
                          "cost": {"total": 0.0125}},
                "content": [
                    {"type": "thinking", "thinking": "let me think about this"},
                    {"type": "text", "text": "Here's my answer"},
                    {"type": "toolCall", "name": "Bash"},
                ],
                "stopReason": "end_turn",
            },
        },
        "cost_usd": 0.0125, "token_count": 1550, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/component/brain")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["total"] == 1
    assert body["calls"][0]["model"] == "claude-opus-4-7"
    assert body["calls"][0]["thinking"] is True
    assert "Bash" in body["calls"][0]["tools_used"]
    assert body["stats"]["today_calls"] == 1
    assert body["stats"]["thinking_calls"] == 1
    assert body["stats"]["model"] == "claude-opus-4-7"


def test_components_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    """No CLAWMETRY_LOCAL_STORE_READ → fast path never runs even with
    a populated events store."""
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=False)
    import routes.components as comp_mod
    importlib.reload(comp_mod)
    store = ls.get_store()
    today = datetime.now().strftime("%Y-%m-%d")
    store.ingest({
        "id": "ev-noflag-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-x", "event_type": "tool_call",
        "ts": f"{today}T10:00:00Z",
        "data": {"name": "exec", "arguments": {"command": "ls"}},
        "cost_usd": 0.0, "token_count": 0, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    a = Flask(__name__)
    a.register_blueprint(comp_mod.bp_components)
    r = a.test_client().get("/api/component/tool/exec")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ── autonomy: /api/autonomy ───────────────────────────────────────────────


@pytest.fixture
def autonomy_app(tmp_path, monkeypatch):
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=True)
    import routes.autonomy as aut_mod
    importlib.reload(aut_mod)
    # Reset the in-process cache so each test gets a fresh compute.
    aut_mod._AUTONOMY_CACHE["data"] = None
    aut_mod._AUTONOMY_CACHE["ts"] = 0.0
    a = Flask(__name__)
    a.register_blueprint(aut_mod.bp_autonomy)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_autonomy_fast_path_returns_local_aggregates(autonomy_app):
    a, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    # Three user messages in one session within the last day → real gaps.
    for i, gap_min in enumerate([0, 30, 90]):
        store.ingest({
            "id": f"ev-aut-{i}", "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-aut-1", "event_type": "message",
            "ts": _iso(now - 86400 + (gap_min * 60)),
            "data": {"message": {"role": "user", "content": [{"type": "text", "text": f"hi {i}"}]}},
            "cost_usd": 0.0, "token_count": 0, "model": "",
        })
    # One "no-nudge" session — single user message → counts toward autonomy ratio.
    store.ingest({
        "id": "ev-aut-noNudge", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-aut-2", "event_type": "message",
        "ts": _iso(now - 3600),
        "data": {"message": {"role": "user", "content": [{"type": "text", "text": "go"}]}},
        "cost_usd": 0.0, "token_count": 0, "model": "",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/autonomy")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["samples_7d"] == 4
    assert body["score"] is not None
    # 1 of 2 sessions was no-nudge → ratio ~0.5
    assert body["autonomy_ratio_7d"] == 0.5
    assert isinstance(body["series_daily"], list)
    assert len(body["series_daily"]) == 7  # 7-day window


def test_autonomy_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=False)
    import routes.autonomy as aut_mod
    importlib.reload(aut_mod)
    aut_mod._AUTONOMY_CACHE["data"] = None
    aut_mod._AUTONOMY_CACHE["ts"] = 0.0
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-aut-noflag", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-noflag", "event_type": "message",
        "ts": _iso(now - 3600),
        "data": {"message": {"role": "user", "content": [{"type": "text", "text": "x"}]}},
        "cost_usd": 0.0, "token_count": 0, "model": "",
    })
    _wait_flush(store)
    a = Flask(__name__)
    a.register_blueprint(aut_mod.bp_autonomy)
    # The legacy path needs `dashboard.SESSIONS_DIR`; this path won't have one
    # so it returns the empty response (no `_source` tag either way).
    r = a.test_client().get("/api/autonomy")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass


# ── advisor: /api/advisor/ask, /api/advisor/status ────────────────────────


@pytest.fixture
def advisor_app(tmp_path, monkeypatch):
    # Block advisor from making outbound LLM calls — clear ANTHROPIC_API_KEY
    # so the auth probe returns "no_auth" deterministically.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=True)
    import routes.advisor as adv_mod
    importlib.reload(adv_mod)
    a = Flask(__name__)
    a.register_blueprint(adv_mod.bp_advisor)
    yield a, ls, adv_mod
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_advisor_status_fast_path_returns_local_tag(advisor_app):
    a, _ls, _adv = advisor_app
    c = a.test_client()
    r = c.get("/api/advisor/status")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    # Auth presence still surfaced — we cleared ANTHROPIC_API_KEY in the
    # fixture so the probe should report no auth (model field stays).
    assert "model" in body


def test_advisor_gather_context_fast_path(advisor_app):
    """The internal context-gather is the load-bearing piece of /ask. We
    test it directly because the endpoint itself short-circuits on
    no_auth before the LLM call (which is the expected runtime path
    when ANTHROPIC_API_KEY isn't set)."""
    _a, ls, adv_mod = advisor_app
    store = ls.get_store()
    now = time.time()
    for i in range(3):
        store.ingest({
            "id": f"ev-adv-{i}", "node_id": "agent+test", "agent_id": "main",
            "session_id": f"sess-adv-{i}", "event_type": "tool_call",
            "ts": _iso(now - i * 60),
            "data": {"name": "Bash", "input": f"echo {i}"},
            "cost_usd": 0.0005 * (i + 1), "token_count": 25 * (i + 1),
            "model": "claude-opus-4-7",
        })
    _wait_flush(store)

    ctx = adv_mod._gather_context(limit_events=10)
    assert ctx.get("_source") == "local_store"
    assert isinstance(ctx.get("events"), list)
    assert len(ctx["events"]) >= 3
    assert ctx["usage"]["total_sessions"] >= 3
    assert isinstance(ctx.get("recent_sessions"), list)


def test_advisor_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=False)
    import routes.advisor as adv_mod
    importlib.reload(adv_mod)
    a = Flask(__name__)
    a.register_blueprint(adv_mod.bp_advisor)
    r = a.test_client().get("/api/advisor/status")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── reasoning: /api/reasoning ─────────────────────────────────────────────


@pytest.fixture
def reasoning_app(tmp_path, monkeypatch):
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=True)
    import routes.reasoning as rea_mod
    importlib.reload(rea_mod)
    a = Flask(__name__)
    a.register_blueprint(rea_mod.bp_reasoning)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_reasoning_fast_path_returns_chains(reasoning_app):
    a, ls = reasoning_app
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-rea-1", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-rea", "event_type": "message",
        "ts": _iso(now - 60),
        "data": {
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking":
                        "The user wants to refactor the function. "
                        "Let me try a cleaner approach.\n\n"
                        "If I extract the helper, the test stays small. "
                        "So I'll do that."},
                    {"type": "text", "text": "Here's the refactor."},
                ],
            },
        },
        "cost_usd": 0.01, "token_count": 200, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/reasoning?session=sess-rea")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()
    assert body.get("_source") == "local_store"
    assert body["session_id"] == "sess-rea"
    assert body["summary"]["chain_count"] == 1
    assert body["chains"][0]["thinking_tokens"] > 0
    assert isinstance(body["chains"][0]["steps"], list) and body["chains"][0]["steps"]


def test_reasoning_fast_path_disabled_without_flag(tmp_path, monkeypatch):
    ls = _reload_local_store(monkeypatch, tmp_path, fast_path=False)
    import routes.reasoning as rea_mod
    importlib.reload(rea_mod)
    store = ls.get_store()
    now = time.time()
    store.ingest({
        "id": "ev-rea-noflag", "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-rea-noflag", "event_type": "message",
        "ts": _iso(now - 60),
        "data": {
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "thinking", "thinking": "The user wants help."},
                    {"type": "text", "text": "Sure."},
                ],
            },
        },
        "cost_usd": 0.0, "token_count": 50, "model": "claude-opus-4-7",
    })
    _wait_flush(store)
    a = Flask(__name__)
    a.register_blueprint(rea_mod.bp_reasoning)
    r = a.test_client().get("/api/reasoning?session=sess-rea-noflag")
    body = r.get_json() or {}
    assert body.get("_source") != "local_store"
    try:
        store.stop(flush=True)
    except Exception:
        pass
