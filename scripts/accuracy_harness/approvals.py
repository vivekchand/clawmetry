#!/usr/bin/env python3
"""scripts/accuracy_harness/approvals.py — approvals queue verifier.

Drives a synthetic approval row → asserts pending state → decides
approve/deny → asserts decided state. Same drive→wait→assert→report
shape as ``tokens.py`` (PR #1395); shared helpers live in ``_lib.py``.

GAPS surfaced (documented in README, asserted around, not hidden):
  * NO ``/api/approvals`` endpoint — only ``/api/nemoclaw/pending-approvals``
    (status=pending only). Decided rows aren't exposed via HTTP today;
    harness asserts that surface via the daemon proxy ``query_approvals``.
  * NO ``/api/approvals/decide`` endpoint. Decisions arrive via cloud
    relay → daemon ``_apply_approval_decision``, OR via this harness's
    direct daemon-proxy ``update_approval_decision`` call. No OSS-side
    UI button decides approvals today.
  * Schema field rename: spec says ``decided_by``/``decided_at``;
    schema columns are ``resolver``/``resolved_at``. Harness asserts the
    schema names (which is what someone debugging the table will see).

Usage:
    python3 scripts/accuracy_harness/approvals.py
    python3 scripts/accuracy_harness/approvals.py --file-issues

Exit: 0 = pass, 1 = drift, 2 = harness setup failure.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from _lib import (  # noqa: E402
    discover_daemon,
    discover_dashboard_url,
    daemon_call,
    file_drift_issue_per_endpoint,
    http_get_json,
)

# ─── Config ─────────────────────────────────────────────────────────────────

DEFAULT_RESOLVER = "harness@accuracy-audit"
QUEUE_FLUSH_TIMEOUT_S = 10
QUEUE_POLL_INTERVAL_S = 0.5
# How recent ``resolved_at`` must be to pass the freshness check. The harness
# decides + reads back inside one second on a healthy box; 30s is generous
# slack for a slow CI runner.
DECIDED_AT_FRESHNESS_S = 30

# The schema field naming differs from the user-facing spec:
#   spec name      → DuckDB column
#   decided_by     → resolver
#   decided_at     → resolved_at
# Keep this map in one place so issue bodies use the schema name (which is
# what someone debugging the table will see).
SCHEMA_FIELDS = {
    "decided_by": "resolver",
    "decided_at": "resolved_at",
}


# ─── Data classes ───────────────────────────────────────────────────────────

@dataclass
class ApprovalGroundTruth:
    """One synthetic approval row we drove + the decision we made."""
    id: str
    action: str
    args: dict
    session_id: str
    requested_at: str
    decision_target: str            # "approve" or "deny"
    resolver: str
    decision_reason: str


@dataclass
class CheckResult:
    endpoint: str
    window_label: str               # used for issue-body grouping; "pending"|"decided"
    metric: str                     # which field/assertion
    ground: Any
    actual: Any
    tolerance: int = 0
    passed: bool = False

    @property
    def delta(self) -> int:
        # Numeric delta is meaningless for string comparisons; just
        # carry 0 for "match", 1 for "mismatch" so file_drift_issue_per_endpoint's
        # ``max(abs(delta))`` headline picks any drift.
        return 0 if self.passed else 1


# ─── Drive: synthetic approval via daemon proxy ─────────────────────────────

def drive_synthetic_approval(daemon: dict, *,
                              decision_target: str,
                              tag_prefix: str) -> ApprovalGroundTruth:
    """Write one synthetic approval row to DuckDB via the daemon. Returns
    the ground-truth record (id + everything we wrote, for later compare).

    The synthetic row uses a ``harness:noop`` action so it can never trigger
    a real side effect even if some downstream consumer scans for actions
    by name. ``args`` is a JSON-serialisable dict so the harness can later
    compare it field-for-field against the queried row.
    """
    aid = f"harness-{tag_prefix}-{decision_target}-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc).isoformat()
    args = {
        "synthetic": True,
        "tag": tag_prefix,
        "decision_target": decision_target,
        "note": "ACCURACY_AUDIT — safe to ignore",
    }
    row = {
        "id": aid,
        "owner_hash": "harness-owner",
        "requestor_session_id": f"harness-session-{tag_prefix}",
        "action": "harness:noop",
        "args": args,
        "status": "pending",
        "created_at": now,
    }
    daemon_call(daemon, "ingest_approval", approval=row)
    return ApprovalGroundTruth(
        id=aid,
        action="harness:noop",
        args=args,
        session_id=row["requestor_session_id"],
        requested_at=now,
        decision_target=decision_target,
        resolver=DEFAULT_RESOLVER,
        decision_reason=f"harness {decision_target} via {tag_prefix}",
    )


# ─── Wait: poll until row appears in DuckDB ─────────────────────────────────

def wait_for_pending_row(daemon: dict, approval_id: str,
                          timeout_s: int = QUEUE_FLUSH_TIMEOUT_S) -> dict | None:
    """Poll ``query_approvals(status='pending')`` until the row with id
    ``approval_id`` surfaces, or timeout. Returns the row dict or None."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rows = daemon_call(daemon, "query_approvals", status="pending", limit=500) or []
        for r in rows:
            if r.get("id") == approval_id:
                return r
        time.sleep(QUEUE_POLL_INTERVAL_S)
    return None


def wait_for_decided_row(daemon: dict, approval_id: str, expected_status: str,
                          timeout_s: int = QUEUE_FLUSH_TIMEOUT_S) -> dict | None:
    """Poll ``query_approvals(status=expected_status)`` until the row appears."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rows = daemon_call(daemon, "query_approvals",
                           status=expected_status, limit=500) or []
        for r in rows:
            if r.get("id") == approval_id:
                return r
        time.sleep(QUEUE_POLL_INTERVAL_S)
    return None


# ─── Assertion builders ─────────────────────────────────────────────────────

def _eq_check(endpoint: str, stage: str, metric: str,
              ground: Any, actual: Any) -> CheckResult:
    """Equality check shorthand."""
    return CheckResult(endpoint=endpoint, window_label=stage, metric=metric,
                       ground=ground, actual=actual, passed=ground == actual)


def assert_pending_row(row: dict | None,
                        ground: ApprovalGroundTruth) -> list[CheckResult]:
    """Compare a fetched row against ground-truth on the pending side."""
    ep = "daemon.query_approvals"
    if row is None:
        return [_eq_check(ep, "pending", "row_present", ground.id, None)]
    return [
        _eq_check(ep, "pending", "row_present", ground.id, row.get("id")),
        _eq_check(ep, "pending", "action", ground.action, row.get("action")),
        _eq_check(ep, "pending", "status", "pending", row.get("status")),
        _eq_check(ep, "pending", "session_id", ground.session_id,
                  row.get("requestor_session_id")),
        _eq_check(ep, "pending", "args", ground.args, row.get("args")),
        _eq_check(ep, "pending", "created_at", ground.requested_at,
                  row.get("created_at")),
    ]


def assert_dashboard_pending(payload: dict | None,
                              ground: ApprovalGroundTruth) -> list[CheckResult]:
    """Verify ``/api/nemoclaw/pending-approvals`` includes the row.
    The endpoint coerces the schema to a legacy NemoClaw shape; we assert
    the user-facing fields the dashboard JS reads."""
    ep = "/api/nemoclaw/pending-approvals"
    if not isinstance(payload, dict):
        return [_eq_check(ep, "pending", "payload_type", "dict",
                          type(payload).__name__)]
    approvals = payload.get("approvals") or []
    matching = next((a for a in approvals if a.get("id") == ground.id), None)
    out = [_eq_check(ep, "pending", "row_present", ground.id,
                     matching.get("id") if matching else None)]
    if matching is None:
        return out
    out += [
        _eq_check(ep, "pending", "action", ground.action, matching.get("action")),
        _eq_check(ep, "pending", "args", ground.args, matching.get("args")),
        _eq_check(ep, "pending", "status", "pending", matching.get("status")),
        _eq_check(ep, "pending", "created_at", ground.requested_at,
                  matching.get("created_at")),
    ]
    return out


def assert_decided_row(row: dict | None,
                        ground: ApprovalGroundTruth) -> list[CheckResult]:
    """Compare a fetched decided row against ground-truth (post update)."""
    ep = "daemon.query_approvals"
    expected_status = "approved" if ground.decision_target == "approve" else "denied"
    if row is None:
        return [_eq_check(ep, "decided", "row_present", ground.id, None)]
    out = [
        _eq_check(ep, "decided", "status", expected_status, row.get("status")),
        _eq_check(ep, "decided", "decision", ground.decision_target,
                  row.get("decision")),
        _eq_check(ep, "decided", SCHEMA_FIELDS["decided_by"], ground.resolver,
                  row.get("resolver")),
        _eq_check(ep, "decided", "decision_reason", ground.decision_reason,
                  row.get("decision_reason")),
    ]
    # ``resolved_at`` freshness — must be within DECIDED_AT_FRESHNESS_S of now.
    fresh_ok = False
    actual_resolved = row.get("resolved_at")
    if isinstance(actual_resolved, str) and actual_resolved:
        try:
            ra = datetime.fromisoformat(actual_resolved.replace("Z", "+00:00"))
            fresh_ok = abs((datetime.now(timezone.utc) - ra).total_seconds()
                            ) < DECIDED_AT_FRESHNESS_S
        except ValueError:
            pass
    out.append(CheckResult(
        endpoint=ep, window_label="decided",
        metric=f"{SCHEMA_FIELDS['decided_at']}_fresh",
        ground=f"<{DECIDED_AT_FRESHNESS_S}s ago",
        actual=actual_resolved, passed=fresh_ok,
    ))
    return out


def assert_pending_no_longer_lists(payload: dict | None,
                                    ground: ApprovalGroundTruth) -> list[CheckResult]:
    """After a decision, ``/api/nemoclaw/pending-approvals`` must NOT list the row."""
    ep = "/api/nemoclaw/pending-approvals"
    if not isinstance(payload, dict):
        return [_eq_check(ep, "post-decide", "payload_type", "dict",
                          type(payload).__name__)]
    leaked = any(a.get("id") == ground.id for a in (payload.get("approvals") or []))
    return [CheckResult(
        endpoint=ep, window_label="post-decide",
        metric="excluded_after_decide", ground="absent",
        actual="present" if leaked else "absent", passed=not leaked,
    )]


# ─── Issue body builder ─────────────────────────────────────────────────────

def _format_approvals_issue_body(endpoint: str,
                                  cs: list[CheckResult],
                                  grounds: list[ApprovalGroundTruth],
                                  dashboard_url: str) -> str:
    lines = [
        f"## Drift report — `{endpoint}`",
        "",
        "Auto-filed by `scripts/accuracy_harness/approvals.py`.",
        "",
        "### Drifted assertions",
        "| stage | metric | ground | actual | result |",
        "|---|---|---|---|---|",
    ]
    for c in cs:
        lines.append(
            f"| {c.window_label} | {c.metric} | "
            f"`{json.dumps(c.ground, default=str)[:80]}` | "
            f"`{json.dumps(c.actual, default=str)[:80]}` | "
            f"{'PASS' if c.passed else 'DRIFT'} |"
        )
    lines += [
        "",
        "### Ground-truth approvals (what we drove)",
        "```json",
        json.dumps([{
            "id": g.id, "action": g.action,
            "decision_target": g.decision_target,
            "resolver": g.resolver,
            "requested_at": g.requested_at,
        } for g in grounds], indent=2),
        "```",
        "",
        "### Root-cause hint",
        "If `daemon.query_approvals` drifts for `decision`/`resolver`/`resolved_at`, "
        "the bug is most likely in `clawmetry/local_store.py:update_approval_decision` "
        "(line ~1860) — that's the single write path. ",
        "If `/api/nemoclaw/pending-approvals` drifts but the daemon-proxy view is correct, "
        "the bug is in `routes/nemoclaw.py:_try_local_store_approvals` (line ~61) — that's "
        "where the schema-to-legacy-shape coercion happens.",
        "",
        "### To reproduce",
        "```bash",
        f"CLAWMETRY_URL={dashboard_url} \\",
        "  python3 scripts/accuracy_harness/approvals.py",
        "```",
        "",
        "_The synthetic row uses `action='harness:noop'` and a unique id prefix "
        "(`harness-…`); these never match a real approval policy._",
    ]
    return "\n".join(lines)


# ─── Main flow ──────────────────────────────────────────────────────────────

def run_one_round(daemon: dict, dashboard_url: str, *,
                   decision_target: str, tag_prefix: str
                   ) -> tuple[ApprovalGroundTruth, list[CheckResult]]:
    """Drive + assert one approval round (one of approve/deny). Returns
    (ground-truth, all-check-results) for the round."""
    print(f"[harness] driving synthetic approval (decision_target={decision_target})…")
    ground = drive_synthetic_approval(
        daemon, decision_target=decision_target, tag_prefix=tag_prefix,
    )
    print(f"  id={ground.id} action={ground.action} session={ground.session_id}")

    print(f"[harness] waiting for pending row to surface "
          f"(timeout={QUEUE_FLUSH_TIMEOUT_S}s)…")
    pending = wait_for_pending_row(daemon, ground.id)
    if pending is None:
        print(f"  [drive] FAILED: row never landed in DuckDB")
    else:
        print(f"  [drive] row landed (created_at={pending.get('created_at')})")
    pending_checks = assert_pending_row(pending, ground)

    print("[harness] fetching /api/nemoclaw/pending-approvals…")
    try:
        payload = http_get_json(f"{dashboard_url}/api/nemoclaw/pending-approvals",
                                timeout=10.0)
    except Exception as e:
        print(f"  [endpoint] FAILED: {e}")
        payload = None
    pending_endpoint_checks = assert_dashboard_pending(payload, ground)

    print(f"[harness] deciding {decision_target!r} via daemon proxy "
          f"(resolver={ground.resolver})…")
    n = daemon_call(
        daemon, "update_approval_decision",
        approval_id=ground.id,
        decision=ground.decision_target,
        resolver=ground.resolver,
        reason=ground.decision_reason,
    )
    if n != 1:
        print(f"  [decide] FAILED: update_approval_decision returned {n}")

    expected_status = "approved" if decision_target == "approve" else "denied"
    print(f"[harness] waiting for decided row "
          f"(status={expected_status}, timeout={QUEUE_FLUSH_TIMEOUT_S}s)…")
    decided = wait_for_decided_row(daemon, ground.id, expected_status)
    if decided is None:
        print("  [decide] FAILED: row never appeared in decided view")
    else:
        print(f"  [decide] row decided (resolved_at={decided.get('resolved_at')})")
    decided_checks = assert_decided_row(decided, ground)

    # Re-fetch pending list and confirm the row is gone.
    try:
        payload2 = http_get_json(f"{dashboard_url}/api/nemoclaw/pending-approvals",
                                 timeout=10.0)
    except Exception as e:
        print(f"  [endpoint post-decide] FAILED: {e}")
        payload2 = None
    post_decide_checks = assert_pending_no_longer_lists(payload2, ground)

    return ground, pending_checks + pending_endpoint_checks + decided_checks + post_decide_checks


def run_harness(args: argparse.Namespace) -> int:
    print(f"[harness] approvals accuracy audit — {datetime.now(timezone.utc).isoformat()}")

    dashboard_url = discover_dashboard_url(args.dashboard_url,
                                            probe_path="/api/usage")
    print(f"[harness] dashboard: {dashboard_url}")

    daemon = discover_daemon()
    if not daemon:
        print("[harness] FATAL: daemon not discoverable; "
              "the approvals harness needs a running daemon to ingest + "
              "decide rows. See ~/.clawmetry/local_query.json.", file=sys.stderr)
        return 2
    print(f"[harness] daemon proxy: 127.0.0.1:{daemon['port']}")

    run_id = uuid.uuid4().hex[:8]
    tag_prefix = f"AUDIT_{run_id}"
    print(f"[harness] tag prefix: {tag_prefix}")

    grounds: list[ApprovalGroundTruth] = []
    all_checks: list[CheckResult] = []
    for target in ("approve", "deny"):
        ground, checks = run_one_round(
            daemon, dashboard_url,
            decision_target=target, tag_prefix=tag_prefix,
        )
        grounds.append(ground)
        all_checks.extend(checks)
        print()

    # Report.
    print("─" * 78)
    print(f"{'ENDPOINT':<35} {'STAGE':<13} {'METRIC':<25} {'RESULT':<6}")
    print("─" * 78)
    drifts: list[CheckResult] = []
    for c in all_checks:
        result = "PASS" if c.passed else "DRIFT"
        if not c.passed:
            drifts.append(c)
        print(f"{c.endpoint:<35} {c.window_label:<13} {c.metric:<25} {result:<6}")
    print("─" * 78)
    print(f"summary: {sum(1 for c in all_checks if c.passed)} pass / "
          f"{len(drifts)} drift / {len(all_checks)} total checks")
    print(f"approvals exercised: {[g.id for g in grounds]}")

    if not drifts:
        print()
        print("[harness] ALL CHECKS PASSED — approvals queue is accurate on this build.")
        return 0

    print()
    print("[harness] DRIFT DETECTED:")
    for c in drifts:
        print(f"  - {c.endpoint} stage={c.window_label} metric={c.metric}: "
              f"ground={c.ground!r} actual={c.actual!r}")

    if args.file_issues:
        def _body_builder(endpoint: str, cs: list) -> str:
            return _format_approvals_issue_body(endpoint, cs, grounds, dashboard_url)
        file_drift_issue_per_endpoint(
            harness_label="approvals", drifts=drifts, body_builder=_body_builder,
        )
    else:
        print("[harness] (re-run with --file-issues to open GitHub issues)")
    return 1


# ─── CLI ────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dashboard-url", type=str, default=None,
                   help="override dashboard URL (default: auto-detect 8900/8903/8905, "
                        "or $CLAWMETRY_URL)")
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
