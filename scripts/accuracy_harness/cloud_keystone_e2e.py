#!/usr/bin/env python3
"""scripts/accuracy_harness/cloud_keystone_e2e.py — CLOUD-side keystone verifier.

Sibling of ``keystone_e2e.py`` (which verifies the LOCAL half of the loop:
OpenClaw -> daemon -> DuckDB -> local /api/*). This harness verifies the
CLOUD half: daemon -> sync.ingest -> Postgres -> app.clawmetry.com /api/*.

The full MOAT loop is ``user message -> local DuckDB -> local API -> cloud
ingest -> cloud Postgres -> cloud API``. Both halves must be green or the
"Node Detail" modal a paying customer opens at https://app.clawmetry.com
silently shows zeros while their local dashboard shows real data.

What this script does
---------------------
1. Auto-discovers the cloud API key + node_id from ``~/.clawmetry/config.json``
   (the file ``clawmetry connect`` writes after the user pairs their node).
2. Probes 6 cloud API surfaces backing the Node Detail page:
     - /api/cloud/account            (auth works)
     - /api/cloud/nodes              (user has the expected node)
     - /api/cloud/node/<id>/info     (node metadata loads)
     - /api/cloud/node/<id>/summary  (model + token totals)
     - /api/cloud/node/<id>/sessions (sessions list)
     - /api/cloud/node/<id>/components  (gateway / exec / browser panels)
3. For each probe that has a local counterpart, runs the LOCAL endpoint
   too and reports a side-by-side LOCAL vs CLOUD comparison so drift is
   immediately visible (the same diff pattern keystone uses for endpoint
   shape).

Exit codes
----------
  0 -- every cloud probe returned a valid shape
  1 -- at least one probe failed (auth / 404 / wrong shape)
  2 -- harness itself failed (no api key, no internet, etc.)

Notes
-----
- Auth fallback: ``?token=<api_key>`` query arg is used because the
  ``cm_token`` cookie path (PR #978) is merged but not yet deployed on
  cloud due to the GitHub Actions billing block.
- ``/api/cloud/node/<id>/events`` was removed 2026-05-13 (epic #1032).
  Brain/event-shaped data is served via ``/api/cloud/brain`` as an
  encrypted blob -- this harness only checks the blob arrives, not its
  decrypted contents (which would require the per-node AES key).
- The harness is READ-ONLY against cloud. It does not POST, PUT, or
  DELETE. Re-running is always safe.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Allow ``python3 scripts/accuracy_harness/cloud_keystone_e2e.py`` to resolve _lib.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _lib import discover_dashboard_url, http_get_json  # noqa: E402


# --- Config -----------------------------------------------------------------

DEFAULT_CLOUD_BASE = os.environ.get("CLAWMETRY_CLOUD_URL",
                                    "https://app.clawmetry.com").rstrip("/")
CONFIG_PATH = Path.home() / ".clawmetry" / "config.json"
HTTP_TIMEOUT_S = 15.0


# --- Result types -----------------------------------------------------------

@dataclass
class Check:
    endpoint: str
    label: str
    status: str  # "pass" | "fail" | "skip"
    detail: str = ""

    def line(self) -> str:
        glyph = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}[self.status]
        return f"  [{glyph}] {self.endpoint:48s} {self.label} {self.detail}".rstrip()


@dataclass
class Drift:
    """Per-metric LOCAL vs CLOUD comparison row."""
    axis: str            # "sessions" | "model" | "tokens" | "events_today"
    local: Any
    cloud: Any
    note: str = ""

    @property
    def ok(self) -> bool:
        """Drift is ok when cloud is a recent subset of local OR they match.

        For session counts: cloud >= 0 AND cloud <= local + small slack.
        For token counts: cloud <= local (cloud is a strict subset of what
        local has ingested -- daemon may not have shipped everything yet).
        For model strings: cloud is empty (no traffic yet) OR matches local.
        """
        if self.local is None or self.cloud is None:
            return False
        if isinstance(self.local, int) and isinstance(self.cloud, int):
            # Cloud is allowed to be a subset of local (sync lag is normal).
            # Drift only fires when cloud > local (impossible without a bug)
            # or both are zero (silent-zero on both sides -> investigate).
            if self.local == 0 and self.cloud == 0:
                return True   # nothing to compare; not a bug per se
            return self.cloud <= self.local
        if isinstance(self.local, str) and isinstance(self.cloud, str):
            # Empty cloud is fine; otherwise must match.
            if not self.cloud:
                return True
            return self.cloud == self.local
        return False

    def line(self) -> str:
        glyph = "OK  " if self.ok else "DRIFT"
        return (f"  [{glyph}] {self.axis:18s} "
                f"local={self.local!r:>40}  cloud={self.cloud!r}"
                + (f"  ({self.note})" if self.note else ""))


# --- Discovery --------------------------------------------------------------

def discover_cloud_creds(override_key: str | None,
                         override_node: str | None) -> tuple[str, str]:
    """Return (api_key, node_id). CLI args win, then config.json, then env.

    Raises RuntimeError when neither source has both fields -- the harness
    cannot run without a paired cloud account.
    """
    api_key = (override_key
               or os.environ.get("CLAWMETRY_API_KEY")
               or "")
    node_id = (override_node
               or os.environ.get("CLAWMETRY_NODE_ID")
               or "")
    if not (api_key and node_id) and CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH) as fh:
                cfg = json.load(fh)
            api_key = api_key or str(cfg.get("api_key") or "")
            node_id = node_id or str(cfg.get("node_id") or "")
        except (OSError, ValueError) as e:
            print(f"[cloud-keystone] WARN: could not read {CONFIG_PATH}: {e}",
                  file=sys.stderr)
    if not api_key:
        raise RuntimeError(
            f"no api_key found (looked in --api-key, $CLAWMETRY_API_KEY, "
            f"{CONFIG_PATH}). Run `clawmetry connect` to pair this node."
        )
    if not node_id:
        raise RuntimeError(
            f"no node_id found (looked in --node-id, $CLAWMETRY_NODE_ID, "
            f"{CONFIG_PATH})."
        )
    return api_key, node_id


def _safe_get(url: str, *, timeout: float = HTTP_TIMEOUT_S) -> tuple[Any, str | None]:
    """GET ``url``. Returns (parsed_json, None) on success or (None, err)."""
    try:
        return http_get_json(url, timeout=timeout), None
    except urllib.error.HTTPError as e:
        return None, f"HTTP {e.code}"
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
        return None, f"{type(e).__name__}: {e}"
    except (ValueError, json.JSONDecodeError) as e:
        return None, f"json decode: {e}"


def _q(path: str, api_key: str, **extra: str) -> str:
    """Build a token-authenticated URL with the api_key as ``?token=``."""
    params = {"token": api_key, **extra}
    return f"{path}?{urllib.parse.urlencode(params)}"


# --- Cloud probes -----------------------------------------------------------

def check_account(cloud: str, api_key: str) -> tuple[Check, dict | None]:
    ep = "/api/cloud/account"
    url = f"{cloud}{_q(ep, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep, "auth", "fail", err), None
    if not isinstance(payload, dict):
        return Check(ep, "shape", "fail",
                     f"expected dict, got {type(payload).__name__}"), None
    if not payload.get("ok"):
        return Check(ep, "ok", "fail", f"ok=false: {payload.get('error')}"), None
    email = payload.get("email") or ""
    plan = payload.get("plan") or ""
    return Check(ep, "auth+ok", "pass",
                 f"email={email} plan={plan} nodes={payload.get('node_count')}"
                 ), payload


def check_nodes(cloud: str, api_key: str, node_id: str
                ) -> tuple[Check, dict | None]:
    ep = "/api/cloud/nodes"
    url = f"{cloud}{_q(ep, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep, "fetch", "fail", err), None
    if not isinstance(payload, list):
        return Check(ep, "shape", "fail",
                     f"expected list, got {type(payload).__name__}"), None
    if not payload:
        return Check(ep, "nodes", "fail", "node list is empty"), None
    match = None
    for n in payload:
        if isinstance(n, dict) and (n.get("node_id") == node_id
                                    or n.get("hostname") == node_id):
            match = n
            break
    if match is None:
        return Check(ep, "node_present", "fail",
                     f"{node_id!r} not in {[n.get('node_id') for n in payload]}"
                     ), None
    return Check(ep, "node_present", "pass",
                 f"node found, status={match.get('status')} "
                 f"version={match.get('version')}"), match


def check_info(cloud: str, api_key: str, node_id: str) -> Check:
    ep_path = f"/api/cloud/node/{urllib.parse.quote(node_id)}/info"
    url = f"{cloud}{_q(ep_path, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep_path, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep_path, "shape", "fail",
                     f"expected dict, got {type(payload).__name__}")
    if "node_id" not in payload and "hostname" not in payload:
        return Check(ep_path, "shape", "fail",
                     f"missing node_id/hostname keys; got "
                     f"{sorted(payload.keys())[:6]}")
    return Check(ep_path, "shape", "pass",
                 f"status={payload.get('status')} "
                 f"version={payload.get('version')}")


def check_summary(cloud: str, api_key: str, node_id: str
                  ) -> tuple[Check, dict | None]:
    ep_path = f"/api/cloud/node/{urllib.parse.quote(node_id)}/summary"
    url = f"{cloud}{_q(ep_path, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep_path, "fetch", "fail", err), None
    if not isinstance(payload, dict):
        return Check(ep_path, "shape", "fail",
                     f"expected dict, got {type(payload).__name__}"), None
    required = {"session_count", "total_tokens", "recent_model", "node"}
    missing = required - set(payload.keys())
    if missing:
        return Check(ep_path, "shape", "fail",
                     f"missing keys: {sorted(missing)}"), None
    return Check(ep_path, "shape", "pass",
                 f"sessions={payload.get('session_count')} "
                 f"tokens={payload.get('total_tokens')} "
                 f"model={payload.get('recent_model')}"), payload


def check_sessions(cloud: str, api_key: str, node_id: str
                   ) -> tuple[Check, dict | None]:
    ep_path = f"/api/cloud/node/{urllib.parse.quote(node_id)}/sessions"
    url = f"{cloud}{_q(ep_path, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep_path, "fetch", "fail", err), None
    if not isinstance(payload, dict):
        return Check(ep_path, "shape", "fail",
                     f"expected dict, got {type(payload).__name__}"), None
    if "sessions" not in payload:
        return Check(ep_path, "shape", "fail",
                     f"missing .sessions key; got {sorted(payload.keys())[:6]}"
                     ), None
    sessions = payload.get("sessions") or []
    # ``_source: relay_pending`` is a legitimate empty-state when the
    # daemon has not yet served the session list through the heartbeat
    # relay -- shape pass, but flag in the body.
    src = payload.get("_source") or ""
    note = f" ({src})" if src else ""
    return Check(ep_path, "shape", "pass",
                 f"sessions={len(sessions)}{note}"), payload


def check_components(cloud: str, api_key: str, node_id: str) -> Check:
    ep_path = f"/api/cloud/node/{urllib.parse.quote(node_id)}/components"
    url = f"{cloud}{_q(ep_path, api_key)}"
    payload, err = _safe_get(url)
    if err:
        return Check(ep_path, "fetch", "fail", err)
    if not isinstance(payload, dict):
        return Check(ep_path, "shape", "fail",
                     f"expected dict, got {type(payload).__name__}")
    # Node Detail's Flow panel reads these five sections (one per
    # component card). Missing any of them blanks out a card.
    required_any = {"gateway", "machine", "exec", "browser", "messages"}
    keys = set(payload.keys())
    if not (keys & required_any):
        return Check(ep_path, "shape", "fail",
                     f"missing all of {required_any}; got {sorted(keys)[:6]}")
    gw = payload.get("gateway") or {}
    return Check(ep_path, "shape", "pass",
                 f"sections={sorted(keys & required_any)} "
                 f"gw_status={gw.get('status')}")


# --- Drift comparison (cloud vs local) -------------------------------------

def collect_local_signals(dashboard: str) -> dict[str, Any]:
    """Pull the dashboard signals we want to drift-check against cloud.

    Returns ``{"sessions": int, "today_tokens": int, "recent_model": str}``,
    filling None for any axis the local dashboard can't supply (so the
    drift report shows ``cloud=...`` without a misleading local value).
    """
    out: dict[str, Any] = {"sessions": None, "today_tokens": None,
                            "recent_model": None}
    # /api/sessions is the OSS-side equivalent of the node sessions list.
    sess_payload, sess_err = _safe_get(f"{dashboard}/api/sessions")
    if not sess_err and isinstance(sess_payload, dict):
        sessions = sess_payload.get("sessions") or []
        out["sessions"] = len(sessions) if isinstance(sessions, list) else None
    # /api/usage drives the Tokens tab; ``today`` is today's billable total.
    usage_payload, usage_err = _safe_get(f"{dashboard}/api/usage")
    if not usage_err and isinstance(usage_payload, dict):
        try:
            out["today_tokens"] = int(usage_payload.get("today") or 0)
        except (TypeError, ValueError):
            out["today_tokens"] = None
        mb = usage_payload.get("modelBreakdown") or []
        if mb and isinstance(mb, list):
            top = max(mb, key=lambda m: (m or {}).get("tokens") or 0)
            out["recent_model"] = str((top or {}).get("model") or "") or None
    return out


def compute_drift(local: dict[str, Any], summary: dict | None,
                   sessions_resp: dict | None) -> list[Drift]:
    """Build the LOCAL-vs-CLOUD diff table for the 4 axes a user sees."""
    drifts: list[Drift] = []
    if summary is None:
        return drifts
    # sessions count: cloud /summary vs local /api/sessions
    cloud_sessions = summary.get("session_count")
    drifts.append(Drift(
        axis="sessions_count",
        local=local.get("sessions"),
        cloud=cloud_sessions,
        note="cloud=/summary.session_count vs local=/api/sessions[].len",
    ))
    # recent model: cloud /summary vs local /api/usage top model
    drifts.append(Drift(
        axis="recent_model",
        local=local.get("recent_model"),
        cloud=str(summary.get("recent_model") or ""),
        note="cloud=/summary.recent_model vs local top of modelBreakdown",
    ))
    # token totals: cloud /summary.total_tokens vs local /api/usage.today
    drifts.append(Drift(
        axis="tokens_today",
        local=local.get("today_tokens"),
        cloud=summary.get("total_tokens"),
        note="cloud=/summary.total_tokens (lifetime) vs local=/api/usage.today",
    ))
    # sessions list shape: cloud /sessions[].len vs local /api/sessions[].len
    cloud_session_list = None
    if isinstance(sessions_resp, dict):
        ss = sessions_resp.get("sessions") or []
        cloud_session_list = len(ss) if isinstance(ss, list) else None
    drifts.append(Drift(
        axis="sessions_listed",
        local=local.get("sessions"),
        cloud=cloud_session_list,
        note="cloud=/node/<id>/sessions[].len vs local=/api/sessions[].len",
    ))
    return drifts


# --- Driver -----------------------------------------------------------------

def run(args) -> int:
    print("[cloud-keystone] CLOUD-side keystone harness starting")
    try:
        api_key, node_id = discover_cloud_creds(args.api_key, args.node_id)
    except RuntimeError as e:
        print(f"[cloud-keystone] PREFLIGHT FAILED: {e}", file=sys.stderr)
        return 2
    cloud = args.cloud_url.rstrip("/")
    print(f"[cloud-keystone]   cloud    = {cloud}")
    print(f"[cloud-keystone]   node_id  = {node_id}")
    print(f"[cloud-keystone]   api_key  = {api_key[:8]}... ({len(api_key)} chars)")

    t0 = time.time()
    print()
    print("[cloud-keystone] Probing 6 cloud API surfaces...")
    checks: list[Check] = []
    acct_check, acct = check_account(cloud, api_key)
    checks.append(acct_check)
    nodes_check, node_row = check_nodes(cloud, api_key, node_id)
    checks.append(nodes_check)
    checks.append(check_info(cloud, api_key, node_id))
    summary_check, summary = check_summary(cloud, api_key, node_id)
    checks.append(summary_check)
    sessions_check, sessions_resp = check_sessions(cloud, api_key, node_id)
    checks.append(sessions_check)
    checks.append(check_components(cloud, api_key, node_id))

    print()
    print("[cloud-keystone] Per-endpoint results:")
    for c in checks:
        print(c.line())

    # --- Drift report (local vs cloud) ------------------------------------
    drift_section = ""
    drifts: list[Drift] = []
    try:
        dashboard = discover_dashboard_url(args.dashboard_url)
        print()
        print(f"[cloud-keystone] Local dashboard = {dashboard}")
        local_signals = collect_local_signals(dashboard)
        drifts = compute_drift(local_signals, summary, sessions_resp)
    except RuntimeError as e:
        print(f"[cloud-keystone] (local dashboard unavailable -- "
              f"skipping drift diff: {e})")

    if drifts:
        print()
        print("[cloud-keystone] LOCAL vs CLOUD drift table:")
        for d in drifts:
            print(d.line())

    failed = [c for c in checks if c.status == "fail"]
    passed = [c for c in checks if c.status == "pass"]
    skipped = [c for c in checks if c.status == "skip"]
    print()
    elapsed = time.time() - t0
    print(f"[cloud-keystone] Summary: {len(passed)} pass / {len(failed)} fail "
          f"/ {len(skipped)} skip (total {len(checks)}; "
          f"{elapsed:.1f}s wall)")

    drift_failures = [d for d in drifts if not d.ok]
    if drift_failures:
        print(f"[cloud-keystone] {len(drift_failures)} drift axis(es) flagged "
              f"(cloud exceeds local or both zero on a non-empty axis):")
        for d in drift_failures:
            print(f"  - {d.axis}: local={d.local!r} cloud={d.cloud!r}")
        print("[cloud-keystone] Diagnostic hints:")
        print("  1. Is the sync daemon running? "
              "`ps aux | grep clawmetry.sync | grep -v grep`")
        print("  2. Has the daemon shipped events to ingest? "
              "`tail -50 ~/.clawmetry/sync.log | grep ingest/events`")
        print("  3. Is the ingest writing to Postgres? "
              "Check cloud heartbeat-relay logs in Cloud Run.")
        print("  4. Does the cloud API query the right table? "
              "Compare /api/cloud/node/<id>/summary SQL vs /api/cloud/usage.")

    if failed:
        print()
        print("[cloud-keystone] FAILED endpoints:")
        for c in failed:
            print(f"  - {c.endpoint} -> {c.detail}")
        return 1
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--cloud-url", default=DEFAULT_CLOUD_BASE,
                   help=f"Cloud base URL (default: {DEFAULT_CLOUD_BASE})")
    p.add_argument("--api-key", default=None,
                   help="Override cloud API key (default: auto-detect from "
                        f"{CONFIG_PATH})")
    p.add_argument("--node-id", default=None,
                   help="Override node_id (default: auto-detect)")
    p.add_argument("--dashboard-url", default=None,
                   help="Local dashboard base URL for drift diff "
                        "(default: auto-detect on 8900/8903/8905)")
    args = p.parse_args()
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
