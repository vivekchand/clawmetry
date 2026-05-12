"""
routes/overview.py — Main-dashboard endpoints.

Extracted from dashboard.py as Phase 5.8 of the incremental modularisation.
Owns the 6 routes registered on ``bp_overview``:

  GET  /api/channels              — active input channels for Flow diagram
  GET  /api/overview              — top-bar live data (polled every 10s)
  GET  /api/timeline              — 30-day session-activity timeline
  GET  /api/cloud-cta/status      — cloud-sync CTA connected status
  POST /api/cloud-cta/send-otp    — cloud-sync CTA: send email OTP
  POST /api/cloud-cta/verify-otp  — cloud-sync CTA: verify code + store token

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


def _try_local_store_overview():
    """Epic #964: opt-in local-store fast path for /api/overview.

    Builds the same response shape as the legacy gateway-backed handler from
    DuckDB: session counts (from query_sessions), most-recently-active session
    metadata (model, tokens, updatedAt) — all derivable from
    ``query_sessions`` + ``query_aggregates`` + ``query_events``.

    System-info and infra blocks still come from local subprocesses; the fast
    path only replaces the gateway-dependent fields (model, sessionCount,
    activeSessions, mainSessionUpdated, mainTokens). Cron + memory counts
    intentionally stay on their existing helpers (they hit the filesystem
    directly and are already <5ms).

    Returns ``None`` to defer to the legacy handler if:
      - the local_store module isn't importable
      - the sessions table is empty (fresh install / non-OpenClaw user)
      - any unexpected error happens (we'd rather degrade than 500)
    """
    import subprocess as _sub
    import sys as _sys
    # Issue #1088: cross-process fast path. Try the daemon HTTP proxy first
    # (covers the standard launchd/systemd install where DuckDB's writer lock
    # blocks the dashboard from opening directly), then fall back to direct
    # open for tests + dev mode.
    sess_rows = None
    try:
        from routes.local_query import local_store_via_daemon
        sess_rows = local_store_via_daemon("query_sessions_table", limit=200)
    except Exception:
        sess_rows = None
    if sess_rows is None:
        try:
            from clawmetry import local_store
            sess_rows = local_store.get_store().query_sessions_table(limit=200)
        except Exception:
            return None
    if not sess_rows:
        return None

    # Build a normalized view of sessions.
    sessions = []
    for r in sess_rows:
        meta = r.get("metadata") or {}
        sessions.append({
            "session_id": r.get("session_id"),
            "agent_id": r.get("agent_id"),
            "title": r.get("title") or "",
            "started_at": r.get("started_at") or "",
            "last_active_at": r.get("last_active_at") or "",
            "ended_at": r.get("ended_at") or "",
            "status": (r.get("status") or "").lower(),
            "total_tokens": int(r.get("total_tokens") or 0),
            "cost_usd": float(r.get("cost_usd") or 0.0),
            "message_count": int(r.get("message_count") or 0),
            "model": meta.get("model"),
        })

    # Pick the most recent non-subagent session as the "main" session.
    def _is_subagent(s):
        sid = (s.get("session_id") or "").lower()
        return "subagent" in sid or "sub-agent" in sid
    main = next((s for s in sessions if not _is_subagent(s)), sessions[0])

    # Active = status=='active' (DuckDB persists status as a free-form string;
    # 'active' is what sync.py writes for in-progress sessions).
    active_count = sum(1 for s in sessions if s["status"] == "active")

    # Model: prefer metadata.model on the main session; fall back to the most
    # recently observed model across events.
    model_name = main.get("model") or "unknown"
    if model_name == "unknown":
        evs = None
        try:
            from routes.local_query import local_store_via_daemon
            evs = local_store_via_daemon("query_events", limit=20)
        except Exception:
            evs = None
        if evs is None:
            try:
                from clawmetry import local_store
                evs = local_store.get_store().query_events(limit=20)
            except Exception:
                evs = []
        for e in (evs or []):
            m = e.get("model")
            if m:
                model_name = m
                break

    # Pull the latest cron + memory totals using the existing dashboard
    # helpers. They're already filesystem-backed and fast — and they read
    # from canonical sources (the gateway / .openclaw memory dir) that the
    # local store doesn't replicate. We still want the fast path to be 100%
    # local-only, so we wrap them in try/except so a missing FS doesn't break
    # the response.
    import dashboard as _d
    try:
        crons = _d._get_crons()
    except Exception:
        crons = []
    enabled = len([j for j in crons if j.get("enabled")])
    disabled = len(crons) - enabled
    try:
        mem_files = _d._get_memory_files()
    except Exception:
        mem_files = []
    total_size = sum(f.get("size", 0) for f in mem_files)

    # System info — copied verbatim from the legacy handler so the response
    # shape matches byte-for-byte. Each subprocess has a 2s timeout so a slow
    # df/free/uptime can't hang the request thread.
    system = []
    try:
        disk = (
            _sub.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[-1].split()
        )
        disk_pct = int(disk[4].replace("%", "")) if len(disk) > 4 else 0
        disk_color = "green" if disk_pct < 80 else ("yellow" if disk_pct < 90 else "red")
        system.append(["Disk /", f"{disk[2]} / {disk[1]} ({disk[4]})", disk_color])
    except Exception:
        system.append(["Disk /", "--", ""])

    try:
        mem = (
            _sub.run(["free", "-h"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[1].split()
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
        uptime = _sub.run(
            ["uptime", "-p"], capture_output=True, text=True, timeout=2
        ).stdout.strip()
        system.append(["Uptime", uptime.replace("up ", ""), ""])
    except Exception:
        system.append(["Uptime", "--", ""])

    if _sys.platform != "win32":
        try:
            gw = _sub.run(
                ["pgrep", "-f", "moltbot"], capture_output=True, text=True, timeout=2
            )
            gw_running = gw.returncode == 0
        except Exception:
            gw_running = False
    else:
        gw_running = False
    system.append([
        "Gateway",
        "Running" if gw_running else "Stopped",
        "green" if gw_running else "red",
    ])

    # Infra block — same shape as legacy.
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
            _sub.run(["df", "-h", "/"], capture_output=True, text=True, timeout=2)
            .stdout.strip().split("\n")[-1].split()
        )
        infra["storage"] = f"{disk_info[1]} root"
    except Exception:
        infra["storage"] = "Disk"

    return {
        "model": model_name,
        "provider": _d._infer_provider_from_model(model_name),
        "sessionCount": len(sessions),
        "sessions": len(sessions),  # alias for E2E compatibility
        "activeSessions": active_count,
        "mainSessionUpdated": main.get("last_active_at") or main.get("started_at"),
        "mainTokens": main.get("total_tokens", 0),
        "contextWindow": 200000,
        "cronCount": len(crons),
        "cronEnabled": enabled,
        "cronDisabled": disabled,
        "memoryCount": len(mem_files),
        "memorySize": total_size,
        "system": system,
        "infra": infra,
        "_source": "local_store",
    }


@bp_overview.route("/api/overview")
def api_overview():
    import dashboard as _d

    # Epic #964: opt-in local-store fast path. When CLAWMETRY_LOCAL_STORE_READ=1
    # AND the local sessions table has rows, serve directly from DuckDB. Falls
    # through to gateway/JSONL otherwise (zero-change default).
    if os.environ.get("CLAWMETRY_LOCAL_STORE_READ") == "1":
        fast = _try_local_store_overview()
        if fast is not None:
            return jsonify(fast)

    # Try gateway API for sessions
    gw_sessions = _d._gw_invoke("sessions_list", {"limit": 20, "messageLimit": 0})
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


def _try_local_store_timeline():
    """Epic #964: opt-in local-store fast path for /api/timeline.

    The legacy handler walks 31 daily JSONL log files (one per day for the
    last 30 days), parsing every line to count events and bucket by hour.
    On busy nodes that's hundreds of MB of disk I/O on a hot path.

    ``query_aggregates`` is the perfect fit: DuckDB pre-buckets events by day
    on the columnar layout in single-digit ms even at 100k+ events. We then
    re-derive the per-hour distribution by querying ``query_events`` once per
    day with a tight window — only days that already showed activity in the
    aggregates pass actually get scanned.

    Returns ``None`` to defer to the JSONL fallback if:
      - the local_store module isn't importable
      - query_aggregates returns empty (no events seen yet)
      - any unexpected error happens
    """
    try:
        from clawmetry import local_store
        store = local_store.get_store()
    except Exception:
        return None
    now = datetime.now()
    cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d") + "T00:00:00"
    try:
        rows = store.query_aggregates(since=cutoff)
    except Exception:
        return None
    if not rows:
        return None

    # Roll up per-day counts (sum across agent_ids).
    day_counts = {}
    for r in rows:
        d = r.get("day")
        if not d:
            continue
        day_counts[d] = day_counts.get(d, 0) + int(r.get("event_count", 0) or 0)

    # Build the per-hour distribution. We pull events once for each day that
    # had activity using the (since, until) window and bucket client-side.
    days = []
    import dashboard as _d
    mem_dir = getattr(_d, "MEMORY_DIR", None)
    for i in range(30, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        count = day_counts.get(ds, 0)
        hours = {}
        if count > 0:
            try:
                ev_rows = store.query_events(
                    since=ds + "T00:00:00",
                    until=ds + "T23:59:59",
                    limit=10000,
                )
                for ev in ev_rows:
                    ts = ev.get("ts") or ""
                    if "T" in ts:
                        try:
                            h = int(ts.split("T")[1][:2])
                            hours[h] = hours.get(h, 0) + 1
                        except Exception:
                            pass
            except Exception:
                pass
        mem_file = os.path.join(mem_dir, f"{ds}.md") if mem_dir else None
        has_memory = bool(mem_file and os.path.exists(mem_file))
        if count > 0 or has_memory:
            days.append({
                "date": ds,
                "label": d.strftime("%a %b %d"),
                "events": count,
                "hasMemory": has_memory,
                "hours": hours,
            })
    return {
        "days": days,
        "today": now.strftime("%Y-%m-%d"),
        "_source": "local_store",
    }


@bp_overview.route("/api/timeline")
def api_timeline():
    """Return available dates with activity counts for time travel."""
    import dashboard as _d

    # Epic #964: opt-in local-store fast path. When CLAWMETRY_LOCAL_STORE_READ=1
    # AND query_aggregates returns rows, serve from DuckDB. Falls through to the
    # 30-day JSONL scan otherwise (zero-change default).
    if os.environ.get("CLAWMETRY_LOCAL_STORE_READ") == "1":
        fast = _try_local_store_timeline()
        if fast is not None:
            return jsonify(fast)

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


def _try_local_store_prompt_errors(since_iso):
    """Fast path for /api/prompt-errors. Reads ``openclaw:prompt-error``
    events from DuckDB instead of scanning the 20 most-recent JSONL files.

    Issue #1088: tries the daemon HTTP proxy FIRST (cross-process safe under
    the standard install where the daemon owns the writer lock), then falls
    back to a direct ``get_store()`` open for single-process boots (tests +
    dev mode).

    Returns ``None`` to defer to the JSONL scan if:
      - neither path can reach the local store
      - the events table is empty / no prompt-error rows
      - any unexpected error happens (we'd rather degrade than 500)
    """
    def _fetch(event_type):
        # Cross-process: ask the daemon first.
        try:
            from routes.local_query import local_store_via_daemon
            r = local_store_via_daemon(
                "query_events",
                event_type=event_type,
                since=since_iso,
                limit=200,
            )
            if r is not None:
                return r
        except Exception:
            pass
        # Single-process fallback.
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            return store.query_events(
                event_type=event_type,
                since=since_iso,
                limit=200,
            )
        except Exception:
            return None

    # Two event_type spellings have been seen in the wild — the canonical
    # ``openclaw:prompt-error`` and the bare ``prompt-error`` from older
    # ingest paths. Try both.
    rows = _fetch("openclaw:prompt-error")
    if not rows:
        rows = _fetch("prompt-error")
    if not rows:
        return None
    errors = []
    for ev in rows:
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        errors.append({
            "ts": ev.get("ts"),
            "runId": data.get("runId"),
            "sessionId": ev.get("session_id") or data.get("sessionId"),
            "provider": data.get("provider"),
            "model": ev.get("model") or data.get("model"),
            "api": data.get("api"),
            "error": data.get("error"),
        })
    errors.sort(key=lambda e: e.get("ts") or "", reverse=True)
    errors = errors[:50]
    return {"errors": errors, "count": len(errors), "_source": "local_store"}


@bp_overview.route("/api/prompt-errors")
def api_prompt_errors():
    """Return recent openclaw:prompt-error events from session JSONL files.

    Scans the 20 most-recently-modified session files so the response stays
    fast regardless of how many sessions exist.  Supports ?since=<ISO8601>
    for incremental polling by the client.
    """
    import dashboard as _d

    since_raw = request.args.get("since")
    since_ts = None
    if since_raw:
        try:
            since_ts = datetime.fromisoformat(since_raw.replace("Z", "+00:00"))
        except Exception:
            pass

    # Epic #964 — opt-in DuckDB fast path. Falls through on miss.
    if os.environ.get("CLAWMETRY_LOCAL_STORE_READ") == "1":
        fast = _try_local_store_prompt_errors(since_raw)
        if fast is not None:
            return jsonify(fast)

    session_dir = _d.SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    if not os.path.isdir(session_dir):
        return jsonify({"errors": [], "count": 0})

    try:
        all_files = [
            f for f in os.listdir(session_dir) if f.endswith(".jsonl")
        ]
        # Scan most-recently-modified first so we surface fresh errors quickly.
        all_files.sort(
            key=lambda f: os.path.getmtime(os.path.join(session_dir, f)),
            reverse=True,
        )
        files = all_files[:20]
    except Exception:
        return jsonify({"errors": [], "count": 0})

    errors = []
    for fname in files:
        fpath = os.path.join(session_dir, fname)
        try:
            with open(fpath, "r") as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    if obj.get("customType") != "openclaw:prompt-error":
                        continue

                    ts_raw = (
                        obj.get("timestamp")
                        or obj.get("time")
                        or obj.get("created_at")
                    )
                    if since_ts and ts_raw:
                        try:
                            ev_ts = datetime.fromisoformat(
                                str(ts_raw).replace("Z", "+00:00")
                            )
                            if ev_ts < since_ts:
                                continue
                        except Exception:
                            pass

                    # Fields may be at the top level or nested under "data".
                    data = obj.get("data") if isinstance(obj.get("data"), dict) else obj
                    errors.append(
                        {
                            "ts": ts_raw,
                            "runId": data.get("runId") or obj.get("runId"),
                            "sessionId": data.get("sessionId") or obj.get("sessionId"),
                            "provider": data.get("provider") or obj.get("provider"),
                            "model": data.get("model") or obj.get("model"),
                            "api": data.get("api") or obj.get("api"),
                            "error": data.get("error") or obj.get("error"),
                        }
                    )
        except Exception:
            continue

    errors.sort(key=lambda e: e.get("ts") or "", reverse=True)
    errors = errors[:50]
    return jsonify({"errors": errors, "count": len(errors)})


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
