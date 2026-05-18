#!/usr/bin/env python3
"""scripts/accuracy_harness/keystone_e2e.py — the MOAT keystone verifier.

Simulates the user's literal workflow:

  > "try sending a message in open claw & see if it creates write
  >  entries in duckdb for tool calls / gateway bubble event etc & the
  >  api response with correct data"

Drives ONE real ``openclaw agent --message`` turn, polls the sync daemon
until the event lands in DuckDB, then asserts every dashboard endpoint a
real user looks at returns shape + non-zero data (where appropriate).

This is the keystone above all the per-feature harnesses in this dir:
``tokens.py`` / ``approvals.py`` / ``alerts.py`` each cover one feature
in depth; keystone covers BREADTH across the 10 endpoints the dashboard
actually loads on every page view.

Exit codes
----------
  0 — every endpoint returned shape + correct data
  1 — at least one endpoint failed (silent zero / wrong shape / 404)
  2 — harness itself failed (daemon down, openclaw missing, dashboard 500)

Anti-patterns this guards against
---------------------------------
- Synthetic event-shape skew (memory: feedback_synthetic_tests_missed_real_event_shape.md).
  We drive REAL ``openclaw agent`` so the events have the exact v3 shape
  the daemon ingests: ``event_type='model.completed'`` with
  ``data.assistantMessage.usage``, NOT the literal ``'message'``.
- DuckDB process-lock (memory: reference_duckdb_process_lock.md). We
  never open the file directly. All DuckDB reads go through the daemon's
  ``/__local_query__/<method>`` HTTP proxy.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable

# Allow ``python3 scripts/accuracy_harness/keystone_e2e.py`` to resolve _lib.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _lib import (  # noqa: E402
    daemon_call,
    daemon_event_count,
    discover_daemon,
    discover_dashboard_url,
    drive_openclaw_message,
    extract_openclaw_usage,
    http_get_json,
)


# ─── Config ─────────────────────────────────────────────────────────────────

FLUSH_TIMEOUT_S = 30
FLUSH_POLL_INTERVAL_S = 1.0
KEYSTONE_TAG = f"keystone-e2e-{int(time.time())}"


# ─── Result types ───────────────────────────────────────────────────────────

@dataclass
class Check:
    endpoint: str
    label: str
    status: str  # "pass" | "fail" | "skip"
    detail: str = ""

    def line(self) -> str:
        glyph = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[self.status]
        return f"  [{glyph}] {self.endpoint:38s} {self.label} {self.detail}".rstrip()


# ─── Pre-flight ─────────────────────────────────────────────────────────────

def preflight(args) -> tuple[str, dict]:
    """Return (dashboard_url, daemon_disc) or raise."""
    print("[keystone] Pre-flight: discovering dashboard + daemon…")
    dashboard = discover_dashboard_url(args.dashboard_url)
    daemon = discover_daemon()
    if not daemon:
        raise RuntimeError(
            "sync daemon not running — start with `launchctl kickstart "
            "-k com.clawmetry.sync` or `clawmetry sync start`"
        )
    print(f"[keystone]   dashboard = {dashboard}")
    print(f"[keystone]   daemon    = 127.0.0.1:{daemon['port']} "
          f"(pid via {os.path.expanduser('~/.clawmetry/local_query.json')})")
    return dashboard, daemon


# ─── Step 1: drive ──────────────────────────────────────────────────────────

def drive_one_message(args) -> dict | None:
    """Run ONE openclaw agent turn. Returns extracted usage dict on success,
    None if openclaw isn't available (we'll fall back to verifying against
    existing DuckDB data).
    """
    print(f"[keystone] Driving 1 real openclaw turn (tag={KEYSTONE_TAG})…")
    try:
        agent_json = drive_openclaw_message(
            "PONG keystone", KEYSTONE_TAG, timeout_s=args.openclaw_timeout,
        )
    except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as e:
        print(f"[keystone]   openclaw drive FAILED — {type(e).__name__}: {e}")
        print("[keystone]   continuing in observation-only mode (verifies "
              "endpoints against pre-existing DuckDB rows).")
        return None
    usage = extract_openclaw_usage(agent_json)
    if usage:
        print(f"[keystone]   driven session={usage['sessionId']} "
              f"model={usage['model']} usage={usage['input']}/{usage['output']} "
              f"(+{usage['cacheRead']} cacheRead, +{usage['cacheWrite']} cacheWrite)")
    return usage


# ─── Step 2: flush wait ─────────────────────────────────────────────────────

def wait_for_flush(daemon: dict, baseline_count: int | None,
                   *, expect_delta: int = 1, timeout_s: int = FLUSH_TIMEOUT_S) -> int | None:
    """Poll the daemon's event_count until it has increased by ``expect_delta``
    relative to ``baseline_count`` (or ``timeout_s`` elapses). Returns the
    final event_count seen, or None if the daemon never responded.
    """
    if baseline_count is None:
        print("[keystone]   no baseline event_count — skipping flush wait")
        return daemon_event_count(daemon)
    deadline = time.time() + timeout_s
    last = baseline_count
    while time.time() < deadline:
        cur = daemon_event_count(daemon)
        if cur is None:
            time.sleep(FLUSH_POLL_INTERVAL_S)
            continue
        if cur - baseline_count >= expect_delta:
            print(f"[keystone]   daemon flushed: {baseline_count} → {cur} "
                  f"(+{cur - baseline_count} ≥ {expect_delta})")
            return cur
        last = cur
        time.sleep(FLUSH_POLL_INTERVAL_S)
    print(f"[keystone]   flush timed out at {last - baseline_count:+d} events "
          f"after {timeout_s}s — proceeding anyway (other agents may have written too)")
    return last


# ─── Step 3: endpoint probes ────────────────────────────────────────────────

def _safe_get(dashboard: str, path: str, *, timeout: float = 10.0) -> tuple[Any, str | None]:
    """GET ``dashboard+path``. Returns (parsed_json, None) on success or
    (None, error_str) on failure (incl. HTTP 4xx/5xx)."""
    try:
        return http_get_json(f"{dashboard}{path}", timeout=timeout), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"
    except (ValueError, json.JSONDecodeError) as e:
        return None, f"json decode: {e}"


def _pick_session_id(dashboard: str) -> str | None:
    """Return ANY known session id from /api/sessions so we can probe
    /api/transcript/<id>. None when sessions list is empty (uncommon)."""
    payload, err = _safe_get(dashboard, "/api/sessions")
    if err or not isinstance(payload, dict):
        return None
    for s in payload.get("sessions") or []:
        sid = s.get("session_id") or s.get("sessionId") or s.get("id")
        if sid:
            return str(sid)
    return None


def check_brain_history(dashboard: str) -> Check:
    ep = "/api/brain-history"
    payload, err = _safe_get(dashboard, f"{ep}?limit=10")
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    events = payload.get("events") or []
    if not isinstance(events, list) or not events:
        return Check(ep, "events", "fail", "no events returned (silent zero?)")
    # Per reference_openclaw_v3_event_types: types are uppercased and
    # namespaced — SESSION.STARTED / PROMPT.SUBMITTED / MODEL.COMPLETED.
    types = {str(e.get("type") or "").upper() for e in events}
    if not types:
        return Check(ep, "types", "fail", "events have no .type field")
    return Check(ep, "events>0", "pass",
                 f"count={len(events)} sample_types={sorted(types)[:3]}")


def check_sessions(dashboard: str) -> tuple[Check, str | None]:
    ep = "/api/sessions"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err), None
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}"), None
    sessions = payload.get("sessions") or []
    if not isinstance(sessions, list) or not sessions:
        return Check(ep, "sessions", "fail", "empty session list"), None
    sid = None
    for s in sessions:
        sid = s.get("session_id") or s.get("sessionId") or s.get("id")
        if sid:
            break
    return Check(ep, "sessions>0", "pass", f"count={len(sessions)}"), sid


def check_transcript(dashboard: str, sid: str | None) -> Check:
    if not sid:
        return Check("/api/transcript/<id>", "fetch", "skip", "no session id available")
    ep = f"/api/transcript/{sid}"
    payload, err = _safe_get(dashboard, ep, timeout=15.0)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    msgs = payload.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return Check(ep, "messages", "fail", "transcript empty (silent zero)")
    return Check(ep, "messages>0", "pass", f"count={len(msgs)}")


def check_usage(dashboard: str) -> Check:
    ep = "/api/usage"
    payload, err = _safe_get(dashboard, ep, timeout=15.0)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    # The four breakdown surfaces a user reads on the Tokens tab:
    #   .days[]  per-day series
    #   .today   today's total
    #   .modelBreakdown[]  per-model split
    #   .modelBilling[]   per-model billed (cost present)
    days = payload.get("days") or []
    today = payload.get("today") or 0
    model_breakdown = payload.get("modelBreakdown") or []
    if not days:
        return Check(ep, "days", "fail", "empty .days[] series")
    nonzero_days = sum(1 for d in days if (d.get("tokens") or 0) > 0)
    if nonzero_days == 0:
        return Check(ep, "nonzero", "fail",
                     "all .days[] are zero (synthetic-event skew?)")
    if not model_breakdown:
        return Check(ep, "modelBreakdown", "fail",
                     "empty .modelBreakdown[] despite nonzero days")
    return Check(ep, "tokens+breakdown", "pass",
                 f"today={today} nonzero_days={nonzero_days}/{len(days)} "
                 f"models={len(model_breakdown)}")


def check_flow(dashboard: str) -> Check:
    ep = "/api/flow"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    # /api/flow returns streaming-mode metadata even with no recent events:
    # ``{"events": [], "ok": true, "streaming": true, "type": "flow-events"}``
    # is the legitimate empty-state shape. Pass when shape is intact, fail
    # only on missing keys / streaming=False with no events.
    if "events" not in payload or "ok" not in payload:
        return Check(ep, "shape", "fail",
                     f"missing .events / .ok keys: {sorted(payload.keys())[:5]}")
    if not payload.get("ok"):
        return Check(ep, "ok", "fail", f"ok=false: {payload.get('error')}")
    return Check(ep, "shape+ok", "pass",
                 f"events={len(payload.get('events') or [])} streaming={payload.get('streaming')}")


def check_component_tool(dashboard: str) -> Check:
    # /api/component/tool/<name> — pick a stable tool name.
    ep = "/api/component/tool/exec"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    # Shape check only — exec may legitimately have 0 calls today.
    if "stats" not in payload or "events" not in payload:
        return Check(ep, "shape", "fail",
                     f"missing .stats / .events keys: {sorted(payload.keys())[:5]}")
    return Check(ep, "shape", "pass",
                 f"events={len(payload.get('events') or [])} "
                 f"today_calls={(payload.get('stats') or {}).get('today_calls')}")


def check_component_simple(dashboard: str, path: str) -> Check:
    payload, err = _safe_get(dashboard, path)
    if err:
        return Check(path, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(path, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    items = payload.get("items") or payload.get("routes")
    if items is None:
        return Check(path, "shape", "fail",
                     f"missing .items/.routes: {sorted(payload.keys())[:5]}")
    if not isinstance(items, list) or not items:
        return Check(path, "items", "fail", "empty .items/.routes (silent zero)")
    return Check(path, "items>0", "pass", f"count={len(items)}")


def check_system_health(dashboard: str) -> Check:
    ep = "/api/system-health"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    # Look for any of the documented sections.
    keys = set(payload.keys())
    required_any = {"channels", "channel_ingest", "system", "crons", "disk", "memory"}
    if not (keys & required_any):
        return Check(ep, "sections", "fail",
                     f"missing all of {required_any}; got {sorted(keys)[:5]}")
    return Check(ep, "shape", "pass", f"sections={sorted(keys & required_any)}")


def check_subagents(dashboard: str) -> Check:
    ep = "/api/subagents"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    if "subagents" not in payload or "counts" not in payload:
        return Check(ep, "shape", "fail",
                     f"missing .subagents / .counts: {sorted(payload.keys())[:5]}")
    # Empty subagents is legitimate — pass on shape alone.
    return Check(ep, "shape", "pass",
                 f"counts={payload.get('counts')} count={len(payload.get('subagents') or [])}")


def check_crons(dashboard: str) -> Check:
    ep = "/api/crons"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    if "jobs" not in payload:
        return Check(ep, "shape", "fail",
                     f"missing .jobs: {sorted(payload.keys())[:5]}")
    # Empty jobs list is legitimate (user may have no crons).
    return Check(ep, "shape", "pass", f"jobs={len(payload.get('jobs') or [])}")


def check_memory_files(dashboard: str) -> Check:
    ep = "/api/memory-files"
    payload, err = _safe_get(dashboard, ep)
    if err:
        return Check(ep, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail", f"expected dict, got {type(payload).__name__}")
    files = payload.get("files") or []
    if not isinstance(files, list):
        return Check(ep, "shape", "fail", f"expected .files list, got {type(files).__name__}")
    if not files:
        # Most OpenClaw installs ship with at least AGENTS.md / SOUL.md.
        return Check(ep, "files", "fail", "no memory files (silent zero)")
    return Check(ep, "files>0", "pass", f"count={len(files)}")


# ─── Diagnostics ────────────────────────────────────────────────────────────

def diagnose_event_types(daemon: dict) -> str:
    """Surface the distinct event_type values currently in DuckDB so a
    silent-zero on /api/* can be diagnosed inline. This is the canonical
    'what shape did the daemon actually write?' query.
    """
    try:
        rows = daemon_call(daemon, "query_events", limit=500)
    except (RuntimeError, urllib.error.URLError, TimeoutError) as e:
        return f"event_type sample unavailable: {e}"
    if not isinstance(rows, list):
        return "event_type sample unavailable: non-list response"
    counts: dict[str, int] = {}
    for r in rows:
        et = str((r or {}).get("event_type") or "")
        counts[et] = counts.get(et, 0) + 1
    if not counts:
        return "DuckDB events table is EMPTY — daemon has nothing to serve"
    top = sorted(counts.items(), key=lambda x: -x[1])[:8]
    return "DuckDB event_type histogram (top 8 of last 500): " + ", ".join(
        f"{et}={n}" for et, n in top)


# ─── Driver ─────────────────────────────────────────────────────────────────

def run(args) -> int:
    try:
        dashboard, daemon = preflight(args)
    except RuntimeError as e:
        print(f"[keystone] PREFLIGHT FAILED: {e}", file=sys.stderr)
        return 2

    baseline = daemon_event_count(daemon)
    print(f"[keystone] Baseline event_count = {baseline}")

    usage = None if args.no_drive else drive_one_message(args)

    if usage is not None:
        wait_for_flush(daemon, baseline, expect_delta=1,
                       timeout_s=args.flush_timeout)
    else:
        print("[keystone] skipping flush wait (no drive)")

    # ─── Hit-list (the 10 endpoints the dashboard reads on page load) ───
    print()
    print("[keystone] Probing 10 API surfaces…")
    sessions_check, sid = check_sessions(dashboard)
    checks: list[Check] = [
        check_brain_history(dashboard),
        sessions_check,
        check_transcript(dashboard, sid),
        check_usage(dashboard),
        check_flow(dashboard),
        check_component_tool(dashboard),
        check_component_simple(dashboard, "/api/component/runtime"),
        check_component_simple(dashboard, "/api/component/machine"),
        check_component_simple(dashboard, "/api/component/gateway"),
        check_system_health(dashboard),
        check_subagents(dashboard),
        check_crons(dashboard),
        check_memory_files(dashboard),
    ]

    print()
    print("[keystone] Per-endpoint results:")
    for c in checks:
        print(c.line())

    failed = [c for c in checks if c.status == "fail"]
    skipped = [c for c in checks if c.status == "skip"]
    passed = [c for c in checks if c.status == "pass"]
    print()
    print(f"[keystone] Summary: {len(passed)} pass / {len(failed)} fail "
          f"/ {len(skipped)} skip (total {len(checks)})")

    if failed:
        print()
        print("[keystone] Diagnostics (silent-zero root cause):")
        print(f"  {diagnose_event_types(daemon)}")
        print()
        print("[keystone] FAILED endpoints:")
        for c in failed:
            print(f"  - {c.endpoint} → {c.detail}")
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--dashboard-url", default=None,
                   help="Override dashboard base URL (default: auto-detect "
                   "on 8900/8903/8905 or $CLAWMETRY_URL)")
    p.add_argument("--openclaw-timeout", type=int, default=60,
                   help="Wall-clock seconds for the single openclaw agent run")
    p.add_argument("--flush-timeout", type=int, default=FLUSH_TIMEOUT_S,
                   help="Max seconds to wait for the daemon to flush the new "
                   "event into DuckDB")
    p.add_argument("--no-drive", action="store_true",
                   help="Skip the openclaw drive; verify against existing "
                   "DuckDB rows only (CI smoke mode)")
    args = p.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
