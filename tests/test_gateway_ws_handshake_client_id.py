"""Issue #1720: gateway WS handshake must identify as the bundled control UI.

The OpenClaw gateway only honours requested scopes (``operator.read`` /
``operator.admin``) when the WS connect handshake sets
``client.id == "openclaw-control-ui"``. Any other identifier (we previously
sent ``"cli"``) silently receives an OK connect response with an empty
``auth.scopes`` array, and every subsequent ``cron.list`` / ``sessions.list``
RPC fails with ``INVALID_REQUEST: missing scope: operator.read``. That made
the Crons tab (and Sessions tab) render empty regardless of whether the
gateway actually had data.

This test pins the identity so the regression — which presented as an empty
Crons tab on both OSS and Cloud — can't return.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import helpers.gateway as gw  # noqa: E402


def _capture_handshake(monkeypatch):
    """Stub websocket.create_connection so we can inspect the connect payload
    the dashboard sends to the gateway. Returns ``(captured_msgs, fake_ws)``.
    """
    captured: list[str] = []
    fake_ws = MagicMock()
    # First recv() returns a challenge event; second returns a successful
    # connect response so _gw_ws_connect's loop terminates cleanly.
    fake_ws.recv.side_effect = [
        json.dumps({"type": "event", "event": "connect.challenge",
                    "payload": {"nonce": "n", "ts": 0}}),
        json.dumps({"type": "res", "id": "clawmetry-connect", "ok": True,
                    "payload": {"auth": {"role": "operator",
                                          "scopes": ["operator.admin",
                                                     "operator.read"]}}}),
    ]
    fake_ws.send.side_effect = lambda payload: captured.append(payload)

    fake_websocket = MagicMock()
    fake_websocket.create_connection.return_value = fake_ws
    monkeypatch.setitem(sys.modules, "websocket", fake_websocket)
    return captured, fake_ws


@pytest.fixture(autouse=True)
def _reset_gateway_state():
    """Reset the module-level WS singleton between tests."""
    gw._ws_client = None
    gw._ws_connected = False
    yield
    gw._ws_client = None
    gw._ws_connected = False


def test_handshake_identifies_as_openclaw_control_ui(monkeypatch):
    """Regression #1720: client.id must be ``openclaw-control-ui`` so the
    gateway grants the requested scopes. Any other id results in
    ``auth.scopes == []`` server-side and downstream RPCs fail."""
    captured, _ = _capture_handshake(monkeypatch)

    fake_dashboard = MagicMock()
    fake_dashboard._load_gw_config.return_value = {
        "url": "http://127.0.0.1:18789", "token": "test-token"
    }
    fake_dashboard.__version__ = "0.0.0-test"
    fake_dashboard._CURRENT_PLATFORM = "test"
    fake_dashboard._uuid = __import__("uuid")
    monkeypatch.setitem(sys.modules, "dashboard", fake_dashboard)

    assert gw._gw_ws_connect() is True
    assert len(captured) == 1
    msg = json.loads(captured[0])
    client = msg["params"]["client"]
    assert client["id"] == "openclaw-control-ui", (
        f"client.id regression — gateway only grants operator scopes when "
        f"client.id == 'openclaw-control-ui', got {client['id']!r}. See #1720."
    )
    # Mode is informational on the gateway side but we keep webchat to
    # match the bundled control UI so log lines stay consistent.
    assert client["mode"] == "webchat"
    # The scope set we request must include operator.read so the gateway's
    # scope-grant table knows to mark our connection as readable.
    assert "operator.read" in msg["params"]["scopes"]
    assert "operator.admin" in msg["params"]["scopes"]
    assert msg["params"]["role"] == "operator"
