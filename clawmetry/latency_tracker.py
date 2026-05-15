"""Per-endpoint p50/p95 handler-latency tracker (in-memory rolling window).

Issue #1283 — eat our own dogfood. Surface ClawMetry's own API handler
latency so a /api/sessions-class regression doesn't silently sit in prod
for weeks before the next user-flagged incident catches it.

Design: process-local, lock-protected, fixed-size deque per endpoint,
5-minute rolling window. Memory ceiling ~200 records × ~100 endpoints
≈ 20k entries — trivially small. No DuckDB write — read path is the
operator dashboard, not historical analytics.
"""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Any

_MAX_PER_ENDPOINT = 200
_WINDOW_SECONDS = 5 * 60

_lock = threading.Lock()
_buckets: dict[str, deque] = defaultdict(lambda: deque(maxlen=_MAX_PER_ENDPOINT))


def record(endpoint: str, elapsed_ms: float) -> None:
    if not endpoint or elapsed_ms < 0:
        return
    now = time.time()
    with _lock:
        _buckets[endpoint].append((now, elapsed_ms))


def _percentile(sorted_values: list[float], pct: float) -> float:
    if not sorted_values:
        return 0.0
    n = len(sorted_values)
    k = max(0, min(n - 1, int(round((pct / 100.0) * (n - 1)))))
    return sorted_values[k]


# Issue #1290 — humanise raw Flask blueprint:func identifiers so the
# operator dashboard reads "Components › Component Tool" instead of the
# unreadable internal name "components.api_component_tool". Static map
# wins for the common dashboard surfaces (~30 endpoints); mechanical
# transform handles the long tail without per-endpoint maintenance.
_LABEL_OVERRIDES: dict[str, str] = {
    "overview.api_overview":              "Main dashboard",
    "sessions.api_sessions":              "Sessions list",
    "sessions.api_transcript":            "Session transcript",
    "sessions.api_subagents":             "Sub-agent tracker",
    "components.api_component_tool":      "Tool detail panel",
    "components.api_component_runtime":   "Runtime panel",
    "components.api_component_machine":   "Machine panel",
    "components.api_component_gateway":   "Gateway panel",
    "components.api_component_brain":     "Brain panel",
    "health.api_system_health":           "System health",
    "health.api_reliability":             "Reliability trend",
    "health.api_heartbeat_status":        "Heartbeat status",
    "health.api_diagnostics":             "Diagnostics",
    "health.api_handler_latency":         "Handler latency (this panel)",
    "usage.api_usage":                    "Token & cost usage",
    "usage.api_anomalies":                "Cost anomalies",
    "usage.api_usage_anomalies":          "Usage anomalies",
    "brain.api_brain_history":            "Brain feed (history)",
    "brain.api_brain_stream":             "Brain feed (live)",
    "crons.api_crons":                    "Cron jobs",
    "alerts.api_alert_rules":             "Alert rules",
    "channels.api_channels":              "Chat channels",
    "heartbeat.api_heartbeat":            "Heartbeat ping (POST)",
    "crons.api_cron_runs":                "Cron run history",
    "fleet.api_nodes":                    "Multi-node fleet",
    "history.api_history":                "Time-series history",
    "alerts.api_alerts":                  "Alert center",
    "alerts.api_alerts_evaluate":         "Alert evaluator",
    "budget.api_budget":                  "Budget panel",
    "memory.api_memory":                  "Memory inspector",
    "security.api_security":              "Security posture",
    "logs.api_logs":                      "Log stream",
    "selfevolve.api_selfevolve":          "Self-evolve loop",
    "advisor.api_advisor":                "Advisor (Q&A)",
    "version_impact.api_version_impact":  "Version impact",
    "skills.api_skills":                  "Skills browser",
    "channels.api_channels_status":       "Channel status",
}


def humanise_endpoint(endpoint: str) -> str:
    """Convert a Flask ``blueprint.func`` identifier into a user-readable label.

    1. Exact match in ``_LABEL_OVERRIDES`` wins (curated for the common
       dashboard surfaces — most readable, zero-cost lookup).
    2. Otherwise, mechanical transform: drop ``api_`` prefix, replace ``_``
       with spaces, title-case each word, separate blueprint from func with
       ``›``. Unknown endpoints get readable fallback like "Components ›
       Component Tool" without per-endpoint maintenance.
    3. If the endpoint doesn't have a ``.``, return as-is (already readable
       e.g. ``static`` or a path-string fallback).

    Both halves get word-splitting (PR #1290 follow-up): multi-word
    blueprint names like ``version_impact`` previously rendered as
    ``Version_impact``; now correctly ``Version Impact``.
    """
    if not endpoint:
        return endpoint
    if endpoint in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[endpoint]
    if "." not in endpoint:
        return endpoint
    bp, func = endpoint.split(".", 1)
    func = func[4:] if func.startswith("api_") else func
    pretty_bp   = " ".join(p.capitalize() for p in bp.split("_") if p)
    pretty_func = " ".join(p.capitalize() for p in func.split("_") if p)
    return f"{pretty_bp} › {pretty_func}"


def get_stats(top_n: int = 20, slow_threshold_ms: float = 500.0) -> dict[str, Any]:
    """Return rolling-window stats per endpoint, sorted by p95 desc."""
    cutoff = time.time() - _WINDOW_SECONDS
    out: list[dict[str, Any]] = []
    with _lock:
        endpoints = list(_buckets.items())
    for endpoint, dq in endpoints:
        recents = [ms for (ts, ms) in dq if ts >= cutoff]
        if not recents:
            continue
        ordered = sorted(recents)
        p50 = _percentile(ordered, 50)
        p95 = _percentile(ordered, 95)
        avg = sum(ordered) / len(ordered)
        out.append({
            "endpoint": endpoint,
            "label":    humanise_endpoint(endpoint),
            "count":    len(ordered),
            "p50_ms":   round(p50, 1),
            "p95_ms":   round(p95, 1),
            "avg_ms":   round(avg, 1),
            "max_ms":   round(ordered[-1], 1),
            "is_slow":  p95 > slow_threshold_ms,
        })
    out.sort(key=lambda r: r["p95_ms"], reverse=True)
    return {
        "window_seconds": _WINDOW_SECONDS,
        "slow_threshold_ms": slow_threshold_ms,
        "endpoints": out[:top_n],
        "endpoint_count": len(out),
    }


def reset() -> None:
    with _lock:
        _buckets.clear()
