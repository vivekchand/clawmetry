"""obs-gap #2591: /v1/traces must map cost/token SPAN ATTRIBUTES into the tiles.

Codex emits cost/token telemetry on spans (e.g. ``codex.api_request``), not as
metrics. The /v1/traces handler previously mapped only span *names*
(run/message) into the metrics cache, so a Codex cost/token span persisted to
the spans table but never lit the cost/usage tiles. ``_process_otlp_traces`` now
also maps any span carrying cost/token attributes.
"""
import time

import pytest

pytest.importorskip("opentelemetry.proto.collector.trace.v1.trace_service_pb2",
                    reason="opentelemetry-proto not installed (pip install clawmetry[otel])")

from opentelemetry.proto.collector.trace.v1 import trace_service_pb2  # noqa: E402
from opentelemetry.proto.trace.v1 import trace_pb2  # noqa: E402
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


def test_codex_cost_token_span_lands_in_tiles(monkeypatch):
    captured = []
    monkeypatch.setattr(_d, "_add_metric", lambda cat, e: captured.append((cat, e)))

    now = int(time.time() * 1e9)
    span = trace_pb2.Span(name="codex.api_request",
                          start_time_unix_nano=now, end_time_unix_nano=now + 500_000_000)
    span.attributes.extend([
        _kv("model", s="gpt-5.4"),
        _kv("cost_usd", d=0.0312),
        _kv("input_tokens", i=1200),
        _kv("output_tokens", i=300),
    ])
    req = trace_service_pb2.ExportTraceServiceRequest(resource_spans=[
        trace_pb2.ResourceSpans(scope_spans=[trace_pb2.ScopeSpans(spans=[span])])])

    # store may be unavailable in this env; the metrics path must still run
    _d._process_otlp_traces(req.SerializeToString())

    cats = {c for c, _ in captured}
    assert "cost" in cats and "tokens" in cats, f"got {cats}"
    cost = next(e for c, e in captured if c == "cost")
    assert abs(cost["usd"] - 0.0312) < 1e-9 and cost["model"] == "gpt-5.4"
    toks = next(e for c, e in captured if c == "tokens")
    assert toks["input"] == 1200 and toks["output"] == 300 and toks["total"] == 1500
