"""Unit + integration tests for the Hallucination Risk Indicator (#567).

The score combines three signals (temperature, token entropy, response
length) into a Low / Medium / High label that the Brain tab paints next
to every assistant chip. These tests pin the contract for:

  1. ``clawmetry.risk.compute_hallucination_risk`` — pure scoring fn.
  2. ``clawmetry.risk.is_llm_event``               — event-type filter.
  3. ``/api/brain-history``                        — risk field on the wire.

Parametrized matrix in ``test_compute_hallucination_risk_table`` keeps
the band thresholds explicit so a future tuning change has to update the
table on purpose.
"""

from __future__ import annotations

import importlib
import time

import pytest
from flask import Flask

from clawmetry.risk import (
    compute_hallucination_risk,
    is_llm_event,
    session_has_high_risk,
)


# ── 1. Pure-function scoring matrix ───────────────────────────────────────


@pytest.mark.parametrize(
    "name,event,expected_level",
    [
        # ── Single-signal cases ───────────────────────────────────────────
        # T very low, short output → low risk.
        (
            "low_temp_short_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.1}, "usage": {"output_tokens": 100}},
            },
            "low",
        ),
        # T moderate, short output → one signal contributes +1 → low band.
        (
            "moderate_temp_short_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.5}, "usage": {"output_tokens": 100}},
            },
            "low",
        ),
        # T high alone (short output) → +2 → just trips medium band.
        (
            "high_temp_short_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.9}, "usage": {"output_tokens": 100}},
            },
            "medium",
        ),
        # Long output alone, low T → +2 → medium band.
        (
            "low_temp_very_long_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.1}, "usage": {"output_tokens": 2500}},
            },
            "medium",
        ),
        # ── Compound risk cases ───────────────────────────────────────────
        # High T + very long output → +2 +2 → high band.
        (
            "high_temp_very_long_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.9}, "usage": {"output_tokens": 2500}},
            },
            "high",
        ),
        # Medium T + medium length → +1 +1 → medium band.
        (
            "medium_temp_medium_output",
            {
                "type": "AGENT",
                "data": {"params": {"temperature": 0.5}, "usage": {"output_tokens": 1000}},
            },
            "medium",
        ),
        # ── Graceful degradation ──────────────────────────────────────────
        # No temperature, no usage — backend should NOT crash and should
        # return a stable low label with an explanatory tooltip.
        (
            "no_signals_available",
            {"type": "AGENT", "data": {}},
            "low",
        ),
        # Has output length signal only (very long) → +2 → medium.
        (
            "only_output_length_signal_long",
            {"type": "AGENT", "data": {"usage": {"output_tokens": 5000}}},
            "medium",
        ),
        # Has temperature signal only (high) → +2 → medium.
        (
            "only_temperature_signal_high",
            {"type": "AGENT", "data": {"params": {"temperature": 1.0}}},
            "medium",
        ),
        # ── Logprobs (when present, as a pre-computed scalar) ─────────────
        # Low confidence (high mean-neg-logprob) + high T + long → high band.
        (
            "logprobs_low_confidence_plus_high_temp",
            {
                "type": "AGENT",
                "mean_neg_logprob": 1.5,
                "data": {"params": {"temperature": 0.9}, "usage": {"output_tokens": 1500}},
            },
            "high",
        ),
    ],
)
def test_compute_hallucination_risk_table(name, event, expected_level):
    """Per-signal + compound matrix for ``compute_hallucination_risk``."""
    out = compute_hallucination_risk(event)
    assert isinstance(out, dict), f"[{name}] expected dict, got {type(out)}"
    assert set(out.keys()) >= {"risk_level", "risk_explanation"}, (
        f"[{name}] missing required keys: {out}"
    )
    assert out["risk_level"] == expected_level, (
        f"[{name}] expected {expected_level!r}, got {out['risk_level']!r}. "
        f"Explanation: {out['risk_explanation']}"
    )
    assert isinstance(out["risk_explanation"], str), (
        f"[{name}] explanation must be a string, got {type(out['risk_explanation'])}"
    )
    assert out["risk_explanation"], f"[{name}] explanation must be non-empty"


def test_compute_hallucination_risk_never_raises_on_garbage():
    """Bad inputs must return a sensible default, never raise."""
    for garbage in (None, 42, "string", [], object(), {"type": "AGENT", "data": "not-a-dict"}):
        out = compute_hallucination_risk(garbage)
        assert isinstance(out, dict)
        assert out["risk_level"] in ("low", "medium", "high")
        assert isinstance(out["risk_explanation"], str)


def test_compute_hallucination_risk_non_llm_event_is_low():
    """USER / EXEC / READ events should not get a risk score above low."""
    for evt_type in ("USER", "EXEC", "READ", "WRITE", "BROWSER", "RESULT"):
        out = compute_hallucination_risk(
            {"type": evt_type, "data": {"params": {"temperature": 1.0}}}
        )
        assert out["risk_level"] == "low", (
            f"{evt_type}: non-LLM event got bumped to {out['risk_level']!r}"
        )
        assert "not an llm call" in out["risk_explanation"].lower(), out


def test_is_llm_event_recognises_all_known_shapes():
    """``is_llm_event`` must accept dashboard, local-store, and JSONL shapes."""
    assert is_llm_event({"type": "AGENT"})
    assert is_llm_event({"type": "THINK"})
    assert is_llm_event({"event_type": "model.completed"})
    assert is_llm_event({"event_type": "MODEL.COMPLETED"})
    assert is_llm_event({"role": "assistant"})
    # Negatives
    assert not is_llm_event({"type": "USER"})
    assert not is_llm_event({"type": "EXEC"})
    assert not is_llm_event({})
    assert not is_llm_event(None)


def test_session_has_high_risk_helper():
    """Convenience helper used by the sessions-list renderer."""
    events = [
        {"risk": {"risk_level": "low"}},
        {"risk": {"risk_level": "medium"}},
    ]
    assert not session_has_high_risk(events)
    events.append({"risk": {"risk_level": "high"}})
    assert session_has_high_risk(events)
    # Missing risk dict on every event → False, never raises.
    assert not session_has_high_risk([{"type": "USER"}, {"type": "EXEC"}])
    assert not session_has_high_risk([])
    assert not session_has_high_risk(None)


# ── 2. Brain-history integration: risk on the wire ───────────────────────


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


@pytest.fixture
def brain_app(tmp_path, monkeypatch):
    """Isolated Flask app + tmp DuckDB with the fast path enabled.

    Mirrors ``tests/test_brain_history_v3_event_detail.py``'s harness so
    we can assert risk-field presence on the same code path the
    dashboard hits in production.
    """
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(
        lq, "_DISCOVERY_PATH", str(tmp_path / "local_query_absent.json"),
    )
    import routes.brain as br
    importlib.reload(br)

    import dashboard as _d
    monkeypatch.setattr(_d, "_is_pro_user", lambda: True)

    app = Flask(__name__)
    app.register_blueprint(br.bp_brain)
    yield app, ls, br
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def test_brain_history_includes_risk_on_llm_events(brain_app):
    """Three seeded rows: low/medium/high. Each comes back with the
    matching ``risk.risk_level`` and a non-empty explanation."""
    app, ls, _br = brain_app
    store = ls.get_store()

    rows = [
        # Low risk: T=0.2, 100 output tokens.
        {
            "id": "ev-low",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-low", "event_type": "model.completed",
            "ts": "2026-05-16T12:00:01Z",
            "data": {
                "completionText": "Short low-temp reply.",
                "params": {"temperature": 0.2},
                "usage": {"output_tokens": 100},
            },
        },
        # Medium: T=0.9, 100 tokens → +2 +0 → medium.
        {
            "id": "ev-medium",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-medium", "event_type": "model.completed",
            "ts": "2026-05-16T12:00:02Z",
            "data": {
                "completionText": "Short high-temp reply.",
                "params": {"temperature": 0.9},
                "usage": {"output_tokens": 100},
            },
        },
        # High: T=0.9, 3000 tokens → +2 +2 → high.
        {
            "id": "ev-high",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-high", "event_type": "model.completed",
            "ts": "2026-05-16T12:00:03Z",
            "data": {
                "completionText": "Very long, very creative reply." * 20,
                "params": {"temperature": 0.9},
                "usage": {"output_tokens": 3000},
            },
        },
        # Non-LLM event: tool result. Should NOT carry a risk field.
        {
            "id": "ev-tool",
            "node_id": "agent+test", "agent_id": "main",
            "session_id": "sess-high", "event_type": "tool.result",
            "ts": "2026-05-16T12:00:04Z",
            "data": {"output": "tool result body"},
        },
    ]
    for r in rows:
        store.ingest(r)
    _wait_flush(store)

    body = app.test_client().get("/api/brain-history?limit=20").get_json()
    assert body["count"] >= 4, body

    by_session = {ev.get("sessionId"): ev for ev in body["events"]}

    low = by_session.get("sess-low")
    assert low is not None, body
    assert "risk" in low, f"LLM event missing risk field: {low}"
    assert low["risk"]["risk_level"] == "low", low["risk"]
    assert low["risk"]["risk_explanation"], low["risk"]

    medium = by_session.get("sess-medium")
    assert medium is not None, body
    assert medium["risk"]["risk_level"] == "medium", medium["risk"]

    high = by_session.get("sess-high")
    # Two events for sess-high; the model.completed should win the by-session
    # map first (insertion order) — but iterate to find the LLM one.
    high_evs = [
        e for e in body["events"]
        if e.get("sessionId") == "sess-high"
        and (e.get("type") or "").upper() == "MODEL.COMPLETED"
    ]
    assert high_evs, body
    assert high_evs[0]["risk"]["risk_level"] == "high", high_evs[0]["risk"]

    # Tool-result event must NOT carry a risk field (per contract: only
    # LLM-call events get scored).
    tool_evs = [
        e for e in body["events"]
        if (e.get("type") or "").upper() == "TOOL.RESULT"
    ]
    assert tool_evs, body
    assert "risk" not in tool_evs[0], (
        f"non-LLM tool.result event should not carry risk: {tool_evs[0]}"
    )
