"""
ClawMetry - See your agent think 🦞

Real-time observability dashboard for your AI agents (OpenClaw, NVIDIA NemoClaw, Claude Code, Codex + 8 more runtimes).
Single-file Flask app with zero config - auto-detects your setup.

Usage:
    clawmetry                             # Auto-detect everything
    clawmetry --port 9000                 # Custom port
    clawmetry --workspace ~/bot           # Custom workspace
    OPENCLAW_HOME=~/bot clawmetry

https://github.com/vivekchand/clawmetry
MIT License
"""

from clawmetry.gateway_protocol import (
    GATEWAY_MAX_PROTOCOL as _GW_MAX_PROTO,
    GATEWAY_MIN_PROTOCOL as _GW_MIN_PROTO,
)
import hashlib
import hmac
import os
import sys

# When run as `python dashboard.py`, this module is registered as `__main__`,
# not `dashboard`. Route blueprints in routes/ do `import dashboard as _d` at
# call time — without this alias, that import re-executes all 33k lines as a
# second `dashboard` module on first request, causing 10s+ timeouts on Windows
# CI (issue surfaced by the bp_sessions refactor).
sys.modules.setdefault("dashboard", sys.modules[__name__])

# Force UTF-8 output on Windows (emoji in BANNER would crash with cp1252).
# Must be reconfigure(), not a new TextIOWrapper around sys.stdout.buffer:
# this block runs twice (the module header is duplicated inside this file),
# and when the second wrapper replaces the first, the orphaned wrapper is
# garbage-collected and closes the shared underlying buffer — leaving
# sys.stdout closed for the rest of the process (silent --help, dead prints).
if sys.platform == "win32":
    import io

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import glob
import json
import socket
from collections import deque, defaultdict

# In-process ring-buffer for quick action history (last 50 entries)
_quick_action_log = deque(maxlen=50)

import argparse
import subprocess
import time
import threading
import select
from datetime import datetime, timezone, timedelta
from typing import Optional
from flask import (
    Flask,
    render_template_string,
    request,
    jsonify,
    Response,
    make_response,
)

# Route blueprints extracted from this file (Phase 5 modularisation).
# Late-imports inside each handler keep dashboard.py as the single source of
# truth for module-level helpers — see routes/sessions.py for the pattern.
from routes.sessions import bp_sessions
from routes.tracing import bp_tracing
from routes.trail import bp_trail
from routes.brain import bp_brain
from routes.advisor import bp_advisor
from routes.selfevolve import bp_selfevolve

# Module-level helpers extracted to helpers/*.py (Phase 6 modularisation).
# Re-exported here so existing `_d.<name>` references in routes/*.py keep
# working without code changes. Over time, route modules will import from
# helpers/ directly and these re-exports will be retired.
from helpers.pricing import (  # noqa: F401 — re-export for routes/
    _provider_from_model,
    _infer_provider_from_model,
)
from helpers.logs import (  # noqa: F401 — re-export for routes/
    _grep_log_file,
    _tail_lines,
    _get_log_dirs,
    _find_log_file,
)
from helpers.streams import (  # noqa: F401 — re-export for routes/
    SSE_MAX_SECONDS,
    _acquire_stream_slot,
    _release_stream_slot,
)
from helpers.hardware import _detect_host_hardware  # noqa: F401 — re-export for routes/
from helpers.gateway import (  # noqa: F401 — re-export for routes/
    _gw_invoke,
    _gw_invoke_docker,
    _gw_ws_rpc,
)
from routes.usage import bp_usage
from routes.crons import bp_crons
from routes.harness import bp_harness
from routes.delegated import bp_delegated
from routes.readiness import bp_readiness
from routes.guard import bp_guard
from routes.signals import bp_signals
from routes.selfdiag import bp_selfdiag
from routes.health import bp_health
from routes.alerts import bp_alerts, bp_budget
from routes.channels import bp_channels
from routes.overview import bp_overview
from routes.trial import bp_trial
from routes.onboarding import bp_onboarding
from routes.components import bp_components
from routes.fleet_history import bp_fleet
from routes.infra import bp_logs, bp_memory, bp_security, bp_config
from routes.meta import bp_auth, bp_cloud_relay, bp_gateway, bp_otel, bp_otlp_traces, bp_version, bp_version_impact
from routes.compliance import bp_compliance
from routes.org_analytics import bp_org_analytics
from routes.nemoclaw import bp_nemoclaw
from routes.skills import bp_skills
from routes.runtime_memory import bp_runtime_memory
from routes.heartbeat import bp_heartbeat
from routes.autonomy import bp_autonomy
from routes.selfconfig import bp_selfconfig
from routes.agents import bp_agents
from routes.inventory import bp_inventory
from routes.govern import bp_govern
from routes.assets import bp_assets
from routes.reasoning import bp_reasoning
from routes.plugins import bp_plugins
from routes.local_query import bp_local_query
from routes.update_check import bp_update_check, start_update_check_thread
from routes.workspaces import bp_workspaces
from routes.bootstrap import bp_bootstrap
from routes.insights import bp_insights
from routes.review import bp_review
from routes.evals import bp_evals
from routes.bench import bp_bench
from routes.cohort import bp_cohort
from routes.quality import bp_quality
from routes.dives import bp_dives
from routes.reports import bp_reports
from routes.scheduler import bp_scheduler
from routes.policy import bp_policy
from routes.turn_anatomy import bp_turn_anatomy
from routes.tool_catalog import bp_tool_catalog
from routes.context_economics import bp_context_economics
from routes.spend_flow import bp_spend_flow
from routes.entitlement import bp_entitlement
from routes.extensions import bp_extensions
from routes.otel_export import bp_otel_export
from routes.device import bp_device
from routes.runtime_ingest import bp_runtime_ingest
from routes.audit import bp_audit
from routes.sla import bp_sla
from routes.hitl import bp_hitl
from routes.rules import bp_rules
from routes.attention import bp_attention
from helpers.openapi import bp_openapi

# History / time-series module
try:
    from history import HistoryDB, HistoryCollector, AgentReliabilityScorer

    _HAS_HISTORY = True
except ImportError:
    _HAS_HISTORY = False
    HistoryDB = None
    HistoryCollector = None
    AgentReliabilityScorer = None

_history_db = None
_history_collector = None

# Optional: OpenTelemetry protobuf support for OTLP receiver
_HAS_OTEL_PROTO = False
try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
    from opentelemetry.proto.collector.logs.v1 import logs_service_pb2

    _HAS_OTEL_PROTO = True
except ImportError:
    metrics_service_pb2 = None
    trace_service_pb2 = None
    logs_service_pb2 = None


# Hard ceiling on a gzip-decompressed OTLP body. A few-KB gzip bomb can expand
# to many GB and OOM the daemon (never-crash / never-hang). Cap the output and
# reject anything larger. Override via CLAWMETRY_OTLP_MAX_DECOMPRESSED_MB.
try:
    _OTLP_MAX_DECOMPRESSED = int(os.environ.get("CLAWMETRY_OTLP_MAX_DECOMPRESSED_MB", "64")) * 1024 * 1024
except (TypeError, ValueError):
    _OTLP_MAX_DECOMPRESSED = 64 * 1024 * 1024


def _gunzip_bounded(pb_data, limit=None):
    """gzip-decompress with a hard output cap. Reads at most ``limit``+1 bytes
    so a gzip bomb can never inflate into memory. Raises ValueError past the cap."""
    import gzip as _gzip
    import io as _io
    limit = _OTLP_MAX_DECOMPRESSED if limit is None else limit
    with _gzip.GzipFile(fileobj=_io.BytesIO(pb_data)) as gf:
        out = gf.read(limit + 1)
    if len(out) > limit:
        raise ValueError("gzip body exceeds decompressed size limit")
    return out


def _otlp_decode(pb_data, proto_msg, content_encoding=None, content_type=None):
    """Decode an OTLP/HTTP request body into ``proto_msg`` and return it.

    OpenLLMetry / traceloop-sdk and the OTel SDKs can export over three
    on-the-wire encodings that all map onto the same proto message:

      * ``application/x-protobuf``                 → ``ParseFromString`` (binary);
      * ``application/json``                       → ``json_format.Parse`` (OTLP/JSON);
      * any of the above wrapped in ``Content-Encoding: gzip``.

    We normalise here so the downstream ``_process_otlp_*`` mappers stay
    encoding-agnostic. Raises on malformed input (the caller turns that into a
    400, never a 500 stacktrace leak)."""
    ce = (content_encoding or "").lower()
    if "gzip" in ce:
        pb_data = _gunzip_bounded(pb_data)
    ct = (content_type or "").lower()
    if "application/json" in ct or "application/x-ndjson" in ct:
        from google.protobuf import json_format as _json_format
        # ignore_unknown_fields: OTLP/JSON producers occasionally add
        # forward-compat keys; tolerate them rather than 400 the whole batch.
        _json_format.Parse(
            pb_data.decode("utf-8") if isinstance(pb_data, (bytes, bytearray)) else pb_data,
            proto_msg,
            ignore_unknown_fields=True,
        )
    else:
        proto_msg.ParseFromString(pb_data)
    return proto_msg


def _otlp_request(pb_data, kind, content_encoding=None, content_type=None):
    """Decode an OTLP body for ``kind`` ('traces' | 'logs' | 'metrics').

    Issue #4781. ``opentelemetry-proto`` is behind the ``otel`` extra, so on a
    default install every OTLP POST used to answer 501 and the advertised
    receiver was simply off. Binary bodies still decode with protobuf exactly as
    before; JSON bodies go through the stdlib decoder in
    ``clawmetry.otlp_json``, which returns objects that duck-type the protobuf
    message API -- so ``_process_otlp_*`` and ``_otel_to_row`` run unchanged
    over either format and there is no second mapping path to drift.

    Raises ``OtlpProtobufUnavailable`` when the payload genuinely needs the
    extra (a protobuf body); the HTTP layer turns that into
    501 with the install hint. Malformed bodies still raise (caller -> 400).

    OTLP/JSON traces and logs go through the stdlib decoder even when protobuf
    IS installed. That is deliberate, and it fixes a silent corruption: protobuf
    JSON maps ``bytes`` fields from BASE64, but the OTLP/JSON spec overrides
    that for ``traceId`` / ``spanId`` / ``parentSpanId``, which are lowercase
    HEX. ``json_format.Parse`` therefore base64-decoded every id and we stored
    the garbage. Measured against a live dashboard: span id ``3333333333333333``
    persisted as ``df7df7df7df7df7df7df7df7``, and every id in the batch was
    mangled the same way, so ids never matched the user's own trace ids or any
    other backend they correlate with.
    """
    ct = (content_type or "").lower()
    if ("application/json" in ct or "application/x-ndjson" in ct) and kind in (
        "traces", "logs", "metrics",
    ):
        from clawmetry.otlp_json import decode as _json_decode
        return _json_decode(pb_data, kind, content_encoding=content_encoding)

    if _HAS_OTEL_PROTO:
        factories = {
            "traces": lambda: trace_service_pb2.ExportTraceServiceRequest(),
            "logs": lambda: logs_service_pb2.ExportLogsServiceRequest(),
            "metrics": lambda: metrics_service_pb2.ExportMetricsServiceRequest(),
        }
        factory = factories.get(kind)
        if factory is None:
            raise ValueError(f"unknown OTLP kind: {kind}")
        return _otlp_decode(pb_data, factory(), content_encoding, content_type)

    # No protobuf, and this is either a binary body or JSON metrics (whose
    # mapper still reaches into sum/gauge/histogram point types).
    from clawmetry.otlp_json import OtlpProtobufUnavailable

    raise OtlpProtobufUnavailable(
        "this payload needs opentelemetry-proto; OTLP/JSON traces, logs and "
        "metrics work without it (send Content-Type: application/json)"
    )


def _otlp_service_name_to_agent_type(service_name):
    """Map an OTLP resource ``service.name`` onto a ClawMetry ``agent_type``.

    OpenLLMetry-instrumented apps ("bring your own agent") set
    ``service.name`` to their app name (the traceloop-sdk default is
    ``"unknown_service"`` but most apps override it, e.g.
    ``"my-langchain-app"``). Without this every foreign span defaulted to
    ``agent_type="openclaw"`` and mis-bucketed under the OpenClaw runtime
    filter. We instead:

      * keep ``"openclaw"`` for OpenClaw / ClawMetry-known emitters (so existing
        OpenClaw OTLP flows are unchanged);
      * slugify any other name to ``[a-z0-9_]`` (``"my-langchain-app"`` →
        ``"my_langchain_app"``) so the app shows up as its OWN runtime/agent in
        the spans + ``/api/v1/*?runtime=`` (agent_type) views;
      * fall back to ``"custom"`` when ``service.name`` is absent or empty.

    Returns ``None`` to signal "no opinion" (caller keeps its own default) only
    when the input is not a string."""
    if service_name is None:
        return "custom"
    if not isinstance(service_name, str):
        return None
    raw = service_name.strip()
    if not raw:
        return "custom"
    low = raw.lower()
    # OpenClaw / ClawMetry-known emitters stay 'openclaw' so we don't break the
    # existing OpenClaw OTLP path or leak it out of the OpenClaw runtime view.
    if low in ("openclaw", "clawmetry", "clawmetry-sync", "clawmetry_sync",
               "openclaw-gateway", "openclaw_gateway", "unknown_service"):
        return "openclaw"
    import re as _re
    slug = _re.sub(r"[^a-z0-9_]+", "_", low).strip("_")
    return slug or "custom"


__version__ = "0.12.847"

# Extensions (Phase 2): import the plugin host now, but defer the actual
# load_plugins() call until after the Flask app is created below so we can
# hand each plugin the app and let it register blueprints. The host falls
# back to a no-op when the package itself is unavailable.
try:
    from clawmetry.extensions import emit as _ext_emit, load_plugins as _ext_load
except ImportError:

    def _ext_emit(event, payload=None):
        pass  # noqa

    def _ext_load(app=None):
        pass  # noqa


# NOTE: the Flask app is constructed ONCE, further down this module (search
# for ``app = Flask(``). A second, earlier construction used to live here and
# silently orphaned every plugin Blueprint: clawmetry-pro registered its
# routes on the early app, then the later ``app = Flask(...)`` replaced it and
# every pro-only endpoint (nemoclaw, selfevolve, assets, compliance, ...)
# 404'd on licensed installs while the OSS 402 stubs skipped registration
# because ``clawmetry_pro.is_loaded()`` was True. ``_ext_load(app)`` must be
# invoked on the app instance that actually serves — it is called immediately
# after the real construction below. Guarded by
# tests/test_plugin_load_on_served_app.py.

# ── Cross-platform helpers ──────────────────────────────────────────────
import re as _re
import tempfile as _tempfile
import platform as _platform


# _grep_log_file, _tail_lines, _get_log_dirs moved to helpers/logs.py (re-exported above)


# _detect_host_hardware moved to helpers/hardware.py (re-exported above)


_CURRENT_PLATFORM = _platform.system().lower()
# ── End cross-platform helpers ──────────────────────────────────────────

# ── Configuration (auto-detected, overridable via CLI/env) ──────────────
MC_URL = os.environ.get("MC_URL", "")  # Optional Mission Control URL, empty = disabled
WORKSPACE = None
MEMORY_DIR = None
LOG_DIR = None
SESSIONS_DIR = None
USER_NAME = None
GATEWAY_URL = None  # e.g. http://localhost:18789
GATEWAY_TOKEN = None  # Bearer token for /tools/invoke
# Removed: a fixed UTC+1 with no DST handling. It was wrong for Europe half
# the year and for everyone else all year, and it made this file's cost
# windows disagree with every other cost surface. Use
# clawmetry.cost_windows.now_local() for windows and .astimezone() for
# display. Guarded by tests/test_cost_windows_one_definition.py.
# SSE_MAX_SECONDS moved to helpers/streams.py (re-exported above)
# Stream-slot caps + state moved to helpers/streams.py (re-exported above)
# _active_brain_stream_clients moved to helpers/streams.py
EXTRA_SERVICES = []  # List of {'name': str, 'port': int} from --monitor-service flags

# ── Multi-Node Fleet Configuration ─────────────────────────────────────
FLEET_API_KEY = os.environ.get("CLAWMETRY_FLEET_KEY", "")
FLEET_DB_PATH = None  # Set via CLI or auto-detected
FLEET_NODE_TIMEOUT = 300  # seconds before node is considered offline

# ── Budget & Alert Configuration ───────────────────────────────────────
_budget_paused = False
_budget_paused_at = 0
_budget_paused_reason = ""
_budget_alert_cooldowns = {}  # rule_id -> last_fired_timestamp
_AGENT_DOWN_SECONDS = 300  # 5 min with no OTLP data = agent down alert
_ALERTS_CONFIG_FILE = os.path.expanduser("~/.openclaw/clawmetry-alerts.json")
_security_posture_hash = ""
# Token velocity alert thresholds (GH#313)
_VELOCITY_TOKENS_PER_2MIN = 10000  # tokens in any 2-minute window
_VELOCITY_CONSECUTIVE_TOOLS = 20  # consecutive tool calls without human turn
_VELOCITY_COST_PER_MIN = 0.10  # USD/min cost rate
# Error-spike alert thresholds (GH#954)
_ERROR_SPIKE_THRESHOLD = int(os.environ.get("ERROR_SPIKE_THRESHOLD", "3"))
_ERROR_SPIKE_WINDOW_SEC = int(os.environ.get("ERROR_SPIKE_WINDOW_SEC", "60"))

# ── OTLP Metrics Store ─────────────────────────────────────────────────
METRICS_FILE = None  # Set via CLI/env, defaults to {WORKSPACE}/.clawmetry-metrics.json
_metrics_lock = threading.Lock()
_otel_last_received = 0  # timestamp of last OTLP data received

metrics_store = {
    "tokens": [],  # [{timestamp, input, output, total, model, channel, provider}]
    "cost": [],  # [{timestamp, usd, model, channel, provider}]
    "runs": [],  # [{timestamp, duration_ms, model, channel}]
    "messages": [],  # [{timestamp, channel, outcome, duration_ms}]
    "webhooks": [],  # [{timestamp, channel, type}]
    "queues": [],  # [{timestamp, channel, depth}]
}
MAX_STORE_ENTRIES = 10_000
STORE_RETENTION_DAYS = 14


            # Continue running despite errors


# ── Multi-Node Fleet Database ───────────────────────────────────────────
import sqlite3 as _sqlite3

_fleet_db_lock = threading.Lock()


# ── Budget & Alert Database ────────────────────────────────────────────


# ── DuckDB cost fallback (issue #1404) ────────────────────────────────
# OTLP is the *cheap* aggregation path: ``metrics_store["cost"]`` is a
# pre-summed in-process buffer the evaluator reads in O(N) without touching
# DuckDB. But the typical OSS install never wires an OTLP exporter (it's
# explicitly optional — ``pip install clawmetry[otel]`` is opt-in), so on
# the vast majority of nodes that buffer stays empty and threshold rules
# silently never fire on real spend.
#
# This helper recomputes daily/weekly/monthly spend by aggregating the
# billable-turn rows the sync daemon already persists into DuckDB. We only
# invoke it when OTLP is empty/stale (see ``_otel_cost_is_fresh``) so
# OTLP-fed installs keep their fast path.
_OTLP_FRESH_WINDOW_SEC = 300  # 5 min — matches AGENT_DOWN threshold


def _otel_cost_is_fresh(since_ts: float) -> bool:
    """True iff ``metrics_store['cost']`` has at least one entry timestamped
    within the last ``_OTLP_FRESH_WINDOW_SEC`` seconds (i.e. an OTLP exporter
    is actively pushing cost data). When False, the evaluator falls back to
    DuckDB so threshold rules can still fire on real OpenClaw spend.

    ``since_ts`` is the earliest period start we care about (e.g. today_start
    for daily rules). Even one fresh OTLP row covering the period means the
    in-memory buffer is the source of truth — DuckDB fallback is unnecessary.
    """
    cutoff = time.time() - _OTLP_FRESH_WINDOW_SEC
    with _metrics_lock:
        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            if ts >= cutoff and ts >= since_ts:
                return True
    return False


def _duckdb_cost_since(since_iso: str) -> Optional[float]:
    """Sum billable-turn USD over the ``events`` table since ``since_iso``.

    Reuses the v3-aware helpers from ``clawmetry.local_store`` so every
    OpenClaw envelope shape (Anthropic-SDK ``message``, v3 ``assistant``,
    ``subagent:assistant``, slim ``model.completed``) is covered. Never
    raises — returns 0.0 on any error so the evaluator still gets a number.

    Issue #1404: without this, ~99% of OSS installs see a zero spend metric
    inside the alert evaluator and no real-spend rule ever fires.

    Issue #1453: route through the daemon-proxy (memory
    ``feedback_daemon_proxy_pattern.md``) so /api/budget/status doesn't
    block on the daemon's exclusive DuckDB writer lock under the standard
    launchd/systemd install. Direct ``get_store()`` was taking 2.5 s per
    call on a real install with sync daemon writing — three calls (daily /
    weekly / monthly) compounded to 7-10 s p50 for the endpoint, stalling
    the Budget panel on every dashboard load. Fall back to a read-only
    direct open for single-process boots (tests, dev mode) where the
    daemon proxy isn't running.
    """
    # 1. Daemon-proxy fast path — cross-process HTTP call into the sync
    #    daemon's local_server, which holds the DuckDB writer lock. Returns
    #    None when the daemon isn't discoverable (single-process boot).
    rows = None
    try:
        from routes.local_query import local_store_via_daemon
        rows = local_store_via_daemon("query_aggregates", since=since_iso)
    except Exception:
        rows = None
    # 2. Read-only direct fallback — tests, dev mode, daemon-down boots.
    if rows is None:
        try:
            from clawmetry import local_store
            store = local_store.get_store(read_only=True)
            rows = store.query_aggregates(since=since_iso)
        except Exception:
            # A read that FAILED is not a window that cost $0.00. Returning
            # 0.0 here made a transient daemon-proxy timeout or writer-lock
            # contention indistinguishable from a genuinely idle window, and
            # the caller then published that zero as fact. Signal absence.
            return None
    if rows is None:
        return None
    total = 0.0
    for r in rows or []:
        try:
            total += float(r.get("cost_usd") or 0)
        except (TypeError, ValueError):
            continue
    return total


def _get_budget_status():
    """Calculate current spending vs budget limits.

    Priority order (issue #1404 fix):
      1. If OTLP cost is fresh (any entry within the last 5 min that also
         falls inside the daily window), use ``metrics_store['cost']``.
      2. Else, fall back to a DuckDB aggregate over ``events.cost_usd`` for
         the same time windows. Installs without an OTLP exporter (the
         common case) finally get a real ``daily_spent`` number — threshold
         rules can fire on real spend instead of silently never tripping.
    """
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    config = _get_budget_config()
    now = time.time()
    # Same calendar-local windows every other cost surface uses. Sampling
    # datetime.now() three separate times could also straddle midnight.
    from clawmetry.cost_windows import window_start_epochs

    today_start, week_start, month_start = window_start_epochs()

    daily_spent = 0.0
    weekly_spent = 0.0
    monthly_spent = 0.0
    cost_source = "otlp"

    with _metrics_lock:
        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            usd = entry.get("usd", 0)
            if ts >= month_start:
                monthly_spent += usd
                if ts >= week_start:
                    weekly_spent += usd
                    if ts >= today_start:
                        daily_spent += usd

    # Issue #1404: when no OTLP exporter is wired (the common OSS case), the
    # in-memory buffer above stays empty and ``daily_spent`` is locked at 0
    # — alert threshold rules then NEVER fire on real spend. Detect that
    # state (no fresh OTLP row covering the daily window) and recompute
    # from DuckDB, which the sync daemon populates for every OpenClaw turn
    # regardless of OTLP configuration.
    if daily_spent == 0.0 and not _otel_cost_is_fresh(today_start):
        try:
            daily_iso   = datetime.fromtimestamp(today_start, tz=timezone.utc).isoformat()
            weekly_iso  = datetime.fromtimestamp(week_start,  tz=timezone.utc).isoformat()
            monthly_iso = datetime.fromtimestamp(month_start, tz=timezone.utc).isoformat()
            duck_daily   = _duckdb_cost_since(daily_iso)
            duck_weekly  = _duckdb_cost_since(weekly_iso)
            duck_monthly = _duckdb_cost_since(monthly_iso)
            # These are three INDEPENDENT reads. Pre-fix each one degraded to
            # 0.0 on failure, so a transient timeout on the daily call while
            # the monthly call succeeded published daily=$0.00 next to a real
            # month -- a triple mixing fact and failure, flipping back on the
            # next poll. That is the "numbers change every few seconds" a
            # customer reported on 2026-08-22. Promote all three or none.
            _duck = (duck_daily, duck_weekly, duck_monthly)
            _duck_ok = all(v is not None for v in _duck)
            # Only switch sources when DuckDB has *something* to report.
            # An empty store on a brand-new install should look the same as
            # an empty OTLP buffer (daily_spent=0), not crash the evaluator.
            if _duck_ok and any(v > 0 for v in _duck):
                daily_spent   = duck_daily
                weekly_spent  = duck_weekly
                monthly_spent = duck_monthly
                cost_source = "duckdb"
        except Exception:
            # Never crash the budget path — graceful fallback per CLAUDE.md.
            pass

    daily_limit = config.get("daily_limit", 0)
    weekly_limit = config.get("weekly_limit", 0)
    monthly_limit = config.get("monthly_limit", 0)

    return {
        "daily_spent": round(daily_spent, 4),
        "weekly_spent": round(weekly_spent, 4),
        "monthly_spent": round(monthly_spent, 4),
        "daily_limit": daily_limit,
        "weekly_limit": weekly_limit,
        "monthly_limit": monthly_limit,
        "daily_pct": round(
            (daily_spent / daily_limit * 100) if daily_limit > 0 else 0, 1
        ),
        "weekly_pct": round(
            (weekly_spent / weekly_limit * 100) if weekly_limit > 0 else 0, 1
        ),
        "monthly_pct": round(
            (monthly_spent / monthly_limit * 100) if monthly_limit > 0 else 0, 1
        ),
        "paused": _budget_paused,
        "paused_at": _budget_paused_at,
        "paused_reason": _budget_paused_reason,
        "auto_pause_enabled": config.get("auto_pause_enabled", False),
        "auto_pause_threshold_usd": config.get("auto_pause_threshold_usd", 0),
        "auto_pause_action": config.get("auto_pause_action", "pause"),
        "warning_threshold_pct": config.get("warning_threshold_pct", 80),
        # Issue #1404: surface which path computed daily_spent so the alerts
        # accuracy harness can verify the DuckDB fallback fired on no-OTLP
        # installs. "otlp" = metrics_store buffer (fast), "duckdb" = events
        # aggregate fallback. Both are accurate; the field is for diagnostics.
        "cost_source": cost_source,
    }


# ── Hard budget cap (issue #555 — Phase 1) ─────────────────────────────
#
# ``_is_over_cap(scope)`` compares the configured ``<scope>_cap_usd`` against
# the matching spend bucket from ``_get_budget_status()``. Scopes:
#   - "daily"   → ``daily_cap_usd``   vs ``daily_spent``
#   - "monthly" → ``monthly_cap_usd`` vs ``monthly_spent``
# Per-session accounting (``session_cap_usd`` vs running session spend)
# lands in Phase 2 alongside the gateway-RPC pause path.
#
# Returns ``(tripped: bool, info: dict)``. ``info`` always includes ``cap``
# and ``spent`` so callers can render a banner like "$10.50 of $10 cap".
# A cap of ``0`` or missing/non-numeric value is treated as "no cap
# configured" and returns ``(False, ...)`` — never trip on the default.
def _is_over_cap(scope: str):
    """Return whether the configured cap for ``scope`` has been hit.

    Phase 1: ``daily`` and ``monthly`` scopes only. ``session`` is
    accepted to keep the API stable (returns ``(False, ...)``) so the
    Phase 2 per-session work doesn't need a signature change.
    """
    scope = (scope or "").strip().lower()
    if scope not in ("daily", "monthly", "session"):
        return False, {"scope": scope, "cap": 0.0, "spent": 0.0,
                       "error": "unknown scope"}
    try:
        cfg = _get_budget_config()
        status = _get_budget_status()
    except Exception:
        # Never crash the budget check — fall back to "not over cap".
        return False, {"scope": scope, "cap": 0.0, "spent": 0.0}
    try:
        cap = float(cfg.get(f"{scope}_cap_usd", 0) or 0)
    except (TypeError, ValueError):
        cap = 0.0
    if scope == "session":
        # Phase 2: aggregate per-session spend from the sessions table.
        # For now we don't have a per-session running total wired into
        # the budget path, so return False with the cap echoed back.
        return False, {"scope": "session", "cap": cap, "spent": 0.0}
    spent = float(status.get(f"{scope}_spent", 0) or 0)
    if cap <= 0:
        # 0 (or unset) means "no cap configured" — never trip.
        return False, {"scope": scope, "cap": 0.0, "spent": spent}
    return spent >= cap, {"scope": scope, "cap": cap, "spent": spent}


# ── Pro-tier gate (issue #1168) ────────────────────────────────────────
#
# Per-agent budget LIMITS are OSS table-stakes (cost control). Per-agent
# alert DISPATCH (Telegram/Slack) is the Cloud-Pro value-add — see
# ``project_alerts_pro_feature.md``: Alerts Center is Cloud-Pro, OSS sees
# a soft paywall, Cloud-Free sees an upgrade CTA. Centralised here so the
# rule is applied consistently from any per-feature dispatch path.
#
# Liveness rule used by the OSS daemon (no async cloud RPC at fire-time):
#   * Signed self-hosted license on disk with a Pro-equivalent tier   → pro
#     (``pro``/``cloud_pro``/``trial``/``enterprise``, source=license)
#   * No ``cm_`` token on disk (and no signed license)                → NOT pro
#   * Has ``cm_`` token + cached plan="cloud_pro"|"pro"|"trial"       → pro
#   * Has ``cm_`` token but no cached plan, or plan="free"            → NOT pro
#
# The cached plan is populated by the cloud-CTA status route the dashboard
# already polls; we read it best-effort and fall back to the conservative
# "not pro" answer so we never accidentally fire paid dispatch on a free
# node. This means Cloud-Free users see the same paywall OSS users do
# until they upgrade, which matches the strategic split.
#
# The self-hosted signed-license branch closes the gap called out in
# #3755 (alerts + approvals): a $190/node/yr licensee with no ``cm_``
# cloud token is still on a paid tier — the entitlements resolver
# reports ``source == "license"`` and a Pro-equivalent ``tier`` — so
# they get the same paid-dispatch surface Cloud-Pro users do (auto-
# pause, per-agent Telegram alert fan-out, ...). Starter self-hosted
# keys (TIER_CLOUD_STARTER) stay in the free branch: Starter does not
# unlock Pro-only features and neither should this gate.
_PRO_EQUIVALENT_TIERS = frozenset(
    {"pro", "cloud_pro", "trial", "enterprise"}
)


def _license_grants_pro():
    """True iff the entitlement resolver reports a signed self-hosted
    license on a Pro-equivalent tier.

    Fail-closed: any exception (entitlements module unimportable, resolver
    raises, unexpected shape) returns False so a flaky lookup never leaks a
    paid dispatch path onto a free node.
    """
    try:
        from clawmetry import entitlements as _ent

        ent = _ent.get_entitlement()
        if getattr(ent, "source", "") != "license":
            return False
        return str(getattr(ent, "tier", "")).strip().lower() in _PRO_EQUIVALENT_TIERS
    except Exception:
        return False


def _is_pro_user():
    """Best-effort, fail-closed Pro check used to gate paid dispatch.

    Returns True when either signal is present:
      1. A signed self-hosted license on disk resolves to a Pro-equivalent
         tier (``pro`` / ``cloud_pro`` / ``trial`` / ``enterprise``,
         ``source == "license"``), OR
      2. A ``cm_`` cloud token is on disk AND the cached plan tier is one
         of ``cloud_pro`` / ``pro`` / ``trial``.

    Any failure (no token, missing cache, exception) returns False so we
    never leak a Cloud-Pro dispatch path onto a free / OSS-only node.
    """
    if _license_grants_pro():
        return True
    try:
        token = _read_cloud_token() or ""
    except Exception:
        token = ""
    if not isinstance(token, str) or not token.startswith("cm_"):
        return False
    # Best-effort plan cache lookup. Populated by the cloud-CTA status
    # route on each /api/cloud-cta/status hit (see routes/overview.py).
    plan = ""
    try:
        cache = globals().get("_cloud_plan_cache") or {}
        plan = str(cache.get("plan") or "").strip().lower()
    except Exception:
        plan = ""
    if plan in ("cloud_pro", "pro", "trial"):
        return True
    return False


# ── Auto-pause Pro gate (issue #1169) ───────────────────────────────────
# Auto-pause-on-100% (a hard kill switch on the gateway) is a Cloud-Pro
# feature, not OSS table-stakes. OSS / Cloud-Free nodes still see the
# in-app budget banner + alert-history row when limits trip, but the
# gateway-stop fan-out is gated. This keeps the warning-only path free
# (a useful teaser) without giving away the FinOps-grade enforcement
# story enterprises pay for. ``_pause_gateway()`` itself is still safe
# to call from manual buttons (``/api/budget/pause``); this gate only
# guards the *automatic* trip wires inside ``_budget_check`` and the
# alert-daemon sweep.


def _auto_pause_allowed():
    """Fail-closed gate for *automatic* gateway pause.

    Returns True only for Cloud-Pro users. Manual pause buttons bypass
    this gate (the user already made the call). Failures default to
    False so a flaky cache never leaks a paid enforcement path onto a
    free node.
    """
    try:
        return bool(_is_pro_user())
    except Exception:
        return False


# ── Per-agent budgets (issue #951) ─────────────────────────────────────
#
# Per-agent overrides live in the DuckDB ``agent_budgets`` table (see
# ``clawmetry/local_store.py``) so they survive process restarts and ride
# the same heartbeat-piggyback relay as the rest of the local store.
# ``_get_agent_budget`` returns ``None`` when no override is present —
# callers fall back to the global ``daily_limit`` / ``monthly_limit``.
#
# Tiered alerts: the in-memory ``_budget_agent_tier_state`` dict tracks
# {(agent_id, period): "warning" | "critical" | None} for the *current*
# period bucket (today / this month). Once we fire a warning we don't fire
# it again until the period resets; once we fire critical we never
# re-fire warning for the same period. This is the dedup contract the
# spec asks for: same threshold, same period, same agent → one alert.


# (agent_id, period, period_key) -> tier last fired. period_key is the
# date string for the current bucket so the slot auto-resets at midnight /
# month-start without an explicit cron.
_budget_agent_tier_state: dict[tuple, str] = {}


def _get_agent_budget(agent_id):
    """Read one per-agent budget override from the local store. Returns
    ``None`` when the local store isn't available or the agent has no
    override row — callers fall back to global limits."""
    if not agent_id:
        return None
    try:
        from clawmetry import local_store

        store = local_store.get_store()
        return store.get_agent_budget(agent_id)
    except Exception:
        return None


def _list_agent_budgets():
    """Return all per-agent overrides as a list. Returns [] on any error."""
    try:
        from clawmetry import local_store

        store = local_store.get_store()
        return store.query_agent_budgets(limit=500)
    except Exception:
        return []


def _set_agent_budget(agent_id, daily_limit_usd=None, monthly_limit_usd=None):
    """Write a per-agent override row. Returns True on success."""
    if not agent_id:
        return False
    try:
        from clawmetry import local_store

        store = local_store.get_store()
        store.set_agent_budget(
            agent_id,
            daily_limit_usd=daily_limit_usd,
            monthly_limit_usd=monthly_limit_usd,
        )
        return True
    except Exception:
        return False


def _delete_agent_budget(agent_id):
    """Remove a per-agent override row. Returns 1 on delete, 0 when missing."""
    if not agent_id:
        return 0
    try:
        from clawmetry import local_store

        store = local_store.get_store()
        return store.delete_agent_budget(agent_id)
    except Exception:
        return 0


def _agent_spend_for_period(agent_id, period_start):
    """Sum cost-store USD entries for one agent since ``period_start``.

    Cost entries written without an ``agent`` key default to ``"main"``,
    matching how the rest of the dashboard names the primary agent."""
    total = 0.0
    with _metrics_lock:
        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            if ts < period_start:
                continue
            ent_agent = entry.get("agent", "main") or "main"
            if ent_agent != agent_id:
                continue
            total += float(entry.get("usd", 0) or 0)
    return total


def _period_bounds():
    """Return (today_start_ts, today_key, month_start_ts, month_key)."""
    now_dt = datetime.now()
    today_start = now_dt.replace(
        hour=0, minute=0, second=0, microsecond=0
    ).timestamp()
    today_key = now_dt.strftime("%Y-%m-%d")
    month_start = now_dt.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).timestamp()
    month_key = now_dt.strftime("%Y-%m")
    return today_start, today_key, month_start, month_key


def _get_agent_budget_status(agent_id):
    """Return per-agent budget status dict for the API. Combines per-agent
    override (when present) with global fallback and current MTD/daily
    spend. Always returns a populated dict — never ``None``."""
    config = _get_budget_config()
    override = _get_agent_budget(agent_id) or {}
    today_start, _, month_start, _ = _period_bounds()
    daily_spent = _agent_spend_for_period(agent_id, today_start)
    monthly_spent = _agent_spend_for_period(agent_id, month_start)

    def _effective(override_val, global_key):
        if override_val is not None and override_val > 0:
            return float(override_val), "agent"
        gv = config.get(global_key, 0) or 0
        try:
            gv = float(gv)
        except (TypeError, ValueError):
            gv = 0.0
        return gv, ("global" if gv > 0 else "none")

    daily_limit, daily_source = _effective(
        override.get("daily_limit_usd"), "daily_limit"
    )
    monthly_limit, monthly_source = _effective(
        override.get("monthly_limit_usd"), "monthly_limit"
    )

    def _pct(spent, limit):
        return round((spent / limit * 100), 1) if limit > 0 else 0.0

    def _status(pct):
        if pct >= 100:
            return "critical"
        if pct >= 80:
            return "warning"
        if pct >= 50:
            return "ok"
        return "ok"

    daily_pct = _pct(daily_spent, daily_limit)
    monthly_pct = _pct(monthly_spent, monthly_limit)
    overall_pct = max(daily_pct, monthly_pct)

    return {
        "agent_id": agent_id,
        "daily_limit": daily_limit,
        "daily_limit_usd": daily_limit,
        "daily_limit_source": daily_source,
        "daily_spent": round(daily_spent, 4),
        "daily_pct": daily_pct,
        "monthly_limit": monthly_limit,
        "monthly_limit_usd": monthly_limit,
        "monthly_limit_source": monthly_source,
        "monthly_spent": round(monthly_spent, 4),
        "mtd_spend": round(monthly_spent, 4),
        "monthly_pct": monthly_pct,
        "status": _status(overall_pct),
        "has_override": bool(override),
    }


def _budget_check_for_agent(agent_id, *, auto_pause_enabled=None,
                            warning_pct=80, pause_pct=100):
    """Tiered-alert check for one agent. Honours dedup-per-period-per-tier.

    Returns True when a critical (100%) breach fired AND auto-pause is
    enabled — caller (``_budget_check``) treats that as a signal to pause
    the gateway. Returns False otherwise."""
    global _budget_agent_tier_state
    override = _get_agent_budget(agent_id)
    if not override:
        return False
    config = _get_budget_config()
    if auto_pause_enabled is None:
        auto_pause_enabled = config.get("auto_pause_enabled", False)
    today_start, today_key, month_start, month_key = _period_bounds()
    pause_triggered = False

    # Issue #1168: per-agent LIMITS are OSS table-stakes, but per-agent
    # Telegram dispatch is a Cloud-Pro feature. OSS / Cloud-Free nodes
    # still get the in-app banner + history row (so the user sees the
    # breach and the bar paints red), they just don't get the paid
    # Telegram fan-out. The UI surfaces an inline "Upgrade for Telegram
    # alerts" link on the per-agent panel.
    _pro = False
    try:
        _pro = bool(_is_pro_user())
    except Exception:
        _pro = False
    _agent_alert_channels = ["banner", "telegram"] if _pro else ["banner"]

    for period, period_start, period_key, override_key, global_key in (
        ("daily", today_start, today_key, "daily_limit_usd", "daily_limit"),
        ("monthly", month_start, month_key, "monthly_limit_usd", "monthly_limit"),
    ):
        limit = override.get(override_key)
        if limit is None or limit <= 0:
            # Fall back to global limit for this period if not overridden.
            try:
                limit = float(config.get(global_key, 0) or 0)
            except (TypeError, ValueError):
                limit = 0.0
            if limit <= 0:
                continue
        spent = _agent_spend_for_period(agent_id, period_start)
        pct = (spent / limit * 100) if limit > 0 else 0
        slot_key = (agent_id, period, period_key)
        prior_tier = _budget_agent_tier_state.get(slot_key)

        # Critical (>=100%) — supersedes warning. Dedup: once per period.
        if pct >= pause_pct:
            if prior_tier != "critical":
                _budget_agent_tier_state[slot_key] = "critical"
                _fire_alert(
                    rule_id=f"budget_agent_{agent_id}_{period}_critical_{period_key}",
                    alert_type="budget.critical",
                    message=(
                        f"BUDGET CRITICAL: agent '{agent_id}' {period} spend "
                        f"${spent:.2f} of ${limit:.2f} (100%) limit"
                    ),
                    channels=_agent_alert_channels,
                )
                if auto_pause_enabled:
                    pause_triggered = True
            continue

        # Warning (>=80% but <100%). Dedup: only fire when crossing from
        # nothing → warning (don't fire if already at critical, can't
        # happen here since we continued above, but defensive).
        if pct >= warning_pct:
            if prior_tier not in ("warning", "critical"):
                _budget_agent_tier_state[slot_key] = "warning"
                _fire_alert(
                    rule_id=f"budget_agent_{agent_id}_{period}_warning_{period_key}",
                    alert_type="budget.warning",
                    message=(
                        f"Budget warning: agent '{agent_id}' {period} spend "
                        f"${spent:.2f} is {pct:.0f}% of ${limit:.2f} limit"
                    ),
                    channels=_agent_alert_channels,
                )

    return pause_triggered


def _budget_check():
    """Check budget limits and fire alerts/auto-pause if needed."""
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    if _budget_paused:
        return
    now = time.time()
    config = _get_budget_config()
    status = _get_budget_status()
    warning_pct = config.get("warning_threshold_pct", 80)
    pause_pct = config.get("auto_pause_threshold_pct", 100)

    # ── Per-agent budgets first (issue #951) ────────────────────────────
    # We collect the unique set of agents that have either spent something
    # in the cost store today/this-month OR have an override configured.
    # Either source can trip a tier, so we union them.
    agents_to_check = set()
    try:
        for ov in _list_agent_budgets():
            aid = ov.get("agent_id")
            if aid:
                agents_to_check.add(aid)
    except Exception:
        pass
    try:
        with _metrics_lock:
            for entry in metrics_store["cost"]:
                agents_to_check.add(entry.get("agent", "main") or "main")
    except Exception:
        pass
    # Issue #1169: auto-pause is a Cloud-Pro feature. Free / OSS users
    # still get the breach alert (banner + history row) via the regular
    # tier-check, but the gateway-stop fan-out is gated. We force
    # ``auto_pause_enabled=False`` into the per-agent check so it never
    # returns the "pause" signal, then re-fire a single banner alert
    # with an upsell message so the user knows enforcement is paused.
    _auto_pause_cfg = bool(config.get("auto_pause_enabled", False))
    _auto_pause_ok = _auto_pause_allowed() if _auto_pause_cfg else True
    for agent_id in agents_to_check:
        try:
            if _budget_check_for_agent(
                agent_id,
                auto_pause_enabled=_auto_pause_cfg and _auto_pause_ok,
                warning_pct=warning_pct,
                pause_pct=pause_pct,
            ):
                _budget_paused = True
                _budget_paused_at = time.time()
                _budget_paused_reason = (
                    f"Agent '{agent_id}' budget exceeded; gateway paused."
                )
                _pause_gateway()
                return
        except Exception:
            # Never let one agent's check kill the whole sweep.
            continue
    if _auto_pause_cfg and not _auto_pause_ok:
        # Surface the gate so the user understands why enforcement did
        # not fire even though their toggle is on. Banner-only; no
        # Telegram fan-out (that is also Pro).
        _fire_alert(
            rule_id="budget_autopause_pro_required",
            alert_type="budget.upsell",
            message=(
                "Auto-pause is a Cloud Pro feature. Budget breaches "
                "still alert here, but the gateway will keep running "
                "until you upgrade. Start a 7-day free trial at "
                "https://app.clawmetry.com/upgrade"
            ),
            channels=["banner"],
        )

    # Check each period (global)
    for period in ["daily", "weekly", "monthly"]:
        limit = config.get(f"{period}_limit", 0)
        if limit <= 0:
            continue
        spent = status[f"{period}_spent"]
        pct = (spent / limit * 100) if limit > 0 else 0

        if period in ("daily", "weekly") and spent >= limit:
            rule_id = f"webhook_{period}_threshold_breached"
            last_fired = _budget_alert_cooldowns.get(rule_id, 0)
            if now - last_fired >= 900:
                _budget_alert_cooldowns[rule_id] = now
                _dispatch_configured_webhooks(
                    f"{period}_threshold_breached",
                    {
                        "type": f"{period}_threshold_breached",
                        "agent": "main",
                        "cost_usd": round(spent, 4),
                        "threshold": round(limit, 4),
                        "timestamp": now,
                        "message": f"{period.capitalize()} cost threshold breached: ${spent:.2f} / ${limit:.2f}",
                    },
                )

        # Warning alert
        if pct >= warning_pct and pct < pause_pct:
            _fire_alert(
                rule_id=f"budget_{period}_warning",
                alert_type="threshold",
                message=f"Budget warning: {period} spending ${spent:.2f} is {pct:.0f}% of ${limit:.2f} limit",
                channels=["banner", "telegram"],
            )

        # Auto-pause (issue #1169: Pro-gated; Free users still get the
        # banner alert, but the gateway is left running.)
        if pct >= pause_pct and config.get("auto_pause_enabled", False):
            if not _auto_pause_ok:
                _fire_alert(
                    rule_id=f"budget_{period}_exceeded_upsell",
                    alert_type="budget.upsell",
                    message=(
                        f"BUDGET EXCEEDED: {period} spending ${spent:.2f} "
                        f"is over ${limit:.2f}. Auto-pause is a Cloud Pro "
                        f"feature. Start a 7-day free trial at "
                        f"https://app.clawmetry.com/upgrade"
                    ),
                    channels=["banner"],
                )
                continue
            _budget_paused = True
            _budget_paused_at = time.time()
            _budget_paused_reason = (
                f"{period.capitalize()} budget exceeded: ${spent:.2f} / ${limit:.2f}"
            )
            _fire_alert(
                rule_id=f"budget_{period}_exceeded",
                alert_type="threshold",
                message=f"BUDGET EXCEEDED: {period} spending ${spent:.2f} exceeds ${limit:.2f} limit. Gateway paused.",
                channels=["banner", "telegram"],
            )
            _pause_gateway()
            return


def _pause_gateway():
    """Attempt to pause the OpenClaw gateway."""
    # Try gateway stop command
    try:
        subprocess.run(["openclaw", "gateway", "stop"], timeout=10, capture_output=True)
        return
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    # Fallback: SIGTERM to gateway process (Unix only)
    # Note: SIGSTOP (19) freezes process indefinitely with TCP held open.
    if sys.platform != 'win32':
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw-gateway"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for pid in result.stdout.strip().split("\n"):
                pid = pid.strip()
                if pid:
                    os.kill(int(pid), 15)  # SIGTERM
                    return
        except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
            pass  # process gone or can't access


def _resume_gateway():
    """Resume the OpenClaw gateway after budget pause."""
    global _budget_paused, _budget_paused_at, _budget_paused_reason
    # Try gateway start command
    try:
        subprocess.run(
            ["openclaw", "gateway", "start"], timeout=10, capture_output=True
        )
    except (FileNotFoundError, subprocess.TimeoutExpired, subprocess.SubprocessError):
        pass
    # Also try SIGCONT (Unix only)
    if sys.platform != "win32":
        try:
            result = subprocess.run(
                ["pgrep", "-f", "openclaw-gateway"],
                capture_output=True,
                text=True,
                timeout=3,
            )
            for pid in result.stdout.strip().split("\n"):
                pid = pid.strip()
                if pid:
                    os.kill(int(pid), 18)  # SIGCONT
        except Exception:
            pass
    _budget_paused = False
    _budget_paused_at = 0
    _budget_paused_reason = ""


def _url_safe_for_external_request(url):
    """Return (ok, reason) for an outbound webhook URL.

    SSRF guard: a user-supplied webhook must reach an EXTERNAL service, never
    the cloud metadata endpoint (169.254.169.254), the local gateway, or any
    internal host. Rejects non-http(s) schemes and any host that resolves to a
    loopback / link-local / private / reserved / multicast / unspecified IP.
    """
    import ipaddress as _ip
    import socket as _socket
    from urllib.parse import urlparse as _urlparse
    try:
        p = _urlparse(url)
    except Exception:
        return False, "unparseable url"
    if p.scheme not in ("http", "https"):
        return False, "scheme must be http or https"
    host = p.hostname
    if not host:
        return False, "missing host"
    try:
        port = p.port or (443 if p.scheme == "https" else 80)
        infos = _socket.getaddrinfo(host, port, proto=_socket.IPPROTO_TCP)
    except Exception:
        return False, "dns resolution failed"
    for info in infos:
        ip = info[4][0]
        try:
            addr = _ip.ip_address(ip)
        except ValueError:
            return False, "unparseable resolved ip"
        if (addr.is_loopback or addr.is_link_local or addr.is_private
                or addr.is_reserved or addr.is_multicast or addr.is_unspecified):
            return False, f"blocked internal address {ip}"
    return True, ""


_velocity_cache = {"ts": 0, "result": None, "mtimes": {}}

def _compute_velocity_status():
    """Compute real-time token velocity across all active sessions.

    Returns a dict with:
      - active: bool (True if any threshold exceeded)
      - tokensIn2Min: total tokens in last 2 minutes across all sessions
      - costPerMin: estimated USD/min cost rate
      - maxConsecutiveTools: highest consecutive-tool-call chain found
      - triggeringSession: session ID with highest burn rate (if any)
      - reasons: list of human-readable trigger reasons
    """
    now = time.time()
    # Cache for 30 seconds to avoid re-reading files
    if _velocity_cache["result"] and (now - _velocity_cache["ts"]) < 30:
        return _velocity_cache["result"]
    window_2min = now - 120

    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    total_tokens_2min = 0.0
    max_consecutive_tools = 0
    triggering_session = None
    highest_tpm = 0.0

    try:
        if os.path.isdir(sessions_dir):
            candidates = sorted(
                [
                    f
                    for f in os.listdir(sessions_dir)
                    if f.endswith(".jsonl") and "deleted" not in f
                ],
                key=lambda f: os.path.getmtime(os.path.join(sessions_dir, f)),
                reverse=True,
            )[:20]  # check 20 most recent sessions
            for fname in candidates:
                fpath = os.path.join(sessions_dir, fname)
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > 300:  # skip sessions inactive > 5 min
                        continue
                    tokens_2min = 0.0
                    consecutive_tools = 0
                    max_consecutive_in_session = 0
                    with open(fpath, "r", errors="replace") as f:
                        lines = list(deque(f, maxlen=2000))
                    for line in lines:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue
                        ts = _json_ts_to_epoch(
                            obj.get("timestamp")
                            or obj.get("time")
                            or obj.get("created_at")
                        )
                        if not ts:
                            continue
                        # Count consecutive tool calls (any tool_use role)
                        msg = (
                            obj.get("message", {})
                            if isinstance(obj.get("message"), dict)
                            else {}
                        )
                        role = msg.get("role", "") or obj.get("role", "")
                        content = msg.get("content", [])
                        is_tool_call = False
                        if isinstance(content, list):
                            for blk in content:
                                if (
                                    isinstance(blk, dict)
                                    and blk.get("type") == "tool_use"
                                ):
                                    is_tool_call = True
                                    break
                        if role == "user" and not is_tool_call:
                            consecutive_tools = 0  # human turn resets counter
                        elif is_tool_call or role == "assistant":
                            consecutive_tools += 1
                            max_consecutive_in_session = max(
                                max_consecutive_in_session, consecutive_tools
                            )
                        # Sum tokens in last 2 minutes
                        if ts >= window_2min:
                            usage = (
                                msg.get("usage", {})
                                if isinstance(msg.get("usage"), dict)
                                else {}
                            )
                            tok = float(
                                usage.get("total_tokens")
                                or usage.get("totalTokens")
                                or (
                                    usage.get("input_tokens", 0)
                                    + usage.get("output_tokens", 0)
                                )
                                or 0
                            )
                            tokens_2min += tok
                    total_tokens_2min += tokens_2min
                    if max_consecutive_in_session > max_consecutive_tools:
                        max_consecutive_tools = max_consecutive_in_session
                    # Track highest burn session
                    burn = _session_burn_stats(fname.replace(".jsonl", ""))
                    tpm = burn.get("tokensPerMin", 0)
                    if tpm > highest_tpm:
                        highest_tpm = tpm
                        triggering_session = fname.replace(".jsonl", "")
                except Exception:
                    continue
    except Exception:
        pass

    usd_per_token = _estimate_usd_per_token()
    cost_per_min = highest_tpm * usd_per_token

    reasons = []
    active = False

    if total_tokens_2min >= _VELOCITY_TOKENS_PER_2MIN:
        active = True
        reasons.append(
            f"Token velocity: {int(total_tokens_2min):,} tokens in 2 min "
            f"(threshold: {_VELOCITY_TOKENS_PER_2MIN:,})"
        )
    if cost_per_min >= _VELOCITY_COST_PER_MIN:
        active = True
        reasons.append(
            f"Cost rate: ${cost_per_min:.3f}/min "
            f"(threshold: ${_VELOCITY_COST_PER_MIN:.2f}/min)"
        )
    if max_consecutive_tools >= _VELOCITY_CONSECUTIVE_TOOLS:
        active = True
        reasons.append(
            f"Consecutive tool calls: {max_consecutive_tools} "
            f"(threshold: {_VELOCITY_CONSECUTIVE_TOOLS})"
        )

    return {
        "active": active,
        "tokensIn2Min": round(total_tokens_2min, 1),
        "costPerMin": round(cost_per_min, 5),
        "maxConsecutiveTools": max_consecutive_tools,
        "triggeringSession": triggering_session,
        "reasons": reasons,
        "thresholds": {
            "tokensIn2Min": _VELOCITY_TOKENS_PER_2MIN,
            "costPerMin": _VELOCITY_COST_PER_MIN,
            "consecutiveTools": _VELOCITY_CONSECUTIVE_TOOLS,
        },
    }


# ── OTLP Protobuf Helpers ──────────────────────────────────────────────


_OTEL_SPAN_KIND_NAMES = {
    0: "UNSPECIFIED",
    1: "INTERNAL",
    2: "SERVER",
    3: "CLIENT",
    4: "PRODUCER",
    5: "CONSUMER",
}

_OTEL_STATUS_CODE_NAMES = {
    0: "UNSET",
    1: "OK",
    2: "ERROR",
}


# Cache for _sync_scope_runtimes(). The sync banner polls, and adapter
# detect() calls glob session dirs (~3.3s measured on a busy machine), so this
# must never run inline in a request handler. 60s is well under how fast a user
# installs a new agent.
_SYNC_SCOPE_CACHE = {"ts": 0.0, "runtimes": [], "running": False}
_SYNC_SCOPE_LOCK = threading.Lock()


def _sync_scope_runtimes():
    """Cached runtime list for the sync banner, served off the request path.

    The first call returns ``[]`` (banner shows the runtime-neutral "Syncing
    your AI agents") and kicks a background refresh; the next poll has the real
    list. Never blocks, never raises.
    """
    with _SYNC_SCOPE_LOCK:
        stale = time.time() - float(_SYNC_SCOPE_CACHE.get("ts") or 0) >= 60
        if stale and not _SYNC_SCOPE_CACHE["running"]:
            _SYNC_SCOPE_CACHE["running"] = True
            threading.Thread(target=_sync_scope_refresh_safe, daemon=True).start()
        return _SYNC_SCOPE_CACHE["runtimes"]


def _sync_scope_refresh_safe():
    """Thread target: refresh the cache, and always clear the in-flight flag.

    Without this a single unexpected raise would leave ``running`` True and
    wedge the cache at its last value for the life of the process.
    """
    try:
        _sync_scope_refresh()
    except Exception as _e:
        with _SYNC_SCOPE_LOCK:
            _SYNC_SCOPE_CACHE["ts"] = time.time()
            _SYNC_SCOPE_CACHE["running"] = False
        print(f"[sync-scope] runtime detection failed: {_e}")


def _sync_scope_refresh():
    """Detect which agent runtimes actually have sessions on this machine.

    Powers the sync banner title so it names the real runtimes ("Syncing your
    Claude Code data") instead of asserting OpenClaw on a machine that never
    had it. Pure filesystem detection: no DuckDB, no writer lock, never raises.

    Same honesty rule as ``_detect_runtimes_for_heartbeat``: a runtime is only
    named when it has **sessions on disk**. Presence alone is not enough, the
    Cursor IDE creates its state dir whether or not the agent was ever used,
    and naming a runtime we aren't actually syncing is the same lie this
    function exists to remove.

    Returns ``[{"id": ..., "label": ...}, ...]``; empty when nothing qualifies.
    """
    found = {}   # id -> {"label": str, "sessions": int}

    def _put(rid, label, sessions):
        rid = str(rid or "").strip().lower()
        if not rid:
            return
        cur = found.get(rid)
        if cur is None or int(sessions or 0) > cur["sessions"]:
            found[rid] = {"label": label or (cur or {}).get("label") or rid,
                          "sessions": int(sessions or 0)}

    # OpenClaw / NemoClaw ship as adapters in OSS. Prefer the live registry
    # (plugins may have overridden an adapter); fall back to the built-ins,
    # because registration happens at app creation and can be empty here.
    _oss = []
    try:
        from clawmetry.adapters import registry as _reg
        _oss = list(_reg.detect_all())
    except Exception:
        pass
    if not _oss:
        try:
            from clawmetry.adapters.openclaw import OpenClawAdapter as _OC
            from clawmetry.adapters.nemo import NemoClawAdapter as _NC
            for _cls in (_OC, _NC):
                try:
                    _oss.append(_cls().detect())
                except Exception:
                    pass
        except Exception:
            pass
    for _r in _oss:
        if getattr(_r, "detected", False):
            _put(getattr(_r, "name", ""), getattr(_r, "display_name", ""),
                 getattr(_r, "session_count", 0))

    # Every other runtime. The lite detector is free and always present; the
    # family adapters are more accurate but live in clawmetry-pro, so they
    # return nothing in OSS. Merge both, keep the higher count per runtime.
    try:
        from clawmetry import sync as _sync_mod
        try:
            for _r in (_sync_mod._detect_runtimes_lite() or []):
                _put(_r.get("id"), _r.get("label"), _r.get("sessions"))
        except Exception:
            pass
        try:
            for _r in (_sync_mod._detect_family_runtimes() or []):
                _put(_r.get("name"), _r.get("displayName"), _r.get("sessionCount"))
        except Exception:
            pass
    except Exception:
        pass

    rows = [{"id": k, "label": v["label"]}
            for k, v in found.items() if v["sessions"] > 0]
    with _SYNC_SCOPE_LOCK:
        _SYNC_SCOPE_CACHE["ts"] = time.time()
        _SYNC_SCOPE_CACHE["runtimes"] = rows
        _SYNC_SCOPE_CACHE["running"] = False
    return rows


# ── HTML Template ───────────────────────────────────────────────────────


import os
import sys

# Force UTF-8 output on Windows (emoji in BANNER would crash with cp1252).
# reconfigure(), not a new TextIOWrapper — see the matching block at the top
# of this file: a second wrapper orphans the first, whose GC finalizer closes
# the shared buffer and kills sys.stdout for the whole process.
if sys.platform == "win32":
    import io

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import threading
from datetime import timezone, timedelta
from flask import (
    Flask,
)

# History / time-series module
try:
    from history import HistoryDB, HistoryCollector, AgentReliabilityScorer

    _HAS_HISTORY = True
except ImportError:
    _HAS_HISTORY = False
    HistoryDB = None
    HistoryCollector = None
    AgentReliabilityScorer = None

_history_db = None
_history_collector = None

# Optional: OpenTelemetry protobuf support for OTLP receiver
_HAS_OTEL_PROTO = False
try:
    from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2
    from opentelemetry.proto.collector.trace.v1 import trace_service_pb2
    from opentelemetry.proto.collector.logs.v1 import logs_service_pb2

    _HAS_OTEL_PROTO = True
except ImportError:
    metrics_service_pb2 = None
    trace_service_pb2 = None
    logs_service_pb2 = None


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'clawmetry', 'templates'),
)

# Plugins (e.g. ``clawmetry-pro``) register their Blueprints on ``app`` HERE —
# this must stay immediately after the one-and-only Flask() construction (see
# the note near the top of this module: a second construction once orphaned
# every plugin route). Older plugins with ``register_all()`` (no args) keep
# working unchanged: the loader inspects the signature and only passes
# ``app`` when accepted.
_ext_load(app)

# Cap request body size (DoS guard). OTLP/JSON batches and config posts are
# small; a 32 MB ceiling lets Flask reject oversized bodies (413) before they
# are read into memory. Override with CLAWMETRY_MAX_REQUEST_MB for large OTLP
# exporters.
try:
    _MAX_REQUEST_MB = int(os.environ.get("CLAWMETRY_MAX_REQUEST_MB", "32"))
except (TypeError, ValueError):
    _MAX_REQUEST_MB = 32
app.config["MAX_CONTENT_LENGTH"] = max(1, _MAX_REQUEST_MB) * 1024 * 1024

# ── Cross-platform helpers ──────────────────────────────────────────────
import platform as _platform


# _grep_log_file, _tail_lines, _get_log_dirs moved to helpers/logs.py (re-exported above)


# _detect_host_hardware moved to helpers/hardware.py (re-exported above)


_CURRENT_PLATFORM = _platform.system().lower()
# ── End cross-platform helpers ──────────────────────────────────────────

# ── Configuration (auto-detected, overridable via CLI/env) ──────────────
MC_URL = os.environ.get("MC_URL", "")  # Optional Mission Control URL, empty = disabled
WORKSPACE = None
MEMORY_DIR = None
LOG_DIR = None
SESSIONS_DIR = None
USER_NAME = None
GATEWAY_URL = None  # e.g. http://localhost:18789
GATEWAY_TOKEN = None  # Bearer token for /tools/invoke
# Removed: a fixed UTC+1 with no DST handling. It was wrong for Europe half
# the year and for everyone else all year, and it made this file's cost
# windows disagree with every other cost surface. Use
# clawmetry.cost_windows.now_local() for windows and .astimezone() for
# display. Guarded by tests/test_cost_windows_one_definition.py.
# SSE_MAX_SECONDS moved to helpers/streams.py (re-exported above)
# Stream-slot caps + state moved to helpers/streams.py (re-exported above)
EXTRA_SERVICES = []  # List of {'name': str, 'port': int} from --monitor-service flags
# _active_brain_stream_clients moved to helpers/streams.py

# ── Multi-Node Fleet Configuration ─────────────────────────────────────
FLEET_API_KEY = os.environ.get("CLAWMETRY_FLEET_KEY", "")
FLEET_DB_PATH = None  # Set via CLI or auto-detected
FLEET_NODE_TIMEOUT = 300  # seconds before node is considered offline

# ── Stuck-Session Detection ────────────────────────────────────────────
STUCK_SESSION_TIMEOUT_SEC = 300   # 5 min silent → warning alert
STUCK_SESSION_CRITICAL_SEC = 900  # 15 min silent → critical alert
_STUCK_SESSION_MAX_WINDOW_SEC = 7200  # beyond 2 h, assume completed — stop alerting
_STUCK_SESSION_COOLDOWN_SEC = 1800  # per-session alert cooldown (30 min)
_stuck_session_cooldowns: dict = {}  # session_id → last alert timestamp

# ── Budget & Alert Configuration ───────────────────────────────────────
_budget_paused = False
_budget_paused_at = 0
_budget_paused_reason = ""
_budget_alert_cooldowns = {}  # rule_id -> last_fired_timestamp
_AGENT_DOWN_SECONDS = 300  # 5 min with no OTLP data = agent down alert

# ── Heartbeat Gap Alerting ─────────────────────────────────────────────
_last_heartbeat_ts = 0  # timestamp of last detected heartbeat event
_heartbeat_interval_sec = 1800  # default 30 min, auto-detected from config
_heartbeat_silent_since = 0  # when silence was first detected (0 = not silent)


def _detect_heartbeat_interval():
    """Read heartbeat interval from OpenClaw config."""
    global _heartbeat_interval_sec
    for cf in [
        os.path.expanduser("~/.clawdbot/openclaw.json"),
        os.path.expanduser("~/.openclaw/openclaw.json"),
    ]:
        try:
            with open(cf) as f:
                cfg = json.load(f)
            hb = cfg.get("agents", {}).get("defaults", {}).get("heartbeat", {})
            every = hb.get("every", "")
            if every:
                import re as _re_hb

                m = _re_hb.match(
                    r"^(\d+)\s*(m|min|h|hr|s|sec)?$", str(every).strip().lower()
                )
                if m:
                    val = int(m.group(1))
                    unit = m.group(2) or "m"
                    if unit.startswith("h"):
                        _heartbeat_interval_sec = val * 3600
                    elif unit.startswith("s"):
                        _heartbeat_interval_sec = val
                    else:
                        _heartbeat_interval_sec = val * 60
                    return
        except Exception:
            continue


def _record_heartbeat():
    """Record that a heartbeat event was observed."""
    global _last_heartbeat_ts, _heartbeat_silent_since
    _last_heartbeat_ts = time.time()
    _heartbeat_silent_since = 0  # reset silence tracker


def _detect_sandbox_metadata():
    """Detect sandbox environment metadata. Returns dict or None."""
    sandbox = {}
    # Check environment variables (set by container wrappers like NemoClaw, Docker, etc.)
    name = os.environ.get("SANDBOX_NAME") or os.environ.get("CONTAINER_NAME")
    stype = os.environ.get("SANDBOX_TYPE") or os.environ.get("CONTAINER_TYPE")
    status = os.environ.get("SANDBOX_STATUS", "running")
    # Check if running inside Docker
    in_docker = os.path.exists("/.dockerenv")
    if not in_docker:
        try:
            with open("/proc/1/cgroup", "r") as f:
                in_docker = "docker" in f.read() or "containerd" in f.read()
        except Exception:
            pass
    # Check openclaw.json for sandbox config
    cfg = _load_gw_config()
    sandbox_cfg = cfg.get("sandbox", {}) if isinstance(cfg, dict) else {}
    if isinstance(sandbox_cfg, dict) and sandbox_cfg:
        name = name or sandbox_cfg.get("name")
        stype = stype or sandbox_cfg.get("type")
        status = sandbox_cfg.get("status", status)
    if name or stype or in_docker:
        sandbox["name"] = name or ("Docker Container" if in_docker else "Unknown")
        sandbox["type"] = stype or ("docker" if in_docker else "unknown")
        sandbox["status"] = status
        return sandbox
    return None


def _detect_inference_metadata():
    """Detect inference provider metadata. Returns dict or None."""
    provider = os.environ.get("INFERENCE_PROVIDER")
    model = os.environ.get("INFERENCE_MODEL")
    # Check openclaw.json
    cfg = _load_gw_config()
    if isinstance(cfg, dict):
        inf_cfg = cfg.get("inference", {})
        if isinstance(inf_cfg, dict) and inf_cfg:
            provider = provider or inf_cfg.get("provider")
            model = model or inf_cfg.get("model")
        # Also check default model from standard config
        if not model:
            model = cfg.get("model") or cfg.get("default_model")
        if not provider and model:
            # Infer provider from model name
            m = (model or "").lower()
            if "claude" in m or "anthropic" in m:
                provider = "Anthropic"
            elif "gpt" in m or "o1" in m or "o3" in m or "o4" in m:
                provider = "OpenAI"
            elif "gemini" in m:
                provider = "Google"
            elif "llama" in m or "mistral" in m or "mixtral" in m:
                provider = "Local/Ollama"
    if provider or model:
        return {"provider": provider, "model": model}
    return None


def _detect_security_metadata():
    """Detect security posture metadata. Returns dict or None."""
    security = {}
    cfg = _load_gw_config()
    if isinstance(cfg, dict):
        sec_cfg = cfg.get("security", {})
        if isinstance(sec_cfg, dict):
            if "sandbox_enabled" in sec_cfg:
                security["sandbox_enabled"] = sec_cfg["sandbox_enabled"]
            if "network_policy" in sec_cfg:
                security["network_policy"] = sec_cfg["network_policy"]
        # Check exec security mode
        exec_cfg = cfg.get("exec", {})
        if isinstance(exec_cfg, dict) and exec_cfg.get("security"):
            security["exec_security"] = exec_cfg["security"]
        # Check if auth is configured
        if cfg.get("auth") or cfg.get("token"):
            security["auth_enabled"] = True
        # Check bind address
        bind = cfg.get("bind") or cfg.get("host")
        if bind:
            security["bind_address"] = bind
            security["localhost_only"] = bind in ("127.0.0.1", "localhost", "::1")
    # Check Docker sandbox
    if os.path.exists("/.dockerenv"):
        security["sandbox_enabled"] = True
        security["sandbox_type"] = "docker"
    if security:
        return security
    return None


def _get_heartbeat_status():
    """Return heartbeat gap status for the API."""
    now = time.time()
    interval = _heartbeat_interval_sec
    threshold = interval * 1.5
    gap_sec = (now - _last_heartbeat_ts) if _last_heartbeat_ts > 0 else 0
    status = "unknown"
    if _last_heartbeat_ts == 0:
        status = "unknown"
    elif gap_sec <= interval:
        status = "ok"
    elif gap_sec <= threshold:
        status = "warning"
    else:
        status = "silent"
    return {
        "status": status,
        "last_heartbeat_ts": _last_heartbeat_ts,
        "gap_seconds": int(gap_sec) if _last_heartbeat_ts > 0 else None,
        "interval_seconds": interval,
        "threshold_seconds": int(threshold),
        "silent_since": _heartbeat_silent_since
        if _heartbeat_silent_since > 0
        else None,
    }


# ── Agent-presence detection (sibling of #1604) ──
# Distinct from ``_get_heartbeat_status``:
#   * heartbeat-status answers "has THIS install's daemon checked in yet?"
#     (transient race, resolves in ~30s — drives #1631's onboarding banner)
#   * detect_agent_install() answers "is there any underlying agent at
#     all?" — served at /api/agent-presence and mirrored into heartbeats
#     (sync.py) for the cloud's install-state aggregation. The dashboard
#     banner this used to drive ("No OpenClaw or NVIDIA NemoClaw
#     detected") was removed once ClawMetry grew past two runtimes; the
#     detection API stays for cloud consumers.
# Cached 60s so polling consumers don't re-stat 4+ paths and shell out
# to ``shutil.which``.
_agent_presence_cache = {"ts": 0.0, "value": None}
_AGENT_PRESENCE_TTL_SEC = 60


def _openclaw_gateway_running():
    """True only if the OpenClaw gateway is actually live (pid alive or the
    JSON-RPC port is listening). Stat + a 200ms localhost probe; never raises."""
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    pid_path = os.path.join(home, "gateway", "gateway.pid")
    try:
        if os.path.exists(pid_path):
            with open(pid_path) as fh:
                pid = int((fh.read() or "0").strip())
            if pid > 0:
                # Portable probe: os.kill(pid, 0) never raises on Windows,
                # so a stale gateway.pid would read as "running" forever.
                from clawmetry.process_control import is_alive as _pid_alive

                if _pid_alive(pid):
                    return True
    except (OSError, ValueError):
        pass
    try:
        import socket as _sock
        s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        s.settimeout(0.2)
        rc = s.connect_ex(("127.0.0.1", 18789))
        s.close()
        return rc == 0
    except Exception:
        return False


def _detect_openclaw_install():
    """Return True only when OpenClaw is GENUINELY installed (a real artifact),
    not when only ClawMetry's own ~/.openclaw scratch dir exists.

    ClawMetry creates ~/.openclaw/workspace (it drops .clawmetry-fleet.db /
    .clawmetry-metrics.json there), so "the dir exists / is non-empty" is NOT a
    signal — that bare-dir heuristic false-positived OpenClaw on uninstalled
    machines (fixed 2026-05-30). Cheap stat-only checks; no subprocess, no DuckDB.
    """
    import shutil as _shutil
    # 0. The openclaw CLI on PATH or the app bundle — unambiguous install.
    if _shutil.which("openclaw") or os.path.isdir("/Applications/OpenClaw.app"):
        return True
    home = os.environ.get("OPENCLAW_HOME") or os.path.expanduser("~/.openclaw")
    if not home:
        return False
    # 1. Gateway PID file / live gateway — strongest "is/was running" signal.
    if os.path.exists(os.path.join(home, "gateway", "gateway.pid")):
        return True
    if _openclaw_gateway_running():
        return True
    # 2. Session JSONLs (agent has produced events at some point).
    sess_dir = os.path.join(home, "agents", "main", "sessions")
    if os.path.isdir(sess_dir):
        try:
            for name in os.listdir(sess_dir):
                if name.endswith(".jsonl"):
                    return True
        except OSError:
            pass
    # 3. Workspace marker files (SOUL.md / AGENTS.md / MEMORY.md) — a real
    # OpenClaw workspace, not ClawMetry's scratch dir.
    ws = os.path.join(home, "workspace")
    for marker in ("SOUL.md", "AGENTS.md", "MEMORY.md"):
        if os.path.exists(os.path.join(ws, marker)):
            return True
    return False


def _detect_nemoclaw_install():
    """Return True if NemoClaw appears installed. Defers to the existing
    ``_detect_nemoclaw`` helper but only needs the boolean — avoids the
    expensive ``nemoclaw list`` subprocess call by short-circuiting on
    ``shutil.which`` and the config dir."""
    import shutil as _shutil
    if _shutil.which("nemoclaw"):
        return True
    cfg = os.path.expanduser("~/.nemoclaw")
    if os.path.isdir(cfg):
        try:
            if any(True for _ in os.scandir(cfg)):
                return True
        except OSError:
            pass
    return False


def _detect_any_local_data():
    """Return True if local DuckDB store has *any* events row. Used as the
    third leg of the no-agent decision so that an OpenClaw-less user who
    is none-the-less getting OTLP traces in still gets the normal UI."""
    try:
        from clawmetry import local_store  # type: ignore
        store = local_store.get_store(read_only=True)
    except Exception:
        return False
    # Best-effort: any of these public query helpers returning a row means
    # "we have data". Wrapped in try/except so a missing-table on a half-
    # initialised DB never raises into the UI thread.
    for method, kwargs in (
        ("query_events", {"limit": 1}),
        ("query_heartbeats", {"limit": 1}),
    ):
        try:
            fn = getattr(store, method, None)
            if fn is None:
                continue
            rows = fn(**kwargs)
            if rows:
                return True
        except Exception:
            continue
    return False


def _detect_other_runtimes_lite():
    """Best-effort list of NON-free runtimes with data on this machine
    (Claude Code, Codex, Cursor, …), each ``{id, label, sessions}``.
    Delegates to the free-tier lite detector in ``clawmetry.sync`` so the
    empty-state banner and the Fleet teaser can never disagree about what
    is installed. Never raises."""
    try:
        from clawmetry.sync import _detect_runtimes_lite
        return list(_detect_runtimes_lite() or [])
    except Exception:
        return []


def _entitled_runtime_ids(runtime_ids):
    """Subset of ``runtime_ids`` the current plan actually covers. Uses
    ``entitled_runtime`` (plan membership), NOT ``allows_runtime`` — grace
    mode answers True for everything, which would hide the trial pitch from
    every free-tier user. Never raises."""
    try:
        from clawmetry.entitlements import get_entitlement
        ent = get_entitlement()
        return [rid for rid in runtime_ids if ent.entitled_runtime(rid)]
    except Exception:
        return []


def detect_agent_install():
    """Return ``{openclaw_detected, nemoclaw_detected, any_data, signals}``
    answering "is there an underlying agent producing data?", plus
    ``detected_runtimes`` — non-free runtimes found on disk, each carrying an
    ``entitled`` flag so the no-agent banner can pitch a Pro trial instead of
    telling a Claude Code / Cursor user to install a second agent.

    Cached for ``_AGENT_PRESENCE_TTL_SEC`` (60s) — every tab switch on the
    dashboard polls this; the underlying filesystem state changes on the
    order of minutes-hours, not milliseconds.
    """
    now = time.time()
    cached = _agent_presence_cache.get("value")
    if cached and (now - _agent_presence_cache["ts"]) < _AGENT_PRESENCE_TTL_SEC:
        return cached
    openclaw = bool(_detect_openclaw_install())
    openclaw_running = bool(_openclaw_gateway_running()) if openclaw else False
    nemoclaw = bool(_detect_nemoclaw_install())
    any_data = bool(_detect_any_local_data())
    others = _detect_other_runtimes_lite()
    entitled = set(_entitled_runtime_ids([r.get("id") for r in others]))
    detected_runtimes = [
        {
            "id": r.get("id"),
            "label": r.get("label") or r.get("id"),
            "sessions": int(r.get("sessions") or 0),
            "entitled": r.get("id") in entitled,
        }
        for r in others
        if r.get("id")
    ]
    signals = []
    if openclaw:
        signals.append("openclaw")
    if nemoclaw:
        signals.append("nemoclaw")
    if any_data:
        signals.append("local_data")
    payload = {
        "openclaw_detected": openclaw,
        "openclaw_running": openclaw_running,  # installed AND gateway live
        "nemoclaw_detected": nemoclaw,
        "any_data": any_data,
        "signals": signals,
        # Unchanged on purpose: "no agent WE ARE OBSERVING" — a detected but
        # unentitled Claude Code install still needs the banner (in its
        # upgrade variant), so it must not clear no_agent.
        "no_agent": not (openclaw or nemoclaw or any_data),
        "detected_runtimes": detected_runtimes,
        "upgrade_candidate": any(not r["entitled"] for r in detected_runtimes),
    }
    _agent_presence_cache["ts"] = now
    _agent_presence_cache["value"] = payload
    return payload


# ── OTLP Metrics Store ─────────────────────────────────────────────────
METRICS_FILE = None  # Set via CLI/env, defaults to {WORKSPACE}/.clawmetry-metrics.json
_metrics_lock = threading.Lock()
_otel_last_received = 0  # timestamp of last OTLP data received

metrics_store = {
    "tokens": [],  # [{timestamp, input, output, total, model, channel, provider}]
    "cost": [],  # [{timestamp, usd, model, channel, provider}]
    "runs": [],  # [{timestamp, duration_ms, model, channel}]
    "messages": [],  # [{timestamp, channel, outcome, duration_ms}]
    "webhooks": [],  # [{timestamp, channel, type}]
    "queues": [],  # [{timestamp, channel, depth}]
}
MAX_STORE_ENTRIES = 10_000
STORE_RETENTION_DAYS = 14


def _metrics_file_path():
    """Get the path to the metrics persistence file."""
    if METRICS_FILE:
        return METRICS_FILE
    if WORKSPACE:
        return os.path.join(WORKSPACE, ".clawmetry-metrics.json")
    return os.path.expanduser("~/.clawmetry-metrics.json")


def _load_metrics_from_disk():
    """Load persisted metrics on startup."""
    global metrics_store, _otel_last_received
    path = _metrics_file_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            for key in metrics_store:
                if key in data and isinstance(data[key], list):
                    metrics_store[key] = data[key][-MAX_STORE_ENTRIES:]
            _otel_last_received = data.get("_last_received", 0)
        _expire_old_entries()
    except json.JSONDecodeError as e:
        print(f"[warn]  Warning: Failed to parse metrics file {path}: {e}")
        # Create backup of corrupted file
        backup_path = f"{path}.corrupted.{int(time.time())}"
        try:
            os.rename(path, backup_path)
            print(f"💾 Corrupted file backed up to {backup_path}")
        except OSError:
            pass
    except (IOError, OSError) as e:
        print(f"[warn]  Warning: Failed to read metrics file {path}: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error loading metrics: {e}")


def _save_metrics_to_disk():
    """Persist metrics store to JSON file."""
    path = _metrics_file_path()
    try:
        d = os.path.dirname(path)
        if d:
            os.makedirs(d, exist_ok=True)
        data = {}
        with _metrics_lock:
            for k in metrics_store:
                data[k] = list(metrics_store[k])
        data["_last_received"] = _otel_last_received
        data["_saved_at"] = time.time()
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, path)
    except OSError as e:
        print(f"[warn]  Warning: Failed to save metrics to {path}: {e}")
        if "No space left on device" in str(e):
            print("💾 Disk full! Consider cleaning up old files or expanding storage.")
    except json.JSONEncodeError as e:
        print(f"[warn]  Warning: Failed to serialize metrics data: {e}")
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error saving metrics: {e}")


def _expire_old_entries():
    """Remove entries older than STORE_RETENTION_DAYS."""
    cutoff = time.time() - (STORE_RETENTION_DAYS * 86400)
    with _metrics_lock:
        for key in metrics_store:
            metrics_store[key] = [
                e for e in metrics_store[key] if e.get("timestamp", 0) > cutoff
            ][-MAX_STORE_ENTRIES:]


def _add_metric(category, entry):
    """Add an entry to the metrics store (thread-safe)."""
    global _otel_last_received
    with _metrics_lock:
        metrics_store[category].append(entry)
        if len(metrics_store[category]) > MAX_STORE_ENTRIES:
            metrics_store[category] = metrics_store[category][-MAX_STORE_ENTRIES:]
        _otel_last_received = time.time()
    # Check budget on cost entries
    if category == "cost":
        try:
            _budget_check()
        except Exception:
            pass


def _metrics_flush_loop():
    """Background thread: save metrics to disk every 60 seconds."""
    while True:
        time.sleep(60)
        try:
            _expire_old_entries()
            _save_metrics_to_disk()
        except KeyboardInterrupt:
            print("📊 Metrics flush loop shutting down...")
            break
        except Exception as e:
            print(f"[warn]  Warning: Error in metrics flush loop: {e}")
            # Continue running despite errors


def _start_metrics_flush_thread():
    """Start the background metrics flush thread."""
    t = threading.Thread(target=_metrics_flush_loop, daemon=True)
    t.start()


def _has_otel_data():
    """Check if we have any OTLP metrics data."""
    return any(len(metrics_store[k]) > 0 for k in metrics_store)


# ── Multi-Node Fleet Database ───────────────────────────────────────────

_fleet_db_lock = threading.Lock()


def _fleet_db_path():
    """Get path to the fleet SQLite database.

    Always uses ~/.clawmetry/fleet.db, creating the directory if needed.
    The curl installer creates ~/.clawmetry/ but we must not rely on that --
    this function is the authoritative path and ensures the dir exists.

    Falls back to a workspace-relative path when WORKSPACE is set (dev mode).
    """
    if FLEET_DB_PATH:
        return FLEET_DB_PATH
    if WORKSPACE:
        _ws_db = os.path.join(WORKSPACE, ".clawmetry-fleet.db")
        # Only honour the workspace-relative path when we can actually write
        # there. Under launchd the process starts with cwd="/", and the
        # workspace auto-detect below falls back to os.getcwd(), so WORKSPACE
        # becomes "/" on any machine with no detectable OpenClaw workspace.
        # That resolved to "/.clawmetry-fleet.db" -- unwritable on macOS -- and
        # the dashboard exited(1) on every launchd boot instead of falling
        # through to the ~/.clawmetry path this function documents as
        # authoritative. A dev-mode workspace stays honoured; only an
        # unwritable one is skipped.
        if os.access(os.path.dirname(_ws_db) or ".", os.W_OK):
            return _ws_db
    # Always use ~/.clawmetry/fleet.db -- create the dir if the installer
    # has not run yet or this is a fresh pip install without curl | bash.
    preferred_dir = os.path.expanduser("~/.clawmetry")
    try:
        os.makedirs(preferred_dir, exist_ok=True)
    except OSError:
        pass  # makedirs failed (permissions?), fall through to legacy path
    if os.path.isdir(preferred_dir):
        return os.path.join(preferred_dir, "fleet.db")
    # Last resort: legacy flat file in home dir (pre-installer environments)
    return os.path.expanduser("~/.clawmetry-fleet.db")


def _fleet_db():
    """Get a SQLite connection to the fleet database."""
    path = _fleet_db_path()
    # Ensure parent directory exists (defence-in-depth: guards against callers
    # that bypass _fleet_init_db, and older code paths that skipped makedirs).
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    db = _sqlite3.connect(path, timeout=10)
    db.row_factory = _sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    return db


def _fleet_init_db():
    """Initialize fleet database tables."""
    path = _fleet_db_path()
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS nodes (
            node_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            hostname TEXT,
            tags TEXT,
            api_key_hash TEXT,
            version TEXT,
            registered_at REAL,
            last_seen_at REAL,
            status TEXT DEFAULT 'unknown'
        );
        CREATE TABLE IF NOT EXISTS node_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id TEXT NOT NULL,
            timestamp REAL NOT NULL,
            metrics_json TEXT NOT NULL,
            FOREIGN KEY (node_id) REFERENCES nodes(node_id)
        );
        CREATE INDEX IF NOT EXISTS idx_node_metrics_node_ts
            ON node_metrics(node_id, timestamp DESC);
    """)
    db.close()


def _fleet_check_key(req):
    """Validate fleet API key from request header. Returns True if valid."""
    if not FLEET_API_KEY:
        return True  # No key configured = open (for dev/testing)
    key = req.headers.get("X-Fleet-Key", "")
    return hmac.compare_digest(key, FLEET_API_KEY)


def _fleet_update_statuses():
    """Update node statuses based on last_seen_at."""
    cutoff = time.time() - FLEET_NODE_TIMEOUT
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute(
            "UPDATE nodes SET status = 'offline' WHERE last_seen_at < ? AND status != 'offline'",
            (cutoff,),
        )
        db.commit()
        db.close()


def _fleet_prune_metrics():
    """Remove metrics older than 7 days."""
    cutoff = time.time() - (7 * 86400)
    with _fleet_db_lock:
        db = _fleet_db()
        db.execute("DELETE FROM node_metrics WHERE timestamp < ?", (cutoff,))
        db.commit()
        db.close()


def _fleet_maintenance_loop():
    """Background thread: update statuses and prune old metrics."""
    while True:
        time.sleep(300)  # every 5 minutes
        try:
            _fleet_update_statuses()
            _fleet_prune_metrics()
        except Exception as e:
            print(f"Warning: Fleet maintenance error: {e}")


def _start_fleet_maintenance_thread():
    """Start the background fleet maintenance thread."""
    t = threading.Thread(target=_fleet_maintenance_loop, daemon=True)
    t.start()


# ── Stuck-Session Health Loop ──────────────────────────────────────────


def _check_stuck_sessions() -> None:
    """Fire a stuck_session alert for any session silent longer than STUCK_SESSION_TIMEOUT_SEC.

    Uses the session's updatedAt (ms) as the last-activity proxy.  For the
    gateway-RPC path, sessions.list only contains live sessions, making this
    reliable.  For the file-based fallback, file mtime serves as the proxy;
    we cap the upper window at 2 h to avoid alerting on sessions that simply
    finished without a terminal event.
    """
    global _stuck_session_cooldowns
    now = time.time()
    try:
        sessions = _get_sessions()
    except Exception:
        return
    for s in sessions:
        sid = s.get("sessionId", "")
        if not sid:
            continue
        # Don't alert on ClawMetry's own helper sessions (clawmetry-fix /
        # clawmetry-selfevolve / clawmetry-mem-probe …) — they're our plumbing,
        # not the user's agent activity. Override: CLAWMETRY_SHOW_INTERNAL_SESSIONS=1.
        from clawmetry.config import hide_clawmetry_session
        if hide_clawmetry_session(sid):
            continue
        updated_ms = s.get("updatedAt") or 0
        if not updated_ms:
            continue
        age_sec = now - (updated_ms / 1000.0)
        if age_sec < STUCK_SESSION_TIMEOUT_SEC:
            continue  # still active
        if age_sec > _STUCK_SESSION_MAX_WINDOW_SEC:
            continue  # too old — likely completed, not stuck
        last_alerted = _stuck_session_cooldowns.get(sid, 0)
        if now - last_alerted < _STUCK_SESSION_COOLDOWN_SEC:
            continue
        _stuck_session_cooldowns[sid] = now
        severity = "critical" if age_sec >= STUCK_SESSION_CRITICAL_SEC else "warning"
        minutes = int(age_sec / 60)
        # Build a richer, human-readable label so users see WHAT got stuck, not
        # a UUID prefix. Order of preference: first user prompt (= the actual
        # task the agent was given) → displayName (if it isn't just a UUID
        # prefix itself) → channel + agent + model fallback → UUID prefix.
        label = _stuck_session_label(s, sid)
        agent = s.get("agent", "main")
        msg = (
            f'Session "{label}" appears stuck — no activity for {minutes} min'
            f" (agent: {agent})"
        )
        # rule_id carries the FULL session id (was [:32] truncated, which broke
        # frontend deep-links for standard UUID/UUID-ish session keys). Exact
        # match still works for cooldown lookup.
        _fire_alert(f"stuck_session_{sid}", "stuck_session", msg, severity=severity)


_UUIDISH_RE = _re.compile(r"^[0-9a-f]{6,}([-_][0-9a-f]+)*$", _re.I)


def _stuck_session_label(sess: dict, sid: str) -> str:
    """Render a human-readable label for the stuck-session banner.

    Tries (in order): the session's first user prompt (the actual task) →
    the gateway-supplied displayName (if it isn't a bare UUID) → a context
    blurb (channel · agent · model) → a UUID prefix. Bounded to ~60 chars.
    Never raises — falls through to ``sid[:16]`` on any error so the alert
    still fires.
    """
    try:
        prompt = _first_user_prompt_for_session(sid)
        if prompt:
            return prompt[:60] + ("…" if len(prompt) > 60 else "")
        name = (sess.get("displayName") or "").strip()
        # Skip pure UUID-prefix display names (the gateway returns these when
        # the agent never set a real one — they're noise to the user).
        if name and not _UUIDISH_RE.match(name):
            return name[:60]
        bits = [b for b in (sess.get("channel"), sess.get("agent"), sess.get("model")) if b]
        if bits:
            return " · ".join(str(b) for b in bits)[:60]
    except Exception:
        pass
    return sid[:16]


def _first_user_prompt_for_session(sid: str) -> str:
    """Return the first user-message text from the session JSONL, truncated.

    The user prompt is the most informative single piece of context for a
    stuck session (it's the task the agent was given). Read just enough of
    the file to extract it; bail on any error (network-mounted dirs, missing
    file, malformed lines) — the caller has a safe fallback. PR docs:
    matches ``_extract_spawn_task`` shape (dashboard.py:14825) but as a
    module-level helper so other features can reuse it.
    """
    try:
        sessions_dir = _get_sessions_dir()
        fpath = os.path.join(sessions_dir, sid + ".jsonl")
        if not os.path.isfile(fpath):
            return ""
        with open(fpath) as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                except (json.JSONDecodeError, ValueError):
                    continue
                # OpenClaw v3 normalises to {type:"prompt.submitted",
                # data:{finalPromptText:...}}; legacy event shape is
                # {type:"message", message:{role:"user", content:...}}.
                if obj.get("type") in ("prompt.submitted",) or obj.get("_v3_type") == "prompt.submitted":
                    txt = (obj.get("data", {}) or {}).get("finalPromptText") or obj.get("finalPromptText")
                    if isinstance(txt, str) and txt.strip():
                        return txt.strip()
                if obj.get("type") == "message":
                    m = obj.get("message", {}) or {}
                    if m.get("role") != "user":
                        continue
                    content = m.get("content", "")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                    if isinstance(content, list):
                        for block in content:
                            if isinstance(block, dict) and block.get("type") == "text":
                                t = block.get("text", "")
                                if isinstance(t, str) and t.strip():
                                    return t.strip()
    except Exception:
        pass
    return ""


def _session_health_loop() -> None:
    """Background thread: check for stuck sessions every 30 s."""
    while True:
        time.sleep(30)
        try:
            _check_stuck_sessions()
        except Exception as e:
            print(f"Warning: stuck-session check error: {e}")


def _start_session_health_thread() -> None:
    """Start the background stuck-session detection thread."""
    t = threading.Thread(target=_session_health_loop, daemon=True)
    t.start()


# ── Budget & Alert Database ────────────────────────────────────────────


def _budget_init_db():
    """Initialize budget and alert tables in the fleet database."""
    db = _fleet_db()
    db.executescript("""
        CREATE TABLE IF NOT EXISTS budget_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_rules (
            id TEXT PRIMARY KEY,
            type TEXT NOT NULL,
            threshold REAL NOT NULL,
            channels TEXT NOT NULL,
            cooldown_min INTEGER DEFAULT 30,
            enabled INTEGER DEFAULT 1,
            runtime TEXT DEFAULT 'all',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS alert_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            rule_id TEXT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            channel TEXT NOT NULL,
            fired_at REAL NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            ack_at REAL,
            FOREIGN KEY (rule_id) REFERENCES alert_rules(id)
        );
        CREATE INDEX IF NOT EXISTS idx_alert_history_fired
            ON alert_history(fired_at DESC);
        CREATE INDEX IF NOT EXISTS idx_alert_history_rule
            ON alert_history(rule_id, fired_at DESC);
    """)
    try:
        # Pre-0.12.639 DBs lack the per-runtime scope column. SQLite has no
        # IF-NOT-EXISTS for columns; the duplicate-column error is the no-op.
        db.execute("ALTER TABLE alert_rules ADD COLUMN runtime TEXT DEFAULT 'all'")
        db.commit()
    except Exception:
        pass
    try:
        # Pre-0.12.711 DBs drop the cloud-vocabulary ``alert_type`` the
        # Alerts tab POSTed, keeping only the mapped local ``type``. That
        # made a rule un-round-trippable: on update we could no longer tell
        # WHICH cloud type an ``anomaly`` row came from, so the DuckDB mirror
        # could not be rebuilt and the daemon evaluator stayed blind to it.
        db.execute("ALTER TABLE alert_rules ADD COLUMN alert_type TEXT DEFAULT ''")
        db.commit()
    except Exception:
        pass
    db.close()


def _get_budget_config():
    """Get all budget config as a dict."""
    defaults = {
        "daily_limit": 0,
        "weekly_limit": 0,
        "monthly_limit": 0,
        "auto_pause_enabled": False,
        "auto_pause_threshold_pct": 100,
        "auto_pause_threshold_usd": 0,
        "auto_pause_action": "pause",
        "warning_threshold_pct": 80,
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        # Issue #555 Phase 1 — hard budget cap. Distinct from
        # ``*_limit`` (soft, warning-thresholded). When ``*_cap_usd`` is
        # > 0 and current spend meets/exceeds it, ``_is_over_cap()``
        # returns True and the dashboard banner shows the resume CTA.
        # ``session_cap_usd`` is accepted now and consumed by per-session
        # accounting in Phase 2.
        "daily_cap_usd": 0.0,
        "monthly_cap_usd": 0.0,
        "session_cap_usd": 0.0,
    }
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute("SELECT key, value FROM budget_config").fetchall()
            db.close()
        for row in rows:
            k = row["key"]
            v = row["value"]
            if k in defaults:
                if isinstance(defaults[k], bool):
                    defaults[k] = v.lower() in ("true", "1", "yes")
                elif isinstance(defaults[k], (int, float)):
                    try:
                        defaults[k] = float(v)
                    except ValueError:
                        pass
                else:
                    defaults[k] = v
    except Exception:
        pass
    return defaults


def _set_budget_config(updates):
    """Update budget config keys."""
    now = time.time()
    with _fleet_db_lock:
        db = _fleet_db()
        for k, v in updates.items():
            db.execute(
                "INSERT OR REPLACE INTO budget_config (key, value, updated_at) VALUES (?, ?, ?)",
                (k, str(v), now),
            )
        db.commit()
        db.close()


_SEVERITY_LEVELS = {"info": 0, "warning": 1, "critical": 2}
_SEVERITY_COLORS_SLACK = {"info": "#36a64f", "warning": "#f59e0b", "critical": "#ef4444"}
_SEVERITY_COLORS_DISCORD = {"info": 3581519, "warning": 16023040, "critical": 15680580}


def _default_alerts_webhook_config():
    return {
        "webhook_url": "",
        "slack_webhook_url": "",
        "discord_webhook_url": "",
        # PagerDuty Events API v2 integration key (32-char hex). Empty = disabled.
        "pagerduty_routing_key": "",
        # OpsGenie API key (Authorization: GenieKey ...). Empty = disabled.
        "opsgenie_api_key": "",
        # Optional EU host override for OpsGenie ("https://api.eu.opsgenie.com").
        "opsgenie_api_url": "",
        # Telegram bot delivery (self-hosted Notifications tab). Both keys
        # required for a send. The /api/alert-channels ROUTE accepted these
        # since the notifications-local work, but this schema (and the save
        # allowlist below) silently dropped them — a "saved" Telegram channel
        # never persisted, so its card stayed on "Connect" forever.
        "telegram_bot_token": "",
        "telegram_chat_id": "",
        # WhatsApp — Meta Cloud API (token + phone_id) or Twilio's WhatsApp
        # channel (twilio_* below). ``whatsapp_template`` is the fallback
        # used when Meta's 24-hour service window has closed.
        "whatsapp_to": "",
        "whatsapp_token": "",
        "whatsapp_phone_id": "",
        "whatsapp_template": "",
        "whatsapp_lang": "",
        # Twilio — voice calls for approvals, and the WhatsApp sender when
        # Meta isn't configured.
        "twilio_account_sid": "",
        "twilio_auth_token": "",
        "twilio_from": "",
        "twilio_whatsapp_from": "",
        "phone_number": "",
        # Local SMTP so a self-hosted (nocloud) node can still email.
        "email_address": "",
        "smtp_host": "",
        "smtp_port": 587,
        "smtp_user": "",
        "smtp_password": "",
        "smtp_from": "",
        "cost_spike_alerts": True,
        "agent_error_rate_alerts": True,
        "security_posture_changes": True,
        "min_severity": "warning",
    }


def _load_alerts_webhook_config():
    cfg = _default_alerts_webhook_config()
    try:
        if os.path.exists(_ALERTS_CONFIG_FILE):
            with open(_ALERTS_CONFIG_FILE, "r") as f:
                data = json.load(f)
            if isinstance(data, dict):
                for k in cfg:
                    if k in data:
                        cfg[k] = data[k]
                if "min_severity" in data:
                    cfg["min_severity"] = data["min_severity"]
    except Exception:
        pass
    return cfg


def _save_alerts_webhook_config(updates):
    cfg = _load_alerts_webhook_config()
    allowed = {
        "webhook_url", "slack_webhook_url", "discord_webhook_url",
        "pagerduty_routing_key", "opsgenie_api_key", "opsgenie_api_url",
        "telegram_bot_token", "telegram_chat_id",
        # Keep in lockstep with _default_alerts_webhook_config above — a key
        # in the schema but not here saves as a no-op (the exact bug the
        # telegram comment there documents).
        "whatsapp_to", "whatsapp_token", "whatsapp_phone_id",
        "whatsapp_template", "whatsapp_lang",
        "twilio_account_sid", "twilio_auth_token", "twilio_from",
        "twilio_whatsapp_from", "phone_number",
        "email_address", "smtp_host", "smtp_port", "smtp_user",
        "smtp_password", "smtp_from",
        "cost_spike_alerts", "agent_error_rate_alerts", "security_posture_changes",
        "min_severity",
    }
    for k in allowed:
        if k in updates:
            cfg[k] = updates[k]
    try:
        os.makedirs(os.path.dirname(_ALERTS_CONFIG_FILE), exist_ok=True)
        with open(_ALERTS_CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass
    return cfg


def _should_send_webhook_for_type(alert_type):
    cfg = _load_alerts_webhook_config()
    if alert_type in (
        "cost_spike",
        "daily_threshold_breached",
        "weekly_threshold_breached",
    ):
        return bool(cfg.get("cost_spike_alerts", True))
    if alert_type == "agent_error_rate":
        return bool(cfg.get("agent_error_rate_alerts", True))
    if alert_type == "security_posture_change":
        return bool(cfg.get("security_posture_changes", True))
    return True


def _severity_passes_filter(severity):
    """Return True if the given severity meets the configured minimum threshold."""
    cfg = _load_alerts_webhook_config()
    min_sev = str(cfg.get("min_severity", "warning")).lower()
    min_level = _SEVERITY_LEVELS.get(min_sev, 1)
    sev_level = _SEVERITY_LEVELS.get(str(severity).lower(), 1)
    return sev_level >= min_level


def _send_slack_alert(message, severity="warning", title="ClawMetry Alert"):
    """Send a Slack-formatted attachment alert using the configured Slack webhook URL."""
    cfg = _load_alerts_webhook_config()
    url = str(cfg.get("slack_webhook_url", "")).strip()
    if not url:
        return
    color = _SEVERITY_COLORS_SLACK.get(str(severity).lower(), "#f59e0b")
    payload = {
        "attachments": [
            {
                "color": color,
                "title": title,
                "text": message,
                "footer": "ClawMetry",
                "ts": int(time.time()),
                "fields": [
                    {"title": "Severity", "value": severity.upper(), "short": True},
                ],
            }
        ]
    }
    _send_webhook_alert(url, payload, payload_type="generic")


def _send_discord_alert(message, severity="warning", title="ClawMetry Alert"):
    """Send a Discord embed alert using the configured Discord webhook URL."""
    cfg = _load_alerts_webhook_config()
    url = str(cfg.get("discord_webhook_url", "")).strip()
    if not url:
        return
    color = _SEVERITY_COLORS_DISCORD.get(str(severity).lower(), 16023040)
    payload = {
        "embeds": [
            {
                "title": title,
                "description": message,
                "color": color,
                "fields": [
                    {"name": "Severity", "value": severity.upper(), "inline": True},
                ],
                "footer": {"text": "ClawMetry"},
                "timestamp": datetime.utcfromtimestamp(time.time()).strftime(
                    "%Y-%m-%dT%H:%M:%SZ"
                ),
            }
        ]
    }
    _send_webhook_alert(url, payload, payload_type="generic")


def _dispatch_alert(title, message, severity="warning", alert_type=None, only=None):
    """Dispatch an alert to all configured channels (Slack, Discord, generic webhook).

    Respects the global min_severity filter and per-type toggles.
    Called automatically from _fire_alert() so all alerts reach webhook channels.
    ``only`` (a set of channel ids) restricts the fan-out to those sinks —
    built-in monitors pass their resolved channel set so the Alerts tab's
    pills and the actual delivery are the same list.
    """
    if not _severity_passes_filter(severity):
        return
    if alert_type and not _should_send_webhook_for_type(alert_type):
        return
    cfg = _load_alerts_webhook_config()
    generic_url = str(cfg.get("webhook_url", "")).strip()
    slack_url = str(cfg.get("slack_webhook_url", "")).strip()
    discord_url = str(cfg.get("discord_webhook_url", "")).strip()
    if only is not None:
        if "webhook" not in only:
            generic_url = ""
        if "slack" not in only:
            slack_url = ""
        if "discord" not in only:
            discord_url = ""

    if generic_url:
        payload = {
            "type": alert_type or "alert",
            "title": title,
            "message": message,
            "severity": severity,
            "timestamp": time.time(),
        }
        _send_webhook_alert(generic_url, payload, payload_type="generic")
    if slack_url:
        _send_slack_alert(message, severity=severity, title=title)
    if discord_url:
        _send_discord_alert(message, severity=severity, title=title)


def _dispatch_configured_webhooks(alert_type, payload):
    if not _should_send_webhook_for_type(alert_type):
        return
    cfg = _load_alerts_webhook_config()
    generic_url = str(cfg.get("webhook_url", "")).strip()
    slack_url = str(cfg.get("slack_webhook_url", "")).strip()
    discord_url = str(cfg.get("discord_webhook_url", "")).strip()
    if generic_url:
        _send_webhook_alert(generic_url, payload, payload_type="generic")
    if slack_url:
        _send_webhook_alert(slack_url, payload, payload_type="slack")
    if discord_url:
        _send_webhook_alert(discord_url, payload, payload_type="discord")


# ── Built-in monitor delivery ──────────────────────────────────────────────
#
# Founder 2026-08-17: the Alerts tab showed every always-on monitor with an
# "In-app · telegram" pill on a node where Telegram was never configured.
# The pills came from a hardcoded ``channels=["banner", "telegram"]`` on each
# ``_fire_alert`` call site; delivery then read Telegram creds from a store
# the Notifications tab never writes and fell back to an undefined gateway
# helper — so "telegram" delivered nothing and the pill was a fabrication.
#
# One resolver now answers "where does this monitor deliver?" for BOTH the
# Alerts tab (``/api/alerts/builtins``) and ``_fire_alert``. A channel is
# offered only when this process can actually deliver to it right now, so
# what the tab shows and what fires cannot drift. Operators can also mute a
# monitor or pin its channels; prefs live in ~/.clawmetry so they survive
# upgrades and are not tied to an OpenClaw install.
_BUILTIN_MONITOR_PREFS_FILE = os.path.expanduser("~/.clawmetry/builtin_monitors.json")
_BUILTIN_CHANNEL_META = {
    # In-app is the floor: it is always deliverable and never removable
    # (to silence a monitor you disable it, not strip its last channel).
    "banner":   ("In-app",   "Red banner + bell in this dashboard"),
    "telegram": ("Telegram", "Direct Bot API message"),
    "slack":    ("Slack",    "Incoming webhook"),
    "discord":  ("Discord",  "Channel webhook"),
    "webhook":  ("Webhook",  "POST JSON to your endpoint"),
}


def _builtin_alert_types():
    try:
        from routes.alerts import BUILTIN_MONITORS
        return {m["alert_type"] for m in BUILTIN_MONITORS}
    except Exception:
        return set()


def _telegram_creds():
    """(bot_token, chat_id) from either store.

    Legacy budget config (SQLite) came first; the Notifications tab writes
    the alert-channels file. Delivery must honour both or a user who
    "connected" Telegram in the tab still gets nothing.
    """
    for loader in (_load_alerts_webhook_config, _get_budget_config):
        try:
            cfg = loader()
            tok = str(cfg.get("telegram_bot_token", "") or "").strip()
            cid = str(cfg.get("telegram_chat_id", "") or "").strip()
            if tok and cid:
                return tok, cid
        except Exception:
            continue
    return "", ""


def _builtin_channels_available():
    """Channels a built-in monitor CAN deliver to from this process right now.

    Never advertises a destination that has no working sender behind it:
    email / phone / WhatsApp are cloud-delivered and have no local sender,
    so they are absent here even when creds are saved.
    """
    out = [{"id": "banner", "label": "In-app",
            "detail": _BUILTIN_CHANNEL_META["banner"][1], "configured": True}]
    tok, cid = _telegram_creds()
    if tok and cid:
        out.append({"id": "telegram", "label": "Telegram",
                    "detail": f"Bot API to chat {cid[-4:].rjust(len(cid), '*')}",
                    "configured": True})
    try:
        cfg = _load_alerts_webhook_config()
    except Exception:
        cfg = {}
    for cid_, key in (("slack", "slack_webhook_url"),
                      ("discord", "discord_webhook_url"),
                      ("webhook", "webhook_url")):
        if str(cfg.get(key, "") or "").strip():
            lbl, det = _BUILTIN_CHANNEL_META[cid_]
            out.append({"id": cid_, "label": lbl, "detail": det, "configured": True})
    return out


def _load_builtin_monitor_prefs():
    try:
        with open(_BUILTIN_MONITOR_PREFS_FILE) as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_builtin_monitor_pref(alert_type, enabled=None, channels=None):
    """Persist one monitor's prefs. ``channels=None`` keeps the current
    value; ``channels=[]`` or a list pins them; the string ``"auto"`` clears
    the pin (back to every available channel)."""
    prefs = _load_builtin_monitor_prefs()
    cur = dict(prefs.get(alert_type) or {})
    if enabled is not None:
        cur["enabled"] = bool(enabled)
    if channels == "auto":
        cur.pop("channels", None)
    elif isinstance(channels, list):
        known = set(_BUILTIN_CHANNEL_META)
        cur["channels"] = sorted({str(c) for c in channels if str(c) in known} | {"banner"})
    prefs[alert_type] = cur
    os.makedirs(os.path.dirname(_BUILTIN_MONITOR_PREFS_FILE), exist_ok=True)
    tmp = _BUILTIN_MONITOR_PREFS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(prefs, f, indent=2)
    os.replace(tmp, _BUILTIN_MONITOR_PREFS_FILE)
    return cur


def _resolve_builtin_delivery(alert_type):
    """The single answer for "is this monitor on, and where does it go?".

    Returns ``{"enabled", "channels", "mode"}`` where ``channels`` is the
    exact list ``_fire_alert`` will deliver to: pinned channels intersected
    with what is deliverable now (a pinned-but-unconfigured channel is
    dropped, not shown), or every available channel in ``auto`` mode.
    """
    prefs = _load_builtin_monitor_prefs().get(alert_type) or {}
    available = [c["id"] for c in _builtin_channels_available()]
    pinned = prefs.get("channels")
    if isinstance(pinned, list):
        chans = [c for c in available if c in pinned or c == "banner"]
        mode = "custom"
    else:
        chans, mode = list(available), "auto"
    return {"enabled": bool(prefs.get("enabled", True)),
            "channels": chans, "mode": mode}


def _fire_alert(rule_id, alert_type, message, channels=None, severity="warning",
                builtin=None):
    """Fire an alert with cooldown check and dispatch to configured webhook channels.

    ``builtin`` — True: route through the built-in monitor resolver (mute +
    channel prefs); False: a user rule, deliver exactly ``channels``; None:
    auto — built-in iff ``alert_type`` is one of the always-on monitors.
    """
    global _budget_alert_cooldowns
    now = time.time()

    if builtin is None:
        builtin = alert_type in _builtin_alert_types()
    only_sinks = None
    if builtin:
        try:
            resolved = _resolve_builtin_delivery(alert_type)
        except Exception:
            resolved = {"enabled": True, "channels": ["banner"], "mode": "auto"}
        if not resolved["enabled"]:
            return  # muted by the operator — no history, no banner, no fan-out
        channels = resolved["channels"]
        only_sinks = set(channels)

    # Check cooldown (default 30 min for budget alerts)
    cooldown_sec = 1800
    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
    if now - last_fired < cooldown_sec:
        return

    _budget_alert_cooldowns[rule_id] = now

    # Save to alert history
    if channels is None:
        channels = ["banner"]
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            for ch in channels:
                db.execute(
                    "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (rule_id, alert_type, message, ch, now),
                )
            db.commit()
            db.close()
    except Exception as e:
        print(f"Warning: Failed to save alert history: {e}")

    # Send to explicit channels (telegram, banner, webhook)
    for ch in channels:
        if ch == "telegram":
            _send_telegram_alert(message)
        elif ch == "webhook":
            pass  # legacy: webhook dispatch now handled below via _dispatch_alert

    # LLM-narrated enrichment (issue #1412, Feature C).  Replaces the raw
    # threshold string with a 1-3 sentence human explanation when the LLM is
    # available and the event hasn't been coalesced.  Falls back silently.
    try:
        from clawmetry import narrator as _narrator
        _narrated = _narrator.narrate(
            alert_type or "threshold",
            {"message": message, "rule_id": rule_id, "alert_type": alert_type,
             "severity": severity},
        )
        if _narrated:
            message = _narrated
    except Exception:
        pass

    # Dispatch to configured alert channels (Slack / Discord / generic webhook).
    # Built-in monitors pass their resolved channel set so a sink the operator
    # unpinned is not fanned out to; user rules keep the legacy fan-out.
    _dispatch_alert(
        title=f"ClawMetry Alert [{alert_type}]",
        message=message,
        severity=severity,
        alert_type=alert_type,
        only=only_sinks,
    )


def _send_telegram_alert(message):
    """Send alert via the direct Telegram Bot API.

    Creds come from either store (see ``_telegram_creds``). With none
    configured this is a no-op — the old "gateway fallback" called a helper
    that was never defined, so it silently delivered nothing anyway.
    """
    token, chat_id = _telegram_creds()
    if not (token and chat_id):
        return
    try:
        import urllib.request

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = json.dumps(
            {
                "chat_id": chat_id,
                "text": f"[ClawMetry Alert] {message}",
                "parse_mode": "Markdown",
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Warning: Direct Telegram alert failed: {e}")


# PagerDuty and OpsGenie integration constants. The actual payload
# builders + transport moved to the closed-source clawmetry-pro package
# (clawmetry_pro/sinks/{pagerduty,opsgenie}.py) per the open-core plan.
# These constants are public URLs / trivial maps and stay in OSS so the
# alerts/webhook-test endpoint can reference them for its UI hints
# without importing the closed package.
_PD_SEVERITY = {"info": "info", "warning": "warning", "error": "error", "critical": "critical"}
_OG_PRIORITY = {"info": "P5", "warning": "P3", "error": "P2", "critical": "P1"}
_PD_EVENTS_URL = "https://events.pagerduty.com/v2/enqueue"
_OG_DEFAULT_API_URL = "https://api.opsgenie.com/v2/alerts"


def _pro_sinks():
    """Return ``clawmetry_pro.sinks`` when importable, else ``None``.

    Cached implicitly by the Python import system; first miss pays one
    ImportError, subsequent misses are a dict lookup.
    """
    try:
        from clawmetry_pro import sinks as _s
        return _s
    except Exception:
        return None


def _build_pagerduty_payload(alert_data: dict, routing_key: str) -> dict:
    """Delegate to clawmetry-pro's PD payload builder.

    Returns ``{}`` when the closed package is not installed so callers
    can detect "no payload built" without exception handling. Public OSS
    cannot actually send PagerDuty events (sink delegation no-ops); this
    helper is here only for tests and for backward-compatible signatures
    in routes/alerts.py callers.
    """
    sinks = _pro_sinks()
    if sinks is None:
        return {}
    try:
        return sinks.build_pagerduty_payload(alert_data, routing_key)
    except Exception:
        return {}


def _build_opsgenie_payload(alert_data: dict) -> dict:
    """Delegate to clawmetry-pro's OpsGenie payload builder. Returns
    ``{}`` when the closed package is not installed."""
    sinks = _pro_sinks()
    if sinks is None:
        return {}
    try:
        return sinks.build_opsgenie_payload(alert_data)
    except Exception:
        return {}


def _send_webhook_alert(url, alert_data, payload_type="generic"):
    """Send alert to a webhook URL (generic JSON, Slack attachment, Discord
    embed). PagerDuty + OpsGenie are delegated to clawmetry-pro when
    installed; when not installed the call is a no-op (Pro feature).
    """
    # PagerDuty + OpsGenie moved to clawmetry-pro/sinks/. Delegate when
    # the closed package is installed; log + return when it isn't (so
    # OSS-only callers don't pretend the alert went out).
    if payload_type in ("pagerduty", "opsgenie"):
        import logging as _lg
        _wh_log = _lg.getLogger("clawmetry.dashboard.webhook")
        sinks = _pro_sinks()
        if sinks is None:
            _wh_log.info(
                "_send_webhook_alert: %s sink requires clawmetry-pro "
                "(install with a license key, or use Cloud Pro). "
                "Alert dropped.", payload_type,
            )
            return
        try:
            if payload_type == "pagerduty":
                routing_key = str(alert_data.get("_pd_routing_key", "")).strip()
                if not routing_key:
                    return
                sinks.send_pagerduty(alert_data, routing_key)
            else:
                api_key = str(alert_data.get("_og_api_key", "")).strip()
                if not api_key:
                    return
                og_url = (url or "").strip() or None
                sinks.send_opsgenie(alert_data, api_key, api_url=og_url)
        except Exception as exc:
            _wh_log.warning("_send_webhook_alert: %s delegation failed: %s", payload_type, exc)
        return

    try:
        import urllib.request as _ur

        extra_headers: dict[str, str] = {}
        if payload_type == "discord":
            message_text = (
                alert_data.get("message")
                or "[{t}] cost=${c} threshold=${th}".format(
                    t=alert_data.get("type", "alert"),
                    c=alert_data.get("cost_usd", 0),
                    th=alert_data.get("threshold", 0),
                )
            )
            severity = str(alert_data.get("severity", "warning")).lower()
            color = _SEVERITY_COLORS_DISCORD.get(severity, 16023040)
            body = {
                "embeds": [
                    {
                        "title": alert_data.get("title", "ClawMetry Alert"),
                        "description": message_text,
                        "color": color,
                        "fields": [
                            {"name": "Severity", "value": severity.upper(), "inline": True},
                            {"name": "Type", "value": str(alert_data.get("type", "alert")), "inline": True},
                        ],
                        "footer": {"text": "ClawMetry"},
                        "timestamp": datetime.utcfromtimestamp(time.time()).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        ),
                    }
                ]
            }
        elif payload_type == "slack":
            message_text = (
                alert_data.get("message")
                or "[{t}] cost=${c} threshold=${th}".format(
                    t=alert_data.get("type", "alert"),
                    c=alert_data.get("cost_usd", 0),
                    th=alert_data.get("threshold", 0),
                )
            )
            severity = str(alert_data.get("severity", "warning")).lower()
            color = _SEVERITY_COLORS_SLACK.get(severity, "#f59e0b")
            body = {
                "attachments": [
                    {
                        "color": color,
                        "title": alert_data.get("title", "ClawMetry Alert"),
                        "text": message_text,
                        "footer": "ClawMetry",
                        "ts": int(time.time()),
                        "fields": [
                            {"title": "Severity", "value": severity.upper(), "short": True},
                            {"title": "Type", "value": str(alert_data.get("type", "alert")), "short": True},
                        ],
                    }
                ]
            }
        else:
            body = alert_data
            target_url = url
        # PD/OpsGenie branches set their own target_url; everything else uses
        # the caller-supplied url (covers generic / slack / discord).
        if payload_type not in ("pagerduty", "opsgenie"):
            target_url = url
        data = json.dumps(body).encode()
        headers = {"Content-Type": "application/json"}
        headers.update(extra_headers)
        req = _ur.Request(
            target_url,
            data=data,
            headers=headers,
            method="POST",
        )
        _ur.urlopen(req, timeout=10)
    except Exception:
        pass


def _dispatch_alert_to_all_sinks(alert_data: dict) -> list[str]:
    """Send an alert to every configured sink in one shot.

    Returns the list of sinks that were attempted (e.g. ``["slack",
    "pagerduty"]``). Used by the dispatcher hooks + the /test endpoint.
    Each ``_send_webhook_alert`` call is best-effort: failures are
    swallowed so a flaky vendor doesn't break the rest of the fan-out.
    """
    cfg = _load_alerts_webhook_config()
    sent: list = []
    url = str(cfg.get("webhook_url", "")).strip()
    if url:
        _send_webhook_alert(url, alert_data, payload_type="generic")
        sent.append("generic")
    slack = str(cfg.get("slack_webhook_url", "")).strip()
    if slack:
        _send_webhook_alert(slack, alert_data, payload_type="slack")
        sent.append("slack")
    discord = str(cfg.get("discord_webhook_url", "")).strip()
    if discord:
        _send_webhook_alert(discord, alert_data, payload_type="discord")
        sent.append("discord")
    pd_key = str(cfg.get("pagerduty_routing_key", "")).strip()
    if pd_key:
        # Stash the key on the payload so the formatter can read it; it
        # never leaks into outbound generic/slack/discord bodies because
        # they don't read the underscore-prefixed keys.
        _send_webhook_alert(
            "",  # ignored; PD uses the fixed enqueue endpoint
            dict(alert_data, _pd_routing_key=pd_key),
            payload_type="pagerduty",
        )
        sent.append("pagerduty")
    og_key = str(cfg.get("opsgenie_api_key", "")).strip()
    if og_key:
        og_url = str(cfg.get("opsgenie_api_url", "")).strip() or _OG_DEFAULT_API_URL
        _send_webhook_alert(
            og_url,
            dict(alert_data, _og_api_key=og_key),
            payload_type="opsgenie",
        )
        sent.append("opsgenie")
    return sent


def _session_runtime_of(sid):
    """Runtime id for a namespaced session id ('copilot:...' -> 'copilot');
    anything without a known family prefix is OpenClaw."""
    sid = str(sid or "")
    if ":" in sid:
        head = sid.split(":", 1)[0]
        try:
            from clawmetry.entitlements import ALL_RUNTIMES
            if head in ALL_RUNTIMES:
                return head
        except ImportError:
            pass
    return "openclaw"


def _runtime_daily_spend(runtime):
    """Today's spend (USD) for ONE runtime from the per-(day, runtime)
    DuckDB rollup, via the daemon proxy. None on any failure so a scoped
    rule silently skips a tick rather than firing on a node-wide number."""
    try:
        from datetime import datetime as _dt, timezone as _tz
        from routes.local_query import local_store_via_daemon
        today = _dt.now(_tz.utc).strftime("%Y-%m-%d")
        rows = local_store_via_daemon(
            "query_rollup_runtime_daily", since=today) or []
        return float(sum(
            (r.get("cost_usd") or 0) for r in rows
            if r.get("day") == today and r.get("runtime") == runtime))
    except Exception:
        return None


def _runtime_tokens_per_min(runtime):
    """Tokens/min over the last 2 minutes for ONE runtime (DuckDB events
    filtered by session-id prefix via the daemon proxy). None on failure."""
    try:
        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
        from routes.local_query import local_store_via_daemon
        since = (_dt.now(_tz.utc) - _td(minutes=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
        rows = local_store_via_daemon(
            "query_events", since=since, runtime=runtime, limit=20000) or []
        return sum(int(r.get("token_count") or 0) for r in rows) / 2.0
    except Exception:
        return None


def _get_alert_rules():
    """Get all alert rules."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_rules ORDER BY created_at DESC"
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_alert_history(limit=50):
    """Get recent alert history."""
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history ORDER BY fired_at DESC LIMIT ?", (limit,)
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _get_active_alerts():
    """Get unacknowledged alerts from last 24h."""
    cutoff = time.time() - 86400
    try:
        with _fleet_db_lock:
            db = _fleet_db()
            rows = db.execute(
                "SELECT * FROM alert_history WHERE acknowledged = 0 AND fired_at > ? "
                "ORDER BY fired_at DESC LIMIT 20",
                (cutoff,),
            ).fetchall()
            db.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _detect_error_spikes():
    """Scan recent session JSONL files for per-agent error spikes (GH#954).

    Fires one grouped alert when a session emits >= ERROR_SPIKE_THRESHOLD
    error events within the last ERROR_SPIKE_WINDOW_SEC seconds, instead of
    N separate alerts.  Dedup is handled by _fire_alert's per-rule_id cooldown.
    """
    from collections import Counter as _Counter

    now = time.time()
    window_start = now - _ERROR_SPIKE_WINDOW_SEC
    sessions_dir = _get_sessions_dir()
    if not os.path.isdir(sessions_dir):
        return

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        if ".deleted." in fname or ".trajectory." in fname or ".checkpoint." in fname:
            continue
        fpath = os.path.join(sessions_dir, fname)
        try:
            if os.path.getmtime(fpath) < window_start - 5:
                continue
        except OSError:
            continue

        sid = fname[: -len(".jsonl")]
        error_events = []
        try:
            with open(fpath, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except Exception:
                        continue
                    if obj.get("type") != "error":
                        continue
                    raw_ts = (
                        obj.get("timestamp")
                        or obj.get("time")
                        or obj.get("created_at")
                    )
                    dt = _parse_event_timestamp(raw_ts, None)
                    if dt is None:
                        continue
                    try:
                        ts = dt.timestamp()
                    except Exception:
                        continue
                    if ts < window_start:
                        continue
                    error_events.append(obj)
        except OSError:
            continue

        if len(error_events) < _ERROR_SPIKE_THRESHOLD:
            continue

        msgs = []
        for ev in error_events:
            raw = ev.get("error") or ev.get("message") or ev.get("content") or ""
            if isinstance(raw, dict):
                raw = raw.get("content") or raw.get("text") or str(raw)
            msgs.append(str(raw)[:80])
        dominant = _Counter(msgs).most_common(1)[0][0] if msgs else "unknown error"

        agent_label = sid if len(sid) <= 24 else sid[:24]
        count = len(error_events)
        alert_msg = (
            f"Error spike: {agent_label}: {dominant} "
            f"({count}× in {_ERROR_SPIKE_WINDOW_SEC}s)"
        )
        rule_id = (
            "error_spike_"
            + sid[:20]
            + "_"
            + dominant[:30].replace(" ", "_").replace("/", "_")
        )
        _fire_alert(
            rule_id=rule_id,
            alert_type="error_spike",
            message=alert_msg,
            channels=["banner"],
            severity="error",
        )


def _budget_monitor_loop():
    """Background thread: check for anomalies, agent-down, and custom alert rules."""
    global \
        _budget_alert_cooldowns, \
        _security_posture_hash, \
        _budget_paused, \
        _budget_paused_at, \
        _budget_paused_reason
    while True:
        time.sleep(60)
        try:
            now = time.time()

            # Agent-down check
            if (
                _otel_last_received > 0
                and (now - _otel_last_received) > _AGENT_DOWN_SECONDS
            ):
                _fire_alert(
                    rule_id="agent_down",
                    alert_type="agent_down",
                    message=f"Agent appears down: no OTLP data for {int((now - _otel_last_received) / 60)} minutes",
                    channels=["banner", "telegram"],
                )

            # Heartbeat gap check
            if _last_heartbeat_ts > 0:
                hb_gap = now - _last_heartbeat_ts
                hb_threshold = _heartbeat_interval_sec * 1.5
                if hb_gap > hb_threshold:
                    if _heartbeat_silent_since == 0:
                        globals()["_heartbeat_silent_since"] = now
                    gap_min = int(hb_gap / 60)
                    _fire_alert(
                        rule_id="heartbeat_gap",
                        alert_type="heartbeat_silent",
                        message=f"Agent heartbeat silent for {gap_min} minutes (expected every {int(_heartbeat_interval_sec / 60)}m)",
                        channels=["banner", "telegram"],
                    )

            # Anomaly check: today's cost > 2x 7-day average
            status = _get_budget_status()
            daily_spent = status["daily_spent"]
            if daily_spent > 0:
                week_avg = (
                    status["weekly_spent"] / 7 if status["weekly_spent"] > 0 else 0
                )
                if week_avg > 0 and daily_spent > week_avg * 2:
                    ratio = daily_spent / week_avg
                    _fire_alert(
                        rule_id="anomaly_daily",
                        alert_type="anomaly",
                        message=f"Spending anomaly: today ${daily_spent:.2f} is {ratio:.1f}x the 7-day average (${week_avg:.2f}/day)",
                        channels=["banner", "telegram"],
                    )
                    _dispatch_configured_webhooks(
                        "cost_spike",
                        {
                            "type": "cost_spike",
                            "agent": "main",
                            "cost_usd": round(daily_spent, 4),
                            "threshold": round(week_avg * 2, 4),
                            "timestamp": now,
                            "message": f"Cost spike detected: {ratio:.1f}x daily average",
                        },
                    )

            # Token velocity alert (GH#313): detect runaway agent loops
            try:
                vel = _compute_velocity_status()
                if vel["active"]:
                    reasons_str = "; ".join(vel["reasons"])
                    sid_hint = (
                        f" (session: {vel['triggeringSession'][:12]}...)"
                        if vel.get("triggeringSession")
                        else ""
                    )
                    msg = f"\u26a1 Runaway loop detected{sid_hint}: {reasons_str}"
                    _fire_alert(
                        rule_id="token_velocity",
                        alert_type="token_velocity",
                        message=msg,
                        channels=["banner", "telegram"],
                    )
            except Exception as _vel_err:
                print(f"Warning: velocity check failed: {_vel_err}")
            # Error-spike detection (GH#954): per-session N-errors-in-window grouping
            try:
                _detect_error_spikes()
            except Exception as _spike_err:
                print(f"Warning: error spike check failed: {_spike_err}")


            # Agent error-rate check from webhook channel metrics (last 60 minutes)
            window_start = now - 3600
            total_wh = 0
            error_wh = 0
            with _metrics_lock:
                for e in metrics_store.get("webhooks", []):
                    ts = e.get("timestamp", 0)
                    if ts < window_start:
                        continue
                    total_wh += 1
                    et = str(e.get("type", "")).lower()
                    if et.endswith(".error") or "error" in et:
                        error_wh += 1
            if total_wh >= 10:
                error_rate = (error_wh / total_wh) * 100.0
                if error_rate >= 20.0:
                    rule_id = "agent_error_rate_high"
                    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                    if now - last_fired >= 1800:
                        _budget_alert_cooldowns[rule_id] = now
                        msg = f"Agent error rate high: {error_rate:.1f}% ({error_wh}/{total_wh}) in the last hour"
                        _fire_alert(
                            rule_id=rule_id,
                            alert_type="agent_error_rate",
                            message=msg,
                            channels=["banner", "telegram"],
                        )
                        _dispatch_configured_webhooks(
                            "agent_error_rate",
                            {
                                "type": "agent_error_rate",
                                "agent": "main",
                                "cost_usd": round(status.get("daily_spent", 0), 4),
                                "threshold": 20.0,
                                "timestamp": now,
                                "message": msg,
                            },
                        )

            # Security posture change check
            posture = _detect_security_metadata() or {}
            posture_hash = json.dumps(posture, sort_keys=True)
            if not _security_posture_hash:
                _security_posture_hash = posture_hash
            elif posture_hash != _security_posture_hash:
                _security_posture_hash = posture_hash
                msg = "Security posture changed (sandbox/auth/network settings updated)"
                _fire_alert(
                    rule_id="security_posture_change",
                    alert_type="security",
                    message=msg,
                    channels=["banner", "telegram"],
                )
                _dispatch_configured_webhooks(
                    "security_posture_change",
                    {
                        "type": "security_posture_change",
                        "agent": "main",
                        "cost_usd": round(status.get("daily_spent", 0), 4),
                        "threshold": 0,
                        "timestamp": now,
                        "message": msg,
                    },
                )

            # Daily threshold auto-pause/alert (absolute USD)
            cfg = _get_budget_config()
            auto_thr = float(cfg.get("auto_pause_threshold_usd", 0) or 0)
            auto_action = str(cfg.get("auto_pause_action", "pause") or "pause").lower()
            if auto_thr > 0 and status.get("daily_spent", 0) >= auto_thr:
                # Issue #1169: Pro-gate the auto-pause action. Free users
                # get the same banner, the gateway just keeps running.
                if auto_action == "pause" and not _auto_pause_allowed():
                    auto_action = "alert"
                if auto_action == "pause" and not _budget_paused:
                    _budget_paused = True
                    _budget_paused_at = now
                    _budget_paused_reason = f"Auto-pause threshold exceeded: ${status['daily_spent']:.2f} / ${auto_thr:.2f}"
                    _fire_alert(
                        rule_id="auto_pause_daily_usd",
                        alert_type="threshold",
                        message=f"AUTO-PAUSE: daily spend ${status['daily_spent']:.2f} exceeded ${auto_thr:.2f}",
                        channels=["banner", "telegram"],
                    )
                    _dispatch_configured_webhooks(
                        "daily_threshold_breached",
                        {
                            "type": "daily_threshold_breached",
                            "agent": "main",
                            "cost_usd": round(status.get("daily_spent", 0), 4),
                            "threshold": round(auto_thr, 4),
                            "timestamp": now,
                            "message": _budget_paused_reason,
                        },
                    )
                    _pause_gateway()
                elif auto_action == "alert":
                    rule_id = "auto_pause_daily_alert_only"
                    last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                    if now - last_fired >= 1800:
                        _budget_alert_cooldowns[rule_id] = now
                        msg = f"Daily spend alert threshold exceeded: ${status['daily_spent']:.2f} / ${auto_thr:.2f}"
                        _fire_alert(
                            rule_id=rule_id,
                            alert_type="threshold",
                            message=msg,
                            channels=["banner", "telegram"],
                        )
                        _dispatch_configured_webhooks(
                            "daily_threshold_breached",
                            {
                                "type": "daily_threshold_breached",
                                "agent": "main",
                                "cost_usd": round(status.get("daily_spent", 0), 4),
                                "threshold": round(auto_thr, 4),
                                "timestamp": now,
                                "message": msg,
                            },
                        )

            # Custom alert rules
            rules = _get_alert_rules()
            for rule in rules:
                if not rule.get("enabled"):
                    continue
                rule_id = rule["id"]
                rtype = rule["type"]
                threshold = rule["threshold"]
                channels = json.loads(rule.get("channels", '["banner"]'))
                cooldown = rule.get("cooldown_min", 30) * 60
                # Per-runtime scope: 'all' (node-wide) or one runtime id.
                # Scoped rules read per-runtime slices from DuckDB via the
                # daemon proxy; node-wide rules keep the legacy aggregates.
                rt_scope = str(rule.get("runtime") or "all").lower()

                last_fired = _budget_alert_cooldowns.get(rule_id, 0)
                if now - last_fired < cooldown:
                    continue

                fired = False
                msg = ""

                if rtype == "threshold":
                    _spent = status["daily_spent"]
                    if rt_scope != "all":
                        _spent = _runtime_daily_spend(rt_scope)
                    if _spent is not None and _spent >= threshold:
                        _scope_lbl = "" if rt_scope == "all" else f" [{rt_scope}]"
                        msg = f"Daily spending{_scope_lbl} ${_spent:.2f} exceeded threshold ${threshold:.2f}"
                        fired = True
                elif rtype == "spike":
                    # Spike: cost in last hour > threshold x average hourly rate
                    hour_ago = now - 3600
                    hour_cost = 0
                    with _metrics_lock:
                        for e in metrics_store["cost"]:
                            if e.get("timestamp", 0) >= hour_ago:
                                hour_cost += e.get("usd", 0)
                    avg_hourly = status["daily_spent"] / max(
                        1,
                        (
                            now
                            - datetime.now()
                            .replace(hour=0, minute=0, second=0, microsecond=0)
                            .timestamp()
                        )
                        / 3600,
                    )
                    if avg_hourly > 0 and hour_cost > avg_hourly * threshold:
                        msg = f"Spending spike: ${hour_cost:.2f} in last hour ({(hour_cost / avg_hourly):.1f}x average)"
                        fired = True
                elif rtype == "token_spike":
                    if rt_scope != "all":
                        _tpm = _runtime_tokens_per_min(rt_scope)
                        if _tpm is not None and _tpm >= threshold:
                            msg = (
                                f"Token spike [{rt_scope}]: {int(_tpm):,} tokens/min "
                                f"(threshold: {int(threshold):,}/min)"
                            )
                            fired = True
                    else:
                        try:
                            vel = _compute_velocity_status()
                        except Exception:
                            vel = None
                        if vel:
                            tokens_per_min = vel.get("tokensIn2Min", 0) / 2.0
                            if tokens_per_min >= threshold:
                                sid = vel.get("triggeringSession") or ""
                                sid_hint = f" (session: {sid[:12]}...)" if sid else ""
                                msg = (
                                    f"Token spike: {int(tokens_per_min):,} tokens/min "
                                    f"(threshold: {int(threshold):,}/min){sid_hint}"
                                )
                                fired = True
                elif rtype == "agent_down":
                    # "Agent offline > N min" (UI alert_type ``node_offline``).
                    # Founder 2026-08-15: this rtype has been accepted by the
                    # POST validator since the self-hosted bridge landed but
                    # never had a branch here, so every rule created from the
                    # tab's "Agent offline" row was a silent no-op.
                    #
                    # Signal is the most recent REAL agent event in DuckDB —
                    # not OTLP (the hardcoded ``agent_down`` monitor above
                    # keys off ``_otel_last_received``, which stays 0 on the
                    # many installs without ``[otel]``, so it never fires
                    # there either). ``exclude_daemon`` keeps ClawMetry's own
                    # diagnostics from masking a dead agent as "alive".
                    try:
                        from datetime import datetime as _dt2, timezone as _tz2
                        from routes.local_query import local_store_via_daemon
                        _rows = local_store_via_daemon(
                            "query_events", limit=1, exclude_daemon=True,
                            **({"runtime": rt_scope} if rt_scope != "all" else {}),
                        ) or []
                        _last_iso = (_rows[0].get("ts") or "") if _rows else ""
                        if _last_iso:
                            _last = _dt2.fromisoformat(
                                str(_last_iso).replace("Z", "+00:00")
                            )
                            if _last.tzinfo is None:
                                _last = _last.replace(tzinfo=_tz2.utc)
                            _idle_min = (
                                _dt2.now(_tz2.utc) - _last
                            ).total_seconds() / 60.0
                            if _idle_min >= threshold:
                                _scope_lbl = (
                                    "" if rt_scope == "all" else f" [{rt_scope}]"
                                )
                                msg = (
                                    f"Agent offline{_scope_lbl}: no activity for "
                                    f"{int(_idle_min)} min "
                                    f"(threshold: {int(threshold)} min)"
                                )
                                fired = True
                    except Exception:
                        pass
                elif rtype == "session_cost":
                    # "Session cost > $N" (UI alert_type ``session_cost``).
                    # Previously mapped onto ``threshold``, which evaluates
                    # DAILY spend — so a $5 per-session rule actually fired on
                    # the whole day's total. This checks the costliest single
                    # session in the last 24h, which is what the row promises.
                    #
                    # Cost is API-equivalent (token split x API rates), never
                    # the user's invoice — say so, per the cost-copy honesty
                    # pass (a Max-plan subscriber pays $0 incremental).
                    try:
                        from datetime import datetime as _dt3, timedelta as _td3, timezone as _tz3
                        from routes.local_query import local_store_via_daemon
                        _since = (_dt3.now(_tz3.utc) - _td3(hours=24)).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                        _sessions = local_store_via_daemon(
                            "query_sessions", since=_since, limit=500,
                        ) or []
                        _worst = None
                        for _s in _sessions:
                            _sid = _s.get("session_id") or ""
                            if rt_scope != "all" and _session_runtime_of(_sid) != rt_scope:
                                continue
                            try:
                                _c = float(_s.get("cost_usd") or 0)
                            except (TypeError, ValueError):
                                continue
                            if _c >= threshold and (_worst is None or _c > _worst[1]):
                                _worst = (_sid, _c)
                        if _worst:
                            _scope_lbl = "" if rt_scope == "all" else f" [{rt_scope}]"
                            msg = (
                                f"Session cost{_scope_lbl}: session "
                                f"{_worst[0][:12]} reached ${_worst[1]:.2f} "
                                f"(threshold: ${threshold:.2f}) - API-equivalent, "
                                f"not a billed amount"
                            )
                            fired = True
                    except Exception:
                        pass
                elif rtype == "unproductive_burn":
                    # Issue #1707 — forward-progress signal. Fires when any
                    # session burns >= ``threshold`` tokens per state delta
                    # over the last 10 min window (genuine spinning, not just
                    # busy productive burn). Pro rule.
                    try:
                        from datetime import datetime as _dt, timedelta as _td, timezone as _tz
                        from routes.local_query import local_store_via_daemon
                        since_iso = (_dt.now(_tz.utc) - _td(minutes=10)).strftime(
                            "%Y-%m-%dT%H:%M:%SZ"
                        )
                        rows = local_store_via_daemon(
                            "query_forward_progress", since=since_iso,
                        ) or []
                        worst = None
                        for r in rows:
                            try:
                                if rt_scope != "all" and _session_runtime_of(
                                        r.get("session_id") or "") != rt_scope:
                                    continue
                                if float(r.get("ratio") or 0) >= float(threshold):
                                    if worst is None or r["ratio"] > worst["ratio"]:
                                        worst = r
                            except (TypeError, ValueError):
                                continue
                        if worst:
                            sid = (worst.get("session_id") or "")[:12]
                            msg = (
                                f"Unproductive burn: session {sid} burned "
                                f"{int(worst['tokens']):,} tokens with "
                                f"{int(worst['state_deltas'])} state deltas "
                                f"(ratio: {int(worst['ratio']):,} tok/delta, "
                                f"threshold: {int(threshold):,})"
                            )
                            fired = True
                    except Exception:
                        pass

                if fired:
                    _budget_alert_cooldowns[rule_id] = now
                    try:
                        with _fleet_db_lock:
                            db = _fleet_db()
                            # Belt-and-suspenders cross-evaluator dedup.
                            # The sync daemon's _evaluate_alerts_local
                            # writes to this SAME alert_history table but
                            # holds a separate per-process cooldown memo,
                            # so before this check the same rule_id could
                            # land twice within a second (live repro
                            # 2026-07-15: ids 3,4 rule 2f270a9c, both
                            # channel=banner). Skip the INSERT when a fire
                            # of the same rule_id already lives inside the
                            # rule's own cooldown window; cooldown=0
                            # disables the check so explicit no-cooldown
                            # rules still fire every tick.
                            skip_insert = False
                            try:
                                cd_int = int(cooldown or 0)
                            except (TypeError, ValueError):
                                cd_int = 0
                            if cd_int > 0:
                                cutoff = now - cd_int
                                existing = db.execute(
                                    "SELECT 1 FROM alert_history "
                                    "WHERE rule_id = ? AND fired_at > ? "
                                    "LIMIT 1",
                                    (rule_id, cutoff),
                                ).fetchone()
                                skip_insert = existing is not None
                            if not skip_insert:
                                for ch in channels:
                                    db.execute(
                                        "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
                                        "VALUES (?, ?, ?, ?, ?)",
                                        (rule_id, rtype, msg, ch, now),
                                    )
                                db.commit()
                            db.close()
                    except Exception:
                        pass
                    for ch in channels:
                        if ch == "telegram":
                            _send_telegram_alert(msg)
                        elif ch == "webhook":
                            webhook_url = rule.get("webhook_url", "")
                            if webhook_url:
                                _send_webhook_alert(
                                    webhook_url,
                                    {"type": rtype, "message": msg, "timestamp": now},
                                )

        except Exception as e:
            print(f"Warning: Budget monitor error: {e}")


def _start_budget_monitor_thread():
    """Start the background budget monitor thread."""
    t = threading.Thread(target=_budget_monitor_loop, daemon=True)
    t.start()


# ── OTLP Protobuf Helpers ──────────────────────────────────────────────


def _otel_attr_value(val):
    """Convert an OTel AnyValue to a Python value."""
    if val.HasField("string_value"):
        return val.string_value
    if val.HasField("int_value"):
        return val.int_value
    if val.HasField("double_value"):
        return val.double_value
    if val.HasField("bool_value"):
        return val.bool_value
    return str(val)


def _get_data_points(metric):
    """Extract data points from a metric regardless of type."""
    if metric.HasField("sum"):
        return metric.sum.data_points
    elif metric.HasField("gauge"):
        return metric.gauge.data_points
    elif metric.HasField("histogram"):
        return metric.histogram.data_points
    elif metric.HasField("summary"):
        return metric.summary.data_points
    return []


def _get_dp_value(dp):
    """Extract the numeric value from a data point."""
    if hasattr(dp, "as_double") and dp.as_double:
        return dp.as_double
    if hasattr(dp, "as_int") and dp.as_int:
        return dp.as_int
    if hasattr(dp, "sum") and dp.sum:
        return dp.sum
    if hasattr(dp, "count") and dp.count:
        return dp.count
    return 0


def _get_dp_attrs(dp):
    """Extract attributes from a data point."""
    attrs = {}
    for attr in dp.attributes:
        attrs[attr.key] = _otel_attr_value(attr.value)
    return attrs


# ── Runtime-profile metrics (WO-57) ─────────────────────────────────────────
#
# The receiver knows OpenTelemetry, not vendors. What a runtime calls its
# counters (and which of them may touch a tile) arrives as an
# ``OtelRuntimeProfile`` (clawmetry/otel_profiles.py): free runtimes register
# from this repo, paid ones from clawmetry-pro. With no profile registered a
# ``<vendor>.*`` metric is ignored exactly as before.
#
# Cost and input/output tokens for these runtimes ALSO arrive on the request
# log record, which the logs path already turns into cost/usage tiles and
# ``llm_call`` events. Feeding the same dollars in from a metric would double
# the tile, so a profile's metrics are ledger-only, with one exception: the
# ``tile_token_metric``'s typed points (cache reads / cache writes, which the
# log record does not carry per type) reach the tokens cache.
_OTEL_CUMULATIVE = 2  # AggregationTemporality.AGGREGATION_TEMPORALITY_CUMULATIVE


def _otel_profile_for_resource(resource_attrs):
    """The registered profile for this emitter, or None."""
    try:
        from clawmetry import otel_profiles
        return otel_profiles.by_service_name(
            (resource_attrs or {}).get("service.name") or "")
    except Exception:
        return None


def _dp_value_or_none(dp):
    """The data point's number, or ``None`` when it carried none. Never turn
    "absent" into ``0``: a zero that was sent is a fact, a zero we invented
    is not (blueprint: no fabricated figures)."""
    # protobuf NumberDataPoint: the number is a oneof; HasField on a name
    # the message does not define RAISES, so ask the oneof by name first.
    which = getattr(dp, "WhichOneof", None)
    if callable(which):
        try:
            field = which("value")
            if field == "as_int":
                return int(dp.as_int)
            if field == "as_double":
                return float(dp.as_double)
        except Exception:
            pass
    has = getattr(dp, "HasField", None)
    if callable(has):
        for name, cast in (("as_int", int), ("as_double", float),
                           ("sum", float), ("count", int)):
            try:
                if has(name):
                    return cast(getattr(dp, name))
            except Exception:
                continue
        return None
    try:
        return _get_dp_value(dp)
    except Exception:
        return None


def _metric_is_cumulative(metric):
    try:
        if metric.HasField("sum"):
            t = getattr(metric.sum, "aggregation_temporality", 0)
            return int(t or 0) == _OTEL_CUMULATIVE
    except Exception:
        pass
    return False


def _profile_metric_record_id(service_name, session_id, name, ts_ns, attrs, value):
    import hashlib as _hl
    parts = [str(service_name or ""), str(session_id or ""), str(name or ""),
             str(ts_ns or 0), repr(value)]
    for k in sorted(attrs):
        parts.append("%s=%s" % (k, attrs[k]))
    return _hl.sha256("\x1f".join(parts).encode("utf-8", "replace")).hexdigest()


def _profile_metric(prof, name, metric, resource_attrs, rows):
    """Map one profile-owned metric into tiles (typed token points only)
    and ledger rows (every data point). Appends to ``rows``; a bad data
    point is skipped, never raised."""
    service_name = resource_attrs.get("service.name") or (prof.service_names or ("",))[0]
    received_at = time.time()
    # A CUMULATIVE sum re-sends the running total every interval; adding it
    # to a tile would grow without bound. Anything cumulative is ledger-only.
    cumulative = _metric_is_cumulative(metric)
    for dp in _get_data_points(metric):
        try:
            attrs = _get_dp_attrs(dp)
            value = _dp_value_or_none(dp)
            ts_ns = int(getattr(dp, "time_unix_nano", 0) or 0)
            ts = ts_ns / 1e9 if ts_ns > 0 else received_at
            # Ledger rows keep the id as sent (REQ-OBS-006); nothing here
            # writes events, so no prefixed form is needed.
            session_id = (attrs.get("session.id")
                          or resource_attrs.get("session.id") or None)
            model = attrs.get("model") or resource_attrs.get("model") or ""
            mtype = str(attrs.get("type") or "").strip().lower()
            cache_field = (prof.token_type_fields or {}).get(mtype)
            # The id first: the tile push below must be as idempotent as the
            # ledger write, or a retried batch doubles the cache tokens.
            rid = _profile_metric_record_id(
                service_name, session_id, name, ts_ns, attrs, value)
            if (prof.tile_token_metric and name == prof.tile_token_metric
                    and cache_field and value is not None and not cumulative):
                try:
                    n = int(value)
                except (TypeError, ValueError):
                    n = 0
                if n and not _otlp_seen(rid):
                    # ``total`` stays 0: cache tokens are not fresh tokens
                    # and must not inflate the tokens tile.
                    _add_metric("tokens", {
                        "timestamp": ts, "input": 0, "output": 0, "total": 0,
                        cache_field: n, "model": model,
                        "channel": "", "provider": "",
                        "_source": name,
                    })
            rows.append({
                "record_id": rid, "ts": ts, "received_at": received_at,
                "event_name": name, "session_id": session_id,
                "user_id": attrs.get("user.id") or resource_attrs.get("user.id"),
                "user_email": (attrs.get("user.email")
                               or resource_attrs.get("user.email")),
                "org_id": (attrs.get("organization.id")
                           or resource_attrs.get("organization.id")),
                "team": (attrs.get("team.id") or resource_attrs.get("team.id")
                         or resource_attrs.get("department")),
                "repo": _otlp_repo_key(attrs.get("repository")
                                       or resource_attrs.get("repository")),
                "node_id": (resource_attrs.get("node.id")
                            or resource_attrs.get("host.name") or "otlp"),
                "agent_type": prof.runtime, "service_name": service_name,
                "model": model or None, "provider": None,
                # Cost / token COLUMNS stay empty on metric rows: the rollup
                # sums those columns and the request log row already
                # carries the same dollars. The value rides in attributes.
                "cost_usd": None, "tokens_input": None, "tokens_output": None,
                "token_count": None, "duration_ms": None,
                "tool_name": attrs.get("tool_name"),
                "decision": attrs.get("decision"),
                "success": None,
                "attributes": {"resource": resource_attrs, "record": attrs,
                               "value": value, "metric": name},
            })
        except Exception:
            continue


def _process_otlp_metrics(pb_data, content_encoding=None, content_type=None):
    """Decode OTLP metrics protobuf/JSON and store relevant data."""
    req = _otlp_request(pb_data, "metrics", content_encoding, content_type)
    _prof_rows = []  # profile-owned ledger rows, one put_otlp_batch per POST

    for resource_metrics in req.resource_metrics:
        resource_attrs = {}
        if resource_metrics.resource:
            for attr in resource_metrics.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_metrics in resource_metrics.scope_metrics:
            for metric in scope_metrics.metrics:
                name = metric.name
                ts = time.time()

                _prof = None
                try:
                    from clawmetry import otel_profiles as _op
                    _prof = _op.for_metric(name)
                except Exception:
                    _prof = None
                if _prof is not None:
                    _profile_metric(_prof, name, metric, resource_attrs, _prof_rows)
                    continue
                if name == "openclaw.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": attrs.get("input_tokens", 0),
                                "output": attrs.get("output_tokens", 0),
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.cost.usd":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "cost",
                            {
                                "timestamp": ts,
                                "usd": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name == "openclaw.run.duration_ms":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "runs",
                            {
                                "timestamp": ts,
                                "duration_ms": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                            },
                        )
                elif name == "openclaw.context.tokens":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": _get_dp_value(dp),
                                "output": 0,
                                "total": _get_dp_value(dp),
                                "model": attrs.get(
                                    "model", resource_attrs.get("model", "")
                                ),
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": attrs.get(
                                    "provider", resource_attrs.get("provider", "")
                                ),
                            },
                        )
                elif name in (
                    "openclaw.message.processed",
                    "openclaw.message.queued",
                    "openclaw.message.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        outcome = (
                            "processed"
                            if "processed" in name
                            else ("queued" if "queued" in name else "duration")
                        )
                        _add_metric(
                            "messages",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "outcome": outcome,
                                "duration_ms": _get_dp_value(dp)
                                if "duration" in name
                                else 0,
                            },
                        )
                elif name in (
                    "openclaw.webhook.received",
                    "openclaw.webhook.error",
                    "openclaw.webhook.duration_ms",
                ):
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        wtype = (
                            "received"
                            if "received" in name
                            else ("error" if "error" in name else "duration")
                        )
                        _add_metric(
                            "webhooks",
                            {
                                "timestamp": ts,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "type": wtype,
                            },
                        )
                # OTel GenAI metric semconv (OpenLLMetry / OTel SDK auto-instrument
                # emit these instead of the openclaw.* names). gen_ai.client.
                # token.usage is a histogram/sum keyed by gen_ai.token.type
                # (input|output); gen_ai.client.operation.duration is the
                # request latency. Map them onto the same tiles as the
                # openclaw.* path so a "bring your own agent" install lights the
                # token / runs tiles. Unknown metrics stay silently dropped.
                elif name == "gen_ai.client.token.usage":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        ttype = str(attrs.get("gen_ai.token.type", "")).lower()
                        try:
                            val = int(_get_dp_value(dp))
                        except (TypeError, ValueError):
                            continue
                        model = attrs.get("gen_ai.request.model") or attrs.get(
                            "model", resource_attrs.get("model", "")
                        )
                        provider = attrs.get("gen_ai.system") or attrs.get(
                            "gen_ai.provider.name"
                        ) or attrs.get("provider", resource_attrs.get("provider", ""))
                        _add_metric(
                            "tokens",
                            {
                                "timestamp": ts,
                                "input": val if ttype == "input" else 0,
                                "output": val if ttype == "output" else 0,
                                "total": val,
                                "model": model,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                                "provider": provider,
                            },
                        )
                elif name == "gen_ai.client.operation.duration":
                    for dp in _get_data_points(metric):
                        attrs = _get_dp_attrs(dp)
                        try:
                            # semconv unit is seconds; the runs tile stores ms.
                            dur_ms = float(_get_dp_value(dp)) * 1000.0
                        except (TypeError, ValueError):
                            continue
                        model = attrs.get("gen_ai.request.model") or attrs.get(
                            "model", resource_attrs.get("model", "")
                        )
                        _add_metric(
                            "runs",
                            {
                                "timestamp": ts,
                                "duration_ms": dur_ms,
                                "model": model,
                                "channel": attrs.get(
                                    "channel", resource_attrs.get("channel", "")
                                ),
                            },
                        )

    if _prof_rows:
        try:
            from clawmetry import local_store as _ls
            _st = _ls.get_store()
            if _st is not None:
                # Keyword args: the dashboard's _ProxyStore forwards **kwargs
                # only (same foot-gun as put_span / put_otlp_batch below).
                _st.put_otlp_batch(records=_prof_rows, events=[])
        except Exception as e:
            try:
                import logging as _lg
                _lg.getLogger("clawmetry.dashboard").warning(
                    "profile metrics ledger write failed: %s", e)
            except Exception:
                pass


_OTEL_SPAN_KIND_NAMES = {
    0: "UNSPECIFIED",
    1: "INTERNAL",
    2: "SERVER",
    3: "CLIENT",
    4: "PRODUCER",
    5: "CONSUMER",
}

_OTEL_STATUS_CODE_NAMES = {
    0: "UNSET",
    1: "OK",
    2: "ERROR",
}


def _hex(b):
    """OTel proto carries trace_id / span_id / parent_span_id as raw bytes.
    DuckDB stores them as hex strings (matches the OTel spec's canonical
    text form). ``b'' → ''`` so parent_span_id stays falsy for root spans."""
    if not b:
        return ""
    try:
        return b.hex() if isinstance(b, (bytes, bytearray)) else str(b)
    except Exception:
        return ""


def _otel_to_row(span, resource_attrs):
    """Translate one OTel proto Span (plus its resource attributes) to the
    dict shape :func:`clawmetry.local_store.LocalStore.ingest_span` expects.

    Issue #1007 / epic #1006. Maps common OTel attribute conventions onto
    typed columns so the dashboard's usage / trace-tree views don't have
    to JSON-extract on every read:

      * ``gen_ai.request.model`` / ``llm.model`` / ``model`` → ``model``
      * ``gen_ai.usage.input_tokens`` / ``llm.usage.prompt_tokens`` →
        ``tokens_input``
      * ``gen_ai.usage.output_tokens`` / ``llm.usage.completion_tokens`` →
        ``tokens_output``
      * ``gen_ai.usage.total_tokens`` → ``token_count``
      * ``gen_ai.usage.cost_usd`` / ``llm.usage.cost`` → ``cost_usd``; when the
        exporter ships no cost (the OTel GenAI norm — cost is not a standard
        span attribute, so MLflow's OpenClaw plugin et al. emit token-only
        spans), it is derived from tokens × model pricing, cache-aware, with
        the provider resolved from ``gen_ai.provider.name`` / ``gen_ai.system``
        or inferred from the model — same as the #2049 event path.
      * ``gen_ai.tool.name`` / ``tool.name`` / ``code.function`` → ``tool_name``
      * ``gen_ai.conversation.id`` / ``session.id`` / ``openclaw.session_id`` →
        ``session_id``; when an exporter sends NONE of them (the OTel GenAI
        convention does not require one, and a plain SDK or OpenLLMetry on
        defaults sends none), the span's own ``trace_id`` supplies it as
        ``<agent_type>:trace:<trace_id>`` so the run still reaches Sessions /
        Cost / Guard (#5691). One trace is one run: measured across 265 real
        traces, ``trace_id`` maps to exactly one session and no session spans
        more than one trace. The ``<agent_type>:`` head is required, not
        cosmetic, because every session-id parser here reads the runtime from
        the text before the first colon; ``trace:`` marks the id as derived
        rather than sent. Not applied when ``agent_type`` is ``openclaw``,
        whose sessions come from transcripts and whose spans keep a null
        ``session_id``.
      * ``gen_ai.agent.id`` / ``agent.id`` / ``openclaw.agent_id`` (also from
        resource) → ``agent_id``
      * ``agent.type`` (also from resource) → ``agent_type``
      * ``gen_ai.input.messages`` / ``gen_ai.output.messages`` (current semconv)
        and the legacy ``gen_ai.prompt`` / ``gen_ai.completion`` → ``input`` /
        ``output``
      * Resource ``service.name`` → ``service_name``

    Targets the OpenTelemetry GenAI semantic conventions (v1.37) so spans from
    any conforming emitter — including MLflow's ``@mlflow/mlflow-openclaw``
    tracer — light up ClawMetry's trace tree and cost views without a bespoke
    per-SDK translator.

    Everything not projected lands in the ``attributes`` JSON blob so the
    span-detail panel can render any custom attributes the SDK exporter
    set (e.g. ``gen_ai.operation.name``, ``gen_ai.agent.name``). Span events /
    links are passed through as JSON arrays.
    """
    attrs = {}
    for attr in span.attributes:
        attrs[attr.key] = _otel_attr_value(attr.value)

    # deployment.environment is a RESOURCE attribute (deployment.environment
    # .name since semconv 1.27; the bare key before that), so it used to be
    # dropped with the rest of the resource. Keep it on the span's attribute
    # blob so a dev/tst/prod fleet (AgentCore's normal shape) stays separable
    # after ingest; the session materializer lifts it onto session metadata.
    if "deployment.environment" not in attrs:
        for _env_key in ("deployment.environment.name", "deployment.environment"):
            _env_val = attrs.get(_env_key) or resource_attrs.get(_env_key)
            if _env_val not in (None, ""):
                attrs["deployment.environment"] = str(_env_val)
                break

    # Time columns. OTel proto carries unix-nano; we store unix-seconds in
    # ``start_ts`` / ``end_ts`` (DOUBLE) so chart libs can format them
    # without converting twice.
    start_ts = (span.start_time_unix_nano or 0) / 1e9
    end_ts = (span.end_time_unix_nano or 0) / 1e9 or start_ts
    duration_ns = max(0, (span.end_time_unix_nano or 0) - (span.start_time_unix_nano or 0))
    duration_ms = duration_ns / 1_000_000.0

    # Status + kind.
    kind_id = getattr(span, "kind", 0) or 0
    kind_name = _OTEL_SPAN_KIND_NAMES.get(kind_id, str(kind_id))
    status_code_id = 0
    status_message = ""
    if span.HasField("status"):
        status_code_id = span.status.code
        status_message = span.status.message or ""
    status_code_name = _OTEL_STATUS_CODE_NAMES.get(status_code_id, str(status_code_id))

    # Attribute → typed-column projection. ``attrs`` first (per-span) so it
    # wins over ``resource_attrs`` (resource-level fallback) — same
    # precedence the OTel spec uses.
    def _pick(*keys):
        for k in keys:
            v = attrs.get(k)
            if v not in (None, ""):
                return v
            v = resource_attrs.get(k)
            if v not in (None, ""):
                return v
        return None

    def _pick_int(*keys):
        v = _pick(*keys)
        if v is None:
            return None
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    def _pick_float(*keys):
        v = _pick(*keys)
        if v is None:
            return None
        try:
            return float(v)
        except (TypeError, ValueError):
            return None

    model = _pick("gen_ai.request.model", "gen_ai.response.model", "llm.model", "model")
    tokens_input = _pick_int("gen_ai.usage.input_tokens", "llm.usage.prompt_tokens", "input_tokens")
    tokens_output = _pick_int("gen_ai.usage.output_tokens", "llm.usage.completion_tokens", "output_tokens")
    token_count = _pick_int("gen_ai.usage.total_tokens", "llm.usage.total_tokens", "total_tokens")
    if token_count is None and (tokens_input or tokens_output):
        token_count = (tokens_input or 0) + (tokens_output or 0)
    # Prompt-cache tokens (OTel GenAI semconv + Anthropic convention). Not
    # stored as typed columns — they ride the attributes blob — but read here
    # so the derived cost below is cache-aware (matches the #2049 event path).
    # A registered runtime profile may name these differently on its own
    # spans (WO-57); the aliases are data, the mapping stays generic.
    _prof = _otel_profile_for_resource(resource_attrs)
    _al = (_prof.span_attr_aliases if _prof is not None else {}) or {}
    # Two spellings, both live in the wild. The CURRENT OTel GenAI semantic
    # convention puts a dot before the noun --
    # ``gen_ai.usage.cache_read.input_tokens`` -- and that is what an
    # exporter emits once it opts in with
    # OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental, which is
    # what the migration guidance tells people to set. Reading only the
    # underscore spelling meant those spans reported ZERO cached tokens,
    # so the cache-aware cost path had nothing to be aware of and the
    # session's cost came out wrong -- and on a long agent session cache
    # reads are usually the majority of input tokens (#5685).
    #
    # ``_pick`` takes the first non-None, so a span carrying both forms is
    # counted once and nothing double-counts.
    cache_read = _pick_int("gen_ai.usage.cache_read.input_tokens",
                           "gen_ai.usage.cache_read_input_tokens", "cache_read_input_tokens",
                           *(_al.get("cache_read") or ())) or 0
    cache_write = _pick_int("gen_ai.usage.cache_creation.input_tokens",
                            "gen_ai.usage.cache_creation_input_tokens", "cache_creation_input_tokens",
                            *(_al.get("cache_write") or ())) or 0
    # Provider: OTel GenAI semconv renamed gen_ai.system -> gen_ai.provider.name.
    provider = _pick("gen_ai.provider.name", "gen_ai.system", "llm.provider", "provider") or ""
    cost_usd = _pick_float("gen_ai.usage.cost_usd", "llm.usage.cost", "cost_usd")
    # Cost is NOT an OTel-standard span attribute, so GenAI emitters (MLflow's
    # OpenClaw plugin, raw OpenAI/Anthropic auto-trace, …) ship token-only spans
    # that would read as $0 in our usage/cost views. Derive it the same way the
    # event ingest does (#2049): tokens x model pricing, cache-aware, provider
    # resolved from the model when the span omits it. Only fill when the exporter
    # supplied no cost at all, so an explicit cost (even 0 for a local model) wins.
    if cost_usd is None and model and (tokens_input or tokens_output or cache_read or cache_write):
        try:
            from clawmetry.providers_pricing import estimate_event_cost_usd
            derived = estimate_event_cost_usd(
                model,
                input_tokens=tokens_input or 0,
                output_tokens=tokens_output or 0,
                cache_read_tokens=cache_read,
                cache_write_tokens=cache_write,
                provider=provider,
            )
            if derived:
                cost_usd = derived
        except Exception:
            pass
    # tool.name: OTel GenAI semconv uses gen_ai.tool.name on execute_tool spans.
    tool_name = _pick("gen_ai.tool.name", "tool.name", "code.function",
                      *(_al.get("tool_name") or ()))
    # session/conversation: semconv uses gen_ai.conversation.id.
    session_id = _pick("gen_ai.conversation.id", "session.id", "openclaw.session_id", "session_id")
    agent_id = _pick("gen_ai.agent.id", "agent.id", "openclaw.agent_id", "agent_id") or "main"
    service_name = resource_attrs.get("service.name") or attrs.get("service.name")
    # Runtime identity. An explicit agent.type wins (OpenClaw / clawmetry-pro
    # adapters set it); otherwise derive it from the OTLP resource service.name
    # so OpenLLMetry-instrumented foreign apps appear as their OWN agent_type
    # ("my-langchain-app" -> "my_langchain_app") instead of mis-bucketing under
    # "openclaw". Absent service.name -> "custom". OpenClaw/clawmetry-known
    # service names stay "openclaw" so existing OpenClaw OTLP flows are intact.
    agent_type = _pick("agent.type", "openclaw.agent_type", "agent_type")
    if not agent_type:
        derived = _otlp_service_name_to_agent_type(service_name)
        agent_type = derived or "openclaw"
    node_id = _pick("node.id", "openclaw.node_id", "host.name")
    if _prof is not None and session_id and _prof.session_key_prefix:
        # The daemon's key for this runtime's sessions (``<runtime>:<id>``),
        # so the span joins the transcript session (WO-57). No profile: the
        # span keeps the bare id, as before.
        session_id = _prof.session_key(session_id)

    # Issue #5691: no conversation id at all. The span lands in ``spans`` and
    # no ``sessions`` row is ever produced, so the app is invisible to
    # Sessions / Cost / Guard while its data sits in the store. Nothing
    # errors, so nothing prompts anyone to look. Nothing in the GenAI
    # convention REQUIRES a conversation id, and a plain OTel SDK or
    # OpenLLMetry on defaults does not send one, so this is the common case.
    #
    # Fall back to the trace id. Measured on a live node before choosing it
    # (see the issue): across 265 real traces, ``trace_id`` maps to exactly
    # one session and no session spans more than one trace, so this
    # reproduces the mapping conforming exporters already produce rather than
    # inventing one. The feared "one trace per tool call" flood is not the
    # shape of real data either: median 2 spans per trace, p90 231, p90
    # duration ~2.4 h, which is a RUN, not a tool call.
    #
    # The key is ``<runtime>:trace:<id>``, NOT ``otlp:trace:<id>``. Every
    # session-id parser in this codebase (``_sid_runtime`` and its siblings in
    # sessions / bench / cohort / harness / health) takes the text before the
    # FIRST colon as the runtime, so an ``otlp:`` prefix would file every one
    # of these under a runtime literally named "otlp" instead of the app's own
    # ``agent_type`` -- the exact mis-bucketing
    # ``_otlp_service_name_to_agent_type`` exists to prevent, and a breach of
    # the per-runtime honesty gate. Keeping ``trace:`` as the second segment
    # marks the id as DERIVED, so a reader can tell it from a session id an
    # exporter actually sent.
    #
    # Confined to foreign apps on purpose. ``agent_type == "openclaw"`` is the
    # one population the materializer deliberately skips (OpenClaw sessions
    # come from transcripts, WO-55's ghost-session guard), so minting a key
    # there would put a session id on a span that joins NO session -- a
    # phantom, which is a bug we have shipped before. Those spans keep the
    # NULL they have today.
    if not session_id and agent_type != "openclaw":
        _tid = _hex(span.trace_id)
        if _tid:
            _derived = "trace:" + _tid
            session_id = (
                _prof.session_key(_derived)
                if (_prof is not None and _prof.session_key_prefix)
                else "{}:{}".format(agent_type, _derived)
            )

    # Span events: array of {time_unix_nano, name, attributes}.
    events = []
    for ev in span.events:
        ev_attrs = {}
        for a in ev.attributes:
            ev_attrs[a.key] = _otel_attr_value(a.value)
        events.append({
            "time_unix_nano": ev.time_unix_nano,
            "name": ev.name,
            "attributes": ev_attrs,
        })

    # Span links: array of {trace_id, span_id, attributes}.
    links = []
    for ln in span.links:
        ln_attrs = {}
        for a in ln.attributes:
            ln_attrs[a.key] = _otel_attr_value(a.value)
        links.append({
            "trace_id": _hex(ln.trace_id),
            "span_id": _hex(ln.span_id),
            "attributes": ln_attrs,
        })

    # input / output messages. The current semconv ships a single
    # ``gen_ai.input.messages`` / ``gen_ai.output.messages`` value, but
    # OpenLLMetry / traceloop-sdk emit INDEXED attributes instead:
    #   gen_ai.prompt.0.role, gen_ai.prompt.0.content, gen_ai.prompt.1.role, ...
    #   gen_ai.completion.0.role, gen_ai.completion.0.content, plus tool-call
    #   variants (gen_ai.completion.0.tool_calls.0.name / .arguments).
    # When the flat keys are absent we assemble an ordered messages list from
    # the indexed attrs so the same downstream column gets a structured value
    # (JSON-serialized by _to_blob, the same shape the flat path stores).
    _MSG_CAP = 200_000  # defensive total-size cap (matches the brain-blob house style)

    def _assemble_indexed(prefix):
        """Collect gen_ai.<prefix>.<i>.<field> into an ordered [{role, content,
        ...}] list. Returns None when no indexed attrs exist (caller falls back
        to the flat keys). Bounded by _MSG_CAP total chars so a pathological
        span can't blow the row up."""
        by_index = {}
        plen = len(prefix) + 1  # "gen_ai.prompt."
        for k, v in attrs.items():
            if not k.startswith(prefix + "."):
                continue
            rest = k[plen:]
            dot = rest.find(".")
            if dot <= 0:
                continue
            idx_str, field = rest[:dot], rest[dot + 1:]
            try:
                idx = int(idx_str)
            except ValueError:
                continue
            by_index.setdefault(idx, {})[field] = v
        if not by_index:
            return None
        out_msgs = []
        total = 0
        for idx in sorted(by_index.keys()):
            fields = by_index[idx]
            msg = {}
            role = fields.get("role")
            if role is not None:
                msg["role"] = role
            content = fields.get("content")
            if content is not None:
                msg["content"] = content
            # Tool-call variants (gen_ai.completion.0.tool_calls.0.name etc.)
            # and any other indexed sub-fields ride along verbatim so nothing
            # is silently dropped.
            for fk, fv in fields.items():
                if fk in ("role", "content"):
                    continue
                msg[fk] = fv
            if not msg:
                continue
            out_msgs.append(msg)
            try:
                total += len(str(content or "")) + len(str(role or ""))
            except Exception:
                pass
            if total >= _MSG_CAP:
                break
        return out_msgs or None

    input_val = (attrs.get("gen_ai.input.messages") or attrs.get("gen_ai.prompt")
                 or attrs.get("llm.prompts") or attrs.get("input"))
    if input_val is None:
        input_val = _assemble_indexed("gen_ai.prompt")
    output_val = (attrs.get("gen_ai.output.messages") or attrs.get("gen_ai.completion")
                  or attrs.get("llm.completions") or attrs.get("output"))
    if output_val is None:
        output_val = _assemble_indexed("gen_ai.completion")

    return {
        "span_id": _hex(span.span_id),
        "trace_id": _hex(span.trace_id),
        "parent_span_id": _hex(span.parent_span_id) or None,
        "agent_type": agent_type,
        "agent_id": agent_id,
        "node_id": node_id,
        "session_id": session_id,
        "service_name": service_name,
        "name": span.name,
        "kind": kind_name,
        "status_code": status_code_name,
        "status_message": status_message,
        "status": status_code_name,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "duration_ms": duration_ms,
        "duration_ns": duration_ns,
        "model": model,
        "tool_name": tool_name,
        "cost_usd": cost_usd,
        "token_count": token_count,
        "tokens_input": tokens_input,
        "tokens_output": tokens_output,
        "input": input_val,
        "output": output_val,
        "attributes": attrs,
        "events": events,
        "links": links,
    }


def _process_otlp_traces(pb_data, content_encoding=None, content_type=None):
    """Decode OTLP traces protobuf and extract relevant span data.

    Two-path design (issue #1007): we still feed the in-memory metrics
    cache (the live dashboard's hot path — sub-second tiles for tokens /
    runs / messages) AND persist every span to DuckDB via
    ``local_store.put_span`` so the trace tree / span detail views can
    query historical traces. The DuckDB write is best-effort wrapped in
    try/except — a write failure must NOT break the metrics cache path.
    """
    req = _otlp_request(pb_data, "traces", content_encoding, content_type)

    # session_id -> deployment.environment (or None) for every non-OpenClaw
    # span in this batch. Feeds ONE materialize_otlp_sessions call at the end
    # so span-only apps (AgentCore, OpenLLMetry) get a sessions row (WO-55).
    _otlp_sessions_seen = {}
    # WO-57: a runtime profile may name a span that means "blocked on a
    # human" (``wait_span_suffix``). Those become ``waiting_on_user`` events
    # on the session so turn anatomy can sum them.
    _otlp_wait_events = []
    _wait_tool_by_span = {}  # span_id -> tool_name, to name a wait by its parent

    # Resolve the local store lazily so unit tests that monkeypatch the
    # singleton in advance (or run without DuckDB) don't pay the import
    # cost upfront.
    _store = None
    try:
        from clawmetry import local_store as _ls
        _store = _ls.get_store()
    except Exception:
        _store = None

    for resource_spans in req.resource_spans:
        resource_attrs = {}
        if resource_spans.resource:
            for attr in resource_spans.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        for scope_spans in resource_spans.scope_spans:
            for span in scope_spans.spans:
                attrs = {}
                for attr in span.attributes:
                    attrs[attr.key] = _otel_attr_value(attr.value)

                ts = time.time()
                duration_ns = span.end_time_unix_nano - span.start_time_unix_nano
                duration_ms = duration_ns / 1_000_000

                span_name = span.name.lower()
                # Count a "run" for OpenClaw-shaped span names AND for GenAI LLM
                # spans: OpenLLMetry / traceloop-sdk name them ``openai.chat`` /
                # ``anthropic.chat`` / ``<vendor>.completion`` and tag the
                # operation on ``gen_ai.operation.name`` (chat / text_completion
                # / generate_content). Without this a "bring your own agent"
                # install records spans but the live Runs tile stays at zero.
                _genai_op = (attrs.get("gen_ai.operation.name") or "").lower()
                _is_genai_run = (
                    _genai_op in ("chat", "text_completion", "generate_content")
                    or span_name.endswith(".chat")
                    or span_name.endswith(".completion")
                    or span_name in ("openai.chat", "anthropic.chat")
                )
                if "run" in span_name or "completion" in span_name or _is_genai_run:
                    _add_metric(
                        "runs",
                        {
                            "timestamp": ts,
                            "duration_ms": duration_ms,
                            "model": attrs.get(
                                "model", resource_attrs.get("model", "")
                            ),
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                        },
                    )
                elif "message" in span_name:
                    _add_metric(
                        "messages",
                        {
                            "timestamp": ts,
                            "channel": attrs.get(
                                "channel", resource_attrs.get("channel", "")
                            ),
                            "outcome": "processed",
                            "duration_ms": duration_ms,
                        },
                    )

                # Generic cost/token mapping from span ATTRIBUTES. Codex (and
                # OTel-instrumented agents) emit cost/token telemetry on spans
                # like ``codex.api_request`` — without this they persist to the
                # spans table but never light the cost/usage tiles. OpenClaw cost
                # arrives via the /v1/metrics path (openclaw.cost.usd), not span
                # attrs, so this doesn't double-count. Same shape as /v1/logs
                # (#2591).
                _sc = (attrs.get("cost_usd") or attrs.get("cost.usd")
                       or attrs.get("cost") or attrs.get("gen_ai.usage.cost_usd"))
                if _sc is not None:
                    try:
                        _add_metric("cost", {
                            "timestamp": ts, "usd": float(_sc),
                            "model": attrs.get("model", resource_attrs.get("model", "")),
                            "channel": attrs.get("channel", resource_attrs.get("channel", "")),
                            "provider": attrs.get("provider", resource_attrs.get("provider", "")),
                        })
                    except (TypeError, ValueError):
                        pass
                _si = (attrs.get("gen_ai.usage.input_tokens")
                       or attrs.get("input_tokens") or attrs.get("tokens.input")
                       or attrs.get("prompt_tokens"))
                _so = (attrs.get("gen_ai.usage.output_tokens")
                       or attrs.get("output_tokens") or attrs.get("tokens.output")
                       or attrs.get("completion_tokens"))
                if _si is not None or _so is not None:
                    try:
                        _i, _o = int(_si or 0), int(_so or 0)
                        _add_metric("tokens", {
                            "timestamp": ts, "input": _i, "output": _o, "total": _i + _o,
                            "model": attrs.get("model", resource_attrs.get("model", "")),
                            "channel": attrs.get("channel", resource_attrs.get("channel", "")),
                            "provider": attrs.get("provider", resource_attrs.get("provider", "")),
                        })
                    except (TypeError, ValueError):
                        pass

                # DuckDB write-through. Failures here are logged but do not
                # break the metrics cache path above (which is what the
                # live tiles read from). Idempotent on span_id — OTLP
                # retries land as INSERT OR REPLACE without duping.
                if _store is not None:
                    try:
                        # Keyword arg is REQUIRED: in the dashboard process
                        # get_store() returns a _ProxyStore that forwards to the
                        # daemon writer, and the proxy only forwards **kwargs
                        # (positional args are dropped). With a positional span
                        # the write silently no-ops and OTLP spans never persist
                        # whenever the daemon owns the writer lock (i.e. every
                        # real install). put_span is allowlisted in
                        # routes/local_query._DAEMON_METHODS so the daemon
                        # executes the real write.
                        _row = _otel_to_row(span, resource_attrs)
                        _store.put_span(span=_row)
                        # Track for session materialization (WO-55). OpenClaw
                        # sessions come from transcripts; only foreign apps
                        # need a span-derived sessions row.
                        _sid = _row.get("session_id")
                        _atype = _row.get("agent_type") or ""
                        _wprof = _otel_profile_for_resource(resource_attrs)
                        _wsuf = (_wprof.wait_span_suffix if _wprof is not None else "") or ""
                        if _wprof is not None and _row.get("tool_name"):
                            _wait_tool_by_span[str(_hex(span.span_id))] = _row.get("tool_name")
                        if (_wsuf and _sid
                                and span.name.lower().endswith(_wsuf.lower())):
                            try:
                                _dur_ms = max(0.0, (span.end_time_unix_nano
                                                    - span.start_time_unix_nano) / 1e6)
                                _st_s = (span.start_time_unix_nano or 0) / 1e9 or time.time()
                                _otlp_wait_events.append({
                                    "id": "otlp:span:" + str(_hex(span.span_id)),
                                    "node_id": _row.get("node_id") or "otlp",
                                    "agent_type": _wprof.runtime,
                                    "agent_id": _row.get("agent_id") or "main",
                                    "session_id": str(_sid),
                                    "ts": datetime.fromtimestamp(
                                        _st_s, timezone.utc).isoformat(),
                                    "runtime_kind": _wprof.runtime,
                                    "event_type": "waiting_on_user",
                                    "data": {
                                        "tool": _row.get("tool_name")
                                        or attrs.get("tool_name"),
                                        "duration_ms": _dur_ms,
                                        "_otlp": True,
                                    },
                                    "_parent_span": str(_hex(span.parent_span_id)),
                                })
                            except Exception:
                                pass
                        # Claude Code spans go through the materializer too:
                        # on a daemon machine the transcript row already
                        # exists under the same ``claude_code:<uuid>`` key
                        # and is left alone (its source is not otlp_spans);
                        # on a daemon-free machine this is the only way the
                        # session reaches the Sessions tab (WO-57 ADR-003).
                        # A profiled runtime's spans go through the
                        # materializer like any other app: on a daemon machine
                        # the transcript row already exists under the same
                        # ``<runtime>:<id>`` key and is left alone (its source
                        # is not otlp_spans); on a daemon-free machine this is
                        # the only way the session reaches the Sessions tab.
                        if _sid and _atype != "openclaw":
                            _env = (_row.get("attributes") or {}).get(
                                "deployment.environment")
                            if _env or str(_sid) not in _otlp_sessions_seen:
                                _otlp_sessions_seen[str(_sid)] = _env
                    except Exception as e:
                        try:
                            import logging as _lg
                            _lg.getLogger("clawmetry.dashboard").warning(
                                "local_store.put_span failed: %s", e
                            )
                        except Exception:
                            pass

    if _store is not None and _otlp_wait_events:
        # A wait span may carry no tool name of its own (measured live); its
        # parent tool span does.
        for _wev in _otlp_wait_events:
            _parent = _wev.pop("_parent_span", None)
            if _wev["data"].get("tool") or not _parent:
                continue
            if _parent in _wait_tool_by_span:
                _wev["data"]["tool"] = _wait_tool_by_span[_parent]
                continue
            # The wait ends before its parent tool span does, so a batching
            # exporter routinely ships them in different POSTs. Events are
            # insert-or-ignore and cannot be back-filled, so ask the store
            # for the parent (one read per unresolved wait, rare).
            try:
                _prow = _store.query_spans(span_id=_parent, limit=1)
                if isinstance(_prow, dict):
                    _prow = _prow.get("result") or _prow.get("rows") or []
                if _prow and (_prow[0].get("tool_name")):
                    _wev["data"]["tool"] = _prow[0]["tool_name"]
                    _wait_tool_by_span[_parent] = _prow[0]["tool_name"]
            except Exception:
                pass
        try:
            _store.put_otlp_batch(records=[], events=_otlp_wait_events)
        except Exception as e:
            try:
                import logging as _lg
                _lg.getLogger("clawmetry.dashboard").warning(
                    "waiting_on_user events write failed: %s", e)
            except Exception:
                pass

    # One materialization call per export batch (not per span — get_store()
    # here can be an HTTP proxy to the daemon; FLYWHEEL 1e). Recomputes the
    # touched sessions from their spans and upserts sessions rows so the
    # Sessions tab and runtime switcher show a span-only OTLP app (WO-55).
    if _store is not None and _otlp_sessions_seen:
        try:
            _store.materialize_otlp_sessions(
                session_ids=sorted(_otlp_sessions_seen),
                environments={k: v for k, v in _otlp_sessions_seen.items() if v},
            )
        except Exception as e:
            try:
                import logging as _lg
                _lg.getLogger("clawmetry.dashboard").warning(
                    "materialize_otlp_sessions failed: %s", e
                )
            except Exception:
                pass


# ── Daemon-free OTLP intake (WO-7) ───────────────────────────────────────────
#
# Everything below serves one deployment shape: an org that does NOT install a
# per-machine daemon and instead sets OTEL_EXPORTER_OTLP_ENDPOINT (one config
# value, pushed by MDM) at a ClawMetry the org already runs. That is the only
# path a 500-developer security review approves in an afternoon.
#
# HONESTY BOUNDARIES on this path, which the docs repeat and nothing here may
# quietly widen:
#   * Only runtimes that emit OTel natively arrive here — Claude Code and
#     Codex today. This is NOT a 26-runtime intake path.
#   * Records arrive in PLAINTEXT. The runtime encrypts nothing, so the
#     daemon's end-to-end encryption guarantee does not cover this path; the
#     honest answer for a customer who needs it is the self-hosted VPC
#     receiver, where the plaintext never leaves their network.

# Log-record event names, matched on the suffix after the runtime prefix
# ("claude_code.tool_decision" -> "tool_decision").
_OTLP_TOOL_CALL_EVENTS = frozenset(
    {"tool_decision", "tool_use", "tool_call"}
)
_OTLP_TOOL_RESULT_EVENTS = frozenset(
    {"tool_result", "tool_use_result"}
)

# WO-57: events a runtime's exporter sends that the transcript never
# carries (permission-mode changes, refusals, MCP health, ...). WHICH names
# and WHICH fields come from the runtime's registered profile; each becomes
# an ``events`` row of the same suffix, fields copied by name, never
# invented. Free text (``prompt`` / ``response``) is capped and tagged.
_OTLP_TEXT_CAP = 4000


def _otlp_typed_event_data(prof, suffix, attrs, pick):
    out = {}
    text_fields = tuple(getattr(prof, "text_fields", ()) or ())
    for k in (prof.typed_events or {}).get(suffix, ()):
        v = pick(attrs, k)
        if v is None:
            continue
        if k in text_fields:
            # Only present when the user opted into content export. Capped,
            # and tagged so a reader (cloud sync, Brain) can exclude it.
            txt = str(v)
            if txt == "<REDACTED>":
                continue
            out[k] = txt[:_OTLP_TEXT_CAP]
            out["has_content"] = True
            if len(txt) > _OTLP_TEXT_CAP:
                out[k + "_truncated"] = True
            continue
        out[k.replace(".", "_")] = v
    return out


# Record ids the live metrics cache has already counted. OTLP delivery is
# at-least-once, so a retried batch used to add its cost to the tiles a second
# time — the DuckDB ledger dedups on the primary key, but the tile a person
# actually looks at showed double. Bounded: this is a cache guard, not a
# ledger, and it must never grow without limit on a busy receiver. Old ids
# fall out; a retry that arrives after ~20k records is vanishingly rare and
# costs one duplicated tile entry, not a duplicated stored row.
_OTLP_SEEN_MAX = 20000
_otlp_seen_ids = set()
_otlp_seen_order = deque()
_otlp_seen_lock = threading.Lock()


def _otlp_seen(record_id):
    """True if this record already reached the metrics cache. Records it
    otherwise. Thread-safe: waitress serves OTLP posts on many threads."""
    if not record_id:
        return False
    with _otlp_seen_lock:
        if record_id in _otlp_seen_ids:
            return True
        _otlp_seen_ids.add(record_id)
        _otlp_seen_order.append(record_id)
        while len(_otlp_seen_order) > _OTLP_SEEN_MAX:
            _otlp_seen_ids.discard(_otlp_seen_order.popleft())
    return False


def _otlp_event_suffix(event_name):
    """``claude_code.tool_decision`` -> ``tool_decision``. Lower-cased."""
    name = (event_name or "").strip().lower()
    return name.rsplit(".", 1)[-1] if "." in name else name


def _otlp_record_ts(rec, received_at):
    """Seconds for ONE OTLP log record, from the record's own clock.

    The prototype stamped ``time.time()`` on every record, so a batched or
    backfilled delivery — the normal case for OTLP, whose exporters buffer and
    retry — was misdated as "now". Any daily or per-sprint rollup built on that
    is wrong, and wrong in a way nobody notices until they compare it to a bill.

    Precedence is the OTel spec's: ``time_unix_nano`` (when the event happened)
    beats ``observed_time_unix_nano`` (when the collector saw it), and receipt
    time is the last resort for an exporter that sends neither.
    """
    for field in ("time_unix_nano", "observed_time_unix_nano"):
        try:
            nanos = int(getattr(rec, field, 0) or 0)
        except (TypeError, ValueError):
            continue
        if nanos > 0:
            return nanos / 1e9
    return received_at


def _otlp_repo_key(value):
    """Normalise a repository attribute into a groupable key.

    An org sends its repo as whatever its tooling has: an https clone URL, an
    ssh remote, or a checkout path. Rolling up cost by repo means those three
    have to land on one key, so we take the last path segment without ``.git``
    (``git@github.com:acme/api.git`` and ``/Users/x/src/api`` both -> ``api``).
    The raw value stays in the attributes blob, so nothing is lost.
    """
    raw = str(value or "").strip()
    if not raw:
        return None
    raw = raw.rstrip("/")
    if raw.endswith(".git"):
        raw = raw[:-4]
    for sep in ("/", "\\", ":"):
        if sep in raw:
            raw = raw.rsplit(sep, 1)[-1]
    return raw or None


def _otlp_record_id(service_name, session_id, event_name, rec, attrs):
    """Deterministic id for one log record, so a retried batch REPLACEs
    instead of double-counting.

    OTLP delivery is at-least-once by specification: an exporter that does not
    see our 200 resends the whole batch. Without a stable key the second
    delivery is a second $4.10, and spend that inflates on a network blip is
    worse than no spend number at all. The record carries no id of its own, so
    we hash what identifies it: emitter, session, event name, its own
    nanosecond timestamp, body, and every attribute.
    """
    # Two decoders reach here: the protobuf message (``HasField``) and the
    # OTLP/JSON shim (a plain object with a ``body`` attribute and no
    # ``HasField``). Read the body without assuming either.
    body = ""
    try:
        raw_body = getattr(rec, "body", None)
        has_field = getattr(rec, "HasField", None)
        if callable(has_field):
            raw_body = rec.body if has_field("body") else None
        if raw_body is not None:
            try:
                body = _otel_attr_value(raw_body)
            except Exception:
                body = str(raw_body)
    except Exception:
        body = ""
    parts = [
        str(service_name or ""), str(session_id or ""), str(event_name or ""),
        str(getattr(rec, "time_unix_nano", 0) or 0),
        str(getattr(rec, "observed_time_unix_nano", 0) or 0),
        str(body),
    ]
    try:
        for k in sorted(attrs):
            parts.append("%s=%s" % (k, attrs[k]))
    except Exception:
        pass
    joined = "\x1f".join(parts).encode("utf-8", "replace")
    return hashlib.sha256(joined).hexdigest()[:32]


def _delegated_is_agent_id(value) -> bool:
    """True when an OTLP conversation id is a delegated vendor agent id.

    Import is late and failure is False: the delegated-usage module is part of
    the OSS package, but an ingest path must not start refusing records because
    an optional import moved.
    """
    try:
        from clawmetry.delegated_usage import is_delegated_agent_id
        return is_delegated_agent_id(value)
    except Exception:
        return False


def _delegated_record_otel(agent_id, tin, tout, cache_read, cache_write,
                           model="", ts=0.0) -> bool:
    """File one Cursor cloud-agent OTel record against its agent id.

    ``require_observed`` stays ON: a team's export carries every agent on the
    Cursor team, and only the ones a transcript on THIS machine actually named
    may be attributed here. Without that bound a colleague's agent would appear
    on your session.
    """
    try:
        from clawmetry.delegated_usage import (
            SOURCE_OTEL, CURSOR, DelegatedUsage, get_store,
        )

        def _n(v):
            try:
                return int(v) if v is not None else 0
            except (TypeError, ValueError):
                return 0

        usage = DelegatedUsage(
            agent_id=str(agent_id),
            vendor=CURSOR,
            source=SOURCE_OTEL,
            input_tokens=_n(tin),
            output_tokens=_n(tout),
            cache_read_tokens=_n(cache_read),
            cache_write_tokens=_n(cache_write),
            model=str(model or ""),
            updated_at=float(ts or 0.0) or 0.0,
        )
        if usage.total_tokens <= 0:
            return False
        return get_store().record(usage)
    except Exception:
        return False


def _process_otlp_logs(pb_data, content_encoding=None, content_type=None):
    """Decode OTLP logs protobuf and ingest agent EVENT records (#2596, WO-7).

    Claude Code and Codex export their per-turn event stream as OTel *logs* —
    ``event_name`` like ``claude_code.api_request`` / ``tool_decision`` with
    cost/token/model attributes. This handler is the daemon-free intake path:
    an org points OTEL_EXPORTER_OTLP_ENDPOINT here and gets observability with
    nothing installed per machine.

    Three destinations, in order of durability:

    1. **DuckDB ``otlp_records``** — the durable ledger. One row per record
       with the identity the runtime already sends (``user.id``,
       ``user.email``, ``organization.id``, ``session.id``) plus the rollup
       dimensions an org adds through ``OTEL_RESOURCE_ATTRIBUTES``
       (``team.id``, repository). Without these there is no per-team or
       per-repo answer, which is the whole reason an org buys this.
    2. **DuckDB ``events``** — ``tool_decision`` / ``tool_result`` records
       become ``tool_call`` / ``tool_result`` events, so the trajectory
       detectors (stuck_loop, no_progress, repeated_tool_failure) work on this
       path exactly as they do on the daemon path.
    3. **The in-memory metrics cache** — unchanged, because it is what the
       live tiles read on the same request. It is a cache, not storage: before
       WO-7 it was the ONLY destination, so a restart erased the deployment's
       entire history.

    Writes go through ``local_store.get_store()``, which in this process is a
    ``_ProxyStore`` forwarding to the daemon that owns the writer lock — the
    request handler never takes it. Best-effort throughout: a bad record never
    breaks the batch, and a failed DuckDB write never breaks the tiles.
    """
    received_at = time.time()
    req = _otlp_request(pb_data, "logs", content_encoding, content_type)

    # Resolve the store lazily (same contract as the traces path): tests that
    # monkeypatch the singleton, and installs without DuckDB, both keep working.
    _store = None
    try:
        from clawmetry import local_store as _ls
        _store = _ls.get_store()
    except Exception:
        _store = None

    # Accumulated across the WHOLE export batch and written in one call. An
    # exporter ships hundreds of records per POST and get_store() here is an
    # HTTP proxy to the daemon, so per-record writes would be per-record round
    # trips (FLYWHEEL 1e, the daemon's CPU budget).
    out_records = []
    out_events = []

    def _f(attrs, *keys):
        for k in keys:
            if k in attrs and attrs[k] not in (None, ""):
                return attrs[k]
        return None

    for resource_logs in req.resource_logs:
        resource_attrs = {}
        if resource_logs.resource:
            for attr in resource_logs.resource.attributes:
                resource_attrs[attr.key] = _otel_attr_value(attr.value)

        service_name = resource_attrs.get("service.name") or ""
        agent_type = (
            _otlp_service_name_to_agent_type(service_name) or "openclaw"
        )
        node_id = (
            resource_attrs.get("node.id")
            or resource_attrs.get("host.name")
            or resource_attrs.get("host.id")
            or "otlp"
        )

        for scope_logs in resource_logs.scope_logs:
            for rec in scope_logs.log_records:
                attrs = {}
                for attr in rec.attributes:
                    attrs[attr.key] = _otel_attr_value(attr.value)

                def _pick(*keys):
                    """Record attributes win over resource attributes — the
                    precedence the OTel spec uses."""
                    v = _f(attrs, *keys)
                    if v is not None:
                        return v
                    return _f(resource_attrs, *keys)

                # ── Fix 1: the record's own timestamp, not receipt time ──
                ts = _otlp_record_ts(rec, received_at)

                # ── Fix 2: identity ──────────────────────────────────────
                # Claude Code sets user.id / user.email / organization.id /
                # session.id on every record; team and repository come from
                # the org's own OTEL_RESOURCE_ATTRIBUTES.
                session_id = _pick(
                    "session.id", "session_id", "gen_ai.conversation.id",
                    "conversation.id",
                    # Cursor's OTel export keys every log record with
                    # cursor.conversation.id, which for a CLOUD agent is the
                    # customer-visible bc-... id -- the same id a Grok Bot
                    # transcript records when it delegates. That attribute is
                    # therefore the join between two vendors' telemetry.
                    "cursor.conversation.id",
                )
                # The LEDGER keeps the session id exactly as sent (REQ-OBS-006:
                # retain identity, derive nothing). EVENTS use the daemon's
                # key, ``claude_code:<uuid>``, so they join the transcript
                # session and bucket under the right runtime (WO-57).
                ledger_session_id = session_id
                _prof = _otel_profile_for_resource(resource_attrs)
                if _prof is not None and session_id and _prof.session_key_prefix:
                    session_id = _prof.session_key(session_id)
                user_id = _pick(
                    "user.id", "user.account_uuid", "enduser.id", "user_id",
                )
                user_email = _pick("user.email", "enduser.email", "user_email")
                org_id = _pick(
                    "organization.id", "organization.uuid", "org.id",
                    "organization_id", "tenant.id",
                )
                team = _pick(
                    "team.id", "team", "department", "cost_center",
                    "cost.center", "squad", "group.id",
                )
                repo_raw = _pick(
                    "vcs.repository.url.full", "vcs.repository.url",
                    "repository", "repo", "git.repository", "git.repo",
                    "code.repository", "project.name", "workspace",
                )
                repo = _otlp_repo_key(repo_raw)

                model = _pick("model", "gen_ai.request.model",
                              "gen_ai.response.model") or ""
                channel = _pick("channel") or ""
                provider = _pick("provider", "gen_ai.provider.name",
                                 "gen_ai.system") or ""

                event_name = (getattr(rec, "event_name", "") or "").strip()
                if not event_name:
                    event_name = str(_f(attrs, "event.name") or "")
                suffix = _otlp_event_suffix(event_name)

                record_id = _otlp_record_id(
                    service_name, ledger_session_id, event_name, rec, attrs
                )
                # The tiles must not count a retried batch twice. The DuckDB
                # write below is idempotent on record_id; this is the same
                # guarantee for the in-memory cache the live tiles read.
                fresh = not _otlp_seen(record_id)

                cost = _f(attrs, "cost_usd", "cost.usd", "cost")
                cost_val = None
                if cost is not None:
                    try:
                        cost_val = float(cost)
                    except (TypeError, ValueError):
                        cost_val = None
                if cost_val is not None and fresh:
                    _add_metric("cost", {
                        "timestamp": ts, "usd": cost_val,
                        "model": model, "channel": channel, "provider": provider,
                    })

                itok = _f(attrs, "input_tokens", "tokens.input", "prompt_tokens",
                          "gen_ai.usage.input_tokens")
                otok = _f(attrs, "output_tokens", "tokens.output",
                          "completion_tokens", "gen_ai.usage.output_tokens")
                tin = tout = None
                if itok is not None or otok is not None:
                    try:
                        tin, tout = int(itok or 0), int(otok or 0)
                    except (TypeError, ValueError):
                        tin = tout = None
                if tin is not None and fresh:
                    _add_metric("tokens", {
                        "timestamp": ts, "input": tin, "output": tout,
                        "total": tin + tout,
                        "model": model, "channel": channel, "provider": provider,
                    })

                # ── Delegated usage: Cursor cloud agents (push lane) ─────
                # Cursor Enterprise can point its OTel export straight at this
                # receiver -- the only lane needing no credential and no
                # outbound call from us. A record whose conversation id is a
                # bc-... cloud agent is work some LOCAL runtime delegated, so
                # it is filed against that agent rather than counted as a
                # session of our own.
                #
                # The per-log token attribute names are NOT in Cursor's public
                # docs (they live in a Wire Reference that is not reachable),
                # so this reads a candidate list and a miss records NOTHING.
                # A wrong guess must yield silence, never a fabricated figure.
                if _delegated_is_agent_id(session_id):
                    try:
                        c_in = _f(
                            attrs, "cursor.api.request.input_tokens",
                            "cursor.input_tokens", "input_tokens",
                            "gen_ai.usage.input_tokens",
                        )
                        c_out = _f(
                            attrs, "cursor.api.request.output_tokens",
                            "cursor.output_tokens", "output_tokens",
                            "gen_ai.usage.output_tokens",
                        )
                        # The GenAI semconv names are not a guess -- they are
                        # the spec, in both the current dotted spelling and the
                        # earlier underscore one -- so they belong on the list
                        # alongside Cursor's own. Without them a cloud agent
                        # exporting standard semconv had its cached tokens
                        # dropped here too (#5685).
                        c_cr = _f(
                            attrs, "cursor.api.request.cache_read_tokens",
                            "cursor.cache_read_tokens", "cache_read_tokens",
                            "gen_ai.usage.cache_read.input_tokens",
                            "gen_ai.usage.cache_read_input_tokens",
                        )
                        c_cw = _f(
                            attrs, "cursor.api.request.cache_creation_tokens",
                            "cursor.cache_write_tokens", "cache_creation_tokens",
                            "gen_ai.usage.cache_creation.input_tokens",
                            "gen_ai.usage.cache_creation_input_tokens",
                        )
                        if any(v is not None for v in (c_in, c_out, c_cr, c_cw)):
                            _delegated_record_otel(
                                session_id, c_in, c_out, c_cr, c_cw, model, ts,
                            )
                    except Exception:
                        pass

                dur = _f(attrs, "duration_ms", "duration.ms")
                dur_val = None
                if dur is not None:
                    try:
                        dur_val = float(dur)
                    except (TypeError, ValueError):
                        dur_val = None
                if dur_val is not None and fresh and any(
                    k in suffix for k in ("request", "run", "completion")
                ):
                    _add_metric("runs", {
                        "timestamp": ts, "duration_ms": dur_val,
                        "model": model, "channel": channel,
                    })

                # ── Fix 4: tool records become tool events ───────────────
                tool_name = _f(
                    attrs, "tool_name", "tool.name", "name",
                    "gen_ai.tool.name",
                )
                decision = _f(attrs, "decision", "tool.decision")
                success_attr = _f(attrs, "success", "tool.success")
                success = None
                if success_attr is not None:
                    success = str(success_attr).strip().lower() not in (
                        "false", "0", "no", "failure", "error",
                    )

                # ── Fix 3: persist, rather than only caching in memory ───
                out_records.append({
                    "record_id": record_id,
                    "ts": ts,
                    "received_at": received_at,
                    "event_name": event_name or suffix or "log",
                    "session_id": ledger_session_id,
                    "user_id": user_id,
                    "user_email": user_email,
                    "org_id": org_id,
                    "team": team,
                    "repo": repo,
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "service_name": service_name,
                    "model": model or None,
                    "provider": provider or None,
                    "cost_usd": cost_val,
                    "tokens_input": tin,
                    "tokens_output": tout,
                    "token_count": (
                        (tin or 0) + (tout or 0) if tin is not None else None
                    ),
                    "duration_ms": dur_val,
                    "tool_name": tool_name,
                    "decision": decision,
                    "success": success,
                    "attributes": {
                        "resource": resource_attrs,
                        "record": attrs,
                        "repo_raw": repo_raw,
                    },
                })

                if not session_id:
                    # Every downstream reader keys on session_id; a record
                    # without one can still be rolled up by team/user above,
                    # but it cannot join a trajectory.
                    continue

                ev_common = {
                    "node_id": node_id,
                    "agent_type": agent_type,
                    "agent_id": "main",
                    "session_id": str(session_id),
                    "workspace_id": repo,
                    "ts": datetime.fromtimestamp(ts, timezone.utc).isoformat(),
                    "runtime_kind": agent_type,
                }

                if suffix in _OTLP_TOOL_CALL_EVENTS and tool_name:
                    # A rejected permission prompt is not a tool CALL — the
                    # tool never ran. Recording it as one would tell the
                    # no-progress detector the agent acted when it was
                    # actually blocked waiting for a human.
                    if str(decision or "").strip().lower() in (
                        "reject", "rejected", "deny", "denied",
                    ):
                        # WO-57: keep the fact that a human (or a hook, or
                        # config) said no, as its own event. Still never a
                        # tool CALL: the tool did not run.
                        if _prof is None:
                            continue
                        ev = dict(ev_common)
                        ev["id"] = "otlp:" + record_id
                        ev["event_type"] = "tool_decision"
                        ev["data"] = {
                            "tool": str(tool_name), "decision": decision,
                            "source": _f(attrs, "source", "tool.source",
                                         "decision_source"),
                            "tool_source": _f(attrs, "tool_source"),
                            "_otlp": True,
                        }
                        out_events.append(ev)
                        continue
                    args = _f(attrs, "tool_parameters", "tool.parameters",
                              "arguments", "input")
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except (ValueError, TypeError):
                            pass
                    if args in (None, ""):
                        # This path usually carries no arguments, and the
                        # stuck_loop detector trips on K consecutive
                        # IDENTICAL (tool, args) calls. Hashing "no args" to
                        # one constant would make five Reads of five
                        # different files look like a loop, so we say what is
                        # true instead: the arguments are unknown here, and
                        # unknown is not evidence of identical. The cycle
                        # branch (tool NAMES only) still works untouched.
                        args = {"_otlp_args_unknown": record_id}
                    ev = dict(ev_common)
                    ev["id"] = "otlp:" + record_id
                    ev["event_type"] = "tool_call"
                    ev["data"] = {
                        "tool": str(tool_name),
                        "tool_name": str(tool_name),
                        "args": args,
                        "decision": decision,
                        "source": _f(attrs, "source", "tool.source"),
                        "_otlp": True,
                    }
                    out_events.append(ev)
                elif suffix in _OTLP_TOOL_RESULT_EVENTS and tool_name:
                    err_text = _f(attrs, "error", "error.message") or ""
                    ev = dict(ev_common)
                    ev["id"] = "otlp:" + record_id
                    ev["event_type"] = "tool_result"
                    ev["data"] = {
                        "tool": str(tool_name),
                        "tool_name": str(tool_name),
                        "is_error": (success is False) or bool(err_text),
                        "error": err_text,
                        "duration_ms": dur_val,
                        "_otlp": True,
                    }
                    out_events.append(ev)
                elif _prof is not None and suffix in (_prof.typed_events or {}):
                    ev = dict(ev_common)
                    ev["id"] = "otlp:" + record_id
                    ev["event_type"] = suffix
                    ev["data"] = _otlp_typed_event_data(_prof, suffix, attrs, _f)
                    ev["data"]["_otlp"] = True
                    if model:
                        ev["model"] = model
                    out_events.append(ev)
                elif cost_val is not None or tin is not None:
                    # The money records (api_request). Landing them in events
                    # is what makes the usage + cost surfaces survive a
                    # restart on a daemon-free deployment.
                    ev = dict(ev_common)
                    ev["id"] = "otlp:" + record_id
                    ev["event_type"] = "llm_call"
                    ev["cost_usd"] = cost_val
                    ev["token_count"] = (
                        (tin or 0) + (tout or 0) if tin is not None else None
                    )
                    ev["model"] = model or None
                    ev["data"] = {
                        "model": model,
                        "provider": provider,
                        "input_tokens": tin,
                        "output_tokens": tout,
                        "cost_usd": cost_val,
                        "duration_ms": dur_val,
                        "_otlp": True,
                    }
                    for _k, _dk in ((_prof.llm_extra_fields or ()) if _prof is not None else ()):
                        _v = _f(attrs, _k)
                        if _v is not None:
                            ev["data"][_dk] = _v
                    out_events.append(ev)

    if _store is not None and (out_records or out_events):
        try:
            # Keyword args are REQUIRED: the dashboard's _ProxyStore forwards
            # **kwargs only, so a positional call silently writes nothing
            # whenever the daemon owns the writer lock — i.e. every real
            # install. put_otlp_batch is allowlisted in
            # routes/local_query._DAEMON_METHODS so the daemon runs the write.
            _store.put_otlp_batch(records=out_records, events=out_events)
        except Exception as e:
            try:
                import logging as _lg
                _lg.getLogger("clawmetry.dashboard").warning(
                    "local_store.put_otlp_batch failed: %s", e
                )
            except Exception:
                pass


def _get_otel_usage_data():
    """Aggregate OTLP metrics into usage data for the Usage tab."""
    today = datetime.now()
    today_start = today.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
    week_start = (
        (today - timedelta(days=today.weekday()))
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .timestamp()
    )
    month_start = today.replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    ).timestamp()

    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    cache_read_total = 0
    cache_write_total = 0
    with _metrics_lock:
        for entry in metrics_store["tokens"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            total = entry.get("total", 0)
            daily_tokens[day] = daily_tokens.get(day, 0) + total
            model = entry.get("model", "unknown") or "unknown"
            model_usage[model] = model_usage.get(model, 0) + total
            # Prompt-cache tokens by kind (Claude Code metrics, WO-57); same
            # field names as the transcript path.
            cache_read_total += int(entry.get("cache_read_tokens") or 0)
            cache_write_total += int(entry.get("cache_write_tokens") or 0)

        for entry in metrics_store["cost"]:
            ts = entry.get("timestamp", 0)
            day = datetime.fromtimestamp(ts).strftime("%Y-%m-%d")
            daily_cost[day] = daily_cost.get(day, 0) + entry.get("usd", 0)

    days = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        ds = d.strftime("%Y-%m-%d")
        days.append(
            {
                "date": ds,
                "tokens": daily_tokens.get(ds, 0),
                "cost": daily_cost.get(ds, 0),
            }
        )

    today_str = today.strftime("%Y-%m-%d")
    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if _safe_date_ts(k) >= week_start)
    month_tok = sum(
        v for k, v in daily_tokens.items() if _safe_date_ts(k) >= month_start
    )
    today_cost_val = daily_cost.get(today_str, 0)
    week_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= week_start
    )
    month_cost_val = sum(
        v for k, v in daily_cost.items() if _safe_date_ts(k) >= month_start
    )

    run_durations = []
    with _metrics_lock:
        for entry in metrics_store["runs"]:
            run_durations.append(entry.get("duration_ms", 0))
    avg_run_ms = sum(run_durations) / len(run_durations) if run_durations else 0

    msg_count = len(metrics_store["messages"])

    # Enhanced cost tracking for OTLP data
    trend_data = _analyze_usage_trends(daily_tokens)
    model_billing, billing_summary = _build_model_billing(model_usage)
    warnings = _generate_cost_warnings(
        today_cost_val,
        week_cost_val,
        month_cost_val,
        trend_data,
        month_tok,
        billing_summary,
    )

    return {
        "source": "otlp",
        "days": days,
        "today": today_tok,
        "week": week_tok,
        "month": month_tok,
        "cacheReadTokens": cache_read_total,
        "cacheWriteTokens": cache_write_total,
        "todayCost": round(today_cost_val, 4),
        "weekCost": round(week_cost_val, 4),
        "monthCost": round(month_cost_val, 4),
        "avgRunMs": round(avg_run_ms, 1),
        "messageCount": msg_count,
        "modelBreakdown": [
            {"model": k, "tokens": v}
            for k, v in sorted(model_usage.items(), key=lambda x: -x[1])
        ],
        "modelBilling": model_billing,
        "billingSummary": billing_summary,
        "trend": trend_data,
        "warnings": warnings,
    }


def _safe_date_ts(date_str):
    """Parse a YYYY-MM-DD date string to a timestamp, returning 0 on failure."""
    if not date_str or not isinstance(date_str, str):
        return 0
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").timestamp()
    except ValueError:
        # Invalid date format - expected but handled gracefully
        return 0
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error parsing date '{date_str}': {e}")
        return 0


def _detected_runtimes():
    """Presence-probe every supported runtime. [] when the probe is unavailable."""
    try:
        from clawmetry.runtime_probe import probe_runtimes
        return [p for p in probe_runtimes() if p.get("found")]
    except Exception:
        return []


def validate_configuration():
    """Validate the detected configuration and provide helpful feedback for new users.

    ClawMetry watches every supported runtime, so the OpenClaw-specific checks
    below only run when OpenClaw (or NemoClaw, which shares its layout) is the
    runtime on this machine. A Claude Code / Codex / Cursor user got a wall of
    "install OpenClaw" warnings about a runtime they never asked for.
    """
    warnings = []
    tips = []

    detected = _detected_runtimes()
    detected_ids = {p["id"] for p in detected}
    openclaw_family = bool({"openclaw", "nemoclaw"} & detected_ids)

    if detected:
        shown = [p["label"] for p in detected[:6]]
        if len(detected) > len(shown):
            shown.append(f"+{len(detected) - len(shown)} more")
        plural = "runtime" if len(detected) == 1 else "runtimes"
        tips.append(f"[ok] Detected {len(detected)} agent {plural}: {', '.join(shown)}")
    else:
        warnings.append("[warn]  No agent runtime detected on this machine")
        tips.append("[tip] Start an agent (OpenClaw, Claude Code, Codex, Cursor, ...) and the dashboard fills in")

    if not openclaw_family:
        # Nothing below applies: the other runtimes keep their own session
        # stores, which the adapters read directly.
        return warnings, tips

    # Check if workspace looks like a real OpenClaw setup
    workspace_files = ['SOUL.md', 'AGENTS.md', 'MEMORY.md', 'memory']
    found_files = []
    for f in workspace_files:
        path = os.path.join(WORKSPACE, f)
        if os.path.exists(path):
            found_files.append(f)

    if not found_files:
        warnings.append(f"[warn]  No OpenClaw workspace files found in {WORKSPACE}")
        tips.append("[tip] Create SOUL.md, AGENTS.md, or MEMORY.md to set up your agent workspace")

    # Check if log directory exists and has recent logs
    if not os.path.exists(LOG_DIR):
        warnings.append(f"[warn]  Log directory doesn't exist: {LOG_DIR}")
        tips.append("[tip] Make sure OpenClaw is running to generate logs")
    else:
        # Check for recent log files
        log_pattern = os.path.join(LOG_DIR, "*claw*.log")
        recent_logs = [f for f in glob.glob(log_pattern)
                      if os.path.getmtime(f) > time.time() - 86400]  # Last 24h
        if not recent_logs:
            warnings.append(f"[warn]  No recent log files found in {LOG_DIR}")
            tips.append("[tip] Start your OpenClaw agent to see real-time data")

    # Check if sessions directory exists
    if not SESSIONS_DIR or not os.path.exists(SESSIONS_DIR):
        warnings.append(f"[warn]  Sessions directory not found: {SESSIONS_DIR}")
        tips.append("[tip] Sessions will appear when your agent starts conversations")

    return warnings, tips


def _auto_detect_data_dir():
    """Auto-detect OpenClaw data directory, including Docker volume mounts."""
    # Standard locations
    candidates = [
        os.path.expanduser('~/.openclaw'),
        os.path.expanduser('~/.clawdbot'),
    ]
    # Docker volume mounts (Hostinger pattern: /docker/*/data/.openclaw)
    try:
        import glob as _glob
        for pattern in ['/docker/*/data/.openclaw', '/docker/*/.openclaw',
                        '/var/lib/docker/volumes/*/_data/.openclaw']:
            candidates.extend(_glob.glob(pattern))
    except Exception:
        pass
    # Check Docker inspect for mount points
    try:
        import subprocess as _sp
        container_ids = _sp.check_output(
            ['docker', 'ps', '-q', '--filter', 'ancestor=*openclaw*'],
            timeout=3, stderr=_sp.DEVNULL
        ).decode().strip().split()
        if not container_ids:
            # Try all containers
            container_ids = _sp.check_output(
                ['docker', 'ps', '-q'], timeout=3, stderr=_sp.DEVNULL
            ).decode().strip().split()
        for cid in container_ids[:3]:
            try:
                mounts = _sp.check_output(
                    ['docker', 'inspect', cid, '--format',
                     '{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}'],
                    timeout=3, stderr=_sp.DEVNULL
                ).decode().strip().split()
                for mount in mounts:
                    parts = mount.split(':')
                    if len(parts) >= 1:
                        src = parts[0]
                        oc_path = os.path.join(src, '.openclaw')
                        if os.path.isdir(oc_path) and oc_path not in candidates:
                            candidates.insert(0, oc_path)
                        # Also check if the mount itself is the .openclaw dir
                        if src.endswith('.openclaw') and os.path.isdir(src):
                            candidates.insert(0, src)
            except Exception:
                pass
    except Exception:
        pass
    for c in candidates:
        if c and os.path.isdir(c) and (
            os.path.isdir(os.path.join(c, 'agents')) or
            os.path.isdir(os.path.join(c, 'workspace')) or
            os.path.exists(os.path.join(c, 'cron', 'jobs.json'))
        ):
            return c
    return None

def detect_config(args=None):
    """Auto-detect OpenClaw/Moltbot paths, with CLI and env overrides."""
    global WORKSPACE, MEMORY_DIR, LOG_DIR, SESSIONS_DIR, USER_NAME

    # 0a. --openclaw-dir: set OpenClaw config directory (Issue #322 - Docker config bleed)
    if args and getattr(args, 'openclaw_dir', None):
        os.environ['CLAWMETRY_OPENCLAW_DIR'] = os.path.expanduser(args.openclaw_dir)

    # 0. --data-dir: set defaults from OpenClaw data directory (e.g. /path/.openclaw)
    data_dir = None
    if args and getattr(args, 'data_dir', None):
        data_dir = os.path.expanduser(args.data_dir)
    elif os.environ.get("OPENCLAW_DATA_DIR"):
        data_dir = os.path.expanduser(os.environ["OPENCLAW_DATA_DIR"])
    else:
        # Auto-detect: check common locations including Docker volumes
        data_dir = _auto_detect_data_dir()

    if data_dir and os.path.isdir(data_dir):
        # Auto-set workspace, sessions, crons from data dir
        ws = os.path.join(data_dir, 'workspace')
        if os.path.isdir(ws) and not (args and args.workspace):
            if not args:
                import argparse
                args = argparse.Namespace()
            args.workspace = ws
        sess = os.path.join(data_dir, 'agents', 'main', 'sessions')
        if os.path.isdir(sess) and not (args and getattr(args, 'sessions_dir', None)):
            args.sessions_dir = sess

    # 1. Workspace - where agent files live (SOUL.md, MEMORY.md, memory/, etc.)
    if args and args.workspace:
        WORKSPACE = os.path.expanduser(args.workspace)
    elif os.environ.get("OPENCLAW_HOME"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_HOME"])
    elif os.environ.get("OPENCLAW_WORKSPACE"):
        WORKSPACE = os.path.expanduser(os.environ["OPENCLAW_WORKSPACE"])
    else:
        # Auto-detect: check common locations
        candidates = [
            _detect_workspace_from_config(),
            os.path.expanduser("~/.openclaw/workspace"),
            os.path.expanduser("~/.clawdbot/workspace"),
            os.path.expanduser("~/clawd"),
            os.path.expanduser("~/openclaw"),
            os.getcwd(),
        ]
        for c in candidates:
            if c and os.path.isdir(c) and (
                os.path.exists(os.path.join(c, "SOUL.md")) or
                os.path.exists(os.path.join(c, "AGENTS.md")) or
                os.path.exists(os.path.join(c, "MEMORY.md")) or
                os.path.isdir(os.path.join(c, "memory"))
            ):
                WORKSPACE = c
                break
        if not WORKSPACE:
            # "/" is not a workspace. launchd starts agents with cwd="/", so
            # this last-resort guess silently poisoned every workspace-relative
            # state path (see _fleet_db_path) on an auto-started install.
            _cwd = os.getcwd()
            WORKSPACE = _cwd if _cwd not in ("/", "") else os.path.expanduser("~")

    MEMORY_DIR = os.path.join(WORKSPACE, "memory")

    # 2. Log directory
    if args and args.log_dir:
        LOG_DIR = os.path.expanduser(args.log_dir)
    elif os.environ.get("OPENCLAW_LOG_DIR"):
        LOG_DIR = os.path.expanduser(os.environ["OPENCLAW_LOG_DIR"])
    else:
        candidates = _get_log_dirs() + [os.path.expanduser("~/.clawdbot/logs")]
        LOG_DIR = next((d for d in candidates if os.path.isdir(d)), _get_log_dirs()[0])

    # 3. Sessions directory (transcript .jsonl files)
    if args and getattr(args, 'sessions_dir', None):
        SESSIONS_DIR = os.path.expanduser(args.sessions_dir)
    elif os.environ.get("OPENCLAW_SESSIONS_DIR"):
        SESSIONS_DIR = os.path.expanduser(os.environ["OPENCLAW_SESSIONS_DIR"])
    else:
        candidates = [
            os.path.expanduser('~/.openclaw/agents/main/sessions'),
            os.path.expanduser('~/.clawdbot/agents/main/sessions'),
            os.path.join(WORKSPACE, 'sessions') if WORKSPACE else None,
            os.path.expanduser('~/.openclaw/sessions'),
            os.path.expanduser('~/.clawdbot/sessions'),
        ]
        # Also scan agents dirs
        for agents_base in [os.path.expanduser('~/.openclaw/agents'), os.path.expanduser('~/.clawdbot/agents')]:
            if os.path.isdir(agents_base):
                for agent in os.listdir(agents_base):
                    p = os.path.join(agents_base, agent, 'sessions')
                    if p not in candidates:
                        candidates.append(p)
        SESSIONS_DIR = next((d for d in candidates if d and os.path.isdir(d)), candidates[0] if candidates else None)

    # 4. User name (shown in Flow visualization)
    if args and args.name:
        USER_NAME = args.name
    elif os.environ.get("OPENCLAW_USER"):
        USER_NAME = os.environ["OPENCLAW_USER"]
    else:
        USER_NAME = "You"

    # ── Register blueprints (Phase 4) ───────────────────────────────────────
    # Pro features (selfevolve, asset_registry, custom_runtime_ingest, ...)
    # live in clawmetry-pro. When that package is installed its Blueprints
    # already registered earlier via ``_ext_load(app)`` and won the URL
    # routes; the OSS-side 402-stub Blueprints must skip registration to
    # avoid a Flask blueprint-name collision. When pro is NOT installed
    # the OSS stubs register and serve HTTP 402 ``upgrade_required``.
    try:
        import clawmetry_pro as _pro
        _pro_loaded = bool(getattr(_pro, "is_loaded", lambda: False)())
    except Exception:
        _pro_loaded = False

    app.register_blueprint(bp_advisor)
    if not _pro_loaded:
        app.register_blueprint(bp_selfevolve)
    app.register_blueprint(bp_alerts)
    app.register_blueprint(bp_autonomy)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_brain)
    app.register_blueprint(bp_budget)
    app.register_blueprint(bp_channels)
    app.register_blueprint(bp_components)
    app.register_blueprint(bp_config)
    app.register_blueprint(bp_crons)
    app.register_blueprint(bp_fleet)
    app.register_blueprint(bp_gateway)
    app.register_blueprint(bp_harness)
    app.register_blueprint(bp_delegated)
    app.register_blueprint(bp_readiness)
    app.register_blueprint(bp_guard)
    app.register_blueprint(bp_signals)
    app.register_blueprint(bp_selfdiag)
    app.register_blueprint(bp_health)
    app.register_blueprint(bp_logs)
    app.register_blueprint(bp_memory)
    app.register_blueprint(bp_otel)
    app.register_blueprint(bp_otel_export)
    # Custom-runtime HTTP ingest is a Pro feature; the impl lives in
    # clawmetry-pro. When that package is installed, its blueprint was
    # already registered by ``_ext_load(app)`` above and won the URL
    # routes; skip the OSS 402-stub registration here to avoid a Flask
    # blueprint-name collision. When the closed package is NOT installed
    # the OSS stub registers and returns HTTP 402 ``upgrade_required``.
    try:
        import clawmetry_pro as _pro
        _pro_loaded = bool(getattr(_pro, "is_loaded", lambda: False)())
    except Exception:
        _pro_loaded = False
    if not _pro_loaded:
        app.register_blueprint(bp_runtime_ingest)
    app.register_blueprint(bp_otlp_traces)
    app.register_blueprint(bp_overview)
    app.register_blueprint(bp_trial)
    app.register_blueprint(bp_onboarding)
    app.register_blueprint(bp_security)
    app.register_blueprint(bp_sessions)
    app.register_blueprint(bp_sla)
    app.register_blueprint(bp_tracing)
    app.register_blueprint(bp_trail)
    app.register_blueprint(bp_usage)
    app.register_blueprint(bp_version)
    app.register_blueprint(bp_version_impact)

    app.register_blueprint(bp_cloud_relay)
    # NeMo governance + approval queue is a Pro feature; the impl lives in
    # clawmetry-pro. When that package is installed, its blueprint was
    # already registered by ``_ext_load(app)`` above and won the URL
    # routes; skip the OSS 402-stub registration here to avoid a Flask
    # blueprint-name collision. When the closed package is NOT installed
    # the OSS stub registers and returns HTTP 402 ``upgrade_required``.
    if not _pro_loaded:
        app.register_blueprint(bp_nemoclaw)
        app.register_blueprint(bp_compliance)
        app.register_blueprint(bp_org_analytics)
    app.register_blueprint(bp_skills)
    app.register_blueprint(bp_runtime_memory)
    app.register_blueprint(bp_heartbeat)
    app.register_blueprint(bp_selfconfig)
    app.register_blueprint(bp_agents)
    app.register_blueprint(bp_inventory)
    app.register_blueprint(bp_govern)
    if not _pro_loaded:
        app.register_blueprint(bp_assets)
    app.register_blueprint(bp_reasoning)
    app.register_blueprint(bp_plugins)
    app.register_blueprint(bp_local_query)
    # ClawMetry Enterprise self-hosted server mode: one process serves the
    # dashboard AND the ingest API the node daemons push to. Gated hard on
    # SELF_HOSTED=true — never registered for normal local/cloud installs.
    try:
        from clawmetry.selfhosted import is_self_hosted as _is_self_hosted
        if _is_self_hosted():
            from routes.selfhosted_ingest import bp_selfhosted
            app.register_blueprint(bp_selfhosted)
            from clawmetry.selfhosted import maybe_start_license_ping
            if maybe_start_license_ping():
                print("  SelfHosted: [ok] license/version ping enabled (daily)")
            print("  SelfHosted: [ok] ingest API registered (/auth, /ingest/*)")
    except Exception as _sh_exc:
        print(f"  SelfHosted: [warn] not registered: {_sh_exc}")
    app.register_blueprint(bp_dives)
    app.register_blueprint(bp_reports)
    app.register_blueprint(bp_scheduler)
    app.register_blueprint(bp_policy)
    # Local pre-tool hook receiver (Claude Code PreToolUse gate) —
    # routes/hooks.py. Its record_once hook also persists this
    # dashboard's port to ~/.clawmetry/server.json for the gate
    # installer's base-URL discovery.
    from routes.hooks import bp_hooks
    app.register_blueprint(bp_hooks)
    # Per-runtime approval routing (/api/approvals/routing) + the phone
    # decision page (/a/<id>) the notification links point at. Paid
    # delivery layer: when clawmetry-pro is installed its blueprint was
    # already registered by ``_ext_load(app)`` above and won these URLs, so
    # skip the OSS registration to avoid a blueprint-name collision. The
    # OSS module is the impl today and becomes a 402 stub once the impl
    # moves — the switch is identical either way.
    try:
        import clawmetry_pro as _pro_ar
        _pro_ar_loaded = bool(getattr(_pro_ar, "is_loaded", lambda: False)())
    except Exception:
        _pro_ar_loaded = False
    if not _pro_ar_loaded:
        from routes.approval_routing import bp_approval_routing
        app.register_blueprint(bp_approval_routing)
    app.register_blueprint(bp_turn_anatomy)
    app.register_blueprint(bp_tool_catalog)
    app.register_blueprint(bp_context_economics)
    app.register_blueprint(bp_spend_flow)
    app.register_blueprint(bp_entitlement)
    app.register_blueprint(bp_extensions)

    # ── Trial-end hard-block gate ───────────────────────────────────────────
    # When the resolver reports an unpaid / expired entitlement, every non-
    # allowlisted request 402s with a machine-readable body carrying
    # ``hard_blocked=True`` and the upgrade URL. Default-ON as of 0.12.x;
    # opt out with ``CLAWMETRY_HARD_BLOCK=0``. The gate honours a per-request
    # ``runtime`` scope hint so an operator who chose the "continue with free
    # runtimes only" fallback (POST /api/trial/continue-free) still gets the
    # OpenClaw / NanoClaw surface while paid runtimes stay blocked. See
    # ``clawmetry/trial_enforcement.py`` for the full policy + allowlist.
    from clawmetry import trial_enforcement as _te_gate

    @app.before_request
    def _trial_hard_block_gate():
        try:
            path = request.path or ""
            if _te_gate.allowlisted_path(path):
                return None
            # Runtime hint sources, in preference order:
            #   1. ?runtime=<name> (canonical UI param)
            #   2. ?scope=<name>   (older alias some routes still emit)
            #   3. X-Clawmetry-Runtime header (used by CLI + adapters)
            rt_hint = None
            try:
                rt_hint = (
                    (request.args.get("runtime") or "").strip()
                    or (request.args.get("scope") or "").strip()
                    or (request.headers.get("X-Clawmetry-Runtime") or "").strip()
                    or None
                )
            except Exception:
                rt_hint = None
            if not _te_gate.is_hard_blocked(path=path, runtime=rt_hint):
                return None
            payload = _te_gate.block_payload()
            resp = jsonify(payload)
            resp.status_code = 402
            resp.headers["X-Clawmetry-Trial-Blocked"] = "1"
            resp.headers["Cache-Control"] = "no-store"
            return resp
        except Exception as exc:
            # Fail-open. A bug in the gate must never brick a paying customer;
            # let the request through and log at warning so operators can spot
            # it in the daemon log rather than in a "why is nothing loading?"
            # support ticket.
            try:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    "trial_hard_block_gate: %s", exc
                )
            except Exception:
                pass
            return None

    app.register_blueprint(bp_audit)
    app.register_blueprint(bp_device)

    # Register built-in agent adapters. External plugins can register more
    # via clawmetry.extensions entry points — see clawmetry/adapters/.
    from clawmetry.adapters import registry as _adapter_registry
    from clawmetry.adapters.openclaw import OpenClawAdapter
    _adapter_registry.register(OpenClawAdapter())
    app.register_blueprint(bp_openapi)
    app.register_blueprint(bp_update_check)
    app.register_blueprint(bp_workspaces)
    app.register_blueprint(bp_bootstrap)
    app.register_blueprint(bp_insights)
    app.register_blueprint(bp_review)
    app.register_blueprint(bp_evals)
    app.register_blueprint(bp_bench)
    app.register_blueprint(bp_cohort)
    app.register_blueprint(bp_quality)
    app.register_blueprint(bp_hitl)
    app.register_blueprint(bp_rules)
    app.register_blueprint(bp_attention)

    # ── v2 React SPA (opt-in) ───────────────────────────────────────────────
    # Default OFF so existing v1 users notice nothing. Enabled when the user
    # passes `--v2` to the CLI or sets CLAWMETRY_V2=1. See clawmetry/v2/.
    if os.environ.get("CLAWMETRY_V2") == "1":
        try:
            from clawmetry.v2.routes import bp_v2 as _bp_v2
            app.register_blueprint(_bp_v2)
        except Exception as _v2_err:  # pragma: no cover - defensive
            import logging as _logging
            _logging.getLogger(__name__).warning(
                "CLAWMETRY_V2=1 set but v2 blueprint failed to register: %s",
                _v2_err,
            )

    # Register built-in agent adapters. External plugins can register more
    # via clawmetry.extensions entry points — see clawmetry/adapters/.
    from clawmetry.adapters import registry as _adapter_registry
    from clawmetry.adapters.openclaw import OpenClawAdapter
    _adapter_registry.register(OpenClawAdapter())

    # NemoClaw is a Free observed runtime alongside OpenClaw (homepage hero
    # promises "OpenClaw + NemoClaw"). The runtime is a NVIDIA OpenClaw
    # wrapper; this read-side facade reads its DuckDB events (tagged
    # agent_type='nemoclaw') so /api/agents + the runtime switcher list it
    # alongside the rest. Register only when detect() finds nemoclaw-tagged
    # events already in the store so an OSS install with no NemoClaw data
    # does not clutter the multi-agent view.
    #
    # NB: NemoClawAdapter (runtime) is distinct from NeMo Guardrails
    # (governance feature, agent_type='nemo'). The latter is exposed via
    # routes/nemoclaw.py governance endpoints, NOT /api/agents.
    try:
        from clawmetry.adapters.nemo import NemoClawAdapter
        _nemoclaw_reader = NemoClawAdapter()
        if _nemoclaw_reader.detect().detected:
            _adapter_registry.register(_nemoclaw_reader)
    except Exception as _nemo_err:  # pragma: no cover - defensive
        import logging as _logging
        _logging.getLogger(__name__).debug("Skipped NemoClaw reader registration: %s", _nemo_err)

    # Non-OpenClaw runtimes ClawMetry can observe via a dedicated reader adapter
    # (Hermes, Claude Code, Codex, Cursor, PicoClaw, NanoClaw, ...). Each uses
    # its own native session format. Register each only when its own cheap,
    # never-raising detect() reports the runtime present on this host, so an
    # absent runtime never clutters the multi-agent view. The single source of
    # truth for which runtimes exist is sync._family_adapter_classes().
    try:
        from clawmetry.sync import _family_adapter_classes as _fam_classes
        for _family_cls in _fam_classes():
            try:
                _inst = _family_cls()
                # A licensed install's clawmetry-pro plugin registers its own
                # (closed) adapter for some runtimes at import time, before this
                # loop runs. Don't clobber it — the registry intentionally lets
                # plugins override the bundled adapter. Free installs have no
                # plugin, so this is a no-op and OSS registers its own.
                if _adapter_registry.get(_inst.name) is not None:
                    continue
                if _inst.detect().detected:
                    _adapter_registry.register(_inst)
            except Exception as _fam_err:  # pragma: no cover - defensive
                import logging as _logging
                _logging.getLogger(__name__).debug(
                    "Skipped %s registration: %s", _family_cls.__name__, _fam_err
                )
    except Exception as _fam_import_err:  # pragma: no cover - defensive
        import logging as _logging
        _logging.getLogger(__name__).debug(
            "Family-runtime adapters unavailable: %s", _fam_import_err
        )

    # Local-OSS shims for cloud-only endpoints. Return empty arrays so the
    # Approvals tab renders cleanly without cloud sync.
    _oss_note = ("OSS install — connect to ClawMetry Cloud "
                 "(`clawmetry connect`) to enable cloud-mediated approvals.")
    @app.route("/api/cloud/approvals", endpoint="oss_approvals_shim")
    def _oss_approvals_shim():
        from flask import jsonify as _jsonify
        return _jsonify({"approvals": [], "count": 0, "note": _oss_note})

    @app.route("/api/cloud/policies", endpoint="oss_policies_shim",
               methods=["GET", "POST"])
    def _oss_policies_shim():
        from flask import jsonify as _jsonify, request as _req
        if _req.method == "POST":
            return _jsonify({"error": "Connect to ClawMetry Cloud to save "
                             "policies from the UI.", "note": _oss_note}), 402
        return _jsonify({"policies": [], "count": 0, "note": _oss_note})

    @app.route("/api/cloud/integrations", endpoint="oss_integrations_shim",
               methods=["GET", "POST"])
    def _oss_integrations_shim():
        from flask import jsonify as _jsonify, request as _req
        if _req.method == "POST":
            return _jsonify({"error": "Connect to ClawMetry Cloud to save "
                             "integrations.", "note": _oss_note}), 402
        return _jsonify({"integrations": [], "count": 0, "note": _oss_note})

    # vivekchand/clawmetry#748 — Initial-sync progress for the dashboard
    # banner. The sync daemon writes ~/.clawmetry/sync_progress.json after
    # each phase; we just stream it through. Local-only, no auth.
    # `runtimes` is added here (not by the daemon) so the banner can NAME what
    # it is syncing instead of hardcoding "your OpenClaw workspace" on a
    # machine that may only run Claude Code / Codex / Cursor.
    @app.route("/api/sync-progress", endpoint="sync_progress")
    def _sync_progress():
        from flask import jsonify as _jsonify
        progress_path = os.path.expanduser("~/.clawmetry/sync_progress.json")
        if not os.path.isfile(progress_path):
            return _jsonify({"error": "no sync progress yet",
                             "runtimes": _sync_scope_runtimes()}), 404
        try:
            with open(progress_path) as _f:
                _payload = json.load(_f)
            if isinstance(_payload, dict):
                _payload["runtimes"] = _sync_scope_runtimes()
            return _jsonify(_payload)
        except Exception as _e:
            return _jsonify({"error": f"unreadable: {_e}"}), 500

    # #1937: cloud-status tri-state so the dashboard banner JS knows whether
    # to show the "Syncing your OpenClaw workspace" banner at all. The banner
    # describes CLOUD-side work, so it's misleading (or just frozen) when:
    #   - cloud sync is opt-out disabled (CLAWMETRY_NO_CLOUD=1 or
    #     ~/.clawmetry/nocloud), or
    #   - the user never connected (no config.json) so there's nothing to sync.
    # The banner only mounts when configured=true AND disabled=false.
    @app.route("/api/cloud-status", endpoint="cloud_status")
    def _cloud_status():
        from flask import jsonify as _jsonify
        from clawmetry.config import is_cloud_disabled, NOCLOUD_MARKER_PATH
        cfg_path = os.path.expanduser("~/.clawmetry/config.json")
        api_key = ""
        if os.path.isfile(cfg_path):
            try:
                with open(cfg_path) as _f:
                    api_key = (json.load(_f) or {}).get("api_key", "")
            except Exception:
                pass
        return _jsonify({
            "disabled": is_cloud_disabled(),
            "configured": bool(api_key),
            "marker_path": NOCLOUD_MARKER_PATH,
            "env_optout": bool(os.environ.get("CLAWMETRY_NO_CLOUD", "").strip()),
        })

    # E2E encryption key — Settings surface for the secret that decrypts
    # cloud-synced snapshots client-side in the browser. Deliberately a bare
    # @app.route in this OSS-only section (like /api/cloud-status above),
    # NOT a Blueprint: the hosted cloud app never calls this route-registration
    # code path (it imports only bp_sessions/bp_overview/bp_health + specific
    # helpers from this module via importlib — see clawmetry-cloud/CLAUDE.md),
    # so this endpoint architecturally does not exist on app.clawmetry.com.
    # Belt-and-braces: cloud's own container also has no ~/.clawmetry/config.json
    # for a user's node in the first place, since the key never leaves this
    # machine except E2E-encrypted. Auth follows the normal /api/* rule in
    # _check_auth() (loopback trusted; remote needs the gateway token).
    def _read_local_config():
        cfg_path = os.path.expanduser("~/.clawmetry/config.json")
        try:
            with open(cfg_path) as _f:
                return json.load(_f) or {}
        except Exception:
            return {}

    @app.route("/api/local/e2e-key", endpoint="e2e_key_get")
    def _e2e_key_get():
        """Whether a key is set — never the key itself.

        SECURITY (2026-08-24 review, finding 8): this used to return the
        plaintext key in a GET body. Loopback callers skip authentication, so
        every local process on the machine could read it, and a GET is exactly
        the shape a hostile page can trigger. Revealing the real value now
        requires the POST below, which the cross-origin write guard covers.
        """
        from flask import jsonify as _jsonify
        cfg = _read_local_config()
        return _jsonify({
            "configured": bool(cfg.get("encryption_key", "")),
            "node_id": cfg.get("node_id", ""),
        })

    @app.route("/api/local/e2e-key/reveal", methods=["POST"], endpoint="e2e_key_reveal")
    def _e2e_key_reveal():
        """Return the key for the Settings pane's reveal/copy control.

        A POST so the Origin guard in ``_check_auth`` applies: a page on
        another origin can still cause this request, but it cannot make the
        browser send an Origin we accept, and it could never read the reply
        anyway.
        """
        from flask import jsonify as _jsonify
        cfg = _read_local_config()
        key = cfg.get("encryption_key", "") or ""
        if not key:
            return _jsonify({"configured": False, "key": None}), 404
        return _jsonify({"configured": True, "key": key})

    @app.route("/api/local/e2e-key/regenerate", methods=["POST"], endpoint="e2e_key_regenerate")
    def _e2e_key_regenerate():
        from flask import jsonify as _jsonify
        from clawmetry.sync import generate_encryption_key, save_config
        cfg_path = os.path.expanduser("~/.clawmetry/config.json")
        try:
            with open(cfg_path) as _f:
                cfg = json.load(_f) or {}
        except Exception:
            cfg = {}
        if not cfg.get("api_key"):
            return _jsonify({
                "error": "Cloud sync isn't set up on this node yet. Run "
                         "\"clawmetry connect\" first.",
            }), 400
        new_key = generate_encryption_key()
        cfg["encryption_key"] = new_key
        save_config(cfg)
        # Restart so the daemon encrypts everything from now on with the new
        # key. Anything already synced under the old key stays readable by
        # anyone who has that old key — regenerating protects data going
        # forward, it does not retroactively re-encrypt history.
        _restart_sync_daemon()
        return _jsonify({"key": new_key})

    # ────────────────────────────────────────────────────────────────────────


def _detect_workspace_from_config():
    """Try to read workspace from Moltbot/OpenClaw agent config."""
    config_paths = [
        os.path.expanduser("~/.clawdbot/agents/main/config.json"),
        os.path.expanduser("~/.clawdbot/config.json"),
    ]
    for cp in config_paths:
        try:
            with open(cp) as f:
                data = json.load(f)
                ws = data.get("workspace") or data.get("workspaceDir")
                if ws:
                    return os.path.expanduser(ws)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            pass
    return None


def _detect_gateway_port():
    """Detect the OpenClaw gateway port from config files or environment."""
    # Check environment variable first
    env_port = os.environ.get('OPENCLAW_GATEWAY_PORT', '').strip()
    if env_port:
        try:
            return int(env_port)
        except ValueError:
            pass
    # Try reading from gateway config
    # Try JSON configs first (openclaw.json / moltbot.json / clawdbot.json)
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, 'openclaw.json'),
        os.path.join(_oc_dir, 'moltbot.json'),
        os.path.join(_oc_dir, 'clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            gw = cfg.get('gateway', {})
            if isinstance(gw, dict) and 'port' in gw:
                return int(gw['port'])
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    # Try YAML configs
    yaml_paths = [
        os.path.expanduser('~/.openclaw/gateway.yaml'),
        os.path.expanduser('~/.openclaw/gateway.yml'),
        os.path.expanduser('~/.clawdbot/gateway.yaml'),
        os.path.expanduser('~/.clawdbot/gateway.yml'),
    ]
    for cp in yaml_paths:
        try:
            with open(cp) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('port:'):
                        port_val = line.split(':', 1)[1].strip()
                        return int(port_val)
        except (FileNotFoundError, ValueError, IndexError):
            pass
    return 18789  # Default OpenClaw gateway port


def _detect_gateway_token():
    """Detect the OpenClaw gateway auth token from env, config files, or running process."""
    # 1. Environment variable (most reliable - matches running gateway)
    env_token = os.environ.get('OPENCLAW_GATEWAY_TOKEN', '').strip()
    if env_token:
        return env_token
    # 2. Try reading from running gateway process env (Linux only)
    try:
        import subprocess as _sp
        result = _sp.run(['pgrep', '-f', 'openclaw-gateway'], capture_output=True, text=True, timeout=3)
        for pid in result.stdout.strip().split('\n'):
            pid = pid.strip()
            if pid:
                try:
                    with open(f'/proc/{pid}/environ', 'r') as f:
                        env_data = f.read()
                    for entry in env_data.split('\0'):
                        if entry.startswith('OPENCLAW_GATEWAY_TOKEN='):
                            return entry.split('=', 1)[1]
                except (PermissionError, FileNotFoundError):
                    pass
    except Exception:
        pass
    # 3. Config files
    _oc_dir = _get_openclaw_dir()
    json_paths = [
        os.path.join(_oc_dir, 'openclaw.json'),
        os.path.join(_oc_dir, 'moltbot.json'),
        os.path.join(_oc_dir, 'clawdbot.json'),
        os.path.expanduser('~/.clawdbot/clawdbot.json'),
    ]
    for jp in json_paths:
        try:
            import json as _json
            with open(jp) as f:
                cfg = _json.load(f)
            # Primary path on current OpenClaw: cfg["gateway"]["auth"]["token"].
            # Older / alternate schemas put it at top-level cfg["auth"]["token"]
            # (issue #1127). Try gateway-nested first, fall back to top-level.
            gw = cfg.get('gateway', {})
            if isinstance(gw, dict):
                gw_auth = gw.get('auth', {})
                if isinstance(gw_auth, dict) and gw_auth.get('token'):
                    return gw_auth['token']
            top_auth = cfg.get('auth', {})
            if isinstance(top_auth, dict) and top_auth.get('token'):
                return top_auth['token']
        except (FileNotFoundError, ValueError, KeyError, TypeError):
            pass
    return None


def _detect_disk_mounts():
    """Detect mounted filesystems to monitor (root + any large data drives)."""
    mounts = ['/']
    try:
        with open('/proc/mounts') as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    mount_point = parts[1]
                    fs_type = parts[2] if len(parts) > 2 else ''
                    # Include additional data mounts (skip virtual/special filesystems)
                    if (mount_point.startswith('/mnt/') or mount_point.startswith('/data')) and \
                       fs_type not in ('tmpfs', 'devtmpfs', 'proc', 'sysfs', 'cgroup', 'cgroup2'):
                        mounts.append(mount_point)
    except (IOError, OSError):
        pass
    return mounts


def _egress_suppressed():
    """Whether discretionary outbound calls are disabled for this install.

    Thin wrapper so a missing/older clawmetry package can never break startup.
    Fails CLOSED: if the check itself errors we suppress the call, because the
    cost of a missing banner line is nothing and the cost of an unexpected
    third-party request in a customer network is a failed security review.
    """
    try:
        from clawmetry.endpoints import egress_suppressed
        return egress_suppressed()
    except Exception:
        return True


def get_public_ip():
    """The machine's public IP, for the "reachable at" startup banner line.

    Returns None instead of calling out when this deployment is not supposed
    to talk to the internet. api.ipify.org is a third party nobody in an
    enterprise deployment agreed to, and the request itself discloses that
    this network runs ClawMetry -- a poor trade for one cosmetic banner line.
    Suppressed for self-hosted, offline/air-gapped, and repointed-endpoint
    installs; see docs/EGRESS.md, which documents this as opt-out.
    """
    if _egress_suppressed():
        return None
    try:
        import urllib.request
        return urllib.request.urlopen("https://api.ipify.org", timeout=2).read().decode().strip()
    except Exception:
        return None


def get_local_ip():
    """Get the machine's LAN IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except (socket.error, OSError) as e:
        # Network unavailable or socket error - common in offline/restricted environments
        return "127.0.0.1"
    except Exception as e:
        print(f"[warn]  Warning: Unexpected error getting local IP: {e}")
        return "127.0.0.1"


# ── HTML Template ───────────────────────────────────────────────────────

# NOTE (2026-09-08): there used to be a SECOND, earlier `DASHBOARD_HTML`
# defined above this point — 5,036 lines of inline HTML/CSS/JS that never
# rendered, because this assignment overwrote it at import time. It was
# deleted. Four separate documents (FLYWHEEL.md, ARCHITECTURE.md,
# AGENTS.md, CLAUDE.md) each carried a warning about the duplicate, and a
# reader or tool grepping for a symbol found the dead copy first. There is
# now exactly one DASHBOARD_HTML; tests/test_dashboard_html_defined_once.py
# keeps it that way.
DASHBOARD_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry</title>
<link rel="icon" href="/favicon.ico" type="image/x-icon">
<link rel="icon" href="/static/img/logo.svg" type="image/svg+xml">
<!-- Self-hosted webfonts. A page load must never contact a third party: an
     air-gapped install has no route to Google, and in the EU an embedded
     Google Fonts request discloses the viewer's IP to a US processor with
     no legal basis. Regenerate with scripts/vendor_fonts.py. -->
<link rel="stylesheet" href="{{ url_for('static', filename='css/fonts.css', v=version) }}">
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css', v=version) }}">
<script src="{{ url_for('static', filename='js/nav-dropdown.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='js/alerts.js', v=version) }}" defer></script>
<script src="{{ url_for('static', filename='js/trail.js', v=version) }}" defer></script>
<!-- Vendored + pinned (no external CDN, no supply-chain risk): marked renders
     transcript markdown, DOMPurify sanitizes it before it touches innerHTML.
     See cmSafeMarkdown() in app.js — never call marked.parse() into the DOM directly.
     chart.js + its date adapter are vendored on the same rule. Every file here is
     byte-compared against its npm registry tarball by scripts/verify_vendor.py,
     and scripts/verify_no_external_assets.py fails CI on any absolute http(s)
     asset reference. The dashboard must render fully with zero egress. -->
<script src="{{ url_for('static', filename='vendor/marked.min.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='vendor/purify.min.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='vendor/chart.umd.min.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='vendor/chartjs-adapter-date-fns.bundle.min.js', v=version) }}"></script>
</head>
<body data-theme="dark" class="booting has-profile-menu">
{% include 'partials/overlays.html' %}
<div class="zoom-wrapper" id="zoom-wrapper">
<div class="nav">
  <h1><a href="https://clawmetry.com" style="display:flex;align-items:center;gap:7px;text-decoration:none;color:inherit"><img src="/static/img/logo.svg" width="22" height="22" style="border-radius:4px;vertical-align:middle;flex-shrink:0" alt="ClawMetry"><span><span style="color:var(--text-primary)">Claw</span><span style="color:#E5443A">Metry</span></span></a></h1>
  <span id="version-badge" class="version-badge" title="ClawMetry version">v{{ version }}</span>
  <div id="workspace-switcher" style="display:none;position:relative;margin-left:8px;">
    <button id="workspace-switcher-btn" onclick="toggleWorkspaceSwitcher(event)" title="Switch profile (this machine). Local OpenClaw profiles only. For fleet view across multiple machines, upgrade to Pro." style="background:var(--button-bg);color:var(--text-tertiary);border:none;border-radius:8px;padding:8px 12px;cursor:pointer;display:flex;align-items:center;box-shadow:var(--card-shadow);transition:all 0.15s;">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
      <span id="workspace-switcher-label" style="display:none">default</span>
    </button>
    <div id="workspace-switcher-menu" style="display:none;position:absolute;top:calc(100% + 6px);left:0;min-width:240px;max-height:320px;overflow-y:auto;background:var(--bg-card,#1c2333);border:1px solid var(--border-color,rgba(255,255,255,0.1));border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.35);z-index:200;padding:4px;"></div>
  </div>
  <!-- Global runtime switcher: scope session views to one agent runtime
       (OpenClaw / Claude Code / Codex / NanoClaw / …). Hidden until >1 runtime
       is detected, so single-runtime installs are unchanged. -->
  <div id="cm-global-runtime-wrap" style="display:none;align-items:center;gap:6px;">
    <span style="font-size:11px;color:var(--text-muted);font-weight:600;">Runtime</span>
    <select id="cm-global-runtime" onchange="_cmOnGlobalRuntimeChange(this)" title="Scope session views to a single agent runtime" style="font-size:12px;font-weight:600;padding:7px 10px;border:1px solid var(--border-color,rgba(255,255,255,0.22));border-radius:8px;background:var(--button-bg,transparent);color:var(--text-tertiary,#cbd5e1);cursor:pointer;"></select>
  </div>
  <!-- Refresh / reconnect. Always visible, because the desktop shell has no
       browser chrome: no address bar, no reload button, and pywebview's Cocoa
       backend swallows Cmd-R. Without this the only way out of a wedged page
       was to quit the app. cmReconnect() probes the backend first and only
       reloads when something is there to reload into -- reloading against a
       dead port would replace the page with a blank error page. Turns amber
       (.cm-attention) once the backend is known unreachable. -->
  <div class="theme-toggle" id="cm-reconnect-btn" onclick="window.cmReconnect && window.cmReconnect()" role="button" tabindex="0" data-i18n-title="topbar.refresh" title="Refresh (Cmd/Ctrl + R)" style="cursor:pointer;">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
  </div>
  <div class="theme-toggle" id="alerts-bell-btn" onclick="switchTab('alerts')" data-i18n-title="topbar.active_alerts" title="Active alerts" style="cursor:pointer;position:relative;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg><span id="alerts-bell-badge" style="display:none;position:absolute;top:-4px;right:-4px;background:#ef4444;color:#fff;border-radius:10px;padding:0 4px;font-size:9px;font-weight:700;min-width:14px;line-height:14px;text-align:center;">0</span></div>
  {# Light/dark toggle REMOVED (header cleanup 2026-09): the light palette
     never got the polish the dark one has, so the toggle only ever led
     somewhere uglier. The dashboard is dark-only; <body data-theme="dark">
     above is the whole story and app.js no longer ships initTheme(). #}

  <!-- Cloud sync toggle chip. Included in every ClawMetry plan (Self-Hosted
       through Enterprise), so it's a one-click UX toggle here rather than a
       plan-tier decision. Hidden until the initial /api/cloud-cta/status
       poll resolves so it doesn't flash the wrong state on first paint.
       Refresh cadence: on load, on click, and after any focus event. -->
  <div class="theme-toggle" id="sync-toggle-btn" onclick="clawmetryToggleSync()" title="Cloud sync" style="display:none;cursor:pointer;padding:6px 10px;gap:6px;align-items:center;">
    <svg id="sync-toggle-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M17.5 19H9a7 7 0 1 1 6.71-9"/><polyline points="17 5 21 5 21 9"/></svg>
    <span id="sync-toggle-label" style="font-size:11px;font-weight:600;letter-spacing:0.2px;">Sync</span>
  </div>

  <div class="theme-toggle" id="logout-btn" onclick="clawmetryLogout()" data-i18n-title="topbar.logout" title="Logout" style="display:none;cursor:pointer;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg></div>
  <div class="i18n-switcher" id="i18n-switcher" style="position:relative;">
    <div id="i18n-switcher-btn" onclick="i18nToggleMenu(event)" data-i18n-title="i18n.language" title="Language" style="cursor:pointer;display:flex;align-items:center;gap:6px;border:1px solid var(--border-color,rgba(255,255,255,0.22));border-radius:8px;padding:7px 10px;color:var(--text-tertiary,#cbd5e1);background:var(--button-bg,transparent);transition:all 0.15s;" onmouseover="this.style.background='rgba(127,127,127,0.12)'" onmouseout="this.style.background='var(--button-bg,transparent)'">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
      <span id="i18n-current-label" style="font-size:12px;font-weight:700;letter-spacing:0.3px;">EN</span>
      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.7;"><polyline points="6 9 12 15 18 9"/></svg>
    </div>
    <div id="i18n-switcher-menu" role="menu" style="display:none;position:absolute;top:calc(100% + 6px);right:0;min-width:180px;max-height:360px;overflow-y:auto;background:var(--bg-card,#1c2333);border:1px solid var(--border-color,rgba(255,255,255,0.1));border-radius:8px;box-shadow:0 6px 18px rgba(0,0,0,0.35);z-index:200;padding:4px;"></div>
  </div>
  {# In-page zoom controls REMOVED (header cleanup 2026-09): the browser's
     own zoom already does this, and applyZoom() used to put a
     `transform: scale()` on #zoom-wrapper even at 100%, which made the
     wrapper a containing block for every `position: fixed` descendant
     (issue #1717). #}
  {% if legacy_nav %}
  <div class="nav-tabs">
    <div class="nav-tab" onclick="switchTab('flow')">Flow</div>
    <div class="nav-tab" onclick="switchTab('brain')">Brain</div>
    <div class="nav-tab active" onclick="switchTab('overview')">Overview <span id="nav-stuck-badge" style="display:none;background:#ef4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;margin-left:4px;">0</span></div>
    <div class="nav-tab" onclick="switchTab('approvals')" title="Cloud-mediated approval queue">Approvals <span id="nav-approvals-badge" style="display:none;background:#ef4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;margin-left:4px;">0</span></div>
    <div class="nav-tab" onclick="switchTab('alerts')" title="Get notified when something goes wrong">Alerts <span id="nav-alerts-badge" style="display:none;background:#ef4444;color:#fff;border-radius:10px;padding:1px 6px;font-size:10px;font-weight:700;margin-left:4px;">0</span></div>
    <div class="nav-tab" onclick="switchTab('notifications')" title="Slack / Email / PagerDuty / Telegram channels">Notifications</div>
    <div class="nav-tab" onclick="switchTab('context-economics')" title="Context-window usage from real per-turn readings">Context</div>
    <div class="nav-tab" onclick="switchTab('usage')">Tokens</div>
    <div class="nav-tab" id="crons-tab" onclick="switchTab('crons')">Crons</div>
    <div class="nav-tab" onclick="switchTab('memory')">Memory</div>
    <div class="nav-tab" onclick="switchTab('security')">Security</div>
    <div class="nav-tab" id="nemoclaw-tab" onclick="switchTab('nemoclaw')" style="display:none;">NemoClaw</div>
    <!-- History tab hidden until mature -->
    <!-- <div class="nav-tab" onclick="switchTab('history')">History</div> -->
    {% if v2_enabled %}
    <a class="nav-tab v1-to-v2-link" href="/v2" style="text-decoration:none;color:#E5443A;border-color:rgba(229,68,58,0.35);" title="Open the v2 (beta) dashboard">&#10024; Try v2 (beta) &#8599;</a>
    {% endif %}
  <div id="cloud-cta-btn" onclick="openCloudModal()" style="display:none;margin-left:8px;cursor:pointer;padding:6px 12px;border:1px solid rgba(96,165,250,0.5);border-radius:8px;font-size:12px;font-weight:600;color:#60a5fa;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(96,165,250,0.1)'" onmouseout="this.style.background='transparent'"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:4px"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Enable Cloud Sync</div>
  <div id="cloud-connected-badge" onclick="window.open('https://app.clawmetry.com/cloud','_blank')" style="display:none;margin-left:8px;cursor:pointer;padding:6px 12px;border:1px solid rgba(34,197,94,0.4);border-radius:8px;font-size:12px;font-weight:600;color:#22c55e;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(34,197,94,0.08)'" onmouseout="this.style.background='transparent'">&#9679; Cloud Connected</div>
  </div>
  {% else %}
  {# Phase-1 IA refactor (issue #1659): the top-nav keeps the logo / zoom
     / theme toggles, but tab navigation moves to the left sidebar below.
     Hidden chrome (cloud CTA, cloud-connected badge, v2 link) stays in the
     header because the rest of the JS still hides/shows them by id. #}
  <div style="margin-left:auto;display:flex;gap:8px;align-items:center;">
    {% if v2_enabled %}
    <a class="nav-tab v1-to-v2-link" href="/v2" style="text-decoration:none;color:#E5443A;border-color:rgba(229,68,58,0.35);" title="Open the v2 (beta) dashboard">&#10024; Try v2 (beta) &#8599;</a>
    {% endif %}
    <div id="cloud-cta-btn" onclick="openCloudModal()" style="display:none;cursor:pointer;padding:6px 12px;border:1px solid rgba(96,165,250,0.5);border-radius:8px;font-size:12px;font-weight:600;color:#60a5fa;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(96,165,250,0.1)'" onmouseout="this.style.background='transparent'"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="display:inline;vertical-align:middle;margin-right:4px"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>Enable Cloud Sync</div>
    <div id="cloud-connected-badge" onclick="window.open('https://app.clawmetry.com/cloud','_blank')" style="display:none;cursor:pointer;padding:6px 12px;border:1px solid rgba(34,197,94,0.4);border-radius:8px;font-size:12px;font-weight:600;color:#22c55e;white-space:nowrap;transition:all 0.2s;user-select:none;" onmouseover="this.style.background='rgba(34,197,94,0.08)'" onmouseout="this.style.background='transparent'">&#9679; Cloud Connected</div>
  </div>
  {% endif %}
  <!-- Trial pill + green Upgrade button. Deliberately OUTSIDE the legacy_nav
       if/else so both navs get exactly one instance, sitting immediately left
       of the account avatar (plan state belongs next to identity).
       Populated by static/js/trial-pill.js, which keeps it empty and
       display:none on every paid install — a paying customer must never be
       shown a countdown. Before this, a trialing user's only warning was a
       line two clicks deep in the avatar dropdown, and the only in-app path
       to a card form was the paywall that appears AFTER expiry. -->
  <div id="cm-trial-pill-slot"></div>
  <!-- Account menu: self-hosted installs sign in (trial/license) just like
       Cloud, so they get the same top-right profile affordance — identity,
       billing/plan management, and an always-visible sign-out. Rendered by
       cmProfileInit() in gw-setup.js; supersedes the bare #logout-btn icon
       (hidden via body.has-profile-menu in dashboard.css). -->
  <div id="cm-profile-wrap" style="position:relative;margin-left:8px;flex-shrink:0;">
    <button id="cm-profile-btn" onclick="cmProfileToggle(event)" data-i18n-title="profile.account" title="Account" aria-haspopup="menu" aria-expanded="false" style="width:32px;height:32px;border-radius:50%;border:1px solid var(--border-color,rgba(255,255,255,0.22));background:var(--button-bg,transparent);color:var(--text-tertiary,#cbd5e1);font-size:13px;font-weight:800;cursor:pointer;display:flex;align-items:center;justify-content:center;padding:0;box-shadow:var(--card-shadow);transition:all 0.15s;">
      <span id="cm-profile-initial" style="display:flex;align-items:center;justify-content:center;line-height:1;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></span>
    </button>
    <div id="cm-profile-menu" role="menu" style="display:none;position:absolute;top:calc(100% + 8px);right:0;min-width:250px;background:var(--bg-card,#1c2333);border:1px solid var(--border-color,rgba(255,255,255,0.1));border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,0.45);z-index:210;padding:6px;"></div>
  </div>
</div>
{% include 'partials/banners.html' %}

{% if not legacy_nav %}
{# Phase-1 IA refactor (issue #1659): 220px left sidebar + content grid.
   Primary nav holds 7 buckets; everything else lives in the Advanced
   drawer. Mobile (<=768px) collapses sidebar to an off-canvas hamburger
   triggered by #left-nav-mobile-toggle. #}
<button id="left-nav-mobile-toggle" type="button" aria-label="Open navigation" onclick="toggleLeftNavMobile()">&#9776;</button>
<div class="app-shell">
  <aside id="left-nav" role="navigation" aria-label="Primary">
    <div class="left-nav-section">
      {# Phase A of the beginner-IA restructure (UX_AUDIT.md): seven plain-words
         Tier-1 items, every expert view inside the default-collapsed Developer
         group below, config-ish tabs under Advanced. data-tab ids are STABLE -
         only labels and grouping changed. #}
      {# Reskin 2026-09: entity-glyph icons became 16px stroke SVGs and the
         Tier-1 list gained labeled sections (Observe / Analyze / Govern),
         Future-AGI-console style. data-tab ids, tooltips and i18n keys are
         UNCHANGED; only icons, ordering and section labels moved. The
         Approvals/Alerts/Notifications adjacency (founder request
         2026-07-29) is preserved inside Govern. #}
      <div class="left-nav-item active" data-tab="transcripts" onclick="switchTab('transcripts')" data-i18n-title="nav.session_replay_tooltip" title="Every session, newest first. Open one to see what it was asked, what it did, and how it ended">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.session_replay">Sessions</span>
      </div>

      {# Session-first IA (Trail, 2026-09): the product opens on the decision
         trail. Sessions is the landing item; the KPI board (Home) and the
         other raw-signal views sit under a "Monitoring" label. data-tab ids
         are unchanged; only order, labels and grouping moved. #}
      <div class="left-nav-section-label" data-i18n="nav.section_monitoring">Monitoring</div>
      <div class="left-nav-item" data-tab="overview" onclick="switchTab('overview')" data-i18n-title="nav.home_tooltip" title="Is everything OK, at a glance">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.home">Home</span>
        <span id="nav-stuck-badge" class="left-nav-badge" style="display:none;">0</span>
      </div>

      <div class="left-nav-item" data-tab="inventory" onclick="switchTab('inventory')" data-i18n-title="nav.inventory_tooltip" title="Every agent on this machine: what it runs, what it costs, is it alive, who owns it">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 8V4H8"/><rect width="16" height="12" x="4" y="8" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.inventory">Agents</span>
      </div>
      <div class="left-nav-item" data-tab="brain" onclick="switchTab('brain')" data-i18n-title="nav.activity_tooltip" title="What your agents are doing right now, step by step">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.brain">Activity</span>
      </div>

      <div class="left-nav-item" data-tab="usage" onclick="switchTab('usage')" data-i18n-title="nav.cost_tooltip" title="Token spend &amp; cost analytics">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><line x1="12" x2="12" y1="2" y2="22"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.cost">Cost</span>
      </div>
      <div class="left-nav-item" data-tab="models" onclick="switchTab('models')" data-i18n-title="nav.models_tooltip" title="Which models your agents used, and what each one cost">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M9 2v2M15 20v2M9 20v2M2 15h2M2 9h2M20 15h2M20 9h2"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.models">Models</span>
      </div>
      <div class="left-nav-item" id="left-nav-context-economics" data-tab="context-economics" onclick="switchTab('context-economics')" title="How full each agent's memory window gets, and when it had to forget">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-9-9"/><path d="M12 7v5l3 3"/><path d="M17 3l4 4-4 4"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.context_usage">Context usage</span>
      </div>

      <div class="left-nav-section-label" data-i18n="nav.section_analyze">Analyze</div>
      <div class="left-nav-item" data-tab="evals" onclick="switchTab('evals')" data-i18n-title="nav.quality_tooltip" title="Is your agent doing good work? See this week's report card and the runs that need attention.">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.quality">Quality</span>
      </div>
      <div class="left-nav-item" data-tab="bench" onclick="switchTab('bench')" data-i18n-title="nav.bench_tooltip" title="Which harness is engineered better for your work? Verdicts, cost per finished job, and what to route where.">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.bench">Harness Engineering</span>
      </div>

      <div class="left-nav-section-label" data-i18n="nav.section_govern">Govern</div>
      <div class="left-nav-item" data-tab="approvals" onclick="switchTab('approvals')" data-i18n-title="nav.approvals_tooltip" title="Cloud-mediated approval queue">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.approvals">Approvals</span>
        <span id="nav-approvals-badge" class="left-nav-badge" style="display:none;">0</span>
      </div>
      <div class="left-nav-item" data-tab="guard" onclick="switchTab('guard')" data-i18n-title="nav.guard_tooltip" title="See what is running, detect agents that go off track, and stop them">
        <span class="left-nav-icon" aria-hidden="true">&#128737;</span>
        <span class="left-nav-label" data-i18n="nav.guard">Guard</span>
        <span id="nav-guard-badge" class="left-nav-badge" style="display:none;">0</span>
      </div>
      <div class="left-nav-item" data-tab="signals" onclick="switchTab('signals')" data-i18n-title="nav.signals_tooltip" title="What people and agents say about a run: frustration, praise, refusals, giving up">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/><line x1="8" y1="9" x2="16" y2="9"/><line x1="8" y1="13" x2="13" y2="13"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.signals">Signals</span>
      </div>
      <div class="left-nav-item" data-tab="alerts" onclick="switchTab('alerts')" data-i18n-title="nav.alerts_tooltip" title="Get notified when something goes wrong with your agents">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.alerts">Alerts</span>
        <span id="nav-alerts-badge" class="left-nav-badge" style="display:none;">0</span>
      </div>
      {# Notifications sits directly under its two consumers (Approvals,
         Alerts) - founder request 2026-07-29: buried in the Advanced drawer,
         nobody could find where to connect a delivery channel, so enabled
         alert rules dead-ended at "no channels". #}
      <div class="left-nav-item" data-tab="notifications" onclick="switchTab('notifications')" data-i18n-title="nav.notifications_tooltip" title="Where Alerts and Approvals get delivered: Slack / Telegram / PagerDuty / Email">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.notifications">Notifications</span>
      </div>

      {# Developer drawer: the deep-dive views. Pure toggle (no data-tab: the
         header must not steal the overview highlight from Home). Collapsed by
         default; a stored cm_live_open=1 re-opens it. #}
      <div class="left-nav-item left-nav-item-group" onclick="toggleLiveDrawer()" data-i18n-title="nav.developer_tooltip" title="Deep-dive views for debugging your agents">
        <span class="left-nav-icon" aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/></svg></span>
        <span class="left-nav-label" data-i18n="nav.developer">Developer</span>
        <button type="button" class="left-nav-group-chevron" id="left-nav-live-toggle" aria-expanded="false" aria-controls="left-nav-live-list" aria-label="Toggle Developer sub-items" onclick="event.stopPropagation(); toggleLiveDrawer();">&#9662;</button>
      </div>
      <div class="left-nav-group-list" id="left-nav-live-list" hidden>
        <div class="left-nav-item left-nav-item-sub" data-tab="flow" onclick="switchTab('flow')">
          <span class="left-nav-label" data-i18n="nav.flow">Flow</span>
        </div>
        {# "LLM Context" merged into Context usage (2026-08-01): the old tab
           mixed hardcoded token estimates with a node-wide gauge. Context
           usage (context-economics) shows the same story from real per-turn
           readings, session + runtime scoped. switchTab('context') aliases
           there so old deep links keep working. #}
        {# Phase B (UX_AUDIT.md) removed Tracing, Turn timing and Compare
           sessions from the global nav as SESSION-scoped views, reached from a
           session drill-down (openSessionDeepDive in app.js, wired into the
           Sessions viewer). Turn timing and Compare sessions still are.
           TRACING IS BACK (#4782): a bring-your-own-agent app that speaks OTLP
           has no session at all -- its traces are keyed by OTel trace_id and
           never appear in the Sessions viewer -- so a drill-down-only entry
           point left those traces reachable by deep link only. #}
        <div class="left-nav-item left-nav-item-sub" id="left-nav-tracing" data-tab="tracing" onclick="switchTab('tracing')" title="Every run as a trace: the span waterfall, the span tree and the agent graph. Includes apps that send OpenTelemetry.">
          <span class="left-nav-label" data-i18n="nav.tracing">Tracing</span>
        </div>
        <div class="left-nav-item left-nav-item-sub" id="left-nav-agents" data-tab="agents" onclick="switchTab('agents')" title="Cross-session agent spawn topology from span data">
          <span class="left-nav-label" data-i18n="nav.agent_graph">Agent Graph</span>
        </div>
        <div class="left-nav-item left-nav-item-sub" id="left-nav-tool-catalog" data-tab="tool-catalog" onclick="switchTab('tool-catalog')" title="Every tool the agent uses by provenance, with call count and p50/p95 latency">
          <span class="left-nav-label" data-i18n="nav.tools">Tools</span>
        </div>
        <div class="left-nav-item left-nav-item-sub" id="left-nav-harness" data-tab="harness" onclick="switchTab('harness')" title="What a harness is, part by part, and where to watch each part live">
          <span class="left-nav-label" data-i18n="nav.harness">Harness</span>
        </div>
      </div>
    </div>

    <button type="button" class="left-nav-advanced-toggle" id="left-nav-advanced-toggle" onclick="toggleAdvancedDrawer()" aria-expanded="false">
      <span class="left-nav-label" data-i18n="nav.advanced">Advanced</span>
      <span class="left-nav-advanced-chevron" aria-hidden="true">&#9662;</span>
    </button>
    <div class="left-nav-advanced-list" id="left-nav-advanced-list" hidden>
      <div class="left-nav-item left-nav-item-sub" data-tab="crons" id="crons-tab" onclick="switchTab('crons')" data-i18n-title="nav.crons_tooltip" title="Scheduled agent jobs">
        <span class="left-nav-label" data-i18n="nav.crons">Schedules</span>
      </div>
      {# Memory + Skills stay under Advanced while the multi-runtime file
         browser matures (founder call 2026-08-14): known gaps — redundant
         runtime chips, file click not loading content, Skills rendering the
         Memory catalog. Promote to Tier-1 once those are fixed. #}
      <div class="left-nav-item left-nav-item-sub" data-tab="memory" onclick="switchTab('memory')" data-i18n-title="nav.memory_tooltip" title="Every runtime's on-disk memory files (CLAUDE.md, AGENTS.md, GEMINI.md, …) in one browser">
        <span class="left-nav-label" data-i18n="nav.memory">Memory</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="skills" onclick="switchTab('skills')" title="Every runtime's installed skills / commands / agents / hooks">
        <span class="left-nav-label" data-i18n="nav.skills">Skills</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="logs" onclick="switchTab('logs')" title="Live runtime log stream">
        <span class="left-nav-label">Logs</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="security" onclick="switchTab('security')">
        <span class="left-nav-label" data-i18n="nav.security">Security</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="policy" onclick="switchTab('policy')" title="Which tools each agent can run, where they run, and what got approved or blocked">
        <span class="left-nav-label" data-i18n="nav.tool_policy">Tool permissions</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="selfevolve" onclick="switchTab('selfevolve')">
        <span class="left-nav-label" data-i18n="nav.self_evolve">Self-Evolve</span>
      </div>
      <div class="left-nav-item left-nav-item-sub" data-tab="version-impact" onclick="switchTab('version-impact')">
        <span class="left-nav-label" data-i18n="nav.version_impact">Version impact</span>
      </div>
      <!-- Rate limits tab removed: cloud endpoint is hard-disabled by design
           (rate-limit state is per-node, doesn't ride the snapshot), and
           the local panel rendered empty for ~95% of users because the
           feed requires either OTLP exporter on the gateway or the opt-in
           clawmetry.track interceptor. Per-provider spend already lives on
           the Cost tab; 429s surface in Brain + Reliability. The
           /api/rate-limits endpoint stays for power users scripting it. -->
      <div class="left-nav-item left-nav-item-sub" data-tab="nemoclaw" id="nemoclaw-tab" onclick="switchTab('nemoclaw')" style="display:none;">
        <span class="left-nav-label">NemoClaw</span>
      </div>
    </div>
  </aside>
  <main class="app-shell-content">
{% endif %}

<!-- OVERVIEW (Split-Screen Hacker Dashboard) -->
{% include 'tabs/overview.html' %}

<!-- AGENT INVENTORY (single-pane control-tower roster) -->
{% include 'tabs/inventory.html' %}

<!-- ALERTS (Cloud-Pro feature) -->
{% include 'tabs/guard.html' %}
{% include 'tabs/signals.html' %}
{% include 'tabs/alerts.html' %}

<!-- EVALS (LLM-as-judge scores + named evaluator library + golden suites) -->
{% include 'tabs/evals.html' %}

<!-- BENCH (Harness Engineering: verdict stamps, $/done, flow deep dive, context lanes) -->
{% include 'tabs/bench.html' %}

<!-- USAGE -->
{% include 'tabs/usage.html' %}

<!-- DIVES (NL-to-SQL-to-chart over local DuckDB) -->

<!-- CRONS -->
{% include 'tabs/crons.html' %}

<!-- MEMORY -->
{% include 'tabs/memory.html' %}

<!-- TRANSCRIPTS -->
{% include 'tabs/transcripts.html' %}

<!-- TRAIL: one session as What it was asked / What it did / How it ended (session-first IA) -->
{% include 'tabs/trail.html' %}


<!-- UPGRADE IMPACT -->
{% include 'tabs/version-impact.html' %}

<!-- SESSION CLUSTERS -->

<!-- HISTORY -->

<!-- Rate limits panel removed -- see sidebar comment above. -->

{% include 'tabs/history.html' %}

<!-- FLOW -->
{% include 'tabs/flow.html' %}

<!-- BRAIN -->
{% include 'tabs/brain.html' %}

<!-- SELF-EVOLVE -->
{% include 'tabs/selfevolve.html' %}

<!-- NOTIFICATIONS -->
{% include 'tabs/notifications.html' %}

<!-- CONTEXT INSPECTOR -->

<!-- TRACING (Phoenix/Arize-style: span waterfall + tree + agent graph) -->
{% include 'tabs/tracing.html' %}

<!-- AGENT GRAPH (cross-session agent spawn topology, issue #1012) -->
{% include 'tabs/agents.html' %}

<!-- TURN ANATOMY (per-turn waterfall + stalled detector, P0-3) -->
{% include 'tabs/turn-anatomy.html' %}

<!-- TOOL CATALOG (provenance + p50/p95 latency + error rate, P1-3) -->
{% include 'tabs/tool-catalog.html' %}
{% include 'tabs/context-economics.html' %}

<!-- HARNESS (declarative per-runtime custom panel; #2667) -->
{% include 'tabs/harness.html' %}

<!-- LOGS (live stream + historical viewer; #3761) -->
{% include 'tabs/logs.html' %}

<!-- SWIMLANE COMPARE — N parallel live lanes (sessions / runtimes) -->
{% include 'tabs/swimlane.html' %}

<!-- SECURITY -->
{% include 'tabs/security.html' %}

<!-- TOOL POLICY + SANDBOX + EXEC-APPROVAL AUDIT (governance, PRD P1-1) -->
{% include 'tabs/policy.html' %}

<!-- APPROVALS — cloud-mediated approval queue (#667) -->
{% include 'tabs/approvals.html' %}

<!-- MODEL ATTRIBUTION (theme 2) -->
{% include 'tabs/models.html' %}

<!-- NEMOCLAW GOVERNANCE -->
{% include 'tabs/nemoclaw.html' %}

<!-- SUB-AGENT TREE (theme 2) -->

<!-- SKILLS FIDELITY (#687) -->
{% include 'tabs/skills.html' %}


{% if not legacy_nav %}
  </main>
</div> <!-- end app-shell -->
{% endif %}
<script src="{{ url_for('static', filename='js/i18n.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='js/runtime-logos.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='js/time-range-picker.js', v=version) }}"></script>
<!-- Provenance badges: the shared "measured / derived / estimated" component
     every dollar amount and score renders through. Loaded BEFORE app.js so
     window.cmMoney / cmProvBadge exist by the time a tab paints. -->
<script src="{{ url_for('static', filename='js/provenance.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='js/app.js', v=version) }}"></script>
</div> <!-- end zoom-wrapper -->

{# position:fixed overlays must live OUTSIDE #zoom-wrapper: its zoom
   transform makes it the containing block for fixed descendants, which
   stretches an inset:0 overlay to document height and pushes the centered
   card below the fold (users saw only the blur backdrop, issue: blank
   blurred dashboard on first run). #}
{% include 'partials/cloud-modal.html' %}
{% include 'partials/e2e-key-modal.html' %}
{% include 'partials/onboarding-modal.html' %}
{% include 'partials/selfhost-modal.html' %}
{% include 'partials/budget-modal.html' %}

<!-- Component Detail Modal -->
<div class="comp-modal-overlay" id="comp-modal-overlay" onclick="if(event.target===this)closeCompModal()">
  <div class="comp-modal-card">
    <div class="comp-modal-header">
      <div class="comp-modal-title" id="comp-modal-title">Component</div>
      <div style="display: flex; align-items: center; gap: 10px;">
        <div class="time-travel-toggle" id="time-travel-toggle" onclick="toggleTimeTravelMode()" title="Enable time travel">🕰️</div>
        <div class="comp-modal-close" onclick="closeCompModal()">&times;</div>
      </div>
    </div>
    <div class="time-travel-bar" id="time-travel-bar">
      <div class="time-travel-controls">
        <div class="time-nav-btn" onclick="timeTravel('prev-day')" title="Previous day">‹</div>
        <div class="time-scrubber">
          <div class="time-slider" id="time-slider" onclick="onTimeSliderClick(event)">
            <div class="time-slider-thumb" id="time-slider-thumb"></div>
          </div>
          <div class="time-display" id="time-display">Loading...</div>
        </div>
        <div class="time-nav-btn" onclick="timeTravel('next-day')" title="Next day">›</div>
        <div class="time-nav-btn" onclick="timeTravel('now')" title="Back to now">⏹</div>
      </div>
    </div>
    <div class="comp-modal-body" id="comp-modal-body">Loading...</div>
    <div class="comp-modal-footer" id="comp-modal-footer">Last updated: --</div>
  </div>
</div>

<!-- Task Detail Modal -->
<div class="modal-overlay" id="task-modal-overlay" onclick="if(event.target===this)closeTaskModal()">
  <div class="modal-card">
    <div class="modal-header">
      <div class="modal-header-left">
        <div class="modal-title" id="modal-title">Task Name</div>
        <div class="modal-session-key" id="modal-session-key">session-id</div>
      </div>
      <div class="modal-header-right">
        <label class="modal-auto-refresh"><input type="checkbox" id="modal-auto-refresh-cb" checked onchange="toggleModalAutoRefresh()"> Auto-refresh</label>
        <div class="modal-close" onclick="closeTaskModal()">&times;</div>
      </div>
    </div>
    <div class="modal-tabs">
      <div class="modal-tab active" onclick="switchModalTab('summary')">Summary</div>
      <div class="modal-tab" onclick="switchModalTab('narrative')">Narrative</div>
      <div class="modal-tab" onclick="switchModalTab('full')">Full Logs</div>
      <div class="modal-tab" onclick="switchModalTab('tools')">Tools</div>
      <div class="modal-tab" onclick="switchModalTab('models')">Model Journey</div>
      <div class="modal-tab" onclick="switchModalTab('subagents')">Subagents</div>
    </div>
    <div class="modal-content" id="modal-content">Loading...</div>
    <div class="modal-footer">
      <span id="modal-event-count">--</span>
      <span id="modal-msg-count">--</span>
    </div>
  </div>
</div>

<script src="{{ url_for('static', filename='js/gw-setup.js', v=version) }}"></script>
<script src="{{ url_for('static', filename='js/onboarding.js', v=version) }}"></script>
<!-- Loaded LAST: trial-pill.js reads window.CM_PLANS (published by app.js) as
     its price ladder and exposes window.cmOpenUpgradeModal, which gw-setup.js's
     profile menu calls. Both are looked up at call time, so load order only
     needs app.js to have run first. -->
<script src="{{ url_for('static', filename='js/trial-pill.js', v=version) }}"></script>

</body>
</html>
"""


# ── API Routes ──────────────────────────────────────────────────────────


# _acquire_stream_slot / _release_stream_slot moved to helpers/streams.py (re-exported above)


# ── Gateway API proxy (WebSocket JSON-RPC + HTTP fallback) ──────────────
import urllib.request as _urllib_req
import uuid as _uuid

_GW_CONFIG_FILE = os.path.expanduser("~/.clawmetry-gateway.json")


def _get_openclaw_dir():
    """Return the OpenClaw config directory, respecting CLAWMETRY_OPENCLAW_DIR env var and --openclaw-dir CLI flag."""
    return os.environ.get("CLAWMETRY_OPENCLAW_DIR", os.path.expanduser("~/.openclaw"))


# _ws_client / _ws_lock / _ws_connected moved to helpers/gateway.py (re-exported above)
# _gw_ws_connect / _gw_ws_rpc moved to helpers/gateway.py


def _load_gw_config():
    """Load gateway config from globals, env, or file.

    Token resolution order (Issue #321 - avoid stale cached tokens):
      1. Environment variable (OPENCLAW_GATEWAY_TOKEN)
      2. Live OpenClaw config (openclaw.json -> gateway.auth.token)
      3. Running gateway process /proc env
      4. CLI/env globals already set
      5. Cached ~/.clawmetry-gateway.json (backward compat fallback)
    """
    global GATEWAY_URL, GATEWAY_TOKEN
    # 1. Auto-detect from live OpenClaw config (most authoritative - reads directly)
    token = _detect_gateway_token()
    port = _detect_gateway_port()
    if token:
        GATEWAY_TOKEN = token
        if not GATEWAY_URL:
            # OPENCLAW_GATEWAY_URL lets Docker / reverse-proxy users point at a
            # remote gateway (e.g. Android) without touching the setup wizard.
            env_url = os.environ.get("OPENCLAW_GATEWAY_URL", "").strip()
            GATEWAY_URL = env_url if env_url else f"http://127.0.0.1:{port}"
        # Update cache file with fresh token (backward compat, not used for reads)
        try:
            cache = {}
            try:
                with open(_GW_CONFIG_FILE) as f:
                    cache = json.load(f)
            except Exception:
                pass
            cache["token"] = token
            cache["url"] = GATEWAY_URL or f"http://127.0.0.1:{port}"
            with open(_GW_CONFIG_FILE, "w") as f:
                json.dump(cache, f)
            os.chmod(_GW_CONFIG_FILE, 0o600)
        except Exception:
            pass
        return {"url": GATEWAY_URL, "token": GATEWAY_TOKEN}
    # 2. Already set via CLI/env
    if GATEWAY_URL and GATEWAY_TOKEN:
        return {"url": GATEWAY_URL, "token": GATEWAY_TOKEN}
    # 3. Fallback to cache file (only if live config unavailable)
    try:
        with open(_GW_CONFIG_FILE) as f:
            cfg = json.load(f)
            GATEWAY_URL = cfg.get("url", GATEWAY_URL)
            GATEWAY_TOKEN = cfg.get("token", GATEWAY_TOKEN)
            return cfg
    except Exception:
        pass
    return {}


# _gw_invoke / _gw_invoke_docker moved to helpers/gateway.py (re-exported above)


# ── Flask Blueprints (Phase 4) ────────────────────────────────────────────────
from flask import Blueprint as _Blueprint
# bp_alerts moved to routes/alerts.py
# bp_auth moved to routes/meta.py
# bp_brain moved to routes/brain.py
# bp_budget moved to routes/alerts.py
# bp_channels moved to routes/channels.py
# bp_components moved to routes/components.py
# bp_config moved to routes/infra.py
# bp_crons moved to routes/crons.py
# bp_fleet moved to routes/fleet_history.py
# bp_gateway moved to routes/meta.py
# bp_health moved to routes/health.py
# bp_logs moved to routes/infra.py
# bp_memory moved to routes/infra.py
# bp_otel moved to routes/meta.py
# bp_overview moved to routes/overview.py
# bp_sessions moved to routes/sessions.py
# bp_security moved to routes/infra.py
# bp_usage moved to routes/usage.py
# bp_version moved to routes/meta.py
# bp_version_impact moved to routes/meta.py

# bp_nemoclaw moved to routes/nemoclaw.py
# ─────────────────────────────────────────────────────────────────────────────

# ── NemoClaw Governance ───────────────────────────────────────────────────────
_nemoclaw_policy_hash = None  # Module-level: tracks last-seen policy hash for drift detection
_nemoclaw_drift_info = {}     # Stores drift metadata (old hash, new hash, timestamp)


def _detect_nemoclaw():
    """Returns dict with nemoclaw info, or None if not installed."""
    import shutil as _shutil
    from pathlib import Path as _Path
    if not _shutil.which("nemoclaw"):
        return None
    home = _Path.home()
    result = {"installed": True}
    # Load config
    cfg_path = home / ".nemoclaw" / "config.json"
    if cfg_path.exists():
        try:
            result["config"] = json.loads(cfg_path.read_text())
        except Exception:
            pass
    # Load state
    state_path = home / ".nemoclaw" / "state" / "nemoclaw.json"
    if state_path.exists():
        try:
            result["state"] = json.loads(state_path.read_text())
        except Exception:
            pass
    # Load policy
    policy_path = home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "policies" / "openclaw-sandbox.yaml"
    if policy_path.exists():
        try:
            result["policy_yaml"] = policy_path.read_text()
            result["policy_hash"] = __import__("hashlib").sha256(policy_path.read_bytes()).hexdigest()[:12]
        except Exception:
            pass
    # Load presets
    presets_dir = home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "policies" / "presets"
    if presets_dir.exists():
        try:
            result["presets"] = [p.stem for p in presets_dir.glob("*.yaml")]
        except Exception:
            pass
    # Load skill catalog metadata
    for _cat_path in [
        home / ".nemoclaw" / "source" / "nemoclaw-blueprint" / "skills" / "catalog-metadata.json",
        home / ".nemoclaw" / "skills" / "catalog-metadata.json",
    ]:
        if _cat_path.exists():
            try:
                _cat = json.loads(_cat_path.read_text())
                _meta = _cat.get("metadata", {})
                result["skill_catalog"] = {
                    "min_version": _meta.get("minNemoClawVersion", ""),
                    "tested_version": _meta.get("testedNemoClawVersion", ""),
                    "export_sha256": _cat.get("exportContentSha256", ""),
                    "source_commit": _cat.get("sourceCommit", _meta.get("sourceCommit", "")),
                    "source_sha256": _cat.get("sourceContentSha256", _meta.get("sourceContentSha256", "")),
                }
            except Exception:
                pass
            break
    # Get sandbox list
    try:
        import subprocess as _sp
        r = _sp.run(["nemoclaw", "list"], capture_output=True, text=True, timeout=5)
        result["sandbox_list_raw"] = r.stdout
    except Exception:
        pass
    return result


def _parse_network_policies(yaml_text):
    """Parse network_policies section from openclaw-sandbox.yaml.
    Returns list of {name, hosts} dicts without requiring PyYAML."""
    policies = []
    try:
        import yaml as _yaml
        data = _yaml.safe_load(yaml_text)
        if isinstance(data, dict):
            net = data.get("network_policies") or data.get("networkPolicies") or {}
            if isinstance(net, dict):
                for name, hosts in net.items():
                    if isinstance(hosts, list):
                        policies.append({"name": name, "hosts": hosts})
                    elif isinstance(hosts, str):
                        policies.append({"name": name, "hosts": [hosts]})
        return policies
    except ImportError:
        pass
    # Fallback: simple line-based parser for network_policies block
    in_block = False
    current_name = None
    current_hosts = []
    for line in yaml_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("network_policies:"):
            in_block = True
            continue
        if in_block:
            if not line.startswith(" ") and not line.startswith("\t") and stripped and not stripped.startswith("#"):
                if current_name:
                    policies.append({"name": current_name, "hosts": current_hosts})
                in_block = False
                break
            if stripped.endswith(":") and not stripped.startswith("-"):
                if current_name:
                    policies.append({"name": current_name, "hosts": current_hosts})
                current_name = stripped[:-1]
                current_hosts = []
            elif stripped.startswith("- ") and current_name:
                current_hosts.append(stripped[2:].strip())
            elif current_name and ":" in stripped and not stripped.startswith("-"):
                # key: value host format
                parts = stripped.split(":", 1)
                if len(parts) == 2:
                    current_hosts.append(stripped.strip())
    if current_name:
        policies.append({"name": current_name, "hosts": current_hosts})
    return policies

# (bp_nemoclaw handlers moved to routes/nemoclaw.py: /api/nemoclaw/governance,
#  /api/nemoclaw/governance/acknowledge-drift)


# ── Version check & self-update routes ────────────────────────────────────────
# State for /api/version PyPI lookup cache, used by routes/meta.py.
_pypi_cache = {"ts": 0, "version": None}


# (bp_version handlers moved to routes/meta.py: /api/version, /api/update)


# ──────────────────────────────────────────────────────────────────────────────


# (bp_gateway handlers moved to routes/meta.py: /api/gw/config,
#  /api/gw/invoke, /api/gw/rpc)


def _auto_discover_gateway(token):
    """Scan common ports to find an OpenClaw gateway."""
    # Honour explicit remote URL before scanning localhost (issue #2106 — Docker/reverse-proxy).
    env_url = os.environ.get("OPENCLAW_GATEWAY_URL", "").strip()
    if env_url:
        return env_url  # Caller validates; wrong URL surfaces a clear error there.

    common_ports = [18789, 56089]
    # Also check env and config files
    env_port = os.environ.get("OPENCLAW_GATEWAY_PORT")
    if env_port:
        try:
            common_ports.insert(0, int(env_port))
        except ValueError:
            pass
    # Add ports from config files
    for cfg_name in ["moltbot.json", "clawdbot.json", "openclaw.json"]:
        for base in [
            os.path.expanduser("~/.openclaw"),
            os.path.expanduser("~/.clawdbot"),
        ]:
            try:
                with open(os.path.join(base, cfg_name)) as f:
                    c = json.load(f)
                    p = c.get("gateway", {}).get("port")
                    if p and p not in common_ports:
                        common_ports.insert(0, int(p))
            except Exception:
                pass
    # Scan for additional ports
    for port_offset in range(0, 100):
        p = 18700 + port_offset
        if p not in common_ports:
            common_ports.append(p)

    for port in common_ports[:20]:  # Cap at 20 ports to scan
        # Try WebSocket first, then HTTP
        url = f"http://127.0.0.1:{port}"
        ws_url = f"ws://127.0.0.1:{port}"
        try:
            import websocket

            ws = websocket.create_connection(f"{ws_url}/", timeout=2)
            ws.recv()  # challenge
            connect_msg = {
                "type": "req",
                "id": "discover",
                "method": "connect",
                "params": {
                    "minProtocol": _GW_MIN_PROTO,
                    "maxProtocol": _GW_MAX_PROTO,
                    "client": {
                        "id": "cli",
                        "version": __version__,
                        "platform": _CURRENT_PLATFORM,
                        "mode": "cli",
                        "instanceId": "clawmetry-discover",
                    },
                    "role": "operator",
                    "scopes": ["operator.admin", "operator.read"],
                    "auth": {"token": token},
                },
            }
            ws.send(json.dumps(connect_msg))
            for _ in range(5):
                r = json.loads(ws.recv())
                if r.get("type") == "res" and r.get("id") == "discover":
                    ws.close()
                    if r.get("ok"):
                        return url
                    break
            try:
                ws.close()
            except Exception:
                pass
        except Exception:
            pass
        # HTTP fallback
        try:
            payload = json.dumps({"tool": "session_status", "args": {}}).encode()
            req = _urllib_req.Request(
                f"{url}/tools/invoke",
                data=payload,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with _urllib_req.urlopen(req, timeout=2) as resp:
                result = json.loads(resp.read())
                if result.get("ok"):
                    return url
        except Exception:
            continue

    # Last resort: try docker exec
    try:
        result = _gw_invoke_docker("session_status", {}, token)
        if result:
            return "docker://localhost:18789"  # sentinel value indicating docker mode
    except Exception:
        pass
    return None


# (bp_auth handlers moved to routes/meta.py: /api/auth/check, /auth, /)


@app.before_request
def _latency_probe_start():
    """Issue #1283: per-endpoint p50/p95 timing for /api/handler-latency."""
    try:
        from flask import g
        import time as _t
        g._lat_start = _t.perf_counter()
    except Exception:
        pass


@app.after_request
def _latency_probe_record(response):
    try:
        from flask import g, request
        import time as _t
        start = getattr(g, "_lat_start", None)
        path = request.path or ""
        if start is not None and path.startswith("/api/"):
            elapsed_ms = (_t.perf_counter() - start) * 1000.0
            from clawmetry import latency_tracker as _lt
            _lt.record(request.endpoint or path, elapsed_ms)
    except Exception:
        pass
    return response


# Bodies bigger than this are left alone: the rewrite below exists for the
# unreachable case, where a handler has almost nothing to say. A multi-MB
# payload means the store answered.
_STORE_FLAG_MAX_BYTES = 2 * 1024 * 1024


@app.after_request
def _stamp_store_available(response):
    """Say so when a read in this request could not reach the local store.

    Issue #5534: a daemon-proxy timeout ends as ``None`` in the handler and
    renders as an EMPTY tab — "no sessions have a transcript yet" under a
    header counting 61, ``{"models": []}`` over a store holding thousands.
    An empty state is a positive claim about the user's own work; when the
    truth is "I could not read it", that claim is false and reads exactly
    like data loss.

    The Cost and Efficiency Analytics blueprint already specifies the field
    (``store_available``) and a handful of endpoints set it themselves. This
    stamps it on every JSON object that did NOT answer the question, so a
    fast path written tomorrow cannot reintroduce the confident empty —
    there is no helper anyone has to remember to call.

    Only ever adds ``false``. Silence stays silence: a handler that already
    reports the fact keeps its own value, and a request where nothing failed
    is untouched, so no existing response shape or snapshot test moves.
    """
    try:
        from routes.local_query import store_available as _store_available
        if _store_available():
            return response
        path = request.path or ""
        if not (path.startswith("/api/") or path.startswith("/v1/")):
            return response
        # The header is the cheap universal signal: the frontend's banner
        # reads it without paying to clone and parse every response body.
        response.headers["X-CM-Store-Available"] = "false"
        if response.direct_passthrough or response.is_streamed:
            return response
        if (response.mimetype or "") != "application/json":
            return response
        raw = response.get_data()
        if not raw or len(raw) > _STORE_FLAG_MAX_BYTES:
            return response
        body = json.loads(raw.decode("utf-8"))
        if not isinstance(body, dict) or "store_available" in body:
            return response
        body["store_available"] = False
        response.set_data(json.dumps(body))
    except Exception:
        pass
    return response


_SAFE_METHODS = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})


def _cross_origin_write_blocked() -> bool:
    """True when this request is a browser-driven WRITE from another site.

    Loopback callers skip authentication entirely (``_check_auth`` below) —
    that is the right posture for a local tool, but on its own it means any
    page the user happens to have open in another tab can drive this API. A
    cross-origin ``<form method=post>`` needs no CORS permission to *arrive*;
    the browser only stops the attacker reading the reply. The side effect
    still lands, so the endpoints that need no request body were reachable
    from any website: rotate the E2E key (making everything already synced
    undecryptable to its owner), emergency-stop the agents, kill every cron,
    deactivate the licence.

    The check is deliberately narrow so nothing legitimate breaks:

    * Safe methods are never blocked — this is CSRF defence, not CORS.
    * A request with **no** ``Origin`` is allowed. Browsers always attach one
      to a non-GET fetch, same-origin included; curl, the CLI, the desktop
      shell and OTLP exporters do not. So absence means "not a browser",
      which is exactly the traffic that must keep working.
    * An ``Origin`` that matches the host this request was addressed to is
      the dashboard talking to itself.

    Everything else is a page on another origin writing to your dashboard.
    ``CLAWMETRY_ALLOW_CROSS_ORIGIN_WRITES=1`` opts out for an embedder that
    genuinely needs it; see docs/EGRESS.md.
    """
    if request.method in _SAFE_METHODS:
        return False
    if str(
        os.environ.get("CLAWMETRY_ALLOW_CROSS_ORIGIN_WRITES", "")
    ).strip().lower() in ("1", "true", "yes"):
        return False
    origin = (request.headers.get("Origin") or "").strip()
    if not origin:
        return False
    try:
        from urllib.parse import urlparse as _urlparse

        netloc = _urlparse(origin).netloc
    except Exception:
        return True  # unparseable Origin — fail closed
    return netloc.lower() != (request.host or "").lower()


@app.before_request
def _check_auth():
    """Require valid gateway token for all /api/* routes when GATEWAY_TOKEN is set."""
    # CSRF guard first: it applies to EVERY state-changing request, including
    # the loopback callers that skip the token check below and the paths
    # (auth-check, gateway config, fleet API) that return early from it.
    if request.path.startswith("/api/") or request.path.startswith("/v1/"):
        if _cross_origin_write_blocked():
            return jsonify(
                {
                    "error": (
                        "Cross-origin write refused. This endpoint changes state "
                        "and may only be called from the dashboard itself."
                    ),
                    "crossOriginBlocked": True,
                }
            ), 403
    if request.path == "/api/auth/check":
        return  # Auth check endpoint is always accessible
    if request.path == "/api/gw/config":
        # Gateway setup must work before auth is configured, but only from
        # loopback: this route opens an outbound connection to a caller-supplied
        # URL, so a non-loopback caller must be authenticated (SSRF guard).
        _r = request.remote_addr or ""
        if _r in ("127.0.0.1", "::1", "localhost"):
            return
        # else fall through to the standard token check below
    if request.path.startswith("/api/nodes"):
        return  # Fleet API uses its own X-Fleet-Key authentication
    # OTLP ingestion (/v1/metrics|traces|logs) accepts UNTRUSTED data that lands
    # in cost/usage analytics, so it must not be open to the network. Gate it
    # like /api/*: loopback is trusted (zero-config local exporters keep working),
    # non-loopback requires the gateway token. Opt out for a trusted LAN with
    # CLAWMETRY_OTLP_ALLOW_UNAUTH=1.
    is_otlp = request.path.startswith("/v1/")
    if not request.path.startswith("/api/") and not is_otlp:
        return  # HTML, static, etc. are fine
    if is_otlp and str(os.environ.get("CLAWMETRY_OTLP_ALLOW_UNAUTH", "")).strip().lower() in ("1", "true", "yes"):
        return
    # Trust localhost — the dashboard is a local tool; auth protects remote access only
    remote = request.remote_addr or ""
    if remote in ("127.0.0.1", "::1", "localhost"):
        return
    if not GATEWAY_TOKEN:
        return jsonify(
            {
                "error": "Gateway token not configured. Please set up your gateway token first.",
                "needsSetup": True,
            }
        ), 401
    token = request.headers.get("Authorization", "").replace("Bearer ", "").strip()
    if not token:
        token = request.args.get("token", "").strip()
    if hmac.compare_digest(token, GATEWAY_TOKEN):
        return
    return jsonify({"error": "Unauthorized", "authRequired": True}), 401


# (moved to routes/overview.py)


# (moved to routes/overview.py)


# (moved to routes/overview.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (moved to routes/sessions.py)


# (8 route handlers moved to routes/crons.py: /api/crons, /api/cron/fix,
#  /api/cron/run, /api/cron/toggle, /api/cron/delete, /api/cron/update,
#  /api/cron/create, /api/cron/<job_id>/runs)


def _enrich_cron_runs(job_id, runs):
    """Add p50/p95 duration and cost stats to a list of cron run records."""
    if not runs:
        return {"jobId": job_id, "runs": [], "stats": {}}

    durations = sorted([r.get("durationMs", 0) for r in runs if r.get("durationMs")])
    costs = [
        r.get("costUsd", 0.0) or r.get("cost_usd", 0.0)
        for r in runs
        if (r.get("costUsd") or r.get("cost_usd"))
    ]
    ok_count = sum(1 for r in runs if r.get("status") in ("ok", "success", "completed"))
    err_count = sum(
        1 for r in runs if r.get("status") in ("error", "failed", "failure")
    )

    def _pct(lst, p):
        if not lst:
            return 0
        idx = int(len(lst) * p / 100)
        return lst[min(idx, len(lst) - 1)]

    stats = {
        "totalRuns": len(runs),
        "successCount": ok_count,
        "errorCount": err_count,
        "successRate": round(ok_count / len(runs) * 100, 1) if runs else 0,
        "avgDurationMs": int(sum(durations) / len(durations)) if durations else 0,
        "p50DurationMs": _pct(durations, 50),
        "p95DurationMs": _pct(durations, 95),
        "avgCostUsd": round(sum(costs) / len(costs), 6) if costs else 0.0,
        "totalCostUsd": round(sum(costs), 6),
    }
    return {"jobId": job_id, "runs": runs[:50], "stats": stats}


def _cron_runs_from_transcripts(job_id):
    """Derive synthetic cron run records from JSONL session analytics."""
    analytics = _compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    jobs = _get_crons()
    target_job = next(
        (j for j in jobs if isinstance(j, dict) and j.get("id") == job_id), None
    )

    runs = []
    for sess in sessions:
        if not sess.get("is_cron_candidate"):
            continue
        # Check if this session is attributed to the target job
        score = (
            _score_cron_match(sess, target_job or {"id": job_id}) if target_job else 0
        )
        explicit = job_id in (sess.get("explicit_cron_refs") or set())
        if score < 20 and not explicit:
            continue

        start_ts = sess.get("start_ts", 0)
        end_ts = sess.get("end_ts", 0)
        dur_ms = int((end_ts - start_ts) * 1000) if end_ts > start_ts else 0
        runs.append(
            {
                "sessionId": sess.get("session_id", ""),
                "timestamp": int(start_ts * 1000) if start_ts else 0,
                "status": "ok",
                "durationMs": dur_ms,
                "costUsd": round(float(sess.get("cost_usd", 0.0) or 0.0), 6),
                "tokens": sess.get("tokens", 0),
            }
        )

    # Most-recent first
    runs.sort(key=lambda r: r.get("timestamp", 0), reverse=True)
    return runs[:50]


# (5 route handlers moved to routes/crons.py: /api/cron/<id>/kill,
#  /api/cron-run-log, /api/cron/health-summary, /api/cron/kill-all,
#  /api/cron-health)


# _find_log_file moved to helpers/logs.py (re-exported above)


# _infer_provider_from_model moved to helpers/pricing.py (re-exported above)


# (4 route handlers moved to routes/overview.py: /api/timeline,
#  /api/cloud-cta/status, /api/cloud-cta/send-otp, /api/cloud-cta/verify-otp)


# (bp_logs routes moved to routes/infra.py: /api/logs, /api/flow-events,
#  /api/flow, /api/logs-stream)
# (bp_memory routes moved to routes/infra.py: /api/memory-files, /api/memory,
#  /api/file, /api/memory-analytics)


# (bp_otel handlers moved to routes/meta.py: /v1/metrics, /v1/traces,
#  /api/otel-status)


# ── Multi-Node Fleet API Routes ──────────────────────────────────────────

FLEET_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ClawMetry Fleet</title>
<link rel="stylesheet" href="/static/css/fonts.css">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body { font-family: 'Manrope', sans-serif; background: #0f1117; color: #e0e0e0; padding: 24px; }
  .header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
  .header h1 { font-size: 28px; font-weight: 800; }
  .header h1 span { color: #0f6fff; }
  .header .back { color: #667; text-decoration: none; font-size: 14px; }
  .header .back:hover { color: #0f6fff; }
  .summary { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
  .stat-card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 12px; padding: 16px 20px; min-width: 150px; }
  .stat-card .label { font-size: 12px; color: #667; text-transform: uppercase; letter-spacing: 0.5px; }
  .stat-card .value { font-size: 28px; font-weight: 700; margin-top: 4px; }
  .stat-card .value.green { color: #22c55e; }
  .stat-card .value.red { color: #ef4444; }
  .stat-card .value.blue { color: #0f6fff; }
  .search { margin-bottom: 16px; }
  .search input { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 8px; padding: 10px 16px; color: #e0e0e0; font-size: 14px; width: 300px; outline: none; }
  .search input:focus { border-color: #0f6fff; }
  .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
  .node-card { background: #1a1d27; border: 1px solid #2a2d37; border-radius: 12px; padding: 20px; cursor: pointer; transition: border-color 0.2s, transform 0.1s; }
  .node-card:hover { border-color: #0f6fff; transform: translateY(-2px); }
  .node-card .top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
  .node-card .name { font-size: 16px; font-weight: 700; }
  .node-card .status { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase; }
  .node-card .status.online { background: #16301d; color: #22c55e; }
  .node-card .status.offline { background: #2d1515; color: #ef4444; }
  .node-card .status.unknown { background: #2a2a1a; color: #eab308; }
  .node-card .meta { font-size: 12px; color: #667; margin-bottom: 12px; }
  .node-card .metrics { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
  .node-card .metric { }
  .node-card .metric .ml { font-size: 11px; color: #667; }
  .node-card .metric .mv { font-size: 15px; font-weight: 600; }
  .node-card .svc-bar { display: flex; gap: 6px; align-items: center; margin-top: 12px; padding-top: 12px; border-top: 1px solid #2a2d37; flex-wrap: wrap; }
  .svc-dot { display: flex; align-items: center; gap: 4px; font-size: 11px; color: #889; }
  .svc-dot .dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
  .svc-dot .dot.green { background: #22c55e; box-shadow: 0 0 4px rgba(34,197,94,0.5); }
  .svc-dot .dot.yellow { background: #eab308; box-shadow: 0 0 4px rgba(234,179,8,0.5); }
  .svc-dot .dot.red { background: #ef4444; box-shadow: 0 0 4px rgba(239,68,68,0.5); }
  .svc-dot .dot.gray { background: #4b5563; }
  .empty { text-align: center; padding: 60px; color: #667; }
  .empty h2 { font-size: 20px; margin-bottom: 8px; color: #888; }
  .empty code { background: #1a1d27; padding: 2px 8px; border-radius: 4px; font-size: 13px; }
</style>
</head>
<body>
<div class="header">
  <a href="/" class="back">< Dashboard</a>
  <h1><span>ClawMetry</span> Fleet</h1>
</div>
<div class="summary" id="summary"></div>
<div class="search"><input type="text" id="search" placeholder="Search nodes..." oninput="filterNodes()"></div>
<div class="grid" id="grid"></div>
<div class="empty" id="empty" style="display:none">
  <h2>No nodes registered yet</h2>
  <p>Register a node by sending a POST request:</p>
  <p style="margin-top:12px"><code>curl -X POST -H "X-Fleet-Key: YOUR_KEY" -H "Content-Type: application/json" \<br>
  -d '{"node_id":"my-node","name":"My Agent"}' http://THIS_HOST/api/nodes/register</code></p>
</div>
<script>
window.onerror = function(msg, src, line, col, err) {
  if(window._jsErrSent) return;
  window._jsErrSent = true;
  var nid = (localStorage.getItem('cm_node_id') || '');
  fetch('/api/js-error', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message:msg, source:src, lineno:line, colno:col, stack:err?err.stack:'', url:location.href, node_id:nid})
  }).catch(function(){});
};
window.addEventListener('unhandledrejection', function(e){
  if(window._jsErrSent) return;
  window._jsErrSent = true;
  fetch('/api/js-error', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({message: e.reason ? String(e.reason) : 'unhandledrejection', source:'promise', lineno:0, colno:0, stack:'', url:location.href, node_id:(localStorage.getItem('cm_node_id')||'')})
  }).catch(function(){});
});
let allNodes = [];
async function load() {
  const r = await fetch('/api/nodes');
  const d = await r.json();
  allNodes = d.nodes || [];
  const s = d.fleet_summary || {};
  document.getElementById('summary').innerHTML = `
    <div class="stat-card"><div class="label">Total Nodes</div><div class="value blue">${s.total_nodes||0}</div></div>
    <div class="stat-card"><div class="label">Online</div><div class="value green">${s.online||0}</div></div>
    <div class="stat-card"><div class="label">Offline</div><div class="value red">${s.offline||0}</div></div>
    <div class="stat-card"><div class="label">Cost Today</div><div class="value">$${(s.total_cost_today||0).toFixed(2)}</div></div>
    <div class="stat-card"><div class="label">Sessions Today</div><div class="value">${s.total_sessions_today||0}</div></div>
  `;
  renderNodes(allNodes);
}
function svcDot(label, colorClass) {
  return `<div class="svc-dot"><div class="dot ${colorClass}"></div>${esc(label)}</div>`;
}
function renderServiceBar(m) {
  // Build service status bar from metrics service_status field
  const ss = m.service_status || {};
  if (!ss || Object.keys(ss).length === 0) return '';
  const items = [];
  // Gateway
  if ('gateway' in ss) items.push(svcDot('GW', ss.gateway ? 'green' : 'red'));
  // Channels (array of {name, connected})
  const channels = Array.isArray(ss.channels) ? ss.channels : [];
  channels.forEach(function(ch) {
    const c = ch.connected ? 'green' : 'red';
    items.push(svcDot(esc(ch.name||'ch'), c));
  });
  // Sync daemon
  if ('sync' in ss) items.push(svcDot('sync', ss.sync ? 'green' : 'red'));
  // Resources (yellow if degraded)
  if ('resources' in ss) {
    const rc = ss.resources === 'ok' ? 'green' : (ss.resources === 'warn' ? 'yellow' : 'red');
    items.push(svcDot('res', rc));
  }
  if (!items.length) return '';
  return `<div class="svc-bar">${items.join('')}</div>`;
}
function renderNodes(nodes) {
  const grid = document.getElementById('grid');
  const empty = document.getElementById('empty');
  if (!nodes.length) { grid.innerHTML=''; empty.style.display='block'; return; }
  empty.style.display='none';
  grid.innerHTML = nodes.map(n => {
    const m = n.latest_metrics || {};
    const ago = n.last_seen_at ? timeSince(n.last_seen_at) : 'never';
    const cost = (m.cost && m.cost.today_usd) ? m.cost.today_usd.toFixed(2) : '0.00';
    const sessions = (m.sessions && m.sessions.total_today) || 0;
    const model = m.model || 'unknown';
    const disk = (m.health && m.health.disk_pct) ? m.health.disk_pct.toFixed(0)+'%' : '-';
    const svcBar = renderServiceBar(m);
    const secMeta = m.security || {};
    const sandboxedBadge = secMeta.sandbox_enabled
      ? '<span style="display:inline-block;padding:1px 7px;border-radius:10px;font-size:10px;font-weight:600;background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3);">🔒 Sandboxed</span>'
      : '';
    return `<div class="node-card" onclick="location.href='/api/nodes/${n.node_id}'">
      <div class="top"><div class="name">${esc(n.name||n.node_id)}</div><div style="display:flex;align-items:center;gap:6px;">${sandboxedBadge}<div class="status ${n.status}">${n.status}</div></div></div>
      <div class="meta">${esc(n.hostname||'')} - last seen ${ago}</div>
      <div class="metrics">
        <div class="metric"><div class="ml">Cost Today</div><div class="mv">$${cost}</div></div>
        <div class="metric"><div class="ml">Sessions</div><div class="mv">${sessions}</div></div>
        <div class="metric"><div class="ml">Model</div><div class="mv">${esc(model)}</div></div>
        <div class="metric"><div class="ml">Disk</div><div class="mv">${disk}</div></div>
      </div>
      ${svcBar}
    </div>`;
  }).join('');
}
function filterNodes() {
  const q = document.getElementById('search').value.toLowerCase();
  renderNodes(allNodes.filter(n => (n.name||'').toLowerCase().includes(q) || (n.node_id||'').includes(q) || (n.hostname||'').toLowerCase().includes(q) || JSON.stringify(n.tags||[]).toLowerCase().includes(q)));
}
function timeSince(ts) {
  const s = Math.floor(Date.now()/1000 - ts);
  if (s<60) return s+'s ago'; if (s<3600) return Math.floor(s/60)+'m ago';
  if (s<86400) return Math.floor(s/3600)+'h ago'; return Math.floor(s/86400)+'d ago';
}
function esc(s) { const d=document.createElement('div'); d.textContent=s; return d.innerHTML; }
load(); setInterval(load, 30000);
</script>
</body>
</html>
"""


# ── Fleet + History API Routes moved to routes/fleet_history.py ─────────


# ── Billing Mode Heuristics (API key vs OAuth/included) ──────────────────

_openclaw_cfg_cache = None


def _load_openclaw_config_cached():
    """Load OpenClaw config once (best effort)."""
    global _openclaw_cfg_cache
    if _openclaw_cfg_cache is not None:
        return _openclaw_cfg_cache
    for cf in [
        os.path.expanduser("~/.openclaw/openclaw.json"),
        os.path.expanduser("~/.clawdbot/openclaw.json"),
    ]:
        try:
            with open(cf) as f:
                _openclaw_cfg_cache = json.load(f)
                return _openclaw_cfg_cache
        except Exception:
            continue
    _openclaw_cfg_cache = {}
    return _openclaw_cfg_cache


# _provider_from_model moved to helpers/pricing.py (re-exported above)


def _provider_has_api_key(provider):
    provider = str(provider or "").lower()
    env_map = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "google": ["GOOGLE_API_KEY", "GEMINI_API_KEY"],
        "openrouter": ["OPENROUTER_API_KEY"],
        "xai": ["XAI_API_KEY"],
    }

    # 1) Direct env check
    for key in env_map.get(provider, []):
        if os.environ.get(key, "").strip():
            return True

    # 2) Config-based check -- try both legacy `providers` and OpenClaw `auth.profiles`
    cfg = _load_openclaw_config_cached()

    # 2a) Legacy: top-level `providers.<name>.apiKey`
    providers = cfg.get("providers", {}) if isinstance(cfg, dict) else {}
    pconf = providers.get(provider, {}) if isinstance(providers, dict) else {}
    if isinstance(pconf, dict):
        api_key = str(pconf.get("apiKey", "")).strip()
        api_key_env = str(pconf.get("apiKeyEnv", "")).strip()
        if api_key:
            return True
        if api_key_env and os.environ.get(api_key_env, "").strip():
            return True

    # 2b) OpenClaw style: `auth.profiles.<provider:*>.mode == "token"`
    auth = cfg.get("auth", {}) if isinstance(cfg, dict) else {}
    profiles = auth.get("profiles", {}) if isinstance(auth, dict) else {}
    for profile_name, profile_cfg in (
        profiles.items() if isinstance(profiles, dict) else []
    ):
        if not isinstance(profile_cfg, dict):
            continue
        profile_provider = str(profile_cfg.get("provider", "")).lower()
        if profile_provider == provider and profile_cfg.get("mode") == "token":
            return True

    return False


def _build_model_billing(model_usage):
    """Return per-model billing heuristics + summary for UI."""
    model_billing = []
    has_api_key_model = False
    has_non_api_key_model = False

    for model, tokens in sorted(model_usage.items(), key=lambda x: -x[1]):
        provider = _provider_from_model(model)
        api_key_configured = _provider_has_api_key(provider)
        mode = "likely_api_key" if api_key_configured else "likely_oauth_or_included"
        if api_key_configured:
            has_api_key_model = True
        else:
            has_non_api_key_model = True

        model_billing.append(
            {
                "model": model,
                "provider": provider,
                "tokens": tokens,
                "apiKeyConfigured": api_key_configured,
                "billingMode": mode,
            }
        )

    if has_api_key_model and has_non_api_key_model:
        summary = "mixed"
    elif has_api_key_model:
        summary = "likely_api_key"
    else:
        summary = "likely_oauth_or_included"

    return model_billing, summary


def _get_billing_coverage(model_billing, today_cost, week_cost, month_cost,
                          fallback_all_covered_when_no_models=False):
    """Detect the user's active subscription plan and split reported
    API-equivalent cost into ``covered_usd`` (paid for by the plan → $0
    out-of-pocket) vs ``out_of_pocket_usd`` (actual incremental spend).

    Users on Claude Max / ChatGPT Plus / Cursor Pro etc. see alarming
    "$X.YZ" cost numbers on the Cost tab even though their subscription
    already covers those calls — the incremental cost is $0. This helper
    is what lets the UI paint a green "Covered by <plan>" badge and stop
    the panic. Same detection path the fleet heartbeat uses on-device
    (`clawmetry.sync._build_billing_payload`), so device and dashboard
    agree on the plan label.

    Split heuristic: proportional to token share of models the per-model
    billing pass classified as OAuth/included (`apiKeyConfigured=False`).
    When the caller has no per-model tokens (local_store fast path),
    ``fallback_all_covered_when_no_models`` treats a detected subscription
    as covering the full amount — coarse but honest to the device UX.

    Always returns a dict; never raises. Cost fields are floats in USD.
    """
    try:
        from clawmetry.sync import _build_billing_payload  # noqa: WPS433
        payload = _build_billing_payload({}) or {}
    except Exception:
        payload = {}

    account_plan = payload.get("account_plan") if isinstance(payload, dict) else None
    runtimes_bm = payload.get("runtimes") or {} if isinstance(payload, dict) else {}

    total_tokens = sum(int(m.get("tokens") or 0) for m in (model_billing or []))
    covered_tokens = sum(
        int(m.get("tokens") or 0)
        for m in (model_billing or [])
        if not m.get("apiKeyConfigured")
    )
    any_sub_now = any((rt or {}).get("mode") == "subscription" for rt in runtimes_bm.values())
    any_metered_now = any((rt or {}).get("mode") == "metered" for rt in runtimes_bm.values())
    if total_tokens > 0:
        ratio = covered_tokens / total_tokens
    elif (fallback_all_covered_when_no_models or (any_sub_now and not any_metered_now)) and any_sub_now:
        # No per-model token activity yet, but we've detected a subscription
        # and no metered runtime — treat as fully covered so the "you're
        # covered by <plan>" banner still paints on a quiet day/fresh install.
        ratio = 1.0
    else:
        ratio = 0.0

    def _split(total):
        t = float(total or 0.0)
        c = round(t * ratio, 6)
        return {
            "covered_usd": c,
            "out_of_pocket_usd": round(max(0.0, t - c), 6),
        }

    any_sub = any((rt or {}).get("mode") == "subscription" for rt in runtimes_bm.values())
    any_metered = any((rt or {}).get("mode") == "metered" for rt in runtimes_bm.values())
    sub_labels = [
        (rt or {}).get("label")
        for rt in runtimes_bm.values()
        if (rt or {}).get("mode") == "subscription" and (rt or {}).get("label")
    ]
    metered_labels = [
        (rt or {}).get("label")
        for rt in runtimes_bm.values()
        if (rt or {}).get("mode") == "metered" and (rt or {}).get("label")
    ]

    return {
        "detected": bool(account_plan) or any_sub,
        "account_plan": account_plan,
        "runtimes": runtimes_bm,
        "subscription_labels": sub_labels,
        "metered_labels": metered_labels,
        "any_subscription": any_sub,
        "any_metered": any_metered,
        # True when we're confident every dollar shown is covered by a
        # subscription (no metered runtime detected AND every model with
        # token usage looks OAuth/included).
        "all_covered": bool(any_sub) and not any_metered and ratio > 0.999,
        "covered_token_share": round(ratio, 4),
        "today": _split(today_cost),
        "week": _split(week_cost),
        "month": _split(month_cost),
    }


# ── Enhanced Cost Tracking Utilities ─────────────────────────────────────


def _get_model_pricing():
    """Model-specific pricing per 1M tokens (input, output)."""
    return {
        "claude-opus": (15.0, 75.0),  # Claude 3 Opus
        "claude-sonnet": (3.0, 15.0),  # Claude 3 Sonnet
        "claude-haiku": (0.25, 1.25),  # Claude 3 Haiku
        "gpt-4": (10.0, 30.0),  # GPT-4 Turbo
        "gpt-3.5": (1.0, 2.0),  # GPT-3.5 Turbo
        "default": (15.0, 45.0),  # Conservative estimate
    }


def _calculate_enhanced_costs(daily_tokens, today_str, week_start, month_start):
    """Enhanced cost calculation with model-specific pricing."""
    pricing = _get_model_pricing()

    # For log parsing fallback, assume 60/40 input/output ratio
    input_ratio, output_ratio = 0.6, 0.4

    def calc_cost(tokens, model_key="default"):
        if tokens == 0:
            return 0.0
        in_price, out_price = pricing.get(model_key, pricing["default"])
        input_cost = (tokens * input_ratio) * (in_price / 1_000_000)
        output_cost = (tokens * output_ratio) * (out_price / 1_000_000)
        return input_cost + output_cost

    today_tok = daily_tokens.get(today_str, 0)
    week_tok = sum(v for k, v in daily_tokens.items() if k >= week_start)
    month_tok = sum(v for k, v in daily_tokens.items() if k >= month_start)

    return (
        round(calc_cost(today_tok), 4),
        round(calc_cost(week_tok), 4),
        round(calc_cost(month_tok), 4),
    )


def _analyze_usage_trends(daily_tokens):
    """Analyze usage trends for predictions."""
    if len(daily_tokens) < 3:
        return {"prediction": None, "trend": "insufficient_data"}

    # Get last 7 days of data
    recent_days = sorted(daily_tokens.items())[-7:]
    if len(recent_days) < 3:
        return {"prediction": None, "trend": "insufficient_data"}

    tokens_series = [v for k, v in recent_days]

    # Simple trend analysis
    if len(tokens_series) >= 3:
        recent_avg = sum(tokens_series[-3:]) / 3
        older_avg = (
            sum(tokens_series[:-3]) / max(1, len(tokens_series) - 3)
            if len(tokens_series) > 3
            else recent_avg
        )

        if recent_avg > older_avg * 1.2:
            trend = "increasing"
        elif recent_avg < older_avg * 0.8:
            trend = "decreasing"
        else:
            trend = "stable"

        # Monthly prediction based on recent average
        daily_avg = sum(tokens_series[-7:]) / len(tokens_series[-7:])
        monthly_prediction = daily_avg * 30

        return {
            "trend": trend,
            "dailyAvg": int(daily_avg),
            "monthlyPrediction": int(monthly_prediction),
        }

    return {"prediction": None, "trend": "stable"}


def _generate_cost_warnings(
    today_cost,
    week_cost,
    month_cost,
    trend_data,
    month_tokens=0,
    billing_summary="unknown",
):
    """Generate cost warnings based on thresholds."""
    warnings = []

    # Daily cost warnings
    if today_cost > 10.0:
        warnings.append(
            {
                "type": "high_daily_cost",
                "level": "error",
                "message": f"High daily cost: ${today_cost:.2f} (threshold: $10)",
            }
        )
    elif today_cost > 5.0:
        warnings.append(
            {
                "type": "elevated_daily_cost",
                "level": "warning",
                "message": f"Elevated daily cost: ${today_cost:.2f}",
            }
        )

    # Weekly cost warnings
    if week_cost > 50.0:
        warnings.append(
            {
                "type": "high_weekly_cost",
                "level": "error",
                "message": f"High weekly cost: ${week_cost:.2f} (threshold: $50)",
            }
        )
    elif week_cost > 25.0:
        warnings.append(
            {
                "type": "elevated_weekly_cost",
                "level": "warning",
                "message": f"Elevated weekly cost: ${week_cost:.2f}",
            }
        )

    # Monthly cost warnings
    if month_cost > 200.0:
        warnings.append(
            {
                "type": "high_monthly_cost",
                "level": "error",
                "message": f"High monthly cost: ${month_cost:.2f} (threshold: $200)",
            }
        )
    elif month_cost > 100.0:
        warnings.append(
            {
                "type": "elevated_monthly_cost",
                "level": "warning",
                "message": f"Elevated monthly cost: ${month_cost:.2f}",
            }
        )

    # Trend-based warnings (use observed effective rate, not hard-coded $/token)
    if (
        trend_data.get("trend") == "increasing"
        and trend_data.get("monthlyPrediction", 0) > 300
    ):
        # If likely OAuth/included, avoid scary projected billing alerts.
        if billing_summary != "likely_oauth_or_included":
            projected_cost = 0.0
            if month_tokens and month_cost > 0:
                effective_cost_per_token = month_cost / float(month_tokens)
                projected_cost = (
                    trend_data.get("monthlyPrediction", 0) * effective_cost_per_token
                )

            if projected_cost > 0:
                warnings.append(
                    {
                        "type": "trend_warning",
                        "level": "warning",
                        "message": f"Usage trending up - projected monthly equivalent (if billed): ${projected_cost:.2f}",
                    }
                )

    return warnings


# ── Usage cache ─────────────────────────────────────────────────────────
_usage_cache = {"data": None, "ts": 0}
_USAGE_CACHE_TTL = 60  # seconds
_sessions_cache = {"data": None, "ts": 0}
_SESSIONS_CACHE_TTL = 10  # seconds


_transcript_analytics_cache = {"data": None, "ts": 0}
_TRANSCRIPT_ANALYTICS_TTL = 60  # seconds


def _get_sessions_dir():
    base = SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
    if os.path.isdir(base):
        return base
    fallback = os.path.expanduser("~/.moltbot/agents/main/sessions")
    return fallback if os.path.isdir(fallback) else base


def _parse_event_timestamp(ts_val, fallback_ts=None):
    if ts_val is None:
        return fallback_ts
    try:
        if isinstance(ts_val, (int, float)):
            return datetime.fromtimestamp(ts_val / 1000 if ts_val > 1e12 else ts_val)
        if isinstance(ts_val, str):
            return datetime.fromisoformat(ts_val.replace("Z", "+00:00"))
    except Exception:
        pass
    return fallback_ts


def _extract_usage_metrics(obj):
    """Best-effort usage extraction from mixed transcript schemas."""
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
    usage = message.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("usage")
    if not isinstance(usage, dict):
        usage = obj.get("tokens_used")
    if not isinstance(usage, dict):
        return {
            "tokens": 0, "cost": 0.0,
            "input_tokens": 0, "output_tokens": 0,
            "cache_read_tokens": 0, "cache_write_tokens": 0,
            "input_cost": 0.0, "output_cost": 0.0,
            "cache_read_cost": 0.0, "cache_write_cost": 0.0,
        }

    in_toks = usage.get("input", usage.get("input_tokens", 0)) or 0
    out_toks = usage.get("output", usage.get("output_tokens", 0)) or 0
    cache_read = usage.get("cacheRead", usage.get("cache_read_tokens", 0)) or 0
    cache_write = usage.get("cacheWrite", usage.get("cache_write_tokens", 0)) or 0
    total = usage.get("totalTokens", usage.get("total_tokens", 0)) or 0
    if not total:
        total = in_toks + out_toks + cache_read + cache_write

    cost = 0.0
    cost_input = 0.0
    cost_output = 0.0
    cost_cache_read = 0.0
    cost_cache_write = 0.0
    cost_data = usage.get("cost", {})
    if isinstance(cost_data, dict):
        raw = cost_data.get("total", cost_data.get("usd", 0))
        try:
            cost = float(raw or 0)
        except Exception:
            cost = 0.0
        # Extract granular cost breakdown if available
        cost_input = float(cost_data.get("input", 0) or 0)
        cost_output = float(cost_data.get("output", 0) or 0)
        cost_cache_read = float(cost_data.get("cacheRead", 0) or 0)
        cost_cache_write = float(cost_data.get("cacheWrite", 0) or 0)
    elif isinstance(cost_data, (int, float)):
        cost = float(cost_data)

    return {
        "tokens": int(total or 0),
        "cost": float(cost or 0.0),
        "input_tokens": int(in_toks or 0),
        "output_tokens": int(out_toks or 0),
        "cache_read_tokens": int(cache_read or 0),
        "cache_write_tokens": int(cache_write or 0),
        "input_cost": float(cost_input),
        "output_cost": float(cost_output),
        "cache_read_cost": float(cost_cache_read),
        "cache_write_cost": float(cost_cache_write),
    }


def _normalize_plugin_name(tool_name):
    name = str(tool_name or "").strip().lower()
    if not name:
        return ""
    for sep in ("/", ":", "."):
        if sep in name:
            name = name.split(sep, 1)[0]
            break
    return name[:64]


def _extract_tool_plugins(obj):
    """Extract plugin/tool names from known tool call locations."""
    plugins = []
    message = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}

    # Newer format: message.content[{type:'toolCall', name:'...'}]
    for part in message.get("content") or []:
        if not isinstance(part, dict):
            continue
        if part.get("type") == "toolCall":
            p = _normalize_plugin_name(part.get("name", ""))
            if p:
                plugins.append(p)

    # OpenAI-like tool call array
    for tc in obj.get("tool_calls") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(
            tc.get("name") or (tc.get("function") or {}).get("name", "")
        )
        if p:
            plugins.append(p)

    # Alternate key
    for tc in obj.get("tool_use") or []:
        if not isinstance(tc, dict):
            continue
        p = _normalize_plugin_name(tc.get("name", ""))
        if p:
            plugins.append(p)

    return plugins


def _collect_cron_refs(obj, out_refs):
    """Recursively collect explicit cron/job IDs from transcript event objects."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in (
                "cronid",
                "cron_id",
                "cronjobid",
                "cron_job_id",
                "jobid",
                "job_id",
                "scheduleid",
                "schedule_id",
            ):
                if isinstance(v, (str, int, float)):
                    sv = str(v).strip().lower()
                    if sv:
                        out_refs.add(sv)
            _collect_cron_refs(v, out_refs)
    elif isinstance(obj, list):
        for it in obj:
            _collect_cron_refs(it, out_refs)


def _score_cron_match(session, job):
    """Heuristic score for mapping a session to a cron job."""
    refs = session.get("explicit_cron_refs", set())
    text = session.get("search_text", "")
    score = 0

    jid = str(job.get("id", "")).strip().lower()
    jname = str(job.get("name", job.get("label", ""))).strip().lower()

    if jid and jid in refs:
        score += 100
    if jname and jname in refs:
        score += 80
    if jid and jid in text:
        score += 30
    if jname and len(jname) >= 4 and jname in text:
        score += 20

    payload = job.get("payload") or job.get("config") or {}
    if isinstance(payload, dict):
        prompt = (
            str(
                payload.get("prompt")
                or payload.get("text")
                or payload.get("message")
                or ""
            )
            .strip()
            .lower()
        )
        if prompt:
            for w in [w for w in _re.split(r"[^a-z0-9_]+", prompt) if len(w) >= 5][:8]:
                if w in text:
                    score += 1
    return score


def _compute_transcript_analytics():
    """Parse transcript files once for usage, anomalies, cron attribution, and plugin breakdown."""
    now = time.time()
    if (
        _transcript_analytics_cache["data"] is not None
        and (now - _transcript_analytics_cache["ts"]) < _TRANSCRIPT_ANALYTICS_TTL
    ):
        return _transcript_analytics_cache["data"]

    sessions_dir = _get_sessions_dir()
    summaries = []
    plugin_stats = defaultdict(lambda: {"tokens": 0.0, "cost": 0.0, "calls": 0})
    plugin_daily_stats: dict = {}  # day -> plugin -> {tokens, cost, calls} (GH#201 trend)
    daily_tokens = {}
    daily_cost = {}
    model_usage = {}

    if os.path.isdir(sessions_dir):
        for fname in os.listdir(sessions_dir):
            # Accept both live `.jsonl` and archived `.jsonl.reset.<ts>` files.
            # Reset archives carry real historical token usage from earlier
            # days; skipping them was making the 14-day chart pile every
            # past-day total onto today.
            if not (fname.endswith(".jsonl") or ".jsonl.reset." in fname):
                continue
            # Runtime trajectory/checkpoint files duplicate session content and
            # can dwarf real transcripts (hundreds of MB). They make usage
            # widgets crawl on first load, so keep analytics on canonical
            # session/reset transcripts only.
            if ".trajectory." in fname or ".checkpoint." in fname or ".deleted." in fname:
                continue
            sid = fname.split(".jsonl", 1)[0]
            fpath = os.path.join(sessions_dir, fname)
            fallback_dt = datetime.fromtimestamp(os.path.getmtime(fpath))

            s_tokens = 0
            s_cost = 0.0
            s_model = "unknown"
            s_start = None
            s_end = None
            search_parts = []
            explicit_cron_refs = set()

            try:
                with open(fpath, "r") as f:
                    for line in f:
                        try:
                            obj = json.loads(line.strip())
                        except Exception:
                            continue

                        ts = _parse_event_timestamp(
                            obj.get("timestamp")
                            or obj.get("time")
                            or obj.get("created_at"),
                            fallback_dt,
                        )
                        if ts:
                            if s_start is None or ts < s_start:
                                s_start = ts
                            if s_end is None or ts > s_end:
                                s_end = ts

                        # Collect cron hints from metadata and known custom session-info events
                        _collect_cron_refs(obj, explicit_cron_refs)
                        if obj.get("customType") == "openclaw.session-info":
                            search_parts.append(
                                json.dumps(obj.get("data", {}), default=str).lower()
                            )

                        message = (
                            obj.get("message", {})
                            if isinstance(obj.get("message"), dict)
                            else {}
                        )
                        model = message.get("model") or obj.get("model")
                        if model:
                            s_model = model

                        usage_metrics = _extract_usage_metrics(obj)
                        tokens = usage_metrics["tokens"]
                        cost = usage_metrics["cost"]

                        if tokens > 0:
                            s_tokens += tokens
                            if cost > 0:
                                s_cost += cost

                            # Bucket to this event's actual date, not the
                            # session start date. Fixes the bug where a
                            # long-running session's entire token total
                            # piled onto the day the session started.
                            _ev_date = (ts or fallback_dt).strftime("%Y-%m-%d")
                            daily_tokens[_ev_date] = daily_tokens.get(_ev_date, 0) + tokens
                            daily_cost[_ev_date] = daily_cost.get(_ev_date, 0.0) + cost

                            plugins = _extract_tool_plugins(obj)
                            if plugins:
                                share_tokens = float(tokens) / float(len(plugins))
                                share_cost = (
                                    float(cost) / float(len(plugins))
                                    if cost > 0
                                    else 0.0
                                )
                                # Track daily breakdown for trend analysis (GH#201)
                                # use the event's actual day so trend lines
                                # match the headline 14-day chart.
                                _ev_day = (ts or fallback_dt).strftime("%Y-%m-%d")
                                for p in plugins:
                                    plugin_stats[p]["tokens"] += share_tokens
                                    plugin_stats[p]["cost"] += share_cost
                                    plugin_stats[p]["calls"] += 1
                                    if _ev_day not in plugin_daily_stats:
                                        plugin_daily_stats[_ev_day] = {}
                                    if p not in plugin_daily_stats[_ev_day]:
                                        plugin_daily_stats[_ev_day][p] = {"tokens": 0.0, "cost": 0.0, "calls": 0}
                                    plugin_daily_stats[_ev_day][p]["tokens"] += share_tokens
                                    plugin_daily_stats[_ev_day][p]["cost"] += share_cost
                                    plugin_daily_stats[_ev_day][p]["calls"] += 1

                        # Textual hints for cron matching
                        if isinstance(message.get("content"), list):
                            for part in message.get("content", []):
                                if isinstance(part, dict):
                                    txt = part.get("text")
                                    if isinstance(txt, str) and txt:
                                        search_parts.append(txt.lower())
                        if obj.get("type") == "custom":
                            try:
                                search_parts.append(
                                    json.dumps(obj, default=str).lower()
                                )
                            except Exception:
                                pass

                if s_start is None:
                    s_start = fallback_dt
                if s_end is None:
                    s_end = fallback_dt

                # daily_tokens/daily_cost are now populated per-event above
                # (bucketed by each event's timestamp, not the session start).
                # Only model_usage still aggregates per-session.
                model_usage[s_model] = model_usage.get(s_model, 0) + s_tokens

                search_text = " ".join(search_parts)
                if len(search_text) > 12000:
                    search_text = search_text[:12000]

                summaries.append(
                    {
                        "session_id": sid,
                        "tokens": s_tokens,
                        "cost_usd": s_cost,
                        "model": s_model,
                        "start_ts": s_start.timestamp() if s_start else 0,
                        "end_ts": s_end.timestamp() if s_end else 0,
                        "day": s_start.strftime("%Y-%m-%d") if s_start else fallback_dt.strftime("%Y-%m-%d"),
                        "search_text": search_text,
                        "explicit_cron_refs": explicit_cron_refs,
                        "is_cron_candidate": ("cron" in search_text)
                        or bool(explicit_cron_refs),
                    }
                )
            except Exception:
                continue

    summaries.sort(key=lambda s: s.get("start_ts", 0))
    result = {
        "sessions": summaries,
        "plugin_stats": plugin_stats,
        "plugin_daily_stats": plugin_daily_stats,
        "daily_tokens": daily_tokens,
        "daily_cost": daily_cost,
        "model_usage": model_usage,
    }
    _transcript_analytics_cache["data"] = result
    _transcript_analytics_cache["ts"] = now
    return result


def _compute_session_cost_anomalies(session_summaries):
    """Flag sessions with cost >2x their rolling 7-day session-cost average."""
    now_ts = time.time()
    day_ago = now_ts - 86400
    anomalies = []

    for i, sess in enumerate(session_summaries):
        ts = sess.get("start_ts", 0) or 0
        if ts < day_ago:
            continue
        cost = float(sess.get("cost_usd", 0.0) or 0.0)
        if cost <= 0:
            continue

        window_start = ts - (7 * 86400)
        window_costs = []
        for prev in session_summaries[:i]:
            pts = prev.get("start_ts", 0) or 0
            pc = float(prev.get("cost_usd", 0.0) or 0.0)
            if pts >= window_start and pts < ts and pc > 0:
                window_costs.append(pc)

        if not window_costs:
            continue
        avg = sum(window_costs) / float(len(window_costs))
        if avg <= 0:
            continue
        if cost > (2.0 * avg):
            anomalies.append(
                {
                    "session_id": sess.get("session_id"),
                    "cost_usd": round(cost, 6),
                    "rolling_avg_usd": round(avg, 6),
                    "ratio": round(cost / avg, 3),
                    "timestamp": int(ts * 1000),
                }
            )

    anomalies.sort(key=lambda a: a.get("ratio", 0), reverse=True)
    return anomalies


# ── New Feature APIs ────────────────────────────────────────────────────


# (bp_usage routes moved to routes/usage.py)


# ─────────────────────────────────────────────────────────────────────────────
# Anomaly Detection Engine (GH #301)
# Rolling-baseline anomaly detector using local SQLite storage.
# Detects cost spikes (>2x), token spikes (>2x), error rate spikes (>3x)
# against a 7-day rolling baseline derived from session transcripts.
# ─────────────────────────────────────────────────────────────────────────────

_ANOMALY_DB_PATH = os.path.expanduser("~/.openclaw/clawmetry.db")
_anomaly_db_conn = None
_anomaly_db_lock = threading.Lock()


def _get_anomaly_db():
    """Return a thread-safe SQLite connection for anomaly storage.

    Uses ~/.openclaw/clawmetry.db (creates if absent). The schema is
    append-only so it is safe to call from any thread with the lock held.
    """
    global _anomaly_db_conn
    with _anomaly_db_lock:
        if _anomaly_db_conn is None:
            db_dir = os.path.dirname(_ANOMALY_DB_PATH)
            os.makedirs(db_dir, exist_ok=True)
            _anomaly_db_conn = sqlite3.connect(
                _ANOMALY_DB_PATH, check_same_thread=False
            )
            _anomaly_db_conn.row_factory = sqlite3.Row
            _anomaly_db_conn.execute("PRAGMA journal_mode=WAL")
            _anomaly_db_conn.execute("PRAGMA synchronous=NORMAL")
            _anomaly_db_conn.executescript("""
                CREATE TABLE IF NOT EXISTS anomalies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    detected_at REAL NOT NULL,
                    session_key TEXT NOT NULL,
                    metric TEXT NOT NULL,
                    value REAL NOT NULL,
                    baseline REAL NOT NULL,
                    ratio REAL NOT NULL,
                    severity TEXT NOT NULL,
                    acknowledged INTEGER DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_anomalies_ts ON anomalies(detected_at);
                CREATE INDEX IF NOT EXISTS idx_anomalies_session ON anomalies(session_key);
                CREATE INDEX IF NOT EXISTS idx_anomalies_metric ON anomalies(metric);
            """)
            _anomaly_db_conn.commit()
        return _anomaly_db_conn


def _fire_token_spike_alerts(new_anomalies):
    """Fire configured token_spike alert rules for freshly inserted anomalies.

    Called from _detect_and_store_anomalies() with only the anomalies that
    were actually new (not deduped-out re-detections).  Matches each token_spike
    anomaly against enabled token_spike rules; fires _fire_alert() when the
    anomaly ratio meets or exceeds the rule's threshold multiplier.
    """
    if not new_anomalies:
        return
    token_spikes = [a for a in new_anomalies if a.get("metric") == "token_spike"]
    if not token_spikes:
        return
    rules = [
        r for r in _get_alert_rules()
        if r.get("type") == "token_spike" and r.get("enabled")
    ]
    if not rules:
        return
    for anomaly in token_spikes:
        ratio = float(anomaly.get("ratio", 0.0))
        session_key = str(anomaly.get("session_key", "unknown"))
        value = int(anomaly.get("value", 0))
        baseline = float(anomaly.get("baseline", 0.0))
        severity = str(anomaly.get("severity", "warning"))
        for rule in rules:
            threshold = float(rule.get("threshold", 2.0))
            if ratio < threshold:
                continue
            rule_id = rule.get("id", "")
            cooldown_key = f"token_spike_{rule_id}_{session_key}"
            try:
                channels = json.loads(rule.get("channels") or '["banner"]')
            except Exception:
                channels = ["banner"]
            msg = (
                f"Token spike: session {session_key} used {value:,} tokens "
                f"({ratio:.1f}× the {baseline:.0f}-token baseline)"
            )
            _fire_alert(cooldown_key, "token_spike", msg, channels, severity)


def _detect_and_store_anomalies():
    """Compute rolling-baseline anomalies and persist new ones to SQLite.

    Runs on every call to /api/anomalies (with a short in-memory TTL to
    avoid re-scanning transcripts too frequently).

    Detects:
    - cost_spike:        session cost > 2x 7-day rolling average
    - token_spike:       session tokens > 2x 7-day rolling average
    - error_rate_spike:  rolling 24h error rate > 3x 7-day baseline

    Returns list of anomaly dicts (both freshly detected and stored).
    """

    analytics = _compute_transcript_analytics()
    sessions = analytics.get("sessions", [])
    now_ts = time.time()
    window_7d = 7 * 86400
    window_24h = 86400

    # ── Build 7-day baseline ──────────────────────────────────────────────────
    baseline_window_start = now_ts - window_7d
    baseline_sessions = [
        s for s in sessions if float(s.get("start_ts", 0) or 0) >= baseline_window_start
    ]

    baseline_costs = [
        float(s.get("cost_usd", 0.0) or 0.0)
        for s in baseline_sessions
        if float(s.get("cost_usd", 0.0) or 0.0) > 0
    ]
    baseline_tokens = [
        int(s.get("tokens", 0) or 0)
        for s in baseline_sessions
        if int(s.get("tokens", 0) or 0) > 0
    ]

    avg_cost_7d = sum(baseline_costs) / len(baseline_costs) if baseline_costs else 0.0
    avg_tokens_7d = (
        sum(baseline_tokens) / len(baseline_tokens) if baseline_tokens else 0.0
    )

    # Error-rate baseline: fraction of sessions in last 7d with errors
    # (We approximate via cost=0 + tokens>0 as proxy for "errored" sessions.)
    err_baseline_count = sum(
        1
        for s in baseline_sessions
        if float(s.get("cost_usd", 0.0) or 0.0) == 0
        and int(s.get("tokens", 0) or 0) > 100
    )
    err_baseline_rate = err_baseline_count / max(len(baseline_sessions), 1)

    # 24h error rate
    recent_sessions_24h = [
        s for s in sessions if float(s.get("start_ts", 0) or 0) >= now_ts - window_24h
    ]
    recent_err_count = sum(
        1
        for s in recent_sessions_24h
        if float(s.get("cost_usd", 0.0) or 0.0) == 0
        and int(s.get("tokens", 0) or 0) > 100
    )
    recent_err_rate = recent_err_count / max(len(recent_sessions_24h), 1)

    # ── Detect anomalies in recent (last 24h) sessions ─────────────────────
    new_anomalies = []
    day_ago = now_ts - window_24h

    for sess in sessions:
        ts = float(sess.get("start_ts", 0) or 0)
        if ts < day_ago:
            continue
        sid = sess.get("session_id", "")
        cost = float(sess.get("cost_usd", 0.0) or 0.0)
        tokens = int(sess.get("tokens", 0) or 0)

        # Cost spike
        if avg_cost_7d > 0 and cost > avg_cost_7d * 2.0:
            ratio = round(cost / avg_cost_7d, 3)
            severity = "critical" if ratio > 5 else "high" if ratio > 3 else "medium"
            new_anomalies.append(
                {
                    "session_key": sid,
                    "metric": "cost_spike",
                    "value": cost,
                    "baseline": avg_cost_7d,
                    "ratio": ratio,
                    "severity": severity,
                    "detected_at": ts,
                }
            )

        # Token spike
        if avg_tokens_7d > 0 and tokens > avg_tokens_7d * 2.0:
            ratio = round(tokens / avg_tokens_7d, 3)
            severity = "critical" if ratio > 5 else "high" if ratio > 3 else "medium"
            new_anomalies.append(
                {
                    "session_key": sid,
                    "metric": "token_spike",
                    "value": tokens,
                    "baseline": avg_tokens_7d,
                    "ratio": ratio,
                    "severity": severity,
                    "detected_at": ts,
                }
            )

    # Error rate spike (aggregate — tied to a synthetic session_key)
    if err_baseline_rate > 0 and recent_err_rate > err_baseline_rate * 3.0:
        ratio = round(recent_err_rate / err_baseline_rate, 3)
        new_anomalies.append(
            {
                "session_key": "__error_rate__",
                "metric": "error_rate_spike",
                "value": round(recent_err_rate, 4),
                "baseline": round(err_baseline_rate, 4),
                "ratio": ratio,
                "severity": "high" if ratio > 5 else "medium",
                "detected_at": now_ts,
            }
        )

    # Session frequency spike: compare 24h session count vs 7-day daily average
    if len(baseline_sessions) > 0:
        days_in_window = max((now_ts - baseline_window_start) / 86400, 1.0)
        avg_sessions_per_day = len(baseline_sessions) / days_in_window
        sessions_last_24h = len(recent_sessions_24h)
        if avg_sessions_per_day >= 2 and sessions_last_24h > avg_sessions_per_day * 2.5:
            freq_ratio = round(sessions_last_24h / avg_sessions_per_day, 3)
            new_anomalies.append(
                {
                    "session_key": "__session_frequency__",
                    "metric": "session_frequency_spike",
                    "value": sessions_last_24h,
                    "baseline": round(avg_sessions_per_day, 2),
                    "ratio": freq_ratio,
                    "severity": "high" if freq_ratio > 4 else "medium",
                    "detected_at": now_ts,
                }
            )

    # ── Persist new anomalies (deduplicate by session_key + metric within 24h) ──
    truly_new_anomalies = []
    try:
        db = _get_anomaly_db()
        with _anomaly_db_lock:
            for a in new_anomalies:
                existing = db.execute(
                    "SELECT id FROM anomalies WHERE session_key = ? AND metric = ? AND detected_at >= ?",
                    (a["session_key"], a["metric"], a["detected_at"] - window_24h),
                ).fetchone()
                if not existing:
                    db.execute(
                        "INSERT INTO anomalies (detected_at, session_key, metric, value, baseline, ratio, severity) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (
                            a["detected_at"],
                            a["session_key"],
                            a["metric"],
                            a["value"],
                            a["baseline"],
                            a["ratio"],
                            a["severity"],
                        ),
                    )
                    truly_new_anomalies.append(a)
            db.commit()
    except Exception as _e:
        pass  # Non-critical — continue with in-memory results

    _fire_token_spike_alerts(truly_new_anomalies)

    # ── Return stored anomalies from last 48h ──────────────────────────────
    try:
        db = _get_anomaly_db()
        cutoff = now_ts - (2 * window_24h)
        rows = db.execute(
            "SELECT * FROM anomalies WHERE detected_at >= ? ORDER BY detected_at DESC LIMIT 200",
            (cutoff,),
        ).fetchall()
        stored = [dict(r) for r in rows]
    except Exception:
        stored = []

    # Compute session frequency baseline for return value
    _days_in_window = max((now_ts - baseline_window_start) / 86400, 1.0)
    _avg_sessions_per_day = (
        len(baseline_sessions) / _days_in_window if len(baseline_sessions) > 0 else 0.0
    )

    return stored, {
        "baseline_cost_7d": round(avg_cost_7d, 6),
        "baseline_tokens_7d": round(avg_tokens_7d, 2),
        "baseline_error_rate_7d": round(err_baseline_rate, 4),
        "recent_error_rate_24h": round(recent_err_rate, 4),
        "baseline_sessions_per_day_7d": round(_avg_sessions_per_day, 2),
        "sessions_last_24h": len(recent_sessions_24h),
        "session_count_7d": len(baseline_sessions),
    }


_anomaly_detection_cache = {"data": None, "ts": 0}
_ANOMALY_CACHE_TTL = 60  # seconds

import sqlite3


def _compute_plugin_trend(plugin_name, plugin_daily_stats, days=14):
    """Return trend direction for a plugin: 'increasing', 'decreasing', or 'stable'.

    Compares average daily cost share of the last 7 days vs the prior 7 days.
    Closes vivekchand/clawmetry#201 (trend over time).
    """
    from datetime import date, timedelta
    today = date.today()
    recent_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 8)]
    prior_days = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(8, 15)]

    def _avg_share(day_list):
        shares = []
        for d in day_list:
            day_data = plugin_daily_stats.get(d, {})
            day_total = sum(v.get("tokens", 0.0) for v in day_data.values()) or 1.0
            p_toks = day_data.get(plugin_name, {}).get("tokens", 0.0)
            if p_toks > 0:
                shares.append(p_toks / day_total * 100.0)
        return sum(shares) / len(shares) if shares else 0.0

    recent_avg = _avg_share(recent_days)
    prior_avg = _avg_share(prior_days)

    if prior_avg < 0.5:
        return "stable"
    delta_pct = (recent_avg - prior_avg) / prior_avg * 100.0
    if delta_pct > 20:
        return "increasing"
    if delta_pct < -20:
        return "decreasing"
    return "stable"


def _build_cost_comparison():
    """Build cost comparison data: actual spend vs alternative models."""
    # Alternative model pricing: (input $/1M, output $/1M, display name, provider)
    ALTERNATIVES = [
        ("gemini-2.0-flash",   0.10,  0.40,  "Gemini 2.0 Flash",     "Google"),
        ("gemini-1.5-flash",   0.075, 0.30,  "Gemini 1.5 Flash",     "Google"),
        ("gpt-4o-mini",        0.15,  0.60,  "GPT-4o Mini",          "OpenAI"),
        ("claude-haiku-3.5",   0.80,  4.00,  "Claude Haiku 3.5",     "Anthropic"),
        ("qwen-plus",          0.40,  1.20,  "Qwen Plus",            "Alibaba"),
        ("claude-sonnet-3.5",  3.00, 15.00,  "Claude Sonnet 3.5",    "Anthropic"),
        ("claude-opus-4",     15.00, 75.00,  "Claude Opus 4",        "Anthropic"),
    ]
    INPUT_RATIO = 0.60  # estimated 60% input, 40% output
    OUTPUT_RATIO = 0.40

    # Collect actual month tokens and cost from metrics store
    from datetime import datetime as _dt
    month_start = time.time() - 30 * 86400
    actual_tokens = 0
    actual_cost = 0.0
    actual_model = "unknown"
    model_token_map = {}  # model -> tokens

    with _metrics_lock:
        for entry in metrics_store.get("tokens", []):
            if entry.get("timestamp", 0) >= month_start:
                tok = float(entry.get("total", 0) or 0)
                actual_tokens += tok
                m = entry.get("model", "")
                if m:
                    model_token_map[m] = model_token_map.get(m, 0) + tok
        for entry in metrics_store.get("cost", []):
            if entry.get("timestamp", 0) >= month_start:
                actual_cost += float(entry.get("usd", 0) or 0)

    # If no cost data, estimate from tokens using current model pricing
    if actual_tokens > 0 and actual_cost == 0.0:
        usd_per_tok = _estimate_usd_per_token()
        actual_cost = actual_tokens * usd_per_tok

    # Determine dominant model
    if model_token_map:
        actual_model = max(model_token_map, key=lambda k: model_token_map[k])

    # Compute alternative costs for same token volume
    alternatives = []
    for alt_id, in_price, out_price, display_name, provider in ALTERNATIVES:
        if actual_tokens == 0:
            alt_cost = 0.0
        else:
            alt_cost = (
                actual_tokens * INPUT_RATIO * (in_price / 1_000_000)
                + actual_tokens * OUTPUT_RATIO * (out_price / 1_000_000)
            )
        if actual_cost > 0:
            savings_pct = round((actual_cost - alt_cost) / actual_cost * 100, 1)
            savings_usd = round(actual_cost - alt_cost, 4)
        else:
            savings_pct = 0.0
            savings_usd = 0.0
        alternatives.append({
            "model_id": alt_id,
            "display_name": display_name,
            "provider": provider,
            "estimated_cost": round(alt_cost, 4),
            "savings_usd": savings_usd,
            "savings_pct": savings_pct,
        })

    # Sort by estimated cost ascending
    alternatives.sort(key=lambda x: x["estimated_cost"])

    return {
        "actual": {
            "model": actual_model,
            "tokens": actual_tokens,
            "cost_usd": round(actual_cost, 4),
        },
        "alternatives": alternatives,
        "period": "30d",
    }


def _summarize_tool_input(name, inp):
    """Create a human-readable one-line summary of a tool call."""
    if name == "exec":
        return (inp.get("command") or str(inp))[:150]
    elif name in ("Read", "read"):
        return f"📖 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ("Write", "write"):
        return f"✏️ {inp.get('file_path') or inp.get('path') or '?'}"
    elif name in ("Edit", "edit"):
        return f"🔧 {inp.get('file_path') or inp.get('path') or '?'}"
    elif name == "web_search":
        return f"[check] {inp.get('query', '?')}"
    elif name == "web_fetch":
        return f"🌐 {inp.get('url', '?')[:80]}"
    elif name == "browser":
        return f"🖥️ {inp.get('action', '?')}"
    elif name == "message":
        return f"💬 {inp.get('action', '?')} -> {inp.get('message', '')[:60]}"
    elif name == "tts":
        return f"🔊 {inp.get('text', '')[:60]}"
    else:
        return str(inp)[:120]


def _generic_channel_data(channel_key):
    """Generic channel data fetcher: scans session transcripts for channel metadata."""

    limit = request.args.get("limit", 50, type=int)
    today = datetime.now().strftime("%Y-%m-%d")

    messages = []
    today_in = 0
    today_out = 0

    # Scan log files for channel events
    log_dirs = _get_log_dirs()
    for ld in log_dirs:
        if not os.path.isdir(ld):
            continue
        for lf in sorted(glob.glob(os.path.join(ld, "*.log")), reverse=True)[:2]:
            try:
                _grep_lines = _grep_log_file(lf, f"messageChannel={channel_key}")
                for line in _grep_lines:
                    try:
                        obj = json.loads(line.strip())
                    except Exception:
                        continue
                    msg1 = obj.get("1", "") or obj.get("0", "")
                    ts = obj.get("time", "")
                    if f"messageChannel={channel_key}" in msg1:
                        direction = "out" if "deliver" in msg1.lower() else "in"
                        messages.append(
                            {
                                "timestamp": ts,
                                "direction": direction,
                                "sender": "User" if direction == "in" else "Clawd",
                                "text": msg1[:200],
                            }
                        )
                        if today and today in ts:
                            if direction == "in":
                                today_in += 1
                            else:
                                today_out += 1
            except Exception:
                pass

    # Also scan sessions.json for channel-tagged sessions
    for sessions_dir in [
        os.path.expanduser("~/.openclaw/agents/main/sessions"),
        os.path.expanduser("~/.clawdbot/agents/main/sessions"),
    ]:
        sessions_file = os.path.join(sessions_dir, "sessions.json")
        if not os.path.exists(sessions_file):
            continue
        try:
            with open(sessions_file) as f:
                sess_data = json.load(f)
            ch_sessions = [
                (sid, s)
                for sid, s in sess_data.items()
                if channel_key in sid.lower() and "sessionId" in s
            ]
            ch_sessions.sort(key=lambda x: x[1].get("updatedAt", 0), reverse=True)
            for sid_key, sinfo in ch_sessions[:5]:
                uuid = sinfo["sessionId"]
                sf = os.path.join(sessions_dir, uuid + ".jsonl")
                if not os.path.exists(sf):
                    continue
                try:
                    fsize = os.path.getsize(sf)
                    with open(sf, "r", errors="replace") as f:
                        if fsize > 65536:
                            f.seek(fsize - 65536)
                            f.readline()
                        for sline in f:
                            sline = sline.strip()
                            if not sline:
                                continue
                            try:
                                sd = json.loads(sline)
                            except Exception:
                                continue
                            sm = sd.get("message", {})
                            ts = sd.get("timestamp", "")
                            role = sm.get("role", "")
                            if role not in ("user", "assistant"):
                                continue
                            content = sm.get("content", "")
                            txt = ""
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, dict) and c.get("type") == "text":
                                        txt = c.get("text", "")
                                        break
                            elif isinstance(content, str):
                                txt = content
                            if (
                                not txt
                                or txt.startswith("System:")
                                or "HEARTBEAT" in txt
                            ):
                                continue
                            direction = "in" if role == "user" else "out"
                            messages.append(
                                {
                                    "timestamp": ts,
                                    "direction": direction,
                                    "sender": "User" if direction == "in" else "Clawd",
                                    "text": txt[:300],
                                }
                            )
                            if today and today in ts:
                                if direction == "in":
                                    today_in += 1
                                else:
                                    today_out += 1
                except Exception:
                    pass
        except Exception:
            pass

    # Deduplicate and sort
    seen = set()
    unique = []
    for m in messages:
        key = (m["timestamp"], m["direction"], m["text"][:50])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    unique.sort(key=lambda x: x["timestamp"], reverse=True)

    status = "connected" if unique else "configured"
    return jsonify(
        {
            "messages": unique[:limit],
            "total": len(unique),
            "todayIn": today_in,
            "todayOut": today_out,
            "status": status,
        }
    )


# ── Security Threat Detection Engine ─────────────────────────────────────────
import re as _sec_re  # noqa: E402

# Built-in threat signatures: pattern matching on tool call details
_THREAT_SIGNATURES = [
    # Critical: Direct system compromise attempts
    {
        "id": "SEC-001",
        "severity": "critical",
        "description": "Reverse shell attempt via exec",
        "tool_types": ["EXEC"],
        "patterns": [
            r"(?:bash|sh|nc|ncat|netcat)\s.*-[ie]\s",
            r"/dev/tcp/",
            r"mkfifo\s+/tmp/",
            r"\bsocat\b.*\bexec\b",
            r"\btelnet\b.*\|.*\bsh\b",
        ],
    },
    {
        "id": "SEC-002",
        "severity": "critical",
        "description": "Credential/secret file access",
        "tool_types": ["READ", "EXEC"],
        "patterns": [
            r"(?:/etc/shadow|/etc/passwd)",
            r"\.ssh/(?:id_rsa|id_ed25519|authorized_keys)",
            r"\.aws/credentials",
            r"\.env(?:\b|$)",
            r"(?:\.kube|kubeconfig)",
            r"\.gnupg/private",
            r"\.netrc",
        ],
    },
    {
        "id": "SEC-003",
        "severity": "critical",
        "description": "Privilege escalation attempt",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bsudo\s+(?:su|bash|sh|chmod\s+[ugo]*s)",
            r"\bchmod\s+[0-7]*4[0-7]{2}\b",
            r"\bchmod\s+u\+s\b",
            r"\bpkexec\b",
            r"\bsu\s+-\s",
        ],
    },
    # High: Data exfiltration and suspicious network activity
    {
        "id": "SEC-004",
        "severity": "high",
        "description": "Potential data exfiltration via curl/wget POST",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bcurl\b.*\b-[dX]\b.*(?:POST|PUT)",
            r"\bcurl\b.*--data(?:-binary|-raw|-urlencode)?\b",
            r"\bwget\b.*--post-(?:data|file)\b",
        ],
    },
    {
        "id": "SEC-005",
        "severity": "high",
        "description": "SSH/SCP to unknown external host",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bssh\b\s+(?!localhost|127\.0\.0\.1|192\.168\.|10\.|172\.(?:1[6-9]|2[0-9]|3[01]))",
            r"\bscp\b\s+.*:",
            r"\brsync\b.*(?<!localhost):",
        ],
    },
    {
        "id": "SEC-006",
        "severity": "high",
        "description": "Cryptocurrency miner indicators",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bxmrig\b",
            r"\bstratum\+tcp\b",
            r"(?:mine|pool)\..*\.(?:com|net|org)",
            r"\bcpuminer\b",
        ],
    },
    # Medium: Suspicious but potentially legitimate
    {
        "id": "SEC-007",
        "severity": "medium",
        "description": "Destructive file operation (rm -rf on system paths)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\brm\s+(?:-[rfRv]+\s+)*(?:/(?:etc|usr|var|boot|lib|bin|sbin|opt|root)\b|/\s*$)",
            r"\brm\s+-[rfR]+\s+\*",
            r"\bdd\s+.*of=/dev/",
            r"\bmkfs\b",
        ],
    },
    {
        "id": "SEC-008",
        "severity": "medium",
        "description": "Package manager running as agent (supply chain risk)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bpip\s+install\b.*(?:--index-url|--extra-index-url|--trusted-host)",
            r"\bnpm\s+install\b.*(?:--registry|--unsafe-perm)",
            r"\bcurl\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
            r"\bwget\b.*\|\s*(?:sudo\s+)?(?:bash|sh)\b",
        ],
    },
    {
        "id": "SEC-009",
        "severity": "medium",
        "description": "Firewall or security policy modification",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\b(?:ufw|iptables|nftables|firewall-cmd)\b.*(?:allow|disable|delete|flush)",
            r"\bsetenforce\s+0\b",
            r"\bsystemctl\s+(?:stop|disable)\s+(?:firewalld|ufw|apparmor)",
        ],
    },
    {
        "id": "SEC-010",
        "severity": "medium",
        "description": "Cron/systemd persistence mechanism",
        "tool_types": ["EXEC", "WRITE"],
        "patterns": [
            r"\bcrontab\b",
            r"/etc/cron\.",
            r"/etc/systemd/system/.*\.service",
            r"systemctl\s+enable\b",
        ],
    },
    # Low: Informational security events
    {
        "id": "SEC-011",
        "severity": "low",
        "description": "Port scanning or network reconnaissance",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bnmap\b",
            r"\bmasscan\b",
            r"\bnetstat\s+-[tul]*p",
            r"\bss\s+-[tul]*p",
        ],
    },
    {
        "id": "SEC-012",
        "severity": "low",
        "description": "Large file download (potential payload)",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bwget\b\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org|dl\.google\.com)",
            r"\bcurl\b\s+-[oOL]+\s+https?://(?!github\.com|pypi\.org|registry\.npmjs\.org)",
        ],
    },
    {
        "id": "SEC-013",
        "severity": "medium",
        "description": "Environment variable or API key extraction",
        "tool_types": ["EXEC", "READ"],
        "patterns": [
            r"\bprintenv\b",
            r"\benv\s*$",
            r"\bset\s*\|\s*grep\b.*(?:KEY|SECRET|TOKEN|PASS)",
            r"cat\s+.*(?:\.env|secrets|credentials)",
        ],
    },
    {
        "id": "SEC-014",
        "severity": "high",
        "description": "Process injection or debugging attachment",
        "tool_types": ["EXEC"],
        "patterns": [
            r"\bgdb\b.*-p\s*\d+",
            r"\bstrace\b.*-p\s*\d+",
            r"\bptrace\b",
            r"\bLD_PRELOAD\b",
            r"\b/proc/\d+/mem\b",
        ],
    },
    {
        "id": "SEC-015",
        "severity": "high",
        "description": "Browser tool accessing sensitive URLs",
        "tool_types": ["BROWSER", "SEARCH"],
        "patterns": [
            r"(?:bank|paypal|stripe\.com/dashboard|console\.aws|portal\.azure)",
            r"(?:admin|phpmyadmin|wp-admin|cpanel)",
            r"file:///etc/",
        ],
    },
    {
        "id": "SEC-016",
        "severity": "high",
        "description": "Prompt injection attempt in external content",
        "tool_types": ["READ", "BROWSER", "SEARCH"],
        "patterns": [
            r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
            r"disregard\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
            r"forget\s+(?:all\s+)?(?:your\s+)?(?:previous|prior|above)\s+instructions",
            r"override\s+(?:your\s+)?(?:system\s+prompt|instructions|directives)",
            r"you\s+are\s+now\s+(?:a\s+)?(?:DAN|uncensored|unrestricted|jailbroken)",
            r"\bdo\s+anything\s+now\b",
            r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
            r"new\s+instructions?[:]\s*(?:you|your|from\s+now)",
        ],
    },
]

# Compile patterns once
for _sig in _THREAT_SIGNATURES:
    _sig["_compiled"] = [
        _sec_re.compile(p, _sec_re.IGNORECASE) for p in _sig["patterns"]
    ]


# Action labels a signature's ``tool_types`` may declare. These come from the
# LEGACY JSONL parser's ``tool_to_type()`` (routes/brain.py) and predate the
# DuckDB-first read path.
_THREAT_ACTION_TYPES = frozenset(
    {"EXEC", "READ", "WRITE", "BROWSER", "SEARCH", "MSG", "SPAWN", "TOOL"}
)

# Rows that are agent *speech*, not agent *action*. Running action signatures
# over these is how you flag the model for merely discussing ``~/.ssh/id_rsa``.
# Content-borne risk (PII, injection, leaked keys) is the content scanners'
# job — see ``_scan_content_for_policy_events``.
_THREAT_NON_ACTION_TYPES = frozenset(
    {"MESSAGE", "THINKING", "USER", "ASSISTANT", "SUMMARY", "COMPACT", "SYSTEM"}
)

# Tool-CALL rows as the DuckDB fast path emits them (routes/brain.py's
# ``evt_type = event_type.upper()``). Only the call is an agent ACTION.
#
# TOOL_RESULT is deliberately absent, and so is ERROR (which routes/brain.py
# derives from a failed TOOL_RESULT). A result is data the agent RECEIVED, not
# something it did, and results are big free-text blobs — a page of docs, web
# search output, a source file. Scanning them for action patterns produced
# nothing but noise: live on a real node, all four hits were TOOL_RESULT rows
# and all four were false positives (a Devin CLI docs page and a geocoding
# result matched "browser reaching an admin panel"; a Python source file
# matched "credential file access" at CRITICAL). Content-borne risk in results
# is the policy scanners' job — see ``_scan_content_for_policy_events``.
_THREAT_TOOL_TYPES = frozenset({"TOOL_CALL", "TOOL.CALL", "TOOL_USE"})

# Returned data, not agent action. Excluded for the reason above.
_THREAT_RESULT_TYPES = frozenset({"TOOL_RESULT", "TOOL.RESULT", "ERROR"})


def _threat_tool_name_to_action(name):
    """Map a tool NAME to a legacy action label. Mirrors routes/brain.py's
    ``tool_to_type`` so both taxonomies agree on what 'EXEC' means."""
    tn = str(name or "").lower()
    if tn == "exec" or "shell" in tn or "bash" in tn or tn == "process":
        return "EXEC"
    if "read" in tn or "grep" in tn or "glob" in tn:
        return "READ"
    if "write" in tn or "edit" in tn:
        return "WRITE"
    if "browser" in tn or "canvas" in tn or "image" in tn:
        return "BROWSER"
    if "web_search" in tn or "web_fetch" in tn or "search" in tn or "fetch" in tn:
        return "SEARCH"
    if "subagent" in tn or "spawn" in tn or "task" in tn:
        return "SPAWN"
    return "TOOL"


def _threat_action_types(ev):
    """Which action labels an event should be matched against.

    The signature table gates on the legacy ``EXEC/READ/WRITE/...`` vocabulary,
    but since the DuckDB-first migration brain rows arrive as
    ``TOOL_CALL/TOOL_RESULT/MESSAGE/THINKING/ERROR``. The two vocabularies do
    not intersect, so every event fell through every signature and the scanner
    could never report a threat (it was structurally pinned at 0). This bridges
    them: legacy labels pass through, speech rows are excluded, and a tool row
    with no tool NAME is matched against every signature — the store keeps the
    tool INPUT in ``detail`` but not which tool produced it, and the signature
    regexes are specific enough (``/dev/tcp/``, ``.ssh/id_rsa``) to carry the
    precision on their own.
    """
    ev_type = str(ev.get("type") or "").upper()
    if not ev_type:
        return frozenset()
    if ev_type in _THREAT_ACTION_TYPES:
        return frozenset({ev_type})
    if ev_type in _THREAT_NON_ACTION_TYPES or ev_type in _THREAT_RESULT_TYPES:
        return frozenset()
    if ev_type in _THREAT_TOOL_TYPES:
        name = ev.get("tool") or ev.get("toolName") or ev.get("name")
        if name:
            return frozenset({_threat_tool_name_to_action(name)})
        return _THREAT_ACTION_TYPES
    # CHANNEL.*, NUMBAT_FINDING, daemon rows, anything else we don't recognise
    # as an agent action: leave alone rather than guess.
    return frozenset()


def _threat_event_session(ev):
    """Session id for a brain event across both read paths.

    The legacy parser used ``source``; the DuckDB fast path emits ``sessionId``
    (full) plus ``src`` (truncated to 32 chars). Reading only ``source`` meant
    every event reported the empty string, so a node with five active sessions
    reported ``sessions_scanned: 1``.
    """
    return str(
        ev.get("sessionId") or ev.get("source") or ev.get("src") or ""
    )


def _threat_session_runtime(session_id):
    """``claude_code:1bfbb30f-...`` → ``claude_code``. Bare ids → ""."""
    sid = str(session_id or "")
    return sid.split(":", 1)[0] if ":" in sid else ""


def _scan_events_for_threats(events, runtime=None):
    """Scan brain-history events against threat signatures. Returns list of threat matches.

    ``runtime`` scopes the scan to one agent runtime (per FLYWHEEL §1c —
    a number shown under the runtime switcher must belong to that runtime).
    """
    threats = []
    sessions_seen = set()
    sessions_with_threats = set()
    want_runtime = str(runtime or "").strip().lower()

    for ev in events:
        source = _threat_event_session(ev)
        if want_runtime and _threat_session_runtime(source).lower() != want_runtime:
            continue
        sessions_seen.add(source)
        action_types = _threat_action_types(ev)
        if not action_types:
            continue
        ev_type = str(ev.get("type") or "")
        detail = ev.get("detail", "")
        if not detail:
            continue

        for sig in _THREAT_SIGNATURES:
            if not action_types.intersection(sig["tool_types"]):
                continue
            for compiled in sig["_compiled"]:
                if compiled.search(detail):
                    sessions_with_threats.add(source)
                    threats.append(
                        {
                            "rule_id": sig["id"],
                            "severity": sig["severity"],
                            "description": sig["description"],
                            "detail": detail[:500],
                            "time": ev.get("time", ""),
                            "session": ev.get("sourceLabel", source),
                            "source": source,
                            "event_type": ev_type,
                            "engine": "builtin",
                            "runtime": _threat_session_runtime(source),
                        }
                    )
                    break  # One match per signature per event

    # Sort by severity then time
    sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    threats.sort(
        key=lambda t: (sev_order.get(t["severity"], 9), t.get("time", "") or ""),
        reverse=False,
    )
    threats.sort(key=lambda t: t.get("time", "") or "", reverse=True)

    counts = {
        "critical": sum(1 for t in threats if t["severity"] == "critical"),
        "high": sum(1 for t in threats if t["severity"] == "high"),
        "medium": sum(1 for t in threats if t["severity"] == "medium"),
        "low": sum(1 for t in threats if t["severity"] == "low"),
        "total": len(threats),
        "sessions_scanned": len(sessions_seen),
        "clean_sessions": len(sessions_seen - sessions_with_threats),
    }
    return threats, counts


# (bp_security routes /api/security/threats and /api/security/signatures
#  moved to routes/infra.py)


def _scan_security_posture():
    """Thin delegate — the OpenClaw posture scan moved to
    :mod:`clawmetry.security_posture` (runtime-aware posture registry).

    Kept as a function on this module so existing callers keep working:
    routes/infra.py's legacy path, clawmetry/sync.py's shadow scan
    (``getattr(dashboard, "_scan_security_posture")``), and tests.
    Behaviour is identical: this returns the openclaw provider's result.
    """
    from clawmetry.security_posture import get_posture

    return get_posture("openclaw")


# (bp_security /api/security/posture moved to routes/infra.py)


# ── Content-policy scanners (PII / prompt-injection / credential-leak) ──────
# Complement to _scan_events_for_threats: that checks WHAT the agent DID
# (exec/read actions); these scan WHAT DATA flows through agent content
# (prompts, completions, tool results) for data-policy violations.

_POLICY_SIGNATURES = [
    # PII ─────────────────────────────────────────────────────────────────
    {
        "id": "POL-PII-001", "type": "PII", "severity": "medium",
        "description": "Email address in agent content",
        "pattern": r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    },
    {
        "id": "POL-PII-002", "type": "PII", "severity": "high",
        "description": "US Social Security Number in agent content",
        "pattern": r"\b\d{3}-\d{2}-\d{4}\b",
    },
    {
        "id": "POL-PII-003", "type": "PII", "severity": "medium",
        "description": "Phone number in agent content",
        "pattern": r"\b(?:\+\d{1,3}\s?)?\(?\d{3}\)?[\s.\-]\d{3}[\s.\-]\d{4}\b",
    },
    # Prompt injection ────────────────────────────────────────────────────
    {
        "id": "POL-INJECT-001", "type": "INJECT", "severity": "high",
        "description": "Prompt injection: ignore-instructions override attempt",
        "pattern": r"(?:ignore|disregard|forget|override)\s+(?:(?:all|your|my|the|those|any)\s+)?(?:previous|prior|above|original|earlier|current)?\s*(?:instructions?|prompts?|guidelines?|rules?|constraints?|system)",
    },
    {
        "id": "POL-INJECT-002", "type": "INJECT", "severity": "high",
        "description": "Prompt injection: role/persona override attempt",
        "pattern": r"(?:you\s+are\s+now|act\s+as|pretend\s+(?:to\s+be|you\s+are)|your\s+new\s+(?:role|persona|instructions?|task|objective))",
    },
    {
        "id": "POL-INJECT-003", "type": "INJECT", "severity": "medium",
        "description": "Prompt injection: hidden system-prompt injection marker",
        "pattern": r"(?:<\s*(?:system|sys|SYSTEM)\s*>|\[SYSTEM\s*PROMPT\]|#\s*SYSTEM\s*:)",
    },
    # Credential leak ─────────────────────────────────────────────────────
    {
        "id": "POL-LEAK-001", "type": "LEAK", "severity": "critical",
        "description": "AWS access key in agent content",
        "pattern": r"(?:AKIA|ABIA|ACCA|ASIA)[0-9A-Z]{16}",
    },
    {
        "id": "POL-LEAK-002", "type": "LEAK", "severity": "critical",
        "description": "Anthropic API key in agent content",
        "pattern": r"sk-ant-(?:api\d{2}-)?[A-Za-z0-9\-_]{86,}",
    },
    {
        "id": "POL-LEAK-003", "type": "LEAK", "severity": "critical",
        "description": "OpenAI API key in agent content",
        "pattern": r"sk-(?:proj-)?[A-Za-z0-9]{48,}",
    },
    {
        "id": "POL-LEAK-004", "type": "LEAK", "severity": "critical",
        "description": "GitHub personal access token in agent content",
        "pattern": r"(?:ghp|gho|ghu|ghs|ghr|github_pat)_[A-Za-z0-9_]{36,}",
    },
    {
        "id": "POL-LEAK-005", "type": "LEAK", "severity": "high",
        "description": "Generic API key/secret assignment in agent content",
        "pattern": r"(?:api[_\-]?key|api[_\-]?secret|secret[_\-]?key|access[_\-]?token)\s*[=:]\s*['\"]?[A-Za-z0-9\-_]{16,}",
    },
]

for _pol in _POLICY_SIGNATURES:
    _pol["_compiled"] = _sec_re.compile(_pol["pattern"], _sec_re.IGNORECASE)


def _scan_content_for_policy_events(events):
    """Scan brain-feed events for PII, prompt-injection, and credential-leak.

    Unlike _scan_events_for_threats (action-based), this inspects the text
    *content* in event detail fields — useful for finding data that should
    not appear in prompts or completions (PII leaking out, credentials leaking
    in/out, injection attempts arriving via tool results or user messages).

    Returns (hits, counts) with the same shape as _scan_events_for_threats.
    """
    hits = []
    for ev in events:
        detail = ev.get("detail") or ""
        if len(detail) < 8:
            continue
        for sig in _POLICY_SIGNATURES:
            m = sig["_compiled"].search(detail)
            if m:
                raw = m.group(0)
                redacted = (raw[:3] + "…" + raw[-2:]) if len(raw) > 6 else "***"
                hits.append({
                    "rule_id":     sig["id"],
                    "type":        sig["type"],
                    "severity":    sig["severity"],
                    "description": sig["description"],
                    "matched":     redacted,
                    "time":        ev.get("time", ""),
                    "session":     ev.get("source", ""),
                    "event_type":  ev.get("type", ""),
                })
                break  # one match per signature family per event
    counts = {
        "PII":    sum(1 for h in hits if h["type"] == "PII"),
        "INJECT": sum(1 for h in hits if h["type"] == "INJECT"),
        "LEAK":   sum(1 for h in hits if h["type"] == "LEAK"),
        "total":  len(hits),
    }
    return hits, counts


def _detect_channel_status():
    """Return list of configured channels with live connectivity status.

    Each entry: {'name': str, 'icon': str, 'status': 'connected'|'configured'|'unknown', 'detail': str}
    """
    CHANNEL_ICONS = {
        "telegram": "✈️",
        "discord": "🎮",
        "slack": "💬",
        "whatsapp": "📱",
        "signal": "🔒",
        "imessage": "🍎",
        "webchat": "🌐",
        "matrix": "🔢",
        "msteams": "🏢",
        "irc": "📡",
        "googlechat": "🔵",
        "mattermost": "⚡",
        "line": "💚",
        "nostr": "🟣",
        "twitch": "💜",
        "bluebubbles": "💙",
    }
    KNOWN_CHANNELS = (
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

    # Detect from gateway YAML config
    oc_dir = _get_openclaw_dir()
    yaml_candidates = [
        os.path.join(oc_dir, "gateway.yaml"),
        os.path.join(oc_dir, "gateway.yml"),
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

    # Detect from JSON config files
    if not configured:
        for cf in [
            os.path.join(oc_dir, "openclaw.json"),
            os.path.expanduser("~/.clawdbot/openclaw.json"),
            os.path.expanduser("~/.clawdbot/moltbot.json"),
        ]:
            try:
                with open(cf) as f:
                    data = json.load(f)
                plugins = data.get("plugins", {}).get("entries", {})
                for name, pconf in plugins.items():
                    if isinstance(pconf, dict) and pconf.get("enabled"):
                        _add(name)
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

    # Also check session data to infer active channels from recent activity
    if not configured:
        try:
            sessions = _get_sessions()
            for s in sessions:
                ch = s.get("channel") or s.get("channelName") or ""
                if ch:
                    _add(ch)
        except Exception:
            pass

    if not configured:
        return []

    # Filter to channels with data directories (evidence of real setup)
    DIR_EXEMPT = {
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
    cb_dir = os.path.expanduser("~/.clawdbot")
    active = []
    for ch in configured:
        if ch in DIR_EXEMPT:
            active.append(ch)
        elif any(os.path.isdir(os.path.join(d, ch)) for d in [oc_dir, cb_dir]):
            active.append(ch)
    if active:
        configured = active

    # Try to probe live connectivity for known channels
    results = []
    for ch in configured:
        icon = CHANNEL_ICONS.get(ch, "📡")
        status = "configured"
        detail = "Configured"

        if ch == "telegram":
            # Check if Telegram bot is reachable via getMe
            try:
                budget_cfg = _get_budget_config()
                tg_token = str(budget_cfg.get("telegram_bot_token", "")).strip()
                if not tg_token:
                    # Try reading directly from openclaw.json
                    for cf in [
                        os.path.join(oc_dir, "openclaw.json"),
                        os.path.expanduser("~/.clawdbot/openclaw.json"),
                    ]:
                        try:
                            with open(cf) as f:
                                d = json.load(f)
                            tg_token = str(
                                d.get("telegram", {}).get("token", "")
                                or d.get("plugins", {})
                                .get("entries", {})
                                .get("telegram", {})
                                .get("token", "")
                            ).strip()
                            if tg_token:
                                break
                        except Exception:
                            pass
                if tg_token:
                    import urllib.request as _ur

                    req = _ur.Request(
                        f"https://api.telegram.org/bot{tg_token}/getMe", method="GET"
                    )
                    req.add_header("User-Agent", "ClawMetry/1.0")
                    with _ur.urlopen(req, timeout=4) as resp:
                        data = json.loads(resp.read())
                    if data.get("ok"):
                        bot_name = data.get("result", {}).get("username", "")
                        status = "connected"
                        detail = f"@{bot_name}" if bot_name else "Connected"
                    else:
                        status = "configured"
                        detail = "Token invalid"
                else:
                    status = "configured"
                    detail = "No token configured"
            except Exception as e:
                err = str(e)
                if "timed out" in err or "timeout" in err:
                    status = "configured"
                    detail = "Timeout checking"
                else:
                    status = "configured"
                    detail = "Check failed"

        results.append(
            {
                "name": ch.capitalize(),
                "id": ch,
                "icon": icon,
                "status": status,
                "detail": detail,
            }
        )

    return results


# ── Rate Limit Monitor (GH#67) ────────────────────────────────────────────────

# Default API rate limits per provider (RPM = requests/min, TPM = tokens/min)
# Users can override these in openclaw.json under clawmetry.rate_limits
_DEFAULT_RATE_LIMITS = {
    'anthropic': {'rpm': 60,  'tpm_input': 80_000,    'tpm_output': 16_000,   'label': 'Anthropic (Claude)'},
    'google':    {'rpm': 360, 'tpm_input': 4_000_000,  'tpm_output': 400_000,  'label': 'Google (Gemini)'},
    'openai':    {'rpm': 60,  'tpm_input': 800_000,    'tpm_output': 100_000,  'label': 'OpenAI'},
    'bedrock':   {'rpm': 60,  'tpm_input': 80_000,     'tpm_output': 16_000,   'label': 'AWS Bedrock'},
    'openrouter':{'rpm': 200, 'tpm_input': 1_000_000,  'tpm_output': 200_000,  'label': 'OpenRouter'},
}


def _infer_provider(entry):
    """Infer API provider from entry metadata."""
    provider = (entry.get('provider') or '').lower()
    if provider and provider != 'unknown':
        return provider
    model = (entry.get('model') or '').lower()
    if any(k in model for k in ('claude', 'haiku', 'sonnet', 'opus')):
        return 'anthropic'
    if any(k in model for k in ('gemini', 'gemma')):
        return 'google'
    if any(k in model for k in ('gpt', 'o1-', 'o3-', 'o4-')):
        return 'openai'
    return 'other'


# (bp_config routes moved to routes/infra.py: /api/llmfit, /api/cost-optimizer,
#  /api/cost-optimization, /api/automation-analysis)


# (bp_nemoclaw handlers moved to routes/nemoclaw.py: /api/nemoclaw/status,
#  /api/nemoclaw/policy, /api/nemoclaw/approve, /api/nemoclaw/reject,
#  /api/nemoclaw/pending-approvals)


# ── Context Inspector (GH #9) ─────────────────────────────────────────


# ── Upgrade Impact Dashboard (GH #408) ────────────────────────────────────────


def _get_openclaw_version():
    """Detect current OpenClaw version from openclaw.json meta field or CLI."""
    # Try meta.lastTouchedVersion from openclaw.json
    oc_config = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(oc_config) as f:
            data = json.load(f)
        v = (data.get("meta") or {}).get("lastTouchedVersion")
        if v:
            return str(v)
        # Also try wizard.lastRunVersion
        v = (data.get("wizard") or {}).get("lastRunVersion")
        if v:
            return str(v)
    except Exception:
        pass
    # Fallback: run openclaw --version
    try:
        import subprocess

        out = (
            subprocess.check_output(
                ["openclaw", "--version"], stderr=subprocess.STDOUT, timeout=5
            )
            .decode()
            .strip()
        )
        # Extract semver-like from output e.g. "openclaw/2026.3.13 ..."
        import re

        m = re.search(r"(\d{4}\.\d+\.\d+|\d+\.\d+\.\d+)", out)
        if m:
            return m.group(1)
    except Exception:
        pass
    return None


def _version_impact_db():
    """Get SQLite connection for version tracking, reusing history.db."""
    db_path = os.path.expanduser("~/.clawmetry/history.db")
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db = _sqlite3.connect(db_path, timeout=10)
    db.row_factory = _sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
        CREATE TABLE IF NOT EXISTS version_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            version TEXT NOT NULL,
            detected_at REAL NOT NULL,
            source TEXT DEFAULT 'openclaw.json'
        );
        CREATE INDEX IF NOT EXISTS idx_ve_ts ON version_events(detected_at);
    """)
    return db


def _record_version_if_changed(current_version):
    """Record a version event if the version has changed since last check."""
    if not current_version:
        return
    db = _version_impact_db()
    try:
        row = db.execute(
            "SELECT version FROM version_events ORDER BY detected_at DESC LIMIT 1"
        ).fetchone()
        if row and row["version"] == current_version:
            db.close()
            return
        db.execute(
            "INSERT INTO version_events (version, detected_at) VALUES (?, ?)",
            (current_version, time.time()),
        )
        db.commit()
    finally:
        db.close()


def _compute_session_stats_in_range(sessions_dir, start_ts, end_ts):
    """Compute aggregate session stats for sessions whose mtime falls in [start_ts, end_ts)."""
    stats = {
        "session_count": 0,
        "total_cost": 0.0,
        "total_tokens": 0,
        "error_count": 0,
        "tool_calls": 0,
        "duration_ms_total": 0,
        "duration_sessions": 0,
    }
    if not sessions_dir or not os.path.isdir(sessions_dir):
        return stats

    for fname in os.listdir(sessions_dir):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(sessions_dir, fname)
        try:
            mtime = os.path.getmtime(fpath)
            if not (start_ts <= mtime < end_ts):
                continue
        except OSError:
            continue

        stats["session_count"] += 1
        session_cost = 0.0
        session_tokens = 0
        session_errors = 0
        session_tools = 0
        first_ts = None
        last_ts = None

        try:
            with open(fpath, "r", errors="replace") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except Exception:
                        continue
                    ts_str = ev.get("timestamp", "")
                    if ts_str:
                        try:
                            ts_dt = datetime.fromisoformat(
                                ts_str.replace("Z", "+00:00")
                            )
                            ts_f = ts_dt.timestamp()
                            if first_ts is None or ts_f < first_ts:
                                first_ts = ts_f
                            if last_ts is None or ts_f > last_ts:
                                last_ts = ts_f
                        except Exception:
                            pass
                    ev_type = ev.get("type", "")
                    if ev_type == "message":
                        msg = ev.get("message", {})
                        role = msg.get("role", "")
                        if role == "assistant":
                            usage = msg.get("usage", {})
                            if isinstance(usage, dict):
                                cost_obj = usage.get("cost", {})
                                if isinstance(cost_obj, dict):
                                    session_cost += float(cost_obj.get("total", 0))
                                elif isinstance(cost_obj, (int, float)):
                                    session_cost += float(cost_obj)
                                tok_in = (
                                    usage.get("input", 0)
                                    or usage.get("inputTokens", 0)
                                    or 0
                                )
                                tok_out = (
                                    usage.get("output", 0)
                                    or usage.get("outputTokens", 0)
                                    or 0
                                )
                                session_tokens += int(tok_in) + int(tok_out)
                        if isinstance(msg.get("content"), list):
                            for part in msg["content"]:
                                if (
                                    isinstance(part, dict)
                                    and part.get("type") == "toolCall"
                                ):
                                    session_tools += 1
                    elif ev_type == "error":
                        session_errors += 1
        except Exception:
            pass

        stats["total_cost"] += session_cost
        stats["total_tokens"] += session_tokens
        stats["error_count"] += session_errors
        stats["tool_calls"] += session_tools
        if first_ts and last_ts and last_ts > first_ts:
            stats["duration_ms_total"] += int((last_ts - first_ts) * 1000)
            stats["duration_sessions"] += 1

    return stats


def _stats_to_summary(stats):
    n = max(stats["session_count"], 1)
    return {
        "session_count": stats["session_count"],
        "avg_cost": round(stats["total_cost"] / n, 6),
        "avg_tokens": int(stats["total_tokens"] / n),
        "avg_tool_calls": round(stats["tool_calls"] / n, 1),
        "error_rate": round(stats["error_count"] / n, 3),
        "avg_duration_ms": int(
            stats["duration_ms_total"] / max(stats["duration_sessions"], 1)
        ),
        "total_cost": round(stats["total_cost"], 6),
    }


def _compute_diff(before, after):
    """Compute percentage change between before and after summaries."""
    diff = {}
    for key in (
        "avg_cost",
        "avg_tokens",
        "avg_tool_calls",
        "error_rate",
        "avg_duration_ms",
    ):
        b = before.get(key, 0)
        a = after.get(key, 0)
        if b == 0:
            pct = None
        else:
            pct = round((a - b) / abs(b) * 100, 1)
        diff[key] = {"before": b, "after": a, "pct_change": pct}
    return diff


# (bp_version_impact handler moved to routes/meta.py: /api/version-impact)


# ── Trace Clustering (GH #406) ───────────────────────────────────────────────

_CLUSTER_TOOL_GROUPS = {
    "browsing": {"browser", "web_fetch", "web_search"},
    "coding": {"exec", "Read", "Write", "Edit", "process"},
    "messaging": {"message", "tts"},
    "pdf": {"pdf", "image"},
    "files": {"Read", "Write", "Edit"},
}


def _build_context_inspector_data():
    """Analyse workspace context files and session transcripts to produce the
    Context Inspector payload.

    Returns:
        {
          agents: [{sessionId, displayName, depth, parentId, contextFiles,
                    coverageScore, lintWarnings, spawnTaskSnippet, tokensIn}],
          lintWarnings: [{sessionId, message, severity}],
          summary: {totalAgents, avgCoverage, totalWarnings, contextFilesFound},
          contextFiles: [{name, sizeKB, exists}],
          generatedAt: ISO string,
        }
    """

    workspace = WORKSPACE or os.path.expanduser("~")
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )

    # ── 1. Discover workspace context files ──────────────────────────────
    KNOWN_CONTEXT_FILES = [
        "SOUL.md",
        "AGENTS.md",
        "MEMORY.md",
        "USER.md",
        "IDENTITY.md",
        "HEARTBEAT.md",
        "CODING.md",
        "TOOLS.md",
    ]
    context_files_info = []
    existing_context_files = set()
    for fname in KNOWN_CONTEXT_FILES:
        fpath = os.path.join(workspace, fname)
        exists = os.path.isfile(fpath)
        size_kb = 0.0
        if exists:
            try:
                size_kb = round(os.path.getsize(fpath) / 1024, 1)
                existing_context_files.add(fname.lower())
            except OSError:
                pass
        context_files_info.append({"name": fname, "sizeKB": size_kb, "exists": exists})

    # Also check memory/ subdirectory
    mem_dir = os.path.join(workspace, "memory")
    memory_file_count = 0
    if os.path.isdir(mem_dir):
        try:
            memory_file_count = sum(1 for f in os.listdir(mem_dir) if f.endswith(".md"))
        except OSError:
            pass

    # ── 2. Parse sessions.json to build agent tree ──────────────────────
    index_path = os.path.join(sessions_dir, "sessions.json")
    sessions_raw = []
    try:
        with open(index_path) as f:
            idx = json.load(f)
            sessions_raw = list(idx.values()) if isinstance(idx, dict) else idx
    except (OSError, json.JSONDecodeError, TypeError):
        pass

    # Limit to 50 most recent to keep response fast
    sessions_raw = sorted(
        sessions_raw, key=lambda s: s.get("lastActiveMs", 0), reverse=True
    )[:50]

    # ── 3. For each session read the first few lines to extract spawn task ─
    def _extract_spawn_task(sess_id):
        """Return first user message text (truncated) — this is the task the agent got."""
        fpath = os.path.join(sessions_dir, sess_id + ".jsonl")
        if not os.path.isfile(fpath):
            return ""
        try:
            with open(fpath) as f:
                for line in f:
                    try:
                        obj = json.loads(line.strip())
                    except (json.JSONDecodeError, ValueError):
                        continue
                    if obj.get("type") == "message":
                        msg = obj.get("message", {})
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            if isinstance(content, str):
                                return content[:300]
                            if isinstance(content, list):
                                for block in content:
                                    if (
                                        isinstance(block, dict)
                                        and block.get("type") == "text"
                                    ):
                                        return block.get("text", "")[:300]
        except OSError:
            pass
        return ""

    def _compute_coverage_score(sess, task_text):
        """Heuristic 0-100 coverage score.

        Checks:
        - Is there a task description at all?           +20
        - SOUL.md mentioned / present in workspace?     +20
        - AGENTS.md / MEMORY.md present?                +15 each
        - Task length ≥ 50 chars (enough context)?      +15
        - memory/ has recent files?                     +15
        """
        score = 0
        if task_text:
            score += 20
        txt_lower = task_text.lower()
        if "soul" in txt_lower or "soul.md" in existing_context_files:
            score += 20
        if "agents.md" in existing_context_files:
            score += 15
        if "memory.md" in existing_context_files:
            score += 15
        if len(task_text) >= 50:
            score += 15
        if memory_file_count > 0:
            score += 15
        return min(score, 100)

    def _lint_task(sess_id, sess, task_text):
        """Return list of lint warning strings for this agent's spawn context."""
        warnings = []
        txt_lower = task_text.lower()
        # Warn if task mentions user-specific data but no memory files
        user_data_hints = ["vivek", "user", "my ", "i'm", "password", "email", "phone"]
        if (
            any(h in txt_lower for h in user_data_hints)
            and "user.md" not in existing_context_files
        ):
            warnings.append(
                {
                    "severity": "warn",
                    "message": "Task references user data but USER.md not found in workspace",
                }
            )
        # Warn if sub-agent task is very short (context starvation risk)
        depth = sess.get("depth", 0) or 0
        if depth > 0 and len(task_text) < 50:
            warnings.append(
                {
                    "severity": "error",
                    "message": f"Sub-agent (depth {depth}) has a very short task — possible context starvation (<50 chars)",
                }
            )
        # Warn if no SOUL.md
        if "soul.md" not in existing_context_files:
            warnings.append(
                {
                    "severity": "warn",
                    "message": "SOUL.md not found — agent identity/persona context is missing",
                }
            )
        # Warn if no MEMORY.md
        if "memory.md" not in existing_context_files:
            warnings.append(
                {
                    "severity": "info",
                    "message": "MEMORY.md not found — long-term memory context unavailable",
                }
            )
        return warnings

    # ── 4. Build agent list ───────────────────────────────────────────────
    agents = []
    all_lint_warnings = []

    for sess in sessions_raw:
        sess_id = sess.get("sessionId") or sess.get("key", "")
        if not sess_id:
            continue

        display = sess.get("displayName") or sess_id[:16]
        depth = int(sess.get("depth", 0) or 0)
        parent_id = sess.get("spawnedBy") or sess.get("parentKey") or None
        tokens_in = sess.get("inputTokens") or sess.get("totalTokens", 0) or 0

        task_text = _extract_spawn_task(sess_id)
        coverage = _compute_coverage_score(sess, task_text)
        lint = _lint_task(sess_id, sess, task_text)

        # Collect files referenced in the task text (simple heuristic)
        referenced = [f for f in KNOWN_CONTEXT_FILES if f.lower() in task_text.lower()]
        missing = [f for f in referenced if f.lower() not in existing_context_files]

        agent_entry = {
            "sessionId": sess_id,
            "displayName": display,
            "depth": depth,
            "parentId": parent_id,
            "coverageScore": coverage,
            "lintWarnings": lint,
            "spawnTaskSnippet": task_text[:200] if task_text else "",
            "referencedContextFiles": referenced,
            "missingContextFiles": missing,
            "tokensIn": tokens_in,
            "lastActiveMs": sess.get("lastActiveMs", 0),
            "model": sess.get("model") or sess.get("modelRef", "unknown"),
        }
        agents.append(agent_entry)

        for w in lint:
            all_lint_warnings.append(
                {"sessionId": sess_id, "displayName": display, **w}
            )

    # Deduplicate global lint warnings (same message across sessions)
    seen_msgs = set()
    deduped_warnings = []
    for w in all_lint_warnings:
        key = w["message"]
        if key not in seen_msgs:
            seen_msgs.add(key)
            deduped_warnings.append(w)

    avg_coverage = (
        round(sum(a["coverageScore"] for a in agents) / len(agents), 1) if agents else 0
    )

    return {
        "agents": agents,
        "lintWarnings": deduped_warnings,
        "summary": {
            "totalAgents": len(agents),
            "avgCoverage": avg_coverage,
            "totalWarnings": len(all_lint_warnings),
            "contextFilesFound": len(existing_context_files),
            "memoryFileCount": memory_file_count,
        },
        "contextFiles": context_files_info,
        "generatedAt": datetime.now(timezone.utc).isoformat(),
    }


# ── Data Helpers ────────────────────────────────────────────────────────


def _extract_gw_session_cost(s: dict):
    """Return the session cost in USD from a gateway sessions.list entry.

    The gateway has emitted this value under several key names across versions
    (costUsd, totalCostUsd, cost_usd) and also as a nested cost.total dict.
    Returns float or None (honest unknown).
    """
    raw = s.get("costUsd") or s.get("totalCostUsd") or s.get("cost_usd")
    if raw is None:
        co = s.get("cost")
        if isinstance(co, dict):
            raw = co.get("total") or co.get("total_usd")
        elif isinstance(co, (int, float)):
            raw = co
    try:
        return float(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _get_sessions():
    """Get sessions via gateway API first, file fallback."""
    now = time.time()
    if (
        _sessions_cache["data"] is not None
        and (now - _sessions_cache["ts"]) < _SESSIONS_CACHE_TTL
    ):
        return _sessions_cache["data"]

    # Try WebSocket RPC first
    api_data = _gw_ws_rpc("sessions.list")
    if api_data and "sessions" in api_data:
        sessions = []
        for s in api_data["sessions"][:30]:
            sessions.append(
                {
                    "sessionId": s.get("key", ""),
                    "key": s.get("key", "")[:12] + "...",
                    "displayName": s.get("displayName", s.get("key", "")[:20]),
                    "updatedAt": s.get("updatedAtMs", s.get("lastActiveMs", 0)),
                    "model": s.get("model", s.get("modelRef", "unknown")),
                    "channel": s.get("channel", "unknown"),
                    "totalTokens": s.get("totalTokens", 0),
                    "inputTokens": s.get("inputTokens", 0),
                    "outputTokens": s.get("outputTokens", 0),
                    "cacheReadTokens": s.get("cacheReadInputTokens", s.get("cacheReadTokens", 0)),
                    "cacheWriteTokens": s.get("cacheCreationInputTokens", s.get("cacheWriteTokens", 0)),
                    "costUsd": _extract_gw_session_cost(s),
                    "contextTokens": api_data.get("defaults", {}).get(
                        "contextTokens", 200000
                    ),
                    "kind": s.get("kind", "direct"),
                    "transcriptionProvider": s.get("transcriptionProvider") or s.get("talkTranscriptionProvider") or s.get("speechProvider") or "",
                    "talkTransport": s.get("talkTransport") or s.get("voiceTransport") or "",
                    "voiceModel": s.get("voiceModel") or s.get("realtimeModel") or s.get("talkModel") or "",
                    "vadMode": s.get("vadMode") or s.get("talkVadMode") or "",
                    "agent": s.get("agentId", "main"),
                    "parentId": s.get("parentSessionId") or s.get("parentId") or s.get("spawnedBy") or s.get("parentKey") or None,
                    "endedAt": s.get("endedAtMs") or s.get("endedAt"),
                    "endReason": s.get("endReason") or "",
                    "messageCount": int(s.get("messageCount") or 0),
                    "title": s.get("title") or "",
                    "costStatus": s.get("costStatus") or "",
                    "target": s.get("target") or s.get("identityTarget"),
                    "capabilityProfile": s.get("capabilityProfile") or s.get("conversationCapability"),
                }
            )
        _sessions_cache["data"] = sessions
        _sessions_cache["ts"] = now
        return sessions

    # File-based fallback
    return _get_sessions_from_files()


def _scan_session_aggregates(file_path):
    """Walk a session JSONL once and return (recent_model, total_tokens).

    Replaces the "file size as totalTokens" heuristic with an actual sum of
    `message.usage.totalTokens`. `recent_model` = the LAST model actually used
    in the session (from model_change / model-snapshot / message.model in
    file order), which is what the MODEL badge on Overview / Flow / Brain
    should display — those are live-activity surfaces that should reflect
    "what's running right now," not a historical aggregate.
    """
    total_tokens = 0
    last_seen_model = ""
    try:
        with open(file_path, "r", errors="replace") as fh:
            for raw in fh:
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                except Exception:
                    continue
                t = obj.get("type", "")
                if t == "model_change":
                    m = obj.get("modelId") or obj.get("model") or ""
                    if m:
                        last_seen_model = m
                elif t == "custom" and obj.get("customType") == "model-snapshot":
                    d = obj.get("data", {}) or {}
                    m = d.get("modelId") or d.get("model") or ""
                    if m:
                        last_seen_model = m
                elif t == "message":
                    msg = obj.get("message", {}) or {}
                    if not isinstance(msg, dict):
                        continue
                    usage = msg.get("usage", {}) or {}
                    if isinstance(usage, dict):
                        total_tokens += int(usage.get("totalTokens", 0) or 0)
                    msg_model = msg.get("model") or ""
                    if msg_model:
                        last_seen_model = msg_model
    except Exception:
        pass
    return (last_seen_model or "unknown", total_tokens)


def _get_sessions_from_files():
    """Read active sessions from the session directory (file-based fallback)."""
    now = time.time()

    sessions = []
    try:
        base = SESSIONS_DIR or os.path.expanduser("~/.openclaw/agents/main/sessions")
        if not os.path.isdir(base):
            return sessions
        idx_files = sorted(
            [
                f
                for f in os.listdir(base)
                if f.endswith(".jsonl") and "deleted" not in f
            ],
            key=lambda f: os.path.getmtime(os.path.join(base, f)),
            reverse=True,
        )
        for fname in idx_files[:30]:
            fpath = os.path.join(base, fname)
            try:
                mtime = os.path.getmtime(fpath)
                with open(fpath) as f:
                    first = json.loads(f.readline())
                sid = fname.replace(".jsonl", "")
                # Single walk gets the session's most recent model + the real
                # token count. Previous code used file size as totalTokens,
                # which gave a bogus number proportional to JSONL bytes not
                # actual usage.
                model, total_tokens = _scan_session_aggregates(fpath)
                sessions.append(
                    {
                        "sessionId": sid,
                        "key": sid[:12] + "...",
                        "displayName": sid[:20],
                        "updatedAt": int(mtime * 1000),
                        "model": model,
                        "channel": "unknown",
                        "totalTokens": total_tokens,
                        "contextTokens": 200000,
                    }
                )
            except Exception:
                pass
    except Exception:
        pass
    _sessions_cache["data"] = sessions
    _sessions_cache["ts"] = now
    try:
        _ext_emit("session.snapshot", {"count": len(sessions)})
    except Exception:
        pass
    return sessions


def _safe_session_id(raw_id):
    sid = str(raw_id or "").strip()
    if not sid or "/" in sid or "\\" in sid or "\x00" in sid or ".." in sid:
        return ""
    return sid


def _resolve_session_stop_target(session_id):
    """Resolve stop target info for a session id/key."""
    sid = _safe_session_id(session_id)
    if not sid:
        return {"session_id": "", "jsonl_path": "", "stop_path": "", "pid": None}
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    final_sid = sid
    pid = None

    direct_jsonl = os.path.join(sessions_dir, f"{sid}.jsonl")
    if os.path.exists(direct_jsonl):
        stop_path = os.path.join(sessions_dir, f"{sid}.stop")
        return {
            "session_id": sid,
            "jsonl_path": direct_jsonl,
            "stop_path": stop_path,
            "pid": None,
        }

    idx = os.path.join(sessions_dir, "sessions.json")
    try:
        with open(idx, "r") as f:
            mapping = json.load(f)
        if isinstance(mapping, dict):
            for key, meta in mapping.items():
                if not isinstance(meta, dict):
                    continue
                mapped_sid = str(meta.get("sessionId", "")).strip()
                if sid in (key, mapped_sid):
                    if mapped_sid:
                        final_sid = mapped_sid
                    pid_raw = meta.get("pid") or meta.get("processId")
                    try:
                        pid = int(pid_raw)
                    except Exception:
                        pid = None
                    break
    except Exception:
        pass

    jsonl_path = os.path.join(sessions_dir, f"{final_sid}.jsonl")
    stop_path = os.path.join(sessions_dir, f"{final_sid}.stop")
    return {
        "session_id": final_sid,
        "jsonl_path": jsonl_path,
        "stop_path": stop_path,
        "pid": pid,
    }


def _estimate_usd_per_token():
    """Estimate USD per token from recent metrics; fallback to conservative default."""
    now = time.time()
    start = now - 86400
    total_tokens = 0.0
    total_cost = 0.0
    with _metrics_lock:
        for t in metrics_store.get("tokens", []):
            if t.get("timestamp", 0) >= start:
                total_tokens += float(t.get("total", 0) or 0)
        for c in metrics_store.get("cost", []):
            if c.get("timestamp", 0) >= start:
                total_cost += float(c.get("usd", 0) or 0)
    if total_tokens > 0 and total_cost > 0:
        return total_cost / total_tokens
    return 3.0 / 1_000_000.0


def _json_ts_to_epoch(v):
    if not v:
        return None
    if isinstance(v, (int, float)):
        iv = float(v)
        if iv > 1e12:
            return iv / 1000.0
        return iv
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _session_burn_stats(session_id):
    sid = _safe_session_id(session_id)
    if not sid:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}
    sessions_dir = SESSIONS_DIR or os.path.expanduser(
        "~/.openclaw/agents/main/sessions"
    )
    fpath = os.path.join(sessions_dir, f"{sid}.jsonl")
    if not os.path.exists(fpath):
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    points = []
    try:
        with open(fpath, "r", errors="replace") as f:
            lines = list(deque(f, maxlen=1200))
        for line in lines:
            try:
                obj = json.loads(line.strip())
            except Exception:
                continue
            ts = _json_ts_to_epoch(
                obj.get("timestamp") or obj.get("time") or obj.get("created_at")
            )
            if not ts:
                continue
            tok = 0.0
            msg = obj.get("message", {}) if isinstance(obj.get("message"), dict) else {}
            usage = msg.get("usage", {}) if isinstance(msg.get("usage"), dict) else {}
            tok = float(
                usage.get("total_tokens")
                or usage.get("totalTokens")
                or usage.get("input_tokens", 0) + usage.get("output_tokens", 0)
                or 0
            )
            if tok <= 0:
                content = msg.get("content", [])
                text = ""
                if isinstance(content, str):
                    text = content
                elif isinstance(content, list):
                    parts = []
                    for b in content:
                        if isinstance(b, dict):
                            if b.get("type") == "text":
                                parts.append(str(b.get("text", "")))
                            elif b.get("type") == "thinking":
                                parts.append(str(b.get("thinking", "")))
                    text = " ".join(parts)
                if text:
                    tok = max(1.0, len(text) / 4.0)
            if tok > 0:
                points.append((ts, tok))
    except Exception:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    if not points:
        return {"tokensPerMin": 0, "projectedCostUsd": 0.0, "burnSeries": [0] * 10}

    end_ts = max(ts for ts, _ in points)
    start_ts = end_ts - 600
    buckets = [0.0] * 10
    for ts, tok in points:
        if ts < start_ts:
            continue
        idx = int((ts - start_ts) // 60)
        if idx < 0:
            idx = 0
        if idx > 9:
            idx = 9
        buckets[idx] += tok

    recent = buckets[-5:] if len(buckets) >= 5 else buckets
    tokens_per_min = (sum(recent) / len(recent)) if recent else 0.0
    usd_per_token = _estimate_usd_per_token()
    projected_cost = tokens_per_min * 60.0 * usd_per_token
    return {
        "tokensPerMin": round(tokens_per_min, 2),
        "projectedCostUsd": round(projected_cost, 4),
        "burnSeries": [round(x, 2) for x in buckets],
    }


def _augment_sessions_with_burn(sessions):
    out = []
    for s in sessions or []:
        if not isinstance(s, dict):
            out.append(s)
            continue
        row = dict(s)
        sid = row.get("sessionId") or row.get("id") or row.get("key") or ""
        row["sessionId"] = sid
        row.update(_session_burn_stats(sid))
        out.append(row)
    return out


def _get_crons():
    """Get crons via gateway API first, file fallback."""
    # Try WebSocket RPC first
    api_data = _gw_ws_rpc("cron.list")
    if api_data and "jobs" in api_data:
        return api_data["jobs"]
    # File-based fallback
    return _get_crons_from_files()


def _get_crons_from_files():
    """Read crons from OpenClaw/moltbot state (file-based fallback)."""
    candidates = [
        os.path.expanduser("~/.openclaw/cron/jobs.json"),
        os.path.expanduser("~/.clawdbot/cron/jobs.json"),
    ]
    # Also check data dir if set via env
    data_dir = os.environ.get("OPENCLAW_DATA_DIR", "")
    if data_dir:
        candidates.insert(0, os.path.join(data_dir, "cron", "jobs.json"))
    for crons_file in candidates:
        try:
            if os.path.exists(crons_file):
                with open(crons_file) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return data
                    if isinstance(data, dict):
                        return data.get("jobs", list(data.values()))
        except Exception:
            pass
    return []


def _normalize_next_run_at_ms(state):
    """Ensure nextRunAtMs is a number (ms timestamp) or null (closes #685)."""
    if not isinstance(state, dict):
        return None
    val = state.get("nextRunAtMs")
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return int(val)
    if isinstance(val, str):
        try:
            # ISO timestamp or numeric string
            if "T" in val:
                from dateutil import parser as _dtp
                return int(_dtp.parse(val).timestamp() * 1000)
            return int(float(val))
        except Exception:
            return None
    return None


def _get_memory_files():
    """List workspace memory files."""
    result = []
    workspace = WORKSPACE or os.getcwd()
    memory_dir = MEMORY_DIR or os.path.join(workspace, "memory")

    for name in [
        "MEMORY.md",
        "SOUL.md",
        "IDENTITY.md",
        "USER.md",
        "AGENTS.md",
        "TOOLS.md",
        "HEARTBEAT.md",
    ]:
        path = os.path.join(workspace, name)
        if os.path.exists(path):
            result.append({"path": name, "size": os.path.getsize(path)})
    if os.path.isdir(memory_dir):
        pattern = os.path.join(memory_dir, "*.md")
        for f in sorted(glob.glob(pattern), reverse=True):
            name = "memory/" + os.path.basename(f)
            result.append({"path": name, "size": os.path.getsize(f)})
    return result


def _get_llmfit_recommendations():
    """Run llmfit to get local model recommendations for this hardware."""
    import shutil

    if not shutil.which("llmfit"):
        return {
            "available": False,
            "recommendations": [],
            "codingModels": [],
            "chatModels": [],
            "system": {},
        }

    try:
        # General recommendations
        result = subprocess.run(
            ["llmfit", "recommend", "--json", "--limit", "8"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        all_data = json.loads(result.stdout) if result.returncode == 0 else {}

        # Coding-specific
        coding_result = subprocess.run(
            ["llmfit", "recommend", "--json", "--use-case", "coding", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        coding_data = (
            json.loads(coding_result.stdout) if coding_result.returncode == 0 else {}
        )

        # Chat-specific
        chat_result = subprocess.run(
            ["llmfit", "recommend", "--json", "--use-case", "chat", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        chat_data = (
            json.loads(chat_result.stdout) if chat_result.returncode == 0 else {}
        )

        system_info = all_data.get("system", {})
        # Annotate: llmfit doesn't detect Apple Silicon GPU but Metal makes it 3-5x faster
        cpu = system_info.get("cpu_name", "")
        if (
            "apple" in cpu.lower()
            or "M1" in cpu
            or "M2" in cpu
            or "M3" in cpu
            or "M4" in cpu
        ):
            system_info["note"] = (
                "Apple Silicon -- Metal GPU available (3-5x faster than llmfit estimates)"
            )
            system_info["has_metal"] = True

        def _clean_model(m):
            # Extract short name from full HF path
            name = m.get("name", "")
            short = name.split("/")[-1] if "/" in name else name
            return {
                "name": short,
                "fullName": name,
                "provider": m.get("provider", ""),
                "category": m.get("category", ""),
                "useCase": m.get("use_case", ""),
                "estimatedTps": m.get("estimated_tps", 0),
                "memoryRequiredGb": m.get("memory_required_gb", 0),
                "parameterCount": m.get("parameter_count", ""),
                "contextLength": m.get("context_length", 0),
                "score": m.get("score", 0),
                "bestQuant": m.get("best_quant", ""),
                "fitLevel": m.get("fit_level", ""),
            }

        return {
            "available": True,
            "system": system_info,
            "recommendations": [
                _clean_model(m) for m in all_data.get("models", [])[:8]
            ],
            "codingModels": [
                _clean_model(m) for m in coding_data.get("models", [])[:5]
            ],
            "chatModels": [_clean_model(m) for m in chat_data.get("models", [])[:5]],
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
            "recommendations": [],
            "codingModels": [],
            "chatModels": [],
            "system": {},
        }


def _generate_savings_opportunities():
    """Identify tasks/crons that could use local models instead of expensive cloud models."""
    opportunities = []

    expensive_models = ["claude-sonnet", "claude-opus", "gpt-4", "o1", "o3"]

    # Check cron jobs
    try:
        crons = _get_crons()
        for cron in crons:
            model = cron.get("model", cron.get("modelRef", ""))
            name = cron.get("name", cron.get("label", "Unknown cron"))
            if any(m in (model or "").lower() for m in expensive_models):
                prompt = (cron.get("prompt", "") or "").lower()
                # Heuristic: heartbeat/status checks are simple tasks
                is_simple = any(
                    w in prompt
                    for w in [
                        "heartbeat",
                        "check",
                        "status",
                        "ping",
                        "monitor",
                        "health",
                    ]
                )
                if is_simple or not prompt:
                    opportunities.append(
                        {
                            "task": f"Cron: {name}",
                            "currentModel": model or "claude-sonnet-4-6",
                            "suggestedModel": "Qwen2.5-Coder-3B via Ollama",
                            "estimatedSavings": "~$1-3/month",
                            "reason": "Periodic checks and status tasks don't need frontier models",
                        }
                    )
    except Exception:
        pass

    # Always suggest heartbeat optimization
    opportunities.append(
        {
            "task": "Heartbeat cron (periodic checks)",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "Qwen3-4B via Ollama",
            "estimatedSavings": "~$2-5/month",
            "reason": "Simple periodic checks (email, calendar, weather) don't need frontier model",
        }
    )
    opportunities.append(
        {
            "task": "Summarization & formatting tasks",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "Llama-3.2-1B-Instruct via Ollama",
            "estimatedSavings": "~$1-2/month",
            "reason": "Text formatting, summarization, and simple rewrites work well locally",
        }
    )
    opportunities.append(
        {
            "task": "Sub-agent coding tasks",
            "currentModel": "claude-sonnet-4-6",
            "suggestedModel": "DeepSeek-Coder-V2-Lite via Ollama",
            "estimatedSavings": "~$3-8/month",
            "reason": "Small, well-scoped coding subtasks can run on local coding models",
        }
    )

    return opportunities[:6]


def _get_cost_summary():
    """Calculate cost summary from metrics store.

    Windows come from ``clawmetry.cost_windows`` so this panel agrees with
    the budget panel, the cost-optimization route and the cloud snapshot.
    It used to compute its own: a fixed ``UTC+1`` "today" (no DST, wrong for
    every non-European user) plus ROLLING 7/30-day weeks and months, while
    every other cost surface used calendar windows. On a Saturday that alone
    made this panel's "week" span 8 calendar days against the cloud's 6.
    """
    from clawmetry.cost_windows import now_local, window_start_days

    now = now_local()
    today, week_start, month_start = window_start_days(now)

    costs = {"today": 0, "week": 0, "month": 0, "projected": 0}

    with _metrics_lock:
        for entry in metrics_store.get("cost", []):
            # Same timezone as the window boundaries above, or entries near
            # midnight land in a different day than the window they are being
            # compared against.
            entry_date = datetime.fromtimestamp(
                entry.get("timestamp", 0) / 1000, now.tzinfo
            ).strftime("%Y-%m-%d")
            entry_cost = entry.get("usd", 0)

            if entry_date == today:
                costs["today"] += entry_cost
            if entry_date >= week_start:
                costs["week"] += entry_cost
            if entry_date >= month_start:
                costs["month"] += entry_cost

    # Project monthly cost based on current daily average
    if costs["month"] > 0:
        # Project from month-to-date over the days actually elapsed in THIS
        # calendar month, then scale to the month's real length. The old form
        # divided by a rolling-30 window and multiplied by a flat 30.
        from calendar import monthrange
        from clawmetry.cost_windows import days_elapsed_in_month

        days_in_period = days_elapsed_in_month(now)
        daily_avg = costs["month"] / days_in_period
        costs["projected"] = daily_avg * monthrange(now.year, now.month)[1]

    return costs


def _detect_ollama():
    """Detect Ollama installation using multiple strategies."""
    import shutil

    # Strategy 1: shutil.which (respects PATH)
    if shutil.which("ollama"):
        return True
    # Strategy 2: Check common installation paths
    common_paths = [
        "/opt/homebrew/bin/ollama",  # macOS Homebrew (Apple Silicon)
        "/usr/local/bin/ollama",  # macOS Homebrew (Intel) / Linux manual
        "/usr/bin/ollama",  # Linux package manager
        os.path.expanduser("~/.ollama/ollama"),  # Custom install
    ]
    # Windows paths
    if os.name == "nt":
        common_paths.extend(
            [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Ollama\ollama.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Ollama\ollama.exe"),
            ]
        )
    for p in common_paths:
        if os.path.isfile(p):
            return True
    # Strategy 3: Try HTTP ping (ollama might be running even if binary not in PATH)
    try:
        import urllib.request

        req = urllib.request.Request("http://localhost:11434/api/version", method="GET")
        with urllib.request.urlopen(req, timeout=2) as resp:
            if resp.status == 200:
                return True
    except Exception:
        pass
    return False


def _check_ollama_availability():
    """Check if Ollama is running and what models are available."""
    try:
        import requests

        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        if response.status_code == 200:
            data = response.json()
            models = data.get("models", [])
            tool_capable_models = []

            for model in models:
                # Check if model supports tools (simplified check)
                model_name = model.get("name", "")
                # Common tool-capable models
                if any(
                    x in model_name.lower()
                    for x in ["llama3", "qwen", "gpt-oss", "mistral", "deepseek"]
                ):
                    tool_capable_models.append(model_name)

            return {
                "available": True,
                "count": len(tool_capable_models),
                "models": tool_capable_models[:10],  # Limit display
            }
    except Exception:
        pass

    # Fallback: use robust detection (binary found or HTTP reachable)
    if _detect_ollama():
        return {"available": True, "count": 0, "models": []}

    return {"available": False, "count": 0, "models": []}


def _generate_cost_recommendations(costs, local_models):
    """Generate cost optimization recommendations."""
    recommendations = []

    # High cost alerts
    if costs["today"] > 1.0:
        recommendations.append(
            {
                "title": "High Daily Cost",
                "description": f"Today's usage (${costs['today']:.3f}) is high. Consider using local models for routine tasks.",
                "priority": "high",
                "action": "Review recent expensive operations below",
            }
        )

    # Local model setup
    if not local_models["available"]:
        recommendations.append(
            {
                "title": "Install Local Models",
                "description": "Set up Ollama with local models to reduce API costs for formatting, simple lookups, and drafts.",
                "priority": "medium",
                "action": "curl -fsSL https://ollama.ai/install.sh | sh && ollama pull llama3.3",
            }
        )
    elif local_models["count"] < 2:
        recommendations.append(
            {
                "title": "Expand Local Model Selection",
                "description": "Add more local models for better task coverage and cost optimization.",
                "priority": "low",
                "action": "ollama pull qwen2.5-coder:32b",
            }
        )

    # Projected cost warning
    if costs["projected"] > 50.0:
        recommendations.append(
            {
                "title": "High Monthly Projection",
                "description": f"Projected monthly cost (${costs['projected']:.2f}) is high. Implement local model fallback urgently.",
                "priority": "high",
                "action": "Configure cost thresholds and local model routing",
            }
        )

    # Low-stakes task identification
    with _metrics_lock:
        recent_calls = metrics_store.get("tokens", [])[-100:]  # Last 100 calls
        high_cost_calls = [c for c in recent_calls if c.get("total", 0) > 10000]
        if len(high_cost_calls) > 20:
            recommendations.append(
                {
                    "title": "High Token Usage Detected",
                    "description": "Many recent calls use >10K tokens. Review if all require cloud models.",
                    "priority": "medium",
                    "action": "Implement task classification for local vs cloud routing",
                }
            )

    return recommendations


def _get_expensive_operations():
    """Get recent high-cost operations for analysis."""
    expensive_ops = []

    with _metrics_lock:
        # Combine cost and token data
        recent_tokens = metrics_store.get("tokens", [])[-50:]
        recent_costs = metrics_store.get("cost", [])[-50:]

        # Match tokens with costs by timestamp (approximate)
        for cost_entry in recent_costs:
            if cost_entry.get("usd", 0) > 0.01:  # Only show operations >$0.01
                timestamp = cost_entry.get("timestamp", 0)
                model = cost_entry.get("model", "unknown")
                cost = cost_entry.get("usd", 0)

                # Find matching token entry
                token_entry = None
                for t in recent_tokens:
                    if (
                        abs(t.get("timestamp", 0) - timestamp) < 5000
                    ):  # Within 5 seconds
                        if t.get("model", "") == model:
                            token_entry = t
                            break

                tokens = token_entry.get("total", 0) if token_entry else 0
                time_ago = datetime.fromtimestamp(timestamp / 1000).astimezone().strftime(
                    "%H:%M"
                )

                # Determine if this operation could be optimized
                can_optimize = False
                if tokens > 0:
                    # Simple heuristic: high token count with low complexity ratio might be local-model suitable
                    # This is a simplified check - in practice you'd analyze the actual request content
                    if (
                        tokens < 5000
                        and "gpt" not in model.lower()
                        and "simple" in model.lower()
                    ):
                        can_optimize = True

                expensive_ops.append(
                    {
                        "model": model,
                        "cost": cost,
                        "tokens": f"{tokens:,}" if tokens > 0 else "unknown",
                        "timeAgo": time_ago,
                        "canOptimize": can_optimize,
                    }
                )

    return sorted(expensive_ops, key=lambda x: x["cost"], reverse=True)[:10]


def _analyze_work_patterns():
    """Analyze recent work patterns from logs and metrics to detect repetitive tasks."""
    patterns = []

    try:
        # Analyze recent log files for repetitive patterns
        log_files = _get_recent_log_files(7)  # Last 7 days
        command_frequency = {}
        tool_frequency = {}
        error_patterns = {}

        for log_file in log_files:
            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue

                        # Track tool usage patterns
                        if "tool_call" in line and "exec" in line:
                            try:
                                if '"command"' in line:
                                    # Extract command from tool call
                                    import re

                                    cmd_match = re.search(
                                        r'"command":\s*"([^"]+)"', line
                                    )
                                    if cmd_match:
                                        cmd = cmd_match.group(1).split()[
                                            0
                                        ]  # First word only
                                        command_frequency[cmd] = (
                                            command_frequency.get(cmd, 0) + 1
                                        )
                            except Exception:
                                pass

                        # Track tool names
                        for tool in [
                            "curl",
                            "git",
                            "npm",
                            "systemctl",
                            "grep",
                            "find",
                            "ls",
                        ]:
                            if tool in line and "tool_call" in line:
                                tool_frequency[tool] = tool_frequency.get(tool, 0) + 1

                        # Track common error patterns
                        if "error" in line.lower() or "failed" in line.lower():
                            for pattern in [
                                "connection failed",
                                "timeout",
                                "not found",
                                "permission denied",
                            ]:
                                if pattern in line.lower():
                                    error_patterns[pattern] = (
                                        error_patterns.get(pattern, 0) + 1
                                    )

            except Exception:
                continue

        # Generate pattern insights
        # High-frequency commands
        for cmd, count in command_frequency.items():
            if count >= 5:  # Used 5+ times in the past week
                confidence = min(90, count * 10)  # Higher frequency = higher confidence
                priority = "high" if count >= 15 else "medium" if count >= 10 else "low"
                patterns.append(
                    {
                        "title": f'Frequent "{cmd}" command usage',
                        "description": f'Command "{cmd}" has been used {count} times in the past week. This might be a candidate for automation.',
                        "frequency": f"{count} times/week",
                        "confidence": confidence,
                        "priority": priority,
                        "type": "command",
                        "target": cmd,
                    }
                )

        # Repeated error handling
        for error, count in error_patterns.items():
            if count >= 3:
                patterns.append(
                    {
                        "title": f"Recurring error: {error}",
                        "description": f"This error pattern has occurred {count} times. Consider adding error handling automation.",
                        "frequency": f"{count} occurrences/week",
                        "confidence": 75,
                        "priority": "medium",
                        "type": "error",
                        "target": error,
                    }
                )

        # Check for Mission Control task patterns (only if MC_URL is configured)
        if MC_URL:
            try:
                mc_response = subprocess.run(
                    ["curl", "-s", f"{MC_URL}/api/tasks"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if mc_response.returncode == 0:
                    mc_data = json.loads(mc_response.stdout)
                    if "tasks" in mc_data:
                        task_types = {}
                        for task in mc_data["tasks"]:
                            title = task.get("title", "").lower()
                            for keyword in [
                                "deploy",
                                "fix",
                                "update",
                                "build",
                                "test",
                                "backup",
                            ]:
                                if keyword in title:
                                    task_types[keyword] = task_types.get(keyword, 0) + 1
                        for task_type, count in task_types.items():
                            if count >= 3:
                                patterns.append(
                                    {
                                        "title": f"Frequent {task_type} tasks",
                                        "description": f'You have {count} tasks involving "{task_type}". This could be automated.',
                                        "frequency": f"{count} tasks",
                                        "confidence": 80,
                                        "priority": "medium",
                                        "type": "task",
                                        "target": task_type,
                                    }
                                )
            except Exception:
                pass

    except Exception as e:
        # Add a debug pattern if analysis fails
        patterns.append(
            {
                "title": "Pattern analysis limited",
                "description": f"Could not fully analyze patterns: {str(e)}",
                "frequency": "unknown",
                "confidence": 10,
                "priority": "low",
                "type": "debug",
                "target": "analysis",
            }
        )

    return sorted(
        patterns,
        key=lambda x: (
            x["priority"] == "high",
            x["priority"] == "medium",
            x["confidence"],
        ),
        reverse=True,
    )


def _generate_automation_suggestions(patterns):
    """Generate concrete automation suggestions based on detected patterns."""
    suggestions = []

    for pattern in patterns:
        if pattern["type"] == "command" and pattern["target"]:
            cmd = pattern["target"]

            # Command-specific automation suggestions
            if cmd in ["curl", "git", "systemctl"]:
                suggestions.append(
                    {
                        "title": f"Automate {cmd} monitoring",
                        "description": f"Create a cron job to monitor and auto-fix common {cmd} operations.",
                        "type": "cron",
                        "implementation": f"# Add to cron: */15 * * * * /path/to/auto-{cmd}.sh",
                        "impact": "Medium - reduces manual monitoring",
                        "effort": "Low - single script creation",
                    }
                )

            elif cmd in ["npm", "git"]:
                suggestions.append(
                    {
                        "title": f"{cmd.upper()} automation skill",
                        "description": f"Create a skill that automates common {cmd} workflows with error handling.",
                        "type": "skill",
                        "implementation": f"Skills/{cmd}-automation/SKILL.md - wrapper with retry logic",
                        "impact": "High - automates entire workflow",
                        "effort": "Medium - requires skill development",
                    }
                )

        elif pattern["type"] == "error":
            error_type = pattern["target"]
            suggestions.append(
                {
                    "title": f"Auto-recovery for {error_type}",
                    "description": f'Create monitoring that detects "{error_type}" errors and attempts automatic recovery.',
                    "type": "cron",
                    "implementation": f"*/10 * * * * /scripts/auto-recover-{error_type.replace(' ', '-')}.sh",
                    "impact": "High - prevents manual intervention",
                    "effort": "Medium - requires error detection logic",
                }
            )

        elif pattern["type"] == "task":
            task_type = pattern["target"]
            if task_type in ["deploy", "build", "update"]:
                suggestions.append(
                    {
                        "title": f"CI/CD pipeline for {task_type}",
                        "description": f"Automate {task_type} tasks with GitHub Actions or cron-based pipeline.",
                        "type": "automation",
                        "implementation": f".github/workflows/{task_type}.yml or cron-based pipeline",
                        "impact": "Very High - eliminates manual tasks",
                        "effort": "High - requires pipeline setup",
                    }
                )

    # Add some universal automation suggestions
    suggestions.extend(
        [
            {
                "title": "Health monitoring cron",
                "description": "Create a cron job that monitors system health and alerts on issues.",
                "type": "cron",
                "implementation": "0 */6 * * * /scripts/health-check.sh | logger",
                "impact": "Medium - proactive issue detection",
                "effort": "Low - single monitoring script",
            },
            {
                "title": "Log rotation automation",
                "description": "Automate log cleanup to prevent disk space issues.",
                "type": "cron",
                "implementation": '0 2 * * 0 find /var/log -type f -name "*.log" -mtime +7 -delete',
                "impact": "Medium - prevents disk space issues",
                "effort": "Very Low - single command cron",
            },
            {
                "title": "Backup verification skill",
                "description": "Create a skill that verifies backup integrity and reports status.",
                "type": "skill",
                "implementation": "Skills/backup-monitor/SKILL.md - checks backup health",
                "impact": "High - ensures backup reliability",
                "effort": "Medium - requires backup checking logic",
            },
        ]
    )

    # Remove duplicates and limit to top suggestions
    seen_titles = set()
    unique_suggestions = []
    for suggestion in suggestions:
        if suggestion["title"] not in seen_titles:
            seen_titles.add(suggestion["title"])
            unique_suggestions.append(suggestion)

    return unique_suggestions[:8]  # Limit to 8 suggestions max


def _get_recent_log_files(days=7):
    """Get list of recent log files to analyze."""
    log_files = []

    if LOG_DIR and os.path.isdir(LOG_DIR):
        # OpenClaw/Moltbot logs
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            log_file = os.path.join(LOG_DIR, f"moltbot-{date}.log")
            if os.path.isfile(log_file):
                log_files.append(log_file)

    # Also check journalctl if available
    try:
        result = subprocess.run(
            [
                "journalctl",
                "--user",
                "-u",
                "moltbot-gateway",
                "--since",
                f"{days} days ago",
                "--no-pager",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Create temporary file with journalctl output for analysis
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".log", delete=False
            ) as f:
                f.write(result.stdout)
                log_files.append(f.name)
    except Exception:
        pass

    return log_files


# ── OTLP compatibility listener (issue #4780) ────────────────────────────
#
# The receiver has always been reachable at /v1/* on the dashboard port, but
# every OpenTelemetry SDK and collector defaults to http://localhost:4318. That
# gap meant an already-instrumented app could not be observed until someone
# discovered OTEL_EXPORTER_OTLP_ENDPOINT and pointed it at :8900 -- an env var
# between the user and "it just works".
#
# So we also listen on 4318, serving ONLY the receiver blueprint. A span
# arriving there takes the identical handler / decoder / store path as one
# arriving on the dashboard port; nothing about the mapping is duplicated.

# Conventional OTLP/HTTP port. Override with CLAWMETRY_OTLP_PORT (0 = pick an
# ephemeral port, which the tests use). CLAWMETRY_OTLP_PORT_DISABLE=1 turns the
# listener off for anyone who wants the port left alone.
_OTLP_COMPAT_DEFAULT_PORT = 4318
_otlp_compat_server = None


def _build_otlp_compat_app():
    """A minimal Flask app exposing the OTLP receiver and nothing else.

    Deliberately NOT the dashboard app: a second surface serving the UI and
    /api/* would widen what is reachable for no gain. Everything except /v1/*
    (and the small /api/otel-status probe on the same blueprint) 404s here.

    The main app's auth guard is registered too, so the loopback-trusted /
    token-required rule is one rule, not two: binding this listener somewhere
    other than loopback cannot silently open an unauthenticated ingest.
    """
    from flask import Flask as _Flask
    from routes.meta import bp_otel as _bp_otel

    otlp_app = _Flask("clawmetry_otlp_compat")
    otlp_app.register_blueprint(_bp_otel)
    otlp_app.before_request(_check_auth)
    return otlp_app


def _start_otlp_compat_listener(host=None, port=None, debug=False):
    """Serve the OTLP receiver on the conventional port in a daemon thread.

    Returns the waitress server (for tests) or ``None`` when the listener is
    disabled, unavailable, or the port is already held. Never raises: a machine
    already running an OTel Collector keeps its collector, and ClawMetry says so
    once rather than failing to boot.
    """
    global _otlp_compat_server
    if str(os.environ.get("CLAWMETRY_OTLP_PORT_DISABLE", "")).strip().lower() in (
        "1", "true", "yes",
    ):
        return None
    # Flask's debug reloader runs main() in BOTH the supervisor and the child.
    # Only the child serves the dashboard, so let it own the port; otherwise the
    # supervisor grabs 4318 and the child logs "already in use" on every reload.
    if debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return None
    if port is None:
        try:
            port = int(os.environ.get("CLAWMETRY_OTLP_PORT", _OTLP_COMPAT_DEFAULT_PORT))
        except (TypeError, ValueError):
            port = _OTLP_COMPAT_DEFAULT_PORT
    # Loopback by default even when the dashboard binds 0.0.0.0. Widening the
    # ingest surface has to be a deliberate act, not a side effect of the
    # dashboard's --host.
    host = host or os.environ.get("CLAWMETRY_OTLP_HOST", "127.0.0.1")

    import logging as _logging
    log = _logging.getLogger("clawmetry.dashboard")
    try:
        from waitress import create_server as _create_server
    except ImportError:
        log.debug("waitress missing; OTLP compat listener not started")
        return None
    try:
        server = _create_server(
            _build_otlp_compat_app(), host=host, port=port,
            threads=4, channel_timeout=60,
        )
    except OSError as e:
        # Port in use is the common, expected case: the user already runs an
        # OTel Collector. Not an error -- the dashboard port still serves /v1/*.
        log.info(
            "OTLP port %s:%s is already in use (%s); ClawMetry is still "
            "receiving OTLP on the dashboard port", host, port, e,
        )
        return None
    except Exception as e:
        log.warning("OTLP compat listener failed to start: %s", e)
        return None

    threading.Thread(
        target=server.run, name="clawmetry-otlp-4318", daemon=True,
    ).start()
    _otlp_compat_server = server
    log.info("OTLP receiver listening on http://%s:%s/v1/traces", host, port)
    return server


# ── CLI Entry Point ─────────────────────────────────────────────────────

BANNER = r"""
   ____ _                 __  __      _
  / ___| | __ ___      __|  \/  | ___| |_ _ __ _   _
 | |   | |/ _` \ \ /\ / /| |\/| |/ _ \ __| '__| | | |
 | |___| | (_| |\ V  V / | |  | |  __/ |_| |  | |_| |
  \____|_|\__,_| \_/\_/  |_|  |_|\___|\__|_|   \__, |
                                                |___/
                          v{version}

  [ClawMetry]  See your agent think

  Tabs: Overview ? ? Usage ? Sessions ? Crons ? Logs
        Memory ? ? Transcripts ? ? Flow
  Flow: Click nodes: ? Automation Advisor ? ? Cost Optimizer ? ?? Time Travel
"""

ARCHITECTURE_OVERVIEW = """\
🦞 ClawMetry {version} -- See your agent think.

  ┌─────────────────────┐              ┌─────────────────────┐              ┌─────────────────────┐
  │  🤖                 │  READS FILES │  🦞                 │  SHOWS YOU  │  📊                 │
  │  Your AI agents     │ ──────────->  │                     │ ──────────->  │                     │
  │  Any of 31 runtimes │              │  ClawMetry          │              │  Your browser       │
  │                     │              │  Parses logs +      │              │  localhost:{port}   │
  │  Running normally.  │              │  sessions.          │              │  Live dashboard     │
  │  Nothing changes.   │              │  Serves dashboard.  │              │                     │
  └─────────────────────┘              └─────────────────────┘              └─────────────────────┘

  Runs locally on the same machine as your agents. Your data never leaves your box.
  Docs: https://clawmetry.com/how-it-works
"""

HELP_TEXT = """\
🦞 ClawMetry {version} -- See your agent think.

Usage: clawmetry [command] [options]

Commands:
  start          Start ClawMetry as a background service (auto-starts on login)
  stop           Stop the background service
  restart        Restart the background service
  status         Show service status, port, and uptime
  uninstall      Remove the background service

Cloud:
  login                  Log in / sign up for ClawMetry Cloud (email or Google/GitHub)
  connect                Activate cloud sync with an API key (scripted/advanced)
  disconnect             Stop cloud sync and remove the account key
  doctor                 Diagnose cloud connectivity (DNS/proxy/TLS, detects
                         corporate TLS interception)
  --turn-on-cloud-sync   Resume cloud sync (keeps your login)
  --turn-off-cloud-sync  Pause cloud sync — nothing leaves this machine;
                         the local dashboard keeps working

Options:
  --port <port>        Port to listen on (default: 8900)
  --host <host>        Host to bind to (default: 127.0.0.1)
  --workspace <path>   OpenClaw workspace path (auto-detected)
  --name <name>        Your name in Flow visualization
  --no-debug           Disable Flask debug/auto-reload
  -v, --version        Show version
  -h, --help           Show this help

Examples:
  clawmetry start              Start as background service on port 8900
  clawmetry start --port 9000  Start on custom port
  clawmetry status             Check if running

Docs: https://docs.clawmetry.com
"""

# Windows has no /tmp, so the literal path resolved to C:\tmp and every read
# failed into the bare except below — _read_pid() always returned None, which
# is what silently disabled the stale-instance reclaim at startup (two dev
# servers could then bind the same port and requests would land on whichever
# Windows picked). tempfile.gettempdir() honours %TEMP% there; POSIX keeps the
# exact path it has always used so existing pid files stay discoverable.
PID_FILE = (
    os.path.join(_tempfile.gettempdir(), "clawmetry.pid")
    if os.name == "nt"
    else "/tmp/clawmetry.pid"
)
LAUNCHD_LABEL = "com.clawmetry.dashboard"
LAUNCHD_PLIST = os.path.expanduser(f"~/Library/LaunchAgents/{LAUNCHD_LABEL}.plist")
SYSTEMD_SERVICE = os.path.expanduser(
    "~/.config/systemd/user/clawmetry-dashboard.service"
)

# Sync daemon uses separate service names
SYNC_LAUNCHD_LABEL = "com.clawmetry.sync"
SYNC_LAUNCHD_PLIST = os.path.expanduser(
    f"~/Library/LaunchAgents/{SYNC_LAUNCHD_LABEL}.plist"
)
SYNC_SYSTEMD_SERVICE = os.path.expanduser(
    "~/.config/systemd/user/clawmetry-sync.service"
)


# ---------------------------------------------------------------------------
# Daemon helpers
# ---------------------------------------------------------------------------


def _get_script_path():
    """Return absolute path to the clawmetry executable / this script."""
    import shutil

    exe = shutil.which("clawmetry")
    if exe:
        return os.path.realpath(exe)
    return os.path.realpath(sys.argv[0])


def _write_pid(pid):
    with open(PID_FILE, "w") as f:
        f.write(str(pid))


def _read_pid():
    try:
        with open(PID_FILE) as f:
            return int(f.read().strip())
    except Exception:
        return None


def _is_pid_running(pid):
    # Delegates to the portable probe: os.kill(pid, 0) never raises on
    # Windows, so this used to report stale dashboard pids as running.
    from clawmetry.process_control import is_alive as _pid_alive

    return _pid_alive(pid)


def _is_macos():
    return sys.platform == "darwin"


def _is_linux():
    return sys.platform.startswith("linux")


def _launchd_running():
    import subprocess

    try:
        result = subprocess.run(
            ["launchctl", "list", LAUNCHD_LABEL], capture_output=True, text=True
        )
        return result.returncode == 0
    except Exception:
        return False


def _systemd_running():
    import subprocess

    try:
        result = subprocess.run(
            ["systemctl", "--user", "is-active", "--quiet", "clawmetry"],
            capture_output=True,
        )
        return result.returncode == 0
    except Exception:
        return False


def _service_running():
    if _is_macos():
        return _launchd_running()
    elif _is_linux():
        return _systemd_running()
    # Fallback: check PID file
    pid = _read_pid()
    return pid is not None and _is_pid_running(pid)


def _get_service_pid():
    """Try to get running PID from launchd/systemd/pid file."""
    if _is_macos():
        import subprocess

        try:
            result = subprocess.run(
                ["launchctl", "list", LAUNCHD_LABEL], capture_output=True, text=True
            )
            for line in result.stdout.splitlines():
                line = line.strip()
                if line and not line.startswith('"') and "\t" in line:
                    parts = line.split("\t")
                    if len(parts) >= 1:
                        try:
                            return int(parts[0])
                        except ValueError:
                            pass
        except Exception:
            pass
    elif _is_linux():
        import subprocess

        try:
            result = subprocess.run(
                ["systemctl", "--user", "show", "clawmetry", "--property=MainPID"],
                capture_output=True,
                text=True,
            )
            for line in result.stdout.splitlines():
                if line.startswith("MainPID="):
                    pid = int(line.split("=", 1)[1].strip())
                    return pid if pid > 0 else None
        except Exception:
            pass
    return _read_pid()


def _get_uptime_str(pid):
    try:
        import subprocess

        if _is_macos():
            result = subprocess.run(
                ["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True
            )
            return result.stdout.strip() or "?"
        else:
            result = subprocess.run(
                ["ps", "-o", "etime=", "-p", str(pid)], capture_output=True, text=True
            )
            return result.stdout.strip() or "?"
    except Exception:
        return "?"


def _read_cloud_token():
    """Resolve the cloud bearer the dashboard uses for /api/cloud-proxy/*.

    Two sources of truth (audit P0 #5, clawmetry-cloud#779):

      1. ``~/.openclaw/openclaw.json`` → ``clawmetry.cloudToken`` (legacy
         OpenClaw sidecar path; written by ``clawmetry connect``).
      2. ``~/.clawmetry/config.json`` → ``api_key`` (the daemon's own
         config, written by ``python -m clawmetry.sync`` once the node is
         paired). Validated by the ``cm_`` prefix.

    Without (2) the dashboard would 401 the entire Alerts UI even on
    machines where the daemon is fully cloud-paired but never had the
    OpenClaw sidecar config written.
    """
    # Source 1 — OpenClaw sidecar (existing path, kept first so an explicit
    # `clawmetry connect` write wins over the daemon-side copy).
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(cfg_path) as f:
            data = json.load(f)
        tok = (data.get("clawmetry", {}) or {}).get("cloudToken", "")
        if tok:
            return tok
    except Exception:
        pass
    # Source 2 — daemon's own config (audit P0 #5 fallback).
    daemon_cfg = os.path.expanduser("~/.clawmetry/config.json")
    try:
        with open(daemon_cfg) as f:
            data = json.load(f)
        tok = data.get("api_key", "")
        if isinstance(tok, str) and tok.startswith("cm_"):
            return tok
    except Exception:
        pass
    return None


def _write_cloud_token(token):
    cfg_path = os.path.expanduser("~/.openclaw/openclaw.json")
    try:
        with open(cfg_path) as f:
            data = json.load(f)
    except Exception:
        data = {}
    if "clawmetry" not in data:
        data["clawmetry"] = {}
    data["clawmetry"]["cloudToken"] = token
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w") as f:
        json.dump(data, f, indent=2)


# In-memory account-email cache for /api/cloud-cta/status. `fail_at` throttles
# cloud lookups on offline machines (retry at most once a minute) so opening
# the profile menu never blocks on a dead network for every click.
_ACCOUNT_EMAIL_CACHE = {"token": "", "email": "", "fail_at": 0.0}


def _account_email_for_token(token):
    """Resolve the sign-in email behind a cm_ key, '' if unknowable.

    The profile menu needs a "who am I" for cloud-OAuth accounts that hold
    no local license (license `sub` is empty there) — without this the
    header says "Not signed in" on a fully signed-in, cloud-connected node
    (founder report 2026-08-09). Resolution order:

      1. ``~/.clawmetry/config.json`` → ``account_email`` (written at
         connect time and by the claim watcher in clawmetry/sync.py).
      2. Cloud ``/api/cloud/account?token=`` (best-effort, cached; the
         result is persisted back into config.json when that file exists
         so restarts skip the network hop).

    Placeholder identities (``agent+<hash>@clawmetry.auto`` / ``.linked``)
    are reported as '' — they are internal pre-claim accounts, not
    something to show a human. Never raises.
    """
    if not token:
        return ""

    def _real(email):
        e = (email or "").strip()
        low = e.lower()
        if low.endswith("@clawmetry.auto") or low.endswith("@clawmetry.linked"):
            return ""
        return e

    daemon_cfg = os.path.expanduser("~/.clawmetry/config.json")
    try:
        with open(daemon_cfg) as f:
            cfg = json.load(f)
        # Only trust the stored email when it belongs to THIS key — after a
        # reconnect under a different account the old email would be stale.
        if cfg.get("api_key") == token:
            e = _real(cfg.get("account_email"))
            if e:
                return e
    except Exception:
        cfg = None

    if _ACCOUNT_EMAIL_CACHE["token"] == token:
        if _ACCOUNT_EMAIL_CACHE["email"]:
            return _ACCOUNT_EMAIL_CACHE["email"]
        if time.time() - _ACCOUNT_EMAIL_CACHE["fail_at"] < 60:
            return ""

    email = ""
    try:
        import urllib.parse as _up
        import urllib.request as _ur
        from clawmetry.endpoints import app_url as _app_url

        url = _app_url() + "/api/cloud/account?token=" + _up.quote(token)
        with _ur.urlopen(url, timeout=3) as resp:
            body = json.loads(resp.read() or b"{}")
        email = _real(body.get("email") if isinstance(body, dict) else "")
    except Exception:
        email = ""

    _ACCOUNT_EMAIL_CACHE.update(
        {"token": token, "email": email,
         "fail_at": 0.0 if email else time.time()}
    )
    if email and isinstance(cfg, dict) and cfg.get("api_key") == token:
        # Best-effort persist so the daemon and future dashboards see it
        # without a network hop; config.json stays 0o600 via save_config.
        try:
            from clawmetry.sync import save_config

            cfg["account_email"] = email
            save_config(cfg)
        except Exception:
            pass
    return email


def _selfhost_intent():
    """True when this install's recorded intent is self-host (local-only).

    Two signals, either wins: the nocloud marker (the daemon-facing egress
    switch), or a recorded selfhost_* choice in ~/.clawmetry/onboarding.json
    (survives even if some flow clears the marker). Used to pick the
    default rail for sign-in flows that did not explicitly choose one:
    founder report 2026-08-09 — a self-host install that signed back in
    via the profile menu rode the managed rail, which called
    enable_cloud() and silently started pushing snapshots. Identity and
    egress are separate choices; sign-in alone must never flip egress on.
    Never raises.
    """
    try:
        from clawmetry.config import is_cloud_disabled

        if is_cloud_disabled():
            return True
    except Exception:
        pass
    try:
        from routes.onboarding import _read_choice_file

        choice = str(_read_choice_file().get("choice", "")).strip().lower()
        return choice.startswith("selfhost")
    except Exception:
        return False


# ── One-click cloud connect via GitHub/Google OAuth (dashboard CTA) ────────────
# The local "Enable Cloud Sync" modal can sign the user up AND connect this node
# in one click. We reuse the same loopback browser-bridge as `clawmetry connect`:
# start a one-shot 127.0.0.1 listener, hand the cloud OAuth flow our port via
# cli_port=<port>, and the cloud callback redirects the freshly-minted cm_ key
# back to loopback. The key only ever travels over 127.0.0.1. What happens on
# capture depends on the bridge mode: "managed" runs the full connect (register
# node -> ~/.clawmetry/config.json -> enable cloud -> start daemon); "selfhost"
# (the onboarding gate's self-host card) keeps egress off and rides the trial
# rail instead. The dashboard polls _OAUTH_BRIDGE for status.
_OAUTH_BRIDGE = {"status": "idle", "provider": "", "mode": "", "node_id": "",
                 "enc_key": "", "trial": "", "error": ""}


def _persist_identity_with_key(api_key):
    """Register the account/node for a verified cm_ key and persist it.

    The shared identity half of both connect flavours: validate/register the
    node (best-effort — network hiccups still save config so it syncs once
    reachable), preserve or auto-generate the E2E encryption key, write
    ~/.clawmetry/config.json, and mirror the token into openclaw.json (so
    the dashboard cloud-proxy works). Deliberately does NOT touch the
    nocloud marker or the daemon — callers own the egress decision.
    Returns (node_id, enc_key).
    """
    import platform
    import socket
    from clawmetry.sync import validate_key, save_config, generate_encryption_key

    cfg_path = os.path.expanduser("~/.clawmetry/config.json")
    saved_node_id, saved_enc = "", ""
    try:
        with open(cfg_path) as _f:
            _c = json.load(_f)
        saved_node_id = _c.get("node_id", "")
        saved_enc = _c.get("encryption_key", "")
    except Exception:
        pass

    hostname = socket.gethostname()
    try:
        result = validate_key(api_key, hostname=hostname, existing_node_id=saved_node_id)
        node_id = result.get("node_id") or saved_node_id or hostname
    except Exception:
        node_id = saved_node_id or hostname

    enc_key = saved_enc or generate_encryption_key()
    config = {
        "api_key": api_key,
        "node_id": node_id,
        "platform": platform.system(),
        "connected_at": __import__("datetime").datetime.now().isoformat(),
        "encryption_key": enc_key,
    }
    # Resolve + store the sign-in email now, while we know the network is up
    # (we just OAuth'd through it) — the profile menu reads it via
    # /api/cloud-cta/status and must not show "Not signed in" on a
    # signed-in node (founder report 2026-08-09).
    try:
        _ACCOUNT_EMAIL_CACHE.update({"token": "", "email": "", "fail_at": 0.0})
        acct_email = _account_email_for_token(api_key)
        if acct_email:
            config["account_email"] = acct_email
    except Exception:
        pass
    save_config(config)
    try:
        _write_cloud_token(api_key)
    except Exception:
        pass
    return node_id, enc_key


def _activate_trial_for_key(api_key) -> str:
    """Mint-or-reuse the account's 7-day Pro trial for ``api_key``.

    Mirrors ``clawmetry.cli._activate_signup_trial`` — same
    ``/api/license/trial/signup`` endpoint, same idempotent server
    semantics — but takes the key as an argument so in-process pairing
    paths (dashboard cloud modal OTP, OAuth loopback bridge) can call it
    without having to first round-trip through
    ``~/.clawmetry/config.json``. Returns
    ``'active' | 'expired' | 'unavailable'`` for the caller to surface;
    every failure path returns ``'unavailable'`` (never raises).

    Founder ask 2026-08-12: cloud users MUST get the same 7-day Pro
    trial that self-host users get on sign-in, so they can experience
    the full product before deciding to pay. Previously the cloud rail
    only enabled sync and left the account on FREE.
    """
    if not (api_key or "").startswith("cm_"):
        return "unavailable"
    try:
        import urllib.request as _ur
        from clawmetry import license as _lic

        req = _ur.Request(
            _lic._cloud_base() + "/api/license/trial/signup",
            data=json.dumps({"api_key": api_key}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with _ur.urlopen(req, timeout=15) as resp:
            body = json.loads(resp.read().decode())
        if not (isinstance(body, dict) and body.get("ok")):
            return "unavailable"
        if body.get("expired"):
            return "expired"
        if not body.get("key"):
            return "unavailable"
        ok, _msg = _lic.activate(body["key"], node_id=_lic._node_id())
        return "active" if ok else "unavailable"
    except Exception:
        return "unavailable"


def _full_connect_with_key(api_key):
    """Register this node with a verified cm_ key and start syncing.

    Mirrors the non-interactive parts of `clawmetry connect`: persist the
    identity (_persist_identity_with_key), mint-or-reuse the account's
    7-day Pro trial (same rail as the CLI's ``_activate_signup_trial``
    and as ``_selfhost_signin_with_key``), opt into egress, and ensure
    the sync daemon is running. Returns (node_id, enc_key, trial) where
    trial is ``'active' | 'expired' | 'unavailable'``. Never raises for
    non-fatal issues.
    """
    node_id, enc_key = _persist_identity_with_key(api_key)

    # Mint-or-reuse the 7-day Pro trial so cloud users get the same
    # "unlock every runtime for 7 days" onboarding self-host already
    # gets. Founder ask 2026-08-12 — without this the cloud rail was
    # asymmetric: self-host signup started the trial, cloud signup did
    # not, so cloud users couldn't experience the full product before
    # the paywall. Runs BEFORE _restart_sync_daemon so the daemon sees
    # the freshly activated license on its first poll.
    trial = _activate_trial_for_key(api_key)

    # Clear the local-only marker so the daemon actually pushes to cloud. A
    # local-only install writes ~/.clawmetry/nocloud; without this the connect
    # succeeds but the daemon keeps running LOCAL-ONLY and nothing reaches the
    # cloud (the "0 nodes after Enable Cloud Sync" bug).
    try:
        from clawmetry.config import enable_cloud as _enable_cloud
        _enable_cloud()
    except Exception:
        pass

    # (Re)start the sync daemon so it re-reads the new key AND re-evaluates
    # cloud mode. If it is already running in local-only mode, merely "starting
    # if absent" would leave it local-only forever, so we restart unconditionally.
    _restart_sync_daemon()

    return node_id, enc_key, trial


def _restart_sync_daemon():
    """Restart the sync daemon so it re-reads ~/.clawmetry/config.json.

    Cross-platform: launchctl kickstart on macOS, systemctl restart on
    Linux, kill+relaunch elsewhere. Best-effort, never raises — callers
    (cloud connect, E2E key regenerate) proceed either way since the config
    file write already succeeded and a stale in-memory daemon just means
    the next natural restart picks up the change.
    """
    try:
        if _is_macos():
            if os.path.exists(SYNC_LAUNCHD_PLIST):
                subprocess.run(["launchctl", "kickstart", "-k",
                                f"gui/{os.getuid()}/{SYNC_LAUNCHD_LABEL}"],
                               capture_output=True)
            else:
                _start_daemon_background()
        elif _is_linux():
            _ensure_systemd_service()
            subprocess.run(_systemctl_cmd("restart", "clawmetry-sync"), capture_output=True)
        else:
            if _is_sync_running():
                _kill_all_sync_procs()
            _start_daemon_background()
    except Exception:
        pass


def _selfhost_signin_with_key(api_key):
    """Self-host sign-in: identity without egress, then the trial rail.

    Mirrors `clawmetry connect` answered with keep-local (identity is what
    unlocks runtimes; egress is a separate choice): touch the nocloud
    marker BEFORE persisting the key — the daemon must never observe a
    cm_ key without the marker, or it would happily start pushing — then
    register the identity and mint-or-reuse the account's 7-day trial via
    /api/license/trial/signup (idempotent server-side, same rail as the
    CLI) and activate it locally. Returns (node_id, trial) where trial is
    'active' | 'expired' | 'unavailable'.
    """
    try:
        from clawmetry.config import NOCLOUD_MARKER_PATH as _marker
        import pathlib as _pl

        _p = _pl.Path(str(_marker))
        _p.parent.mkdir(parents=True, exist_ok=True)
        _p.touch(exist_ok=True)
    except Exception:
        pass

    node_id, _enc = _persist_identity_with_key(api_key)

    # Same trial rail as _full_connect_with_key (cloud) and
    # clawmetry.cli._activate_signup_trial — mint-or-reuse the 7-day
    # Pro trial. Delegated to the shared helper so cloud + self-host
    # never drift on trial semantics again (founder ask 2026-08-12).
    trial = _activate_trial_for_key(api_key)

    # Same as the email-OTP trial path: make sure the local ingest daemon is
    # running (it stays local-only under the marker written above).
    try:
        from routes.trial import _ensure_local_daemon

        _ensure_local_daemon()
    except Exception:
        pass
    return node_id, trial


def _start_oauth_bridge(provider, mode="managed"):
    """Start the loopback OAuth bridge and return the cloud start URL (or None).

    The caller (dashboard JS) opens the returned URL in a new browser tab. A
    background thread captures the loopback callback and updates the
    module-level _OAUTH_BRIDGE the status route reports. mode picks what
    happens with the captured key: "managed" runs _full_connect_with_key
    (register node + enable cloud sync); "selfhost" runs
    _selfhost_signin_with_key (identity + local trial, egress stays off).
    """
    import http.server
    import threading
    import time as _time
    import urllib.parse as _uparse

    global _OAUTH_BRIDGE
    provider = (provider or "").lower()
    mode = "selfhost" if (mode or "").lower() == "selfhost" else "managed"
    if provider not in ("github", "google"):
        _OAUTH_BRIDGE = {"status": "error", "provider": provider, "mode": mode,
                         "node_id": "", "enc_key": "", "trial": "",
                         "error": "Unsupported provider"}
        return None

    from clawmetry.endpoints import app_url as _resolve_app_url
    app_base = _resolve_app_url()
    captured = {}

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            params = _uparse.parse_qs(_uparse.urlparse(self.path).query)
            captured["token"] = (params.get("token") or [""])[0]
            ok = captured["token"].startswith("cm_")
            msg = ("You're connected. Return to the ClawMetry dashboard."
                   if ok else "Sign-in failed. Return to the dashboard and use email instead.")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>ClawMetry</title></head>"
                 "<body style='font-family:sans-serif;background:#0b0f1a;color:#e2e8f0;display:flex;"
                 "align-items:center;justify-content:center;height:100vh;margin:0'>"
                 "<div style='text-align:center'><div style='font-size:40px'>\U0001F99E</div>"
                 "<h2 style='font-weight:700'>" + msg + "</h2></div></body></html>").encode("utf-8")
            )

        def log_message(self, *args):  # silence default stderr request logging
            pass

    try:
        srv = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    except OSError:
        _OAUTH_BRIDGE = {"status": "error", "provider": provider, "mode": mode,
                         "node_id": "", "enc_key": "", "trial": "",
                         "error": "Could not start local listener"}
        return None

    port = srv.server_address[1]
    _OAUTH_BRIDGE = {"status": "waiting", "provider": provider, "mode": mode,
                     "node_id": "", "enc_key": "", "trial": "", "error": ""}

    def _run():
        global _OAUTH_BRIDGE
        srv.timeout = 1
        deadline = _time.time() + 300
        try:
            while "token" not in captured and _time.time() < deadline:
                srv.handle_request()
        finally:
            srv.server_close()
        tok = captured.get("token", "")
        if not tok.startswith("cm_"):
            _OAUTH_BRIDGE = {"status": "error", "provider": provider, "mode": mode,
                             "node_id": "", "enc_key": "", "trial": "",
                             "error": "Sign-in was not completed."}
            return
        try:
            if mode == "selfhost":
                node_id, trial = _selfhost_signin_with_key(tok)
                _OAUTH_BRIDGE = {"status": "connected", "provider": provider,
                                 "mode": mode, "node_id": node_id, "enc_key": "",
                                 "trial": trial, "error": ""}
            else:
                node_id, enc_key, trial = _full_connect_with_key(tok)
                _OAUTH_BRIDGE = {"status": "connected", "provider": provider,
                                 "mode": mode, "node_id": node_id,
                                 "enc_key": enc_key, "trial": trial, "error": ""}
        except Exception as e:  # pragma: no cover - defensive
            _OAUTH_BRIDGE = {"status": "error", "provider": provider, "mode": mode,
                             "node_id": "", "enc_key": "", "trial": "",
                             "error": str(e)[:200]}

    threading.Thread(target=_run, daemon=True).start()
    return f"{app_base}/api/oauth/{provider}/start?cli_port={port}"


def _build_plist(python_exe, script_path, port, host, log_path="/tmp/clawmetry.log"):
    extra = []
    if host != "127.0.0.1":
        extra += ["<string>--host</string>", f"<string>{host}</string>"]
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>{LAUNCHD_LABEL}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_exe}</string>
        <string>{script_path}</string>
        <string>--no-debug</string>
        <string>--port</string>
        <string>{port}</string>
        {"".join(extra)}
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{log_path}</string>
    <key>StandardErrorPath</key>
    <string>{log_path}</string>
</dict>
</plist>
"""


def _build_systemd_unit(python_exe, script_path, port, host):
    extra = f" --host {host}" if host != "127.0.0.1" else ""
    return f"""[Unit]
Description=ClawMetry Dashboard
After=network.target

[Service]
ExecStart={python_exe} {script_path} --no-debug --port {port}{extra}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""


# ---------------------------------------------------------------------------
# CLI subcommands
# ---------------------------------------------------------------------------


def cmd_start(args):
    """Start ClawMetry as a background daemon."""
    import subprocess

    port = args.port
    host = args.host
    python_exe = sys.executable
    script_path = _get_script_path()

    try:
        print(ARCHITECTURE_OVERVIEW.format(version=__version__, port=port))
    except (ValueError, OSError):
        pass
    try:
        print("Starting dashboard...")
    except (ValueError, OSError):
        pass

    # Before loading daemon: if port is busy, only kill if it's our own stale process
    import socket as _socket

    _s = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    _port_busy = _s.connect_ex(("127.0.0.1", port)) == 0
    _s.close()
    if _port_busy:
        _old_pid = None
        try:
            with open(PID_FILE) as _pf:
                _old_pid = int(_pf.read().strip())
        except Exception:
            pass
        if _old_pid:
            try:
                import subprocess as _sp

                _r = _sp.run(
                    ["ps", "-p", str(_old_pid), "-o", "command="],
                    capture_output=True,
                    text=True,
                )
                _cmd = _r.stdout
                if "clawmetry" in _cmd or "dashboard.py" in _cmd:
                    import signal as _signal

                    os.kill(_old_pid, _signal.SIGTERM)
                    import time as _time

                    _time.sleep(1)
                else:
                    print(
                        f"❌ Port {port} is in use by another application. Choose a different port with --port."
                    )
                    sys.exit(1)
            except Exception:
                pass
        else:
            print(
                f"❌ Port {port} is in use by another application. Choose a different port with --port."
            )
            sys.exit(1)

    if _is_macos():
        # Write plist
        plist_content = _build_plist(python_exe, script_path, port, host)
        os.makedirs(os.path.dirname(LAUNCHD_PLIST), exist_ok=True)
        with open(LAUNCHD_PLIST, "w") as f:
            f.write(plist_content)

        # Unload if already loaded (ignore errors)
        subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
        result = subprocess.run(
            ["launchctl", "load", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to load service: {result.stderr.strip()}")
            sys.exit(1)

        import time

        time.sleep(1)
        if _launchd_running():
            print(f"[ok] ClawMetry started  ->  http://localhost:{port}")
            print("   Auto-starts on login - logs: /tmp/clawmetry.log")
            print("   Stop with: clawmetry stop")
        else:
            print(
                "[warn]  Service loaded but may still be starting. Check: clawmetry status"
            )

    elif _is_linux():
        unit_content = _build_systemd_unit(python_exe, script_path, port, host)
        os.makedirs(os.path.dirname(SYSTEMD_SERVICE), exist_ok=True)
        with open(SYSTEMD_SERVICE, "w") as f:
            f.write(unit_content)

        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "clawmetry"], capture_output=True
        )
        result = subprocess.run(
            _systemctl_cmd("restart"), capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"❌ Failed to start service: {result.stderr.strip()}")
            sys.exit(1)

        import time

        time.sleep(1)
        if _systemd_running():
            print(f"[ok] ClawMetry started  ->  http://localhost:{port}")
            print("   Auto-starts on login - logs: journalctl --user -u clawmetry -f")
            print("   Stop with: clawmetry stop")
        else:
            print(
                "[warn]  Service started but may still be initialising. Check: clawmetry status"
            )
    else:
        print(
            "[warn]  Daemon mode not supported on this OS. Running in foreground instead."
        )
        _run_server(args)


def cmd_stop(args):
    """Stop the ClawMetry dashboard daemon (sync keeps running)."""
    import subprocess

    if _is_macos():
        if not os.path.exists(LAUNCHD_PLIST):
            # Try legacy service name
            _old = os.path.expanduser("~/Library/LaunchAgents/com.clawmetry.plist")
            if os.path.exists(_old):
                subprocess.run(["launchctl", "unload", _old], capture_output=True)
                print("[ok] Stopped legacy ClawMetry service.")
            else:
                print(
                    "ℹ️  No service file found. ClawMetry may not be installed as a service."
                )
            sys.exit(0)
        result = subprocess.run(
            ["launchctl", "unload", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry dashboard stopped. Cloud sync still running.")
        else:
            print(
                f"[warn]  {result.stderr.strip() or 'Service may already be stopped.'}"
            )
    elif _is_linux():
        # Stop dashboard service (new or legacy name)
        result = subprocess.run(
            _systemctl_cmd("stop", "clawmetry-dashboard"),
            capture_output=True,
            text=True,
        )
        # Also try legacy name
        subprocess.run(_systemctl_cmd("stop", "clawmetry"), capture_output=True)
        if result.returncode == 0:
            print("[ok] ClawMetry dashboard stopped. Cloud sync still running.")
        else:
            print(
                f"[warn]  {result.stderr.strip() or 'Service may already be stopped.'}"
            )
    else:
        # Fallback: kill via PID file
        pid = _read_pid()
        if pid and _is_pid_running(pid):
            os.kill(pid, 15)  # SIGTERM
            print(f"[ok] Sent SIGTERM to PID {pid}.")
        else:
            print("ℹ️  No running ClawMetry process found.")


def cmd_restart(args):
    """Restart the ClawMetry dashboard daemon (sync keeps running)."""
    import subprocess

    if _is_macos():
        if not os.path.exists(LAUNCHD_PLIST):
            print("ℹ️  No service installed. Use: clawmetry start")
            sys.exit(1)
        subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
        result = subprocess.run(
            ["launchctl", "load", LAUNCHD_PLIST], capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry restarted.")
        else:
            print(f"❌ {result.stderr.strip()}")
            sys.exit(1)
    elif _is_linux():
        result = subprocess.run(
            _systemctl_cmd("restart"), capture_output=True, text=True
        )
        if result.returncode == 0:
            print("[ok] ClawMetry restarted.")
        else:
            print(f"❌ {result.stderr.strip()}")
            sys.exit(1)
    else:
        print("[warn]  Daemon mode not supported on this OS.")


def cmd_status(args):
    """Show ClawMetry service status."""
    running = _service_running()
    pid = _get_service_pid() if running else None
    uptime = _get_uptime_str(pid) if pid else "--"
    token = _read_cloud_token()
    port = args.port

    if _is_macos():
        svc_type = "launchd"
    elif _is_linux():
        svc_type = "systemd"
    else:
        svc_type = "process"

    status_icon = "[ok] Running" if running else "❌ Stopped"
    cloud_status = "[ok] Connected" if token else "❌ Not connected"

    print(f"""
🦞 ClawMetry Status

  Service:   {status_icon} ({svc_type})
  Port:      {port}
  PID:       {pid or "--"}
  Uptime:    {uptime}
  URL:       http://localhost:{port}
  Version:   {__version__}
  Cloud:     {cloud_status}
""")


def _kill_all_sync_procs():
    """Kill ALL running clawmetry sync processes (any platform)."""
    import subprocess
    import signal

    try:
        subprocess.run(
            ["pkill", "-9", "-f", "clawmetry.*sync"], capture_output=True, timeout=5
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    pid = _read_pid()
    if pid and _is_pid_running(pid):
        try:
            # signal.SIGKILL does not exist on Windows (AttributeError);
            # SIGTERM maps to TerminateProcess there, same hard-kill intent.
            os.kill(pid, getattr(signal, "SIGKILL", signal.SIGTERM))
        except OSError:
            pass


def _is_root():
    return os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _systemctl_cmd(action, service="clawmetry-dashboard"):
    """Build systemctl command -- omit --user when running as root."""
    if _is_root():
        return ["systemctl", action, service] if service else ["systemctl", action]
    return (
        ["systemctl", "--user", action, service]
        if service
        else ["systemctl", "--user", action]
    )


def _start_daemon_background():
    """Start sync daemon as a background process (fallback for non-service setups)."""
    import subprocess
    import pathlib as _pl

    # Without a config the spawned daemon crash-loops (load_config raises)
    # and the local store never fills; and `python -m` puts the CWD on
    # sys.path, so a dashboard launched from a source checkout would spawn
    # the repo's (possibly stale) sync.py instead of the installed wheel.
    try:
        from clawmetry.sync import ensure_local_config
        ensure_local_config()
    except Exception:
        pass
    spawn_kwargs = {"cwd": os.path.expanduser("~")}
    if os.name == "nt":
        # start_new_session is POSIX-only and silently no-ops on Windows:
        # the daemon stayed tied to this console (killed when it closes)
        # and, when the dashboard itself runs hidden, python.exe popped a
        # visible console window. Mirror cli.py _start_subprocess.
        spawn_kwargs["creationflags"] = (
            subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        )
    else:
        spawn_kwargs["start_new_session"] = True
    # Output goes to ~/.clawmetry/sync.log, not devnull. cmd_connect's own
    # failure path already tells the user to `cat ~/.clawmetry/sync.log` -- a
    # file nothing ever wrote -- so a daemon that died on startup did so
    # invisibly (#5740).
    cm_dir = _pl.Path.home() / ".clawmetry"
    cm_dir.mkdir(parents=True, exist_ok=True)
    log_path = cm_dir / "sync.log"
    try:
        log_fh = open(log_path, "a", buffering=1)
    except OSError:
        log_fh = open(os.devnull, "w")
    proc = subprocess.Popen(
        [sys.executable, "-m", "clawmetry.sync"],
        stdout=log_fh,
        stderr=subprocess.STDOUT,
        **spawn_kwargs,
    )
    # Deliberately NOT writing sync.pid here. That file is the daemon's
    # singleton lock and the daemon authors it itself, together with the
    # identity record `_lock_holder_verdict` checks. A pid file written by
    # this process carries no such record, so the daemon has to treat its own
    # lock as stale and reclaim it before it can start -- work that only
    # exists because we wrote the file.
    print_pid = proc.pid
    try:
        rc = proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        rc = None
    if rc is None:
        print(f"  Sync daemon started (background, PID {print_pid})")
        return
    tail = ""
    try:
        lines = log_path.read_text(errors="replace").strip().splitlines()
        tail = lines[-1][:160] if lines else ""
    except Exception:
        pass
    print(f"  Sync daemon exited immediately (exit {rc}); see {log_path}"
          + (f"\n    {tail}" if tail else ""))


def _is_sync_running():
    """Check if any clawmetry sync process is running."""
    import subprocess

    try:
        r = subprocess.run(
            ["pgrep", "-f", "clawmetry.*sync"], capture_output=True, timeout=3
        )
        return r.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _ensure_systemd_service():
    """Create systemd service file if needed (supports root and user mode)."""
    import pathlib as _pl
    import subprocess

    if _is_root():
        svc_dir = _pl.Path("/etc/systemd/system")
    else:
        svc_dir = _pl.Path.home() / ".config" / "systemd" / "user"
    svc_path = svc_dir / "clawmetry-sync.service"
    svc_dir.mkdir(parents=True, exist_ok=True)
    python_bin = sys.executable
    home = _pl.Path.home()
    target = "multi-user.target" if _is_root() else "default.target"
    svc_content = f"""[Unit]
Description=ClawMetry Sync Daemon
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart={python_bin} -m clawmetry.sync
Restart=always
RestartSec=10
Environment=HOME={home}

[Install]
WantedBy={target}
"""
    svc_path.write_text(svc_content)
    if _is_root():
        subprocess.run(["systemctl", "daemon-reload"], capture_output=True)
        subprocess.run(["systemctl", "enable", "clawmetry-sync"], capture_output=True)
    else:
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "clawmetry-sync"], capture_output=True
        )


def cmd_connect(args):
    """Connect to ClawMetry Cloud."""
    import subprocess
    import pathlib

    print()
    print("ClawMetry Cloud Connect")
    print()

    # Stop existing sync processes (but leave dashboard running)
    _kill_all_sync_procs()
    if _is_macos() and os.path.exists(SYNC_LAUNCHD_PLIST):
        subprocess.run(["launchctl", "unload", SYNC_LAUNCHD_PLIST], capture_output=True)
    elif _is_linux():
        subprocess.run(_systemctl_cmd("stop", "clawmetry-sync"), capture_output=True)
    print("  Stopped existing sync daemon")

    token = getattr(args, "key", None) or ""
    if not token:
        print("  1. Go to: https://clawmetry.com/connect")
        print("  2. Sign in and copy your API key (starts with cm_)")
        print()
        try:
            token = input("  Paste your API key: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nCancelled.")
            sys.exit(0)

    if not token.startswith("cm_"):
        print("Invalid key -- must start with cm_")
        sys.exit(1)

    # Clear old sync state so new account gets full initial sync
    state_file = pathlib.Path.home() / ".clawmetry" / "sync-state.json"
    if state_file.exists():
        state_file.unlink()
        print("  Cleared previous sync state")

    _write_cloud_token(token)
    # Opt-in to cloud: clear any local-only marker so the daemon pushes.
    try:
        from clawmetry.config import enable_cloud as _enable_cloud
        if _enable_cloud():
            print("  Re-enabled cloud sync (was local-only)")
    except Exception:
        pass
    print()
    print(
        f"  Connected! View your fleet at: https://app.clawmetry.com/fleet/?token={token}"
    )
    print()

    # Install + start service
    if _is_macos():
        if os.path.exists(LAUNCHD_PLIST):
            subprocess.run(["launchctl", "load", LAUNCHD_PLIST], capture_output=True)
            subprocess.run(["launchctl", "start", LAUNCHD_LABEL], capture_output=True)
            print("  Sync daemon started (launchd)")
        else:
            try:
                cmd_start(type("Args", (), {})())
            except SystemExit:
                _start_daemon_background()
    elif _is_linux():
        _ensure_systemd_service()
        subprocess.run(_systemctl_cmd("restart", "clawmetry-sync"), capture_output=True)
        print("  Sync daemon started (systemd)")
    else:
        _start_daemon_background()

    # Verify after 3s
    import time

    time.sleep(3)
    if _is_sync_running():
        print("  Sync daemon is running -- your node will appear in ~60 seconds")
    else:
        # Last resort: start in background
        print("  Service didn't start, trying background mode...")
        _start_daemon_background()
        time.sleep(2)
        if _is_sync_running():
            print("  Sync daemon is running -- your node will appear in ~60 seconds")
        else:
            print("  Could not start daemon. Check: cat ~/.clawmetry/sync.log")


def cmd_uninstall(args):
    """Stop and remove the ClawMetry service."""
    import subprocess

    print("🗑️  Uninstalling ClawMetry service...")

    if _is_macos():
        if os.path.exists(LAUNCHD_PLIST):
            subprocess.run(["launchctl", "unload", LAUNCHD_PLIST], capture_output=True)
            os.remove(LAUNCHD_PLIST)
            print(f"  Removed: {LAUNCHD_PLIST}")
        else:
            print("  No launchd service found.")
    elif _is_linux():
        subprocess.run(_systemctl_cmd("stop"), capture_output=True)
        subprocess.run(_systemctl_cmd("disable"), capture_output=True)
        if os.path.exists(SYSTEMD_SERVICE):
            os.remove(SYSTEMD_SERVICE)
            print(f"  Removed: {SYSTEMD_SERVICE}")
        subprocess.run(["systemctl", "--user", "daemon-reload"], capture_output=True)
    else:
        print("  Daemon mode not supported on this OS.")

    # Remove PID file if present
    if os.path.exists(PID_FILE):
        os.remove(PID_FILE)

    print("[ok] ClawMetry service removed.")


_SERVER_HOST = None  # populated by _run_server; routes/meta.py reads this for the
                     # /api/auth/detected-token bind-host gate.


def _print_login_url_banner(port, host, token):
    """Print a one-click /auth?token= URL when GATEWAY_TOKEN is set (#1356 PR-D).

    Behavior:
      - If token is empty/None -> no-op (preserves prior banner output).
      - If host binds publicly (0.0.0.0 / ::), still print but reference
        ``localhost`` so the link only works from the local machine.
      - Always uses the URL framing (never logs the bare token alone).
    """
    if not token:
        return
    # Always frame the token inside the /auth URL; never print the bare token.
    # 0.0.0.0 / :: are bind-all sentinels; the user clicks from localhost.
    public_binds = ("0.0.0.0", "::", "")
    display_host = "localhost" if host in public_binds else host
    url = f"http://{display_host}:{port}/auth?token={token}"
    print(f"  -> {url}  (one-click sign-in)")


def _run_server(args):
    global _SERVER_HOST
    _SERVER_HOST = getattr(args, "host", None)
    import sys as _sys

    # Windows: guard against closed/detached stdout/stderr before Flask or
    # click try to use them.  Two scenarios cause problems:
    #
    #   1. pythonw.exe / Start-Process / GUI launchers close the standard
    #      handles at startup.  click._winconsole._is_console() calls
    #      f.fileno() on sys.stdout, which raises:
    #        ValueError: I/O operation on closed file
    #      (reported in GH#264, reproduced on Python 3.11 Windows 10/11)
    #
    #   2. Normal CMD terminal with CP1252 encoding: box-drawing chars and
    #      emoji crash with UnicodeEncodeError.
    #
    # Strategy:
    #   a) Try fileno() first — if it raises, the stream is closed/detached;
    #      replace with a devnull sink so click/Flask banners never crash.
    #   b) If the stream is open, reconfigure() to UTF-8 (Python 3.7+).
    if _sys.platform == "win32":
        import io as _io

        for _attr in ("stdout", "stderr"):
            _stream = getattr(_sys, _attr, None)
            if _stream is None:
                # Completely absent — attach a null sink
                try:
                    setattr(_sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(_sys, _attr, _io.StringIO())
                continue
            try:
                _stream.fileno()  # raises ValueError/OSError when closed
            except (AttributeError, ValueError, OSError):
                # Stream is closed or has no real file descriptor.
                # Replace with devnull so click._winconsole never calls fileno().
                try:
                    setattr(_sys, _attr, open(os.devnull, "w", encoding="utf-8"))
                except OSError:
                    setattr(_sys, _attr, _io.StringIO())
                continue
            # Stream is open — reconfigure to UTF-8 to avoid CP1252 issues.
            try:
                _stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, Exception):
                pass
    """Start the Flask server (foreground). Called by foreground mode and cmd_start on unsupported OS."""
    detect_config(args)
    _load_gw_config()

    # Parse --monitor-service flags
    global EXTRA_SERVICES, MC_URL
    for svc_spec in args.monitor_service:
        if ":" in svc_spec:
            name, port_str = svc_spec.rsplit(":", 1)
            try:
                EXTRA_SERVICES.append(
                    {"name": name.strip(), "port": int(port_str.strip())}
                )
            except ValueError:
                print(
                    f"[warn]  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)"
                )
        else:
            print(
                f"[warn]  Invalid --monitor-service format: {svc_spec} (expected NAME:PORT)"
            )

    if args.mc_url:
        MC_URL = args.mc_url
    elif not MC_URL:
        MC_URL = os.environ.get("MC_URL", "")

    global METRICS_FILE
    if args.metrics_file:
        METRICS_FILE = os.path.expanduser(args.metrics_file)
    elif os.environ.get("OPENCLAW_METRICS_FILE"):
        METRICS_FILE = os.path.expanduser(os.environ["OPENCLAW_METRICS_FILE"])

    global SSE_MAX_SECONDS, MAX_LOG_STREAM_CLIENTS, MAX_HEALTH_STREAM_CLIENTS
    sse_max = args.sse_max_seconds
    if sse_max is None:
        env_sse_max = os.environ.get("OPENCLAW_SSE_MAX_SECONDS", "").strip()
        if env_sse_max:
            try:
                sse_max = int(env_sse_max)
            except ValueError:
                sse_max = None
    if sse_max is not None and sse_max > 0:
        SSE_MAX_SECONDS = sse_max
    MAX_LOG_STREAM_CLIENTS = max(1, args.max_log_stream_clients)
    MAX_HEALTH_STREAM_CLIENTS = max(1, args.max_health_stream_clients)

    _load_metrics_from_disk()
    _start_metrics_flush_thread()

    global _history_db, _history_collector
    if _HAS_HISTORY:
        history_db_path = os.environ.get("CLAWMETRY_HISTORY_DB", None)
        _history_db = HistoryDB(history_db_path)
        _history_collector = HistoryCollector(_history_db, _gw_invoke)
        _history_collector.start()

    global FLEET_API_KEY, FLEET_DB_PATH
    if args.fleet_api_key:
        FLEET_API_KEY = args.fleet_api_key
    if args.fleet_db:
        FLEET_DB_PATH = os.path.expanduser(args.fleet_db)
    try:
        _fleet_init_db()
    except Exception as _fleet_exc:
        db_path = _fleet_db_path()
        print(
            f"\n[clawmetry] ERROR: Could not initialise fleet database at {db_path!r}\n"
            f"  Cause: {_fleet_exc}\n\n"
            f"  Try one of:\n"
            f"    1. Ensure the directory exists and is writable:\n"
            f"         mkdir -p ~/.clawmetry && chmod 700 ~/.clawmetry\n"
            f"    2. Specify a custom path:\n"
            f"         clawmetry --fleet-db /tmp/fleet.db\n",
            flush=True,
        )
        raise SystemExit(1) from _fleet_exc
    _budget_init_db()
    _detect_heartbeat_interval()
    _start_fleet_maintenance_thread()
    _start_budget_monitor_thread()
    _start_session_health_thread()
    start_update_check_thread()
    # Weekly Insights Digest cron — gated by CLAWMETRY_INSIGHTS=1 (no-op
    # when the flag is unset). Daemon thread, dies with the process.
    try:
        from clawmetry.insights import start_weekly_scheduler
        if start_weekly_scheduler():
            print("  Insights:   [ok] Weekly digest cron registered (Mon 9am local)")
    except Exception as _ins_exc:
        print(f"  Insights:   [warn] cron not started: {_ins_exc}")

    # Outbound OTLP exporter — gated by CLAWMETRY_OTEL_EXPORT_ENDPOINT (no-op
    # when unset). Emits GenAI semantic convention spans to Datadog / Grafana /
    # Honeycomb / any OTLP HTTP collector. Daemon thread, dies with the process.
    try:
        from clawmetry.otel_exporter import start_exporter as _start_otel_exporter
        if _start_otel_exporter():
            _otel_ep = os.environ.get("CLAWMETRY_OTEL_EXPORT_ENDPOINT", "")
            print(f"  OTLP Export:[ok] Exporting to {_otel_ep}")
    except Exception as _otel_exc:
        print(f"  OTLP Export:[warn] not started: {_otel_exc}")

    try:
        print(BANNER.format(version=__version__))
        print(f"  Workspace:  {WORKSPACE}")
        print(f"  Sessions:   {SESSIONS_DIR}")
        print(f"  Logs:       {LOG_DIR}")
        print(f"  Metrics:    {_metrics_file_path()}")
        if _HAS_OTEL_PROTO:
            print("  OTLP:       [ok] Ready (opentelemetry-proto installed)")
        print(f"  User:       {USER_NAME}")
        print(
            f"  Mode:       {'[dev]  Dev (auto-reload ON)' if args.debug else '[prod] Prod (auto-reload OFF)'}"
        )
        print(
            f"  SSE Limits: {SSE_MAX_SECONDS}s max duration - logs {MAX_LOG_STREAM_CLIENTS} clients - health {MAX_HEALTH_STREAM_CLIENTS} clients"
        )
        print(f"  Fleet DB:   {_fleet_db_path()}")
        print(
            f"  Fleet Auth: {'Enabled (key set)' if FLEET_API_KEY else 'Open (no key - set --fleet-api-key for production)'}"
        )
        if _HAS_HISTORY and _history_db:
            print(f"  History DB: {_history_db.db_path}")
        else:
            print("  History:    Disabled (history.py not found)")
        print()

        warnings, tips = validate_configuration()
        if warnings or tips:
            print("[check] Configuration Check:")
            for warning in warnings:
                print(f"  {warning}")
            for tip in tips:
                print(f"  {tip}")
            print()
            if warnings:
                print(
                    "[tip] The dashboard will work with limited functionality. See tips above for full experience."
                )
                print()
    except (ValueError, OSError):
        pass  # stdout may be closed/redirected on Windows

    # Start the OTLP compatibility listener BEFORE the banner so the banner can
    # report the port it actually bound (or stay quiet when it stepped aside for
    # an existing collector). Issue #4780.
    _otlp_listener = _start_otlp_compat_listener(debug=args.debug)

    try:
        local_ip = get_local_ip()
        public_ip = get_public_ip()
        print(f"  -> http://localhost:{args.port}")
        if local_ip != "127.0.0.1":
            print(f"  -> http://{local_ip}:{args.port}  (LAN)")
        if public_ip and public_ip != local_ip:
            print(
                f"  -> http://{public_ip}:{args.port}  (Public - ensure port is open)"
            )
        # OTLP ingest is always on now: OTLP/JSON needs no extra (#4781), and
        # the receiver also listens on the conventional 4318 (#4780). Print the
        # endpoint an OTel SDK would use with no configuration at all.
        if _otlp_listener is not None:
            print(
                f"  -> OTLP endpoint: http://localhost:{_otlp_listener.effective_port}"
                "  (OTEL_EXPORTER_OTLP_ENDPOINT)"
            )
        else:
            print(f"  -> OTLP endpoint: http://localhost:{args.port}"
                  "  (OTEL_EXPORTER_OTLP_ENDPOINT)")
        # One-click login URL when gateway token was detected (#1356 PR-D).
        # Defense against shoulder-surfing screenshots: only the framed URL is
        # printed (never the bare token), and only on the interactive startup
        # banner (stdout). We never log this line to /tmp/clawmetry.log because
        # the daemon-mode launcher redirects only the noisy server output, not
        # this one-shot banner that runs before serve().
        try:
            _print_login_url_banner(args.port, args.host, GATEWAY_TOKEN)
        except Exception:
            pass  # Never let banner printing break the dashboard
        print()
        # Cloud nudge — only if not already connected
        _already_connected = bool(
            os.environ.get("CLAWMETRY_API_KEY") or os.environ.get("CLAWMETRY_NODE_ID")
        )
        if not _already_connected:
            _sep = "  -" if sys.platform == "win32" else "  \u2500"
            print(_sep * 25)
            print()
            _globe = "[web]" if sys.platform == "win32" else "🌐 "
            _lock = "[enc]" if sys.platform == "win32" else "🔒 "
            print(
                f"  {_globe}  Run clawmetry connect to access your dashboard from app.clawmetry.com"
            )
            print(
                f"      {_lock}  E2E encrypted with your local key — decrypted in the dashboard on demand."
            )
            print("      Free 7-day trial · no credit card required.")
            print()

        if not args.debug:
            print("  Tip: run as background service with: clawmetry start")
            print()
    except (ValueError, OSError):
        pass  # stdout may be closed/redirected on Windows

    if args.debug:
        # Dev mode -- use Flask's reloader
        app.run(
            host=args.host, port=args.port, debug=True, use_reloader=True, threaded=True
        )
    else:
        # Prod mode -- use Waitress (no WSGI warning, multi-threaded)
        try:
            from waitress import serve

            # threads=32: each SSE stream (health, logs, flow) holds a thread
            # for its lifetime. Older 8-thread default got exhausted after 2-3
            # tab reloads, leaving new requests stuck pending. 32 gives ~10 tabs
            # of headroom before queuing.
            serve(app, host=args.host, port=args.port, threads=32, channel_timeout=120)
        except ImportError:
            # Waitress not installed -- fall back to Flask dev server.
            # On Windows with redirected stdout (e.g. Start-Process),
            # Flask/Click banner printing crashes on closed file handles.
            # Unconditionally redirect to devnull on Windows to prevent it.
            import logging

            log = logging.getLogger("werkzeug")
            log.setLevel(logging.ERROR)
            if os.name == "nt":
                sys.stdout = open(os.devnull, "w", encoding="utf-8")
                sys.stderr = open(os.devnull, "w", encoding="utf-8")
            app.run(
                host=args.host,
                port=args.port,
                debug=False,
                use_reloader=False,
                threaded=True,
            )


def _init_data_provider():
    """Phase 3: Initialize the active DataProvider after path detection."""
    try:
        from clawmetry.providers import init_providers

        return init_providers(
            sessions_dir=SESSIONS_DIR or "",
            log_dir=LOG_DIR or "",
            workspace=WORKSPACE or "",
            metrics_file=METRICS_FILE or "",
        )
    except Exception:
        return None



def _ensure_ingest_running() -> None:
    """Start the sync daemon on a plain `clawmetry` boot when nothing is
    ingesting for THIS home (#5740).

    `pip install clawmetry && clawmetry` is the command in the README, on the
    homepage and in every install doc, and it starts only the dashboard.
    Ingest is the daemon's job, and every other `_start_daemon_background()`
    call site sits in the cloud-connect flow -- so a user who followed the
    documented quickstart got a dashboard that told them it had detected their
    runtime and then showed zero sessions, with no error to search for.
    Reproduced on the published wheel and on main with a real Goose store:
    the probe found Goose, /api/overview reported 0 sessions, and one manual
    `python -m clawmetry.sync` turned it into 4.

    Deliberately HOME-scoped. The obvious check, `_is_sync_running()`, shells
    out to `pgrep -f "clawmetry.*sync"`, which matches a daemon belonging to
    ANOTHER home serving a DIFFERENT store -- on a developer machine that is
    the normal case, and it would make this skip exactly where it is needed.
    `local_store._daemon_registered()` reads a file scoped to this home.

    Never raises, never blocks the boot, and `CLAWMETRY_AUTO_INGEST=0` turns
    it off entirely.
    """
    if str(os.environ.get("CLAWMETRY_AUTO_INGEST", "1")).strip().lower() in (
        "0", "false", "no", "off",
    ):
        return
    # Sample mode serves a synthetic store; ingesting real sessions into it
    # would defeat the isolation the sample depends on.
    try:
        from clawmetry import sample_data as _sample_data
        if _sample_data.is_sample_mode():
            return
    except Exception:
        pass
    try:
        from clawmetry import local_store as _ls
        if _ls._daemon_registered():
            return  # something already owns this home's store
    except Exception:
        return  # cannot tell -> do nothing rather than risk a second writer
    try:
        _start_daemon_background()
    except Exception as exc:
        # A failure here must never stop the dashboard serving -- but it must
        # not be silent either, or we are back to an empty screen with no
        # explanation.
        print(f"  Could not start the sync daemon ({exc}). The dashboard will "
              f"show no sessions until one runs: python3 -m clawmetry.sync")


def main():
    # Enterprise TLS/proxy bootstrap (idempotent; also runs in cli.main).
    # Covers direct `python3 dashboard.py` runs so telemetry/cloud-proxy
    # POSTs work behind corporate TLS-intercepting proxies.
    try:
        from clawmetry.net import configure_outbound_network
        configure_outbound_network(role="dashboard")
    except Exception:
        pass
    try:
        from clawmetry.winconsole import hide_child_console_windows
        hide_child_console_windows()
    except Exception:
        pass
    # -----------------------------------------------------------------------
    # Build a shared parent parser for options that apply to all subcommands
    # (and to foreground mode when no subcommand is given).
    # -----------------------------------------------------------------------
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--port", "-p", type=int, default=8900, help="Port (default: 8900)"
    )
    shared.add_argument(
        "--host", "-H", type=str, default="127.0.0.1", help="Host (default: 127.0.0.1)"
    )
    shared.add_argument("--workspace", "-w", type=str, help="Agent workspace directory")
    shared.add_argument(
        "--data-dir", "-d", type=str, help="OpenClaw data directory (e.g. ~/.openclaw)."
    )
    shared.add_argument(
        "--openclaw-dir",
        type=str,
        help="OpenClaw config directory (default: ~/.openclaw). Env: CLAWMETRY_OPENCLAW_DIR",
    )
    shared.add_argument("--log-dir", "-l", type=str, help="Log directory")
    shared.add_argument(
        "--sessions-dir",
        "-s",
        type=str,
        help="Sessions directory (transcript .jsonl files)",
    )
    shared.add_argument(
        "--metrics-file", "-m", type=str, help="Path to metrics persistence JSON file"
    )
    shared.add_argument("--name", "-n", type=str, help="Your name (shown in Flow tab)")
    shared.add_argument("--debug", dest="debug", action="store_true", default=True)
    shared.add_argument(
        "--no-debug",
        dest="debug",
        action="store_false",
        help="Disable debug mode and auto-reload",
    )
    shared.add_argument("--sse-max-seconds", type=int, default=None)
    shared.add_argument("--max-log-stream-clients", type=int, default=10)
    shared.add_argument("--max-health-stream-clients", type=int, default=10)
    shared.add_argument(
        "--monitor-service", action="append", default=[], metavar="NAME:PORT"
    )
    shared.add_argument("--mc-url", type=str)
    shared.add_argument("--fleet-api-key", type=str)
    shared.add_argument("--fleet-db", type=str)

    # -----------------------------------------------------------------------
    # Top-level parser
    # -----------------------------------------------------------------------
    parser = argparse.ArgumentParser(
        prog="clawmetry",
        description=HELP_TEXT.format(version=__version__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[shared],
    )

    class _SafeVersion(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            try:
                import sys

                sys.stdout.write(f"clawmetry {__version__}\n")
                sys.stdout.flush()
            except Exception:
                pass
            parser.exit()

    parser.add_argument(
        "--version", "-v", nargs=0, action=_SafeVersion, help="Show version"
    )

    subparsers = parser.add_subparsers(dest="command", metavar="command")

    # clawmetry start
    p_start = subparsers.add_parser(
        "start",
        parents=[shared],
        add_help=True,
        help="Start ClawMetry as a background service",
    )

    # clawmetry stop
    p_stop = subparsers.add_parser(
        "stop", parents=[shared], add_help=True, help="Stop the background service"
    )

    # clawmetry restart
    p_restart = subparsers.add_parser(
        "restart",
        parents=[shared],
        add_help=True,
        help="Restart the background service",
    )

    # clawmetry status
    p_status = subparsers.add_parser(
        "status",
        parents=[shared],
        add_help=True,
        help="Show service status, port, and uptime",
    )

    # clawmetry connect
    p_connect = subparsers.add_parser(
        "connect", parents=[shared], add_help=True, help=argparse.SUPPRESS
    )

    # clawmetry uninstall
    p_uninstall = subparsers.add_parser(
        "uninstall",
        parents=[shared],
        add_help=True,
        help="Remove the background service",
    )

    # clawmetry help (alias)
    subparsers.add_parser("help", add_help=True, help="Show this help message")

    args = parser.parse_args()

    # "clawmetry help" -> print help and exit
    if args.command == "help":
        try:
            parser.print_help()
        except (ValueError, OSError):
            pass
        sys.exit(0)

    # Dispatch to subcommand handlers
    if args.command == "start":
        cmd_start(args)
    elif args.command == "stop":
        cmd_stop(args)
    elif args.command == "restart":
        cmd_restart(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "connect":
        cmd_connect(args)
    elif args.command == "uninstall":
        cmd_uninstall(args)
    else:
        # No subcommand -> foreground server (original behaviour)
        try:
            print(ARCHITECTURE_OVERVIEW.format(version=__version__, port=args.port))
        except (ValueError, OSError):
            pass
        try:
            print("Starting dashboard...")
            print()
        except (ValueError, OSError):
            pass
        # The dashboard renders what the daemon collects; without one, a
        # machine full of agent sessions renders empty (#5740).
        _ensure_ingest_running()
        _run_server(args)


if __name__ == "__main__":
    main()
