"""REQ-OBS-OTG-001, the gaps left after 0.12.878 (vivekchand/clawmetry#5938).

1. **Hosted parity.** A Guard incident raised from a received span has to
   reach app.clawmetry.com, which has no store and no OTLP receiver. The path
   is span -> tool event -> detector pass -> ``loop_signals`` row -> the
   ``/api/guard/sessions`` body built on the node -> the ``guardSessions``
   slice of the ENCRYPTED system snapshot -> the hosted ``cm-cloud-guard``
   interceptor. The test below runs the real receiver, the real detector pass
   and the real ``sync_system_snapshot``, captures the blob it would POST,
   decrypts it, and reads the row the way the interceptor does (runtime
   filter included).
2. **One source per tool call**, deterministically: a call both signals name
   by call id is recorded once, from the span, in either arrival order; a
   call only one signal reports is not dropped.
3. **Content profile** ``CLAWMETRY_OTLP_CONTENT=full|redacted|metadata``, with
   secret masking and personal-data filtering kept separate.
4. **Rescrub** of spans stored before scrubbing existed: explicit, a dry run
   until applied, content columns only.

No shell command runs anywhere here; destructive commands are strings inside
span attributes.
"""
import argparse
import importlib
import json
import os
import pathlib
import tempfile
import threading
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

SERVICE = "support-agent"
RUNTIME = "support_agent"
EMAIL = "dana.canary@example.com"
ANTHROPIC_KEY = "sk-ant-CANARYnotarealkey000000000000"
# Any 32-byte key; encrypt_payload decodes it base64url-style.
ENC_KEY = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcd"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in ("CLAWMETRY_REDACT", "CLAWMETRY_REDACT_PII", "CLAWMETRY_OTLP_CONTENT"):
        monkeypatch.delenv(var, raising=False)
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()


@pytest.fixture()
def store(monkeypatch):
    ls = importlib.import_module("clawmetry.local_store")
    tmpdir = tempfile.mkdtemp(prefix="clawmetry-otg2-")
    path = os.path.join(tmpdir, "otg2.duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", path)
    ls._reset_singleton_for_tests()
    prev = ls.DB_PATH
    ls.DB_PATH = pathlib.Path(path)
    st = ls.LocalStore()
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: st)
    try:
        yield st
    finally:
        try:
            st.stop(flush=True)
        except Exception:
            pass
        ls.DB_PATH = prev
        ls._reset_singleton_for_tests()


# ── OTLP builders ───────────────────────────────────────────────────────────

def _kv(key, s=None, i=None):
    v = common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    return common_pb2.KeyValue(key=key, value=v)


def _span(span_seed, name, attrs, *, trace_seed=0x11, off_s=0.0, dur_s=0.5,
          error=None, events=()):
    base = time.time() - 30
    sp = trace_pb2.Span(
        trace_id=bytes([trace_seed]) * 16, span_id=bytes([span_seed]) * 8,
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


def _chat_span(span_seed, conv, extra=(), **kw):
    attrs = [
        _kv("gen_ai.operation.name", s="chat"),
        _kv("gen_ai.request.model", s="gpt-4o"),
        _kv("gen_ai.usage.input_tokens", i=120),
        _kv("gen_ai.usage.output_tokens", i=30),
        _kv("gen_ai.conversation.id", s=conv),
    ] + list(extra)
    return _span(span_seed, "chat gpt-4o", attrs, **kw)


def _tool_span(span_seed, tool, args, conv, call_id=None, extra=(), **kw):
    attrs = [
        _kv("gen_ai.operation.name", s="execute_tool"),
        _kv("gen_ai.tool.name", s=tool),
        _kv("gen_ai.conversation.id", s=conv),
        _kv("gen_ai.tool.call.id", s=call_id or ("call-%d" % span_seed)),
    ]
    if args is not None:
        attrs.append(_kv("gen_ai.tool.call.arguments", s=json.dumps(args)))
    attrs.extend(extra)
    return _span(span_seed, "execute_tool " + tool, attrs, **kw)


def _traces(spans):
    res = trace_pb2.ResourceSpans(scope_spans=[trace_pb2.ScopeSpans(spans=spans)])
    res.resource.attributes.extend([_kv("service.name", s=SERVICE)])
    return trace_service_pb2.ExportTraceServiceRequest(resource_spans=[res]).SerializeToString()


def _logs(records):
    res = logs_pb2.ResourceLogs(scope_logs=[logs_pb2.ScopeLogs(log_records=records)])
    res.resource.attributes.extend([_kv("service.name", s=SERVICE)])
    return logs_service_pb2.ExportLogsServiceRequest(resource_logs=[res]).SerializeToString()


def _log_record(event_name, session_id, attrs):
    rec = logs_pb2.LogRecord(time_unix_nano=int((time.time() - 20) * 1e9))
    rec.event_name = event_name
    rec.attributes.extend([_kv("session.id", s=session_id)] + list(attrs))
    return rec


def _log_call(session_id, call_id, tool="bash"):
    """A tool call as a log exporter sends it: decision then result, no args."""
    return [
        _log_record("support_agent.tool_decision", session_id, [
            _kv("tool_name", s=tool), _kv("decision", s="accept"),
            _kv("call_id", s=call_id)]),
        _log_record("support_agent.tool_result", session_id, [
            _kv("tool_name", s=tool), _kv("success", s="true"),
            _kv("call_id", s=call_id)]),
    ]


def _tool_events(store, session_id):
    return [e for e in store.query_events(session_id=session_id, limit=500)
            if e["event_type"] in ("tool_call", "tool_result")]


def _guard_tick(store, monkeypatch):
    from clawmetry import incident_alerts as _ia
    from clawmetry import sync as _sync

    monkeypatch.setattr(_ia, "deliver_incident",
                        lambda st, inc, **kw: {"delivered_via": []})
    monkeypatch.setattr(_sync, "_apply_guard_policies",
                        lambda st, state, incs, facts: 0)
    _sync._emit_detector_incidents(store, {})


# ── 1. Hosted parity ────────────────────────────────────────────────────────

def _hosted_guard_rows(snapshot, runtime=""):
    """What cm-cloud-guard serves for GET /api/guard/sessions?runtime=<rt>:
    ``snapshot.guardSessions.sessions`` filtered on ``row.runtime``."""
    gs = snapshot.get("guardSessions")
    assert isinstance(gs, dict) and isinstance(gs.get("sessions"), list), (
        "no guardSessions slice: the hosted tab would say it is waiting for the node")
    rt = runtime.lower()
    return [r for r in gs["sessions"]
            if isinstance(r, dict) and (not rt or rt == "all"
                                         or str(r.get("runtime") or "").lower() == rt)]


def test_a_span_raised_incident_reaches_the_hosted_guard_tab_through_the_encrypted_snapshot(
        store, monkeypatch, tmp_path):
    """
    AC-OBS-OTG-001.7
    AC-OBS-OTG-001.6
    """
    from clawmetry import config as _config
    from clawmetry import sync
    import routes.guard as guard

    _d._process_otlp_traces(_traces([
        _chat_span(0x01, "conv-hosted"),
        _tool_span(0x02, "bash", {"command": "rm -rf /"}, "conv-hosted", off_s=1),
    ]))
    _guard_tick(store, monkeypatch)

    signals = [r for r in store.query_recent_loop_signals(limit=200, since_minutes=0)
               if r.get("session_id") == "conv-hosted"]
    assert any(r["signature"] == "daemon_detect_file_blast_radius" for r in signals)
    # Filed under the runtime the telemetry names, not the Free-install guess.
    assert {r["agent_type"] for r in signals} == {RUNTIME}

    posted = []
    monkeypatch.setattr(sync, "_post",
                        lambda path, body, key, **kw: posted.append((path, body)))
    monkeypatch.setattr(sync, "_sync_allowed", lambda: True)
    monkeypatch.setattr(_config, "is_cloud_disabled", lambda: False)
    monkeypatch.setattr(guard, "_live_only_rows", lambda rows: [])
    rc = sync.sync_system_snapshot(
        {"api_key": "k", "node_id": "n1", "encryption_key": ENC_KEY},
        state={"spending": {"today": 0, "week": 0, "month": 0}},
        paths={"workspace": str(tmp_path), "sessions_dir": str(tmp_path)},
    )
    assert rc == 1 and posted, "the snapshot was not sent"
    path, body = posted[-1]
    assert path == "/ingest/system-snapshot" and body["encrypted"] is True
    # What leaves the machine is ciphertext: the incident is not readable in it.
    assert "conv-hosted" not in json.dumps(body)

    snapshot = sync.decrypt_payload(body["blob"], ENC_KEY)

    rows = [r for r in _hosted_guard_rows(snapshot, RUNTIME)
            if r["session_id"] == "conv-hosted"]
    assert len(rows) == 1, "the hosted Guard tab filtered to this runtime does not list it"
    row = rows[0]
    inc = row["incident"]
    assert inc and inc["kind"] == "file_blast_radius"
    assert inc["severity"] == "critical"
    assert inc["observation"] == {
        "source": "received_telemetry", "signals": ["trace"],
        "after_the_fact": True, "prevented": False,
    }
    assert "did not hold or block it" in inc["detail"]
    # Nothing on any machine can signal an agent seen only through telemetry.
    assert row["controllable"] is False
    assert row["control_state"] == "unsupported"
    assert row["control_actions"] == []
    assert "telemetry" in row["control_reason"]
    assert snapshot["guardSessions"]["flagged"] >= 1
    # And it is not misfiled under the runtime a Free install guesses.
    assert not [r for r in _hosted_guard_rows(snapshot, "openclaw")
                if r["session_id"] == "conv-hosted"]


def test_the_guard_tab_says_an_observed_incident_was_seen_after_it_ran():
    """
    AC-OBS-OTG-001.6
    AC-OBS-OTG-001.7
    """
    root = pathlib.Path(__file__).resolve().parent.parent
    js = (root / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    fn = js[js.index("function loadGuardSessions()"):]
    fn = fn[:fn.index("\n}\n")]
    assert "inc.observation.prevented === false" in fn
    assert "seen after it ran" in fn


# ── 2. One source per tool call ─────────────────────────────────────────────

@pytest.mark.parametrize("order", ["logs_first", "traces_first"])
def test_a_call_both_signals_identify_is_recorded_once_from_the_span(store, order):
    """
    AC-OBS-OTG-001.8
    AC-OBS-OTG-001.3
    """
    from clawmetry import otlp_sources

    conv = "conv-pair-" + order
    trace = _traces([_tool_span(0x70, "bash", {"command": "ls -la /srv"}, conv,
                                call_id="call-pair")])
    logs = _logs(_log_call(conv, "call-pair"))
    if order == "logs_first":
        _d._process_otlp_logs(logs)
        _d._process_otlp_traces(trace)
    else:
        _d._process_otlp_traces(trace)
        _d._process_otlp_logs(logs)

    tool = _tool_events(store, conv)
    calls = [e for e in tool if e["event_type"] == "tool_call"]
    results = [e for e in tool if e["event_type"] == "tool_result"]
    assert len(calls) == 1 and len(results) == 1, tool
    assert calls[0]["id"] == otlp_sources.call_event_id(conv, "call-pair", "call")
    assert results[0]["id"] == otlp_sources.call_event_id(conv, "call-pair", "result")
    # The span's copy, whichever arrived first: arguments and trace identity.
    assert calls[0]["data"]["_otlp_signal"] == "trace"
    assert calls[0]["data"]["args"] == {"command": "ls -la /srv"}
    assert calls[0]["data"]["span_id"] == "70" * 8
    assert results[0]["data"]["_otlp_signal"] == "trace"


def test_a_call_only_one_signal_reports_is_not_dropped(store):
    """
    AC-OBS-OTG-001.8
    """
    _d._process_otlp_traces(_traces([
        _tool_span(0x71, "bash", {"command": "ls"}, "conv-mixed", call_id="call-both"),
    ]))
    _d._process_otlp_logs(_logs(
        _log_call("conv-mixed", "call-both") + _log_call("conv-mixed", "call-logs-only",
                                                         tool="read_file")))
    calls = [e for e in _tool_events(store, "conv-mixed") if e["event_type"] == "tool_call"]
    assert sorted((c["data"]["tool"], c["data"]["_otlp_signal"]) for c in calls) == [
        ("bash", "trace"), ("read_file", "log")]


def test_replacing_the_log_copy_keeps_the_tamper_evident_chain_valid(store):
    """
    AC-OBS-OTG-001.8
    """
    _d._process_otlp_logs(_logs(_log_call("conv-chain", "call-chain")))
    _d._process_otlp_traces(_traces([
        _tool_span(0x72, "bash", {"command": "pwd"}, "conv-chain", call_id="call-chain"),
    ]))
    store._flush_now()
    verdict = store.verify_integrity()
    assert verdict["status"] in ("valid", "empty"), verdict


def test_two_exports_arriving_together_record_each_call_once(store):
    """
    AC-OBS-OTG-001.8
    """
    conv = "conv-race"
    ids = ["call-race-%d" % n for n in range(4)]
    trace = _traces([_tool_span(0x80 + n, "bash", {"command": "echo %d" % n}, conv,
                                call_id=cid, off_s=n) for n, cid in enumerate(ids)])
    logs = _logs([rec for cid in ids for rec in _log_call(conv, cid)])
    workers = [threading.Thread(target=_d._process_otlp_logs, args=(logs,)),
               threading.Thread(target=_d._process_otlp_traces, args=(trace,))]
    for w in workers:
        w.start()
    for w in workers:
        w.join(60)
    calls = [e for e in _tool_events(store, conv) if e["event_type"] == "tool_call"]
    assert len(calls) == len(ids)
    assert {c["data"]["_otlp_signal"] for c in calls} == {"trace"}


# ── 3. Content profile ──────────────────────────────────────────────────────

def _prompt_trace(conv, extra_chat=(), tool_args=None):
    prompt = json.dumps([{"role": "user", "content":
                          "I am %s and my key is %s" % (EMAIL, ANTHROPIC_KEY)}])
    return _traces([
        _chat_span(0x91, conv, extra=[_kv("gen_ai.input.messages", s=prompt)] + list(extra_chat),
                   error="refused for " + EMAIL,
                   events=[("exception", [_kv("exception.type", s="AuthError"),
                                          _kv("exception.message", s="bad key for " + EMAIL)])]),
        _tool_span(0x92, "http_request", tool_args or {"notify": EMAIL, "token": ANTHROPIC_KEY},
                   conv, off_s=1),
    ])


def test_full_profile_keeps_personal_data_but_still_masks_secrets(store, monkeypatch):
    """
    AC-OBS-OTG-001.9
    """
    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "full")
    _d._process_otlp_traces(_prompt_trace("conv-full"))
    _d._process_otlp_logs(_logs([_log_record("support_agent.user_prompt", "conv-full", [
        _kv("prompt", s="mail %s with key %s" % (EMAIL, ANTHROPIC_KEY))])]))

    spans = json.dumps(store.query_spans(session_id="conv-full", limit=10), default=str)
    events = json.dumps(store.query_events(session_id="conv-full", limit=50), default=str)
    ledger = json.dumps(store.query_otlp_records(session_id="conv-full"), default=str)
    for stored in (spans, events, ledger):
        assert EMAIL in stored, "full keeps personal data as sent"
        assert ANTHROPIC_KEY not in stored, "no content profile relaxes secret masking"
    chat = [s for s in store.query_spans(session_id="conv-full", limit=10)
            if s["name"] == "chat gpt-4o"][0]
    assert chat["attributes"]["clawmetry.content"] == "full"


def test_full_profile_is_still_bound_by_the_secret_switch(store, monkeypatch):
    """Secret masking follows only CLAWMETRY_REDACT.

    AC-OBS-OTG-001.9
    """
    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "redacted")
    monkeypatch.setenv("CLAWMETRY_REDACT_PII", "0")
    _d._process_otlp_traces(_prompt_trace("conv-pii-off"))
    spans = json.dumps(store.query_spans(session_id="conv-pii-off", limit=10), default=str)
    assert EMAIL in spans and ANTHROPIC_KEY not in spans


def test_metadata_profile_stores_no_content_and_labels_what_it_withheld(store, monkeypatch):
    """
    AC-OBS-OTG-001.9
    """
    from clawmetry import otlp_content

    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "metadata")
    _d._process_otlp_traces(_prompt_trace(
        "conv-meta", extra_chat=[_kv("url.full", s="https://api.example.net/u/" + EMAIL)]))
    _d._process_otlp_logs(_logs([_log_record("support_agent.user_prompt", "conv-meta", [
        _kv("user.email", s=EMAIL), _kv("prompt", s="deploy it please")])]))

    spans = store.query_spans(session_id="conv-meta", limit=10)
    stored = json.dumps(spans, default=str)
    for text in (EMAIL, ANTHROPIC_KEY, "I am", "refused for", "bad key"):
        assert text not in stored, "%r stored under the metadata profile" % text
    chat = [s for s in spans if s["name"] == "chat gpt-4o"][0]
    # Metadata survives: model, tokens, timing, status, exception type.
    assert chat["model"] == "gpt-4o" and chat["tokens_input"] == 120
    assert chat["status_code"] == "ERROR"
    assert chat["attributes"]["clawmetry.content"] == "metadata"
    withheld = chat["attributes"]["clawmetry.content.withheld"]
    assert {"gen_ai.input.messages", "url.full", "input", "status_message",
            "exception.message"} <= set(withheld)
    assert chat["events"][0]["attributes"]["exception.type"] == "AuthError"
    assert chat["events"][0]["attributes"]["exception.message"] == otlp_content.WITHHELD

    calls = [e for e in _tool_events(store, "conv-meta") if e["event_type"] == "tool_call"]
    assert len(calls) == 1
    assert calls[0]["data"]["tool"] == "http_request"
    assert calls[0]["data"]["content_withheld"] == "metadata"
    assert calls[0]["data"]["args"].get("_otlp_args_unknown") is True

    ledger = store.query_otlp_records(session_id="conv-meta")[0]
    assert ledger["attributes"]["record"]["prompt"] == otlp_content.WITHHELD
    assert ledger["user_email"] == EMAIL  # identity kept as sent (AC-OBS-006.2)


def test_an_exporter_cannot_claim_a_content_profile(store):
    """
    AC-OBS-OTG-001.9
    """
    _d._process_otlp_traces(_prompt_trace(
        "conv-spoof", extra_chat=[_kv("clawmetry.content", s="full")]))
    spans = store.query_spans(session_id="conv-spoof", limit=10)
    stored = json.dumps(spans, default=str)
    assert EMAIL not in stored and ANTHROPIC_KEY not in stored
    assert all("clawmetry.content" not in (s.get("attributes") or {}) for s in spans)


def test_the_posture_names_the_profile_and_what_is_not_detected(monkeypatch):
    """
    AC-OBS-OTG-001.9
    """
    from clawmetry import otlp_content, security_posture

    check = otlp_content.posture_check()
    assert check["profile"] == "redacted" and check["status"] == "pass"
    assert "names" in check["detail"] and "street addresses" in check["detail"]
    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "metdata")
    check = otlp_content.posture_check()
    assert check["profile"] == "redacted" and check["status"] == "warn"
    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "full")
    assert otlp_content.posture_check()["status"] == "warn"
    monkeypatch.setenv("CLAWMETRY_OTLP_CONTENT", "metadata")
    assert otlp_content.posture_check()["status"] == "pass"
    env = security_posture._with_node_checks({"checks": []})
    assert "otlp_content" in {c["id"] for c in env["checks"]}
    for c in env["checks"]:
        assert "—" not in json.dumps(c)


# ── 4. Rescrub of spans stored before scrubbing ─────────────────────────────

def _raw_span_row(store, span_id):
    return store._fetch(
        "SELECT content_hash, cost_usd, tokens_input, model, start_ts, input, attributes "
        "FROM spans WHERE span_id = ?", [span_id])[0]


def test_rescrub_is_a_dry_run_until_applied_and_rewrites_content_only(store, monkeypatch):
    """
    AC-OBS-OTG-001.10
    """
    from clawmetry import span_rescrub

    # A span stored the way pre-0.12.878 stored it: as received.
    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    store.put_span(span={
        "span_id": "b1" * 8, "trace_id": "b2" * 16, "name": "chat",
        "start_ts": 1_700_000_000.0, "session_id": "conv-old", "agent_type": RUNTIME,
        "model": "gpt-4o", "cost_usd": 0.5, "tokens_input": 10,
        "input": "my email is %s and key %s" % (EMAIL, ANTHROPIC_KEY),
        "attributes": {"note": EMAIL},
    })
    store.put_span(span={
        "span_id": "c1" * 8, "trace_id": "c2" * 16, "name": "chat",
        "start_ts": 1_700_000_001.0, "session_id": "conv-old", "agent_type": RUNTIME,
        "input": "nothing sensitive here",
    })
    monkeypatch.delenv("CLAWMETRY_REDACT")
    before = _raw_span_row(store, "b1" * 8)

    dry = span_rescrub.run(store.rescrub_spans, apply=False, batch=1)
    assert dry == {"scanned": 2, "changed": 1, "withheld": 0, "applied": False}
    assert "Nothing was changed" in span_rescrub.summary(dry)
    assert EMAIL in json.dumps(store.query_spans(session_id="conv-old", limit=5), default=str)

    done = span_rescrub.run(store.rescrub_spans, apply=True, batch=1)
    assert done["changed"] == 1 and done["applied"] is True
    assert "not affected" in span_rescrub.summary(done)
    stored = json.dumps(store.query_spans(session_id="conv-old", limit=5), default=str)
    assert EMAIL not in stored and ANTHROPIC_KEY not in stored
    assert "nothing sensitive here" in stored
    after = _raw_span_row(store, "b1" * 8)
    # Identity, money, time and the received-content hash are untouched.
    assert after[:5] == before[:5]

    again = span_rescrub.run(store.rescrub_spans, apply=False, batch=1)
    assert again["changed"] == 0


def test_rescrub_refuses_when_redaction_is_off(store, monkeypatch):
    """
    AC-OBS-OTG-001.10
    """
    from clawmetry import span_rescrub

    monkeypatch.setenv("CLAWMETRY_REDACT", "0")
    totals = span_rescrub.run(store.rescrub_spans, apply=True)
    assert totals["error"] == span_rescrub.REFUSED_REDACTION_OFF
    assert totals["applied"] is False
    assert "CLAWMETRY_REDACT=0" in span_rescrub.summary(totals)


def test_the_rescrub_command_is_explicit_and_served_by_the_daemon(store, monkeypatch, capsys):
    """
    AC-OBS-OTG-001.10
    """
    from clawmetry import span_rescrub
    from routes.local_query import _DAEMON_METHODS, _RPC_MEMO_METHODS

    assert "rescrub_spans" in _DAEMON_METHODS
    assert "rescrub_spans" not in _RPC_MEMO_METHODS  # a write is never served from a memo
    monkeypatch.setattr(span_rescrub, "_caller", lambda: store.rescrub_spans)
    code = span_rescrub.cmd_maintenance(argparse.Namespace(
        maintenance_cmd="rescrub-spans", apply=False, batch=50, as_json=True))
    out = json.loads(capsys.readouterr().out)
    assert code == 0 and out["applied"] is False and "Dry run" in out["message"]
    src = (pathlib.Path(__file__).resolve().parent.parent / "clawmetry" / "cli.py").read_text(
        encoding="utf-8")
    assert '"rescrub-spans"' in src and '"--apply"' in src
