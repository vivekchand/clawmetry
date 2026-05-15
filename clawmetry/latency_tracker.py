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
            "count": len(ordered),
            "p50_ms": round(p50, 1),
            "p95_ms": round(p95, 1),
            "avg_ms": round(avg, 1),
            "max_ms": round(ordered[-1], 1),
            "is_slow": p95 > slow_threshold_ms,
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
