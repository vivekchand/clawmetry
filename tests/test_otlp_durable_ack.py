"""REQ-OBS-OIA-001: an OpenTelemetry sender knows what was kept.

Before this, ``/v1/logs``, ``/v1/traces`` and ``/v1/metrics`` answered 200 to
every export that decoded. The store write behind that answer was best effort:
when the daemon that owns DuckDB could not be reached (``_ProxyStore`` returns
``None``), the write was dropped with a warning and the exporter, told the
batch had arrived, threw it away. A spending-limit pause answered 429 to every
export for as long as it lasted, a retried span added its cost to the live
tiles twice, and a record with no output-token count stored 0.

Every test drives the real receiver route (``routes/meta.py::_otlp_receive``)
over the real mappers, and, where it matters, the real DuckDB store and the
real daemon proxy class with no daemon behind it. Nothing is simulated that the
production path does not do.

Acceptance criteria declared here:

* AC-OBS-OIA-001.1 -- an export is acknowledged only once stored; 503 plus
  Retry-After otherwise, and a retry lands exactly once:
  ``test_logs_export_the_store_never_took_is_503_then_lands_once_on_retry``,
  ``test_traces_export_the_proxy_lost_is_503_then_lands_once``,
  ``test_a_store_that_raises_is_503``,
  ``test_a_failed_event_flush_is_not_acknowledged``,
  ``test_profile_metrics_the_store_never_took_are_503``.
* AC-OBS-OIA-001.2 -- partial refusal, malformed body, authentication:
  ``test_one_malformed_span_is_refused_and_the_rest_are_stored``,
  ``test_protobuf_sender_gets_a_protobuf_partial_success``,
  ``test_a_span_the_store_cannot_hold_is_refused_and_the_valid_span_is_stored``,
  ``test_a_log_record_the_store_cannot_hold_is_refused_not_retried_forever``,
  ``test_a_span_write_the_store_itself_failed_is_still_503``,
  ``test_one_unstorable_span_keeps_the_rest_of_the_batch``,
  ``test_an_undecodable_body_is_400_and_counted``,
  ``test_a_remote_request_without_a_token_is_401_and_counted``.
* AC-OBS-OIA-001.3 -- re-delivery changes nothing; distinct calls stay two:
  ``test_redelivered_log_export_changes_no_total_and_no_tile``,
  ``test_two_distinct_model_calls_are_two_charges``,
  ``test_redelivered_span_lights_the_tiles_once``,
  ``test_redelivered_metric_point_lights_the_tiles_once``.
* AC-OBS-OIA-001.4 -- intake status, with no content and no credentials:
  ``test_intake_status_counts_and_never_repeats_content``.
* AC-OBS-OIA-001.5 -- a budget pause does not pause intake:
  ``test_a_budget_pause_does_not_stop_intake``.
* AC-OBS-OIA-001.6 -- unknown usage is not zero:
  ``test_unreported_usage_is_unknown_not_zero``.
* AC-OBS-OIA-001.7 -- sampled traces do not reduce the spend rollup:
  ``test_sampled_spans_do_not_change_spend_from_unsampled_log_records``.
* AC-OBS-OIA-001.8 -- the generated reference states the rules:
  ``test_generated_reference_states_ack_retry_identity_and_session_rules``.
"""
import importlib
import json
import os
import pathlib
import tempfile
import time

import pytest

pytest.importorskip(
    "opentelemetry.proto.collector.logs.v1.logs_service_pb2",
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)

from opentelemetry.proto.collector.logs.v1 import logs_service_pb2  # noqa: E402
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2  # noqa: E402
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2  # noqa: E402
from opentelemetry.proto.common.v1 import common_pb2  # noqa: E402
from opentelemetry.proto.logs.v1 import logs_pb2  # noqa: E402
from opentelemetry.proto.metrics.v1 import metrics_pb2  # noqa: E402
from opentelemetry.proto.trace.v1 import trace_pb2  # noqa: E402

import flask  # noqa: E402

import dashboard as _d  # noqa: E402
from clawmetry import otlp_intake  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[1]
PB = "application/x-protobuf"


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clean_module_state(monkeypatch):
    """The live-tile dedup set and the intake counters are process state. Left
    dirty, one test's export would read as a re-delivery in the next."""
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    otlp_intake.reset_for_tests()
    monkeypatch.setattr(_d, "_budget_paused", False, raising=False)
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    otlp_intake.reset_for_tests()


@pytest.fixture()
def ls():
    # Re-resolve: other suites reload clawmetry.local_store, which would leave
    # a module-level import here pointing at a stale copy.
    return importlib.import_module("clawmetry.local_store")


@pytest.fixture()
def store(monkeypatch, ls):
    """A private DuckDB writer wired in as the singleton the mappers resolve."""
    tmpdir = tempfile.mkdtemp(prefix="clawmetry-oia-")
    path = os.path.join(tmpdir, "oia.duckdb")
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


@pytest.fixture()
def unreachable_daemon(monkeypatch, ls):
    """Install the REAL dashboard-side proxy with no daemon behind it: what a
    receiver sees while the daemon restarts. Every write returns None."""
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    proxy = ls._ProxyStore()
    monkeypatch.setattr(ls, "get_store", lambda read_only=False: proxy)
    return proxy


@pytest.fixture()
def client():
    import routes.meta as meta
    app = flask.Flask(__name__)
    app.register_blueprint(meta.bp_otel)
    return app.test_client()


@pytest.fixture()
def tiles(monkeypatch):
    captured = []
    monkeypatch.setattr(_d, "_add_metric", lambda cat, e: captured.append((cat, e)))
    return captured


# ── builders ────────────────────────────────────────────────────────────────

def _kv(key, s=None, i=None, d=None):
    v = common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    elif d is not None:
        v.double_value = d
    return common_pb2.KeyValue(key=key, value=v)


def _api_request(when_s, session_id="sess-oia", cost=4.10, tin=1500, tout=300,
                 extra=()):
    rec = logs_pb2.LogRecord(time_unix_nano=int(when_s * 1e9))
    rec.event_name = "claude_code.api_request"
    attrs = [_kv("session.id", s=session_id), _kv("model", s="claude-opus-4-8")]
    if cost is not None:
        attrs.append(_kv("cost_usd", d=cost))
    if tin is not None:
        attrs.append(_kv("input_tokens", i=tin))
    if tout is not None:
        attrs.append(_kv("output_tokens", i=tout))
    attrs.extend(extra)
    rec.attributes.extend(attrs)
    return rec


def _logs(records, team="platform"):
    res = logs_pb2.ResourceLogs(scope_logs=[logs_pb2.ScopeLogs(log_records=records)])
    res.resource.attributes.extend([
        _kv("service.name", s="claude-code"), _kv("team.id", s=team),
    ])
    return logs_service_pb2.ExportLogsServiceRequest(
        resource_logs=[res]).SerializeToString()


def _span(span_hex, trace_hex="ab" * 16, name="codex.api_request", cost=None,
          session_id="sess-oia", start_s=None):
    start = int((start_s or time.time()) * 1e9)
    sp = trace_pb2.Span(
        trace_id=bytes.fromhex(trace_hex) if trace_hex else b"",
        span_id=bytes.fromhex(span_hex) if span_hex else b"",
        name=name, start_time_unix_nano=start,
        end_time_unix_nano=start + 250_000_000,
    )
    attrs = [_kv("gen_ai.conversation.id", s=session_id),
             _kv("gen_ai.request.model", s="gpt-5.4")]
    if cost is not None:
        attrs += [_kv("cost_usd", d=cost), _kv("input_tokens", i=100),
                  _kv("output_tokens", i=20)]
    sp.attributes.extend(attrs)
    return sp


def _traces(spans):
    rs = trace_pb2.ResourceSpans(scope_spans=[trace_pb2.ScopeSpans(spans=spans)])
    rs.resource.attributes.extend([_kv("service.name", s="my-agent")])
    return trace_service_pb2.ExportTraceServiceRequest(
        resource_spans=[rs]).SerializeToString()


def _post(client, signal, body, content_type=PB):
    return client.post(f"/v1/{signal}", data=body, content_type=content_type)


def _cost_by_team(store, team="platform"):
    rows = {r["key"]: r for r in store.query_otlp_rollup(dimension="team")}
    return rows.get(team)


# ── AC-OBS-OIA-001.1: acknowledged only once stored ─────────────────────────

def test_logs_export_the_store_never_took_is_503_then_lands_once_on_retry(
        client, unreachable_daemon, store, monkeypatch, ls):
    """The daemon is restarting: the export must not be acknowledged. When it
    is back, the retry lands once, at the record's own time (late delivery),
    and a further retry changes nothing."""
    six_hours_ago = time.time() - 6 * 3600
    body = _logs([_api_request(six_hours_ago)])

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: unreachable_daemon)
    r = _post(client, "logs", body)
    assert r.status_code == 503, r.get_data(as_text=True)
    assert r.headers.get("Retry-After") == "5"
    assert r.get_json()["retryable"] is True
    assert store.query_otlp_records(session_id="sess-oia") == []

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
    r = _post(client, "logs", body)
    assert r.status_code == 200, r.get_data(as_text=True)
    r = _post(client, "logs", body)
    assert r.status_code == 200

    rows = store.query_otlp_records(session_id="sess-oia")
    assert len(rows) == 1
    assert abs(rows[0]["ts"] - six_hours_ago) < 1.0
    assert _cost_by_team(store)["cost_usd"] == pytest.approx(4.10)

    items = otlp_intake.snapshot()["signals"]["logs"]
    assert items["requests"]["retry_requested"] == 1
    assert items["requests"]["acknowledged"] == 2
    assert items["items"]["retry_requested"] == 1
    assert items["last_failure"] == "store_unavailable"


def test_traces_export_the_proxy_lost_is_503_then_lands_once(
        client, unreachable_daemon, store, monkeypatch, ls, tiles):
    body = _traces([_span("1111111111111111", cost=0.25)])

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: unreachable_daemon)
    r = _post(client, "traces", body)
    assert r.status_code == 503, r.get_data(as_text=True)
    assert r.headers.get("Retry-After") == "5"

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
    assert _post(client, "traces", body).status_code == 200
    assert _post(client, "traces", body).status_code == 200

    spans = store.query_spans(span_id="1111111111111111", limit=10)
    assert len(spans) == 1
    # Three deliveries, one span's cost in the live tiles.
    assert [c for c, _ in tiles].count("cost") == 1


def test_a_store_that_raises_is_503(client, monkeypatch, ls):
    class _Broken:
        def put_otlp_batch(self, **_kw):
            raise RuntimeError("disk full")

    monkeypatch.setattr(ls, "get_store", lambda read_only=False: _Broken())
    r = _post(client, "logs", _logs([_api_request(time.time())]))
    assert r.status_code == 503
    assert otlp_intake.snapshot()["signals"]["logs"]["last_failure"] == "store_write_failed"


def test_a_failed_event_flush_is_not_acknowledged(client, store, monkeypatch):
    """The record's events sit in the ring when the flush fails. A restart
    before the flusher's next tick loses them, so the receiver may not call
    them stored."""
    def _boom():
        raise RuntimeError("flush failed")

    monkeypatch.setattr(store, "_flush_now", _boom)
    r = _post(client, "logs", _logs([_api_request(time.time())]))
    assert r.status_code == 503, r.get_data(as_text=True)


def test_profile_metrics_the_store_never_took_are_503(
        client, unreachable_daemon, store, monkeypatch, ls):
    """A runtime-profile metric is a stored ledger row, so it gets the same
    rule as a log record: no confirmed write, no acknowledgement."""
    from clawmetry import otel_profiles
    prof = otel_profiles.OtelRuntimeProfile(
        runtime="acme_oia", label="Acme OIA", service_names=("acme-oia",),
        metric_prefix="acme_oia.", event_prefix="acme_oia.",
    )
    otel_profiles.register(prof)
    try:
        dp = metrics_pb2.NumberDataPoint(
            time_unix_nano=int(time.time() * 1e9), as_int=42)
        dp.attributes.extend([_kv("session.id", s="sess-oia-metric")])
        m = metrics_pb2.Metric(name="acme_oia.lines_of_code.count",
                               sum=metrics_pb2.Sum(data_points=[dp]))
        rm = metrics_pb2.ResourceMetrics(
            scope_metrics=[metrics_pb2.ScopeMetrics(metrics=[m])])
        rm.resource.attributes.extend([_kv("service.name", s="acme-oia")])
        body = metrics_service_pb2.ExportMetricsServiceRequest(
            resource_metrics=[rm]).SerializeToString()

        monkeypatch.setattr(ls, "get_store", lambda read_only=False: unreachable_daemon)
        r = _post(client, "metrics", body)
        assert r.status_code == 503, r.get_data(as_text=True)

        monkeypatch.setattr(ls, "get_store", lambda read_only=False: store)
        assert _post(client, "metrics", body).status_code == 200
        assert _post(client, "metrics", body).status_code == 200
        assert len(store.query_otlp_records(session_id="sess-oia-metric")) == 1
        assert otlp_intake.snapshot()["signals"]["metrics"]["items"]["stored"] == 2
    finally:
        otel_profiles.unregister("acme_oia")


# ── AC-OBS-OIA-001.2: partial refusal, malformed body, authentication ───────

def _json_traces(spans):
    return json.dumps({"resourceSpans": [{
        "resource": {"attributes": [
            {"key": "service.name", "value": {"stringValue": "my-agent"}}]},
        "scopeSpans": [{"spans": spans}],
    }]})


def test_one_malformed_span_is_refused_and_the_rest_are_stored(client, store):
    now = int(time.time() * 1e9)
    good = {"traceId": "cd" * 16, "spanId": "2222222222222222", "name": "openai.chat",
            "startTimeUnixNano": str(now), "endTimeUnixNano": str(now + 1000)}
    no_id = {"traceId": "cd" * 16, "spanId": "", "name": "openai.chat",
             "startTimeUnixNano": str(now), "endTimeUnixNano": str(now + 1000)}
    r = _post(client, "traces", _json_traces([good, no_id]), "application/json")
    assert r.status_code == 200, r.get_data(as_text=True)
    body = r.get_json()
    assert body["partialSuccess"]["rejectedSpans"] == "1"
    assert "Resending them will not change that" in body["partialSuccess"]["errorMessage"]
    assert len(store.query_spans(span_id="2222222222222222", limit=5)) == 1

    status = otlp_intake.snapshot()["signals"]["traces"]
    assert status["items"]["rejected"] == 1
    assert status["items"]["stored"] == 1
    assert status["requests"]["partially_acknowledged"] == 1


def test_protobuf_sender_gets_a_protobuf_partial_success(client, store):
    r = _post(client, "traces", _traces([
        _span("3333333333333333"), _span("3333333333333334", name=""),
    ]))
    assert r.status_code == 200, r.get_data(as_text=True)
    assert r.headers["Content-Type"] == PB
    resp = trace_service_pb2.ExportTraceServiceResponse.FromString(r.get_data())
    assert resp.partial_success.rejected_spans == 1
    # A clean export answers with an EMPTY message, which is valid protobuf;
    # the old "{}" text body is not.
    r = _post(client, "traces", _traces([_span("3333333333333335")]))
    assert r.status_code == 200 and r.get_data() == b""


# A value the store cannot hold. OTLP carries int64; the token columns are
# DuckDB INTEGER. Resending the item resends the value, so it is refused like
# any malformed item and must not poison the rest of its export.
_BEYOND_INTEGER = 3_000_000_000


def test_a_span_the_store_cannot_hold_is_refused_and_the_valid_span_is_stored(
        client, store):
    """Before: the one-transaction batch failed on the bad value, the export
    was answered 503, every retry failed the same way, and the valid span in
    it never landed."""
    bad = _span("4444444444444442")
    bad.attributes.extend([_kv("gen_ai.usage.input_tokens", i=_BEYOND_INTEGER)])
    body = _traces([_span("4444444444444441"), bad])
    for _ in range(3):
        r = _post(client, "traces", body)
        assert r.status_code == 200, r.get_data(as_text=True)
        resp = trace_service_pb2.ExportTraceServiceResponse.FromString(r.get_data())
        assert resp.partial_success.rejected_spans == 1
    assert len(store.query_spans(span_id="4444444444444441", limit=5)) == 1
    assert len(store.query_spans(span_id="4444444444444442", limit=5)) == 0
    status = otlp_intake.snapshot()["signals"]["traces"]
    assert status["requests"]["retry_requested"] == 0
    assert status["requests"]["partially_acknowledged"] == 3
    assert status["items"]["rejected"] == 3
    assert status["items"]["stored"] == 3


def test_a_log_record_the_store_cannot_hold_is_refused_not_retried_forever(
        client, store):
    """Before: the valid record was stored, the bad one counted as a failed
    write, and every delivery of the export was answered 503."""
    now = time.time()
    body = _logs([
        _api_request(now, session_id="sess-oia-ok"),
        _api_request(now, session_id="sess-oia-beyond", tin=_BEYOND_INTEGER),
    ])
    for _ in range(3):
        r = _post(client, "logs", body)
        assert r.status_code == 200, r.get_data(as_text=True)
        resp = logs_service_pb2.ExportLogsServiceResponse.FromString(r.get_data())
        assert resp.partial_success.rejected_log_records == 1
    assert len(store.query_otlp_records(session_id="sess-oia-ok")) == 1
    assert store.query_otlp_records(session_id="sess-oia-beyond") == []
    status = otlp_intake.snapshot()["signals"]["logs"]
    assert status["requests"]["retry_requested"] == 0
    assert status["requests"]["partially_acknowledged"] == 3


def test_a_span_write_the_store_itself_failed_is_still_503(client, store, monkeypatch):
    """Only a value the store cannot hold is refused. A store error that is
    not the data's fault still asks the sender to retry."""
    import duckdb

    def _io_error(_rows):
        raise duckdb.IOException("disk I/O error")

    monkeypatch.setattr(store, "_write_span_rows_locked", _io_error)
    r = _post(client, "traces", _traces([_span("4444444444444443")]))
    assert r.status_code == 503, r.get_data(as_text=True)
    assert otlp_intake.snapshot()["signals"]["traces"]["last_failure"] == "store_write_failed"


def test_one_unstorable_span_keeps_the_rest_of_the_batch(store, ls):
    """The store half: every caller of ingest_spans_batch (the daemon's own
    span reconstruction too) keeps the valid spans of a batch."""
    import duckdb
    ok = {"span_id": "oia-u1", "trace_id": "t", "name": "n", "start_ts": 1.0}
    beyond = dict(ok, span_id="oia-u2", tokens_input=_BEYOND_INTEGER)
    unencodable = dict(ok, span_id="oia-u3", name="n\ud800")
    infinite = dict(ok, span_id="oia-u4", tokens_input=float("inf"))
    no_name = {"span_id": "oia-u5", "trace_id": "t", "start_ts": 1.0}
    out = store.ingest_spans_batch(
        spans=[ok, beyond, unencodable, infinite, no_name], with_outcome=True)
    # An infinite count is not a number, so it is stored as unknown.
    assert out == {"written": 2, "rejected": 3}
    assert store.ingest_spans_batch(
        [dict(ok, span_id="oia-u6"), dict(beyond, span_id="oia-u7")]) == 1

    # The event ring: one event whose token count is beyond events.token_count
    # used to fail the flush for every event queued beside it, on every retry.
    base = {"node_id": "otlp", "agent_type": "my_agent", "agent_id": "main",
            "session_id": "sess-oia-ring", "runtime_kind": "my_agent",
            "event_type": "llm_call", "data": {"_otlp": True},
            "ts": "2026-09-14T00:00:00+00:00"}
    outcome = store.put_otlp_batch(records=[], events=[
        dict(base, id="otlp:oia-ring-ok", token_count=120),
        dict(base, id="otlp:oia-ring-beyond", token_count=_BEYOND_INTEGER),
    ])
    assert outcome["events"] == 2 and outcome["events_flush_failed"] is False
    stored = dict(store._fetch(
        "SELECT id, token_count FROM events WHERE session_id = ?", ["sess-oia-ring"]))
    assert stored == {"otlp:oia-ring-ok": 120, "otlp:oia-ring-beyond": None}

    assert ls._is_data_error(duckdb.ConversionException("out of range"))
    assert not ls._is_data_error(duckdb.IOException("disk I/O error"))
    assert not ls._is_data_error(duckdb.ConnectionException("Connection already closed"))
    assert not ls._is_data_error(RuntimeError("disk full"))


def test_an_undecodable_body_is_400_and_counted(client, store):
    r = _post(client, "logs", b"{not json", "application/json")
    assert r.status_code == 400
    assert otlp_intake.snapshot()["signals"]["logs"]["requests"]["malformed"] == 1


def test_a_remote_request_without_a_token_is_401_and_counted(monkeypatch):
    """Refused before the body is read, and visible in the intake status, with
    the offered token nowhere in it."""
    monkeypatch.setattr(_d, "GATEWAY_TOKEN", "secret-token", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_ALLOW_UNAUTH", raising=False)
    with _d.app.test_request_context(
        "/v1/traces", method="POST",
        headers={"Authorization": "Bearer wrong-token-value"},
        environ_base={"REMOTE_ADDR": "203.0.113.9"},
    ):
        rv = _d._check_auth()
    assert rv is not None and rv[1] == 401
    snap = otlp_intake.snapshot()
    assert snap["signals"]["traces"]["requests"]["unauthorized"] == 1
    assert snap["signals"]["traces"]["last_failure"] == "unauthorized"
    assert "wrong-token-value" not in json.dumps(snap)


# ── AC-OBS-OIA-001.3: re-delivery changes nothing ───────────────────────────

def test_redelivered_log_export_changes_no_total_and_no_tile(client, store, tiles):
    body = _logs([_api_request(time.time())])
    for _ in range(3):
        assert _post(client, "logs", body).status_code == 200
    assert _cost_by_team(store)["cost_usd"] == pytest.approx(4.10)
    assert len(store.query_otlp_records(session_id="sess-oia")) == 1
    assert [c for c, _ in tiles].count("cost") == 1
    assert otlp_intake.snapshot()["signals"]["logs"]["items"]["already_stored"] == 2


def test_two_distinct_model_calls_are_two_charges(client, store):
    """A provider retry the sender billed again is a different call: its own
    time, its own request id. It must stay a second charge."""
    t = time.time()
    body = _logs([
        _api_request(t, extra=[_kv("request_id", s="req-1")]),
        _api_request(t + 0.5, extra=[_kv("request_id", s="req-2")]),
    ])
    assert _post(client, "logs", body).status_code == 200
    assert len(store.query_otlp_records(session_id="sess-oia")) == 2
    assert _cost_by_team(store)["cost_usd"] == pytest.approx(8.20)


def test_redelivered_span_lights_the_tiles_once(client, store, tiles):
    body = _traces([_span("4444444444444444", cost=0.5)])
    for _ in range(2):
        assert _post(client, "traces", body).status_code == 200
    assert [c for c, _ in tiles].count("cost") == 1
    assert [c for c, _ in tiles].count("tokens") == 1


def _token_usage(t_ns, value):
    dp = metrics_pb2.NumberDataPoint(time_unix_nano=t_ns, as_int=value)
    dp.attributes.extend([_kv("gen_ai.token.type", s="input")])
    m = metrics_pb2.Metric(name="gen_ai.client.token.usage",
                           sum=metrics_pb2.Sum(data_points=[dp]))
    rm = metrics_pb2.ResourceMetrics(
        scope_metrics=[metrics_pb2.ScopeMetrics(metrics=[m])])
    rm.resource.attributes.extend([_kv("service.name", s="my-agent")])
    return metrics_service_pb2.ExportMetricsServiceRequest(
        resource_metrics=[rm]).SerializeToString()


def test_redelivered_metric_point_lights_the_tiles_once(client, store, tiles):
    t = int(time.time() * 1e9)
    body = _token_usage(t, 120)
    assert _post(client, "metrics", body).status_code == 200
    assert _post(client, "metrics", body).status_code == 200
    assert [c for c, _ in tiles].count("tokens") == 1
    # A new reading at a new time is not a re-delivery.
    assert _post(client, "metrics", _token_usage(t + 10**9, 120)).status_code == 200
    assert [c for c, _ in tiles].count("tokens") == 2
    status = otlp_intake.snapshot()["signals"]["metrics"]["items"]
    assert status["live_view_only"] == 3
    assert status["stored"] == 0


# ── AC-OBS-OIA-001.4: intake status ─────────────────────────────────────────

def test_intake_status_counts_and_never_repeats_content(client, store):
    secret = "sk-ant-api03-DO-NOT-ECHO-" + "x" * 20
    email = "dana@acme.example"
    body = _logs([_api_request(time.time(), extra=[
        _kv("prompt", s=f"use {secret} and mail {email}"),
    ])])
    assert _post(client, "logs", body).status_code == 200
    assert _post(client, "logs", b"garbage", "application/json").status_code == 400

    r = client.get("/api/otel-status")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    intake = r.get_json()["intake"]
    logs = intake["signals"]["logs"]
    assert logs["items"]["received"] == 1
    assert logs["items"]["stored"] == 1
    assert logs["requests"]["acknowledged"] == 1
    assert logs["requests"]["malformed"] == 1
    assert logs["last_success_at"] and logs["last_failure"] == "malformed"
    assert intake["queue"]["kept"] is False
    text = json.dumps(intake)
    assert secret not in text and email not in text and "garbage" not in text


# ── AC-OBS-OIA-001.5: a budget pause does not pause intake ──────────────────

def test_a_budget_pause_does_not_stop_intake(client, store, monkeypatch):
    monkeypatch.setattr(_d, "_budget_paused", True, raising=False)
    r = _post(client, "logs", _logs([_api_request(time.time(), cost=9.99)]))
    assert r.status_code == 200, r.get_data(as_text=True)
    assert _cost_by_team(store)["cost_usd"] == pytest.approx(9.99)
    reqs = otlp_intake.snapshot()["signals"]["logs"]["requests"]
    assert reqs["during_budget_pause"] == 1


# ── AC-OBS-OIA-001.6: unknown usage is not zero ─────────────────────────────

def test_unreported_usage_is_unknown_not_zero(client, store):
    t = time.time()
    _post(client, "logs", _logs([
        _api_request(t, session_id="s-input-only", cost=None, tout=None),
    ], team="no-cost"))
    _post(client, "logs", _logs([
        _api_request(t, session_id="s-priced", cost=1.25),
        _api_request(t + 1, session_id="s-unpriced", cost=None),
    ], team="mixed"))

    row = store.query_otlp_records(session_id="s-input-only")[0]
    assert row["tokens_input"] == 1500
    assert row["tokens_output"] is None, "an unreported side is unknown, not 0"
    assert row["cost_usd"] is None

    groups = {r["key"]: r for r in store.query_otlp_rollup(dimension="team")}
    assert groups["no-cost"]["cost_usd"] is None
    assert groups["no-cost"]["records_with_cost"] == 0
    assert groups["mixed"]["cost_usd"] == pytest.approx(1.25)
    assert groups["mixed"]["records_with_cost"] == 1
    assert groups["mixed"]["records"] == 2


# ── AC-OBS-OIA-001.7: trace sampling does not reduce spend ──────────────────

def test_sampled_spans_do_not_change_spend_from_unsampled_log_records(client, store):
    """Three model calls are logged (logs are not sampled). The sender's trace
    sampler kept one of the three spans, which carries its own cost. The
    spend answer is the three log records, not the one surviving span, and
    the span's cost is not added on top."""
    t = time.time()
    _post(client, "logs", _logs([
        _api_request(t + i, session_id="sess-sampled", cost=1.0) for i in range(3)
    ]))
    _post(client, "traces", _traces([
        _span("5555555555555555", cost=1.0, session_id="sess-sampled"),
    ]))
    by_session = {r["key"]: r for r in store.query_otlp_rollup(dimension="session_id")}
    assert by_session["sess-sampled"]["cost_usd"] == pytest.approx(3.0)
    assert by_session["sess-sampled"]["records"] == 3


# ── AC-OBS-OIA-001.8: the generated reference ───────────────────────────────

def test_generated_reference_states_ack_retry_identity_and_session_rules():
    doc = (ROOT / "docs" / "INGEST.md").read_text()
    for phrase in (
        "| `503` |", "Retry-After", "partialSuccess", "| `401` |",
        "### Acknowledgement and retry", "### Recognising a re-delivery",
        "### Session identity when the sender names none",
        "### Held only in the live view", "### Intake status",
        "does not pause intake",
    ):
        assert phrase in doc, f"docs/INGEST.md does not state: {phrase}"
    # Only the OTLP receiver's table: the run/event API below it keeps its own
    # 429 row, which is a different surface.
    otlp_section = doc.split("## OTLP receiver", 1)[1].split("## Run / event ingest API", 1)[0]
    assert "| `429` |" not in otlp_section, "OTLP intake no longer pauses on a budget limit"
    from clawmetry.ingest_contract import OTLP_RETRY_AFTER_SECONDS
    assert otlp_intake.snapshot()["retry_after_seconds"] == OTLP_RETRY_AFTER_SECONDS


# ── every real mapper reports an outcome ────────────────────────────────────

@pytest.mark.parametrize("name", ["_process_otlp_logs", "_process_otlp_traces",
                                  "_process_otlp_metrics"])
def test_every_mapper_reports_an_outcome(name, store):
    empty = {
        "_process_otlp_logs": logs_service_pb2.ExportLogsServiceRequest(),
        "_process_otlp_traces": trace_service_pb2.ExportTraceServiceRequest(),
        "_process_otlp_metrics": metrics_service_pb2.ExportMetricsServiceRequest(),
    }[name].SerializeToString()
    out = getattr(_d, name)(empty)
    assert isinstance(out, dict) and out["durable"] is True and out["received"] == 0
