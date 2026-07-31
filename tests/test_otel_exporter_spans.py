"""OTLP exporter emits well-formed GenAI spans (clawmetry/otel_exporter.py).

Uses an in-memory OTLP collector (stdlib HTTP server capturing request
bodies) plus a fake store — no DuckDB, no network beyond localhost.
"""
import http.server
import json
import threading

import pytest

from clawmetry import otel_exporter as oe


class _Collector:
    """Minimal in-memory OTLP/HTTP collector."""

    def __init__(self):
        self.payloads = []
        collector = self

        class _Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length", 0))
                collector.payloads.append(json.loads(self.rfile.read(length)))
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b"{}")

            def log_message(self, *a):
                pass

        self.server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    @property
    def endpoint(self):
        return f"http://127.0.0.1:{self.server.server_port}/v1/traces"

    def close(self):
        self.server.shutdown()
        self.server.server_close()


class _FakeStore:
    def __init__(self, sessions, events):
        self._sessions = sessions
        self._events = events

    def query_sessions(self, **kwargs):
        return self._sessions

    def query_events(self, **kwargs):
        return self._events


SESSION = {
    "session_id": "sess-1",
    "agent_type": "claude_code",
    "agent_id": "main",
    "model": "claude-sonnet-5",
    "token_count": 1234,
    "cost_usd": 0.42,
    "event_count": 7,
    "started_at": "2026-07-30T10:00:00+00:00",
    "updated_at": "2026-07-30T10:05:00+00:00",
}

TOOL_EVENT = {
    "id": "ev-1",
    "session_id": "sess-1",
    "agent_type": "claude_code",
    "event_type": "tool_call",
    "ts": "2026-07-30T10:01:00+00:00",
    "data": {"tool_calls": [{"name": "Bash", "args": {"command": "ls"}}]},
}


@pytest.fixture
def collector():
    c = _Collector()
    yield c
    c.close()


@pytest.fixture
def wired(monkeypatch, collector):
    import clawmetry.local_store as ls

    store = _FakeStore([SESSION], [TOOL_EVENT])
    monkeypatch.setattr(ls, "get_store", lambda **kw: store)
    monkeypatch.setattr(oe, "_last_watermark", None)
    return collector


def _attrs(span):
    return {a["key"]: a["value"] for a in span["attributes"]}


def test_flush_emits_wellformed_spans(wired):
    sent = oe._flush_once(wired.endpoint, {"X-Test": "1"})
    assert sent == 2  # 1 session span + 1 tool span

    assert len(wired.payloads) == 1
    payload = wired.payloads[0]
    resource_spans = payload["resourceSpans"]
    resource_attrs = {
        a["key"]: a["value"] for a in resource_spans[0]["resource"]["attributes"]
    }
    assert resource_attrs["service.name"] == {"stringValue": "clawmetry"}

    spans = resource_spans[0]["scopeSpans"][0]["spans"]
    assert len(spans) == 2
    session_span = next(s for s in spans if s["name"] == "claude_code.session")
    tool_span = next(s for s in spans if s["name"] == "execute_tool Bash")

    # Well-formed ids (hex, OTLP sizes) and a real time range.
    assert len(session_span["traceId"]) == 32
    assert len(session_span["spanId"]) == 16
    int(session_span["traceId"], 16)
    assert int(session_span["endTimeUnixNano"]) > int(
        session_span["startTimeUnixNano"]
    )

    attrs = _attrs(session_span)
    assert attrs["gen_ai.system"] == {"stringValue": "claude_code"}
    assert attrs["gen_ai.operation.name"] == {"stringValue": "invoke_agent"}
    assert attrs["gen_ai.agent.name"] == {"stringValue": "main"}
    assert attrs["gen_ai.request.model"] == {"stringValue": "claude-sonnet-5"}
    assert attrs["gen_ai.usage.input_tokens"] == {"intValue": "1234"}
    assert attrs["clawmetry.cost_usd"] == {"doubleValue": 0.42}

    # Tool span is a child of the session span, in the same trace.
    assert tool_span["traceId"] == session_span["traceId"]
    assert tool_span["parentSpanId"] == session_span["spanId"]
    tool_attrs = _attrs(tool_span)
    assert tool_attrs["gen_ai.operation.name"] == {"stringValue": "execute_tool"}
    assert tool_attrs["gen_ai.tool.name"] == {"stringValue": "Bash"}


def test_trace_ids_are_deterministic_across_flushes(wired):
    oe._flush_once(wired.endpoint, {})
    oe._last_watermark = None  # simulate a restart re-exporting the window
    oe._flush_once(wired.endpoint, {})
    first, second = wired.payloads
    span_a = first["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    span_b = second["resourceSpans"][0]["scopeSpans"][0]["spans"][0]
    assert span_a["traceId"] == span_b["traceId"]
    assert span_a["spanId"] == span_b["spanId"]


def test_watermark_advances_past_exported_rows(wired):
    oe._flush_once(wired.endpoint, {})
    assert oe._last_watermark == "2026-07-30T10:05:00+00:00"


def test_start_exporter_scopes(monkeypatch, tmp_path):
    # Don't run real export loops from this test — resolution logic only.
    monkeypatch.setattr(oe, "_export_loop", lambda *a, **k: None)
    # Nothing configured -> neither scope starts.
    monkeypatch.delenv("CLAWMETRY_OTEL_EXPORT_ENDPOINT", raising=False)
    monkeypatch.setattr(oe, "_CONFIG_PATH", str(tmp_path / "config.json"))
    assert oe.start_exporter() is False
    assert oe.start_exporter(scope="config") is False

    # Config key activates ONLY the config scope (daemon path)...
    (tmp_path / "config.json").write_text(
        json.dumps({"otlp_endpoint": "http://127.0.0.1:9/v1/traces",
                    "otlp_headers": {"X-K": "v"},
                    "otlp_export_interval": 3600})
    )
    assert oe.start_exporter() is False  # env scope still off
    assert oe.start_exporter(scope="config") is True

    # ...and the env var activates only the env scope (dashboard path).
    monkeypatch.setenv("CLAWMETRY_OTEL_EXPORT_ENDPOINT", "http://127.0.0.1:9/v1/traces")
    monkeypatch.setenv("CLAWMETRY_OTEL_EXPORT_INTERVAL", "3600")
    assert oe.start_exporter() is True
