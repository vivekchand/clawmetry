"""Issue #4356: _gw_ws_connect must back off after gateway rejections.

When the gateway rejects the handshake (e.g. protocol-4 with mismatched
maxProtocol), the dashboard polled endpoints (/api/sessions, /api/crons)
each call _gw_ws_connect() on every HTTP request. Without backoff, fast
concurrent requests produce bursts of reconnect attempts — gateway logs
fill with warnings at ~5/100ms. This regression guard confirms the
exponential-backoff gate fires correctly.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import helpers.gateway as gw  # noqa: E402


@pytest.fixture(autouse=True)
def _reset_gateway_state():
    """Reset all WS singleton state between tests."""
    gw._ws_client = None
    gw._ws_connected = False
    gw._ws_fail_count = 0
    gw._ws_next_retry_time = 0.0
    yield
    gw._ws_client = None
    gw._ws_connected = False
    gw._ws_fail_count = 0
    gw._ws_next_retry_time = 0.0


def _make_fake_dashboard(monkeypatch):
    fake = MagicMock()
    fake._load_gw_config.return_value = {
        "url": "http://127.0.0.1:18789", "token": "test-token"
    }
    fake.__version__ = "0.0.0-test"
    fake._CURRENT_PLATFORM = "test"
    fake._uuid = __import__("uuid")
    monkeypatch.setitem(sys.modules, "dashboard", fake)
    return fake


def _ws_rejecting(monkeypatch):
    """Stub websocket whose connect response is ok=False."""
    fake_ws = MagicMock()
    fake_ws.recv.side_effect = [
        json.dumps({"type": "event", "event": "connect.challenge", "payload": {}}),
        json.dumps({"type": "res", "id": "clawmetry-connect", "ok": False,
                    "error": {"message": "protocol-mismatch"}}),
    ]
    fake_websocket = MagicMock()
    fake_websocket.create_connection.return_value = fake_ws
    monkeypatch.setitem(sys.modules, "websocket", fake_websocket)
    return fake_websocket, fake_ws


def _ws_accepting(monkeypatch):
    """Stub websocket whose connect response is ok=True."""
    fake_ws = MagicMock()
    fake_ws.recv.side_effect = [
        json.dumps({"type": "event", "event": "connect.challenge", "payload": {}}),
        json.dumps({"type": "res", "id": "clawmetry-connect", "ok": True,
                    "payload": {"auth": {"scopes": ["operator.admin", "operator.read"]}}}),
    ]
    fake_websocket = MagicMock()
    fake_websocket.create_connection.return_value = fake_ws
    monkeypatch.setitem(sys.modules, "websocket", fake_websocket)
    return fake_websocket, fake_ws


def test_backoff_blocks_retry_after_rejection(monkeypatch):
    """A rejected handshake must block the next attempt until the backoff window expires."""
    fake_wm, _ = _ws_rejecting(monkeypatch)
    _make_fake_dashboard(monkeypatch)

    # First call: gateway rejects — should return False and record next_retry_time.
    assert gw._gw_ws_connect() is False
    assert gw._ws_fail_count == 1
    assert gw._ws_next_retry_time > 0.0
    first_create_calls = fake_wm.create_connection.call_count
    assert first_create_calls == 1

    # Second call immediately after: backoff window is active — must NOT call
    # create_connection again (that would re-hammer the gateway).
    assert gw._gw_ws_connect() is False
    assert fake_wm.create_connection.call_count == 1, (
        "create_connection was called again during the backoff window — "
        "this is the reconnect-storm bug from issue #4356."
    )


def test_backoff_delay_grows_with_each_failure(monkeypatch):
    """Each successive failure must schedule a longer retry delay (exponential)."""
    import time as _time

    _make_fake_dashboard(monkeypatch)
    delays = []

    for i, delay in enumerate(gw._WS_BACKOFF_DELAYS):
        # Force _ws_next_retry_time to zero so the guard passes each time.
        gw._ws_next_retry_time = 0.0
        gw._ws_fail_count = i

        fake_wm, _ = _ws_rejecting(monkeypatch)
        before = _time.monotonic()
        gw._gw_ws_connect()
        scheduled = gw._ws_next_retry_time - before
        delays.append(scheduled)

    for i, (actual, expected) in enumerate(zip(delays, gw._WS_BACKOFF_DELAYS)):
        assert actual >= expected - 0.1, (
            f"Backoff delay at failure {i} is {actual:.1f}s, expected ≥{expected}s."
        )
    # Verify the ladder is monotonically increasing (no regression to flat retry).
    assert delays[0] < delays[-1], "Backoff delays must grow across retries."


def test_success_resets_backoff(monkeypatch):
    """A successful connection must clear fail_count and next_retry_time."""
    _make_fake_dashboard(monkeypatch)

    # Prime the backoff state as if we had a prior failure.
    gw._ws_fail_count = 3
    gw._ws_next_retry_time = 0.0  # allow through for this test

    _ws_accepting(monkeypatch)
    assert gw._gw_ws_connect() is True
    assert gw._ws_fail_count == 0, "fail_count must reset to 0 after success."
    assert gw._ws_next_retry_time == 0.0, "next_retry_time must reset to 0 after success."
    assert gw._ws_connected is True
