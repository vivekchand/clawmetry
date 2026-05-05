"""
helpers/gateway.py — OpenClaw gateway WebSocket RPC + HTTP invoke client.

Extracted from dashboard.py as Phase 6.5. Owns the persistent WebSocket
JSON-RPC client used for live gateway queries (sessions.list, cron.list,
etc.) and the HTTP `/tools/invoke` fan-out (with a docker-exec fallback
for installs where the gateway binds only to loopback inside a container).

Re-exported from dashboard.py: `_gw_invoke`, `_gw_invoke_docker` (what
routes/*.py actually reach via `_d.<name>`). `_gw_ws_rpc` and
`_gw_ws_connect` are also accessed as `_d._gw_ws_rpc` from routes/meta.py
and internally from dashboard.py — Python's module caching means
`dashboard._gw_ws_rpc` resolves to this module's function as soon as
dashboard.py imports it, so no explicit re-export line is needed for
those two.

CLI/config detection (``_load_gw_config``, ``_detect_gateway_token``,
``GATEWAY_URL``/``GATEWAY_TOKEN`` globals) stays in dashboard.py because
it is intertwined with argparse and the live OpenClaw config. We reach
those via late ``import dashboard as _d`` inside the functions below —
the same pattern routes/*.py use.
"""

import json
import subprocess
import threading


# ── WebSocket RPC Client ────────────────────────────────────────────────
# Persistent connection state. Shared by all threads that call
# `_gw_ws_rpc`; the lock serialises send/recv pairs so responses don't
# get scrambled across concurrent callers.
_ws_client = None
_ws_lock = threading.Lock()
_ws_connected = False


def _gw_ws_connect(url=None, token=None):
    """Connect to the OpenClaw gateway via WebSocket JSON-RPC."""
    global _ws_client, _ws_connected
    try:
        import websocket
    except ImportError:
        return False

    import dashboard as _d

    cfg = _d._load_gw_config()
    ws_url = (
        (url or cfg.get("url", "") or "")
        .replace("http://", "ws://")
        .replace("https://", "wss://")
        .rstrip("/")
    )
    tok = token or cfg.get("token", "")
    if not ws_url or not tok:
        return False

    try:
        # timeout=5 applies to the initial TCP/WS handshake; we also set
        # ws.settimeout(5) below so per-message recv() can't hang forever if
        # the gateway accepts the connection but never responds.
        ws = websocket.create_connection(f"{ws_url}/", timeout=5)
        ws.settimeout(5)
        # Read challenge event
        ws.recv()
        # Send connect
        connect_msg = {
            "type": "req",
            "id": "clawmetry-connect",
            "method": "connect",
            "params": {
                "minProtocol": 3,
                "maxProtocol": 3,
                "client": {
                    "id": "cli",
                    "version": _d.__version__,
                    "platform": _d._CURRENT_PLATFORM,
                    "mode": "cli",
                    "instanceId": f"clawmetry-{_d._uuid.uuid4().hex[:8]}",
                },
                "role": "operator",
                "scopes": ["operator.read", "operator.admin"],
                "auth": {"token": tok},
            },
        }
        ws.send(json.dumps(connect_msg))
        # Wait for connect response
        for _ in range(5):
            r = json.loads(ws.recv())
            if r.get("type") == "res" and r.get("id") == "clawmetry-connect":
                if r.get("ok"):
                    _ws_client = ws
                    _ws_connected = True
                    return True
                else:
                    ws.close()
                    return False
        ws.close()
    except Exception:
        pass
    return False


def _gw_ws_rpc(method, params=None):
    """Make a JSON-RPC call over the WebSocket connection. Returns payload or None."""
    global _ws_client, _ws_connected
    import dashboard as _d

    with _ws_lock:
        if not _ws_connected or _ws_client is None:
            if not _gw_ws_connect():
                return None
        try:
            mid = f"cm-{_d._uuid.uuid4().hex[:8]}"
            msg = {"type": "req", "id": mid, "method": method, "params": params or {}}
            # Per-message timeout so a stalled gateway can't pin the waitress
            # request thread indefinitely. 5s is plenty for gateway RPCs
            # (typical round-trip <50ms); if something blocks longer we fail
            # fast and the caller renders an empty state.
            try:
                _ws_client.settimeout(5)
            except Exception:
                pass
            _ws_client.send(json.dumps(msg))
            # Read responses, skipping events
            for _ in range(30):
                r = json.loads(_ws_client.recv())
                if r.get("type") == "res" and r.get("id") == mid:
                    if r.get("ok"):
                        return r.get("payload", {})
                    else:
                        return None
        except Exception:
            # Connection lost or recv timed out — reset so the next call
            # reconnects fresh instead of reusing a wedged socket.
            _ws_connected = False
            try:
                _ws_client.close()
            except Exception:
                pass
            _ws_client = None
    return None


def _gw_invoke(tool, args=None):
    """Invoke a tool via the OpenClaw gateway /tools/invoke endpoint.
    Tries: 1) Direct HTTP, 2) Docker exec fallback."""
    import dashboard as _d

    cfg = _d._load_gw_config()
    token = cfg.get("token")
    url = cfg.get("url")

    # Try direct HTTP first
    if url and token:
        try:
            payload = json.dumps({"tool": tool, "args": args or {}}).encode()
            req = _d._urllib_req.Request(
                f"{url.rstrip('/')}/tools/invoke",
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with _d._urllib_req.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                if data.get("ok"):
                    return data.get("result", {}).get("details", data.get("result", {}))
        except Exception:
            pass

    # Fallback: docker exec (for Hostinger/Docker installs where gateway binds to loopback)
    if token:
        result = _gw_invoke_docker(tool, args, token)
        if result:
            return result

    return None


def _gw_invoke_docker(tool, args=None, token=None):
    """Invoke gateway API via docker exec (when gateway is inside Docker)."""
    try:
        container_id = (
            subprocess.check_output(
                ["docker", "ps", "-q"], timeout=3, stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
            .split("\n")[0]
        )
        if not container_id:
            return None
        payload = json.dumps({"tool": tool, "args": args or {}})
        cmd = [
            "docker",
            "exec",
            container_id,
            "curl",
            "-s",
            "--max-time",
            "8",
            "-X",
            "POST",
            "http://127.0.0.1:18789/tools/invoke",
            "-H",
            f"Authorization: Bearer {token}",
            "-H",
            "Content-Type: application/json",
            "-d",
            payload,
        ]
        output = subprocess.check_output(
            cmd, timeout=15, stderr=subprocess.DEVNULL
        ).decode()
        if output:
            data = json.loads(output)
            if data.get("ok"):
                return data.get("result", {}).get("details", data.get("result", {}))
    except Exception:
        pass
    return None
