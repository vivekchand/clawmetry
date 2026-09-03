"""Claude Code native telemetry through the OTLP receiver (WO-57).

Requirement: Claude Code Native Telemetry (a4bd3c7e). Covers
AC-RSO-CCT-001.4 (claude_code.* metrics), AC-RSO-CCT-001.5 (typed events),
AC-RSO-CCT-001.6 (tracing-beta spans + waiting-on-you), AC-RSO-CCT-001.7
(one session, two sources) and AC-RSO-CCT-001.8 (/api/otel-status).

Every payload here is OTLP/JSON with ``dashboard._HAS_OTEL_PROTO`` forced
False: that is the wire format ``clawmetry instrument claude`` configures
and it must work on a vanilla install with no ``[otel]`` extra. A private
DuckDB writer is wired in per test (same fixture shape as the WO-7 suite);
the developer's real store is never touched.
"""
from __future__ import annotations

import importlib
import json
import os
import tempfile
import time

import pytest
from flask import Flask

import dashboard as _d

_SESSION = "0f5c1c1e-7a1e-4c2a-9d0e-2b6f9c4a1234"       # bare uuid on the wire
_STORED = "claude_code:" + _SESSION                      # what the daemon stamps


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _no_proto_and_clean_cache(monkeypatch):
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", False)
    monkeypatch.setattr(_d, "metrics_store", {k: [] for k in
                        ("tokens", "cost", "runs", "messages", "webhooks", "queues")})
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()


@pytest.fixture()
def store(monkeypatch):
    _ls = importlib.import_module("clawmetry.local_store")
    tmpdir = tempfile.mkdtemp(prefix="clawmetry-wo57-")
    path = os.path.join(tmpdir, "wo57.duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", path)
    _ls._reset_singleton_for_tests()
    import pathlib
    prev = _ls.DB_PATH
    _ls.DB_PATH = pathlib.Path(path)
    st = _ls.LocalStore()
    monkeypatch.setattr(_ls, "get_store", lambda read_only=False: st)
    try:
        yield st
    finally:
        try:
            st.stop(flush=True)
        except Exception:
            pass
        _ls.DB_PATH = prev
        _ls._reset_singleton_for_tests()


@pytest.fixture()
def client(monkeypatch):
    import routes.meta as meta
    importlib.reload(meta)
    a = Flask(__name__)
    a.register_blueprint(meta.bp_otel)
    return a.test_client(), meta


# ── OTLP/JSON builders (Claude Code's actual attribute names) ───────────────

def _kv(k, v):
    if isinstance(v, bool):
        return {"key": k, "value": {"boolValue": v}}
    if isinstance(v, int):
        return {"key": k, "value": {"intValue": str(v)}}
    if isinstance(v, float):
        return {"key": k, "value": {"doubleValue": v}}
    return {"key": k, "value": {"stringValue": str(v)}}


def _resource(**extra):
    base = {"service.name": "claude-code", "service.version": "2.1.259",
            "host.name": "mac-of-dana"}
    base.update(extra)
    return {"attributes": [_kv(k, v) for k, v in base.items()]}


def _ident(**extra):
    base = {"session.id": _SESSION, "user.id": "u-42",
            "user.email": "dana@acme.example", "organization.id": "org-acme"}
    base.update(extra)
    return [_kv(k, v) for k, v in base.items()]


def _log(event_name, when_ns, **attrs):
    return {"timeUnixNano": str(when_ns), "eventName": event_name,
            "body": {"stringValue": event_name},
            "attributes": _ident() + [_kv(k, v) for k, v in attrs.items()]}


def _logs_payload(records):
    return json.dumps({"resourceLogs": [{"resource": _resource(),
                                         "scopeLogs": [{"logRecords": records}]}]}).encode()


def _metric(name, points, kind="sum"):
    dps = []
    for value, attrs in points:
        dp = {"timeUnixNano": str(int(time.time() * 1e9)),
              "attributes": _ident() + [_kv(k, v) for k, v in attrs.items()]}
        if isinstance(value, float):
            dp["asDouble"] = value
        else:
            dp["asInt"] = str(value)
        dps.append(dp)
    body = {"dataPoints": dps}
    if kind == "sum":
        body.update({"aggregationTemporality": "AGGREGATION_TEMPORALITY_DELTA",
                     "isMonotonic": True})
    return {"name": name, "unit": "1", kind: body}


def _metrics_payload(metrics):
    return json.dumps({"resourceMetrics": [{"resource": _resource(),
                                            "scopeMetrics": [{"metrics": metrics}]}]}).encode()


def _span(name, start_ns, end_ns, span_id, parent=None, **attrs):
    sp = {"traceId": "ab" * 16, "spanId": span_id, "name": name,
          "kind": "SPAN_KIND_INTERNAL",
          "startTimeUnixNano": str(start_ns), "endTimeUnixNano": str(end_ns),
          "attributes": _ident() + [_kv("span.type", name)]
          + [_kv(k, v) for k, v in attrs.items()]}
    if parent:
        sp["parentSpanId"] = parent
    return sp


def _traces_payload(spans):
    return json.dumps({"resourceSpans": [{"resource": _resource(),
                                          "scopeSpans": [{"spans": spans}]}]}).encode()


def _events(store, session_id):
    rows = store.query_events(session_id=session_id, limit=500)
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    return list(rows or [])


def _data(ev):
    d = ev.get("data")
    if isinstance(d, str):
        try:
            d = json.loads(d)
        except Exception:
            d = {}
    return d or {}


# ── AC-RSO-CCT-001.4: metrics ───────────────────────────────────────────────

def test_claude_code_metrics_decode_as_json_without_protobuf(store, client):
    """AC-RSO-CCT-001.4 -- a vanilla install (no otel extra) accepts Claude
    Code's OTLP/JSON metrics: 200, not 501.

    AC-RSO-CCT-001.4
    """
    c, _ = client
    r = c.post("/v1/metrics", data=_metrics_payload([
        _metric("claude_code.token.usage", [(1500, {"type": "input", "model": "claude-opus-4-8"})]),
    ]), content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)


def test_cache_token_types_land_in_cache_fields_and_ledger(store, client):
    """AC-RSO-CCT-001.4 -- cacheRead / cacheCreation types reach the live
    tokens cache under cache fields; input/output and cost go to the ledger
    only (the api_request log row already carries those dollars).

    AC-RSO-CCT-001.4
    """
    c, _ = client
    r = c.post("/v1/metrics", data=_metrics_payload([
        _metric("claude_code.token.usage", [
            (1500, {"type": "input", "model": "claude-opus-4-8"}),
            (300, {"type": "output", "model": "claude-opus-4-8"}),
            (42000, {"type": "cacheRead", "model": "claude-opus-4-8"}),
            (7000, {"type": "cacheCreation", "model": "claude-opus-4-8"}),
        ]),
        _metric("claude_code.cost.usage", [(4.10, {"model": "claude-opus-4-8"})]),
        _metric("claude_code.lines_of_code.count", [(120, {"type": "added"}), (8, {"type": "removed"})]),
        _metric("claude_code.commit.count", [(1, {})]),
        _metric("claude_code.pull_request.count", [(1, {})]),
        _metric("claude_code.active_time.total", [(95, {"type": "user"}), (240, {"type": "cli"})]),
        _metric("claude_code.code_edit_tool.decision", [(1, {"tool_name": "Edit", "decision": "accept", "source": "user_temporary", "language": "python"})]),
        _metric("claude_code.session.count", [(1, {"start_type": "fresh"})]),
    ]), content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)

    toks = _d.metrics_store["tokens"]
    # Same field names the transcript path writes; ``total`` stays 0 so the
    # tokens tile does not count cache reads as fresh tokens.
    assert sum(t.get("cache_read_tokens", 0) for t in toks) == 42000
    assert sum(t.get("cache_write_tokens", 0) for t in toks) == 7000
    assert sum(t.get("total", 0) for t in toks) == 0
    assert sum(t.get("input", 0) for t in toks) == 0, "input tokens are ledger-only on the metric path"
    assert _d.metrics_store["cost"] == [], "cost.usage never feeds the cost tile (api_request does)"
    usage = _d._get_otel_usage_data()
    assert usage["cacheReadTokens"] == 42000 and usage["cacheWriteTokens"] == 7000

    rows = store.query_otlp_records(limit=100)
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    names = sorted({r["event_name"] for r in rows})
    assert names == sorted({
        "claude_code.token.usage", "claude_code.cost.usage",
        "claude_code.lines_of_code.count", "claude_code.commit.count",
        "claude_code.pull_request.count", "claude_code.active_time.total",
        "claude_code.code_edit_tool.decision", "claude_code.session.count"}), names
    assert {r["session_id"] for r in rows} == {_SESSION}, "ledger keeps the id as sent"
    assert {r["agent_type"] for r in rows} == {"claude_code"}
    assert all(r.get("cost_usd") in (None, 0, 0.0) for r in rows), "metric rows must not carry cost columns"
    edit = [r for r in rows if r["event_name"] == "claude_code.code_edit_tool.decision"][0]
    assert edit["tool_name"] == "Edit" and edit["decision"] == "accept"
    # Retry is a replace, not an add: ledger AND tile.
    n_before = store.count_otlp_records()
    payload = _metrics_payload([
        _metric("claude_code.token.usage", [(5000, {"type": "cacheRead", "model": "m"})])])
    c.post("/v1/metrics", data=payload, content_type="application/json")
    c.post("/v1/metrics", data=payload, content_type="application/json")
    assert store.count_otlp_records() == n_before + 1
    assert sum(t.get("cache_read_tokens", 0) for t in _d.metrics_store["tokens"]) == 47000


def test_cumulative_sums_and_absent_values_never_reach_a_tile(store, client):
    """AC-RSO-CCT-001.4 -- a CUMULATIVE token sum is ledger-only (a running
    total must not be added every interval); a data point with no number is
    stored with value null, never 0.

    AC-RSO-CCT-001.4
    """
    c, _ = client
    cumulative = _metric("claude_code.token.usage", [(99999, {"type": "cacheRead", "model": "m"})])
    cumulative["sum"]["aggregationTemporality"] = "AGGREGATION_TEMPORALITY_CUMULATIVE"
    empty = {"name": "claude_code.commit.count", "sum": {"dataPoints": [
        {"timeUnixNano": str(int(time.time() * 1e9)), "attributes": _ident()}]}}
    r = c.post("/v1/metrics", data=_metrics_payload([cumulative, empty]),
               content_type="application/json")
    assert r.status_code == 200
    assert _d.metrics_store["tokens"] == []
    rows = store.query_otlp_records(limit=10)
    if isinstance(rows, dict):
        rows = rows.get("result") or rows.get("rows") or []
    by = {r["event_name"]: r for r in rows}
    assert by["claude_code.token.usage"]["attributes"]["value"] == 99999
    assert by["claude_code.commit.count"]["attributes"]["value"] is None


# ── AC-RSO-CCT-001.5: typed events ──────────────────────────────────────────

def test_typed_claude_code_events_are_persisted_with_their_fields(store):
    """AC-RSO-CCT-001.5 -- permission-mode change, refusal, error, MCP
    connection, auth, prompt/response lengths become events of the same
    name with their fields, and a rejected decision is never a tool call.

    AC-RSO-CCT-001.5
    """
    now = int(time.time() * 1e9)
    _d._process_otlp_logs(_logs_payload([
        _log("claude_code.permission_mode_changed", now + 1, from_mode="default", to_mode="plan", trigger="shift_tab"),
        _log("claude_code.api_refusal", now + 2, model="claude-opus-4-8", query_source="main", attempt=1, has_explanation=True),
        _log("claude_code.api_error", now + 3, model="claude-opus-4-8", error="overloaded", status_code=529, attempt=2, duration_ms=1200.0),
        _log("claude_code.mcp_server_connection", now + 4, status="failed", server_name="github", transport_type="stdio", error_code="ENOENT"),
        _log("claude_code.auth", now + 5, action="login", success=True, auth_method="oauth"),
        _log("claude_code.user_prompt", now + 6, prompt_length=88),
        _log("claude_code.assistant_response", now + 7, response_length=410, model="claude-opus-4-8"),
        _log("claude_code.tool_decision", now + 8, tool_name="Bash", decision="reject", source="user_reject", tool_source="builtin"),
        _log("claude_code.tool_decision", now + 9, tool_name="Read", decision="accept", source="config"),
        _log("claude_code.api_request", now + 10, model="claude-opus-4-8", cost_usd=0.5, input_tokens=100, output_tokens=20,
             cache_read_tokens=9000, cache_creation_tokens=1000, **{"skill.name": "deploy", "agent.name": "reviewer", "query_source": "subagent"}),
    ]), content_type="application/json")

    evs = _events(store, _STORED)
    by_type = {}
    for e in evs:
        by_type.setdefault(e["event_type"], []).append(e)
    for t in ("permission_mode_changed", "api_refusal", "api_error",
              "mcp_server_connection", "auth", "user_prompt", "assistant_response"):
        assert t in by_type, (t, sorted(by_type))
        assert _data(by_type[t][0]).get("_otlp") is True
    assert _data(by_type["permission_mode_changed"][0])["to_mode"] == "plan"
    assert _data(by_type["api_error"][0])["status_code"] == 529
    assert _data(by_type["mcp_server_connection"][0])["server_name"] == "github"
    assert _data(by_type["user_prompt"][0])["prompt_length"] == 88
    assert "prompt" not in _data(by_type["user_prompt"][0]), "no prompt text unless the exporter sent it"
    # With content on, text is kept (capped) and the row is tagged; the
    # literal "<REDACTED>" Claude Code sends when content is off is dropped.
    _d._process_otlp_logs(_logs_payload([
        _log("claude_code.user_prompt", now + 20, prompt_length=5000, prompt="x" * 5000),
        _log("claude_code.assistant_response", now + 21, response_length=4, response="<REDACTED>"),
    ]), content_type="application/json")
    ups = [e for e in _events(store, _STORED) if e["event_type"] == "user_prompt"]
    tagged = [e for e in ups if _data(e).get("content")]
    assert len(tagged) == 1 and len(_data(tagged[0])["prompt"]) == 4000
    assert _data(tagged[0])["prompt_truncated"] is True
    resp = [e for e in _events(store, _STORED) if e["event_type"] == "assistant_response"]
    assert all("response" not in _data(e) for e in resp)
    # Rejected decision: recorded as tool_decision, NOT as a tool_call.
    rejected = [e for e in by_type.get("tool_decision", [])]
    assert len(rejected) == 1 and _data(rejected[0])["source"] == "user_reject"
    calls = [e for e in by_type.get("tool_call", [])]
    assert [_data(e)["tool"] for e in calls] == ["Read"]
    assert _data(calls[0])["tool_name"] == "Read", "turn anatomy labels by tool_name"
    # api_request keeps cache + attribution on the llm_call event.
    llm = by_type["llm_call"][0]
    d = _data(llm)
    assert d["cache_read_tokens"] == 9000 and d["cache_creation_tokens"] == 1000
    assert d["skill"] == "deploy" and d["agent"] == "reviewer" and d["query_source"] == "subagent"
    # Every event is keyed to the daemon's session id form.
    assert {e["session_id"] for e in evs} == {_STORED}


# ── AC-RSO-CCT-001.6: tracing-beta spans ────────────────────────────────────

def test_tracing_beta_spans_carry_tokens_tool_names_and_waiting_time(store):
    """AC-RSO-CCT-001.6 -- llm_request spans read Claude Code's cache token
    names; tool spans keep the tool name; blocked_on_user becomes a
    waiting_on_user event with the real duration. No session is
    materialized from Claude Code spans.

    AC-RSO-CCT-001.6
    """
    t0 = int(time.time() * 1e9)
    ms = 1_000_000
    _d._process_otlp_traces(_traces_payload([
        _span("claude_code.interaction", t0, t0 + 9000 * ms, "11" * 8),
        _span("claude_code.llm_request", t0 + 10 * ms, t0 + 2000 * ms, "22" * 8, parent="11" * 8,
              model="claude-opus-4-8", input_tokens=120, output_tokens=40,
              cache_read_tokens=8000, cache_creation_tokens=500),
        _span("claude_code.tool", t0 + 2100 * ms, t0 + 8000 * ms, "33" * 8, parent="11" * 8, tool_name="Bash"),
        _span("claude_code.tool.blocked_on_user", t0 + 2100 * ms, t0 + 6100 * ms, "44" * 8, parent="33" * 8, tool_name="Bash"),
        _span("claude_code.tool.execution", t0 + 6100 * ms, t0 + 8000 * ms, "55" * 8, parent="33" * 8, tool_name="Bash"),
    ]), content_type="application/json")

    spans = store.query_spans(session_id=_STORED, limit=50)
    if isinstance(spans, dict):
        spans = spans.get("result") or spans.get("rows") or []
    by_name = {s["name"]: s for s in spans}
    assert "claude_code.llm_request" in by_name, sorted(by_name)
    llm = by_name["claude_code.llm_request"]
    assert int(llm.get("tokens_input") or 0) == 120 and int(llm.get("tokens_output") or 0) == 40
    assert float(llm.get("cost_usd") or 0) > 0, "cache-aware derived cost from Claude Code's attribute names"
    assert by_name["claude_code.tool"].get("tool_name") == "Bash"
    assert {s["session_id"] for s in spans} == {_STORED}

    waits = [e for e in _events(store, _STORED) if e["event_type"] == "waiting_on_user"]
    assert len(waits) == 1
    assert abs(_data(waits[0])["duration_ms"] - 4000.0) < 1.0
    assert _data(waits[0])["tool"] == "Bash"
    # Live Claude Code sends NO tool_name on the blocked_on_user span; the
    # parent claude_code.tool span names it.
    _d._process_otlp_traces(_traces_payload([
        _span("claude_code.tool", t0 + 9000 * ms, t0 + 9900 * ms, "66" * 8, parent="11" * 8, tool_name="Edit"),
        _span("claude_code.tool.blocked_on_user", t0 + 9000 * ms, t0 + 9500 * ms, "77" * 8, parent="66" * 8),
    ]), content_type="application/json")
    waits = [e for e in _events(store, _STORED) if e["event_type"] == "waiting_on_user"]
    assert sorted(_data(w)["tool"] for w in waits) == ["Bash", "Edit"]
    # And when the parent shipped in an EARLIER batch (the wait ends before
    # its parent, so batching exporters split them), the store answers.
    _d._process_otlp_traces(_traces_payload([
        _span("claude_code.tool", t0 + 10000 * ms, t0 + 12000 * ms, "88" * 8, parent="11" * 8, tool_name="Write"),
    ]), content_type="application/json")
    _d._process_otlp_traces(_traces_payload([
        _span("claude_code.tool.blocked_on_user", t0 + 10000 * ms, t0 + 10800 * ms, "99" * 8, parent="88" * 8),
    ]), content_type="application/json")
    waits = [e for e in _events(store, _STORED) if e["event_type"] == "waiting_on_user"]
    assert sorted(_data(w)["tool"] for w in waits) == ["Bash", "Edit", "Write"]

    sessions = store.list_sessions(limit=50) if hasattr(store, "list_sessions") else []
    if isinstance(sessions, dict):
        sessions = sessions.get("result") or sessions.get("rows") or []
    assert not [s for s in (sessions or []) if str(s.get("id") or s.get("session_id") or "").endswith(_SESSION)], \
        "Claude Code spans must not materialize a session"


def test_turn_anatomy_sums_waiting_on_you_per_turn():
    """AC-RSO-CCT-001.6 -- the per-turn figure exists only when a wait span
    was received, and equals the received duration.

    AC-RSO-CCT-001.6
    """
    from routes.turn_anatomy import _build_turns
    t = 1_700_000_000_000
    rows = [
        {"event_type": "prompt.submitted", "ts": t, "data": {"finalPromptText": "fix it"}},
        {"event_type": "tool_call", "ts": t + 100, "data": {"tool": "Bash", "tool_name": "Bash", "tool_calls": [{"id": "x1", "name": "Bash"}]}},
        {"event_type": "waiting_on_user", "ts": t + 100, "data": {"tool": "Bash", "duration_ms": 4000, "_otlp": True}},
        {"event_type": "tool_result", "ts": t + 5000, "data": {"tool": "Bash", "tool_use_id": "x1"}},
        {"event_type": "model.completed", "ts": t + 6000, "data": {"role": "assistant"}},
    ]
    turns = _build_turns(rows)
    assert len(turns) == 1
    assert turns[0]["waiting_on_you_ms"] == 4000
    assert [s for s in turns[0]["spans"] if s["kind"] == "wait"][0]["label"].startswith("waiting on you")
    rows_no_wait = [r for r in rows if r["event_type"] != "waiting_on_user"]
    assert _build_turns(rows_no_wait)[0]["waiting_on_you_ms"] is None


def test_turn_anatomy_daemon_free_session_splits_on_user_prompt_and_shows_markers():
    """AC-RSO-CCT-001.6 -- with no transcript prompt (daemon-free machine)
    the Claude Code ``user_prompt`` event is the turn boundary, an
    ``api_error`` / rejected decision shows as a zero-width marker, and a
    session that HAS transcript prompts ignores ``user_prompt`` entirely.

    AC-RSO-CCT-001.6
    """
    from routes.turn_anatomy import _build_turns
    t = 1_700_000_000_000
    free = [
        {"event_type": "user_prompt", "ts": t, "data": {"prompt_length": 72, "_otlp": True}},
        {"event_type": "llm_call", "ts": t + 100, "data": {"model": "m"}, "model": "m"},
        {"event_type": "api_error", "ts": t + 200, "data": {"status_code": 529, "error": "overloaded"}},
        {"event_type": "tool_decision", "ts": t + 300, "data": {"tool": "Bash", "decision": "reject", "source": "user_reject"}},
        {"event_type": "user_prompt", "ts": t + 5000, "data": {"prompt_length": 10, "_otlp": True}},
        {"event_type": "llm_call", "ts": t + 5100, "data": {"model": "m"}, "model": "m"},
    ]
    turns = _build_turns(free)
    assert len(turns) == 2
    assert turns[0]["prompt"] == "prompt (72 chars)"
    kinds = [s["kind"] for s in turns[0]["spans"]]
    assert kinds.count("marker") == 2 and "model" in kinds
    labels = [s["label"] for s in turns[0]["spans"] if s["kind"] == "marker"]
    assert "API error 529" in labels and "Bash reject by user_reject" in labels
    owned = [{"event_type": "prompt.submitted", "ts": t, "data": {"finalPromptText": "real"}}] + free[1:]
    assert len(_build_turns(owned)) == 1, "user_prompt never splits a transcript-owned session"


# ── AC-RSO-CCT-001.7: one session, two sources ──────────────────────────────

def test_daemon_owned_session_keeps_its_totals_and_gains_otel_only_facts(store):
    """AC-RSO-CCT-001.7 -- with a transcript-derived session already in the
    store, an OTel batch for the same uuid adds no llm_call / tool_call
    duplicates (totals unchanged) but attaches the OTel-only events.

    AC-RSO-CCT-001.7
    """
    now = time.time()
    # What the daemon writes from the transcript: id NOT prefixed otlp:.
    store.ingest({
        "id": "cc-transcript-1", "node_id": "mac-of-dana", "agent_type": "openclaw",
        "agent_id": "main", "session_id": _STORED, "runtime_kind": "claude_code",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now - 5)),
        "event_type": "llm_call", "cost_usd": 4.10, "token_count": 1800,
        "model": "claude-opus-4-8",
        "data": {"model": "claude-opus-4-8", "input_tokens": 1500, "output_tokens": 300},
    })
    store._flush_now()
    before = _events(store, _STORED)
    cost_before = sum(float(e.get("cost_usd") or 0) for e in before)

    ns = int(now * 1e9)
    res_payload = _logs_payload([
        _log("claude_code.api_request", ns, model="claude-opus-4-8", cost_usd=4.10, input_tokens=1500, output_tokens=300),
        _log("claude_code.tool_decision", ns + 1, tool_name="Bash", decision="accept", source="config"),
        _log("claude_code.permission_mode_changed", ns + 2, from_mode="default", to_mode="acceptEdits", trigger="shift_tab"),
        _log("claude_code.api_refusal", ns + 3, model="claude-opus-4-8", attempt=1),
    ])
    _d._process_otlp_logs(res_payload, content_type="application/json")

    after = _events(store, _STORED)
    types = sorted(e["event_type"] for e in after)
    assert types.count("llm_call") == 1, types
    assert "tool_call" not in types, types
    assert "permission_mode_changed" in types and "api_refusal" in types, types
    assert abs(sum(float(e.get("cost_usd") or 0) for e in after) - cost_before) < 1e-9
    # The identity ledger still saw every record (org rollup is unaffected),
    # keyed by the uuid exactly as Claude Code sent it.
    assert store.count_otlp_records() == 4
    ledger = store.query_otlp_records(session_id=_SESSION)
    if isinstance(ledger, dict):
        ledger = ledger.get("result") or ledger.get("rows") or []
    assert len(ledger) == 4
    otel_only = next(e for e in after if e["event_type"] == "permission_mode_changed")
    assert _data(otel_only)["_otlp"] is True, "provenance marker so a reader can tell the source"


# ── AC-RSO-CCT-001.8: status ────────────────────────────────────────────────

def test_otel_status_reports_claude_code_exporter(client, monkeypatch):
    """AC-RSO-CCT-001.8 -- /api/otel-status says whether the block is in
    place and how old the last Claude Code batch is; unknown is null, not 0.

    AC-RSO-CCT-001.8
    """
    c, meta = client
    monkeypatch.setattr("clawmetry.instrument_claude.status", lambda **kw: {
        "configured": True, "settings_path": "/home/dana/.claude/settings.json",
        "endpoint": "http://127.0.0.1:4318", "content": False,
        "telemetry_enabled": True})
    now = time.time()
    monkeypatch.setattr(meta, "_ls_call", lambda name, **kw: (
        {"ts": now - 30, "received_at": now - 12, "count": 57}
        if name == "latest_otlp_record" and kw.get("service_name") == "claude-code"
        else None))
    body = c.get("/api/otel-status").get_json()
    cc = body["claude_code"]
    assert cc["configured"] is True
    assert cc["endpoint"] == "http://127.0.0.1:4318"
    assert cc["records"] == 57
    assert 11 <= cc["last_batch_age_s"] <= 20

    monkeypatch.setattr(meta, "_ls_call", lambda name, **kw: None)
    cc = c.get("/api/otel-status").get_json()["claude_code"]
    assert cc["last_batch_ts"] is None and cc["records"] is None
