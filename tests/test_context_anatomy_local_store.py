"""Tier-1 DuckDB fast path for /api/context-anatomy session-history bucket.

The endpoint historically scanned the 5 most-recent session JSONL files
on every request to find the last non-zero ``usage.input_tokens`` reading
(an estimate of the live conversation's running context size).

This test asserts:
  1. Unit — when the local DuckDB has message events with non-zero
     ``usage.input_tokens``, the route returns a "Session history"
     bucket sized to the LAST per-turn reading from the most-recent
     session (not summed across turns, not from older sessions).
  2. E2E — synthetic OpenClaw-shaped events round-trip:
        ingest -> DuckDB -> /api/context-anatomy -> bucket value
     Both ``usage.input`` (OpenClaw native) and ``usage.input_tokens``
     (Anthropic SDK echo) are accepted.
  3. Fallback — empty store + empty workspace -> bucket absent (no
     synthetic data, no crash).
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


# ── fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Flask app with bp_config registered, fresh DuckDB per test."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic isolation: on a dev machine with the sync daemon running,
    # ~/.clawmetry/local_query.json trips _daemon_registered() and steers
    # get_store() to a _ProxyStore that forwards into the developer's REAL
    # DuckDB (the test would then read live sessions, not the tmp_path
    # fixture). Force the writer-owner path + stub the discovery hooks so
    # every read opens the tmp_path store in-process. Matches CI, where no
    # daemon runs.
    ls.mark_writer_owner()
    import routes.local_query as _lq
    monkeypatch.setattr(_lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(_lq, "_cached_discovery", lambda: None)
    # Point WORKSPACE/SESSIONS_DIR at empty tmp dirs so the legacy JSONL
    # fallback has nothing to find — proves the fast path is really
    # what's populating the bucket.
    import dashboard as _d
    monkeypatch.setattr(_d, "WORKSPACE", str(tmp_path / "ws"), raising=False)
    monkeypatch.setattr(_d, "SESSIONS_DIR", str(tmp_path / "sessions"), raising=False)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    a = Flask(__name__)
    a.register_blueprint(infra_mod.bp_config)
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


def _ingest_message(store, *, sid: str, ts: str, input_tokens: int,
                    field: str = "input_tokens", ev_id: str | None = None):
    """Insert one OpenClaw-shaped message event into the local store.

    ``field`` selects the JSON path used to expose the token count —
    ``input_tokens`` mirrors the Anthropic SDK echo (legacy scanner only
    handled this), ``input`` mirrors OpenClaw's native JSONL.
    """
    if ev_id is None:
        ev_id = f"msg-{sid}-{ts}-{input_tokens}"
    usage: dict = {field: input_tokens, "output_tokens": 50}
    store.ingest({
        "id":         ev_id,
        "node_id":    "agent+test",
        "agent_id":   "main",
        "session_id": sid,
        "event_type": "message",
        "ts":         ts,
        "data":       {"message": {"role": "assistant", "usage": usage}},
        "cost_usd":   0.001,
        "token_count": input_tokens,
        "model":      "claude-opus-4-7",
    })


# ── E2E: synthetic OpenClaw events round-trip through DuckDB ──────────────


def test_context_anatomy_session_history_from_local_store(app):
    """Insert messages with monotonically growing input_tokens — the
    bucket must reflect the LAST reading (most recent turn), not a
    sum, not the first reading."""
    a, ls = app
    store = ls.get_store()
    # Three turns in the same session, growing context
    _ingest_message(store, sid="sess-active", ts="2026-05-15T10:00:00Z", input_tokens=12_000)
    _ingest_message(store, sid="sess-active", ts="2026-05-15T10:01:00Z", input_tokens=18_000)
    _ingest_message(store, sid="sess-active", ts="2026-05-15T10:02:00Z", input_tokens=24_500)
    _wait_flush(store)

    body = a.test_client().get("/api/context-anatomy").get_json()
    buckets_by_label = {b["label"]: b for b in body["buckets"]}
    assert "Session history" in buckets_by_label, (
        f"missing Session history bucket; got: {list(buckets_by_label)}"
    )
    # known_static = sum of all other buckets (Tool defs ~1500). The
    # legacy code subtracts known_static from the raw reading. We mirror
    # the assertion: bucket = max(0, 24500 - sum(other_tokens)).
    other_total = sum(b["tokens"] for label, b in buckets_by_label.items()
                      if label != "Session history")
    assert buckets_by_label["Session history"]["tokens"] == max(0, 24_500 - other_total)


def test_context_anatomy_picks_most_recent_session(app):
    """Older session has higher reading; newer session has lower —
    the bucket must follow the NEWER session, not the higher number."""
    a, ls = app
    store = ls.get_store()
    # Old session (yesterday) — high reading
    _ingest_message(store, sid="sess-old", ts="2026-05-14T08:00:00Z", input_tokens=80_000)
    # New session (today) — lower reading; this is the one the user is in
    _ingest_message(store, sid="sess-new", ts="2026-05-15T11:00:00Z", input_tokens=15_000)
    _wait_flush(store)

    body = a.test_client().get("/api/context-anatomy").get_json()
    by_label = {b["label"]: b for b in body["buckets"]}
    assert "Session history" in by_label
    other = sum(b["tokens"] for lbl, b in by_label.items() if lbl != "Session history")
    assert by_label["Session history"]["tokens"] == max(0, 15_000 - other)


def test_context_anatomy_accepts_openclaw_native_field(app):
    """OpenClaw's native JSONL writes ``usage.input``; legacy scanner
    only handled ``input_tokens`` — fast path closes that gap so
    OpenClaw-only nodes (no Anthropic-SDK echo) aren't blank."""
    a, ls = app
    store = ls.get_store()
    _ingest_message(store, sid="sess-oc", ts="2026-05-15T12:00:00Z",
                    input_tokens=33_000, field="input")
    _wait_flush(store)

    body = a.test_client().get("/api/context-anatomy").get_json()
    by_label = {b["label"]: b for b in body["buckets"]}
    assert "Session history" in by_label
    other = sum(b["tokens"] for lbl, b in by_label.items() if lbl != "Session history")
    assert by_label["Session history"]["tokens"] == max(0, 33_000 - other)


def test_context_anatomy_skips_zero_readings(app):
    """A fresh assistant turn that hasn't reported tokens yet (usage=0)
    must NOT crowd out an earlier non-zero reading from the same
    session — the bucket should reflect the earlier real number."""
    a, ls = app
    store = ls.get_store()
    _ingest_message(store, sid="sess-mix", ts="2026-05-15T09:00:00Z", input_tokens=20_000)
    _ingest_message(store, sid="sess-mix", ts="2026-05-15T09:01:00Z", input_tokens=0)
    _wait_flush(store)

    body = a.test_client().get("/api/context-anatomy").get_json()
    by_label = {b["label"]: b for b in body["buckets"]}
    assert "Session history" in by_label
    other = sum(b["tokens"] for lbl, b in by_label.items() if lbl != "Session history")
    assert by_label["Session history"]["tokens"] == max(0, 20_000 - other)


def test_context_anatomy_falls_through_when_store_empty(app):
    """No DuckDB rows + empty SESSIONS_DIR -> no Session history bucket
    (and no exception). Static buckets (Tool defs) still present."""
    a, _ls = app
    body = a.test_client().get("/api/context-anatomy").get_json()
    labels = {b["label"] for b in body["buckets"]}
    assert "Session history" not in labels
    # Static "Tool defs (est.)" bucket is unconditional.
    assert "Tool defs (est.)" in labels


# ── Unit: the LocalStore method itself ─────────────────────────────────────


def test_query_context_window_peek_returns_zero_on_empty(app):
    _a, ls = app
    store = ls.get_store()
    result = store.query_context_window_peek(scan_sessions=5)
    assert result == {"input_tokens": 0}


def test_query_context_window_peek_returns_session_id_and_ts(app):
    _a, ls = app
    store = ls.get_store()
    _ingest_message(store, sid="sess-x", ts="2026-05-15T13:00:00Z", input_tokens=42_000)
    _wait_flush(store)

    result = store.query_context_window_peek(scan_sessions=5)
    assert result["input_tokens"] == 42_000
    assert result["session_id"] == "sess-x"
    assert result["ts"] == "2026-05-15T13:00:00Z"


# ── v3 real-shape regression (issue #1385) ────────────────────────────────


def test_query_context_window_peek_v3_assistant_event(app):
    """v3 real-shape regression (#1385): real OpenClaw v3 emits
    ``event_type='assistant'`` (not ``'message'``) for the parent
    agent turn. The token count lives at
    ``data.message.usage.input_tokens`` — same as the legacy shape —
    but the predicate must also accept the new event_type. Fixture
    extracted from ``/Users/vivek/.clawmetry/clawmetry.duckdb`` on
    2026-05-15.
    """
    _a, ls = app
    store = ls.get_store()
    store.ingest({
        "id":         "v3-assistant-1",
        "node_id":    "agent+Macbook-Pro-2-local",
        "agent_id":   "main",
        "session_id": "575597e9-f609-4e88-9c12-055392f1c107",
        "event_type": "assistant",
        "ts":         "2026-05-15T22:22:09.768Z",
        # Real OpenClaw v3 ``assistant`` event payload (truncated).
        "data": {
            "type":     "assistant",
            "version":  3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens":              6,
                    "output_tokens":             108,
                    "cache_read_input_tokens":   18498,
                    "cache_creation_input_tokens": 19325,
                },
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    result = store.query_context_window_peek(scan_sessions=5)
    # Live context size = input + cache_read + cache_write (all three are
    # part of the prompt the model saw). 6 + 18498 + 19325 = 37829. The
    # old expectation of 6 (input only) under-counted cache-heavy turns —
    # see test_query_context_window_peek_sums_cache_tokens for the Claude
    # Code shape where that bug showed "2 / 200K".
    assert result["input_tokens"] == 6 + 18498 + 19325, (
        f"cache splits not summed into context size; result={result}"
    )
    assert result["session_id"] == "575597e9-f609-4e88-9c12-055392f1c107"


def test_query_context_window_peek_v3_model_completed_event(app):
    """v3 real-shape regression (#1385): OpenClaw v3 also emits a
    parallel ``model.completed`` event whose token count lives at
    ``data.promptCache.lastCallUsage.input`` — a path the legacy
    ``data.message.usage.input_tokens`` walker missed entirely.
    Fixture extracted from
    ``/Users/vivek/.clawmetry/clawmetry.duckdb`` on 2026-05-15.
    """
    _a, ls = app
    store = ls.get_store()
    store.ingest({
        "id":         "v3-mcp-1",
        "node_id":    "agent+Macbook-Pro-2-local",
        "agent_id":   "main",
        "session_id": "575597e9-f609-4e88-9c12-055392f1c107",
        "event_type": "model.completed",
        "ts":         "2026-05-15T22:22:09.768Z",
        # Real OpenClaw v3 ``model.completed`` event payload (verbatim).
        "data": {
            "type":      "model.completed",
            "modelId":   "claude-opus-4-7",
            "provider":  "claude-cli",
            "promptCache": {
                "lastCallUsage": {"input": 6, "output": 108, "total": 114},
            },
            "stopReason": "stop",
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    result = store.query_context_window_peek(scan_sessions=5)
    # lastCallUsage carries no cache split, so context size == input == 6.
    assert result["input_tokens"] == 6, (
        f"v3 model.completed event was not counted; result={result}"
    )


def test_query_context_window_peek_sums_cache_tokens(app):
    """Cache-heavy regression (surfaced 2026-05-23 verifying OSS↔cloud
    parity): a Claude Code assistant turn reports a tiny raw
    ``input_tokens`` (the un-cached delta) while the bulk of the live
    context lives in ``cache_read_input_tokens``. Reading input alone made
    ``currentContextTokens`` show 2 for a ~150K-full window → the LLM
    Context Inspector gauge read "2 / 200K (0%)". The peek must sum
    input + cache_read + cache_write so the gauge reflects the real prompt
    size. Fixture is the exact shape pulled from session
    625c0ad9 on the dev box.
    """
    _a, ls = app
    store = ls.get_store()
    store.ingest({
        "id":         "cc-cache-1",
        "node_id":    "agent+Macbook-Pro-2-local",
        "agent_id":   "main",
        "session_id": "625c0ad9-71af-4a56-9a3b-cab396860a85",
        "event_type": "assistant",
        "ts":         "2026-05-24T18:50:51.723Z",
        "data": {
            "type":    "assistant",
            "version": 3,
            "message": {
                "role":  "assistant",
                "model": "claude-opus-4-7",
                "usage": {
                    "input_tokens":                2,
                    "output_tokens":               140,
                    "cache_read_input_tokens":     148_000,
                    "cache_creation_input_tokens": 1_500,
                },
            },
        },
        "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    result = store.query_context_window_peek(scan_sessions=5)
    # 2 + 148000 + 1500 = 149502 — the real live context, not the raw 2.
    assert result["input_tokens"] == 2 + 148_000 + 1_500, (
        f"cache tokens not summed; gauge would show the bogus raw input; "
        f"result={result}"
    )
