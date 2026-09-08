"""``GET /api/otel/export?shape=sessions`` — the eval-stack export.

The event shape says what happened; the session shape says how it went and
what it cost, which is what Braintrust / Langfuse / Arize actually score on.
Exporting those fields is the deliberate alternative to building a competing
evaluation view.

Also pins the runtime-attribution fix. The exported stream used to stamp
``agent_type: "openclaw"`` on every record, because ``sessions.agent_type``
is a legacy column ``upsert_sessions`` hardcodes — so a customer piping us
into Datadog saw their Claude Code and Codex fleets labelled OpenClaw. Same
class of bug as the hosted Activity feed's runtime prefix
(``reference_brain_cloud_shape_loses_runtime_prefix``).
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask

import routes.otel_export as O


@pytest.fixture
def grace(monkeypatch, tmp_path):
    """Grace mode — the entitlement gate passes every feature key through."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _app():
    app = Flask(__name__)
    app.register_blueprint(O.bp_otel_export)
    return app


def _attrs(record):
    """OTLP attribute list → a plain dict of the values."""
    out = {}
    for a in record["attributes"]:
        (kind, val), = a["value"].items()
        out[a["key"]] = val
    return out


# ── runtime attribution ─────────────────────────────────────────────────────


def test_runtime_comes_from_the_session_id_prefix():
    assert O._runtime_of("openclaw", "claude_code:abc123") == "claude_code"
    assert O._runtime_of(None, "codex:xyz") == "codex"


def test_bare_session_id_stays_openclaw():
    """OpenClaw writes unprefixed ids; that's the one runtime the legacy
    ``agent_type`` value was ever right about."""
    assert O._runtime_of("openclaw", "abc123") == "openclaw"
    assert O._runtime_of(None, None) == "openclaw"


def test_legacy_agent_type_never_overrides_the_prefix():
    """The regression this fixes: every row carries agent_type=openclaw."""
    rec = O._session_to_log_record(
        {"session_id": "cursor:s1", "agent_type": "openclaw",
         "outcome": "success"}
    )
    a = _attrs(rec)
    assert a["runtime"] == "cursor"
    assert a["agent_type"] == "cursor"


def test_event_records_carry_the_runtime_too():
    rec = O._event_to_log_record(
        {"session_id": "codex:e1", "event_type": "tool_call",
         "agent_type": "openclaw"}
    )
    assert _attrs(rec)["runtime"] == "codex"


# ── the evaluation fields ───────────────────────────────────────────────────


def test_session_record_carries_outcome_cost_and_tokens():
    rec = O._session_to_log_record({
        "session_id": "claude_code:s1",
        "title": "Fix the flaky test",
        "outcome": "success",
        "outcome_confidence": 0.9,
        "cost_usd": 0.42,
        "total_tokens": 12345,
        "started_at": "2026-08-24T10:00:00Z",
        "last_active_at": "2026-08-24T10:05:30Z",
    })
    a = _attrs(rec)
    assert a["outcome"] == "success"
    assert a["outcome_confidence"] == 0.9
    assert a["cost_usd"] == 0.42
    assert a["total_tokens"] == "12345"   # OTLP intValue is a string
    assert a["duration_sec"] == 330.0
    assert a["session_title"] == "Fix the flaky test"
    assert rec["body"]["stringValue"] == "session.success"


def test_failed_sessions_map_to_otel_error_severity():
    """So a Datadog / Grafana monitor works without the operator writing an
    attribute filter first."""
    for outcome in ("failed", "cognitive_loop", "tool_call_stuck"):
        rec = O._session_to_log_record({"session_id": "s", "outcome": outcome})
        assert rec["severityText"] == "ERROR", outcome
    assert O._session_to_log_record(
        {"session_id": "s", "outcome": "escalated"})["severityText"] == "WARN"
    assert O._session_to_log_record(
        {"session_id": "s", "outcome": "success"})["severityText"] == "INFO"


def test_missing_fields_are_omitted_not_zeroed():
    """A record with no cost must not claim the session was free."""
    a = _attrs(O._session_to_log_record({"session_id": "s1"}))
    assert "cost_usd" not in a
    assert "total_tokens" not in a
    assert "duration_sec" not in a
    assert a["outcome"] == "unknown"


def test_unparseable_timestamps_never_raise():
    rec = O._session_to_log_record({
        "session_id": "s1", "outcome": "success",
        "started_at": "not-a-date", "last_active_at": "also-not",
    })
    assert rec["timeUnixNano"] == "0"
    assert "duration_sec" not in _attrs(rec)


def test_negative_duration_is_dropped():
    """Clock skew shouldn't publish a session that ended before it started."""
    rec = O._session_to_log_record({
        "session_id": "s1", "outcome": "success",
        "started_at": "2026-08-24T10:05:00Z",
        "ended_at": "2026-08-24T10:00:00Z",
    })
    assert "duration_sec" not in _attrs(rec)


# ── the route ───────────────────────────────────────────────────────────────


def test_sessions_shape_returns_session_records(grace, monkeypatch):
    monkeypatch.setattr(
        O, "_fetch_sessions",
        lambda limit, window, runtime: [
            {"session_id": "codex:s1", "outcome": "failed", "cost_usd": 1.5},
        ],
    )
    with _app().test_client() as c:
        body = c.get("/api/otel/export?shape=sessions").get_json()
    scope_logs = body["resourceLogs"][0]["scopeLogs"][0]
    assert scope_logs["scope"]["name"] == "clawmetry.sessions"
    rec = scope_logs["logRecords"][0]
    assert rec["body"]["stringValue"] == "session.failed"
    assert _attrs(rec)["runtime"] == "codex"


def test_default_shape_is_still_events(grace, monkeypatch):
    """Back-compat: existing collectors polling the bare URL keep working."""
    monkeypatch.setattr(O, "_fetch_events", lambda limit: [
        {"session_id": "s1", "event_type": "tool_call"},
    ])
    monkeypatch.setattr(
        O, "_fetch_sessions",
        lambda *a, **k: pytest.fail("session fetch ran for the default shape"),
    )
    with _app().test_client() as c:
        body = c.get("/api/otel/export").get_json()
    scope = body["resourceLogs"][0]["scopeLogs"][0]["scope"]["name"]
    assert scope == "clawmetry.events"


def test_window_and_runtime_reach_the_fetch(grace, monkeypatch):
    seen = {}

    def _fake(limit, window, runtime):
        seen.update(limit=limit, window=window, runtime=runtime)
        return []

    monkeypatch.setattr(O, "_fetch_sessions", _fake)
    with _app().test_client() as c:
        c.get("/api/otel/export?shape=sessions&window=30d"
              "&runtime=claude_code&limit=50")
    assert seen == {"limit": 50, "window": "30d", "runtime": "claude_code"}


def test_empty_result_is_a_valid_envelope(grace, monkeypatch):
    """No sessions yet must still be well-formed OTLP, not a 500."""
    monkeypatch.setattr(O, "_fetch_sessions", lambda *a, **k: [])
    with _app().test_client() as c:
        r = c.get("/api/otel/export?shape=sessions")
        assert r.status_code == 200
        assert r.get_json()["resourceLogs"][0]["scopeLogs"][0]["logRecords"] == []
