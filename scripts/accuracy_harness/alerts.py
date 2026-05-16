#!/usr/bin/env python3
"""scripts/accuracy_harness/alerts.py — alert-rule round-trip verifier.

Drives the full alerts pipeline: drive ground truth via one ``openclaw``
turn → create a tripping threshold rule via ``POST /api/alerts/rules`` →
force-trip the evaluator through the ``/api/_harness/inject-cost`` test
hook (60s natural cadence is too slow for CI) → assert the row appears in
``/api/alerts/history`` with correct rule_id/type/message → assert the
webhook dispatch lands on a local capture listener → clean up.

GAPS this harness surfaces by design (asserted, not hidden):
  * Evaluator reads ``metrics_store['cost']`` (in-process OTLP buffer),
    NOT DuckDB. Most installs have no OTLP flow so daily_spent stays 0
    and no real-spend rule can fire — harness captures + reports this.
  * Natural cadence is 60s (``_budget_monitor_loop`` tick); hook forces
    a synchronous pass.
  * No ``alert_dispatch_attempts`` table — webhook dispatch is fire-and-
    forget. Harness verifies via a local capture listener.

Usage:
    CLAWMETRY_HARNESS_HOOKS=1 python3 scripts/accuracy_harness/alerts.py
    CLAWMETRY_HARNESS_HOOKS=1 python3 scripts/accuracy_harness/alerts.py --file-issues

Exit: 0 = pass, 1 = drift, 2 = harness setup failure.
"""
from __future__ import annotations

import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))

import argparse
import http.server
import json
import re
import socketserver
import sys
import threading
import time
import urllib.error
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from _lib import (  # noqa: E402
    discover_dashboard_url,
    drive_openclaw_message,
    extract_openclaw_usage,
    file_drift_issue_per_endpoint,
    http_delete_json,
    http_get_json,
    http_post_json,
    wait_for_event,
)

# ─── Config ─────────────────────────────────────────────────────────────────

TRIPPING_THRESHOLD_USD = 0.001          # any real opus turn blows past this
FORCED_INJECT_USD = 0.01                # synthetic spend pushed through hook
TOLERANCE_PCT = 0.05                    # ±5% on triggered_value
HISTORY_WAIT_S = 10
WEBHOOK_WAIT_S = 10
NATURAL_TICK_WAIT_S = 90                # fallback if hook disabled


# ─── Data classes ───────────────────────────────────────────────────────────

@dataclass
class AlertGround:
    rule_id: str
    rule_name_tag: str
    threshold_usd: float
    real_spend_usd: float        # estimated from openclaw usage block
    forced_inject_usd: float
    expected_triggered_value: float
    capture_url: str


@dataclass
class CheckResult:
    endpoint: str
    window_label: str            # "create"|"spend_visibility"|"fire"|"dispatch"|"cleanup"
    metric: str
    ground: Any
    actual: Any
    tolerance: float = 0.0
    passed: bool = False
    notes: str = ""

    @property
    def delta(self) -> int:
        return 0 if self.passed else 1


# ─── Webhook capture listener ──────────────────────────────────────────────

class _WebhookCapture:
    """Localhost HTTP listener; records every POST body."""

    def __init__(self):
        self.received: list[dict] = []
        self._server: socketserver.TCPServer | None = None
        self._thread: threading.Thread | None = None
        self.port: int = 0

    def start(self) -> None:
        received = self.received

        class Handler(http.server.BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b""
                try:
                    body = json.loads(raw.decode("utf-8") or "{}")
                except (UnicodeDecodeError, ValueError):
                    body = {"_raw": raw[:200].decode("utf-8", "replace")}
                received.append({"received_at": time.time(),
                                 "path": self.path, "body": body})
                self.send_response(200)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def log_message(self, *a, **kw):
                pass

        self._server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        self.port = self._server.server_address[1]
        self._thread = threading.Thread(target=self._server.serve_forever,
                                        daemon=True)
        self._thread.start()

    def url(self) -> str:
        return f"http://127.0.0.1:{self.port}/harness-webhook"

    def stop(self) -> None:
        if self._server:
            try:
                self._server.shutdown()
                self._server.server_close()
            except OSError:
                pass


# ─── Drive ──────────────────────────────────────────────────────────────────

def _estimate_cost_from_usage(usage: dict) -> float:
    """Estimate USD for the openclaw turn using the same pricing table the
    dashboard uses — keeps the assertion in sync with the dashboard."""
    try:
        from clawmetry.providers_pricing import estimate_cost_usd
    except ImportError:
        return 0.0
    return estimate_cost_usd(provider="anthropic",
                             tokens_in=int(usage.get("input") or 0),
                             tokens_out=int(usage.get("output") or 0),
                             model=usage.get("model") or "claude-opus-4")


def drive_real_spend(tag: str) -> tuple[dict | None, float]:
    print(f"[harness] driving real openclaw turn (tag={tag})…")
    agent_json = drive_openclaw_message("Say PONG and nothing else.", tag)
    usage = extract_openclaw_usage(agent_json)
    if not usage:
        print("  [drive] WARN: openclaw response had no usage block")
        return None, 0.0
    cost = _estimate_cost_from_usage(usage)
    print(f"  [drive] usage={usage} estimated_cost=${cost:.6f}")
    return usage, cost


def create_rule(dashboard_url: str, ground_tag: str) -> str:
    body = {"type": "threshold", "threshold": TRIPPING_THRESHOLD_USD,
            "channels": ["banner", "webhook"], "cooldown_min": 1,
            "enabled": True}
    resp = http_post_json(f"{dashboard_url}/api/alerts/rules", body=body)
    rid = resp.get("id")
    if not rid:
        raise RuntimeError(f"rule create returned no id: {resp}")
    print(f"[harness] created rule id={rid} tag={ground_tag} "
          f"threshold=${TRIPPING_THRESHOLD_USD}")
    return rid


def configure_webhook(dashboard_url: str, capture_url: str) -> dict:
    prior = http_get_json(f"{dashboard_url}/api/alerts/webhook")
    http_post_json(f"{dashboard_url}/api/alerts/webhook",
                   body={"webhook_url": capture_url})
    return prior or {}


def restore_webhook(dashboard_url: str, prior: dict) -> None:
    try:
        http_post_json(f"{dashboard_url}/api/alerts/webhook", body={
            "webhook_url": prior.get("webhook_url") or "",
            "slack_webhook_url": prior.get("slack_webhook_url") or "",
            "discord_webhook_url": prior.get("discord_webhook_url") or "",
        })
    except Exception as e:
        print(f"[harness] WARN: webhook restore failed: {e}")


def delete_rule(dashboard_url: str, rule_id: str) -> bool:
    try:
        http_delete_json(f"{dashboard_url}/api/alerts/rules/{rule_id}")
        return True
    except (urllib.error.URLError, urllib.error.HTTPError) as e:
        print(f"[harness] WARN: rule delete failed: {e}")
        return False


# ─── Trip + wait ────────────────────────────────────────────────────────────

def force_trip_via_hook(dashboard_url: str, rule_id: str) -> dict | None:
    try:
        return http_post_json(
            f"{dashboard_url}/api/_harness/inject-cost",
            body={"usd": FORCED_INJECT_USD, "model": "claude-opus-4-7",
                  "provider": "anthropic", "clear_cooldown_for": [rule_id]},
        )
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace") if e.fp else str(e)
        print(f"[harness] hook returned {e.code}: {body[:200]}")
        return None
    except urllib.error.URLError as e:
        print(f"[harness] hook unreachable: {e}")
        return None


def wait_for_fire(dashboard_url: str, rule_id: str,
                  timeout_s: float) -> dict | None:
    def _probe():
        try:
            payload = http_get_json(
                f"{dashboard_url}/api/alerts/history?limit=500", timeout=5.0)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            print(f"  [poll] /api/alerts/history error: {e}")
            return None
        for row in (payload.get("alerts") or []):
            if row.get("rule_id") == rule_id:
                return row
        return None
    return wait_for_event(_probe, timeout=timeout_s, interval=1.0,
                          description=f"history row for rule {rule_id}")


def wait_for_webhook(capture: _WebhookCapture, timeout_s: float) -> dict | None:
    return wait_for_event(lambda: capture.received[-1] if capture.received else None,
                          timeout=timeout_s, interval=0.25, description="webhook")


# ─── Asserts ────────────────────────────────────────────────────────────────

def _eq(endpoint, stage, metric, ground, actual, notes="") -> CheckResult:
    return CheckResult(endpoint=endpoint, window_label=stage, metric=metric,
                       ground=ground, actual=actual, passed=ground == actual,
                       notes=notes)


def _within(endpoint, stage, metric, ground, actual, tolerance_pct) -> CheckResult:
    passed = (abs(actual) < 1e-6) if ground == 0 else (
        abs(actual - ground) / abs(ground) <= tolerance_pct)
    return CheckResult(endpoint=endpoint, window_label=stage, metric=metric,
                       ground=ground, actual=actual, tolerance=tolerance_pct,
                       passed=passed)


def assert_rule_created(dashboard_url, ground) -> list[CheckResult]:
    ep = "/api/alerts/rules"
    try:
        payload = http_get_json(f"{dashboard_url}{ep}")
    except Exception as e:
        return [_eq(ep, "create", "list_reachable", True, False, notes=str(e))]
    matching = next((r for r in (payload.get("rules") or [])
                     if r.get("id") == ground.rule_id), None)
    if not matching:
        return [_eq(ep, "create", "row_present", ground.rule_id, None)]
    return [
        _eq(ep, "create", "row_present", ground.rule_id, matching.get("id")),
        _eq(ep, "create", "type", "threshold", matching.get("type")),
        _within(ep, "create", "threshold", ground.threshold_usd,
                float(matching.get("threshold") or 0), tolerance_pct=0.001),
        _eq(ep, "create", "enabled", 1, int(matching.get("enabled") or 0)),
    ]


def assert_spend_visibility(dashboard_url, ground) -> list[CheckResult]:
    """Check whether real openclaw spend reached the metric the evaluator
    sees. On installs without OTLP this is the headline drift."""
    ep = "/api/budget/status"
    try:
        status = http_get_json(f"{dashboard_url}{ep}")
    except Exception as e:
        return [_eq(ep, "spend_visibility", "reachable", True, False, notes=str(e))]
    actual_daily = float(status.get("daily_spent") or 0)
    return [CheckResult(
        endpoint=ep, window_label="spend_visibility",
        metric="real_spend_visible",
        ground=f">={ground.real_spend_usd * 0.5:.6f}", actual=actual_daily,
        passed=actual_daily >= ground.real_spend_usd * 0.5,
        notes="evaluator reads metrics_store['cost'] (OTLP-fed); 0 ⇒ no real-spend rule can fire",
    )]


def assert_fire_row(row, ground) -> list[CheckResult]:
    ep = "/api/alerts/history"
    if row is None:
        return [_eq(ep, "fire", "row_present", ground.rule_id, None)]
    out = [
        _eq(ep, "fire", "row_present", ground.rule_id, row.get("rule_id")),
        _eq(ep, "fire", "type", "threshold", row.get("type")),
        CheckResult(endpoint=ep, window_label="fire", metric="channel_present",
                    ground="banner|webhook", actual=row.get("channel"),
                    passed=row.get("channel") in ("banner", "webhook")),
    ]
    msg = str(row.get("message") or "")
    out.append(CheckResult(
        endpoint=ep, window_label="fire", metric="message_mentions_threshold",
        ground=f"contains '${ground.threshold_usd:.2f}'", actual=msg[:80],
        passed=f"${ground.threshold_usd:.2f}" in msg,
    ))
    m = re.search(r"\$([\d.]+)\s+exceeded", msg)
    actual_val = float(m.group(1)) if m else 0.0
    out.append(_within(ep, "fire", "triggered_value_within_5pct",
                       ground.expected_triggered_value, actual_val,
                       tolerance_pct=TOLERANCE_PCT))
    fired_at = float(row.get("fired_at") or 0)
    out.append(CheckResult(
        endpoint=ep, window_label="fire", metric="fired_at_fresh",
        ground="<60s ago", actual=fired_at,
        passed=abs(time.time() - fired_at) < 60.0,
    ))
    return out


def assert_dispatch(capture, ground) -> list[CheckResult]:
    ep = "webhook_capture"
    if not capture.received:
        return [_eq(ep, "dispatch", "received", True, False,
                    notes="no POST landed; dispatch path (urllib.urlopen) silently dropped")]
    body = (capture.received[-1].get("body") or {})
    return [
        _eq(ep, "dispatch", "received", True, True),
        _eq(ep, "dispatch", "type_field", "threshold", body.get("type")),
        CheckResult(endpoint=ep, window_label="dispatch", metric="message_present",
                    ground="non-empty", actual=str(body.get("message", ""))[:80],
                    passed=bool(body.get("message"))),
        CheckResult(endpoint=ep, window_label="dispatch", metric="severity_present",
                    ground="warning|info|critical", actual=body.get("severity"),
                    passed=body.get("severity") in ("warning", "info", "critical")),
    ]


def assert_cleanup(dashboard_url, ground) -> list[CheckResult]:
    ep = "/api/alerts/rules"
    try:
        payload = http_get_json(f"{dashboard_url}{ep}")
    except Exception as e:
        return [_eq(ep, "cleanup", "list_reachable", True, False, notes=str(e))]
    leaked = any(r.get("id") == ground.rule_id
                 for r in (payload.get("rules") or []))
    return [CheckResult(
        endpoint=ep, window_label="cleanup", metric="row_absent_after_delete",
        ground="absent", actual="present" if leaked else "absent",
        passed=not leaked,
    )]


# ─── Drift issue body ──────────────────────────────────────────────────────

def _format_alerts_issue_body(endpoint, cs, ground, dashboard_url) -> str:
    rows = "\n".join(
        f"| {c.window_label} | {c.metric} | "
        f"`{json.dumps(c.ground, default=str)[:60]}` | "
        f"`{json.dumps(c.actual, default=str)[:60]}` | "
        f"{'PASS' if c.passed else 'DRIFT'} | {(c.notes or '')[:80]} |"
        for c in cs
    )
    ground_json = json.dumps({
        "rule_id": ground.rule_id, "rule_name_tag": ground.rule_name_tag,
        "threshold_usd": ground.threshold_usd,
        "real_spend_usd": ground.real_spend_usd,
        "forced_inject_usd": ground.forced_inject_usd,
        "expected_triggered_value": ground.expected_triggered_value,
    }, indent=2)
    return (
        f"## Drift report — `{endpoint}`\n\n"
        f"Auto-filed by `scripts/accuracy_harness/alerts.py`.\n\n"
        f"### Drifted assertions\n"
        f"| stage | metric | ground | actual | result | notes |\n"
        f"|---|---|---|---|---|---|\n{rows}\n\n"
        f"### Ground-truth\n```json\n{ground_json}\n```\n\n"
        f"### Root-cause hints\n"
        f"* `/api/budget/status` `real_spend_visible` drift ⇒ OTLP→`metrics_store['cost']` is the broken pipeline; no real-spend rule can fire without OTLP traffic.\n"
        f"* `/api/alerts/history` `triggered_value_within_5pct` drift ⇒ `dashboard.py:_budget_monitor_loop` (~L8752) message formatter pulls from `status['daily_spent']`.\n"
        f"* `webhook_capture` `received` drift ⇒ `_dispatch_alert` filters via `_severity_passes_filter` / `_should_send_webhook_for_type` (~L8112/8127).\n\n"
        f"### To reproduce\n```bash\n"
        f"CLAWMETRY_URL={dashboard_url} CLAWMETRY_HARNESS_HOOKS=1 \\\n"
        f"  python3 scripts/accuracy_harness/alerts.py\n```\n"
    )


# ─── Main ───────────────────────────────────────────────────────────────────

def run_harness(args) -> int:
    print(f"[harness] alerts accuracy audit — {datetime.now(timezone.utc).isoformat()}")
    dashboard_url = discover_dashboard_url(args.dashboard_url,
                                            probe_path="/api/usage")
    print(f"[harness] dashboard: {dashboard_url}")

    run_id = uuid.uuid4().hex[:8]
    ground_tag = f"ACCURACY_AUDIT_{run_id}_alert"
    print(f"[harness] tag: {ground_tag}")

    usage, real_cost = drive_real_spend(ground_tag)
    if usage is None:
        print("[harness] FATAL: openclaw drove no usage; can't compute ground truth")
        return 2

    capture = _WebhookCapture()
    capture.start()
    print(f"[harness] webhook capture listening on {capture.url()}")

    prior_webhook = None
    rule_id = None
    all_checks: list[CheckResult] = []
    ground = AlertGround(rule_id="", rule_name_tag=ground_tag,
                         threshold_usd=TRIPPING_THRESHOLD_USD,
                         real_spend_usd=real_cost,
                         forced_inject_usd=FORCED_INJECT_USD,
                         expected_triggered_value=0.0,
                         capture_url=capture.url())
    try:
        prior_webhook = configure_webhook(dashboard_url, capture.url())
        rule_id = create_rule(dashboard_url, ground_tag)
        ground.rule_id = rule_id
        all_checks.extend(assert_rule_created(dashboard_url, ground))
        all_checks.extend(assert_spend_visibility(dashboard_url, ground))

        print("[harness] tripping via /api/_harness/inject-cost…")
        hook_resp = force_trip_via_hook(dashboard_url, rule_id)
        if hook_resp is None:
            print(f"[harness] hook unavailable — falling back to natural "
                  f"60s tick (waiting up to {NATURAL_TICK_WAIT_S}s)")
            wait_window = NATURAL_TICK_WAIT_S
        else:
            print(f"  hook ok: {hook_resp}")
            ground.expected_triggered_value = float(hook_resp.get("daily_spent") or 0)
            wait_window = HISTORY_WAIT_S

        print(f"[harness] polling /api/alerts/history for rule {rule_id} "
              f"(timeout={wait_window}s)…")
        fire = wait_for_fire(dashboard_url, rule_id, wait_window)
        if fire is None:
            print(f"  [fire] FAILED: no history row after {wait_window}s")
        else:
            print(f"  [fire] row landed: channel={fire.get('channel')} "
                  f"msg={(fire.get('message') or '')[:80]}")
        all_checks.extend(assert_fire_row(fire, ground))

        print(f"[harness] waiting up to {WEBHOOK_WAIT_S}s for webhook capture…")
        hook = wait_for_webhook(capture, WEBHOOK_WAIT_S)
        if hook is None:
            print("  [dispatch] FAILED: no POST received on capture listener")
        else:
            print(f"  [dispatch] POST received: type={hook['body'].get('type')} "
                  f"msg={(hook['body'].get('message') or '')[:60]}")
        all_checks.extend(assert_dispatch(capture, ground))
    finally:
        if rule_id:
            print(f"[harness] cleaning up rule {rule_id}…")
            if delete_rule(dashboard_url, rule_id):
                all_checks.extend(assert_cleanup(dashboard_url, ground))
        if prior_webhook is not None:
            restore_webhook(dashboard_url, prior_webhook)
        capture.stop()

    print()
    print("─" * 90)
    print(f"{'ENDPOINT':<28} {'STAGE':<18} {'METRIC':<34} {'RESULT':<6}")
    print("─" * 90)
    drifts: list[CheckResult] = []
    for c in all_checks:
        result = "PASS" if c.passed else "DRIFT"
        if not c.passed:
            drifts.append(c)
        print(f"{c.endpoint:<28} {c.window_label:<18} {c.metric:<34} {result:<6}")
    print("─" * 90)
    print(f"summary: {sum(1 for c in all_checks if c.passed)} pass / "
          f"{len(drifts)} drift / {len(all_checks)} total checks")
    print(f"rule exercised: id={rule_id} tag={ground_tag} "
          f"threshold=${TRIPPING_THRESHOLD_USD}")

    if not drifts:
        print()
        print("[harness] ALL CHECKS PASSED — alerts pipeline is accurate on this build.")
        return 0

    print()
    print("[harness] DRIFT DETECTED:")
    for c in drifts:
        print(f"  - {c.endpoint} stage={c.window_label} metric={c.metric}: "
              f"ground={c.ground!r} actual={c.actual!r}"
              + (f"  ({c.notes})" if c.notes else ""))

    if args.file_issues:
        def _body_builder(endpoint, cs):
            return _format_alerts_issue_body(endpoint, cs, ground, dashboard_url)
        file_drift_issue_per_endpoint(harness_label="alerts", drifts=drifts,
                                       body_builder=_body_builder)
    else:
        print("[harness] (re-run with --file-issues to open GitHub issues)")
    return 1


# ─── CLI ────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--dashboard-url", type=str, default=None,
                   help="override dashboard URL (default: auto-detect, $CLAWMETRY_URL)")
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
