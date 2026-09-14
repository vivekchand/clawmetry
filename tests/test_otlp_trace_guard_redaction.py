"""REQ-OBS-OTG-001: exported traces reach Guard, and are scrubbed before storage.

Before this, a span received on /v1/traces was written to the ``spans`` table
and nowhere else. The detectors behind Guard read ``events``, so a trace that
showed an agent running a recursive delete at the filesystem root raised
nothing, and redaction ran only at the event chokepoint, so a secret or an
email in a prompt, a tool argument or an exception event rested in DuckDB as
sent. The OTLP *log* path had neither gap (tests/test_otlp_daemon_free_intake.py).

Everything here runs through the real receiver (``_process_otlp_traces`` /
``_process_otlp_logs``), the real store and the daemon's real detector pass
(``sync._emit_detector_incidents``). No shell command is executed anywhere in
this file: the destructive command is a string inside a span attribute, which
is exactly what an exported trace is.
"""
import importlib
import json
import os
import pathlib
import tempfile
import time

import pytest

pytest.importorskip(
    "opentelemetry.proto.collector.trace.v1.trace_service_pb2",
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)

from opentelemetry.proto.collector.logs.v1 import logs_service_pb2  # noqa: E402
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2  # noqa: E402
from opentelemetry.proto.common.v1 import common_pb2  # noqa: E402
from opentelemetry.proto.logs.v1 import logs_pb2  # noqa: E402
from opentelemetry.proto.trace.v1 import trace_pb2  # noqa: E402

import dashboard as _d  # noqa: E402

_ls = importlib.import_module("clawmetry.local_store")

SERVICE = "support-agent"
# Canary values. Shaped like the real thing so the scrubber's patterns apply;
# none of them is a credential for anything.
EMAIL = "dana.canary@example.com"
ANTHROPIC_KEY = "sk-ant-CANARYnotarealkey000000000000"
BEARER = "CANARYbearer1234567890"
URL_TOKEN = "CANARYurltoken123456"
BASIC = "CANARYbasic1234567890"
CANARIES = (EMAIL, ANTHROPIC_KEY, BEARER, URL_TOKEN, BASIC)


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_REDACT", raising=False)
    monkeypatch.delenv("CLAWMETRY_REDACT_PII", raising=False)
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()


@pytest.fixture()
def store(monkeypatch):
    """A private DuckDB writer wired in as the singleton the handlers resolve.
    Same shape as test_otlp_daemon_free_intake.py's fixture, for the same
    reasons (module reloads elsewhere in the suite, DB_PATH module state)."""
    global _ls
    _ls = importlib.import_module("clawmetry.local_store")
    tmpdir = tempfile.mkdtemp(prefix="clawmetry-otg-")
    path = os.path.join(tmpdir, "otg.duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", path)
    _ls._reset_singleton_for_tests()
    prev_db_path = _ls.DB_PATH
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
        _ls.DB_PATH = prev_db_path
        _ls._reset_singleton_for_tests()


# ── OTLP builders ───────────────────────────────────────────────────────────

def _kv(key, s=None, i=None, arr=None):
    v = common_pb2.AnyValue()
    if arr is not None:
        v.array_value.values.extend([common_pb2.AnyValue(string_value=x) for x in arr])
    elif s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    return common_pb2.KeyValue(key=key, value=v)


def _span(trace_seed, span_seed, name, attrs, *, error=None, events=(),
          off_s=0.0, dur_s=0.5):
    base = time.time() - 30
    sp = trace_pb2.Span(
        trace_id=bytes([trace_seed]) * 16,
        span_id=bytes([span_seed]) * 8,
        name=name,
        start_time_unix_nano=int((base + off_s) * 1e9),
        end_time_unix_nano=int((base + off_s + dur_s) * 1e9),
    )
    sp.attributes.extend(attrs)
    if error is not None:
        sp.status.code = trace_pb2.Status.STATUS_CODE_ERROR
        sp.status.message = error
    for ev_name, ev_attrs in events:
        ev = sp.events.add()
        ev.name = ev_name
        ev.time_unix_nano = sp.start_time_unix_nano
        ev.attributes.extend(ev_attrs)
    return sp


def _chat_span(span_seed, conv, *, trace_seed=0x11, extra=(), **kw):
    attrs = [
        _kv("gen_ai.operation.name", s="chat"),
        _kv("gen_ai.request.model", s="gpt-4o"),
        _kv("gen_ai.usage.input_tokens", i=120),
        _kv("gen_ai.usage.output_tokens", i=30),
    ]
    if conv:
        attrs.append(_kv("gen_ai.conversation.id", s=conv))
    attrs.extend(extra)
    return _span(trace_seed, span_seed, "chat gpt-4o", attrs, **kw)


def _tool_span(span_seed, tool, args=None, *, conv="conv-canary",
               trace_seed=0x11, extra=(), **kw):
    attrs = [
        _kv("gen_ai.operation.name", s="execute_tool"),
        _kv("gen_ai.tool.name", s=tool),
        _kv("gen_ai.tool.call.id", s="call-%d" % span_seed),
    ]
    if conv:
        attrs.append(_kv("gen_ai.conversation.id", s=conv))
    if args is not None:
        attrs.append(_kv("gen_ai.tool.call.arguments", s=json.dumps(args)))
    attrs.extend(extra)
    return _span(trace_seed, span_seed, "execute_tool " + tool, attrs, **kw)


def _traces(spans, service=SERVICE):
    res = trace_pb2.ResourceSpans(scope_spans=[trace_pb2.ScopeSpans(spans=spans)])
    res.resource.attributes.extend([_kv("service.name", s=service)])
    return trace_service_pb2.ExportTraceServiceRequest(
        resource_spans=[res]).SerializeToString()


def _logs(records, service=SERVICE):
    res = logs_pb2.ResourceLogs(scope_logs=[logs_pb2.ScopeLogs(log_records=records)])
    res.resource.attributes.extend([_kv("service.name", s=service)])
    return logs_service_pb2.ExportLogsServiceRequest(
        resource_logs=[res]).SerializeToString()


def _log_record(event_name, session_id, attrs):
    rec = logs_pb2.LogRecord(time_unix_nano=int((time.time() - 20) * 1e9))
    rec.event_name = event_name
    rec.attributes.extend([_kv("session.id", s=session_id)] + list(attrs))
    return rec


def _guard_tick(store, monkeypatch):
    """One real detector pass. Alert delivery and the policy pass are
    captured rather than run: this file is about what reaches them."""
    from clawmetry import incident_alerts as _ia
    from clawmetry import sync as _sync

    delivered, policy_batches = [], []
    monkeypatch.setattr(
        _ia, "deliver_incident",
        lambda st, inc, **kw: delivered.append(dict(inc)) or {"delivered_via": []})
    monkeypatch.setattr(
        _sync, "_apply_guard_policies",
        lambda st, state, incs, facts: policy_batches.append(list(incs)) or 0)
    _sync._emit_detector_incidents(store, {})
    return delivered, policy_batches


def _signals(store, session_id):
    out = []
    for row in store.query_recent_loop_signals(limit=200, since_minutes=0):
        if row.get("session_id") != session_id:
            continue
        details = row.get("details")
        if isinstance(details, str):
            details = json.loads(details)
        out.append(dict(row, details=details))
    return out


def _tool_events(store, session_id):
    return [e for e in store.query_events(session_id=session_id, limit=500)
            if e["event_type"] in ("tool_call", "tool_result")]


# ── Guard sees the trace ────────────────────────────────────────────────────

def test_a_destructive_tool_span_raises_a_guard_incident_labelled_as_observed(store, monkeypatch):
    """The issue's own reproduction, through the daemon's real detector pass.

    AC-OBS-OTG-001.1
    AC-OBS-OTG-001.6
    """
    _d._process_otlp_traces(_traces([
        _chat_span(0x01, "conv-canary"),
        _tool_span(0x02, "bash", {"command": "rm -rf /"}, off_s=1),
    ]))

    calls = [e for e in _tool_events(store, "conv-canary") if e["event_type"] == "tool_call"]
    assert len(calls) == 1, calls
    data = calls[0]["data"]
    # The event keeps where it came from.
    assert calls[0]["session_id"] == "conv-canary"
    assert data["trace_id"] == "11" * 16
    assert data["span_id"] == "02" * 8
    assert data["call_id"] == "call-2"
    assert data["capture"] == "post_action_telemetry"

    delivered, policy_batches = _guard_tick(store, monkeypatch)

    rows = [r for r in _signals(store, "conv-canary")
            if r["signature"] == "daemon_detect_file_blast_radius"]
    assert rows, "a recursive delete at the root in a received trace raised nothing"
    row = rows[0]
    assert row["severity"] == "critical"
    details = row["details"]
    assert details["observation"] == {
        "source": "received_telemetry", "signals": ["trace"],
        "after_the_fact": True, "prevented": False,
    }
    assert "after the action ran" in details["detail"]
    assert "did not hold or block it" in details["detail"]
    # The same incident reaches the policy pass every other runtime uses.
    assert any(i.get("kind") == "file_blast_radius"
               for batch in policy_batches for i in batch)


def test_failing_tool_spans_are_failed_tool_results_the_detectors_count(store):
    """
    AC-OBS-OTG-001.1
    """
    from clawmetry import detectors

    spans = [
        _tool_span(0x20 + i, "run_tests", {"command": "pytest tests/test_%d.py" % i},
                   conv="conv-fail", error="exit status 1", off_s=i)
        for i in range(8)
    ]
    _d._process_otlp_traces(_traces(spans))
    events = store.query_events(session_id="conv-fail", limit=200)
    results = [e for e in events if e["event_type"] == "tool_result"]
    assert len(results) == 8
    assert all(r["data"]["is_error"] is True for r in results)
    assert detectors.repeated_tool_failure(events, "conv-fail", None) is not None


def test_benign_controls_and_missing_fields_raise_nothing(store, monkeypatch):
    """A harmless tool, a chat span, a function span that is not a tool, and
    an OpenClaw span with no session.

    AC-OBS-OTG-001.2
    """
    _d._process_otlp_traces(_traces([
        _chat_span(0x31, "conv-benign"),
        _tool_span(0x32, "bash", {"command": "ls -la"}, conv="conv-benign", off_s=1),
        _span(0x11, 0x33, "helper", [
            _kv("code.function", s="helper"),
            _kv("gen_ai.conversation.id", s="conv-benign"),
        ], off_s=2),
        # OpenClaw spans keep a null session by design, so even a destructive
        # command there is not an event this path may mint.
        _span(0x12, 0x34, "execute_tool bash", [
            _kv("agent.type", s="openclaw"),
            _kv("gen_ai.operation.name", s="execute_tool"),
            _kv("gen_ai.tool.name", s="bash"),
            _kv("gen_ai.tool.call.arguments", s=json.dumps({"command": "rm -rf /"})),
        ], off_s=3),
    ]))

    tool = _tool_events(store, "conv-benign")
    assert sorted(e["event_type"] for e in tool) == ["tool_call", "tool_result"]
    assert tool[0]["data"]["tool"] == "bash"
    everything = json.dumps(store.query_events(limit=500), default=str)
    assert "rm -rf" not in everything

    _guard_tick(store, monkeypatch)
    assert _signals(store, "conv-benign") == []


def test_a_tool_span_without_arguments_is_not_read_as_a_loop(store):
    """
    AC-OBS-OTG-001.2
    """
    from clawmetry import detectors

    _d._process_otlp_traces(_traces([
        _tool_span(0x40 + i, "read_file", None, conv="conv-noargs", off_s=i)
        for i in range(10)
    ]))
    events = store.query_events(session_id="conv-noargs", limit=200)
    calls = [e for e in events if e["event_type"] == "tool_call"]
    assert len(calls) == 10
    assert len({detectors._args_hash(e["data"].get("args")) for e in calls}) == 10
    assert detectors.stuck_loop(events, "conv-noargs", None) is None


def test_an_all_digit_span_id_is_not_masked_as_a_card_number(store):
    """A span id is 16 hex characters and can be all digits. A Luhn-valid one
    used to come out of the personal-data tier as ``[card]``, which erased the
    join back to the trace and collapsed two calls with unknown arguments into
    one hash (a fabricated loop).

    AC-OBS-OTG-001.1
    AC-OBS-OTG-001.2
    """
    from clawmetry import redaction

    seeds = [b for b in range(0x10, 0x9A)
             if (bytes([b]) * 8).hex().isdigit()
             and redaction.luhn_valid((bytes([b]) * 8).hex())]
    assert len(seeds) >= 2, "fixture needs two Luhn-valid all-digit span ids"
    _d._process_otlp_traces(_traces([
        _tool_span(seed, "read_file", None, conv="conv-digits", off_s=n)
        for n, seed in enumerate(seeds[:2])
    ]))
    calls = [e for e in _tool_events(store, "conv-digits") if e["event_type"] == "tool_call"]
    assert sorted(c["data"]["span_id"] for c in calls) == sorted(
        (bytes([s]) * 8).hex() for s in seeds[:2])
    assert len({json.dumps(c["data"]["args"], sort_keys=True) for c in calls}) == 2


# ── One source per tool call ────────────────────────────────────────────────

def _log_tool_call(session_id, tool="bash"):
    return [
        _log_record("support_agent.tool_decision", session_id,
                    [_kv("tool_name", s=tool), _kv("decision", s="accept")]),
        _log_record("support_agent.tool_result", session_id,
                    [_kv("tool_name", s=tool), _kv("success", s="true")]),
    ]


def test_logs_then_traces_count_each_tool_call_once(store):
    """
    AC-OBS-OTG-001.3
    """
    _d._process_otlp_logs(_logs(_log_tool_call("conv-both")))
    _d._process_otlp_traces(_traces([
        _tool_span(0x50, "bash", {"command": "ls"}, conv="conv-both"),
    ]))
    tool = _tool_events(store, "conv-both")
    assert [e["event_type"] for e in tool].count("tool_call") == 1
    assert not [e for e in tool if str(e["id"]).startswith("otlp:span:")]


def test_traces_then_logs_count_each_tool_call_once(store):
    """
    AC-OBS-OTG-001.3
    """
    _d._process_otlp_traces(_traces([
        _tool_span(0x51, "bash", {"command": "ls"}, conv="conv-both2"),
    ]))
    _d._process_otlp_logs(_logs(_log_tool_call("conv-both2")))
    tool = _tool_events(store, "conv-both2")
    assert [e["event_type"] for e in tool].count("tool_call") == 1
    assert all(str(e["id"]).startswith("otlp:span:") for e in tool)


def test_a_session_the_daemon_observes_keeps_the_daemon_copy(store):
    """
    AC-OBS-OTG-001.3
    """
    store.ingest({
        "id": "daemon-evt-otg", "node_id": "n1", "agent_type": "support_agent",
        "session_id": "conv-daemon", "event_type": "tool_call",
        "ts": "2026-09-14T10:00:00+00:00",
        "data": {"tool": "bash", "args": {"command": "ls"}},
    })
    store._flush_now()
    _d._process_otlp_traces(_traces([
        _tool_span(0x52, "bash", {"command": "ls"}, conv="conv-daemon"),
    ]))
    assert [e["id"] for e in _tool_events(store, "conv-daemon")] == ["daemon-evt-otg"]


# ── Scrubbed before it rests ────────────────────────────────────────────────

def test_span_payloads_are_scrubbed_before_storage(store):
    """Prompts, responses, tool arguments, URL / header / path attributes,
    exception events and the status message, all in one export.

    AC-OBS-OTG-001.4
    """
    prompt = json.dumps([{"role": "user", "content":
                          "I am %s and my key is %s" % (EMAIL, ANTHROPIC_KEY)}])
    reply = json.dumps([{"role": "assistant", "content": "I will email " + EMAIL}])
    _d._process_otlp_traces(_traces([
        _chat_span(0x61, "conv-scrub", extra=[
            _kv("gen_ai.input.messages", s=prompt),
            _kv("gen_ai.output.messages", s=reply),
            _kv("url.full", s="https://api.example.net/v1/items?access_token=" + URL_TOKEN),
            _kv("http.request.header.authorization", arr=["Basic " + BASIC]),
            _kv("file.path", s="/srv/exports/" + EMAIL + "/report.csv"),
        ], error="upstream refused Bearer " + BEARER, events=[
            ("exception", [
                _kv("exception.type", s="AuthError"),
                _kv("exception.message", s="key %s rejected for %s" % (ANTHROPIC_KEY, EMAIL)),
            ]),
        ]),
        _tool_span(0x62, "http_request", {
            "command": "curl -H 'Authorization: Bearer %s' https://api.example.net" % BEARER,
            "notify": EMAIL,
        }, conv="conv-scrub", off_s=1),
    ]))

    spans = store.query_spans(session_id="conv-scrub", limit=10)
    assert len(spans) == 2
    stored = json.dumps(spans, default=str)
    for canary in CANARIES:
        assert canary not in stored, "%s rested unscrubbed in spans" % canary
    # Scrubbed, not dropped: the placeholders are there and the structure a
    # reader needs is intact.
    assert "[email]" in stored and "[REDACTED:" in stored
    by_name = {s["name"]: s for s in spans}
    chat = by_name["chat gpt-4o"]
    assert chat["model"] == "gpt-4o"
    assert chat["tokens_input"] == 120
    assert chat["trace_id"] == "11" * 16
    assert chat["status_code"] == "ERROR"
    assert by_name["execute_tool http_request"]["tool_name"] == "http_request"
    assert "clawmetry.redaction" not in (chat.get("attributes") or {})

    # The events Guard reads are scrubbed too (the event chokepoint).
    events = json.dumps(store.query_events(session_id="conv-scrub", limit=50), default=str)
    assert "http_request" in events
    for canary in CANARIES:
        assert canary not in events


def test_the_log_record_ledger_is_scrubbed_and_keeps_its_identity(store):
    """
    AC-OBS-OTG-001.4
    """
    _d._process_otlp_logs(_logs([
        _log_record("support_agent.user_prompt", "conv-ledger", [
            _kv("user.email", s=EMAIL),
            _kv("prompt", s="deploy with key " + ANTHROPIC_KEY + " and mail " + EMAIL),
        ]),
    ]))
    rows = store.query_otlp_records(session_id="conv-ledger")
    assert len(rows) == 1
    row = rows[0]
    # Identity is retained as sent (AC-OBS-006.2), in the column and its copy.
    assert row["user_email"] == EMAIL
    assert row["attributes"]["record"]["user.email"] == EMAIL
    prompt = row["attributes"]["record"]["prompt"]
    assert ANTHROPIC_KEY not in prompt and EMAIL not in prompt
    assert "[REDACTED:" in prompt and "[email]" in prompt


def test_a_value_too_large_to_scan_is_withheld_and_marked(store, monkeypatch):
    """
    AC-OBS-OTG-001.5
    """
    from clawmetry import redaction

    monkeypatch.setattr(redaction, "_MAX_SCAN", 256)
    big = "padding " * 64 + EMAIL
    _d._process_otlp_traces(_traces([
        _chat_span(0x71, "conv-big", extra=[_kv("gen_ai.input.messages", s=big)]),
    ]))
    span = store.query_spans(session_id="conv-big", limit=1)[0]
    stored = json.dumps(span, default=str)
    assert EMAIL not in stored
    assert redaction.WITHHELD_TOO_LARGE in stored
    assert span["attributes"]["clawmetry.redaction"] == "withheld:too_large"


def test_a_scrubber_failure_withholds_instead_of_storing_raw(store, monkeypatch):
    """
    AC-OBS-OTG-001.5
    """
    from clawmetry import redaction

    def _boom(text):
        raise RuntimeError("scanner broke")

    monkeypatch.setattr(redaction, "_scrub_text", _boom)
    store.put_span(span={
        "span_id": "e1" * 8, "trace_id": "e2" * 16, "name": "chat",
        "start_ts": time.time(), "session_id": "conv-err",
        "agent_type": "support_agent",
        "input": "my email is " + EMAIL,
        "attributes": {"gen_ai.request.model": "gpt-4o", "note": EMAIL},
    })
    span = store.query_spans(session_id="conv-err", limit=1)[0]
    stored = json.dumps(span, default=str)
    assert EMAIL not in stored
    assert redaction.WITHHELD_ERROR in stored
    assert span["attributes"]["clawmetry.redaction"] == "withheld:error"
    assert span["span_id"] == "e1" * 8


def test_redaction_switched_off_stores_spans_as_received(store, monkeypatch):
    """The operator's choice, matching the event path.

    AC-OBS-OTG-001.5
    """
    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    store.put_span(span={
        "span_id": "f1" * 8, "trace_id": "f2" * 16, "name": "chat",
        "start_ts": time.time(), "session_id": "conv-raw",
        "agent_type": "support_agent", "input": "my email is " + EMAIL,
    })
    span = store.query_spans(session_id="conv-raw", limit=1)[0]
    assert EMAIL in json.dumps(span, default=str)
    assert "clawmetry.redaction" not in json.dumps(span, default=str)


def test_an_unchanged_span_resent_is_not_scanned_again(store, monkeypatch):
    """Runtime adapters re-send unchanged spans every tick. Scanning them again
    would spend the daemon's CPU budget for no change in what is stored."""
    from clawmetry import redaction

    calls = []
    real = redaction.redact_span
    monkeypatch.setattr(redaction, "redact_span",
                        lambda span: calls.append(1) or real(span))
    span = {"span_id": "a1" * 8, "trace_id": "a2" * 16, "name": "chat",
            "start_ts": 1_700_000_000.0, "session_id": "conv-tick",
            "agent_type": "support_agent", "input": "hello " + EMAIL}
    store.put_span(span=dict(span))
    store.put_span(span=dict(span))
    assert len(calls) == 1
    store.put_span(span=dict(span, input="changed " + EMAIL))
    assert len(calls) == 2
    stored = store.query_spans(session_id="conv-tick", limit=1)[0]
    assert "changed" in json.dumps(stored) and EMAIL not in json.dumps(stored)
