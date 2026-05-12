"""
routes/health.py — Health / reliability / diagnostics / rate-limits endpoints.

Extracted from dashboard.py as Phase 5.5 of the incremental modularisation.
Owns the 11 routes registered on bp_health:

  GET  /api/reliability           — cross-session behavioral reliability trend
  GET  /api/heatmap               — activity heatmap (events per hour, N days)
  GET  /api/system-health         — comprehensive system health (services, disks, crons)
  GET  /api/health                — health check panel (gateway/disk/memory/uptime/otel)
  GET  /api/diagnostics           — detected configuration snapshot
  GET  /api/service-status        — compact service_status for fleet heartbeat
  GET  /api/heartbeat-status      — heartbeat gap alerting status
  POST /api/heartbeat-ping        — record a heartbeat from frontend
  GET  /api/rate-limits           — rolling 1m/1h API rate-limit utilisation
  GET  /api/health-stream         — SSE auto-refresh of health checks (30s)
  GET  /api/sandbox-status        — sandbox / inference / security posture
  GET  /api/loop-detection        — scan recent sessions for repeated tool-call loops (#849)

Module-level helpers (``_history_db``, ``AgentReliabilityScorer``,
``_find_log_file``, ``SESSIONS_DIR``, ``_load_gw_config``, ``_detect_gateway_port``,
``EXTRA_SERVICES``, ``MC_URL``, ``_gw_invoke``, ``_gw_invoke_docker``,
``_detect_disk_mounts``, ``_get_crons``, ``_get_sessions``,
``_get_heartbeat_status``, ``_detect_sandbox_metadata``,
``_detect_inference_metadata``, ``_detect_security_metadata``,
``_detect_channel_status``, ``_record_heartbeat``, ``_has_otel_data``,
``_otel_last_received``, ``metrics_store``, ``_HAS_OTEL_PROTO``,
``GATEWAY_URL``, ``WORKSPACE``, ``GATEWAY_TOKEN``, ``validate_configuration``,
``_metrics_lock``, ``_infer_provider``, ``_DEFAULT_RATE_LIMITS``,
``_acquire_stream_slot``, ``_release_stream_slot``, ``SSE_MAX_SECONDS``,
``app``) stay in ``dashboard.py`` and are reached via late
``import dashboard as _d``. Pure mechanical move — zero behaviour change.
"""

import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta

from flask import Blueprint, Response, jsonify, request

bp_health = Blueprint('health', __name__)


@bp_health.route("/api/reliability")
def api_reliability():
    """Cross-session behavioral reliability trend (AgentReliabilityScorer)."""
    import dashboard as _d
    if not _d._history_db or not _d.AgentReliabilityScorer:
        return jsonify(
            {"error": "History module not available", "direction": "insufficient_data"}
        ), 200
    try:
        window = int(request.args.get("window", 30))
        window = max(1, min(window, 90))
        scorer = _d.AgentReliabilityScorer(_d._history_db)
        result = scorer.score(window_days=window)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "direction": "insufficient_data"}), 500


@bp_health.route("/api/heatmap")
def api_heatmap():
    """Activity heatmap - events per hour for the last N days (default 7, max 90).

    Query params:
      days: int  number of days to show (1-90, default 7)
    """
    import dashboard as _d
    try:
        n_days = max(1, min(90, int(request.args.get("days", 7))))
    except (ValueError, TypeError):
        n_days = 7

    now = datetime.now()
    # Initialize N days × 24 hours grid
    grid = {}
    day_labels = []
    for i in range(n_days - 1, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        grid[ds] = [0] * 24
        lbl = d.strftime("%b %d") if n_days > 7 else d.strftime("%a %d")
        day_labels.append({"date": ds, "label": lbl})

    # Source 1: log files
    for i in range(n_days):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        log_file = _d._find_log_file(ds)
        if not log_file:
            continue
        try:
            with open(log_file) as lf:
                for line in lf:
                    try:
                        obj = json.loads(line.strip())
                        ts = obj.get("time") or (
                            obj.get("_meta", {}).get("date")
                            if isinstance(obj.get("_meta"), dict)
                            else None
                        )
                        if ts:
                            if isinstance(ts, (int, float)):
                                dt = datetime.fromtimestamp(
                                    ts / 1000 if ts > 1e12 else ts
                                )
                            else:
                                dt = datetime.fromisoformat(
                                    str(ts).replace("Z", "+00:00").replace("+00:00", "")
                                )
                            day_key = dt.strftime("%Y-%m-%d")
                            if day_key in grid:
                                grid[day_key][dt.hour] += 1
                    except Exception:
                        if ds in grid:
                            grid[ds][12] += 1  # default to noon
        except Exception:
            pass

    # Source 2: session JSONL files (fills gaps when log files missing)
    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    cutoff = now - timedelta(days=n_days)
    if sessions_dir and os.path.isdir(sessions_dir):
        try:
            for fname in os.listdir(sessions_dir):
                if not fname.endswith(".jsonl") or "deleted" in fname:
                    continue
                fpath = os.path.join(sessions_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if datetime.fromtimestamp(mtime) < cutoff:
                        continue
                    with open(fpath, errors="replace") as sf:
                        for line in sf:
                            try:
                                obj = json.loads(line.strip())
                                ts = (
                                    obj.get("timestamp")
                                    or obj.get("ts")
                                    or obj.get("time")
                                    or (
                                        obj.get("_meta", {}).get("date")
                                        if isinstance(obj.get("_meta"), dict)
                                        else None
                                    )
                                )
                                if not ts:
                                    continue
                                if isinstance(ts, (int, float)):
                                    dt = datetime.fromtimestamp(
                                        ts / 1000 if ts > 1e12 else ts
                                    )
                                else:
                                    dt = datetime.fromisoformat(
                                        str(ts)
                                        .replace("Z", "+00:00")
                                        .replace("+00:00", "")
                                    )
                                if dt < cutoff:
                                    continue
                                day_key = dt.strftime("%Y-%m-%d")
                                if day_key in grid:
                                    grid[day_key][dt.hour] += 1
                            except Exception:
                                pass
                except Exception:
                    pass
        except Exception:
            pass

    max_val = max(max(hours) for hours in grid.values()) if grid else 0
    days_out = []
    for dl in day_labels:
        days_out.append({"label": dl["label"], "hours": grid.get(dl["date"], [0] * 24)})

    return jsonify({"days": days_out, "max": max_val, "n_days": n_days})


@bp_health.route("/api/system-health")
def api_system_health():
    """Comprehensive system health for the Overview tab."""
    import dashboard as _d
    import shutil

    # --- SERVICES (auto-detect gateway + user-configured extras) ---
    services = []
    # Always check OpenClaw Gateway (from gateway config or auto-detect)
    cfg = _d._load_gw_config()
    if cfg.get("url"):
        try:
            from urllib.parse import urlparse

            gw_port = urlparse(cfg["url"]).port or 18789
        except Exception:
            gw_port = _d._detect_gateway_port()
    else:
        gw_port = _d._detect_gateway_port()
    service_checks = [("OpenClaw Gateway", gw_port)]
    # Add any user-configured extra services
    for svc in _d.EXTRA_SERVICES:
        service_checks.append((svc["name"], svc["port"]))
    # Add Mission Control only if MC_URL is explicitly configured
    if _d.MC_URL:
        try:
            from urllib.parse import urlparse

            mc_parsed = urlparse(_d.MC_URL)
            mc_port = mc_parsed.port or 3002
            service_checks.append(("Mission Control", mc_port))
        except Exception:
            pass
    for name, port in service_checks:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            ok = s.connect_ex(("127.0.0.1", port)) == 0
            s.close()
            # If direct socket fails and this is the gateway, try docker exec
            if not ok and "Gateway" in name:
                cfg_check = _d._load_gw_config()
                if cfg_check.get("url", "").startswith("docker://") or cfg_check.get(
                    "token"
                ):
                    docker_result = _d._gw_invoke_docker(
                        "session_status", {}, cfg_check.get("token")
                    )
                    if docker_result:
                        ok = True
            services.append({"name": name, "port": port, "up": ok})
        except Exception:
            services.append({"name": name, "port": port, "up": False})

    # --- DISK USAGE ---
    disks = []
    for mount in _d._detect_disk_mounts():
        try:
            usage = shutil.disk_usage(mount)
            used_gb = usage.used / (1024**3)
            total_gb = usage.total / (1024**3)
            pct = (usage.used / usage.total) * 100
            disks.append(
                {
                    "mount": mount,
                    "used_gb": round(used_gb, 1),
                    "total_gb": round(total_gb, 1),
                    "pct": round(pct, 1),
                }
            )
        except Exception:
            pass

    # --- CRON JOBS ---
    gw_cron_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": True})
    crons = (
        gw_cron_data.get("jobs", [])
        if gw_cron_data and "jobs" in gw_cron_data
        else _d._get_crons()
    )
    cron_enabled = len([j for j in crons if j.get("enabled", True)])
    cron_ok_24h = 0
    cron_failed = []
    now_ts = time.time()
    for j in crons:
        last = j.get("lastRun", {})
        if not last:
            continue
        run_ts = last.get("timestamp", 0)
        if isinstance(run_ts, str):
            try:
                run_ts = datetime.fromisoformat(
                    run_ts.replace("Z", "+00:00")
                ).timestamp()
            except Exception:
                run_ts = 0
        if run_ts and (now_ts - run_ts) < 86400:
            if last.get("exitCode", last.get("exit", 0)) == 0 and not last.get("error"):
                cron_ok_24h += 1
            else:
                cron_failed.append(j.get("name", j.get("id", "unknown")))

    # --- SUB-AGENTS (24H) ---
    sessions = _d._get_sessions()
    sa_runs = 0
    sa_success = 0
    for s in sessions:
        mtime = s.get("updatedAt", 0)
        if isinstance(mtime, (int, float)) and mtime > 1e12:
            mtime = mtime / 1000
        if mtime and (now_ts - mtime) < 86400:
            sid = s.get("sessionId", "")
            if "subagent" in sid:
                sa_runs += 1
                sa_success += 1  # We don't track failure in session files currently

    sa_pct = round((sa_success / sa_runs * 100) if sa_runs > 0 else 100, 0)

    # Build compact service_status dict (fleet node card format)
    gw_up = any(s["name"] == "OpenClaw Gateway" and s["up"] for s in services)
    resources_state = "ok"
    if disks:
        max_pct = max(d["pct"] for d in disks)
        if max_pct >= 95:
            resources_state = "critical"
        elif max_pct >= 80:
            resources_state = "warn"
    service_status = {
        "gateway": gw_up,
        "channels": [],  # populated by sync daemon from live gateway data
        "sync": True,  # dashboard is running = sync present
        "resources": resources_state,
    }

    return jsonify(
        {
            "services": services,
            "channels": _d._detect_channel_status(),
            "disks": disks,
            "crons": {
                "enabled": cron_enabled,
                "ok24h": cron_ok_24h,
                "failed": cron_failed,
            },
            "subagents": {"runs": sa_runs, "successPct": sa_pct},
            "heartbeat": _d._get_heartbeat_status(),
            "sandbox": _d._detect_sandbox_metadata(),
            "inference": _d._detect_inference_metadata(),
            "security": _d._detect_security_metadata(),
            "service_status": service_status,
        }
    )


@bp_health.route("/api/health")
def api_health():
    """System health checks."""
    import dashboard as _d
    checks = []
    # 1. Gateway - check if gateway port is responding
    gw_port = _d._detect_gateway_port()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex(("127.0.0.1", gw_port))
        s.close()
        if result == 0:
            checks.append(
                {
                    "id": "gateway",
                    "status": "healthy",
                    "color": "green",
                    "detail": f"Port {gw_port} responding",
                }
            )
        else:
            # Fallback: check process (Unix only)
            gw_proc = None
            if sys.platform != "win32":
                gw_proc = subprocess.run(
                    ["pgrep", "-f", "moltbot"], capture_output=True, text=True, timeout=2
                )
            if gw_proc and gw_proc.returncode == 0:
                checks.append(
                    {
                        "id": "gateway",
                        "status": "warning",
                        "color": "yellow",
                        "detail": "Process running, port not responding",
                    }
                )
            else:
                checks.append(
                    {
                        "id": "gateway",
                        "status": "critical",
                        "color": "red",
                        "detail": "Not running",
                    }
                )
    except Exception:
        checks.append(
            {
                "id": "gateway",
                "status": "critical",
                "color": "red",
                "detail": "Check failed",
            }
        )

    # 2. Disk space - warn if < 5GB free
    try:
        st = os.statvfs("/")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        total_gb = (st.f_blocks * st.f_frsize) / (1024**3)
        pct_used = ((total_gb - free_gb) / total_gb) * 100
        if free_gb < 2:
            checks.append(
                {
                    "id": "disk",
                    "status": "critical",
                    "color": "red",
                    "detail": f"{free_gb:.1f} GB free ({pct_used:.0f}% used)",
                }
            )
        elif free_gb < 5:
            checks.append(
                {
                    "id": "disk",
                    "status": "warning",
                    "color": "yellow",
                    "detail": f"{free_gb:.1f} GB free ({pct_used:.0f}% used)",
                }
            )
        else:
            checks.append(
                {
                    "id": "disk",
                    "status": "healthy",
                    "color": "green",
                    "detail": f"{free_gb:.1f} GB free ({pct_used:.0f}% used)",
                }
            )
    except Exception:
        checks.append(
            {
                "id": "disk",
                "status": "warning",
                "color": "yellow",
                "detail": "Check failed",
            }
        )

    # 3. Memory usage (RSS of this process + overall)
    try:
        import resource

        rss_mb = (
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
        )  # KB -> MB on Linux
        mem = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=2)
        mem_parts = mem.stdout.strip().split("\n")[1].split()
        used_mb = int(mem_parts[2])
        total_mb = int(mem_parts[1])
        pct = (used_mb / total_mb) * 100
        if pct > 90:
            checks.append(
                {
                    "id": "memory",
                    "status": "critical",
                    "color": "red",
                    "detail": f"{used_mb}MB / {total_mb}MB ({pct:.0f}%)",
                }
            )
        elif pct > 75:
            checks.append(
                {
                    "id": "memory",
                    "status": "warning",
                    "color": "yellow",
                    "detail": f"{used_mb}MB / {total_mb}MB ({pct:.0f}%)",
                }
            )
        else:
            checks.append(
                {
                    "id": "memory",
                    "status": "healthy",
                    "color": "green",
                    "detail": f"{used_mb}MB / {total_mb}MB ({pct:.0f}%)",
                }
            )
    except Exception:
        checks.append(
            {
                "id": "memory",
                "status": "warning",
                "color": "yellow",
                "detail": "Check failed",
            }
        )

    # 4. Uptime
    try:
        uptime = (
            subprocess.run(["uptime", "-p"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .replace("up ", "")
        )
        checks.append(
            {"id": "uptime", "status": "healthy", "color": "green", "detail": uptime}
        )
    except Exception:
        checks.append(
            {
                "id": "uptime",
                "status": "warning",
                "color": "yellow",
                "detail": "Unknown",
            }
        )

    # 5. OTLP Metrics
    if _d._has_otel_data():
        ago = time.time() - _d._otel_last_received
        if ago < 300:  # <5min
            total = sum(len(_d.metrics_store[k]) for k in _d.metrics_store)
            checks.append(
                {
                    "id": "otel",
                    "status": "healthy",
                    "color": "green",
                    "detail": f"Connected - {total} data points, last {int(ago)}s ago",
                }
            )
        elif ago < 3600:
            checks.append(
                {
                    "id": "otel",
                    "status": "warning",
                    "color": "yellow",
                    "detail": f"Stale - last data {int(ago / 60)}m ago",
                }
            )
        else:
            checks.append(
                {
                    "id": "otel",
                    "status": "warning",
                    "color": "yellow",
                    "detail": f"Stale - last data {int(ago / 3600)}h ago",
                }
            )
    elif _d._HAS_OTEL_PROTO:
        checks.append(
            {
                "id": "otel",
                "status": "warning",
                "color": "yellow",
                "detail": "OTLP ready - no data received yet",
            }
        )
    else:
        checks.append(
            {
                "id": "otel",
                "status": "warning",
                "color": "yellow",
                "detail": "Not installed - pip install clawmetry[otel]",
            }
        )

    return jsonify({"checks": checks})


@bp_health.route("/api/config-diagnostics")
@bp_health.route("/api/diagnostics")
def api_diagnostics():
    """Surface detected configuration for the Diagnostics panel (GH#28).

    Returns a snapshot of the auto-detected config so users can verify what
    ClawMetry found without digging through env vars or config files.

    Shape::

        {
          "gateway_url":        "http://localhost:18789",
          "gateway_port":       18789,
          "workspace_path":     "/home/user/clawd",
          "auth_token_status":  "present" | "missing",
          "openclaw_flags":     {"reasoning": "enabled", "model": "claude-3-5-sonnet"},
          "warnings":           ["[warn]  ..."],
          "auto_detected":      ["workspace", "gateway_port"]
        }
    """
    import dashboard as _d
    auto_detected = []

    # Gateway URL & port
    gw_port = _d._detect_gateway_port()
    gw_url = _d.GATEWAY_URL or f"http://localhost:{gw_port}"
    if not _d.GATEWAY_URL:
        auto_detected.append("gateway_port")

    # Workspace
    ws = _d.WORKSPACE or os.getcwd()
    if _d.WORKSPACE:
        auto_detected.append("workspace")

    # Auth token — never expose the value, only whether it is present
    token = _d.GATEWAY_TOKEN or os.environ.get("OPENCLAW_GATEWAY_TOKEN", "").strip()
    auth_token_status = "present" if token else "missing"

    # OpenClaw runtime flags from environment
    openclaw_flags = {}
    flag_map = {
        "OPENCLAW_MODEL": "model",
        "OPENCLAW_REASONING": "reasoning",
        "OPENCLAW_THINKING": "thinking",
        "OPENCLAW_MAX_TOKENS": "max_tokens",
    }
    for env_key, flag_name in flag_map.items():
        val = os.environ.get(env_key, "").strip()
        if val:
            openclaw_flags[flag_name] = val

    # Run validate_configuration for warnings/tips
    try:
        warnings_list, _tips = _d.validate_configuration()
    except Exception:
        warnings_list = []

    return jsonify(
        {
            "gateway_url": gw_url,
            "gateway_port": gw_port,
            "workspace_path": ws,
            "auth_token_status": auth_token_status,
            "openclaw_flags": openclaw_flags,
            "warnings": warnings_list,
            "auto_detected": auto_detected,
        }
    )


@bp_health.route("/api/service-status")
def api_service_status():
    """Compact service status for fleet heartbeat payloads.

    Returns a ``service_status`` dict suitable for inclusion in sync-daemon
    metrics pushes (``POST /api/nodes/<id>/metrics``).  The fleet overview
    uses this shape to render per-node status dots.

    Shape::

        {
          "gateway": true,          # bool: gateway port responding
          "channels": [             # active OpenClaw channels
            {"name": "telegram", "connected": true},
            {"name": "discord",  "connected": false}
          ],
          "sync": true,             # bool: clawmetry sync process running
          "resources": "ok"         # "ok" | "warn" | "critical"
        }
    """
    import dashboard as _d
    cfg = _d._load_gw_config()
    # ── Gateway ──────────────────────────────────────────────────────────────
    gw_port = _d._detect_gateway_port()
    if cfg.get("url"):
        try:
            from urllib.parse import urlparse as _upl

            gw_port = _upl(cfg["url"]).port or gw_port
        except Exception:
            pass
    try:
        _s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _s.settimeout(2)
        gw_up = _s.connect_ex(("127.0.0.1", gw_port)) == 0
        _s.close()
    except Exception:
        gw_up = False

    # ── Channels ─────────────────────────────────────────────────────────────
    channels_out = []
    try:
        gw_data = _d._gw_invoke("status", {})
        if gw_data and isinstance(gw_data.get("channels"), list):
            for ch in gw_data["channels"]:
                channels_out.append(
                    {
                        "name": str(ch.get("name", ch.get("kind", "unknown"))),
                        "connected": bool(ch.get("connected", ch.get("ok", False))),
                    }
                )
    except Exception:
        pass
    # Fallback: detect from config file
    if not channels_out:
        try:
            raw_cfg = cfg.get("channels") or []
            for ch in raw_cfg:
                if isinstance(ch, dict):
                    channels_out.append(
                        {
                            "name": str(ch.get("kind", ch.get("name", "channel"))),
                            "connected": None,  # unknown without live data
                        }
                    )
        except Exception:
            pass

    # ── Sync daemon (is clawmetry running?) ──────────────────────────────────
    sync_up = False
    try:
        if sys.platform != "win32":
            result = subprocess.run(
                ["pgrep", "-f", "clawmetry"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            sync_up = result.returncode == 0
        else:
            sync_up = True  # cannot easily detect on Windows; assume ok
    except Exception:
        sync_up = True  # dashboard IS running, so sync is present

    # ── Resources ────────────────────────────────────────────────────────────
    resources = "ok"
    try:
        st = os.statvfs("/")
        free_gb = (st.f_bavail * st.f_frsize) / (1024**3)
        if free_gb < 2:
            resources = "critical"
        elif free_gb < 5:
            resources = "warn"
    except Exception:
        pass
    try:
        mem_out = subprocess.run(
            ["free", "-m"], capture_output=True, text=True, timeout=3
        )
        if mem_out.returncode == 0:
            parts = mem_out.stdout.strip().split("\n")[1].split()
            used_mb = int(parts[2])
            total_mb = int(parts[1])
            if total_mb > 0 and (used_mb / total_mb) > 0.95:
                resources = "critical" if resources == "ok" else resources
            elif total_mb > 0 and (used_mb / total_mb) > 0.85:
                resources = "warn" if resources == "ok" else resources
    except Exception:
        pass

    return jsonify(
        {
            "service_status": {
                "gateway": gw_up,
                "channels": channels_out,
                "sync": sync_up,
                "resources": resources,
            }
        }
    )


def _try_local_store_heartbeat_status(node_id=None):
    """Epic #964: opt-in local-store fast path for /api/heartbeat-status.

    Returns the same response shape as ``_get_heartbeat_status()`` derived from
    the most-recent row in the DuckDB ``heartbeats`` table (optionally scoped
    to ``node_id``). Returns ``None`` to defer to the in-memory globals if:

      - the local_store module isn't importable
      - the heartbeats table is empty (fresh install / non-OpenClaw user)
      - any unexpected error happens (we'd rather degrade than 500)

    The fast path is most useful on multi-node fleets where the dashboard
    process didn't witness the heartbeat itself (the sync daemon on each node
    persists its own heartbeat row, but ``_last_heartbeat_ts`` lives in
    dashboard memory and only sees what the local websocket emitted).
    """
    try:
        from clawmetry import local_store
    except Exception:
        return None
    try:
        store = local_store.get_store()
        rows = store.query_heartbeats(limit=1, node_id=node_id) if node_id else store.query_heartbeats(limit=1)
    except Exception:
        return None
    if not rows:
        return None

    import dashboard as _d
    interval = int(_d._heartbeat_interval_sec)
    threshold = interval * 1.5
    now = time.time()

    last_ts_str = rows[0].get("ts") or ""
    try:
        last_ts = datetime.fromisoformat(last_ts_str.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None
    if last_ts <= 0:
        return None

    gap_sec = now - last_ts
    if gap_sec <= interval:
        status = "ok"
    elif gap_sec <= threshold:
        status = "warning"
    else:
        status = "silent"

    return {
        "status": status,
        "last_heartbeat_ts": last_ts,
        "gap_seconds": int(gap_sec),
        "interval_seconds": interval,
        "threshold_seconds": int(threshold),
        "silent_since": None,
        "_source": "local_store",
    }


@bp_health.route("/api/heartbeat-status")
def api_heartbeat_status():
    """Return heartbeat gap alerting status."""
    import dashboard as _d
    # Epic #964: opt-in local-store fast path. Optional ?node=<node_id> scopes
    # the lookup to one fleet node (otherwise: most-recent across all nodes).
    if os.environ.get("CLAWMETRY_LOCAL_STORE_READ") == "1":
        node = (request.args.get("node") or "").strip() or None
        fast = _try_local_store_heartbeat_status(node)
        if fast is not None:
            return jsonify(fast)
    return jsonify(_d._get_heartbeat_status())


@bp_health.route("/api/heartbeat-ping", methods=["POST"])
def api_heartbeat_ping():
    """Called by frontend when a heartbeat event is detected in log stream."""
    import dashboard as _d
    _d._record_heartbeat()
    return jsonify({"ok": True})


@bp_health.route('/api/rate-limits')
def api_rate_limits():
    """Return rolling 1-minute and 1-hour API rate limit utilisation per provider."""
    import dashboard as _d
    now = time.time()
    one_min_ago = now - 60
    one_hour_ago = now - 3600

    with _d._metrics_lock:
        token_entries = list(_d.metrics_store.get('tokens', []))
        cost_entries  = list(_d.metrics_store.get('cost', []))

    providers: dict = {}

    def _get_p(prov):
        if prov not in providers:
            providers[prov] = {
                'rpm_1m': 0, 'tokens_in_1m': 0, 'tokens_out_1m': 0,
                'tokens_in_1h': 0, 'tokens_out_1h': 0,
                'request_count_1h': 0, 'cost_1h': 0.0,
                'models': set(),
            }
        return providers[prov]

    for entry in token_entries:
        ts   = entry.get('timestamp', 0)
        prov = _d._infer_provider(entry)
        p    = _get_p(prov)
        p['models'].add(entry.get('model') or 'unknown')
        if ts >= one_min_ago:
            p['rpm_1m']       += 1
            p['tokens_in_1m'] += entry.get('input', 0)
            p['tokens_out_1m']+= entry.get('output', 0)
        if ts >= one_hour_ago:
            p['request_count_1h'] += 1
            p['tokens_in_1h']     += entry.get('input', 0)
            p['tokens_out_1h']    += entry.get('output', 0)

    for entry in cost_entries:
        ts   = entry.get('timestamp', 0)
        prov = _d._infer_provider(entry)
        p    = _get_p(prov)
        if ts >= one_hour_ago:
            p['cost_1h'] += entry.get('usd', 0)

    result = []
    for prov, stats in sorted(providers.items()):
        limits   = _d._DEFAULT_RATE_LIMITS.get(prov, {'rpm': 60, 'tpm_input': 100_000, 'tpm_output': 20_000, 'label': prov.title()})
        rpm_pct  = round(stats['rpm_1m']       / limits['rpm']        * 100, 1) if limits['rpm']        else 0
        in_pct   = round(stats['tokens_in_1m'] / limits['tpm_input']  * 100, 1) if limits['tpm_input']  else 0
        out_pct  = round(stats['tokens_out_1m']/ limits['tpm_output'] * 100, 1) if limits['tpm_output'] else 0
        worst    = max(rpm_pct, in_pct, out_pct)
        result.append({
            'provider': prov,
            'label':    limits.get('label', prov.title()),
            'models':   sorted(stats['models']),
            'rpm':       {'current': stats['rpm_1m'],        'limit': limits['rpm'],        'pct': rpm_pct},
            'tpm_input': {'current': stats['tokens_in_1m'],  'limit': limits['tpm_input'],  'pct': in_pct},
            'tpm_output':{'current': stats['tokens_out_1m'], 'limit': limits['tpm_output'], 'pct': out_pct},
            'hour': {
                'requests':   stats['request_count_1h'],
                'tokens_in':  stats['tokens_in_1h'],
                'tokens_out': stats['tokens_out_1h'],
                'cost_usd':   round(stats['cost_1h'], 4),
            },
            'utilization_pct': worst,
            'status': 'red' if worst >= 90 else ('amber' if worst >= 70 else 'green'),
        })

    result.sort(key=lambda x: x['utilization_pct'], reverse=True)
    return jsonify({'providers': result, 'timestamp': now})


@bp_health.route('/api/health-stream')
def api_health_stream():
    """SSE endpoint - auto-refresh health checks every 30 seconds."""
    import dashboard as _d
    if not _d._acquire_stream_slot("health"):
        return jsonify({"error": "Too many active health streams"}), 429

    def generate():
        started_at = time.time()
        try:
            while True:
                if time.time() - started_at > _d.SSE_MAX_SECONDS:
                    yield 'event: done\ndata: {"reason":"max_duration_reached"}\n\n'
                    break
                try:
                    with _d.app.test_request_context():
                        resp = api_health()
                        data = resp.get_json()
                        yield f"data: {json.dumps(data)}\n\n"
                except Exception:
                    yield f"data: {json.dumps({'checks': []})}\n\n"
                time.sleep(30)
        finally:
            _d._release_stream_slot("health")

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@bp_health.route("/api/sandbox-status")
def api_sandbox_status():
    """Dedicated endpoint: generic sandbox, inference provider & security posture.

    Returns:
        {
            "sandbox":   {"name": str, "status": str, "type": str} | null,
            "inference": {"provider": str, "model": str} | null,
            "security":  {"sandbox_enabled": bool, "network_policy": str} | null,
        }

    All top-level keys are always present; values are null when the respective
    metadata cannot be detected (platform-agnostic, no vendor logos/assumptions).
    """
    import dashboard as _d
    sandbox_raw = _d._detect_sandbox_metadata()
    inference_raw = _d._detect_inference_metadata()
    security_raw = _d._detect_security_metadata()

    # Normalise sandbox — keep only the three canonical fields
    sandbox = None
    if sandbox_raw and isinstance(sandbox_raw, dict):
        sandbox = {
            "name": sandbox_raw.get("name"),
            "status": sandbox_raw.get("status", "running"),
            "type": sandbox_raw.get("type"),
        }

    # Normalise inference — keep only the two canonical fields
    inference = None
    if inference_raw and isinstance(inference_raw, dict):
        inference = {
            "provider": inference_raw.get("provider"),
            "model": inference_raw.get("model"),
        }

    # Normalise security — keep only the two canonical fields
    security = None
    if security_raw and isinstance(security_raw, dict):
        sec_fields: dict = {}
        if "sandbox_enabled" in security_raw:
            sec_fields["sandbox_enabled"] = bool(security_raw["sandbox_enabled"])
        if "network_policy" in security_raw:
            sec_fields["network_policy"] = security_raw["network_policy"]
        if sec_fields:
            security = sec_fields

    return jsonify({"sandbox": sandbox, "inference": inference, "security": security})


# ---------------------------------------------------------------------------
# Loop / drift detection (#849)
# ---------------------------------------------------------------------------


def _detect_loops_in_sessions(sessions_dir, max_sessions=20, window=10, min_repeats=3):
    """Scan recent session JSONLs for repeated tool-call patterns.

    A "loop" is: the same (tool_name, args_fingerprint) pair appearing
    *min_repeats* or more times within a sliding window of *window* consecutive
    tool calls in a single session.  Returns (loops, checked) where *loops* is a
    deduplicated list of hits and *checked* is the number of files scanned.
    """
    try:
        all_names = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
        ]
    except OSError:
        return [], 0

    paths = sorted(
        [os.path.join(sessions_dir, n) for n in all_names],
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )[:max_sessions]

    loops = []

    for fpath in paths:
        session_id = os.path.splitext(os.path.basename(fpath))[0]
        tool_seq = []  # list of (tool_name, args_fp, ts_str)

        try:
            with open(fpath, errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue
                    if ev.get("type") != "message":
                        continue
                    msg = ev.get("message") or {}
                    if msg.get("role") != "assistant":
                        continue
                    content = msg.get("content") or []
                    if not isinstance(content, list):
                        continue
                    ts = ev.get("timestamp", "")
                    for blk in content:
                        if not isinstance(blk, dict):
                            continue
                        if blk.get("type") != "toolCall":
                            continue
                        name = (blk.get("name") or "").strip()
                        if not name:
                            continue
                        inp = blk.get("input") or {}
                        raw_args = json.dumps(inp, sort_keys=True, default=str)[:500]
                        fp = hashlib.md5(raw_args.encode()).hexdigest()[:8]
                        tool_seq.append((name, fp, ts))
        except Exception:
            continue

        if len(tool_seq) < min_repeats:
            continue

        seen_combos = set()
        for i in range(max(1, len(tool_seq) - window + 1)):
            chunk = tool_seq[i : i + window]
            counts = {}
            for name, fp, _ts in chunk:
                combo = (name, fp)
                counts[combo] = counts.get(combo, 0) + 1
            for combo, count in counts.items():
                if count >= min_repeats and combo not in seen_combos:
                    seen_combos.add(combo)
                    first_ts = next(
                        ts for n, f, ts in tool_seq if (n, f) == combo
                    )
                    loops.append({
                        "session_id": session_id,
                        "tool_name": combo[0],
                        "repeat_count": count,
                        "first_seen_ts": first_ts,
                    })

    return loops, len(paths)


@bp_health.route("/api/loop-detection")
def api_loop_detection():
    """Scan recent sessions for agent loop/drift patterns.

    Query params (all optional):
      max_sessions  — JSONL files to scan (default 20, max 50)
      window        — sliding window in tool calls (default 10, max 20)
      min_repeats   — repetitions needed to flag (default 3, max 10)

    Response:
      {
        "checked":    <int>,
        "loop_count": <int>,
        "loops": [
          {"session_id": str, "tool_name": str,
           "repeat_count": int, "first_seen_ts": str}
        ]
      }
    """
    import dashboard as _d

    try:
        max_sessions = max(1, min(50, int(request.args.get("max_sessions", 20))))
    except (TypeError, ValueError):
        max_sessions = 20
    try:
        window = max(3, min(20, int(request.args.get("window", 10))))
    except (TypeError, ValueError):
        window = 10
    try:
        min_repeats = max(2, min(10, int(request.args.get("min_repeats", 3))))
    except (TypeError, ValueError):
        min_repeats = 3

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )

    loops = []
    checked = 0

    if os.path.isdir(sessions_dir):
        try:
            loops, checked = _detect_loops_in_sessions(
                sessions_dir,
                max_sessions=max_sessions,
                window=window,
                min_repeats=min_repeats,
            )
        except Exception:
            pass

    return jsonify({
        "checked": checked,
        "loop_count": len(loops),
        "loops": loops,
    })


# ---------------------------------------------------------------------------
# MCP tool call observability (#850)
# ---------------------------------------------------------------------------

_BUILTIN_TOOLS = frozenset({
    "exec", "Exec",
    "Read", "Edit", "Write", "MultiEdit",
    "Glob", "Grep", "Bash",
    "web_search", "WebSearch", "web_fetch", "WebFetch",
    "browser", "Browser",
    "message", "tts", "image", "canvas",
    "nodes", "process",
    "sessions_spawn", "sessions_send", "session_status",
    "cron", "gateway",
    "TodoWrite", "TodoRead",
    "NotebookRead", "NotebookEdit",
    "computer", "Agent",
})


def _parse_ts_ms(val):
    """Return milliseconds-since-epoch for a timestamp value, or None."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        v = float(val)
        return v * 1000.0 if v < 1e10 else v
    try:
        s = str(val).strip().rstrip("Z")
        # Handle optional fractional seconds and timezone offset
        for fmt in (
            "%Y-%m-%dT%H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
        ):
            try:
                from datetime import datetime, timezone
                dt = datetime.strptime(s[:26], fmt)
                return dt.replace(tzinfo=timezone.utc).timestamp() * 1000.0
            except ValueError:
                continue
    except Exception:
        pass
    return None


def _collect_mcp_stats(sessions_dir, max_sessions=20):
    """Scan recent session JSONLs for external (non-builtin) tool call stats.

    Returns (stats_list, files_checked) where stats_list is a list of dicts:
      {name, calls, errors, error_rate_pct, avg_latency_ms}
    sorted by call count descending.
    """
    try:
        all_names = [
            f for f in os.listdir(sessions_dir)
            if f.endswith(".jsonl")
            and ".deleted." not in f
            and ".reset." not in f
        ]
    except OSError:
        return [], 0

    paths = sorted(
        [os.path.join(sessions_dir, n) for n in all_names],
        key=lambda p: os.path.getmtime(p),
        reverse=True,
    )[:max_sessions]

    # {tool_name: {calls, errors, latencies_ms}}
    tool_stats: dict = {}

    for fpath in paths:
        # Map toolCall id -> (name, start_ms) within this file
        pending: dict = {}

        try:
            with open(fpath, errors="replace") as fh:
                for raw in fh:
                    raw = raw.strip()
                    if not raw:
                        continue
                    try:
                        ev = json.loads(raw)
                    except Exception:
                        continue

                    ev_ts_ms = _parse_ts_ms(ev.get("timestamp"))
                    msg = ev.get("message") or {}
                    role = msg.get("role", "")

                    if role == "assistant":
                        content = msg.get("content") or []
                        if not isinstance(content, list):
                            continue
                        for blk in content:
                            if not isinstance(blk, dict):
                                continue
                            if blk.get("type") != "toolCall":
                                continue
                            name = (blk.get("name") or "").strip()
                            if not name or name in _BUILTIN_TOOLS:
                                continue
                            if name not in tool_stats:
                                tool_stats[name] = {"calls": 0, "errors": 0, "latencies_ms": []}
                            tool_stats[name]["calls"] += 1
                            tc_id = blk.get("id", "")
                            if tc_id:
                                pending[tc_id] = (name, ev_ts_ms)

                    elif role == "toolResult":
                        tc_id = msg.get("toolCallId", "")
                        if not tc_id or tc_id not in pending:
                            continue
                        name, start_ms = pending.pop(tc_id)
                        if msg.get("isError"):
                            tool_stats[name]["errors"] += 1
                        if start_ms and ev_ts_ms and ev_ts_ms > start_ms:
                            latency = ev_ts_ms - start_ms
                            if latency < 300_000:  # ignore pairs > 5 min apart
                                tool_stats[name]["latencies_ms"].append(latency)
        except Exception:
            continue

    result = []
    for name, s in tool_stats.items():
        calls = s["calls"]
        errors = s["errors"]
        lats = s["latencies_ms"]
        result.append({
            "name": name,
            "calls": calls,
            "errors": errors,
            "error_rate_pct": round(errors * 100.0 / calls, 1) if calls else 0.0,
            "avg_latency_ms": round(sum(lats) / len(lats)) if lats else None,
        })

    result.sort(key=lambda x: x["calls"], reverse=True)
    return result, len(paths)


@bp_health.route("/api/mcp-stats")
def api_mcp_stats():
    """Per-tool stats for non-builtin (MCP / external) tool calls.

    Scans the 20 most-recently-modified session JSONLs and returns call
    counts, error rates, and average latency for every tool whose name is
    not in the standard OpenClaw built-in set.

    Response:
      {
        "checked": <int>,
        "tools": [
          {"name": str, "calls": int, "errors": int,
           "error_rate_pct": float, "avg_latency_ms": int|null}
        ]
      }
    """
    import dashboard as _d

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )

    tools: list = []
    checked = 0

    if os.path.isdir(sessions_dir):
        try:
            tools, checked = _collect_mcp_stats(sessions_dir)
        except Exception:
            pass

    return jsonify({"checked": checked, "tools": tools})
