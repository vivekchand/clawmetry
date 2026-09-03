"""Runtime profiles on the OTLP receiver (WO-57).

Requirement: Claude Code Native Telemetry (a4bd3c7e). The receiver is
vendor-neutral; what a runtime calls its metrics, events and spans arrives as
an ``OtelRuntimeProfile`` (free runtimes from this repo, paid ones from
clawmetry-pro). These tests exercise the seam with a FIXTURE runtime
(``acme_cli``) so nothing vendor-specific lives in the public suite. The
Claude Code profile and its tests live in clawmetry-pro.

Covers AC-RSO-CCT-001.4 (profile metrics), .5 (typed events), .6 (spans +
waiting time), .7 (one session, two sources), .8 (status) and .10 (no
profile = the generic free path, unchanged).

Every payload is OTLP/JSON with ``dashboard._HAS_OTEL_PROTO`` forced False.
A private DuckDB writer is wired in per test; the developer's real store is
never touched.
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
from clawmetry import otel_profiles

_SESSION = "0f5c1c1e-7a1e-4c2a-9d0e-2b6f9c4a1234"       # bare id on the wire
_STORED = "acme_cli:" + _SESSION                        # the daemon's key form
_SERVICE = "acme-cli"

PROFILE = otel_profiles.OtelRuntimeProfile(
    runtime="acme_cli",
    label="Acme CLI",
    service_names=("acme-cli",),
    metric_prefix="acme_cli.",
    event_prefix="acme_cli.",
    session_key_prefix="acme_cli:",
    tile_token_metric="acme_cli.token.usage",
    token_type_fields={"cacheread": "cache_read_tokens", "cachecreation": "cache_write_tokens"},
    typed_events={
        "permission_mode_changed": ("from_mode", "to_mode", "trigger"),
        "api_refusal": ("model", "attempt"),
        "api_error": ("model", "error", "status_code", "attempt", "duration_ms"),
        "mcp_server_connection": ("status", "server_name", "transport_type", "error_code"),
        "auth": ("action", "success", "auth_method"),
        "user_prompt": ("prompt_length", "prompt"),
        "assistant_response": ("response_length", "model", "response"),
    },
    llm_extra_fields=(("cache_read_tokens", "cache_read_tokens"),
                      ("cache_creation_tokens", "cache_creation_tokens"),
                      ("skill.name", "skill"), ("agent.name", "agent"),
                      ("query_source", "query_source")),
    span_attr_aliases={"cache_read": ("cache_read_tokens",),
                       "cache_write": ("cache_creation_tokens",),
                       "tool_name": ("tool_name",)},
    wait_span_suffix=".blocked_on_user",
)


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    monkeypatch.setattr(_d, "_HAS_OTEL_PROTO", False)
    monkeypatch.setattr(_d, "metrics_store", {k: [] for k in
                        ("tokens", "cost", "runs", "messages", "webhooks", "queues")})
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    otel_profiles._reset_for_tests()
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    otel_profiles._reset_for_tests()


@pytest.fixture()
def profile():
    otel_profiles.register(PROFILE)
    return PROFILE


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


# ── OTLP/JSON builders ──────────────────────────────────────────────────────

def _kv(k, v):
    if isinstance(v, bool):
        return {"key": k, "value": {"boolValue": v}}
    if isinstance(v, int):
        return {"key": k, "value": {"intValue": str(v)}}
    if isinstance(v, float):
        return {"key": k, "value": {"doubleValue": v}}
    return {"key": k, "value": {"stringValue": str(v)}}


def _resource(**extra):
    base = {"service.name": _SERVICE, "host.name": "mac-of-dana"}
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


def _rows(x):
    if isinstance(x, dict):
        return x.get("result") or x.get("rows") or []
    return list(x or [])


# ── registry ────────────────────────────────────────────────────────────────

def test_registry_resolves_by_runtime_alias_service_metric_and_event():
    """AC-RSO-CCT-001.10 -- the seam: lookups by runtime id, CLI alias,
    service.name, metric prefix and event prefix; nothing registered means
    nothing resolves.

    AC-RSO-CCT-001.10
    """
    assert otel_profiles.by_runtime("acme_cli") is None
    assert otel_profiles.by_service_name(_SERVICE) is None
    prof = otel_profiles.OtelRuntimeProfile(runtime="acme_cli", aliases=("acme",),
                                            service_names=("acme-cli",),
                                            metric_prefix="acme_cli.", event_prefix="acme_cli.",
                                            session_key_prefix="acme_cli:")
    otel_profiles.register(prof)
    assert otel_profiles.by_runtime("ACME") is prof
    assert otel_profiles.by_service_name("Acme-CLI") is prof
    assert otel_profiles.for_metric("acme_cli.token.usage") is prof
    assert otel_profiles.for_event("acme_cli.api_request") is prof
    assert otel_profiles.for_metric("other.token.usage") is None
    assert prof.session_key("abc") == "acme_cli:abc"
    assert prof.session_key("acme_cli:abc") == "acme_cli:abc"
    assert prof.session_key("") is None
    otel_profiles.unregister("acme_cli")
    assert otel_profiles.by_runtime("acme_cli") is None


# ── AC .4: metrics ──────────────────────────────────────────────────────────

def test_profile_metrics_decode_as_json_without_protobuf(store, client, profile):
    """AC-RSO-CCT-001.4 -- a vanilla install (no otel extra) accepts a
    runtime's OTLP/JSON metrics: 200, not 501.

    AC-RSO-CCT-001.4
    """
    c, _ = client
    r = c.post("/v1/metrics", data=_metrics_payload([
        _metric("acme_cli.token.usage", [(1500, {"type": "input", "model": "m"})])]),
        content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)


def test_cache_token_types_land_in_cache_fields_and_ledger(store, client, profile):
    """AC-RSO-CCT-001.4 -- the profile's typed token points reach the cache
    fields the transcript path uses; input/output and cost go to the ledger
    only; every data point is a ledger row named after its metric; retry
    is a replace, in the ledger AND the tile.

    AC-RSO-CCT-001.4
    """
    c, _ = client
    r = c.post("/v1/metrics", data=_metrics_payload([
        _metric("acme_cli.token.usage", [
            (1500, {"type": "input", "model": "m"}),
            (300, {"type": "output", "model": "m"}),
            (42000, {"type": "cacheRead", "model": "m"}),
            (7000, {"type": "cacheCreation", "model": "m"}),
        ]),
        _metric("acme_cli.cost.usage", [(4.10, {"model": "m"})]),
        _metric("acme_cli.lines_of_code.count", [(120, {"type": "added"})]),
        _metric("acme_cli.code_edit_tool.decision", [(1, {"tool_name": "Edit", "decision": "accept"})]),
    ]), content_type="application/json")
    assert r.status_code == 200
    toks = _d.metrics_store["tokens"]
    assert sum(t.get("cache_read_tokens", 0) for t in toks) == 42000
    assert sum(t.get("cache_write_tokens", 0) for t in toks) == 7000
    assert sum(t.get("total", 0) for t in toks) == 0
    assert sum(t.get("input", 0) for t in toks) == 0
    assert _d.metrics_store["cost"] == []
    usage = _d._get_otel_usage_data()
    assert usage["cacheReadTokens"] == 42000 and usage["cacheWriteTokens"] == 7000

    rows = _rows(store.query_otlp_records(limit=100))
    assert sorted({r["event_name"] for r in rows}) == [
        "acme_cli.code_edit_tool.decision", "acme_cli.cost.usage",
        "acme_cli.lines_of_code.count", "acme_cli.token.usage"]
    assert {r["session_id"] for r in rows} == {_SESSION}, "ledger keeps the id as sent"
    assert {r["agent_type"] for r in rows} == {"acme_cli"}
    assert all(r.get("cost_usd") in (None, 0, 0.0) for r in rows)
    edit = next(r for r in rows if r["event_name"] == "acme_cli.code_edit_tool.decision")
    assert edit["tool_name"] == "Edit" and edit["decision"] == "accept"

    n_before = store.count_otlp_records()
    payload = _metrics_payload([_metric("acme_cli.token.usage", [(5000, {"type": "cacheRead", "model": "m"})])])
    c.post("/v1/metrics", data=payload, content_type="application/json")
    c.post("/v1/metrics", data=payload, content_type="application/json")
    assert store.count_otlp_records() == n_before + 1
    assert sum(t.get("cache_read_tokens", 0) for t in _d.metrics_store["tokens"]) == 47000


def test_cumulative_sums_and_absent_values_never_reach_a_tile(store, client, profile):
    """AC-RSO-CCT-001.4 -- a CUMULATIVE token sum is ledger-only; a data
    point with no number stores null, never 0.

    AC-RSO-CCT-001.4
    """
    c, _ = client
    cumulative = _metric("acme_cli.token.usage", [(99999, {"type": "cacheRead", "model": "m"})])
    cumulative["sum"]["aggregationTemporality"] = "AGGREGATION_TEMPORALITY_CUMULATIVE"
    empty = {"name": "acme_cli.commit.count", "sum": {"dataPoints": [
        {"timeUnixNano": str(int(time.time() * 1e9)), "attributes": _ident()}]}}
    r = c.post("/v1/metrics", data=_metrics_payload([cumulative, empty]),
               content_type="application/json")
    assert r.status_code == 200
    assert _d.metrics_store["tokens"] == []
    by = {r["event_name"]: r for r in _rows(store.query_otlp_records(limit=10))}
    assert by["acme_cli.token.usage"]["attributes"]["value"] == 99999
    assert by["acme_cli.commit.count"]["attributes"]["value"] is None


def test_absent_value_is_null_on_the_protobuf_path_too():
    """AC-RSO-CCT-001.4 -- a protobuf NumberDataPoint with no number set
    stores null, never 0 (HasField on an undefined name raises there).

    AC-RSO-CCT-001.4
    """
    pytest.importorskip("opentelemetry.proto.metrics.v1.metrics_pb2")
    from opentelemetry.proto.metrics.v1 import metrics_pb2 as m
    dp = m.NumberDataPoint()
    assert _d._dp_value_or_none(dp) is None
    dp.as_int = 0
    assert _d._dp_value_or_none(dp) == 0
    dp2 = m.NumberDataPoint()
    dp2.as_double = 1.5
    assert _d._dp_value_or_none(dp2) == 1.5


# ── AC .5: typed events ─────────────────────────────────────────────────────

def test_typed_events_are_persisted_with_their_fields(store, profile):
    """AC-RSO-CCT-001.5 -- the profile's typed events become events of the
    same name with their fields; a rejected decision is never a tool call;
    the request event carries the profile's extra fields; text is capped
    and tagged, the literal <REDACTED> dropped.

    AC-RSO-CCT-001.5
    """
    now = int(time.time() * 1e9)
    _d._process_otlp_logs(_logs_payload([
        _log("acme_cli.permission_mode_changed", now + 1, from_mode="default", to_mode="plan", trigger="shift_tab"),
        _log("acme_cli.api_refusal", now + 2, model="m", attempt=1),
        _log("acme_cli.api_error", now + 3, model="m", error="overloaded", status_code=529, attempt=2, duration_ms=1200.0),
        _log("acme_cli.mcp_server_connection", now + 4, status="failed", server_name="github", transport_type="stdio", error_code="ENOENT"),
        _log("acme_cli.auth", now + 5, action="login", success=True, auth_method="oauth"),
        _log("acme_cli.user_prompt", now + 6, prompt_length=88, prompt="<REDACTED>"),
        _log("acme_cli.assistant_response", now + 7, response_length=410, model="m"),
        _log("acme_cli.tool_decision", now + 8, tool_name="Bash", decision="reject", source="user_reject", tool_source="builtin"),
        _log("acme_cli.tool_decision", now + 9, tool_name="Read", decision="accept", source="config"),
        _log("acme_cli.api_request", now + 10, model="m", cost_usd=0.5, input_tokens=100, output_tokens=20,
             cache_read_tokens=9000, cache_creation_tokens=1000, **{"skill.name": "deploy", "agent.name": "reviewer", "query_source": "subagent"}),
        _log("acme_cli.user_prompt", now + 20, prompt_length=5000, prompt="x" * 5000),
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
    ups = by_type["user_prompt"]
    assert any(_data(u)["prompt_length"] == 88 and "prompt" not in _data(u) for u in ups)
    tagged = [u for u in ups if _data(u).get("has_content")]
    assert len(tagged) == 1 and len(_data(tagged[0])["prompt"]) == 4000
    assert _data(tagged[0])["prompt_truncated"] is True
    rejected = by_type.get("tool_decision", [])
    assert len(rejected) == 1 and _data(rejected[0])["source"] == "user_reject"
    calls = by_type.get("tool_call", [])
    assert [_data(e)["tool"] for e in calls] == ["Read"]
    assert _data(calls[0])["tool_name"] == "Read"
    d = _data(by_type["llm_call"][0])
    assert d["cache_read_tokens"] == 9000 and d["cache_creation_tokens"] == 1000
    assert d["skill"] == "deploy" and d["agent"] == "reviewer" and d["query_source"] == "subagent"
    assert {e["session_id"] for e in evs} == {_STORED}
    # The ledger keeps the id as sent.
    assert len(_rows(store.query_otlp_records(session_id=_SESSION))) == 11


# ── AC .6: spans ────────────────────────────────────────────────────────────

def test_spans_use_profile_aliases_and_wait_spans_become_waiting_time(store, profile):
    """AC-RSO-CCT-001.6 -- the profile's span attribute aliases feed tokens
    and tool names; its wait-span suffix becomes a waiting_on_user event
    named by the parent tool span, across batches too.

    AC-RSO-CCT-001.6
    """
    t0 = int(time.time() * 1e9)
    ms = 1_000_000
    _d._process_otlp_traces(_traces_payload([
        _span("acme_cli.interaction", t0, t0 + 9000 * ms, "11" * 8),
        _span("acme_cli.llm_request", t0 + 10 * ms, t0 + 2000 * ms, "22" * 8, parent="11" * 8,
              model="m", input_tokens=120, output_tokens=40,
              cache_read_tokens=8000, cache_creation_tokens=500),
        _span("acme_cli.tool", t0 + 2100 * ms, t0 + 8000 * ms, "33" * 8, parent="11" * 8, tool_name="Bash"),
        _span("acme_cli.tool.blocked_on_user", t0 + 2100 * ms, t0 + 6100 * ms, "44" * 8, parent="33" * 8),
    ]), content_type="application/json")
    spans = _rows(store.query_spans(session_id=_STORED, limit=50))
    by_name = {s["name"]: s for s in spans}
    llm = by_name["acme_cli.llm_request"]
    assert int(llm.get("tokens_input") or 0) == 120 and int(llm.get("tokens_output") or 0) == 40
    assert by_name["acme_cli.tool"].get("tool_name") == "Bash"
    assert {s["session_id"] for s in spans} == {_STORED}
    waits = [e for e in _events(store, _STORED) if e["event_type"] == "waiting_on_user"]
    assert len(waits) == 1
    assert abs(_data(waits[0])["duration_ms"] - 4000.0) < 1.0
    assert _data(waits[0])["tool"] == "Bash", "named by the parent tool span"
    # Parent shipped in an earlier batch: the store answers.
    _d._process_otlp_traces(_traces_payload([
        _span("acme_cli.tool", t0 + 10000 * ms, t0 + 12000 * ms, "88" * 8, parent="11" * 8, tool_name="Write")]),
        content_type="application/json")
    _d._process_otlp_traces(_traces_payload([
        _span("acme_cli.tool.blocked_on_user", t0 + 10000 * ms, t0 + 10800 * ms, "99" * 8, parent="88" * 8)]),
        content_type="application/json")
    waits = [e for e in _events(store, _STORED) if e["event_type"] == "waiting_on_user"]
    assert sorted(_data(w)["tool"] for w in waits) == ["Bash", "Write"]
    # A session row is materialized under the daemon's key (daemon-free case).
    try:
        store._flush_now()
    except Exception:
        pass
    rows = store._fetch("SELECT session_id FROM sessions WHERE session_id = ?", [_STORED])
    assert len(rows) == 1, rows
    assert not store._fetch("SELECT session_id FROM sessions WHERE session_id = ?", [_SESSION])


def test_turn_anatomy_sums_waiting_on_you_and_shows_markers():
    """AC-RSO-CCT-001.6 -- per-turn waiting time exists only when a wait
    event was received; a daemon-free session splits on user_prompt and
    shows api_error / rejected decisions as markers; a transcript-owned
    session ignores user_prompt.

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
    assert len(turns) == 1 and turns[0]["waiting_on_you_ms"] == 4000
    assert next(s for s in turns[0]["spans"] if s["kind"] == "wait")["label"].startswith("waiting on you")
    assert _build_turns([r for r in rows if r["event_type"] != "waiting_on_user"])[0]["waiting_on_you_ms"] is None

    free = [
        {"event_type": "user_prompt", "ts": t, "data": {"prompt_length": 72, "_otlp": True}},
        {"event_type": "llm_call", "ts": t + 100, "data": {"model": "m"}, "model": "m"},
        {"event_type": "api_error", "ts": t + 200, "data": {"status_code": 529}},
        {"event_type": "tool_decision", "ts": t + 300, "data": {"tool": "Bash", "decision": "reject", "source": "user_reject"}},
        {"event_type": "user_prompt", "ts": t + 5000, "data": {"prompt_length": 10, "_otlp": True}},
        {"event_type": "llm_call", "ts": t + 5100, "data": {"model": "m"}, "model": "m"},
    ]
    turns = _build_turns(free)
    assert len(turns) == 2 and turns[0]["prompt"] == "prompt (72 chars)"
    kinds = [s["kind"] for s in turns[0]["spans"]]
    assert kinds.count("marker") == 2 and "model" in kinds
    labels = [s["label"] for s in turns[0]["spans"] if s["kind"] == "marker"]
    assert "API error 529" in labels and "Bash reject by user_reject" in labels
    owned = [{"event_type": "prompt.submitted", "ts": t, "data": {"finalPromptText": "real"}}] + free[1:]
    assert len(_build_turns(owned)) == 1


# ── AC .7: one session, two sources ─────────────────────────────────────────

def test_daemon_owned_session_keeps_its_totals_and_gains_otel_only_facts(store, profile):
    """AC-RSO-CCT-001.7 -- with a transcript-derived session in the store,
    an OTel batch for the same id adds no llm_call / tool_call duplicates
    (totals unchanged) but attaches the OTel-only events with provenance.

    AC-RSO-CCT-001.7
    """
    now = time.time()
    store.ingest({
        "id": "transcript-1", "node_id": "mac-of-dana", "agent_type": "openclaw",
        "agent_id": "main", "session_id": _STORED, "runtime_kind": "acme_cli",
        "ts": time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(now - 5)),
        "event_type": "llm_call", "cost_usd": 4.10, "token_count": 1800, "model": "m",
        "data": {"model": "m", "input_tokens": 1500, "output_tokens": 300},
    })
    store._flush_now()
    cost_before = sum(float(e.get("cost_usd") or 0) for e in _events(store, _STORED))
    ns = int(now * 1e9)
    _d._process_otlp_logs(_logs_payload([
        _log("acme_cli.api_request", ns, model="m", cost_usd=4.10, input_tokens=1500, output_tokens=300),
        _log("acme_cli.tool_decision", ns + 1, tool_name="Bash", decision="accept", source="config"),
        _log("acme_cli.permission_mode_changed", ns + 2, from_mode="default", to_mode="acceptEdits", trigger="shift_tab"),
        _log("acme_cli.api_refusal", ns + 3, model="m", attempt=1),
    ]), content_type="application/json")
    after = _events(store, _STORED)
    types = sorted(e["event_type"] for e in after)
    assert types.count("llm_call") == 1 and "tool_call" not in types, types
    assert "permission_mode_changed" in types and "api_refusal" in types
    assert abs(sum(float(e.get("cost_usd") or 0) for e in after) - cost_before) < 1e-9
    assert store.count_otlp_records() == 4
    assert _data(next(e for e in after if e["event_type"] == "permission_mode_changed"))["_otlp"] is True


# ── AC .8: status ───────────────────────────────────────────────────────────

def test_otel_status_reports_each_instrumented_runtime(client, monkeypatch, profile):
    """AC-RSO-CCT-001.8 -- /api/otel-status lists every profiled runtime
    with configured / endpoint / last batch age; unknown is null, not 0.

    AC-RSO-CCT-001.8
    """
    c, meta = client
    monkeypatch.setattr("clawmetry.instrument.status_all", lambda probe=False: {
        "acme_cli": {"configured": True, "settings_path": "/home/dana/.acme/settings.json",
                     "endpoint": "http://127.0.0.1:4318", "content": False,
                     "telemetry_enabled": True, "entitled": True, "label": "Acme CLI"}})
    now = time.time()
    monkeypatch.setattr(meta, "_ls_call", lambda name, **kw: (
        {"ts": now - 30, "received_at": now - 12, "count": 57}
        if name == "latest_otlp_record" and kw.get("service_name") == _SERVICE else None))
    rt = c.get("/api/otel-status").get_json()["runtimes"]["acme_cli"]
    assert rt["configured"] is True and rt["endpoint"] == "http://127.0.0.1:4318"
    assert rt["records"] == 57 and 11 <= rt["last_batch_age_s"] <= 20
    monkeypatch.setattr(meta, "_ls_call", lambda name, **kw: None)
    rt = c.get("/api/otel-status").get_json()["runtimes"]["acme_cli"]
    assert rt["last_batch_ts"] is None and rt["records"] is None


# ── AC .10: no profile = the generic free path ──────────────────────────────

def test_without_a_profile_only_the_generic_free_path_remains(store, client):
    """AC-RSO-CCT-001.10 -- with NO profile registered for the emitter (a
    free install without the runtime's pro wheel), a batch is still
    accepted and the ledger keeps every record, but nothing runtime
    specific happens: no cache tile, no typed events, no rejected-decision
    event, no session-key rewrite, no waiting event. Exactly what shipped
    before profiles existed.

    AC-RSO-CCT-001.10
    """
    c, _ = client
    r = c.post("/v1/metrics", data=_metrics_payload([
        _metric("acme_cli.token.usage", [(42000, {"type": "cacheRead", "model": "m"})])]),
        content_type="application/json")
    assert r.status_code == 200
    assert _d.metrics_store["tokens"] == []
    assert store.count_otlp_records() == 0, "an unknown vendor metric is ignored, as before"
    now = int(time.time() * 1e9)
    _d._process_otlp_logs(_logs_payload([
        _log("acme_cli.api_request", now, model="m", cost_usd=0.5, input_tokens=10, output_tokens=2, **{"skill.name": "deploy"}),
        _log("acme_cli.permission_mode_changed", now + 1, from_mode="default", to_mode="plan", trigger="shift_tab"),
        _log("acme_cli.tool_decision", now + 2, tool_name="Bash", decision="reject", source="user_reject"),
        _log("acme_cli.tool_decision", now + 3, tool_name="Read", decision="accept", source="config"),
    ]), content_type="application/json")
    assert _events(store, _STORED) == []
    free = _events(store, _SESSION)
    assert sorted(e["event_type"] for e in free) == ["llm_call", "tool_call"]
    assert "skill" not in _data(next(e for e in free if e["event_type"] == "llm_call"))
    assert store.count_otlp_records() == 4
    t0 = int(time.time() * 1e9)
    ms = 1_000_000
    _d._process_otlp_traces(_traces_payload([
        _span("acme_cli.tool", t0, t0 + 500 * ms, "aa" * 8, tool_name="Bash"),
        _span("acme_cli.tool.blocked_on_user", t0, t0 + 200 * ms, "bb" * 8, parent="aa" * 8),
    ]), content_type="application/json")
    assert len(_rows(store.query_spans(session_id=_SESSION, limit=10))) == 2
    assert [e for e in _events(store, _SESSION) + _events(store, _STORED)
            if e["event_type"] == "waiting_on_user"] == []
