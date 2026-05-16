#!/usr/bin/env python3
"""Probe key dashboard endpoints; fail on p50/p95 budget breach (issue #1241).
Runs each endpoint N times and asserts p50<500ms / p95<1500ms by default.
Tunable via CLAWMETRY_SMOKE_{RUNS,P50_MS,P95_MS,TIMEOUT,SKIP} env vars."""

from __future__ import annotations

import os
import statistics
import sys
import time
from typing import Iterable

import requests

BASE_URL = os.environ.get("CLAWMETRY_URL", "http://localhost:8900").rstrip("/")
TOKEN = os.environ.get("CLAWMETRY_TOKEN", "")
RUNS = int(os.environ.get("CLAWMETRY_SMOKE_RUNS", "5"))
P50_BUDGET_MS = float(os.environ.get("CLAWMETRY_SMOKE_P50_MS", "500"))
P95_BUDGET_MS = float(os.environ.get("CLAWMETRY_SMOKE_P95_MS", "1500"))
TIMEOUT_S = float(os.environ.get("CLAWMETRY_SMOKE_TIMEOUT", "10"))
SKIP = {p.strip() for p in os.environ.get("CLAWMETRY_SMOKE_SKIP", "").split(",") if p.strip()}

# Mirrors CLAUDE.md "Key API Endpoints". transcript id matches the seeded
# session in scripts/seed_smoke_duckdb.py.
ENDPOINTS: tuple[str, ...] = (
    "/api/overview",
    "/api/sessions",
    "/api/subagents",
    "/api/transcript/smoke-sess-000",
    "/api/usage",
    "/api/flow",
    "/api/brain-history",
    "/api/crons",
    "/api/system-health",
    "/api/nodes",
    "/api/budget/status",
    "/api/alerts/rules",
    "/api/heartbeat-status",
    "/api/memory-files",
)


def _percentile(samples: list[float], pct: float) -> float:
    """Linear-interpolation percentile (matches numpy.percentile method=linear)."""
    if not samples:
        return float("nan")
    s = sorted(samples)
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * (pct / 100.0)
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def _probe_one(session: requests.Session, path: str) -> tuple[list[float], int | None, str]:
    samples, last_status, err = [], None, ""
    url = f"{BASE_URL}{path}"
    for _ in range(RUNS):
        t0 = time.perf_counter()
        try:
            r = session.get(url, timeout=TIMEOUT_S)
            last_status = r.status_code
            _ = r.content  # drain body so timing includes serialisation
        except requests.RequestException as e:
            err = type(e).__name__
        samples.append((time.perf_counter() - t0) * 1000)
    return samples, last_status, err


def run(endpoints: Iterable[str] = ENDPOINTS) -> int:
    headers = {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}
    session = requests.Session()
    session.headers.update(headers)

    print(f"probe target:  {BASE_URL}")
    print(f"runs/endpoint: {RUNS}")
    print(f"budgets:       p50<{P50_BUDGET_MS:.0f}ms, p95<{P95_BUDGET_MS:.0f}ms\n")
    header = f"{'endpoint':<40} {'p50':>8} {'p95':>8} {'max':>8}  status  verdict"
    print(header)
    print("-" * len(header))

    failures: list[str] = []
    annotations: list[str] = []
    for path in endpoints:
        if path in SKIP:
            print(f"{path:<40} {'-':>8} {'-':>8} {'-':>8}  skip    SKIP")
            continue
        samples, status, err = _probe_one(session, path)
        p50, p95, smax = _percentile(samples, 50), _percentile(samples, 95), max(samples)
        verdict, breach_bits, ann_bits = "OK", [], []
        # Network errors / 5xx are a hard fail — the endpoint is down, not slow.
        if status is None or status >= 500:
            verdict = "FAIL"
            breach_bits.append(f"status={status or err or 'connerr'}")
            ann_bits.append(f"status={status or err or 'connerr'}")
        if p50 > P50_BUDGET_MS:
            verdict = "FAIL"
            breach_bits.append(f"p50={p50:.0f}ms>{P50_BUDGET_MS:.0f}ms")
            ann_bits.append(
                f"p50={p50:.0f}ms exceeds {P50_BUDGET_MS:.0f}ms budget by {p50 - P50_BUDGET_MS:.0f}ms"
            )
        if p95 > P95_BUDGET_MS:
            verdict = "FAIL"
            breach_bits.append(f"p95={p95:.0f}ms>{P95_BUDGET_MS:.0f}ms")
            ann_bits.append(
                f"p95={p95:.0f}ms exceeds {P95_BUDGET_MS:.0f}ms budget by {p95 - P95_BUDGET_MS:.0f}ms"
            )
        print(f"{path:<40} {p50:>7.0f}ms {p95:>7.0f}ms {smax:>7.0f}ms"
              f"  {status if status is not None else '---':>4}    {verdict}")
        if verdict != "OK":
            failures.append(f"{path}: " + ", ".join(breach_bits))
            # Machine-readable GitHub annotation, distinct from [setup-flake]
            # so devs and downstream automation can filter the two classes.
            annotations.append(f"::error::[regression] {path} {'; '.join(ann_bits)}")

    print()
    if failures:
        # Emit GH annotations AFTER the table so the human-readable summary
        # stays grouped together; annotations float to the run summary anyway.
        for ann in annotations:
            print(ann)
        print(f"FAIL: {len(failures)} endpoint(s) breached the latency gate:")
        for line in failures:
            print(f"  - {line}")
        return 1
    print("PASS: all endpoints under p50/p95 budgets.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
