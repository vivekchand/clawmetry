#!/usr/bin/env python3
"""scripts/accuracy_harness/tokens.py — tokens-first ground-truth verifier.

Goal
====
Audit the ClawMetry Tokens tab end-to-end by driving real OpenClaw turns
through the gateway with known token usage, waiting for the sync daemon
to flush them into DuckDB, then asserting that every relevant dashboard
endpoint + time window reports those tokens accurately.

This is a tokens-first proof-of-concept. The same SHAPE
(`drive ground truth → wait for flush → query every window → diff →
report or file drift issue`) will extend cleanly to:
  * approvals (drive N approval requests, assert the queue + history)
  * alerts (trip a known threshold, assert evaluator + webhook)

Usage
-----
    # Defaults: 3 messages, dashboard auto-detected on 8900/8903/8905
    python3 scripts/accuracy_harness/tokens.py

    # Override
    CLAWMETRY_URL=http://localhost:8903 \\
      python3 scripts/accuracy_harness/tokens.py --messages 5 --message-text "Say PONG"

    # File drift issues on failure (default: print only)
    python3 scripts/accuracy_harness/tokens.py --file-issues

Exit codes
----------
  0 — all windows + metrics within tolerance
  1 — one or more drifts detected (issue filed if --file-issues)
  2 — harness itself failed (couldn't reach dashboard / daemon / openclaw)
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ─── Config ─────────────────────────────────────────────────────────────────

DEFAULT_DASHBOARD_PORTS = (8900, 8903, 8905)
DEFAULT_MESSAGE_TEXT = "Say PONG and nothing else."
DEFAULT_MESSAGE_COUNT = 3
TOLERANCE_TOKENS = 1  # cache splits can drift ±1 due to rounding
FLUSH_TIMEOUT_S = 30
FLUSH_POLL_INTERVAL_S = 1.0
OPENCLAW_BIN = shutil.which("openclaw") or "openclaw"
GH_REPO = "vivekchand/clawmetry"
LOCAL_QUERY_DISCOVERY = Path.home() / ".clawmetry" / "local_query.json"


# ─── Data classes ───────────────────────────────────────────────────────────

@dataclass
class GroundTruth:
    """Sum of usage across all synthetic messages we just drove."""
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0
    total: int = 0  # input + output (cache excluded from billed total)
    sessions: set[str] = field(default_factory=set)
    models: dict[str, int] = field(default_factory=dict)  # model → input+output
    events: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class WindowSnapshot:
    """What the dashboard reported for a single (endpoint, window) probe."""
    endpoint: str
    window_label: str
    # Sums we extracted from the response (delta from baseline).
    input_delta: int = 0
    output_delta: int = 0
    cache_read_delta: int = 0
    cache_write_delta: int = 0
    total_delta: int = 0
    raw_today: int | None = None
    raw_today_after: int | None = None
    notes: str = ""


@dataclass
class CheckResult:
    endpoint: str
    window_label: str
    metric: str
    ground: int
    actual: int
    tolerance: int
    passed: bool

    @property
    def delta(self) -> int:
        return self.actual - self.ground


# ─── Helpers: HTTP ──────────────────────────────────────────────────────────

def _http_get_json(url: str, timeout: float = 10.0) -> Any:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_post_json(url: str, body: dict, headers: dict | None = None, timeout: float = 10.0) -> Any:
    data = json.dumps(body).encode("utf-8")
    h = {"Content-Type": "application/json", "Accept": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ─── Helpers: discovery ─────────────────────────────────────────────────────

def _port_listening(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        return s.connect_ex((host, port)) == 0
    finally:
        s.close()


def discover_dashboard_url(override: str | None) -> str:
    if override:
        return override.rstrip("/")
    env = os.environ.get("CLAWMETRY_URL")
    if env:
        return env.rstrip("/")
    for port in DEFAULT_DASHBOARD_PORTS:
        if not _port_listening(port):
            continue
        url = f"http://localhost:{port}"
        # Probe /api/usage to distinguish dashboard from other listeners.
        try:
            payload = _http_get_json(f"{url}/api/usage", timeout=3.0)
            if isinstance(payload, dict) and "days" in payload:
                return url
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError):
            continue
    raise RuntimeError(
        f"could not find a ClawMetry dashboard on any of {DEFAULT_DASHBOARD_PORTS}. "
        f"Set CLAWMETRY_URL or pass --dashboard-url."
    )


def discover_daemon() -> dict | None:
    """Return ``{port, token}`` for the daemon proxy, or None if unavailable."""
    try:
        with open(LOCAL_QUERY_DISCOVERY) as fh:
            d = json.load(fh)
        if not (d.get("port") and d.get("token")):
            return None
        # Liveness check.
        try:
            os.kill(int(d.get("pid") or 0), 0)
        except (OSError, ValueError):
            return None
        return {"port": int(d["port"]), "token": d["token"]}
    except (FileNotFoundError, ValueError, OSError):
        return None


def daemon_event_count(daemon: dict) -> int | None:
    """Return the daemon's total event count via /__local_query__/health.
    Returns None if the daemon is unreachable."""
    url = f"http://127.0.0.1:{daemon['port']}/__local_query__/health"
    try:
        body = _http_post_json(
            url, body={},
            headers={"Authorization": f"Bearer {daemon['token']}"},
            timeout=3.0,
        )
        # Response: {"result": {"event_count": N, ...}}
        result = body.get("result") if isinstance(body, dict) else None
        if isinstance(result, dict):
            ev = result.get("event_count")
            return int(ev) if ev is not None else None
        return None
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, TimeoutError, OSError):
        return None


# ─── Helpers: driving openclaw ──────────────────────────────────────────────

def drive_message(message: str, tag: str, timeout_s: int = 120) -> dict[str, Any]:
    """Run ``openclaw agent --agent main --message <m> --json`` once.
    Returns the parsed JSON (status + result + meta) — caller extracts usage.
    Tag is embedded into the message for traceability (sessions list / DuckDB).
    """
    full_msg = f"{message} [{tag}]"
    cmd = [OPENCLAW_BIN, "agent", "--agent", "main", "--message", full_msg, "--json"]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=timeout_s, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"openclaw agent exited {proc.returncode}\nstderr: {proc.stderr[:500]}"
        )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"openclaw agent --json returned non-JSON: {e}\nfirst 300 bytes: {proc.stdout[:300]}"
        )


def extract_usage(agent_json: dict) -> dict[str, Any] | None:
    """Pull the ``usage`` block out of an ``openclaw agent --json`` response.
    Returns dict with input/output/cacheRead/cacheWrite/sessionId/model, or
    None if the response didn't include billable usage (e.g. an error turn).
    """
    meta = (agent_json or {}).get("result", {}).get("meta", {}) or {}
    agent_meta = meta.get("agentMeta") or {}
    usage = agent_meta.get("usage") or {}
    if not usage:
        return None
    return {
        "input":      int(usage.get("input") or 0),
        "output":     int(usage.get("output") or 0),
        "cacheRead":  int(usage.get("cacheRead") or 0),
        "cacheWrite": int(usage.get("cacheWrite") or 0),
        "sessionId":  agent_meta.get("sessionId") or "",
        "model":      agent_meta.get("model") or "",
    }


# ─── Endpoint scrapers ──────────────────────────────────────────────────────

def fetch_api_usage(dashboard_url: str) -> dict:
    # /api/usage carries today/week/month + per-day breakdown. There is NO
    # ?window= parameter (Tokens tab derives every window from `days[]`).
    return _http_get_json(f"{dashboard_url}/api/usage", timeout=15.0)


def fetch_context_anatomy(dashboard_url: str) -> dict:
    return _http_get_json(f"{dashboard_url}/api/context-anatomy", timeout=10.0)


# ─── Window math ────────────────────────────────────────────────────────────

def today_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def week_start_iso() -> str:
    today = datetime.now()
    from datetime import timedelta
    return (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")


def month_start_iso() -> str:
    return datetime.now().strftime("%Y-%m-01")


def sum_days(days: list[dict], key: str, since_iso: str) -> int:
    return sum(int(d.get(key) or 0) for d in (days or []) if (d.get("date") or "") >= since_iso)


def snapshot_window(payload: dict, window_label: str) -> dict[str, int]:
    """Extract (input, output, cacheRead, cacheWrite, total) for a window
    from a /api/usage payload. Returns a dict of ints. Handles the 3 windows
    the Tokens tab exposes directly: today / week / month. For windows the
    server pre-computes (today/week/month scalars) we use those; for hour
    or other custom windows we sum `days[]` ourselves.
    """
    days = payload.get("days") or []
    if window_label == "today":
        since = today_iso()
    elif window_label == "week":
        since = week_start_iso()
    elif window_label == "month":
        since = month_start_iso()
    elif window_label == "all_14d":
        since = "0000-00-00"
    else:
        raise ValueError(f"unknown window: {window_label}")

    inp = sum_days(days, "inputTokens", since)
    out = sum_days(days, "outputTokens", since)
    cr  = sum_days(days, "cacheReadTokens", since)
    cw  = sum_days(days, "cacheWriteTokens", since)
    tot = sum_days(days, "tokens", since)
    return {
        "input": inp, "output": out, "cache_read": cr, "cache_write": cw, "total": tot,
    }


# ─── Main flow ──────────────────────────────────────────────────────────────

def run_harness(args: argparse.Namespace) -> int:
    print(f"[harness] tokens accuracy audit — {datetime.now(timezone.utc).isoformat()}")
    print(f"[harness] sending {args.messages} message(s) via `{OPENCLAW_BIN}`")

    dashboard_url = discover_dashboard_url(args.dashboard_url)
    print(f"[harness] dashboard: {dashboard_url}")

    daemon = discover_daemon()
    if daemon:
        print(f"[harness] daemon proxy: 127.0.0.1:{daemon['port']} (event_count probe enabled)")
    else:
        print(f"[harness] daemon proxy not discoverable — will use time-based flush wait")

    # 1. Baseline.
    print("[harness] capturing baseline /api/usage…")
    baseline_payload = fetch_api_usage(dashboard_url)
    baseline_windows = {
        w: snapshot_window(baseline_payload, w)
        for w in ("today", "week", "month", "all_14d")
    }
    baseline_ev_count = daemon_event_count(daemon) if daemon else None
    print(f"[harness] baseline today: {baseline_windows['today']}")
    print(f"[harness] baseline event_count: {baseline_ev_count}")

    # 2. Drive ground truth.
    run_id = uuid.uuid4().hex[:8]
    tag_prefix = f"ACCURACY_AUDIT_{run_id}"
    ground = GroundTruth()
    print(f"[harness] tag prefix: {tag_prefix}")

    for i in range(args.messages):
        tag = f"{tag_prefix}_msg{i+1}"
        t0 = time.time()
        try:
            resp = drive_message(args.message_text, tag, timeout_s=args.openclaw_timeout)
        except Exception as e:
            print(f"  [msg {i+1}] FAILED to drive: {e}", file=sys.stderr)
            continue
        usage = extract_usage(resp)
        elapsed = time.time() - t0
        if not usage:
            print(f"  [msg {i+1}] no usage in response (skipping); status={resp.get('status')}")
            continue
        ground.input       += usage["input"]
        ground.output      += usage["output"]
        ground.cache_read  += usage["cacheRead"]
        ground.cache_write += usage["cacheWrite"]
        ground.total       += usage["input"] + usage["output"]
        if usage["sessionId"]:
            ground.sessions.add(usage["sessionId"])
        if usage["model"]:
            ground.models[usage["model"]] = ground.models.get(usage["model"], 0) + usage["input"] + usage["output"]
        ground.events.append({"tag": tag, "elapsed_s": round(elapsed, 2), **usage})
        print(f"  [msg {i+1}] in={usage['input']} out={usage['output']} "
              f"cacheR={usage['cacheRead']} cacheW={usage['cacheWrite']} "
              f"session={usage['sessionId'][:8] if usage['sessionId'] else '?'} "
              f"({elapsed:.1f}s)")

    if not ground.events:
        print("[harness] FATAL: zero ground-truth events captured", file=sys.stderr)
        return 2

    print(f"[harness] GROUND TRUTH: input={ground.input} output={ground.output} "
          f"cacheR={ground.cache_read} cacheW={ground.cache_write} "
          f"sessions={len(ground.sessions)} models={list(ground.models.keys())}")

    # 3. Wait for flush.
    print(f"[harness] waiting up to {FLUSH_TIMEOUT_S}s for sync daemon to flush…")
    flushed = False
    if daemon and baseline_ev_count is not None:
        deadline = time.time() + FLUSH_TIMEOUT_S
        target = baseline_ev_count + len(ground.events)  # ≥ N more events
        while time.time() < deadline:
            ec = daemon_event_count(daemon)
            if ec is not None and ec >= target:
                print(f"[harness] flush detected: event_count {baseline_ev_count}→{ec}")
                flushed = True
                break
            time.sleep(FLUSH_POLL_INTERVAL_S)
        if not flushed:
            print(f"[harness] flush wait timed out (event_count={daemon_event_count(daemon)}, "
                  f"target={target}); continuing anyway")
    else:
        time.sleep(min(FLUSH_TIMEOUT_S, 10.0))

    # Bust the dashboard's in-process /api/usage cache. The route caches for
    # _USAGE_CACHE_TTL seconds — without a probe-wait, we'd read pre-flush
    # numbers. The cache TTL is short (<10s), so a brief sleep + retry works.
    print("[harness] sleeping 3s for /api/usage cache TTL …")
    time.sleep(3.0)

    # 4. Re-fetch & compare.
    print("[harness] fetching post-run /api/usage…")
    after_payload = fetch_api_usage(dashboard_url)
    after_windows = {
        w: snapshot_window(after_payload, w)
        for w in ("today", "week", "month", "all_14d")
    }

    # Context-anatomy is the per-session bucket view, not totals — we don't
    # assert it numerically against ground truth, but we DO assert the
    # endpoint stays responsive after the test traffic. Document this
    # limitation and don't fail the run on it.
    try:
        ca = fetch_context_anatomy(dashboard_url)
        ca_ok = bool(ca.get("buckets"))
    except Exception as e:
        ca, ca_ok = {"error": str(e)}, False

    # 5. Build per-window checks.
    checks: list[CheckResult] = []
    metric_map = [
        ("input",       "input"),
        ("output",      "output"),
        ("cache_read",  "cache_read"),
        ("cache_write", "cache_write"),
        ("total",       "total"),  # billed total = input + output
    ]
    ground_per_metric = {
        "input": ground.input,
        "output": ground.output,
        "cache_read": ground.cache_read,
        "cache_write": ground.cache_write,
        "total": ground.input + ground.output,
    }

    for window in ("today", "week", "month", "all_14d"):
        for metric_label, metric_key in metric_map:
            before = baseline_windows[window][metric_key]
            after  = after_windows[window][metric_key]
            delta  = after - before
            expected = ground_per_metric[metric_label]
            # Wider tolerance for cache splits.
            tol = TOLERANCE_TOKENS * (3 if metric_label.startswith("cache") else 1)
            passed = abs(delta - expected) <= tol
            checks.append(CheckResult(
                endpoint="/api/usage",
                window_label=window,
                metric=metric_label,
                ground=expected,
                actual=delta,
                tolerance=tol,
                passed=passed,
            ))

    # 6. Report.
    print()
    print("─" * 78)
    print(f"{'ENDPOINT':<14} {'WINDOW':<10} {'METRIC':<12} {'GROUND':>8} {'ACTUAL':>8} {'DELTA':>8}  RESULT")
    print("─" * 78)
    drifts: list[CheckResult] = []
    for c in checks:
        delta_sign = f"{c.delta:+d}"
        result = "PASS" if c.passed else "DRIFT"
        if not c.passed:
            drifts.append(c)
        print(f"{c.endpoint:<14} {c.window_label:<10} {c.metric:<12} "
              f"{c.ground:>8} {c.actual:>8} {delta_sign:>8}  {result}")
    print("─" * 78)
    print(f"context-anatomy: {'OK' if ca_ok else 'FAIL'} "
          f"({len(ca.get('buckets', []))} buckets, "
          f"pct_used={ca.get('pct_used')})  [observational only — no numeric assert]")
    print()
    print(f"summary: {sum(1 for c in checks if c.passed)} pass / {len(drifts)} drift / "
          f"{len(checks)} total checks")
    print(f"sessions touched: {sorted(ground.sessions)}")
    print(f"models touched: {ground.models}")

    if not drifts:
        print()
        print("[harness] ALL CHECKS PASSED — Tokens tab is accurate on this build.")
        return 0

    print()
    print("[harness] DRIFT DETECTED:")
    for c in drifts:
        print(f"  - {c.endpoint} window={c.window_label} metric={c.metric}: "
              f"ground={c.ground} actual={c.actual} delta={c.delta:+d} "
              f"(tol=±{c.tolerance})")

    if args.file_issues:
        file_drift_issues(drifts, ground, tag_prefix, dashboard_url)
    else:
        print("[harness] (re-run with --file-issues to open GitHub issues)")

    return 1


# ─── Issue filing ───────────────────────────────────────────────────────────

def _open_audit_issue_exists(endpoint: str, today: str) -> bool:
    """Cheap dedup so we don't fill the tracker on repeat runs in one day."""
    try:
        proc = subprocess.run(
            ["gh", "issue", "list",
             "--repo", GH_REPO,
             "--state", "open",
             "--search", f"[accuracy-audit {today}] tokens drift: {endpoint} in:title",
             "--json", "number"],
            check=True, capture_output=True, text=True, timeout=15,
        )
        return bool(json.loads(proc.stdout or "[]"))
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError, subprocess.TimeoutExpired):
        return False  # If dedup probe fails, let the file go through


def file_drift_issues(
    drifts: list[CheckResult],
    ground: GroundTruth,
    tag_prefix: str,
    dashboard_url: str,
) -> None:
    """File one GitHub issue per drifted endpoint. All drifted (window, metric)
    pairs for that endpoint collapse into one body so we don't fan out
    N×M near-identical issues when the root cause is shared."""
    if not shutil.which("gh"):
        print("[harness] `gh` CLI not on PATH; cannot file issues. Skipping.")
        return

    # Group drifts by endpoint only — windows/metrics fan out from one root
    # cause more often than not. If a future check has independent failures
    # per window, the body table makes that obvious.
    grouped: dict[str, list[CheckResult]] = {}
    for c in drifts:
        grouped.setdefault(c.endpoint, []).append(c)

    today = datetime.now().strftime("%Y-%m-%d")
    for endpoint, cs in grouped.items():
        # Title: pick the worst drift as the headline.
        headline = max(cs, key=lambda c: abs(c.delta))
        title = (
            f"[accuracy-audit {today}] tokens drift: {endpoint} "
            f"{headline.window_label}/{headline.metric} "
            f"ground={headline.ground} actual={headline.actual} "
            f"(delta={headline.delta:+d}; {len(cs)} drifts total)"
        )
        # Idempotency: skip if an open issue already covers this endpoint
        # today. A new day → new issue (so weekly trends are visible).
        if _open_audit_issue_exists(endpoint, today):
            print(f"[harness] open issue for {endpoint} already exists today — skipping file")
            continue
        body = _format_issue_body(endpoint, cs, ground, tag_prefix, dashboard_url)
        try:
            subprocess.run(
                ["gh", "issue", "create",
                 "--repo", GH_REPO,
                 "--title", title,
                 "--body", body,
                 "--label", "accuracy-audit,tokens,bug"],
                check=True, capture_output=True, text=True,
            )
            print(f"[harness] filed issue: {title}")
        except subprocess.CalledProcessError as e:
            # Labels may not exist on the repo — retry without them.
            try:
                proc = subprocess.run(
                    ["gh", "issue", "create",
                     "--repo", GH_REPO,
                     "--title", title,
                     "--body", body],
                    check=True, capture_output=True, text=True,
                )
                print(f"[harness] filed (no labels): {proc.stdout.strip()}")
            except subprocess.CalledProcessError as e2:
                print(f"[harness] FAILED to file issue: {e2.stderr[:300]}")


def _format_issue_body(
    endpoint: str,
    cs: list[CheckResult],
    ground: GroundTruth,
    tag_prefix: str,
    dashboard_url: str,
) -> str:
    lines = [
        f"## Drift report — `{endpoint}`",
        "",
        "Auto-filed by `scripts/accuracy_harness/tokens.py`.",
        "",
        "### Drifted (window, metric) pairs",
        "| window | metric | ground | actual | delta | tolerance |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for c in cs:
        lines.append(
            f"| {c.window_label} | {c.metric} | {c.ground} | {c.actual} | {c.delta:+d} | ±{c.tolerance} |"
        )
    lines += [
        "",
        "### Ground-truth event log",
        "```json",
        json.dumps(ground.events, indent=2),
        "```",
        "",
        f"- sessions touched: `{sorted(ground.sessions)}`",
        f"- models touched: `{ground.models}`",
        f"- tag prefix (search DuckDB): `{tag_prefix}`",
        "",
        "### To reproduce",
        "```bash",
        f"CLAWMETRY_URL={dashboard_url} \\",
        f"  python3 scripts/accuracy_harness/tokens.py \\",
        f"  --messages {len(ground.events)} --message-text 'Say PONG and nothing else.'",
        "```",
        "",
        "_Drift threshold: ±1 token (±3 for cache splits — rounding)._",
    ]
    return "\n".join(lines)


# ─── CLI ────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--messages", type=int, default=DEFAULT_MESSAGE_COUNT,
                   help=f"how many synthetic messages to send (default: {DEFAULT_MESSAGE_COUNT})")
    p.add_argument("--message-text", type=str, default=DEFAULT_MESSAGE_TEXT,
                   help=f"message body (default: {DEFAULT_MESSAGE_TEXT!r})")
    p.add_argument("--dashboard-url", type=str, default=None,
                   help="override dashboard URL (default: auto-detect 8900/8903/8905, "
                        "or $CLAWMETRY_URL)")
    p.add_argument("--openclaw-timeout", type=int, default=120,
                   help="seconds to wait per openclaw turn (default: 120)")
    p.add_argument("--file-issues", action="store_true",
                   help="file GitHub issues for any drift (requires `gh` on PATH)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    try:
        return run_harness(args)
    except KeyboardInterrupt:
        print("\n[harness] interrupted")
        return 130
    except Exception as e:
        print(f"[harness] FATAL: {e}", file=sys.stderr)
        import traceback; traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
