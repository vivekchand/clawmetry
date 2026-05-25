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
  GET  /api/agent-presence        — is any underlying agent (OpenClaw / NemoClaw) installed?
  GET  /api/rate-limits           — rolling 1m/1h API rate-limit utilisation
  GET  /api/health-stream         — SSE auto-refresh of health checks (30s)
  GET  /api/sandbox-status        — sandbox / inference / security posture
  GET  /api/loop-detection        — scan recent sessions for repeated tool-call loops (#849)
  GET  /api/gateway-health        — OpenClaw gateway process vitals (#852)

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
import re
import socket
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone

from flask import Blueprint, Response, jsonify, request
from clawmetry.config import is_local_store_read_enabled

bp_health = Blueprint('health', __name__)


# ---------------------------------------------------------------------------
# Daemon-log error-rate parser (PRD #1133 layer 4 — read side only)
#
# Reads the tail of ``~/.clawmetry/sync.log`` and counts ERROR-level lines in
# rolling 5-min and 1-hour windows so the System Health card can warn the
# user when the cloud-sync daemon is silently failing (e.g. the
# ``ALERTS_EVAL_INTERVAL_SEC`` NameError that was logging 4×/min on every
# install since 0.12.179 with no in-product surface).
#
# Pure helpers — no Flask globals — so they can be unit-tested without a
# running server. The endpoint that consumes these lives below in
# ``api_system_health``.
# ---------------------------------------------------------------------------

# Lines look like:
#   2026-05-13 09:33:52,180 [clawmetry-sync] ERROR Sync cycle error: ...
# Capture the timestamp + the message body (everything after the level).
_DAEMON_LOG_LINE_RE = re.compile(
    r"^(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:[,.]\d+)?\s+"
    r"\[[^\]]+\]\s+(?P<level>[A-Z]+)\s+(?P<msg>.*)$"
)

# How many lines to read from the tail of the log. Safe upper bound: even at
# 60 ERROR lines/min (well above the PRD trigger of 10/min) a 1-hour window
# only sees ~3,600 lines, and we cap at 1,000 to stay cheap on slower disks.
DAEMON_LOG_TAIL_LINES = 1000


def _default_daemon_log_path():
    """Return the canonical sync.log path. Honours ``CLAWMETRY_HOME`` for tests."""
    home = os.environ.get("CLAWMETRY_HOME") or os.path.expanduser("~/.clawmetry")
    return os.path.join(home, "sync.log")


def _ls_call(method_name, **kwargs):
    """Cross-process LocalStore call with single-process fallback.

    Mirror of ``routes/crons.py:_ls_call``. Issue #1256: the dashboard's
    direct ``get_store().query_*`` opens raise ``IOException: Could not
    set lock`` on the standard install (daemon owns the writer lock), so
    we route through the daemon's HTTP proxy first and only fall back to
    a direct open for single-process boots (tests + dev mode). Returns
    ``None`` on miss so callers can defer to the legacy gateway path.
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


def _parse_iso_to_epoch(ts):
    """Best-effort ISO-8601 / numeric → epoch seconds. Returns 0 on any failure."""
    if not ts:
        return 0
    if isinstance(ts, (int, float)):
        # Heuristic: values >1e12 are ms, otherwise seconds.
        return float(ts) / 1000.0 if ts > 1e12 else float(ts)
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0
    return 0


def _tail_lines(path, n=DAEMON_LOG_TAIL_LINES):
    """Return the last ``n`` lines of ``path`` (or [] if missing/unreadable).

    Uses a bounded read from the end of the file so we never load multi-MB
    logs into memory. Falls back to a full read for tiny files.
    """
    try:
        size = os.path.getsize(path)
    except OSError:
        return []
    # Estimate ~256 bytes/line average for our log format; cap at 512 KB.
    read_bytes = min(size, max(256 * n, 64 * 1024), 512 * 1024)
    try:
        with open(path, "rb") as f:
            if size > read_bytes:
                f.seek(size - read_bytes)
                # Drop the partial first line so we never split mid-record.
                f.readline()
            data = f.read()
    except OSError:
        return []
    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        return []
    lines = text.splitlines()
    return lines[-n:] if len(lines) > n else lines


def _parse_daemon_log_line(line):
    """Return ``(ts_epoch, level, message)`` or ``None`` if the line is non-conforming.

    Timestamps in the log are local-time without TZ info; we treat them as
    naive local time (which matches how Python's ``logging`` module writes
    them). For window arithmetic we convert via ``mktime``.
    """
    m = _DAEMON_LOG_LINE_RE.match(line)
    if not m:
        return None
    try:
        dt = datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S")
        ts_epoch = time.mktime(dt.timetuple())
    except (ValueError, OverflowError):
        return None
    return ts_epoch, m.group("level"), m.group("msg")


def _status_from_counts(errors_last_5min: int) -> str:
    """Compute status pill from 5-min error count. PR #1139 thresholds."""
    if errors_last_5min > 30:
        return "broken"
    if errors_last_5min > 0:
        return "degraded"
    return "healthy"


def _try_local_store_daemon_health(now_ts: float, log_path: str):
    """DuckDB-first path: query ``events`` for ``daemon.error`` rows in the
    last hour and aggregate the same fields the log parser produces.

    Returns the summary dict on success, or ``None`` if the local store is
    unreachable / has zero rows in the window (so the caller can fall back
    to log-tail parsing).
    """
    cutoff_1h_iso = datetime.fromtimestamp(
        now_ts - 60 * 60, tz=timezone.utc
    ).isoformat()
    cutoff_5m_ts = now_ts - 5 * 60

    rows = None
    # Cross-process safe path (daemon owns the writer lock under the
    # standard install — direct opens fail). Same pattern as
    # ``_try_local_store_heatmap``.
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon(
            "query_events",
            event_type="daemon.error",
            agent_id="clawmetry-daemon",
            since=cutoff_1h_iso,
            limit=5000,
        )
    except Exception:
        rows = None
    if rows is None:
        # Single-process fallback (tests / dev mode).
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(
                event_type="daemon.error",
                agent_id="clawmetry-daemon",
                since=cutoff_1h_iso,
                limit=5000,
            )
        except Exception:
            return None
    if not rows:
        return None

    errors_5m = 0
    errors_1h = 0
    last_err_ts = None
    last_err_msg = None
    for ev in rows:
        ts = ev.get("ts")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        ev_ts = dt.timestamp()
        errors_1h += 1
        if ev_ts >= cutoff_5m_ts:
            errors_5m += 1
        if last_err_ts is None or ev_ts >= last_err_ts:
            last_err_ts = ev_ts
            data = ev.get("data") or {}
            if isinstance(data, dict):
                last_err_msg = data.get("message") or None
            elif isinstance(data, str):
                last_err_msg = data

    summary = {
        "log_path": log_path,
        "errors_last_5min": errors_5m,
        "errors_last_1h": errors_1h,
        "last_error_message": (last_err_msg or "")[:500] if last_err_msg else None,
        "last_error_ts": (
            datetime.fromtimestamp(last_err_ts, tz=timezone.utc).isoformat()
            if last_err_ts is not None
            else None
        ),
        "status": _status_from_counts(errors_5m),
        "log_present": os.path.exists(log_path),
        "_source": "local_store",
    }
    return summary


def _compute_daemon_health_from_log(log_path: str, now_ts: float):
    """Legacy log-tail parser. Retained as a fallback for fresh installs
    that don't yet have ``daemon.error`` rows in DuckDB (pre-this-PR data
    or first-boot before the handler fires)."""
    summary = {
        "log_path": log_path,
        "errors_last_5min": 0,
        "errors_last_1h": 0,
        "last_error_message": None,
        "last_error_ts": None,
        "status": "healthy",
        "log_present": os.path.exists(log_path),
        "_source": "sync_log",
    }
    if not summary["log_present"]:
        return summary

    cutoff_5m = now_ts - 5 * 60
    cutoff_1h = now_ts - 60 * 60
    last_err_ts = None
    last_err_msg = None
    for line in _tail_lines(log_path):
        parsed = _parse_daemon_log_line(line)
        if not parsed:
            continue
        ts_epoch, level, msg = parsed
        if level != "ERROR":
            continue
        if ts_epoch >= cutoff_1h:
            summary["errors_last_1h"] += 1
        if ts_epoch >= cutoff_5m:
            summary["errors_last_5min"] += 1
        if last_err_ts is None or ts_epoch >= last_err_ts:
            last_err_ts = ts_epoch
            last_err_msg = msg

    if last_err_ts is not None:
        summary["last_error_ts"] = (
            datetime.fromtimestamp(last_err_ts, tz=timezone.utc).isoformat()
        )
        summary["last_error_message"] = (last_err_msg or "")[:500]

    summary["status"] = _status_from_counts(summary["errors_last_5min"])
    return summary


def compute_daemon_health(log_path=None, now=None):
    """Return a daemon health summary dict, sourced from DuckDB first.

    Returns the structure documented in PRD #1133 layer 4:

        {
            "log_path": "<absolute path>",
            "errors_last_5min": int,
            "errors_last_1h": int,
            "last_error_message": str | None,
            "last_error_ts": ISO-8601 str | None,
            "status": "healthy" | "degraded" | "broken",
            "log_present": bool,
            "_source": "local_store" | "sync_log",
        }

    Status thresholds (per PRD): >30 errors in 5 min → ``broken``,
    >0 → ``degraded``, else ``healthy``. Missing/empty log + zero DuckDB
    rows → ``healthy`` so a fresh install doesn't flash red.

    Source order:
      1. DuckDB ``events`` table (event_type='daemon.error') — populated
         by the daemon-side handler in ``clawmetry/sync.py``. This is the
         DuckDB-first canonical path.
      2. ``~/.clawmetry/sync.log`` tail-parser — fallback for fresh
         installs that don't yet have ``daemon.error`` rows but DO have
         pre-existing ERROR lines in the log file.
    """
    path = log_path or _default_daemon_log_path()
    now_ts = now if now is not None else time.time()

    # DuckDB-first.
    duckdb_summary = _try_local_store_daemon_health(now_ts, path)
    if duckdb_summary is not None:
        return duckdb_summary

    # Fallback: log-tail parser (pre-#1133-layer-4 behavior).
    return _compute_daemon_health_from_log(path, now_ts)


# ---------------------------------------------------------------------------
# Gateway process health (#852).
#
# OpenClaw's gateway is a separate process listening on :18789. We already
# socket-check the port from ``/api/system-health`` — this surface adds
# process-level vitals (RSS, CPU, uptime) so the user can spot the slow
# memory-bloat-then-crash pattern (~600 MB → ~945 MB OOM) before the gateway
# dies. ``psutil`` is preferred when available; otherwise we fall back to a
# bounded ``ps`` invocation so we don't add a hard dependency for OSS installs
# that don't ship psutil.
#
# Pure helpers — no Flask globals — so they're unit-testable without a server.
# ---------------------------------------------------------------------------

# Memory bloat threshold. OpenClaw gateway has been observed to crash around
# 945 MB; 900 MB gives us a ~50 MB cushion to surface "critical" before OOM.
# warning kicks in at 75% of this (= 675 MB).
GATEWAY_MEMORY_THRESHOLD_MB = 900
GATEWAY_MEMORY_WARNING_RATIO = 0.75


def _default_gateway_pid_path():
    """Canonical path to OpenClaw's gateway PID file.

    Honours ``OPENCLAW_HOME`` so multi-workspace setups + tests can override.
    """
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    return os.path.join(home, "gateway", "gateway.pid")


def _read_gateway_pid(pid_path=None):
    """Return the gateway PID as an int, or ``None`` if missing/unreadable.

    The OpenClaw gateway writes its PID to ``~/.openclaw/gateway/gateway.pid``
    when it starts. We treat any unreadable/garbage file as "no gateway"
    rather than crashing — same graceful-degrade contract as the rest of
    ``routes/health.py``.
    """
    path = pid_path or _default_gateway_pid_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read().strip()
    except OSError:
        return None
    if not raw:
        return None
    # Some daemons write "<pid>\n<extra metadata>" — take just the first token.
    first = raw.splitlines()[0].strip().split()[0] if raw.split() else ""
    try:
        pid = int(first)
    except ValueError:
        return None
    return pid if pid > 0 else None


def _find_gateway_pid_by_cmdline():
    """Walk running processes for an ``openclaw-gateway`` cmdline.

    Used as a fallback when the PID file is missing (Docker installs, manual
    starts, stale PID files). Prefers psutil when available; otherwise runs
    a bounded ``ps -eo pid,command`` and scans cmdlines.
    """
    try:
        import psutil  # type: ignore

        for p in psutil.process_iter(["pid", "cmdline"]):
            try:
                cmd = " ".join(p.info.get("cmdline") or [])
                if "openclaw-gateway" in cmd or "openclaw/gateway" in cmd:
                    return int(p.info["pid"])
            except Exception:
                continue
        return None
    except Exception:
        pass
    # ps fallback — wide enough cmdline column to spot the gateway.
    try:
        out = subprocess.run(
            ["ps", "-eo", "pid=,command="],
            capture_output=True,
            text=True,
            timeout=2,
        )
        for line in (out.stdout or "").splitlines():
            line = line.strip()
            if not line:
                continue
            if "openclaw-gateway" not in line and "openclaw/gateway" not in line:
                continue
            head = line.split(None, 1)
            if not head:
                continue
            try:
                return int(head[0])
            except ValueError:
                continue
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return None


def _process_vitals_psutil(pid):
    """Return ``(uptime_seconds, rss_mb, cpu_pct)`` via psutil, or ``None``."""
    try:
        import psutil  # type: ignore
    except Exception:
        return None
    try:
        proc = psutil.Process(pid)
        # cpu_percent() with interval=None returns the value since the last
        # call; first call returns 0.0. That's fine — the next /api/system-health
        # poll (and there will be one ~every 30s) returns a real number.
        with proc.oneshot():
            rss_bytes = proc.memory_info().rss
            create_ts = proc.create_time()
            cpu_pct = proc.cpu_percent(interval=None)
    except Exception:
        return None
    uptime = max(0, int(time.time() - create_ts))
    rss_mb = round(rss_bytes / (1024 * 1024), 1)
    return uptime, rss_mb, round(float(cpu_pct), 1)


def _process_vitals_ps(pid):
    """Return ``(uptime_seconds, rss_mb, cpu_pct)`` via ``ps`` fallback, or ``None``.

    ``ps -o rss=,pcpu=,etime= -p <pid>`` works on macOS + Linux. ``rss`` is
    in kilobytes; ``etime`` is a duration we parse to seconds.
    """
    try:
        out = subprocess.run(
            ["ps", "-o", "rss=,pcpu=,etime=", "-p", str(pid)],
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return None
    line = (out.stdout or "").strip()
    if not line:
        return None
    parts = line.split()
    if len(parts) < 3:
        return None
    try:
        rss_kb = int(parts[0])
        cpu_pct = float(parts[1])
    except ValueError:
        return None
    rss_mb = round(rss_kb / 1024.0, 1)
    uptime = _parse_etime(parts[2])
    return uptime, rss_mb, round(cpu_pct, 1)


def _parse_etime(etime):
    """Parse ``ps`` ``etime`` (``[[dd-]hh:]mm:ss``) to seconds, or 0 on garbage."""
    if not etime:
        return 0
    days = 0
    rest = etime
    if "-" in rest:
        d, _, rest = rest.partition("-")
        try:
            days = int(d)
        except ValueError:
            days = 0
    parts = rest.split(":")
    try:
        parts_i = [int(p) for p in parts]
    except ValueError:
        return 0
    if len(parts_i) == 3:
        h, m, s = parts_i
    elif len(parts_i) == 2:
        h, m, s = 0, parts_i[0], parts_i[1]
    elif len(parts_i) == 1:
        h, m, s = 0, 0, parts_i[0]
    else:
        return 0
    return days * 86400 + h * 3600 + m * 60 + s


def _classify_gateway_status(rss_mb, threshold_mb):
    """Memory-pressure classification used by the dashboard badge."""
    if rss_mb is None:
        return "not_running"
    if rss_mb > threshold_mb:
        return "critical"
    if rss_mb > threshold_mb * GATEWAY_MEMORY_WARNING_RATIO:
        return "warning"
    return "healthy"


def compute_gateway_health(
    pid_path=None,
    threshold_mb=GATEWAY_MEMORY_THRESHOLD_MB,
    _psutil_vitals=_process_vitals_psutil,
    _ps_vitals=_process_vitals_ps,
    _cmdline_pid=_find_gateway_pid_by_cmdline,
):
    """Return the gateway-process health payload documented in issue #852.

    Discovery order:
      1. PID file at ``~/.openclaw/gateway/gateway.pid``.
      2. Cmdline scan for ``openclaw-gateway`` (psutil, then ``ps``).

    Vitals source order:
      1. psutil (rss + cpu + create_time).
      2. ``ps -o rss=,pcpu=,etime= -p <pid>`` fallback.

    Returns the canonical shape — all keys always present, fields default to
    ``None`` when the gateway isn't running:

        {
          "pid": int | null,
          "uptime_seconds": int | null,
          "rss_mb": float | null,
          "cpu_pct": float | null,
          "status": "healthy" | "warning" | "critical" | "not_running",
          "memory_threshold_mb": 900,
        }
    """
    payload = {
        "pid": None,
        "uptime_seconds": None,
        "rss_mb": None,
        "cpu_pct": None,
        "status": "not_running",
        "memory_threshold_mb": threshold_mb,
    }
    pid = _read_gateway_pid(pid_path)
    if pid is None:
        try:
            pid = _cmdline_pid()
        except Exception:
            pid = None
    if pid is None:
        return payload

    vitals = None
    try:
        vitals = _psutil_vitals(pid)
    except Exception:
        vitals = None
    if vitals is None:
        try:
            vitals = _ps_vitals(pid)
        except Exception:
            vitals = None
    if vitals is None:
        # PID exists but we can't read vitals (process gone between calls,
        # permission denied, ps not on PATH). Report the PID we found but
        # leave vitals null — UI still renders "Running, vitals unavailable".
        payload["pid"] = pid
        payload["status"] = "warning"
        return payload

    uptime, rss_mb, cpu_pct = vitals
    payload["pid"] = pid
    payload["uptime_seconds"] = uptime
    payload["rss_mb"] = rss_mb
    payload["cpu_pct"] = cpu_pct
    payload["status"] = _classify_gateway_status(rss_mb, threshold_mb)
    return payload


# ---------------------------------------------------------------------------
# Epic #964 — DuckDB local-store fast paths.
#
# Each helper below is opt-in via CLAWMETRY_LOCAL_STORE_READ=1 and returns
# ``None`` on any failure (missing module, empty table, unexpected exception)
# so the legacy code path runs unchanged. Response shapes match the existing
# contracts; the only addition is a ``_source: "local_store"`` marker so
# clients can tell which path served the request.
# ---------------------------------------------------------------------------


def _try_local_store_reliability(window_days: int):
    """Compute reliability trend from local DuckDB heartbeats + events.

    Builds the same response shape as ``AgentReliabilityScorer.score()``:
    direction / slope_per_session / significant / session_count /
    window_days / degrading_dimensions / points.

    Heartbeats are the liveness signal (one per ~minute when the daemon is
    up); error events are the failure signal. We bucket per-day and run an
    OLS slope on the per-day delivery_score (= 1 - error_rate). Returns
    ``None`` to defer to the HistoryDB scorer if anything goes wrong.
    """
    # Issue #1291 cliff #2: route through daemon HTTP proxy. Direct
    # ``get_store()`` (writable) collided with the sync daemon's exclusive
    # DuckDB lock under standard installs (per memory
    # `reference_duckdb_process_lock.md`), errored out, fell through to
    # the HistoryDB scorer that scans the SQLite file → 7.5s p95 the
    # latency probe (#1287) surfaced.
    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    since_iso = (now - timedelta(days=window_days)).isoformat()

    # Parallelize the two daemon-proxy round-trips. Sequential they cost
    # ~550ms total on a warm daemon; parallel cuts that in half (~280ms),
    # putting the endpoint under our <500ms target.
    hb_rows = None
    ev_rows = None
    try:
        from routes.local_query import local_store_via_daemon
        from concurrent.futures import ThreadPoolExecutor

        def _hb():
            try:
                return local_store_via_daemon(
                    "query_heartbeats", since=since_iso, limit=10000)
            except Exception:
                return None

        def _ev():
            try:
                return local_store_via_daemon(
                    "query_events", since=since_iso, limit=10000)
            except Exception:
                return None

        with ThreadPoolExecutor(max_workers=2) as ex:
            f_hb = ex.submit(_hb)
            f_ev = ex.submit(_ev)
            hb_rows = f_hb.result(timeout=4)
            ev_rows = f_ev.result(timeout=4)
    except Exception:
        pass

    # Single-process fallback (tests/dev mode where daemon isn't running).
    if hb_rows is None and ev_rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            hb_rows = store.query_heartbeats(since=since_iso, limit=10000)
            ev_rows = store.query_events(since=since_iso, limit=10000)
        except Exception:
            return None
    hb_rows = hb_rows or []
    ev_rows = ev_rows or []
    # Empty windows are NOT a miss — surface them as insufficient_data
    # instead of falling through to the HistoryDB scorer (which would
    # take the same 7s walk and return the same answer).
    if not hb_rows and not ev_rows:
        return {
            "direction":            "insufficient_data",
            "slope_per_session":    0.0,
            "significant":          False,
            "session_count":        0,
            "window_days":          window_days,
            "degrading_dimensions": [],
            "delivery_slope":       0.0,
            "error_rate":           0.0,
            "success_rate":         1.0,
            "points":               [],
            "_source":              "local_store",
        }

    # Per-day buckets keyed by YYYY-MM-DD.
    buckets: dict[str, dict[str, int]] = {}
    for h in hb_rows:
        ts = (h.get("ts") or "")[:10]
        if not ts:
            continue
        b = buckets.setdefault(ts, {"beats": 0, "errors": 0, "total": 0})
        b["beats"] += 1
        b["total"] += 1
    for e in ev_rows:
        ts = (e.get("ts") or "")[:10]
        if not ts:
            continue
        et = (e.get("event_type") or "").lower()
        b = buckets.setdefault(ts, {"beats": 0, "errors": 0, "total": 0})
        b["total"] += 1
        if "error" in et or "fail" in et or "stalled" in et or "timeout" in et:
            b["errors"] += 1

    if not buckets:
        return None

    ordered_days = sorted(buckets.keys())
    points = []
    for day in ordered_days:
        b = buckets[day]
        total = max(b["total"], 1)
        # delivery_score = 1.0 when no errors; drops as errors/total grows.
        delivery = max(0.0, 1.0 - (b["errors"] / total))
        success_rate = delivery
        error_rate = round(b["errors"] / total, 4)
        points.append({
            "ts": day,
            "delivery": round(delivery, 4),
            "success_rate": round(success_rate, 4),
            "error_rate": error_rate,
            "events": b["total"],
            "beats": b["beats"],
        })

    # OLS slope on delivery over ordered days. Same logic as the legacy
    # scorer — keep callers' expectations stable.
    def _ols_slope(ys):
        n = len(ys)
        if n < 2:
            return 0.0
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(ys) / n
        num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys))
        den = sum((x - x_mean) ** 2 for x in xs)
        return num / den if den else 0.0

    delivery_slope = _ols_slope([p["delivery"] for p in points])
    threshold = 0.02
    if delivery_slope < -threshold:
        direction = "degrading"
    elif delivery_slope > threshold:
        direction = "improving"
    else:
        direction = "stable"

    degrading = []
    if delivery_slope < -threshold:
        degrading.append("delivery_score")

    # Aggregate rates across the whole window for headline numbers.
    total_events = sum(b["total"] for b in buckets.values())
    total_errors = sum(b["errors"] for b in buckets.values())
    overall_error_rate = round(total_errors / total_events, 4) if total_events else 0.0
    overall_success_rate = round(1.0 - overall_error_rate, 4)

    return {
        "direction": direction,
        "slope_per_session": round(delivery_slope, 6),
        "significant": abs(delivery_slope) > threshold,
        "session_count": len(points),
        "window_days": window_days,
        "degrading_dimensions": degrading,
        "delivery_slope": round(delivery_slope, 6),
        "error_rate": overall_error_rate,
        "success_rate": overall_success_rate,
        "points": points[-60:],
        "_source": "local_store",
    }


# Issue #1291 cliff #2 follow-up: window-scaled TTL cache on
# reliability response. The endpoint returns an N-DAY rolling window —
# 1-day windows benefit from fresher data, 90-day windows can cache for
# longer since a single new heartbeat is statistically invisible.
# PR #1304 originally used a flat 30s; PR #1304 review's product P1
# pointed out scaling the TTL with the window is sharper UX.
_RELIABILITY_CACHE: dict = {}


def _reliability_ttl(window_days: int) -> float:
    """TTL scales with window: 1-day → 10s, 30-day → 30s, 90-day → 60s.
    Floor at 10s (avoid hot-loop refreshes), ceiling at 60s (no point
    caching a yearly trend longer than a minute under any plausible UX)."""
    return float(min(60, max(10, window_days)))


@bp_health.route("/api/reliability")
def api_reliability():
    """Cross-session behavioral reliability trend (AgentReliabilityScorer)."""
    import dashboard as _d
    try:
        window = int(request.args.get("window", 30))
        window = max(1, min(window, 90))
    except (TypeError, ValueError):
        window = 30

    # TTL cache key is the window — different window sizes get separate
    # cache slots. Tiny memory footprint (<10 keys ever).
    cache_key = ("reliability", window)
    cached = _RELIABILITY_CACHE.get(cache_key)
    if cached is not None:
        cached_at, payload = cached
        if (time.time() - cached_at) < _reliability_ttl(window):
            return jsonify(payload)

    # Epic #964 fast path — only when explicitly opted in. Falls through
    # to the HistoryDB scorer on any failure so behaviour is identical
    # for users without local_store data.
    if is_local_store_read_enabled():
        fast = _try_local_store_reliability(window)
        if fast is not None:
            _RELIABILITY_CACHE[cache_key] = (time.time(), fast)
            return jsonify(fast)
    # Cloud's dashboard.py is a different module than OSS's; AgentReliabilityScorer
    # only lives in OSS. Use getattr so we degrade to a 200 "insufficient_data"
    # response on cloud instead of 500-ing on AttributeError.
    history_db = getattr(_d, "_history_db", None)
    scorer_cls = getattr(_d, "AgentReliabilityScorer", None)
    if not history_db or not scorer_cls:
        return jsonify(
            {"error": "History module not available", "direction": "insufficient_data"}
        ), 200
    try:
        scorer = scorer_cls(history_db)
        result = scorer.score(window_days=window)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "direction": "insufficient_data"}), 500


def _try_local_store_heatmap(n_days: int):
    """Issue #1088 fast path for /api/heatmap. Bucket events into a (days × 24h)
    grid using DuckDB ``query_events`` instead of scanning every log + JSONL.

    Tries the daemon HTTP proxy FIRST (cross-process safe — under the standard
    install the daemon owns the writer lock and direct opens fail), then falls
    back to a direct ``get_store()`` open for single-process boots (tests +
    dev mode).

    Returns ``None`` to defer to the legacy file scan if:
      - neither path can reach the local store
      - the events table is empty inside the requested window
      - any unexpected error happens
    """
    now = datetime.now()
    cutoff = now - timedelta(days=n_days)
    since_iso = cutoff.replace(microsecond=0).isoformat()
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        # Heatmap is bounded: 90 days × 24h = 2160 cells. 50k events is a
        # generous cap that covers a very busy single-user node and still
        # finishes in <50ms on a laptop.
        rows = local_store_via_daemon("query_events", limit=50000, since=since_iso)
    except Exception:
        rows = None
    # Single-process fallback: open the DuckDB ourselves (tests / dev mode).
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(since=since_iso, limit=50000)
        except Exception:
            return None
    if not rows:
        return None

    grid: dict[str, list[int]] = {}
    day_labels = []
    for i in range(n_days - 1, -1, -1):
        d = now - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        grid[ds] = [0] * 24
        lbl = d.strftime("%b %d") if n_days > 7 else d.strftime("%a %d")
        day_labels.append({"date": ds, "label": lbl})

    counted = 0
    for ev in rows:
        ts = ev.get("ts")
        if not ts:
            continue
        try:
            dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        except Exception:
            continue
        # Drop tz to match the naive ``datetime.now()`` grid keys.
        if dt.tzinfo is not None:
            dt = dt.replace(tzinfo=None)
        day_key = dt.strftime("%Y-%m-%d")
        if day_key in grid:
            grid[day_key][dt.hour] += 1
            counted += 1
    if counted == 0:
        return None

    max_val = max(max(hours) for hours in grid.values()) if grid else 0
    days_out = []
    for dl in day_labels:
        days_out.append({"label": dl["label"], "hours": grid.get(dl["date"], [0] * 24)})
    return {
        "days": days_out,
        "max": max_val,
        "n_days": n_days,
        "_source": "local_store",
    }


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

    # Epic #964 / Issue #1088 — opt-in DuckDB fast path. When
    # CLAWMETRY_LOCAL_STORE_READ=1 AND the store has events in the window,
    # serve from DuckDB via the daemon HTTP proxy (cross-process safe).
    # Falls through to the JSONL/log scan otherwise.
    if is_local_store_read_enabled():
        fast = _try_local_store_heatmap(n_days)
        if fast is not None:
            return jsonify(fast)

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
    # Issue #1256: the legacy ``_gw_invoke("cron", ...)`` round-trips to the
    # OpenClaw gateway via HTTP (10s urllib timeout) and falls through to
    # docker-exec (15s timeout) when that fails. On any user whose gateway
    # is unreachable (no OpenClaw, gateway crashed, port firewalled) the
    # whole /api/system-health request hangs ~7-25s.
    #
    # Fast path: daemon-proxy → DuckDB query_crons. Treat ANY non-None
    # response (including empty list) as authoritative — falling back to
    # the gateway when DuckDB is "just empty" defeats the entire purpose.
    # Same daemon-proxy + single-process fallback wrapper as routes/
    # crons.py:_ls_call (shipped in PR #1258).
    now_ts = time.time()
    cron_source = None
    cron_enabled = 0
    cron_ok_24h = 0
    cron_failed = []
    crons_raw = _ls_call("query_crons", limit=500)
    if crons_raw is not None:
        cron_source = "daemon_proxy"
        for r in crons_raw:
            if r.get("enabled", True):
                cron_enabled += 1
            last_run_ts = _parse_iso_to_epoch(r.get("last_run_at"))
            if last_run_ts and (now_ts - last_run_ts) < 86400:
                status = (r.get("last_status") or "").lower()
                if status in ("ok", "success", "completed", "done", ""):
                    cron_ok_24h += 1
                else:
                    cron_failed.append(r.get("name") or r.get("cron_id") or "unknown")
    else:
        # Legacy gateway/file path. Only reached when the daemon proxy is
        # unreachable AND a direct DuckDB open fails (e.g. truly fresh
        # install with no daemon running). Bounded by the underlying
        # _gw_invoke 10s timeout — slow but correct.
        cron_source = "gateway"
        gw_cron_data = _d._gw_invoke("cron", {"action": "list", "includeDisabled": True})
        crons = (
            gw_cron_data.get("jobs", [])
            if gw_cron_data and "jobs" in gw_cron_data
            else _d._get_crons()
        )
        cron_enabled = len([j for j in crons if j.get("enabled", True)])
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
    # Same daemon-proxy first / gateway-fallback ordering as crons above so
    # we don't pay a 5-10s _gw_ws_rpc("sessions.list") penalty per request
    # when the gateway is unreachable. Empty response from the daemon is
    # authoritative (no sessions in the last 24h is a valid answer).
    sessions_source = None
    sa_runs = 0
    sa_success = 0
    since_24h_iso = datetime.fromtimestamp(
        now_ts - 86400, tz=timezone.utc
    ).isoformat()
    sess_rows = _ls_call("query_sessions", since=since_24h_iso, limit=500)
    if sess_rows is not None:
        sessions_source = "daemon_proxy"
        for s in sess_rows:
            sid = s.get("session_id") or ""
            if "subagent" in sid:
                sa_runs += 1
                sa_success += 1  # We don't track failure in session files currently
    else:
        sessions_source = "gateway"
        for s in _d._get_sessions():
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

    # --- DAEMON ERROR-RATE (PRD #1133 layer 4) ---
    # Tails ~/.clawmetry/sync.log so the user notices silent NameError-class
    # daemon bugs without having to ssh in and `tail -f` the log.
    try:
        daemon_health = compute_daemon_health()
    except Exception:
        # Never crash on bad input — fall back to a healthy-shaped null block.
        daemon_health = {
            "log_path": _default_daemon_log_path(),
            "errors_last_5min": 0,
            "errors_last_1h": 0,
            "last_error_message": None,
            "last_error_ts": None,
            "status": "healthy",
            "log_present": False,
        }

    # --- GATEWAY PROCESS HEALTH (#852) ---
    # Surfaces RSS / CPU / uptime so the ~600MB → ~945MB OOM pattern is
    # visible from the dashboard, not just by tailing logs.
    try:
        gateway_health = compute_gateway_health()
    except Exception:
        gateway_health = {
            "pid": None,
            "uptime_seconds": None,
            "rss_mb": None,
            "cpu_pct": None,
            "status": "not_running",
            "memory_threshold_mb": GATEWAY_MEMORY_THRESHOLD_MB,
        }
    # 852 follow-up: include a tiny last-hour summary from the daemon-
    # persisted gateway.metric events so the card can show "memory
    # trending up over the last hour" without a second roundtrip. Best-
    # effort — empty / not-installed local_store → zero counts.
    try:
        gateway_health["history"] = _summarise_gateway_metric_recent(minutes=60)
    except Exception:
        gateway_health["history"] = {
            "count": 0,
            "min_rss_mb": None,
            "max_rss_mb": None,
            "avg_rss_mb": None,
        }

    # Per-section _source markers help operators see which path served the
    # data without changing the legacy JSON shape (top-level _source is
    # "local_store" only when EVERY DuckDB-eligible block came from the
    # daemon; mixed responses fall back to "mixed").
    sources = {s for s in (cron_source, sessions_source) if s}
    if sources == {"daemon_proxy"}:
        top_source = "daemon_proxy"
    elif sources:
        top_source = "mixed"
    else:
        top_source = "gateway"

    return jsonify(
        {
            "services": services,
            "channels": _d._detect_channel_status(),
            "disks": disks,
            "crons": {
                "enabled": cron_enabled,
                "ok24h": cron_ok_24h,
                "failed": cron_failed,
                "_source": cron_source or "gateway",
            },
            "subagents": {
                "runs": sa_runs,
                "successPct": sa_pct,
                "_source": sessions_source or "gateway",
            },
            "heartbeat": _d._get_heartbeat_status(),
            "sandbox": _d._detect_sandbox_metadata(),
            "inference": _d._detect_inference_metadata(),
            "security": _d._detect_security_metadata(),
            "service_status": service_status,
            "daemon": daemon_health,
            "gateway": gateway_health,
            # Issue #1310 follow-up — per-provider channel ingest summary
            # so operators see whether the gateway WS tap is actually
            # writing Telegram/Signal/Slack/etc. messages to DuckDB.
            "channel_ingest": _channel_ingest_recent(),
            # Connector liveness (incident 2026-05-24: a node went deaf for
            # ~37h with no alarm). Per enabled channel: is the inbound poll
            # alive? 'down' = stopped receiving messages — the one that bites.
            "connector_liveness": _connector_liveness(),
            "_source": top_source,
        }
    )


# Freshness window for the DuckDB fast path. The sync daemon captures one
# ``gateway.metric`` sample every 30s and dedupes near-identical samples for
# up to 5 min (GATEWAY_METRIC_INTERVAL_SEC + GATEWAY_METRIC_DEDUP_WINDOW_SEC
# in clawmetry/sync.py). 10 min keeps us safely past the dedupe horizon
# while still flagging "DuckDB has nothing recent → defer to live psutil".
_GATEWAY_HEALTH_FAST_PATH_MAX_AGE_SEC = 600


def _try_local_store_gateway_health():
    """Fast path for /api/gateway-health — read the most-recent
    ``gateway.metric`` event the sync daemon has already captured to
    DuckDB instead of re-running the psutil/ps live probe on every poll
    (Tier-1 #1565).

    Why the migration:
      * The legacy ``compute_gateway_health()`` shells out to ``ps`` (or
        invokes ``psutil``) every request, which costs ~30-80ms on macOS
        per call and is the dominant cost when an external monitor polls
        this endpoint at sub-minute cadence.
      * On a multi-node fleet, the dashboard process may not see the
        gateway PID at all (different container / different namespace),
        producing a misleading ``not_running`` even when DuckDB has
        recent samples written by the sibling daemon on the host where
        the gateway actually lives.
      * The sync daemon already writes ``gateway.metric`` events every
        30s (clawmetry/sync.py::capture_gateway_metric) with the exact
        ``{pid, uptime_seconds, rss_mb, cpu_pct}`` quartet we need.

    Returns the canonical ``compute_gateway_health()`` shape with the
    additional ``_source: 'local_store'`` marker so the audit canary can
    confirm DuckDB-first service. Returns ``None`` to defer to the live
    probe when:
      * DuckDB is unreachable (no daemon, no fallback handle), OR
      * no ``gateway.metric`` event exists in the freshness window
        (fresh install or daemon down for >10 min).

    The freshness gate is intentional: a 30-minute-old DuckDB sample is
    NOT a useful health reading; the operator wants to know the gateway
    is alive *now*, so we defer to ``compute_gateway_health()`` which
    will correctly report ``not_running`` instead of returning stale
    vitals tagged ``healthy``.
    """
    cutoff_iso = (
        datetime.now(timezone.utc)
        - timedelta(seconds=_GATEWAY_HEALTH_FAST_PATH_MAX_AGE_SEC)
    ).isoformat()
    # Pull just enough rows to find the freshest sample (DuckDB returns
    # newest-first under ``query_events``). limit=1 keeps the daemon-proxy
    # round-trip cheap.
    rows = _ls_call(
        "query_events",
        event_type="gateway.metric",
        since=cutoff_iso,
        limit=1,
    )
    if not rows:
        return None
    row = rows[0]
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    rss_mb = data.get("rss_mb")
    cpu_pct = data.get("cpu_pct")
    pid = data.get("pid")
    uptime = data.get("uptime_seconds")
    # The sync daemon never writes a sample with status=not_running
    # (capture_gateway_metric returns early on that branch), so any row we
    # find here represents a live gateway as of `ts`. Re-classify from
    # rss_mb so we honour the same warning/critical thresholds the legacy
    # path uses.
    status = _classify_gateway_status(rss_mb, GATEWAY_MEMORY_THRESHOLD_MB)
    return {
        "pid": pid,
        "uptime_seconds": uptime,
        "rss_mb": rss_mb,
        "cpu_pct": cpu_pct,
        "status": status,
        "memory_threshold_mb": GATEWAY_MEMORY_THRESHOLD_MB,
        "sample_ts": row.get("ts"),
        "_source": "local_store",
    }


@bp_health.route("/api/gateway-health")
def api_gateway_health():
    """Standalone JSON probe for gateway process vitals (#852).

    Mirrors the ``gateway`` block returned by ``/api/system-health`` so an
    operator (or external monitor) can poll just this surface without
    pulling the full system-health payload.

    Issue #1565 Tier-1: prefer the DuckDB fast path (recent
    ``gateway.metric`` event written by the sync daemon) when
    ``CLAWMETRY_LOCAL_STORE_READ=1``. Falls through to the live psutil/ps
    probe when DuckDB has no recent sample or the env gate is off.
    """
    if is_local_store_read_enabled():
        try:
            fast = _try_local_store_gateway_health()
        except Exception:
            fast = None
        if fast is not None:
            return jsonify(fast)
    try:
        return jsonify(compute_gateway_health())
    except Exception:
        return jsonify(
            {
                "pid": None,
                "uptime_seconds": None,
                "rss_mb": None,
                "cpu_pct": None,
                "status": "not_running",
                "memory_threshold_mb": GATEWAY_MEMORY_THRESHOLD_MB,
            }
        )


def _query_gateway_metric_history(hours: int):
    """Return ``gateway.metric`` events from the last *hours* hours sorted
    ASC (oldest → newest). Internal helper so the test suite can drive it
    without spinning up the Flask app.

    Each row: ``{"ts": ISO8601, "rss_mb": float|None, "cpu_pct": float|None}``.
    No DuckDB / no events → empty list (NOT an error; fresh installs have no
    history yet).

    Issue #1256: routes through ``_ls_call`` so the read goes via the
    daemon's HTTP proxy under the standard install. Direct ``get_store
    (read_only=True)`` was hanging ~2.5s waiting for the writer lock the
    daemon already holds, which dominated the /api/system-health latency
    even after the cron + sessions fast paths landed.
    """
    since_iso = (
        datetime.now(timezone.utc) - timedelta(hours=int(hours))
    ).isoformat()
    # ``query_events`` defaults to DESC + LIMIT 500. A day at 30s with max
    # dedupe relaxation is ≤ 2,880 rows; in practice (dedupe) we see
    # ~50-300/day, but we ask for 10,000 to be safe and sort ASC here.
    rows = _ls_call(
        "query_events",
        event_type="gateway.metric",
        since=since_iso,
        limit=10000,
    )
    if rows is None:
        return []
    out = []
    for r in rows:
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        out.append({
            "ts":      r.get("ts"),
            "rss_mb":  data.get("rss_mb"),
            "cpu_pct": data.get("cpu_pct"),
        })
    out.sort(key=lambda r: r.get("ts") or "")
    return out


def _channel_ingest_recent():
    """Per-provider channel-ingest summary for the System Health UI
    (#1310 follow-up). Returns a list of dicts:

        [{"provider": "telegram", "total": 654, "msg_in": 600,
          "msg_out": 54, "last_ts": "2026-05-15T11:30:00Z",
          "mins_ago": 2}, ...]

    Reads ``query_channel_summary`` via the daemon HTTP proxy so it
    works under the standard install where the dashboard process can't
    open DuckDB directly. Returns ``[]`` on any failure (this is a
    decorative panel; never block /api/system-health on it).

    The ``mins_ago`` field is the operator-felt signal: if it's a small
    number for a given provider, the gateway WS tap is hot for that
    channel. If it's "never" or huge, the tap is off OR there's been
    no traffic — the UI distinguishes those by also showing total>0.
    """
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_channel_summary")
    except Exception:
        rows = None
    if rows is None:
        # Single-process fallback (tests/dev with no sync daemon).
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_channel_summary()
        except Exception:
            return []
    if not rows:
        return []

    now = datetime.now(timezone.utc)
    out = []
    for r in rows:
        if not isinstance(r, dict):
            continue
        last_ts = r.get("last_ts")
        mins_ago = None
        if last_ts:
            try:
                ts = datetime.fromisoformat(str(last_ts).replace("Z", "+00:00"))
                mins_ago = max(0, int((now - ts).total_seconds() / 60))
            except Exception:
                mins_ago = None
        out.append({
            "provider": r.get("provider") or "?",
            "total":    int(r.get("total") or 0),
            "msg_in":   int(r.get("msg_in") or 0),
            "msg_out":  int(r.get("msg_out") or 0),
            "last_ts":  last_ts,
            "mins_ago": mins_ago,
        })
    # Most-recently-active provider first.
    out.sort(key=lambda r: r.get("mins_ago") if r.get("mins_ago") is not None else 1e9)
    return out


# ── Connector liveness ("agent went deaf and nobody noticed") ───────────────
# A channel went deaf for ~37h with no alarm (2026-05-24): the inbound
# long-poll wedged but outbound (crons) kept working, so health stayed green.
# The daemon records connector.health signals (sync.sync_connector_health
# _from_logs); the classifier is shared with the cloud snapshot builder in
# ``clawmetry/connector_health.py`` so the local UI and cloud never disagree.
def _connector_liveness():
    """Per-enabled-channel inbound-poll verdict for the System Health UI.

    Returns ``[{provider, state, reason, mins_ago, last_kind}, ...]`` with
    ``state`` ∈ ``down`` | ``degraded`` | ``unknown`` | ``ok`` (worst first).
    Reads connector.health signals via the daemon proxy (DuckDB-first);
    returns ``[]`` on any failure — never blocks /api/system-health.
    """
    from clawmetry.connector_health import (
        enabled_channels_from_config, classify_connector_liveness,
    )
    enabled = enabled_channels_from_config()
    if not enabled:
        return []
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_connector_health", since_hours=24)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_connector_health(since_hours=24)
        except Exception:
            rows = []
    return classify_connector_liveness(enabled, rows)


def _summarise_gateway_metric_recent(minutes: int = 60):
    """Return a small {count, min_rss_mb, max_rss_mb, avg_rss_mb} summary
    suitable for embedding in the existing ``/api/system-health.gateway``
    block. Cheap (single read of the recent slice); never raises.
    """
    rows = _query_gateway_metric_history(hours=max(1, int(minutes / 60) or 1))
    if not rows:
        return {"count": 0, "min_rss_mb": None, "max_rss_mb": None, "avg_rss_mb": None}
    # Restrict to the requested last-N-minutes window in case query padded out.
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
    rss_values = [
        r["rss_mb"]
        for r in rows
        if r.get("ts") and r["ts"] >= cutoff and r.get("rss_mb") is not None
    ]
    if not rss_values:
        return {"count": 0, "min_rss_mb": None, "max_rss_mb": None, "avg_rss_mb": None}
    return {
        "count":      len(rss_values),
        "min_rss_mb": round(min(rss_values), 1),
        "max_rss_mb": round(max(rss_values), 1),
        "avg_rss_mb": round(sum(rss_values) / len(rss_values), 1),
    }


@bp_health.route("/api/gateway-health/history")
def api_gateway_health_history():
    """24h-window sparkline data for the gateway-health card (#852 followup).

    Query string:
      * ``hours`` — lookback window (1-168, default 24).

    Returns a JSON array of ``{ts, rss_mb, cpu_pct}`` rows, sorted oldest →
    newest. Empty array (NOT 4xx/5xx) when no events have been written yet
    — fresh installs need ~30s to capture the first sample, and the frontend
    treats empty data as "sparkline not available yet" rather than an error.
    """
    try:
        hours = int(request.args.get("hours", "24"))
    except (TypeError, ValueError):
        hours = 24
    # Clamp to a sane range. 1 week max — anything longer should query DuckDB
    # directly; the dashboard sparkline only needs 24h.
    hours = max(1, min(168, hours))
    try:
        rows = _query_gateway_metric_history(hours=hours)
    except Exception:
        rows = []
    return jsonify(rows)


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

    # 4. Uptime — portable across macOS/Linux/Win (GNU `uptime -p` is Linux-only).
    try:
        from helpers.system import uptime_pretty

        uptime = uptime_pretty().replace("up ", "")
        if uptime == "unknown":
            checks.append(
                {
                    "id": "uptime",
                    "status": "warning",
                    "color": "yellow",
                    "detail": "Unknown",
                }
            )
        else:
            checks.append(
                {
                    "id": "uptime",
                    "status": "healthy",
                    "color": "green",
                    "detail": uptime,
                }
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


def _try_local_store_service_status():
    """Compose service_status from heartbeats + system_snapshots.

    - ``sync``: True iff a heartbeat row exists within the last 5 minutes
      (the daemon writes one per minute when up).
    - ``gateway``: from the most recent system_snapshot of kind 'gateway'
      (data.up boolean) when present, else inferred from the same heartbeat
      payload (``data.gateway_up``).
    - ``channels``: from the most recent system_snapshot of kind 'channels'
      when present (data.channels list), else from the heartbeat payload's
      ``channels`` field, else empty.
    - ``resources``: from the most recent system_snapshot of kind
      'resources' when present (data.status string), else "ok".

    Returns ``None`` when no recent heartbeat exists — the legacy handler
    will then live-probe the gateway port + run pgrep, which is the right
    behaviour for a node that has never written to the local store.

    MOAT Tier-1 sweep (refs #1565): route through the daemon HTTP proxy
    first. The previous direct ``local_store.get_store(read_only=True)``
    open silently failed on multi-process installs (DuckDB exclusive lock
    blocks even RO opens — see memory ``reference_duckdb_process_lock.md``),
    forcing /api/service-status to fall through to a live gateway probe
    + pgrep on every poll for every standard launchd / systemd user.
    """
    from routes.local_query import local_store_via_daemon

    def _query(method, **kwargs):
        """Daemon proxy first, single-process direct open as fallback."""
        try:
            rows = local_store_via_daemon(method, **kwargs)
            if rows is not None:
                return rows
        except Exception:
            pass
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            return getattr(store, method)(**kwargs)
        except Exception:
            return None

    hb_rows = _query("query_heartbeats", limit=1)
    if not hb_rows:
        return None
    hb = hb_rows[0]
    hb_data = hb.get("data") if isinstance(hb.get("data"), dict) else {}

    # Sync up = heartbeat seen recently.
    sync_up = True
    try:
        from datetime import datetime, timezone
        ts = (hb.get("ts") or "").replace("Z", "+00:00")
        beat_dt = datetime.fromisoformat(ts)
        age = (datetime.now(timezone.utc) - beat_dt).total_seconds()
        sync_up = age < 300  # 5 min staleness threshold
    except Exception:
        pass

    # Helper to grab the most recent snapshot of a given kind from the
    # same node, falling back to any node's most recent of that kind.
    node_id = hb.get("node_id")

    def _latest_snapshot(kind: str):
        rows = _query("query_system_snapshots", node_id=node_id, kind=kind, limit=1)
        if not rows:
            rows = _query("query_system_snapshots", kind=kind, limit=1)
        return rows[0] if rows else None

    gw_snap = _latest_snapshot("gateway")
    if gw_snap and isinstance(gw_snap.get("data"), dict):
        gw_up = bool(gw_snap["data"].get("up", gw_snap["data"].get("gateway", True)))
    else:
        gw_up = bool(hb_data.get("gateway_up", True))

    ch_snap = _latest_snapshot("channels")
    channels_out = []
    if ch_snap and isinstance(ch_snap.get("data"), dict):
        raw = ch_snap["data"].get("channels") or []
        if isinstance(raw, list):
            for ch in raw:
                if isinstance(ch, dict):
                    channels_out.append({
                        "name": str(ch.get("name", ch.get("kind", "unknown"))),
                        "connected": bool(ch.get("connected", ch.get("ok", False))),
                    })
    if not channels_out:
        raw = hb_data.get("channels") or []
        if isinstance(raw, list):
            for ch in raw:
                if isinstance(ch, dict):
                    channels_out.append({
                        "name": str(ch.get("name", ch.get("kind", "unknown"))),
                        "connected": bool(ch.get("connected", ch.get("ok", False))),
                    })

    res_snap = _latest_snapshot("resources")
    resources = "ok"
    if res_snap and isinstance(res_snap.get("data"), dict):
        s = res_snap["data"].get("status") or res_snap["data"].get("resources")
        if s in ("ok", "warn", "critical"):
            resources = s

    return {
        "service_status": {
            "gateway": gw_up,
            "channels": channels_out,
            "sync": sync_up,
            "resources": resources,
        },
        "_source": "local_store",
    }


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
    # Epic #964 fast path. Composite of heartbeats + system_snapshots.
    if is_local_store_read_enabled():
        fast = _try_local_store_service_status()
        if fast is not None:
            return jsonify(fast)
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
    # CRITICAL (regression #1228): the sync daemon (separate process)
    # holds DuckDB's exclusive lock on clawmetry.duckdb. Even read-only
    # opens block on it — direct ``get_store()`` here can hang for the full
    # retry budget (~2.5s) and then return None, leaving the dashboard
    # panel stuck on "No heartbeats yet". Route through the daemon's
    # local_query proxy first; only fall back to direct open in the
    # single-process / dev-mode case where the daemon isn't running.
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        kwargs = {"limit": 1}
        if node_id:
            kwargs["node_id"] = node_id
        rows = local_store_via_daemon("query_heartbeats", **kwargs)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
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
    if is_local_store_read_enabled():
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


@bp_health.route("/api/agent-presence")
def api_agent_presence():
    """Return whether any underlying agent (OpenClaw / NVIDIA NemoClaw) is
    installed and producing data. Sibling of ``/api/heartbeat-status``
    that answers a different question (see ``detect_agent_install``
    docstring in dashboard.py).

    Frontend uses this to render the "No agent detected" page-level empty
    state when ``no_agent=true``, so users who installed ClawMetry without
    an agent see actionable copy + install links instead of an empty
    dashboard that looks broken.
    """
    import dashboard as _d
    return jsonify(_d.detect_agent_install())


def _try_local_store_rate_limits():
    """Fast path for /api/rate-limits — derive rolling 1m/1h utilisation
    from the DuckDB ``events`` table instead of the per-process in-memory
    ``metrics_store`` ring buffer.

    Why the migration: the legacy handler aggregates only the LLM
    token/cost events the *current dashboard process* witnessed via OTLP
    + the in-process interceptor (see ``dashboard._record_token_event``
    callers). On a fresh dashboard restart the buffer is empty and the
    panel reads "0% utilisation" for several minutes until traffic
    re-populates it; on multi-node fleets the buffer also misses spend
    that landed on sibling nodes. The DuckDB ``events`` table is the
    canonical, cross-process, cross-restart store — every cost-bearing
    event the sync daemon ingests (Anthropic SDK echo, OpenClaw v3
    ``model.completed`` bubbles, OTLP-relayed metrics) lands there with
    a stable ``model``/``cost_usd``/``token_count`` column trio plus a
    ``data`` blob carrying the raw ``usage`` dict for input/output
    splits.

    AUDIT FALSE-POSITIVE NOTE (refs #1565): Eng C's audit flagged this
    route as "JSONL-fallback" but the actual legacy path is the
    in-memory ``metrics_store`` (no JSONL walker). The migration is
    still worth doing — promoting to the canonical DuckDB helper makes
    the response visible to the audit canary (_source tag) and survives
    dashboard restarts — but the audit row should be relabelled
    "in-memory ring → DuckDB events" rather than "JSONL → DuckDB".

    Returns ``None`` when the store is unreachable so the legacy
    in-memory aggregation still serves. Returns a populated zero-shell
    when the store is reachable but no cost-bearing events exist (fresh
    install) — same shape the legacy handler emits for an empty buffer,
    so the dashboard panel renders "no traffic" instantly instead of
    waiting for the legacy path to confirm the same empty answer.
    """
    now = time.time()
    one_min_ago = now - 60
    one_hour_ago = now - 3600
    since_iso = datetime.fromtimestamp(one_hour_ago, tz=timezone.utc).isoformat()

    # query_events sorts newest-first and is bounded by the daemon-proxy
    # row cap. 5k rows ≈ 80+ requests/min for a full hour — plenty of
    # headroom while keeping the JSON payload modest. Anything older than
    # 1h doesn't contribute to either rolling window.
    rows = _ls_call("query_events", since=since_iso, limit=5000)
    if rows is None:
        return None

    import dashboard as _d

    # Buckets keyed by canonical provider name (anthropic/openai/google/...).
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

    def _row_ts_epoch(ev):
        ts = ev.get("ts")
        if isinstance(ts, (int, float)):
            return float(ts)
        try:
            return datetime.fromisoformat(
                str(ts).replace("Z", "+00:00")
            ).timestamp()
        except Exception:
            return 0.0

    # Event-type filter: only count cost/token-bearing turns. v3 real
    # data emits ``model.completed`` and bare ``assistant`` (no synthetic
    # ``message`` rows — per reference_openclaw_v3_event_types.md and
    # feedback_synthetic_tests_missed_real_event_shape.md). Keep the
    # legacy ``message`` string for synthetic harnesses.
    BILLABLE_TYPES = {
        "message", "assistant", "model.completed",
        "subagent:assistant", "user",
    }

    for ev in rows:
        et = (ev.get("event_type") or "").strip()
        if et and et not in BILLABLE_TYPES:
            continue
        ts = _row_ts_epoch(ev)
        if ts < one_hour_ago:
            continue

        # Extract input/output token splits. The ``token_count`` column
        # is the SUM, the ``data`` blob carries the breakdown. Walk both
        # the Anthropic-SDK echo shape (data.message.usage) AND the
        # OpenClaw-native v3 shape (data.assistantMessage.usage) so we
        # don't silently zero one or the other.
        data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
        usage = {}
        msg = data.get("message") if isinstance(data.get("message"), dict) else None
        am = data.get("assistantMessage") if isinstance(data.get("assistantMessage"), dict) else None
        if isinstance(msg, dict) and isinstance(msg.get("usage"), dict):
            usage = msg["usage"]
        elif isinstance(am, dict) and isinstance(am.get("usage"), dict):
            usage = am["usage"]
        elif isinstance(data.get("usage"), dict):
            usage = data["usage"]
        in_tok = int(usage.get("input_tokens") or usage.get("input") or 0)
        out_tok = int(usage.get("output_tokens") or usage.get("output") or 0)
        # Fall back to the coarse token_count column when the usage dict
        # is missing entirely (e.g. legacy rows pre-v3).
        total = int(ev.get("token_count") or 0)
        if not (in_tok or out_tok) and total:
            # Best-effort split: count as input (Anthropic-style prompt
            # counts dominate). Better than zero.
            in_tok = total
            out_tok = 0

        model = ev.get("model") or (data.get("model") if isinstance(data.get("model"), str) else "") or "unknown"
        provider = _d._infer_provider({"provider": data.get("provider"), "model": model})

        p = _get_p(provider)
        p['models'].add(model)
        if ts >= one_min_ago:
            p['rpm_1m'] += 1
            p['tokens_in_1m'] += in_tok
            p['tokens_out_1m'] += out_tok
        p['request_count_1h'] += 1
        p['tokens_in_1h'] += in_tok
        p['tokens_out_1h'] += out_tok
        p['cost_1h'] += float(ev.get("cost_usd") or 0.0)

    result = []
    for prov, stats in sorted(providers.items()):
        limits = _d._DEFAULT_RATE_LIMITS.get(
            prov,
            {'rpm': 60, 'tpm_input': 100_000, 'tpm_output': 20_000, 'label': prov.title()},
        )
        rpm_pct = round(stats['rpm_1m']        / limits['rpm']        * 100, 1) if limits['rpm']        else 0
        in_pct  = round(stats['tokens_in_1m']  / limits['tpm_input']  * 100, 1) if limits['tpm_input']  else 0
        out_pct = round(stats['tokens_out_1m'] / limits['tpm_output'] * 100, 1) if limits['tpm_output'] else 0
        worst = max(rpm_pct, in_pct, out_pct)
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
    return {
        'providers': result,
        'timestamp': now,
        '_source': 'local_store',
    }


@bp_health.route('/api/rate-limits')
def api_rate_limits():
    """Return rolling 1-minute and 1-hour API rate limit utilisation per provider."""
    import dashboard as _d
    if is_local_store_read_enabled():
        fast = _try_local_store_rate_limits()
        if fast is not None:
            return jsonify(fast)

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


def _try_local_store_sandbox_status():
    """Read sandbox/inference/security from system_snapshots(kind="sandbox").

    The daemon writes a single 'sandbox' kind row per snapshot containing
    the three sub-dicts (sandbox / inference / security) the legacy handler
    derives from the local environment. We pick the most-recent row.

    Returns ``None`` if the local_store module is missing, no snapshot of
    kind 'sandbox' exists, or the row's payload doesn't decode.
    """
    # Issue #1282: daemon-proxy first, read-only fallback for single-process boots.
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_system_snapshots", kind="sandbox", limit=1)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_system_snapshots(kind="sandbox", limit=1)
        except Exception:
            return None
    if not rows:
        return None
    payload = rows[0].get("data")
    if not isinstance(payload, dict):
        return None

    # Accept either the canonical {sandbox, inference, security} shape
    # straight from the snapshot, or a flat dict that mirrors the legacy
    # detection helpers' output.
    sandbox = payload.get("sandbox")
    inference = payload.get("inference")
    security = payload.get("security")

    # Normalise to the same canonical fields the legacy handler emits.
    if isinstance(sandbox, dict):
        sandbox = {
            "name": sandbox.get("name"),
            "status": sandbox.get("status", "running"),
            "type": sandbox.get("type"),
        }
    else:
        sandbox = None
    if isinstance(inference, dict):
        inference = {
            "provider": inference.get("provider"),
            "model": inference.get("model"),
        }
    else:
        inference = None
    if isinstance(security, dict):
        sec_fields: dict = {}
        if "sandbox_enabled" in security:
            sec_fields["sandbox_enabled"] = bool(security["sandbox_enabled"])
        if "network_policy" in security:
            sec_fields["network_policy"] = security["network_policy"]
        security = sec_fields or None
    else:
        security = None

    return {
        "sandbox": sandbox,
        "inference": inference,
        "security": security,
        "_source": "local_store",
    }


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
    # Epic #964 fast path. When the daemon has written a sandbox snapshot
    # to DuckDB, prefer that — it's the most recently-collected view.
    if is_local_store_read_enabled():
        fast = _try_local_store_sandbox_status()
        if fast is not None:
            return jsonify(fast)
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


def _try_local_store_loop_detection(window: int, min_repeats: int):
    """Detect rapid-repeat tool_call loops from events table.

    Walks all events with event_type='tool_call' (or 'toolCall'), groups
    them per session, and applies the same sliding-window detection as
    the JSONL scanner: a tool name + arg fingerprint pair appearing
    ``min_repeats`` or more times within ``window`` consecutive calls.

    Returns ``None`` when local_store is missing or no tool_call events
    exist. ``checked`` is the count of distinct sessions inspected.
    """
    # Issue #1282: daemon-proxy first, read-only fallback for single-process boots.
    rows: list = []
    try:
        from routes.local_query import local_store_via_daemon
        for et in ("tool_call", "toolCall"):
            try:
                proxy_rows = local_store_via_daemon("query_events", event_type=et, limit=10000)
                if proxy_rows:
                    rows.extend(proxy_rows)
            except Exception:
                continue
    except Exception:
        rows = []
    if not rows:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            for et in ("tool_call", "toolCall"):
                try:
                    rows.extend(store.query_events(event_type=et, limit=10000))
                except Exception:
                    continue
        except Exception:
            return None
    if not rows:
        return None

    # Sort ascending by ts so window-detection is in temporal order.
    rows.sort(key=lambda r: r.get("ts") or "")

    # Bucket per session.
    by_session: dict = {}
    for r in rows:
        sid = r.get("session_id") or ""
        if not sid:
            continue
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        name = (data.get("name") or data.get("tool") or "").strip()
        if not name:
            continue
        # Same fingerprint as the JSONL scanner: stable hash of input dict.
        inp = data.get("input") or data.get("args") or {}
        try:
            raw_args = json.dumps(inp, sort_keys=True, default=str)[:500]
        except Exception:
            raw_args = str(inp)[:500]
        fp = hashlib.md5(raw_args.encode()).hexdigest()[:8]
        by_session.setdefault(sid, []).append((name, fp, r.get("ts") or ""))

    if not by_session:
        return None

    loops = []
    for sid, seq in by_session.items():
        if len(seq) < min_repeats:
            continue
        seen_combos = set()
        for i in range(max(1, len(seq) - window + 1)):
            chunk = seq[i:i + window]
            counts: dict = {}
            for name, fp, _ts in chunk:
                combo = (name, fp)
                counts[combo] = counts.get(combo, 0) + 1
            for combo, count in counts.items():
                if count >= min_repeats and combo not in seen_combos:
                    seen_combos.add(combo)
                    first_ts = next(ts for n, f, ts in seq if (n, f) == combo)
                    loops.append({
                        "session_id": sid,
                        "tool_name": combo[0],
                        "repeat_count": count,
                        "first_seen_ts": first_ts,
                    })

    return {
        "checked": len(by_session),
        "loop_count": len(loops),
        "loops": loops,
        "_source": "local_store",
    }


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

    # Epic #964 fast path. When tool_call events are present in the local
    # DuckDB, run loop detection directly against the columnar store
    # instead of walking ~/.openclaw/agents/main/sessions/*.jsonl.
    if is_local_store_read_enabled():
        fast = _try_local_store_loop_detection(window, min_repeats)
        if fast is not None:
            return jsonify(fast)

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
# Loop-detection signals from clawmetry/proxy.py LoopDetector (issue #1364)
#
# Distinct from /api/loop-detection above (which scans tool_call sequences
# in session JSONL). This endpoint serves the persisted signals that the
# enforcement proxy emits whenever a request hash repeats often enough to
# trip ``LoopDetectionConfig.max_similar`` in a window. Backed by the
# DuckDB ``loop_signals`` table; gracefully returns ``[]`` when the local
# store is unreachable so the Brain badge fails closed (no badge) rather
# than blowing up the page.
# ---------------------------------------------------------------------------


@bp_health.route("/api/loop-signals")
def api_loop_signals():
    """Return recent LoopDetector signals for the dashboard's Brain badge.

    Query params (all optional):
      limit          — max rows (default 20, clamp 1..200)
      since_minutes  — last-N minute window (default 60, <=0 disables)

    Response:
      {
        "signals": [
          {"session_id": str, "signature": str, "repeat_count": int,
           "first_seen": str, "last_seen": str, "severity": str,
           "agent_type": str, "details": dict|str|None}
        ],
        "count": <int>,
        "total_count": <int>,         # rows the store would have returned
        "capped_pro_gated": <bool>    # True when OSS cap dropped rows
      }

    Empty-list fallback (HTTP 200) on any error so the badge never breaks
    the page.

    OSS / Cloud-Free gating (issue #1376): Cloud-Pro is the home of loop
    history, alert-on-N-loops, and Slack/PagerDuty dispatch. Shipping the
    full table in OSS leaks that value. We cap OSS callers to a single
    teaser row and flag the response so the UI can render the upgrade CTA.
    Cloud-Pro users (validated by ``dashboard._is_pro_user``) keep the
    full table.
    """
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    try:
        since_minutes = int(request.args.get("since_minutes", 60))
    except (TypeError, ValueError):
        since_minutes = 60

    # Pro gate (issue #1376). Fail closed: any error → OSS cap applies.
    try:
        import dashboard as _d
        is_pro = bool(_d._is_pro_user())
    except Exception:
        is_pro = False

    rows = _ls_call(
        "query_recent_loop_signals",
        limit=limit,
        since_minutes=since_minutes,
    )
    if rows is None:
        rows = []

    total_count = len(rows)
    capped_pro_gated = False
    if not is_pro and total_count > 1:
        rows = rows[:1]
        capped_pro_gated = True

    return jsonify({
        "signals": rows,
        "count": len(rows),
        "total_count": total_count,
        "capped_pro_gated": capped_pro_gated,
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


def _try_local_store_mcp_stats():
    """Aggregate MCP tool-call stats from events(event_type='mcp_call').

    Each event row is expected to carry the tool ``name`` (and optionally
    ``error``/``is_error`` and ``latency_ms`` / ``duration_ms``) in its
    JSON ``data`` payload. Built-in tools are filtered out — same rule as
    the JSONL scanner.

    Returns ``None`` when the local_store module is missing or no
    ``mcp_call`` events exist.
    """
    # Issue #1282: daemon-proxy first, read-only fallback for single-process boots.
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_events", event_type="mcp_call", limit=10000)
    except Exception:
        rows = None
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_events(event_type="mcp_call", limit=10000)
        except Exception:
            return None
    if not rows:
        return None

    # {tool_name: {calls, errors, latencies_ms}}
    tool_stats: dict = {}
    distinct_sessions: set = set()
    for r in rows:
        data = r.get("data") if isinstance(r.get("data"), dict) else {}
        name = (data.get("name") or data.get("tool") or "").strip()
        if not name or name in _BUILTIN_TOOLS:
            continue
        sid = r.get("session_id")
        if sid:
            distinct_sessions.add(sid)
        s = tool_stats.setdefault(name, {"calls": 0, "errors": 0, "latencies_ms": []})
        s["calls"] += 1
        if data.get("error") or data.get("is_error") or data.get("isError"):
            s["errors"] += 1
        lat = data.get("latency_ms") or data.get("duration_ms")
        if isinstance(lat, (int, float)) and lat >= 0:
            s["latencies_ms"].append(float(lat))

    if not tool_stats:
        return None

    out = []
    for name, s in tool_stats.items():
        calls = s["calls"]
        errors = s["errors"]
        lats = s["latencies_ms"]
        out.append({
            "name": name,
            "calls": calls,
            "errors": errors,
            "error_rate_pct": round(errors * 100.0 / calls, 1) if calls else 0.0,
            "avg_latency_ms": round(sum(lats) / len(lats)) if lats else None,
        })
    out.sort(key=lambda x: x["calls"], reverse=True)

    return {
        "checked": len(distinct_sessions),
        "tools": out,
        "_source": "local_store",
    }


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
    # Epic #964 fast path. When mcp_call events are present in the local
    # DuckDB, aggregate from there instead of re-walking session JSONLs.
    if is_local_store_read_enabled():
        fast = _try_local_store_mcp_stats()
        if fast is not None:
            return jsonify(fast)

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


@bp_health.route("/api/handler-latency")
def api_handler_latency():
    """Issue #1283 — per-endpoint p50/p95 from a 5-minute rolling buffer.

    Operator dashboard for ClawMetry's own handler latency. Lets us catch
    the next /api/sessions-class regression in seconds, not weeks.
    """
    try:
        from clawmetry import latency_tracker
    except Exception:
        return jsonify({"endpoints": [], "endpoint_count": 0, "_source": "unavailable"})

    try:
        top_n = max(1, min(100, int(request.args.get("top", 20))))
    except (TypeError, ValueError):
        top_n = 20
    try:
        slow_ms = float(request.args.get("slow_ms", 500.0))
    except (TypeError, ValueError):
        slow_ms = 500.0

    stats = latency_tracker.get_stats(top_n=top_n, slow_threshold_ms=slow_ms)
    stats["_source"] = "in_memory"
    return jsonify(stats)
