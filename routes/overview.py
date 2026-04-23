"""
routes/overview.py — Main-dashboard endpoints.

Extracted from dashboard.py as Phase 5.8 of the incremental modularisation.
Owns the 8 routes registered on ``bp_overview``:

  GET  /api/channels              — active input channels for Flow diagram
  GET  /api/overview              — top-bar live data (polled every 10s)
  GET  /api/main-activity         — main-agent recent tool-call activity
  GET  /api/timeline              — 30-day session-activity timeline
  GET  /api/cloud-cta/status      — cloud-sync CTA connected status
  POST /api/cloud-cta/send-otp    — cloud-sync CTA: send email OTP
  POST /api/cloud-cta/verify-otp  — cloud-sync CTA: verify code + store token
  GET  /api/prompt-errors         — openclaw:prompt-error events from sessions (GH#601)

Module-level helpers (``_gw_invoke``, ``_get_sessions``, ``_get_crons``,
``_get_memory_files``, ``_find_log_file``, ``_infer_provider_from_model``,
``_read_cloud_token``, ``_write_cloud_token``, ``get_local_ip``,
``SESSIONS_DIR``, ``MEMORY_DIR``, ``USER_NAME``) stay in ``dashboard.py``
and are reached via late ``import dashboard as _d``. Pure mechanical move
— zero behaviour change.
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request

bp_overview = Blueprint('overview', __name__)


@bp_overview.route("/api/channels")
def api_channels():
    """Return active input channels for the Flow diagram.

    Includes:
    - `tui` (always — the CLI is always available)
    - configured delivery channels from openclaw.json / gateway.yaml
    - `webchat` if recent activity in gateway.log (control UI counts as input)

    Previously fell back to a hardcoded ['telegram', 'signal', 'whatsapp']
    list when nothing was detected — which displayed fake channels for users
    who hadn't configured any. Removed.
    """
    KNOWN_CHANNELS = (
        "tui",
        "telegram",
        "signal",
        "whatsapp",
        "discord",
        "webchat",
        "imessage",
        "irc",
        "slack",
        "googlechat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    )
    configured = []

    def _add(name):
        n = name.lower()
        if n in KNOWN_CHANNELS and n not in configured:
            configured.append(n)

    # 1. Check gateway.yaml / gateway.yml (OpenClaw gateway config)
    yaml_candidates = [
        os.path.expanduser("~/.openclaw/gateway.yaml"),
        os.path.expanduser("~/.openclaw/gateway.yml"),
        os.path.expanduser("~/.clawdbot/gateway.yaml"),
        os.path.expanduser("~/.clawdbot/gateway.yml"),
    ]
    for yf in yaml_candidates:
        try:
            import yaml as _yaml

            with open(yf) as f:
                ydata = _yaml.safe_load(f)
            if not isinstance(ydata, dict):
                continue
            # channels: or plugins: section
            for section_key in ("channels", "plugins"):
                section = ydata.get(section_key, {})
                if isinstance(section, dict):
                    for name, conf in section.items():
                        if isinstance(conf, dict) and conf.get("enabled", True):
                            _add(name)
                        elif isinstance(conf, bool) and conf:
                            _add(name)
                elif isinstance(section, list):
                    for name in section:
                        _add(str(name))
            if configured:
                break
        except Exception:
            continue

    # 2. Check JSON config files (clawdbot/openclaw/moltbot)
    if not configured:
        config_files = [
            os.path.expanduser("~/.openclaw/openclaw.json"),
            os.path.expanduser("~/.clawdbot/openclaw.json"),
            os.path.expanduser("~/.clawdbot/clawdbot.json"),
            os.path.expanduser("~/.clawdbot/moltbot.json"),
        ]
        for cf in config_files:
            try:
                with open(cf) as f:
                    data = json.load(f)
                # Check plugins.entries for enabled channels
                plugins = data.get("plugins", {}).get("entries", {})
                for name, pconf in plugins.items():
                    if isinstance(pconf, dict) and pconf.get("enabled"):
                        _add(name)
                # Also check channels key
                channels = data.get("channels", {})
                if isinstance(channels, dict):
                    for name in channels:
                        _add(name)
                elif isinstance(channels, list):
                    for name in channels:
                        _add(str(name))
                if configured:
                    break
            except Exception:
                continue

    # Filter to channels that actually have data directories (proof of real usage)
    # Some channels (like imessage) use system paths, not openclaw dirs -- skip dir check for those
    DIR_EXEMPT_CHANNELS = {
        "imessage",
        "irc",
        "googlechat",
        "slack",
        "webchat",
        "bluebubbles",
        "matrix",
        "mattermost",
        "msteams",
        "line",
        "nostr",
        "twitch",
        "feishu",
        "synology-chat",
        "nextcloud-talk",
        "tlon",
        "zalo",
        "zalouser",
    }
    if configured:
        active_channels = []
        oc_dir = os.path.expanduser("~/.openclaw")
        cb_dir = os.path.expanduser("~/.clawdbot")
        for ch in configured:
            if ch in DIR_EXEMPT_CHANNELS:
                active_channels.append(ch)
            elif any(os.path.isdir(os.path.join(d, ch)) for d in [oc_dir, cb_dir]):
                active_channels.append(ch)
        if active_channels:
            configured = active_channels

    # TUI is always available (it's the CLI) — pin it to the front so the
    # Flow diagram reflects that the user can always reach the agent that way.
    if "tui" not in configured:
        configured.insert(0, "tui")

    # Surface webchat if the OpenClaw control-UI has recent activity. Looking
    # for "webchat connected" in the rolling gateway.log catches the case
    # where the user is using the OpenClaw control UI but hasn't configured
    # webchat as a formal channel.
    try:
        gw_log_paths = [
            os.path.expanduser("~/.openclaw/logs/gateway.log"),
            os.path.expanduser("~/.openclaw-dev/logs/gateway.log"),
        ]
        gw_log = next((p for p in gw_log_paths if os.path.isfile(p)), None)
        if gw_log:
            today = datetime.now().strftime("%Y-%m-%d")
            with open(gw_log) as _wf:
                for line in _wf:
                    if today in line and "webchat connected" in line:
                        if "webchat" not in configured:
                            configured.append("webchat")
                        break
    except Exception:
        pass

    return jsonify({"channels": configured})


@bp_overview.route("/api/overview")
def api_overview():
    import dashboard as _d

    # Try gateway API for sessions
    gw_sessions = _d._gw_invoke("sessions_list", {"limit": 50, "messageLimit": 0})
    if gw_sessions and "sessions" in gw_sessions:
        sessions = gw_sessions["sessions"]
    else:
        sessions = _d._get_sessions()
    main = next(
        (
            s
            for s in sessions
            if "subagent" not in (s.get("key", s.get("sessionId", "")).lower())
        ),
        sessions[0] if sessions else {},
    )

    crons = _d._get_crons()
    enabled = len([j for j in crons if j.get("enabled")])
    disabled = len(crons) - enabled

    mem_files = _d._get_memory_files()
    total_size = sum(f["size"] for f in mem_files)

    # System info
    system = []
    # 2s timeout on every subprocess: on slow/NFS-backed volumes df/free/uptime
    # can hang the request thread indefinitely, and /api/overview is on the
    # dashboard's hot path (fires every refresh). Better to show "--" than hang.
    try:
        disk = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = (
            "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        )
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])

    try:
        mem = (
            subprocess.run(["free", "-h"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[1]
            .split()
        )
        system.append(["RAM", f"{mem[2]} / {mem[1]}", ""])
    except Exception:
        system.append(["RAM", "--", ""])

    try:
        load = open("/proc/loadavg").read().split()[:3]
        system.append(["Load", " ".join(load), ""])
    except Exception:
        system.append(["Load", "--", ""])

    try:
        uptime = subprocess.run(
            ["uptime", "-p"], capture_output=True, text=True, timeout=2
        ).stdout.strip()
        system.append(["Uptime", uptime.replace("up ", ""), ""])
    except Exception:
        system.append(["Uptime", "--", ""])

    if sys.platform != "win32":
        try:
            gw = subprocess.run(
                ["pgrep", "-f", "moltbot"], capture_output=True, text=True, timeout=2
            )
            gw_running = gw.returncode == 0
        except Exception:
            gw_running = False
    else:
        gw_running = False
    system.append(
        [
            "Gateway",
            "Running" if gw_running else "Stopped",
            "green" if gw_running else "red",
        ]
    )

    # Infrastructure details for Flow tab
    infra = {
        "userName": _d.USER_NAME,
        "network": _d.get_local_ip(),
    }
    try:
        import platform

        uname = platform.uname()
        infra["machine"] = uname.node
        infra["runtime"] = f"Node.js - {uname.system} {uname.release.split('-')[0]}"
    except Exception:
        infra["machine"] = "Host"
        infra["runtime"] = "Runtime"

    try:
        disk_info = (
            subprocess.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip()
            .split("\n")[-1]
            .split()
        )
        infra["storage"] = f"{disk_info[1]} root"
    except Exception:
        infra["storage"] = "Disk"

    model_name = main.get("model") or "unknown"
    return jsonify(
        {
            "model": model_name,
            "provider": _d._infer_provider_from_model(model_name),
            "sessionCount": len(sessions),
            "sessions": len(sessions),  # alias for E2E compatibility
            "activeSessions": len([s for s in sessions if s.get("active")]),
            "mainSessionUpdated": main.get("updatedAt"),
            "mainTokens": main.get("totalTokens", 0),
            "contextWindow": main.get("contextTokens", 200000),
            "cronCount": len(crons),
            "cronEnabled": enabled,
            "cronDisabled": disabled,
            "memoryCount": len(mem_files),
            "memorySize": total_size,
            "system": system,
            "infra": infra,
        }
    )


@bp_overview.route("/api/main-activity")
def api_main_activity():
    """Return recent tool calls from the main (most recently modified) session."""
    import dashboard as _d

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(sessions_dir):
        return jsonify({"calls": [], "error": "sessions dir not found"})
    # Find the main session: largest recently-modified JSONL (main sessions accumulate far more data)
    candidates = []
    for f in os.listdir(sessions_dir):
        if not f.endswith(".jsonl"):
            continue
        fp = os.path.join(sessions_dir, f)
        try:
            st = os.stat(fp)
            # Only consider files modified in last 24h
            if time.time() - st.st_mtime < 86400:
                candidates.append((fp, st.st_size, st.st_mtime))
        except Exception:
            continue
    if not candidates:
        return jsonify({"calls": []})
    # Pick most recently modified file (active main session)
    candidates.sort(key=lambda x: x[2], reverse=True)
    best = candidates[0][0]
    best_mt = candidates[0][2]
    if not best:
        return jsonify({"calls": []})
    # Read last ~200 lines to find tool calls
    try:
        with open(best, "rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            chunk = min(size, 512000)
            fh.seek(max(0, size - chunk))
            tail = fh.read().decode("utf-8", errors="replace")
        lines = tail.strip().split("\n")
    except Exception:
        return jsonify({"calls": []})
    tool_icons = {
        "exec": "🔧",
        "Read": "📖",
        "read": "📖",
        "Edit": "✏️",
        "edit": "✏️",
        "Write": "✏️",
        "write": "✏️",
        "web_search": "🌐",
        "web_fetch": "🌐",
        "browser": "🖥️",
        "message": "💬",
        "tts": "🔊",
        "image": "🖼️",
        "canvas": "🎨",
        "nodes": "📱",
        "process": "🔧",
    }
    calls = []
    for line in lines:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        msg = obj.get("message", obj)
        ts = obj.get("timestamp") or msg.get("timestamp")
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for item in content:
            if item.get("type") != "toolCall":
                continue
            name = item.get("name", "?")
            args = item.get("arguments", {}) or {}
            # Build summary
            if name == "exec":
                summary = args.get("command", "")[:60]
            elif name in ("Read", "read"):
                summary = (args.get("file_path") or args.get("path") or "")[:60]
            elif name in ("Edit", "edit"):
                summary = (args.get("file_path") or args.get("path") or "")[:60]
            elif name in ("Write", "write"):
                summary = (args.get("file_path") or args.get("path") or "")[:60]
            elif name == "web_search":
                summary = args.get("query", "")[:60]
            elif name == "web_fetch":
                summary = args.get("url", "")[:60]
            elif name == "browser":
                summary = args.get("action", "")
            elif name == "message":
                action = args.get("action", "")
                target = args.get("target") or args.get("to") or args.get("channel", "")
                msg = (args.get("message") or "")[:40]
                summary = (
                    f"{action} -> {target}: {msg}" if msg else f"{action} -> {target}"
                )
                summary = summary[:60]
            elif name == "tts":
                summary = args.get("text", "")[:60]
            elif name == "process":
                action = args.get("action", "")
                sid = args.get("sessionId", "")[:15]
                summary = f"{action}: {sid}" if sid else action
            elif name == "sessions_spawn":
                task = (args.get("task", "") or args.get("label", ""))[:50]
                summary = task
            elif name == "sessions_send":
                label = args.get("label") or args.get("sessionKey", "")
                summary = f"-> {label}"[:60]
            elif name == "cron":
                action = args.get("action", "")
                jid = args.get("jobId", "")[:10]
                summary = f"{action} {jid}".strip()
            elif name == "gateway":
                summary = args.get("action", "")
            elif name == "session_status":
                summary = "checking status"
            elif name == "image":
                summary = (args.get("prompt", "") or args.get("image", ""))[:60]
            else:
                # Clean up dict display
                s = str(args)
                if len(s) > 60:
                    s = s[:57] + "..."
                summary = s
            icon = tool_icons.get(name, "⚙️")
            calls.append({"ts": ts, "name": name, "icon": icon, "summary": summary})
    # Return last 20
    calls = calls[-20:]
    return jsonify(
        {"calls": calls, "sessionFile": os.path.basename(best), "lastModified": best_mt}
    )


@bp_overview.route("/api/timeline")
def api_timeline():
    """Return available dates with activity counts for time travel."""
    import dashboard as _d

    now = datetime.now()
    days = []
    for i in range(30, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        log_file = _d._find_log_file(ds)
        count = 0
        hours = {}
        if log_file:
            try:
                with open(log_file) as f:
                    for line in f:
                        count += 1
                        try:
                            obj = json.loads(line.strip())
                            ts = obj.get("time") or ""
                            if "T" in ts:
                                h = int(ts.split("T")[1][:2])
                                hours[h] = hours.get(h, 0) + 1
                        except Exception:
                            pass
            except Exception:
                pass
        # Also check memory files for that date
        mem_file = os.path.join(_d.MEMORY_DIR, f"{ds}.md") if _d.MEMORY_DIR else None
        has_memory = mem_file and os.path.exists(mem_file)
        if count > 0 or has_memory:
            days.append(
                {
                    "date": ds,
                    "label": d.strftime("%a %b %d"),
                    "events": count,
                    "hasMemory": has_memory,
                    "hours": hours,
                }
            )
    return jsonify({"days": days, "today": now.strftime("%Y-%m-%d")})


@bp_overview.route("/api/cloud-cta/status")
def cloud_cta_status():
    import dashboard as _d

    token = _d._read_cloud_token()
    return jsonify({"connected": bool(token)})


@bp_overview.route(
    "/api/cloud-proxy/<path:cloud_path>",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
)
def cloud_proxy(cloud_path):
    """Forward an authenticated request to https://app.clawmetry.com/<path>.

    Used by the Alerts tab (and anything else that needs cloud-side data) so
    the cm_ token never has to leave the OSS dashboard. The token is read from
    ~/.openclaw/openclaw.json.cloudToken and injected as Bearer.

    Returns 401 if no cloud token is configured (UI shows the "Sign up for
    Cloud" CTA in that case).
    """
    import dashboard as _d
    import urllib.error
    import urllib.request

    token = _d._read_cloud_token()
    if not token:
        return jsonify({"error": "cloud_not_connected"}), 401

    url = "https://app.clawmetry.com/" + cloud_path
    if request.query_string:
        url += "?" + request.query_string.decode("utf-8", errors="replace")

    body = None
    if request.method in ("POST", "PUT", "PATCH"):
        body = request.get_data() or b""

    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": request.headers.get("Content-Type", "application/json"),
        "Accept": "application/json",
    }

    req = urllib.request.Request(url, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            payload = resp.read()
            ct = resp.headers.get("Content-Type", "application/json")
            return (payload, resp.status, {"Content-Type": ct})
    except urllib.error.HTTPError as e:
        # Pass through 4xx/5xx with body so the UI can read 402 upgrade_required etc.
        return (e.read() or b"{}", e.code,
                {"Content-Type": e.headers.get("Content-Type", "application/json")})
    except Exception as e:
        return jsonify({"error": "proxy_failed", "detail": str(e)[:200]}), 502


@bp_overview.route("/api/cloud-cta/send-otp", methods=["POST"])
def cloud_cta_send_otp():
    import urllib.request as _ur
    import json as _jr

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    if not email or "@" not in email:
        return jsonify({"ok": False, "error": "Invalid email"}), 400
    try:
        _body = _jr.dumps({"email": email, "source": "dashboard"}).encode()
        _req = _ur.Request(
            "https://app.clawmetry.com/api/otp/send",
            data=_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(_req, timeout=10) as _resp:
            result = _jr.loads(_resp.read())
            return jsonify({"ok": True, "error": result.get("error")})
    except Exception as _ex:
        _sc = getattr(getattr(_ex, "code", None), "__class__", type(_ex)).__name__
        try:
            _eb = _jr.loads(_ex.read()) if hasattr(_ex, "read") else {}
        except Exception:
            _eb = {}
        return jsonify(
            {"ok": False, "error": _eb.get("error", "Could not reach ClawMetry server")}
        ), 502


@bp_overview.route("/api/cloud-cta/verify-otp", methods=["POST"])
def cloud_cta_verify_otp():
    import dashboard as _d
    import urllib.request as _ur
    import json as _jr

    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip()
    code = (data.get("code") or "").strip()
    if not email or not code:
        return jsonify({"ok": False, "error": "Missing email or code"}), 400
    try:
        _body = _jr.dumps({"email": email, "code": code}).encode()
        _req = _ur.Request(
            "https://app.clawmetry.com/api/otp/verify",
            data=_body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(_req, timeout=10) as _resp:
            result = _jr.loads(_resp.read())
            if result.get("token"):
                _d._write_cloud_token(result["token"])
                return jsonify({"ok": True, "token": result["token"]})
            return jsonify({"ok": False, "error": result.get("error", "Invalid code")})
    except Exception as _ex:
        try:
            _eb = _jr.loads(_ex.read()) if hasattr(_ex, "read") else {}
        except Exception:
            _eb = {}
        return jsonify({"ok": False, "error": _eb.get("error", "Invalid code")}), 502


@bp_overview.route("/api/prompt-errors")
def api_prompt_errors():
    """Return openclaw:prompt-error events from session JSONL files.

    Query params:
        since (int): Unix timestamp (ms) — only return errors newer than this
        limit (int): Max errors to return (default 20)

    Returns JSON array of prompt errors:
        {
            "timestamp": "2026-04-23T10:31:17.336Z",
            "runId": "...",
            "sessionId": "...",
            "provider": "ollama",
            "model": "kimi-k2.5:cloud",
            "api": "ollama",
            "error": "aborted"
        }
    """
    import dashboard as _d

    since = request.args.get("since", "0")
    try:
        since_ms = int(since)
    except Exception:
        since_ms = 0

    limit = request.args.get("limit", "20")
    try:
        limit = int(limit)
    except Exception:
        limit = 20

    sessions_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    errors = []

    if not os.path.isdir(sessions_dir):
        return jsonify({"errors": []})

    # Scan session JSONL files for prompt-error events
    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        fp = os.path.join(sessions_dir, fname)
        try:
            with open(fp, "rb") as fh:
                # Read last chunk to avoid loading huge files
                fh.seek(0, 2)
                size = fh.tell()
                chunk_size = min(size, 512000)  # Last 512KB
                fh.seek(max(0, size - chunk_size))
                data = fh.read().decode("utf-8", errors="replace")

            for line in data.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue

                # Check for prompt-error custom events
                if obj.get("type") != "custom":
                    continue
                if obj.get("customType") != "openclaw:prompt-error":
                    continue

                pdata = obj.get("data", {})
                ts = pdata.get("timestamp", 0)

                # Filter by since
                if since_ms and ts <= since_ms:
                    continue

                errors.append({
                    "timestamp": obj.get("timestamp", ""),
                    "runId": pdata.get("runId", ""),
                    "sessionId": pdata.get("sessionId", ""),
                    "provider": pdata.get("provider", ""),
                    "model": pdata.get("model", ""),
                    "api": pdata.get("api", ""),
                    "error": pdata.get("error", ""),
                })
        except Exception:
            continue

    # Sort by timestamp descending and limit
    errors.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    errors = errors[:limit]

    return jsonify({"errors": errors})
