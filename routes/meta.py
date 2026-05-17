"""
routes/meta.py — Auth / gateway / OTLP / version / clusters / version-impact.

Extracted from dashboard.py as Phase 5.12 of the incremental modularisation.
Six small Blueprints bundled into one file because each is tiny (1-3 routes)
and they are all auth/meta/observability plumbing:

  bp_version        (2)  — /api/version, /api/update
  bp_gateway        (3)  — /api/gw/{config,invoke,rpc}
  bp_auth           (3)  — /api/auth/check, /auth, /  (main page)
  bp_otel           (3)  — /v1/metrics, /v1/traces, /api/otel-status
  bp_version_impact (1)  — /api/version-impact
  bp_clusters       (1)  — /api/clusters

Module-level helpers (``_auto_discover_gateway``, ``_gw_invoke_docker``,
``_gw_invoke``, ``_gw_ws_rpc``, ``_load_gw_config``, ``_ext_emit``,
``_process_otlp_metrics``, ``_process_otlp_traces``, ``_has_otel_data``,
``_get_openclaw_version``, ``_record_version_if_changed``,
``_version_impact_db``, ``_compute_session_stats_in_range``,
``_stats_to_summary``, ``_compute_diff``, ``_build_clusters``) and module
state (``GATEWAY_URL``, ``GATEWAY_TOKEN``, ``_ws_client``, ``_ws_connected``,
``_GW_CONFIG_FILE``, ``_CURRENT_PLATFORM``, ``__version__``, ``_pypi_cache``,
``_budget_paused``, ``_HAS_OTEL_PROTO``, ``_metrics_lock``, ``metrics_store``,
``_otel_last_received``, ``SESSIONS_DIR``, ``DASHBOARD_HTML``) stay in
``dashboard.py`` and are reached via late ``import dashboard as _d``.

The ``@app.before_request`` ``_check_auth`` hook is registered on the global
Flask app, not a Blueprint, so it stays in ``dashboard.py``.

Pure mechanical move — zero behaviour change.
"""

import html
import json
import os
import sys
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, make_response, render_template_string, request
from clawmetry.config import is_local_store_read_enabled

bp_version = Blueprint('version', __name__)
bp_gateway = Blueprint('gateway', __name__)
bp_auth = Blueprint('auth', __name__)
bp_otel = Blueprint('otel', __name__)
bp_version_impact = Blueprint('version_impact', __name__)
bp_clusters = Blueprint('clusters', __name__)


# ── Version check & self-update routes ────────────────────────────────────────


@bp_version.route("/api/version")
def api_version():
    """Return current and latest version info."""
    import dashboard as _d
    import time as _time
    import json as _json

    current = _d.__version__
    latest = current
    update_available = False
    now = _time.time()
    # Cache PyPI check for 1 hour
    if _d._pypi_cache["version"] and (now - _d._pypi_cache["ts"]) < 3600:
        latest = _d._pypi_cache["version"]
    else:
        try:
            import urllib.request as _ur

            req = _ur.Request(
                "https://pypi.org/pypi/clawmetry/json",
                headers={"User-Agent": "clawmetry/" + current},
            )
            with _ur.urlopen(req, timeout=10) as resp:
                data = _json.loads(resp.read().decode())
                latest = data.get("info", {}).get("version", current)
                _d._pypi_cache["version"] = latest
                _d._pypi_cache["ts"] = now
        except Exception:
            pass
    if latest != current:
        # Compare version tuples
        try:
            cur_parts = [int(x) for x in current.split(".")]
            lat_parts = [int(x) for x in latest.split(".")]
            update_available = lat_parts > cur_parts
        except Exception:
            update_available = latest != current
    return {"current": current, "latest": latest, "update_available": update_available}


@bp_version.route("/api/update", methods=["POST"])
def api_update():
    """Self-update clawmetry via pip, then schedule process restart."""
    import dashboard as _d
    import subprocess as _sp
    import threading as _thr

    old_version = _d.__version__
    try:
        _sp.check_call(
            [sys.executable, "-m", "pip", "install", "--upgrade", "clawmetry"],
            timeout=120,
            stdout=_sp.DEVNULL,
            stderr=_sp.STDOUT,
        )
    except Exception as exc:
        return {"ok": False, "error": str(exc)}, 500
    # Re-read new version from pip metadata
    new_version = old_version
    try:
        out = _sp.check_output(
            [sys.executable, "-m", "pip", "show", "clawmetry"],
            timeout=10,
        ).decode()
        for line in out.splitlines():
            if line.startswith("Version:"):
                new_version = line.split(":", 1)[1].strip()
                break
    except Exception:
        pass

    # Schedule restart after response is sent
    def _restart():
        import os as _os

        _os._exit(0)

    _thr.Timer(2.0, _restart).start()
    return {"ok": True, "old_version": old_version, "new_version": new_version}


@bp_version.route("/api/install-age")
def api_install_age():
    """Return the ctime of ``~/.clawmetry/config.json`` as a Unix epoch.

    Used by the Brain restoration toast (issue #1195) to distinguish
    fresh installs from upgrades across the 0.12.182 empty-detail
    regression window. Returns ``{exists: false, ctime: null}`` when the
    config file is missing (fresh install with no prior daemon).
    """
    cfg_path = os.path.expanduser("~/.clawmetry/config.json")
    try:
        st = os.stat(cfg_path)
        # Prefer ctime (inode creation) over mtime, since `clawmetry connect`
        # rewrites the file on every key change. ctime is closer to "first
        # ever install" than mtime.
        return {"exists": True, "ctime": int(st.st_ctime), "mtime": int(st.st_mtime)}
    except FileNotFoundError:
        return {"exists": False, "ctime": None, "mtime": None}
    except Exception:
        # Never crash on bad filesystem state; treat as fresh-install.
        return {"exists": False, "ctime": None, "mtime": None}


# ── Gateway proxy routes ──────────────────────────────────────────────────────


@bp_gateway.route("/api/gw/config", methods=["GET", "POST"])
def api_gw_config():
    """Get or set gateway configuration."""
    import dashboard as _d
    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        token = data.get("token", "").strip()
        if not token:
            return jsonify({"error": "Token is required"}), 400
        # Auto-discover gateway port by scanning common ports
        gw_url = data.get("url", "").strip()
        if not gw_url:
            gw_url = _d._auto_discover_gateway(token)
        if not gw_url:
            return jsonify(
                {"error": "Could not find OpenClaw gateway. Please provide URL."}
            ), 404
        # Validate the connection
        valid = False

        # Docker mode: skip HTTP/WS, validate via docker exec
        if gw_url.startswith("docker://"):
            result = _d._gw_invoke_docker("session_status", {}, token)
            if result:
                valid = True

        # WebSocket validation (non-docker)
        if not valid and not gw_url.startswith("docker://"):
            ws_url = gw_url.replace("http://", "ws://").replace("https://", "wss://")
            try:
                import websocket

                ws = websocket.create_connection(f"{ws_url}/", timeout=5)
                ws.recv()  # challenge
                connect_msg = {
                    "type": "req",
                    "id": "validate",
                    "method": "connect",
                    "params": {
                        "minProtocol": 3,
                        "maxProtocol": 3,
                        "client": {
                            "id": "cli",
                            "version": _d.__version__,
                            "platform": _d._CURRENT_PLATFORM,
                            "mode": "cli",
                            "instanceId": "clawmetry-validate",
                        },
                        "role": "operator",
                        "scopes": ["operator.admin", "operator.read"],
                        "auth": {"token": token},
                    },
                }
                ws.send(json.dumps(connect_msg))
                for _ in range(5):
                    r = json.loads(ws.recv())
                    if r.get("type") == "res" and r.get("id") == "validate":
                        valid = r.get("ok", False)
                        break
                ws.close()
            except Exception:
                pass

        # HTTP fallback validation (non-docker)
        if not valid and not gw_url.startswith("docker://"):
            try:
                payload = json.dumps({"tool": "session_status", "args": {}}).encode()
                req = _d._urllib_req.Request(
                    f"{gw_url.rstrip('/')}/tools/invoke",
                    data=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with _d._urllib_req.urlopen(req, timeout=5) as resp:
                    result = json.loads(resp.read())
                    valid = result.get("ok", False)
            except Exception:
                pass

        # Docker exec fallback (last resort)
        if not valid:
            result = _d._gw_invoke_docker("session_status", {}, token)
            if result:
                valid = True
                gw_url = "docker://localhost:18789"

        if not valid:
            return jsonify({"error": "Invalid token or gateway not responding"}), 401
        # Save config
        _d.GATEWAY_URL = gw_url
        _d.GATEWAY_TOKEN = token
        # Reset WS connection to use new credentials
        _d._ws_connected = False
        _d._ws_client = None
        cfg = {"url": gw_url, "token": token}
        try:
            with open(_d._GW_CONFIG_FILE, "w") as f:
                json.dump(cfg, f)
            os.chmod(_d._GW_CONFIG_FILE, 0o600)
        except Exception:
            pass
        return jsonify({"ok": True, "url": gw_url})
    else:
        cfg = _d._load_gw_config()
        return jsonify(
            {
                "configured": bool(cfg.get("url") and cfg.get("token")),
                "url": cfg.get("url", ""),
                "hasToken": bool(cfg.get("token")),
            }
        )


@bp_gateway.route("/api/gw/invoke", methods=["POST"])
def api_gw_invoke():
    """Proxy a tool invocation to the OpenClaw gateway."""
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    tool = data.get("tool")
    args = data.get("args", {})
    if not tool:
        return jsonify({"error": "tool is required"}), 400
    if _d._budget_paused and tool in ("sessions_spawn", "session_start", "session.create"):
        return jsonify(
            {"error": "Auto-pause active: refusing new session starts", "paused": True}
        ), 429
    result = _d._gw_invoke(tool, args)
    if result is None:
        return jsonify({"error": "Gateway not configured or unreachable"}), 503
    return jsonify(result)


@bp_gateway.route("/api/gw/rpc", methods=["POST"])
def api_gw_rpc():
    """Proxy a JSON-RPC method call to the OpenClaw gateway via WebSocket."""
    import dashboard as _d
    data = request.get_json(silent=True) or {}
    method = data.get("method", "")
    params = data.get("params", {})
    if not method:
        return jsonify({"error": "method is required"}), 400
    result = _d._gw_ws_rpc(method, params)
    if result is None:
        return jsonify({"error": "Gateway not connected or method failed"}), 503
    return jsonify(result)


# ── Auth routes ───────────────────────────────────────────────────────────────


@bp_auth.route("/api/auth/check")
def api_auth_check():
    """Check if auth is required and validate token."""
    import dashboard as _d
    if not _d.GATEWAY_TOKEN:
        return jsonify({"authRequired": True, "valid": False, "needsSetup": True})
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        token = request.args.get("token", "").strip()
    if token == _d.GATEWAY_TOKEN:
        try:
            _d._ext_emit("auth.check", {"ok": True})
        except Exception:
            pass
        return jsonify({"authRequired": True, "valid": True})
    return jsonify({"authRequired": True, "valid": False})


# Loopback addresses allowed to bootstrap their auth header via
# /api/auth/detected-token. Anything else (LAN IP, public IP, proxied request)
# is rejected with 403 to keep the GATEWAY_TOKEN from leaking off-box.
_LOOPBACK_ADDRS = frozenset({"127.0.0.1", "::1", "localhost"})

# Host header values accepted by the bootstrap endpoint. A browser pointed at a
# DNS-rebound name (evil.com → 127.0.0.1) will still send Host: evil.com, so we
# reject anything outside this set even when remote_addr is loopback.
_LOOPBACK_HOSTS = frozenset({"localhost", "127.0.0.1", "[::1]", "::1"})


def _is_loopback_request(req) -> bool:
    """Return True iff *req* originates from this machine without a proxy.

    Four checks must all hold:

    1. ``REMOTE_ADDR`` (read from raw WSGI environ, not the Flask attribute,
       so a future ProxyFix wrap can't silently invert this) is one of the
       loopback aliases above.
    2. ``Host:`` header (sans port) is also a loopback alias — defends
       against DNS rebinding where remote_addr is genuinely loopback but
       the page origin is attacker-controlled.
    3. No ``X-Forwarded-For`` / ``X-Real-IP`` / ``Forwarded`` header is
       present. Their presence means *something* on the path declared
       this request was proxied; even on a loopback peer we must assume
       the original client could be remote.
    4. The dashboard was started bound to a loopback host. If the operator
       passed ``--host 0.0.0.0`` (LAN exposure), refuse to hand out the
       token at all — we cannot tell from a single request whether the
       browser is on this box or on the LAN.
    """
    raw_addr = (req.environ.get("REMOTE_ADDR") or "").strip().lower()
    if raw_addr not in _LOOPBACK_ADDRS:
        return False
    host = (req.host or "").strip().lower()
    if host.startswith("["):
        # Bracketed IPv6: "[::1]" or "[::1]:8900" -> "[::1]"
        end = host.find("]")
        if end != -1:
            host = host[: end + 1]
    elif ":" in host:
        # IPv4 / hostname with port -> strip port
        host = host.rsplit(":", 1)[0]
    if host not in _LOOPBACK_HOSTS:
        return False
    if req.headers.get("X-Forwarded-For", "").strip():
        return False
    if req.headers.get("X-Real-IP", "").strip():
        return False
    if req.headers.get("Forwarded", "").strip():
        return False
    if not _server_bound_loopback():
        return False
    return True


def _server_bound_loopback() -> bool:
    """Did we boot bound to a loopback host? Defaults to True when unknown.

    The dashboard records its bind address in ``_d._SERVER_HOST`` when
    served via ``cli.serve()``. If that attribute is missing (pytest /
    ad-hoc imports), assume loopback — the test harness drives requests
    from the same process anyway.
    """
    import dashboard as _d
    bind = getattr(_d, "_SERVER_HOST", None)
    if not bind:
        return True
    bind = str(bind).strip().lower()
    return bind in _LOOPBACK_ADDRS or bind in {"", "localhost"}


def _detected_token_source(token: str):
    """Best-effort label for where ``token`` was sourced from.

    Re-walks the same locations as ``dashboard._detect_gateway_token``
    (env var → running gateway process → openclaw.json) and returns the
    first match. ``"process"`` is the Linux ``/proc/<pid>/environ`` path
    that lets us read the live gateway's env vars even when the user
    never exported ``OPENCLAW_GATEWAY_TOKEN`` in their own shell.

    Falls back to ``"openclaw.json"`` if no source can be confirmed —
    that's the most common origin in practice and the label only drives
    a UI hint, never a security decision.
    """
    import dashboard as _d
    if not token:
        return "openclaw.json"
    env_token = os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
    if env_token and env_token == token:
        return "env"
    # Linux /proc-based discovery from the running openclaw-gateway process.
    try:
        import subprocess as _sp

        result = _sp.run(
            ["pgrep", "-f", "openclaw-gateway"],
            capture_output=True,
            text=True,
            timeout=3,
        )
        for pid in (result.stdout or "").strip().split("\n"):
            pid = pid.strip()
            if not pid:
                continue
            try:
                with open(f"/proc/{pid}/environ", "r") as f:
                    env_data = f.read()
            except (PermissionError, FileNotFoundError, OSError):
                continue
            for entry in env_data.split("\0"):
                if entry.startswith("OPENCLAW_GATEWAY_TOKEN="):
                    if entry.split("=", 1)[1] == token:
                        return "process"
    except Exception:
        pass
    # Fall through: assume openclaw.json (or one of the other config files
    # _detect_gateway_token scans). We don't re-read the file just to
    # confirm — the label is informational, and `_d.GATEWAY_TOKEN` being
    # populated already proves *some* discovery path succeeded.
    return "openclaw.json"


@bp_auth.route("/api/auth/detected-token")
def api_auth_detected_token():
    """Return the locally-detected gateway token to bootstrap the dashboard.

    Solves a chicken-and-egg problem: the dashboard JS needs the token
    *before* it can send any authenticated request, but the token lives
    in OpenClaw's config — not in the browser. This endpoint hands the
    token back to the page on first load, but ONLY when the request is
    provably loopback-local and unproxied. Anything else gets 403.

    Intentionally callable without an Authorization header — this IS
    the bootstrap.
    """
    import dashboard as _d
    if not _is_loopback_request(request):
        return jsonify({"error": "localhost only"}), 403
    token = getattr(_d, "GATEWAY_TOKEN", None)
    if not token:
        return jsonify({"error": "no token detected"}), 404
    return jsonify({"token": token, "source": _detected_token_source(token)})


# ── Anonymous funnel-loss instrumentation (issue #1365) ──────────────────────
# Allowed event names. Keep this tiny — every new value is an analytics
# schema commitment. Today we only ship the one funnel we got burned on
# in #1357 (typo'd pgrep killed auto-detect).
_ANON_ALLOWED_EVENTS = frozenset({"auth_fail_first_load"})
_ANON_ALLOWED_UA = frozenset({"chrome", "safari", "firefox", "other"})
_ANON_LOG_PATH = os.path.expanduser("~/.clawmetry/anon_events.jsonl")
# Hard caps: defence in depth against anything that slips past the JS
# helpers and posts pathological payloads.
_ANON_VERSION_MAX = 32
_ANON_EVENT_MAX = 64
_ANON_LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB rolling cap — older entries pruned.

# Fields that MUST NEVER appear in a body — defense against accidental PII
# leak if a future caller forgets the schema. Server rejects 400 on any.
_ANON_FORBIDDEN_FIELDS = frozenset({
    "token", "auth", "authorization", "bearer", "password", "secret",
    "ip", "remote_addr", "x_forwarded_for", "user_id", "email", "username",
    "session_id", "cookie",
})


def _anon_append_local(payload: dict) -> None:
    """Append ``payload`` as a JSONL line to the local durable log.

    Local DuckDB is process-locked (see memory: DuckDB locks at PROCESS
    level — daemon owns the writer). We don't want to add a daemon-proxy
    hop for a fire-and-forget telemetry ping, so we use a plain JSONL
    file as the durable record. The daemon can flush it to cloud later;
    losing a few lines on crash is acceptable for a counter ping.
    """
    try:
        os.makedirs(os.path.dirname(_ANON_LOG_PATH), exist_ok=True)
        # Rolling cap: if the file is over the limit, truncate. We could
        # do a proper rotate, but this is a counter ping — keeping the
        # most recent 5 MB is more than enough for funnel-loss analysis.
        try:
            if os.path.getsize(_ANON_LOG_PATH) > _ANON_LOG_MAX_BYTES:
                with open(_ANON_LOG_PATH, "w"):
                    pass
        except OSError:
            pass
        with open(_ANON_LOG_PATH, "a") as fh:
            fh.write(json.dumps(payload, separators=(",", ":")) + "\n")
    except Exception:
        # Telemetry must never break the dashboard. Eat all errors.
        pass


def _anon_forward_cloud(payload: dict) -> None:
    """Best-effort POST to the cloud analytics ingest. Fail-silent.

    The cloud endpoint may not exist yet — that's fine, the local JSONL
    is the durable record. We try anyway so once cloud catches up, the
    OSS side starts feeding live data without another release.
    """
    try:
        import urllib.request as _ur
        req = _ur.Request(
            "https://app.clawmetry.com/api/admin/anon-event",
            data=json.dumps(payload, separators=(",", ":")).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Short timeout — never block the OSS request thread on the cloud.
        _ur.urlopen(req, timeout=2).close()
    except Exception:
        pass


@bp_auth.route("/api/anon-auth-fail-ping", methods=["POST"])
def api_anon_auth_fail_ping():
    """Receive an anonymous funnel-loss ping from the dashboard JS.

    Triggered by the OSS dashboard's bootstrap path when ``/api/auth/check``
    rejects on first page-load with no prior token in localStorage. The
    typo regression of #1357 was completely invisible to us because no
    such ping existed; this is the early-warning canary so we catch the
    next one within a day instead of a week.

    Strict allowlist on schema — any unexpected field, any token-like
    name, any unbucketed UA class is a 400. We default-deny to keep the
    "anonymous only" invariant verifiable from a single function.
    """
    body = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify({"error": "body must be a JSON object"}), 400

    # Defense in depth: reject any forbidden field before parsing the
    # allowed ones. If a future client (or attacker) tries to sneak
    # ``{event: ..., token: "leak"}`` past us, we'd rather 400 than
    # silently drop the token and persist the rest.
    for key in body.keys():
        if str(key).strip().lower() in _ANON_FORBIDDEN_FIELDS:
            return jsonify({"error": "forbidden field in body"}), 400

    event = str(body.get("event") or "").strip()
    version = str(body.get("version") or "").strip()
    ua_class = str(body.get("user_agent_class") or "").strip().lower()

    if event not in _ANON_ALLOWED_EVENTS:
        return jsonify({"error": "unknown event"}), 400
    if ua_class not in _ANON_ALLOWED_UA:
        return jsonify({"error": "unknown user_agent_class"}), 400
    if not version or len(version) > _ANON_VERSION_MAX:
        return jsonify({"error": "invalid version"}), 400
    if len(event) > _ANON_EVENT_MAX:
        return jsonify({"error": "event too long"}), 400

    # Build the durable record. Server stamps ``ts`` (UTC seconds) so the
    # client clock can't pollute the time series. No IP, no user id, no
    # token — explicitly so.
    payload = {
        "ts": int(time.time()),
        "event": event,
        "version": version,
        "user_agent_class": ua_class,
    }
    # Both helpers swallow their own errors, but we wrap defensively
    # too: if a future refactor accidentally lets an exception escape,
    # we still return 200 to the dashboard instead of breaking boot.
    try:
        _anon_append_local(payload)
    except Exception:
        pass
    try:
        _anon_forward_cloud(payload)
    except Exception:
        pass
    return jsonify({"ok": True})


@bp_auth.route("/auth")
def auth_token():
    """Accept ?token=XXX, store in localStorage via JS, redirect to /.
    Works for both OSS gateway tokens and cloud cm_ keys.
    URL: /auth?token=YOUR_TOKEN
    """
    token = request.args.get("token", "").strip()
    if not token:
        return (
            '<html><body style="background:#0b0f1a;color:#e2e8f0;font-family:sans-serif;padding:40px;">'
            "<h2>Missing token</h2><p>Usage: <code>/auth?token=YOUR_TOKEN</code></p></body></html>",
            400,
        )
    # Escape token before JS interpolation. html.escape with quote=True converts
    # ' and " to &#x27; / &quot; which break out of the JS string-literal
    # context inside <script>...</script> (the browser does NOT decode HTML
    # entities inside raw <script> content, so the escaped form is just inert
    # literal characters). Originally reported by @dumko2001 in #511.
    escaped = html.escape(token, quote=True)
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="background:#0b0f1a;color:#e2e8f0;font-family:sans-serif;padding:40px;min-height:100vh;">
<p>Authenticating...</p>
<script>
  localStorage.setItem('clawmetry-token', '{escaped}');
  localStorage.setItem('clawmetry-gw-token', '{escaped}');
  window.location.href = '/';
</script>
</body></html>"""


@bp_auth.route("/")
def index():
    import dashboard as _d
    # v2_enabled gates the unobtrusive "Try v2" link in the v1 sidebar
    # (week-1 migration plan, README §"What to communicate"). Mirrors the
    # same env var the v2 blueprint registration in dashboard.py uses, so we
    # never advertise /v2 to users who'd hit a 404.
    v2_enabled = os.environ.get("CLAWMETRY_V2") == "1"
    resp = make_response(
        render_template_string(
            _d.DASHBOARD_HTML,
            version=_d.__version__,
            v2_enabled=v2_enabled,
        )
    )
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return resp


# ── OTLP receiver routes ──────────────────────────────────────────────────────


@bp_otel.route("/v1/metrics", methods=["POST"])
def otlp_metrics():
    """OTLP/HTTP receiver for metrics (protobuf)."""
    import dashboard as _d
    if _d._budget_paused:
        return jsonify(
            {"error": "Budget limit exceeded - intake paused", "paused": True}
        ), 429
    if not _d._HAS_OTEL_PROTO:
        return jsonify(
            {
                "error": "opentelemetry-proto not installed",
                "message": "Install OTLP support: pip install clawmetry[otel]  "
                "or: pip install opentelemetry-proto protobuf",
            }
        ), 501

    try:
        pb_data = request.get_data()
        _d._process_otlp_metrics(pb_data)
        return "{}", 200, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp_otel.route("/v1/traces", methods=["POST"])
def otlp_traces():
    """OTLP/HTTP receiver for traces (protobuf)."""
    import dashboard as _d
    if _d._budget_paused:
        return jsonify(
            {"error": "Budget limit exceeded - intake paused", "paused": True}
        ), 429
    if not _d._HAS_OTEL_PROTO:
        return jsonify(
            {
                "error": "opentelemetry-proto not installed",
                "message": "Install OTLP support: pip install clawmetry[otel]  "
                "or: pip install opentelemetry-proto protobuf",
            }
        ), 501

    try:
        pb_data = request.get_data()
        _d._process_otlp_traces(pb_data)
        return "{}", 200, {"Content-Type": "application/json"}
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@bp_otel.route("/api/otel-status")
def api_otel_status():
    """Return OTLP receiver status."""
    import dashboard as _d
    counts = {}
    with _d._metrics_lock:
        for k in _d.metrics_store:
            counts[k] = len(_d.metrics_store[k])
    return jsonify(
        {
            "available": _d._HAS_OTEL_PROTO,
            "hasData": _d._has_otel_data(),
            "lastReceived": _d._otel_last_received,
            "counts": counts,
        }
    )


# ── Version impact analysis ───────────────────────────────────────────────────


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Mirrors ``routes/usage.py:_ls_call`` — daemon HTTP proxy first
    (covers the standard install where the daemon owns the DuckDB writer
    lock), then falls back to a direct read-only open for single-process
    boots (tests + dev mode). Returns ``None`` on miss so callers defer
    to the legacy SQLite + JSONL fallback path.
    """
    try:
        from routes.local_query import local_store_via_daemon
        result = local_store_via_daemon(method_name, **kwargs)
        if result is not None:
            return result
    except Exception:
        pass
    try:
        from clawmetry import local_store
        store = local_store.get_store(read_only=True)
        return getattr(store, method_name)(**kwargs)
    except Exception:
        return None


def _to_epoch(s):
    """Parse an ISO-8601 timestamp string to a Unix epoch seconds float.

    Returns 0.0 on failure so callers can sort/compare uniformly.
    """
    if not s:
        return 0.0
    if isinstance(s, (int, float)):
        return float(s)
    try:
        return datetime.fromisoformat(
            str(s).replace("Z", "+00:00")
        ).timestamp()
    except Exception:
        return 0.0


def _try_local_store_version_impact(current_version):
    """DuckDB fast path for /api/version-impact (Tier-1 #1565).

    Strategy:

    1. Pull every ``session.started`` event (these carry ``data.version``
       on real OpenClaw v3 installs — see
       ``clawmetry/sync.py::_parse_v3_event`` and
       ``reference_openclaw_v3_event_types.md``).
    2. Group by version → earliest detection timestamp. That gives us the
       same shape the legacy SQLite ``version_events`` table tracks
       (version + detected_at), but derived from real session activity
       rather than per-process polling. Replaces the JSONL re-walk that
       happened on every request.
    3. For each adjacent (prev, curr) version pair, aggregate per-session
       stats (token spend, cost, tool-call count, error count, duration)
       for sessions that started inside the version's active window.
       Uses ``query_sessions`` (already sibling-pair deduped at the SQL
       layer per issue #1460) for cost+tokens, and ``query_events`` for
       tool/error counts.

    Returns ``None`` when no ``session.started`` events carry a version
    field — older installs / fresh DuckDB stores fall through to the
    SQLite + JSONL legacy path so the route never regresses to empty.
    """
    started_rows = _ls_call("query_events", event_type="session.started", limit=5000)
    if started_rows is None:
        return None

    # Group by version → (earliest_ts, session_ids_seen).
    versions_seen: dict[str, dict] = {}
    for row in started_rows:
        data = row.get("data") if isinstance(row.get("data"), dict) else {}
        version = (data.get("version") or data.get("openclawVersion")
                   or data.get("openclaw_version"))
        if not version:
            continue
        version = str(version)
        ts_epoch = _to_epoch(row.get("ts"))
        if ts_epoch <= 0:
            continue
        entry = versions_seen.setdefault(version, {"earliest": ts_epoch, "sids": set()})
        if ts_epoch < entry["earliest"]:
            entry["earliest"] = ts_epoch
        sid = row.get("session_id")
        if sid:
            entry["sids"].add(sid)

    if not versions_seen:
        # No version-bearing events — defer to SQLite/JSONL fallback.
        return None

    # Sort versions by earliest-detected ascending — matches the legacy
    # SQLite ``version_events`` ORDER BY detected_at ASC.
    version_order = sorted(versions_seen.items(), key=lambda kv: kv[1]["earliest"])
    now_ts = time.time()

    def _summarise_range(start_ts, end_ts):
        """Aggregate per-session metrics for sessions started in [start, end)."""
        since_iso = datetime.fromtimestamp(start_ts, tz=timezone.utc).isoformat()
        until_iso = datetime.fromtimestamp(end_ts, tz=timezone.utc).isoformat()
        sessions = _ls_call("query_sessions", since=since_iso, until=until_iso,
                            limit=10000) or []
        # tool/error counts come from the raw events table (query_sessions
        # gives us deduped cost+tokens but not tool-call frequency).
        events = _ls_call("query_events", since=since_iso, until=until_iso,
                          limit=20000) or []
        tool_types = {"tool_call", "tool.call", "toolCall", "tool_use"}
        error_types = {"error", "session.error", "model.error"}
        per_sid_tools: dict[str, int] = {}
        per_sid_errors: dict[str, int] = {}
        for ev in events:
            sid = ev.get("session_id")
            if not sid:
                continue
            et = ev.get("event_type") or ""
            if et in tool_types:
                per_sid_tools[sid] = per_sid_tools.get(sid, 0) + 1
            elif et in error_types:
                per_sid_errors[sid] = per_sid_errors.get(sid, 0) + 1

        total_cost = 0.0
        total_tokens = 0
        total_tools = 0
        total_errors = 0
        duration_ms_total = 0
        duration_sessions = 0
        session_count = 0
        for s in sessions:
            sid = s.get("session_id")
            if not sid:
                continue
            session_count += 1
            total_cost += float(s.get("cost_usd") or 0.0)
            total_tokens += int(s.get("token_count") or 0)
            total_tools += per_sid_tools.get(sid, 0)
            total_errors += per_sid_errors.get(sid, 0)
            start_s = _to_epoch(s.get("started_at"))
            end_s = _to_epoch(s.get("updated_at"))
            if start_s and end_s and end_s > start_s:
                duration_ms_total += int((end_s - start_s) * 1000)
                duration_sessions += 1
        return {
            "session_count": session_count,
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "error_count": total_errors,
            "tool_calls": total_tools,
            "duration_ms_total": duration_ms_total,
            "duration_sessions": duration_sessions,
        }

    import dashboard as _d
    transitions = []
    version_history = []

    for i, (version, info) in enumerate(version_order):
        start_ts = info["earliest"]
        end_ts = (version_order[i + 1][1]["earliest"]
                  if i + 1 < len(version_order) else now_ts)
        version_history.append({
            "version": version,
            "detected_at": datetime.fromtimestamp(
                start_ts, tz=timezone.utc
            ).isoformat(),
        })
        if i == 0:
            continue
        prev_version, prev_info = version_order[i - 1]
        before = _d._stats_to_summary(
            _summarise_range(prev_info["earliest"], start_ts))
        after = _d._stats_to_summary(_summarise_range(start_ts, end_ts))
        transitions.append({
            "from_version": prev_version,
            "to_version": version,
            "upgraded_at": datetime.fromtimestamp(
                start_ts, tz=timezone.utc
            ).isoformat(),
            "before": before,
            "after": after,
            "diff": _d._compute_diff(before, after),
        })

    return {
        "current_version": (current_version
                            or version_order[-1][0]
                            or "unknown"),
        "version_detected": bool(current_version),
        "version_history": version_history,
        "transitions": transitions,
        "_source": "local_store",
    }


@bp_version_impact.route("/api/version-impact")
def api_version_impact():
    """Return version transition list with before/after metric comparisons."""
    import dashboard as _d
    current_version = _d._get_openclaw_version()
    _d._record_version_if_changed(current_version)

    # DuckDB fast path: derive version timeline + per-version stats from
    # session.started events in the local store. Returns None on fresh
    # installs / pre-v3 data so the legacy SQLite + JSONL walker stays
    # the canonical fallback.
    if is_local_store_read_enabled():
        fast = _try_local_store_version_impact(current_version)
        if fast is not None:
            return jsonify(fast)

    db = _d._version_impact_db()
    try:
        rows = db.execute(
            "SELECT version, detected_at FROM version_events ORDER BY detected_at ASC"
        ).fetchall()
    finally:
        db.close()

    if not rows:
        return jsonify(
            {
                "current_version": current_version or "unknown",
                "transitions": [],
                "version_detected": bool(current_version),
                "note": "No version history yet. Version tracking starts from first load."
                if not current_version
                else "First version recorded. Comparisons will appear after next version upgrade.",
            }
        )

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    transitions = []
    now_ts = time.time()

    for i in range(len(rows)):
        row = rows[i]
        version = row["version"]
        start_ts = row["detected_at"]
        end_ts = rows[i + 1]["detected_at"] if i + 1 < len(rows) else now_ts

        if i > 0:
            prev_row = rows[i - 1]
            prev_version = prev_row["version"]
            prev_start = prev_row["detected_at"]
            prev_end = start_ts

            before_stats = _d._compute_session_stats_in_range(
                sessions_dir, prev_start, prev_end
            )
            after_stats = _d._compute_session_stats_in_range(
                sessions_dir, start_ts, end_ts
            )

            before_summary = _d._stats_to_summary(before_stats)
            after_summary = _d._stats_to_summary(after_stats)
            diff = _d._compute_diff(before_summary, after_summary)

            transitions.append(
                {
                    "from_version": prev_version,
                    "to_version": version,
                    "upgraded_at": datetime.fromtimestamp(
                        start_ts, tz=timezone.utc
                    ).isoformat(),
                    "before": before_summary,
                    "after": after_summary,
                    "diff": diff,
                }
            )

    return jsonify(
        {
            "current_version": current_version
            or (rows[-1]["version"] if rows else "unknown"),
            "version_detected": bool(current_version),
            "version_history": [
                {
                    "version": r["version"],
                    "detected_at": datetime.fromtimestamp(
                        r["detected_at"], tz=timezone.utc
                    ).isoformat(),
                }
                for r in rows
            ],
            "transitions": transitions,
        }
    )


# ── Trace clustering ──────────────────────────────────────────────────────────


@bp_clusters.route("/api/clusters")
def api_clusters():
    """Return session clusters grouped by tool call pattern, cost, and error types."""
    import dashboard as _d
    sessions_dir = getattr(_d, "SESSIONS_DIR", None) or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    # Issue #1088: opt-in DuckDB fast path. Delegates to the same DuckDB-driven
    # clustering used by /api/sessions/clusters and exposes a thinner shape
    # (clusters + total_clusters) — _source: "local_store" for tests.
    if is_local_store_read_enabled():
        try:
            from routes.usage import _try_local_store_sessions_clusters
            fast = _try_local_store_sessions_clusters(30)
            if fast is not None:
                return jsonify({
                    "clusters": fast.get("clusters", []),
                    "total_clusters": len(fast.get("clusters", [])),
                    "sessions_dir": sessions_dir,
                    "_source": "local_store",
                })
        except Exception:
            pass
    # Cloud's dashboard.py doesn't ship _build_clusters; fall through to an
    # empty 200 instead of leaking a 500 with an AttributeError body into the
    # user's console. (When cloud_route_policy is loaded, this endpoint is
    # normally returned as 410 by the policy enforcer; this guard is the
    # defence-in-depth path for environments where the policy isn't active.)
    build_clusters = getattr(_d, "_build_clusters", None)
    if build_clusters is None:
        return jsonify(
            {"clusters": [], "total_clusters": 0, "sessions_dir": sessions_dir}
        )
    try:
        clusters = build_clusters(sessions_dir)
        return jsonify(
            {
                "clusters": clusters,
                "total_clusters": len(clusters),
                "sessions_dir": sessions_dir,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "clusters": []}), 500
