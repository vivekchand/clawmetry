"""Deep edge-case coverage for the OTLP metrics → cost/token feature.

The OTLP metrics receiver (``POST /v1/metrics`` → ``_process_otlp_metrics``)
feeds the in-memory ``metrics_store`` that powers the dashboard's cost/token
history + the ``/api/otel-status`` panel. This pins the edge cases that path
must survive, driven through the REAL receiver and read back via the real
``/api/otel-status`` endpoint:

  * ``openclaw.tokens`` data point → recorded with input/output/total;
  * ``openclaw.cost.usd`` data point → recorded with the usd value;
  * empty metrics request → accepted, nothing recorded, hasData False;
  * unknown metric name → ignored (not stored), never errors;
  * multiple data points in one metric → all recorded;
  * gauge AND sum data-point types both extract;
  * malformed protobuf → 4xx, never a 500 / stacktrace leak.

Deterministic + real. Gated on ``opentelemetry-proto`` (the receiver 501s
without it). The in-memory ``metrics_store`` is reset per test for isolation.
"""

from __future__ import annotations

import importlib

import pytest
from flask import Flask

try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2 as _ms_pb2
    from opentelemetry.proto.metrics.v1 import metrics_pb2 as _m_pb2  # noqa: F401
    _HAS_OTEL_PROTO = True
except Exception:  # pragma: no cover
    _HAS_OTEL_PROTO = False

pytestmark = pytest.mark.skipif(
    not _HAS_OTEL_PROTO,
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)

_STORE_KEYS = ("tokens", "cost", "runs", "messages", "webhooks", "queues")


@pytest.fixture
def app(monkeypatch):
    import dashboard as _d
    import routes.meta as meta
    importlib.reload(meta)
    # Isolate the in-memory metrics store (module global) per test.
    monkeypatch.setattr(_d, "metrics_store", {k: [] for k in _STORE_KEYS})
    monkeypatch.setattr(_d, "_otel_last_received", 0, raising=False)

    a = Flask(__name__)
    a.register_blueprint(meta.bp_otel)
    return a, _d


def _metric(name, *, as_int=None, as_double=None, kind="sum", attrs=None,
            extra_points=None):
    """Build one OTLP Metric proto with a single (or multiple) data point(s)."""
    met = _m_pb2.Metric()
    met.name = name
    container = met.sum if kind == "sum" else met.gauge
    points = [(as_int, as_double, attrs or {})]
    points.extend(extra_points or [])
    for pi, pd, pa in points:
        dp = container.data_points.add()
        if pd is not None:
            dp.as_double = pd
        elif pi is not None:
            dp.as_int = pi
        for k, v in pa.items():
            a = dp.attributes.add()
            a.key = k
            if isinstance(v, bool):
                a.value.bool_value = v
            elif isinstance(v, int):
                a.value.int_value = v
            elif isinstance(v, float):
                a.value.double_value = v
            else:
                a.value.string_value = str(v)
    return met


def _build_pb(metrics):
    req = _ms_pb2.ExportMetricsServiceRequest()
    rm = req.resource_metrics.add()
    ra = rm.resource.attributes.add()
    ra.key = "service.name"
    ra.value.string_value = "openclaw"
    sm = rm.scope_metrics.add()
    for met in metrics:
        sm.metrics.add().CopyFrom(met)
    return req.SerializeToString()


def _post(client, pb_bytes):
    return client.post("/v1/metrics", data=pb_bytes,
                       content_type="application/x-protobuf")


def _status(client):
    r = client.get("/api/otel-status")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]
    return r.get_json()


# ── happy path: tokens + cost recorded ──────────────────────────────────────


def test_tokens_metric_recorded(app):
    a, _d = app
    c = a.test_client()
    r = _post(c, _build_pb([_metric(
        "openclaw.tokens", as_int=1500, kind="sum",
        attrs={"input_tokens": 1000, "output_tokens": 500,
               "model": "claude-3-5-haiku-20241022", "provider": "anthropic"},
    )]))
    assert r.status_code == 200
    entries = _d.metrics_store["tokens"]
    assert len(entries) == 1
    e = entries[0]
    assert e["input"] == 1000 and e["output"] == 500 and e["total"] == 1500
    assert e["model"] == "claude-3-5-haiku-20241022"
    status = _status(c)
    assert status["hasData"] is True
    assert status["counts"]["tokens"] == 1


def test_cost_metric_recorded_as_double(app):
    a, _d = app
    c = a.test_client()
    _post(c, _build_pb([_metric(
        "openclaw.cost.usd", as_double=0.0123, kind="gauge",
        attrs={"model": "claude-3-5-haiku-20241022", "provider": "anthropic"},
    )]))
    entries = _d.metrics_store["cost"]
    assert len(entries) == 1
    assert entries[0]["usd"] == pytest.approx(0.0123)
    assert _status(c)["counts"]["cost"] == 1


# ── empty / unknown ─────────────────────────────────────────────────────────


def test_empty_metrics_request_no_data(app):
    a, _d = app
    c = a.test_client()
    r = _post(c, _ms_pb2.ExportMetricsServiceRequest().SerializeToString())
    assert r.status_code == 200, "empty metrics request must be accepted"
    assert _status(c)["hasData"] is False
    assert all(len(v) == 0 for v in _d.metrics_store.values())


def test_unknown_metric_name_ignored(app):
    a, _d = app
    c = a.test_client()
    r = _post(c, _build_pb([_metric("some.unrelated.metric", as_int=42)]))
    assert r.status_code == 200
    # No known category should have captured it; store stays empty.
    assert all(len(v) == 0 for v in _d.metrics_store.values()), (
        "an unrecognised metric name must be ignored, not mis-filed"
    )
    assert _status(c)["hasData"] is False


# ── multiple data points ────────────────────────────────────────────────────


def test_multiple_data_points_all_recorded(app):
    a, _d = app
    c = a.test_client()
    _post(c, _build_pb([_metric(
        "openclaw.tokens", as_int=100, kind="sum",
        attrs={"input_tokens": 60, "output_tokens": 40, "model": "m1"},
        extra_points=[
            (200, None, {"input_tokens": 120, "output_tokens": 80, "model": "m2"}),
            (300, None, {"input_tokens": 180, "output_tokens": 120, "model": "m3"}),
        ],
    )]))
    entries = _d.metrics_store["tokens"]
    assert len(entries) == 3, f"expected 3 data points recorded, got {len(entries)}"
    assert {e["total"] for e in entries} == {100, 200, 300}


# ── malformed input ─────────────────────────────────────────────────────────


def test_malformed_protobuf_is_4xx_not_500(app):
    a, _d = app
    c = a.test_client()
    r = c.post("/v1/metrics", data=b"\x00\x01not-valid\xff",
               content_type="application/x-protobuf")
    assert r.status_code in (400, 422), (
        f"malformed OTLP metrics must be a 4xx, got {r.status_code}"
    )
    assert r.status_code != 500
    # And nothing should have been recorded from garbage.
    assert all(len(v) == 0 for v in _d.metrics_store.values())
