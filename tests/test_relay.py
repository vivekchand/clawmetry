"""Tests for clawmetry/relay.py — node-side WebSocket relay client.

The relay's networking is mocked end-to-end. We're testing the dispatch +
chunking logic, not the actual websocket-client library.
"""

from __future__ import annotations

import importlib
import json
import sys
import types
from unittest.mock import MagicMock

import pytest


def _install_fake_websocket():
    """Install a minimal stub of `websocket-client` so tests don't depend
    on the optional dep being installed in CI."""
    if "websocket" in sys.modules:
        return sys.modules["websocket"]
    fake = types.ModuleType("websocket")
    class WebSocketTimeoutException(Exception):
        pass
    fake.WebSocketTimeoutException = WebSocketTimeoutException
    fake.create_connection = MagicMock()
    sys.modules["websocket"] = fake
    return fake


@pytest.fixture
def fake_ws(monkeypatch):
    """Return a MagicMock standing in for a connected WebSocket."""
    _install_fake_websocket()
    ws = MagicMock(name="WebSocket")
    return ws


def _send_payloads(ws):
    """Return list of dicts the relay sent on `ws.send()` calls."""
    return [json.loads(c.args[0]) for c in ws.send.call_args_list]


def test_start_relay_thread_skips_when_no_cloud_account():
    from clawmetry import relay
    importlib.reload(relay)
    assert relay.start_relay_thread({}) is None
    assert relay.start_relay_thread({"node_id": "x"}) is None
    assert relay.start_relay_thread({"api_key": "y"}) is None


def test_start_relay_thread_skips_when_websocket_missing(monkeypatch):
    from clawmetry import relay
    importlib.reload(relay)
    # Force the import inside start_relay_thread() to fail.
    sys.modules.pop("websocket", None)
    real_import = __builtins__["__import__"] if isinstance(__builtins__, dict) else __builtins__.__import__
    def fake_import(name, *a, **k):
        if name == "websocket":
            raise ImportError("forced")
        return real_import(name, *a, **k)
    monkeypatch.setitem(__builtins__ if isinstance(__builtins__, dict) else __builtins__.__dict__, "__import__", fake_import) if isinstance(__builtins__, dict) else monkeypatch.setattr("builtins.__import__", fake_import)
    assert relay.start_relay_thread({"api_key": "k", "node_id": "n"}) is None


def test_handle_query_dispatches_via_local_query(fake_ws, tmp_path, monkeypatch):
    """End-to-end of the dispatch path: relay calls relay_dispatch(),
    chunks the response, sends it back over the (fake) WS."""
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    from clawmetry import relay
    importlib.reload(relay)

    # Seed one event so the events shape returns something.
    store = ls.get_store()
    store.ingest({
        "id": "ev-relay-1",
        "node_id": "agent+test",
        "agent_id": "main",
        "session_id": "sess-relay",
        "event_type": "tool_call",
        "ts": "2026-05-11T12:00:00Z",
        "data": {"tool": "Bash"},
        "cost_usd": 0.001,
        "token_count": 5,
        "model": "claude-opus-4-7",
    })
    # Wait for flush.
    import time
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline and store.health()["ring_depth"] > 0:
        time.sleep(0.02)

    relay._handle_query(fake_ws, {
        "type": "query",
        "id": "q-1",
        "shape": "events",
        "args": {"session_id": "sess-relay"},
    })

    payloads = _send_payloads(fake_ws)
    assert len(payloads) == 1
    response = payloads[0]
    assert response["type"] == "response"
    assert response["id"] == "q-1"
    assert response["final"] is True
    assert response["count"] == 1
    assert response["rows"][0]["id"] == "ev-relay-1"


def test_handle_query_chunks_large_results(fake_ws, monkeypatch):
    """Force >100 rows and confirm we send N chunks with final=True only on the last."""
    from clawmetry import relay
    importlib.reload(relay)

    # Stub relay_dispatch to return 250 rows.
    fake_rows = [{"id": f"ev-{i}"} for i in range(250)]
    def fake_dispatch(shape, args):
        return {"_shape": shape, "_elapsed_ms": 1, "rows": fake_rows, "count": 250}
    monkeypatch.setattr("routes.local_query.relay_dispatch", fake_dispatch)

    relay._handle_query(fake_ws, {"id": "q-2", "shape": "events", "args": {}})

    payloads = _send_payloads(fake_ws)
    assert len(payloads) == 3   # 100 + 100 + 50
    assert payloads[0]["chunk"] == 1 and payloads[0]["final"] is False
    assert payloads[1]["chunk"] == 2 and payloads[1]["final"] is False
    assert payloads[2]["chunk"] == 3 and payloads[2]["final"] is True
    assert payloads[2]["count"] == 250
    assert len(payloads[0]["rows"]) == 100
    assert len(payloads[2]["rows"]) == 50


def test_handle_query_unknown_shape_returns_error(fake_ws):
    from clawmetry import relay
    importlib.reload(relay)
    relay._handle_query(fake_ws, {"id": "q-3", "shape": "drop_table_users", "args": {}})
    p = _send_payloads(fake_ws)
    assert len(p) == 1
    assert p[0]["type"] == "error"
    assert p[0]["id"] == "q-3"
    assert "code" in p[0]


def test_handle_frame_responds_to_ping(fake_ws):
    from clawmetry import relay
    importlib.reload(relay)
    relay._handle_frame(fake_ws, {"type": "ping"})
    p = _send_payloads(fake_ws)
    assert p == [{"type": "pong"}]


def test_handle_frame_ignores_unknown_types(fake_ws):
    from clawmetry import relay
    importlib.reload(relay)
    relay._handle_frame(fake_ws, {"type": "weather_report"})
    assert fake_ws.send.call_count == 0


def test_capabilities_match_local_query_shapes():
    """If a new shape is added to routes/local_query._SHAPES, the relay
    must advertise it too — otherwise the cloud thinks the node can't
    serve it."""
    from clawmetry import relay
    import routes.local_query as lq
    importlib.reload(relay)
    importlib.reload(lq)
    advertised = {c.split(".", 1)[1] for c in relay._CAPABILITIES}
    actual = set(lq._SHAPES.keys())
    assert advertised == actual, (
        f"relay capabilities drift from _SHAPES — "
        f"missing in relay: {actual - advertised}; "
        f"missing in _SHAPES: {advertised - actual}"
    )
