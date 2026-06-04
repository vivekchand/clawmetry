"""obs-gap #2596: the /v1/logs OTLP receiver must ingest agent event records.

Claude Code / Codex export their per-turn EVENT stream as OTel *logs* (event_name
like ``claude_code.api_request`` with cost/token/model attributes). We had
/v1/metrics + /v1/traces but no /v1/logs, so those events were dropped.
``_process_otlp_logs`` maps any log record carrying cost/token attributes into
the cost + tokens metric tiles. Skips cleanly when opentelemetry-proto is absent
(same as the other OTLP tests).
"""
import time

import pytest

pytest.importorskip("opentelemetry.proto.collector.logs.v1.logs_service_pb2",
                    reason="opentelemetry-proto not installed (pip install clawmetry[otel])")

from opentelemetry.proto.collector.logs.v1 import logs_service_pb2  # noqa: E402
from opentelemetry.proto.logs.v1 import logs_pb2  # noqa: E402
from opentelemetry.proto.common.v1 import common_pb2  # noqa: E402

import dashboard as _d  # noqa: E402


def _kv(key, s=None, i=None, d=None):
    v = common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    elif d is not None:
        v.double_value = d
    return common_pb2.KeyValue(key=key, value=v)


def _request_with_api_event():
    rec = logs_pb2.LogRecord(time_unix_nano=int(time.time() * 1e9))
    rec.event_name = "claude_code.api_request"
    rec.attributes.extend([
        _kv("model", s="claude-opus-4-8"),
        _kv("cost_usd", d=0.1234),
        _kv("input_tokens", i=1500),
        _kv("output_tokens", i=300),
        _kv("duration_ms", d=820.0),
    ])
    scope = logs_pb2.ScopeLogs(log_records=[rec])
    res = logs_pb2.ResourceLogs(scope_logs=[scope])
    return logs_service_pb2.ExportLogsServiceRequest(resource_logs=[res])


def test_otlp_log_event_lands_in_cost_and_tokens(monkeypatch):
    captured = []
    monkeypatch.setattr(_d, "_add_metric", lambda cat, e: captured.append((cat, e)))

    _d._process_otlp_logs(_request_with_api_event().SerializeToString())

    cats = {c for c, _ in captured}
    assert "cost" in cats and "tokens" in cats and "runs" in cats, f"got {cats}"
    cost = next(e for c, e in captured if c == "cost")
    assert abs(cost["usd"] - 0.1234) < 1e-9
    assert cost["model"] == "claude-opus-4-8"
    toks = next(e for c, e in captured if c == "tokens")
    assert toks["input"] == 1500 and toks["output"] == 300 and toks["total"] == 1800
    runs = next(e for c, e in captured if c == "runs")
    assert abs(runs["duration_ms"] - 820.0) < 1e-6


def test_record_without_cost_or_tokens_is_ignored(monkeypatch):
    captured = []
    monkeypatch.setattr(_d, "_add_metric", lambda cat, e: captured.append((cat, e)))
    rec = logs_pb2.LogRecord(time_unix_nano=int(time.time() * 1e9))
    rec.event_name = "claude_code.tool_decision"
    rec.attributes.extend([_kv("tool_name", s="Bash"), _kv("decision", s="allow")])
    req = logs_service_pb2.ExportLogsServiceRequest(
        resource_logs=[logs_pb2.ResourceLogs(scope_logs=[logs_pb2.ScopeLogs(log_records=[rec])])])
    _d._process_otlp_logs(req.SerializeToString())
    assert captured == [], "a non-cost/token event must not add metrics"
