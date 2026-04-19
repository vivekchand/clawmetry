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

import json
import os
import sys
import time
from datetime import datetime, timezone

from flask import Blueprint, jsonify, make_response, render_template_string, request

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
                        "scopes": ["operator.read", "operator.admin"],
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
    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"></head>
<body style="background:#0b0f1a;color:#e2e8f0;font-family:sans-serif;padding:40px;min-height:100vh;">
<p>Authenticating...</p>
<script>
  localStorage.setItem('clawmetry-token', '{token}');
  localStorage.setItem('clawmetry-gw-token', '{token}');
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
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    try:
        clusters = _d._build_clusters(sessions_dir)
        return jsonify(
            {
                "clusters": clusters,
                "total_clusters": len(clusters),
                "sessions_dir": sessions_dir,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e), "clusters": []}), 500
