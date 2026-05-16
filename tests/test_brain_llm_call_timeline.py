"""Tests for /api/llm-call-timeline/<event_id> (issue #568).

The endpoint returns a per-call phase breakdown so the Brain tab can
visualise the LLM call lifecycle as a horizontal timeline. Two shapes:

  * Reasoning model — 5-phase output (prompt_received,
    reasoning_started, reasoning_completed, first_output_token,
    completion).
  * Non-reasoning model — 3-phase collapse (prompt_received,
    first_output_token, completion). first_output_token is synthesised
    from completion_tokens when no streaming markers exist.

The fixture seeds a synthetic OpenClaw v3 chain (prompt.submitted →
trace.artifacts → model.completed) into a real DuckDB store, then calls
the endpoint and asserts the response shape + ordering.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def app(tmp_path, monkeypatch):
    """Isolated Flask app + tmp DuckDB. Daemon-proxy disabled by pointing
    the discovery file at a non-existent path, so reads hit the fixture
    store directly via local_store.get_store(read_only=True).
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "local_query_absent.json"),
    )
    import routes.brain as br
    importlib.reload(br)

    a = Flask(__name__)
    a.register_blueprint(br.bp_brain)
    yield a, ls, br
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── Reasoning model: 5-phase chain ─────────────────────────────────────────


def test_timeline_returns_five_phases_for_reasoning_model(app):
    a, ls, _br = app
    store = ls.get_store()
    # Synthetic chain mimicking real v3 ingest:
    #   t+0ms   prompt.submitted
    #   t+150ms trace.artifacts (reasoning start)
    #   t+4350ms trace.artifacts (reasoning end)
    #   t+6750ms model.completed
    rows = [
        ("ev-prompt-1", "prompt.submitted", "2026-05-13T12:00:00.000Z",
         {"finalPromptText": "Plan a deployment strategy"}),
        ("ev-reason-1", "trace.artifacts", "2026-05-13T12:00:00.150Z",
         {"kind": "reasoning",
          "artifacts": [{"type": "thinking", "text": "let me think"}]}),
        ("ev-reason-2", "trace.artifacts", "2026-05-13T12:00:04.350Z",
         {"kind": "reasoning",
          "artifacts": [{"type": "thinking", "text": "conclusion follows"}]}),
        ("ev-complete-1", "model.completed", "2026-05-13T12:00:06.750Z",
         {"completionText": "Here is the plan",
          "modelId": "claude-opus-4-7",
          "usage": {"output_tokens": 240}}),
    ]
    for eid, etype, ts, data in rows:
        store.ingest({
            "id": eid, "node_id": "n1", "agent_id": "main",
            "session_id": "sess-r1", "event_type": etype, "ts": ts,
            "data": data, "cost_usd": 0.0,
            "token_count": data.get("usage", {}).get("output_tokens") or 0,
            "model": data.get("modelId") or "claude-opus-4-7",
        })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/llm-call-timeline/ev-complete-1?session_id=sess-r1")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert body["event_id"] == "ev-complete-1"
    assert body["session_id"] == "sess-r1"
    assert body["reasoning"] is True
    assert body["phase_count"] == 5
    assert body["model"] == "claude-opus-4-7"

    phase_names = [p["phase"] for p in body["phases"]]
    assert phase_names == [
        "prompt_received",
        "reasoning_started",
        "reasoning_completed",
        "first_output_token",
        "completion",
    ]
    # Phase ms values are monotonically non-decreasing (chronological).
    ms_values = [p["ms"] for p in body["phases"]]
    assert ms_values == sorted(ms_values), \
        f"phases not chronological: {ms_values}"
    # prompt_received is the origin (0).
    assert ms_values[0] == 0
    # Total span matches the prompt→completion ms (6750ms ±5ms).
    assert 6700 <= body["total_ms"] <= 6800
    # Reasoning_completed lands at +4200ms (4350 - 150) ±5ms ... wait, we
    # measure from prompt origin not reasoning start. 4350 - 0 = 4350ms.
    reasoning_completed = next(
        p for p in body["phases"] if p["phase"] == "reasoning_completed"
    )
    assert 4300 <= reasoning_completed["ms"] <= 4400
    # first_output_token falls between reasoning_completed and completion.
    first_tok = next(p for p in body["phases"] if p["phase"] == "first_output_token")
    completion = next(p for p in body["phases"] if p["phase"] == "completion")
    assert reasoning_completed["ms"] <= first_tok["ms"] <= completion["ms"]


# ── Non-reasoning model: 3-phase collapse ──────────────────────────────────


def test_timeline_collapses_to_three_phases_when_no_reasoning(app):
    a, ls, _br = app
    store = ls.get_store()
    # Synthetic chain WITHOUT any reasoning artifacts — Sonnet without
    # extended-thinking, Haiku, GPT-4 etc.
    rows = [
        ("ev-prompt-2", "prompt.submitted", "2026-05-13T12:10:00.000Z",
         {"finalPromptText": "What is 2+2?"}),
        ("ev-complete-2", "model.completed", "2026-05-13T12:10:01.200Z",
         {"completionText": "4",
          "modelId": "claude-haiku-3-5",
          "usage": {"output_tokens": 8}}),
    ]
    for eid, etype, ts, data in rows:
        store.ingest({
            "id": eid, "node_id": "n1", "agent_id": "main",
            "session_id": "sess-nr1", "event_type": etype, "ts": ts,
            "data": data, "cost_usd": 0.0,
            "token_count": data.get("usage", {}).get("output_tokens") or 0,
            "model": data.get("modelId") or "claude-haiku-3-5",
        })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/llm-call-timeline/ev-complete-2?session_id=sess-nr1")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    body = r.get_json()

    assert body["reasoning"] is False
    assert body["phase_count"] == 3
    phase_names = [p["phase"] for p in body["phases"]]
    assert phase_names == [
        "prompt_received",
        "first_output_token",
        "completion",
    ]
    # Total span ≈ 1200ms.
    assert 1100 <= body["total_ms"] <= 1300
    # first_output_token is flagged as estimated since no streaming marker
    # exists in the chain.
    first_tok = next(p for p in body["phases"] if p["phase"] == "first_output_token")
    assert first_tok.get("estimated") is True


# ── Error paths ────────────────────────────────────────────────────────────


def test_timeline_404_for_unknown_event_id(app):
    a, ls, _br = app
    store = ls.get_store()
    # Seed *something* so the local-store path isn't unavailable.
    store.ingest({
        "id": "ev-unrelated", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-other", "event_type": "prompt.submitted",
        "ts": "2026-05-13T12:00:00Z",
        "data": {"finalPromptText": "hi"}, "cost_usd": 0.0,
        "token_count": 0, "model": "claude-opus-4-7",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/llm-call-timeline/does-not-exist?session_id=sess-other")
    assert r.status_code == 404


def test_timeline_400_when_anchor_is_not_an_llm_call(app):
    a, ls, _br = app
    store = ls.get_store()
    store.ingest({
        "id": "ev-tool-result", "node_id": "n1", "agent_id": "main",
        "session_id": "sess-tool", "event_type": "tool.result",
        "ts": "2026-05-13T12:00:00Z",
        "data": {"output": "ok"}, "cost_usd": 0.0,
        "token_count": 0, "model": "",
    })
    _wait_flush(store)

    c = a.test_client()
    r = c.get("/api/llm-call-timeline/ev-tool-result?session_id=sess-tool")
    assert r.status_code == 400


# ── Helper unit tests (pure functions) ─────────────────────────────────────


def test_parse_iso_ts_handles_z_and_offset():
    from routes.brain import _parse_iso_ts
    assert _parse_iso_ts("2026-05-13T12:00:00Z") == _parse_iso_ts(
        "2026-05-13T12:00:00+00:00"
    )
    assert _parse_iso_ts(None) is None
    assert _parse_iso_ts("") is None
    assert _parse_iso_ts("not a date") is None


def test_is_reasoning_event_detects_v3_and_legacy_shapes():
    from routes.brain import _is_reasoning_event
    # v3 mapper shape
    assert _is_reasoning_event({
        "event_type": "trace.artifacts",
        "data": {"kind": "reasoning"},
    })
    # legacy thinking event
    assert _is_reasoning_event({
        "event_type": "thinking",
        "data": {},
    })
    # legacy block-list shape
    assert _is_reasoning_event({
        "event_type": "assistant",
        "data": {"message": {"role": "assistant",
                              "content": [{"type": "thinking", "thinking": "..."}]}},
    })
    # Non-reasoning rows
    assert not _is_reasoning_event({
        "event_type": "prompt.submitted", "data": {},
    })
    assert not _is_reasoning_event({
        "event_type": "tool.call", "data": {},
    })
