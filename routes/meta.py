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
    resp = make_response(render_template_string(_d.DASHBOARD_HTML, version=_d.__version__))
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


@bp_version_impact.route("/api/version-impact")
def api_version_impact():
    """Return version transition list with before/after metric comparisons."""
    import dashboard as _d
    current_version = _d._get_openclaw_version()
    _d._record_version_if_changed(current_version)

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
