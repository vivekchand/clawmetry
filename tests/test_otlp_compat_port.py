"""OTLP compatibility listener on the conventional port — issue #4780.

Every OpenTelemetry SDK and collector defaults to ``http://localhost:4318``.
ClawMetry served ``/v1/*`` only on the dashboard port, so an already-instrumented
app could not be observed until someone found ``OTEL_EXPORTER_OTLP_ENDPOINT``.

These tests pin the listener's contract:
  * a span POSTed to the compat port takes the same path as one POSTed to the
    dashboard port (same handler, same decoder, same store)
  * the compat surface serves the receiver and NOTHING else (no UI, no /api/*)
  * a port already held by a real collector is a log line, not a crash
  * the disable switch and the port override work

The socket-level test binds port 0 (ephemeral) so it never collides with a real
collector on the developer's machine or with a parallel CI job.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request

import pytest

import dashboard as _d


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_OTLP_PORT_DISABLE", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_PORT", raising=False)
    monkeypatch.delenv("CLAWMETRY_OTLP_HOST", raising=False)


def _trace_json(span_id="00000000000000f1"):
    now_ns = str(int(time.time() * 1e9))
    return json.dumps({"resourceSpans": [{
        "resource": {"attributes": [
            {"key": "service.name", "value": {"stringValue": "compat-port-app"}}]},
        "scopeSpans": [{"spans": [{
            "traceId": "0123456789abcdef0123456789abcdef",
            "spanId": span_id,
            "name": "openai.chat",
            "kind": "SPAN_KIND_CLIENT",
            "startTimeUnixNano": now_ns,
            "endTimeUnixNano": now_ns,
            "attributes": [],
        }]}],
    }]}).encode("utf-8")


# ── the compat app's surface ────────────────────────────────────────────────


def test_compat_app_serves_the_receiver():
    c = _d._build_otlp_compat_app().test_client()
    r = c.post("/v1/traces", data=_trace_json(), content_type="application/json")
    assert r.status_code == 200, r.get_data(as_text=True)[:300]


def test_compat_app_serves_nothing_else():
    """A second port must not widen what is reachable. UI and /api/* stay off."""
    c = _d._build_otlp_compat_app().test_client()
    for path in ("/", "/api/overview", "/api/sessions", "/static/js/app.js"):
        assert c.get(path).status_code == 404, f"{path} should not be served here"


def test_compat_app_carries_the_auth_guard():
    """The loopback-trusted / token-required rule must be one rule, not two:
    a non-loopback caller has to be gated here exactly as on the main app."""
    app = _d._build_otlp_compat_app()
    funcs = app.before_request_funcs.get(None, [])
    assert _d._check_auth in funcs


# ── lifecycle ───────────────────────────────────────────────────────────────


def test_disable_switch_returns_none(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OTLP_PORT_DISABLE", "1")
    assert _d._start_otlp_compat_listener() is None


def test_port_in_use_is_survivable(monkeypatch):
    """A machine already running an OTel Collector keeps its collector. The
    listener logs and steps aside; startup must not fail."""
    def _boom(*a, **kw):
        raise OSError(98, "Address already in use")

    import waitress
    monkeypatch.setattr(waitress, "create_server", _boom)
    assert _d._start_otlp_compat_listener(port=4318) is None


def test_bad_port_env_falls_back_to_default(monkeypatch):
    """A typo in CLAWMETRY_OTLP_PORT must not crash the dashboard."""
    monkeypatch.setenv("CLAWMETRY_OTLP_PORT", "not-a-port")
    captured = {}

    def _fake_create_server(app, host=None, port=None, **kw):
        captured["port"] = port
        raise OSError("stop here")

    import waitress
    monkeypatch.setattr(waitress, "create_server", _fake_create_server)
    assert _d._start_otlp_compat_listener() is None
    assert captured["port"] == _d._OTLP_COMPAT_DEFAULT_PORT


def test_debug_reloader_supervisor_does_not_grab_the_port(monkeypatch):
    """Flask's reloader runs main() twice. Only the child serves requests, so
    the supervisor must leave 4318 alone or the child logs 'already in use' on
    every reload."""
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)
    assert _d._start_otlp_compat_listener(debug=True) is None
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")
    monkeypatch.setenv("CLAWMETRY_OTLP_PORT", "0")
    server = _d._start_otlp_compat_listener(debug=True)
    assert server is not None
    server.close()


def test_binds_loopback_even_when_dashboard_is_wide_open(monkeypatch):
    """The dashboard's --host must not silently widen the ingest surface."""
    captured = {}

    def _fake_create_server(app, host=None, port=None, **kw):
        captured["host"] = host
        raise OSError("stop here")

    import waitress
    monkeypatch.setattr(waitress, "create_server", _fake_create_server)
    _d._start_otlp_compat_listener()
    assert captured["host"] == "127.0.0.1"


# ── real socket ─────────────────────────────────────────────────────────────


def test_real_post_over_the_socket(monkeypatch):
    """End to end over TCP: bind an ephemeral port, POST OTLP/JSON, get 200.

    Port 0 keeps this hermetic -- no clash with a real collector on 4318.
    """
    monkeypatch.setenv("CLAWMETRY_OTLP_PORT", "0")
    server = _d._start_otlp_compat_listener()
    assert server is not None, "listener failed to bind an ephemeral port"
    try:
        url = f"http://127.0.0.1:{server.effective_port}/v1/traces"
        req = urllib.request.Request(
            url, data=_trace_json("00000000000000f2"),
            headers={"Content-Type": "application/json"}, method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            assert resp.status == 200
    finally:
        try:
            server.close()
        except Exception:
            pass


def test_real_socket_404s_the_dashboard(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_OTLP_PORT", "0")
    server = _d._start_otlp_compat_listener()
    assert server is not None
    try:
        url = f"http://127.0.0.1:{server.effective_port}/api/overview"
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(url, timeout=10)
        assert exc.value.code == 404
    finally:
        try:
            server.close()
        except Exception:
            pass
