#!/usr/bin/env python3
"""Verify the runtime-filter rule (FLYWHEEL.md §1c) against the public v1 API.

When the runtime switcher is set to a runtime, every view must show ONLY that
runtime's data. The public v1 API (https://app.clawmetry.com/api/v1/*) is the
filtering contract: it scopes server-side by ?runtime=<id>. This script sweeps
EVERY runtime a node reports and asserts the v1 responses actually scope, so a
filter that hard-codes one runtime (or no-ops on an aggregate) is caught.

Usage:
    python3 scripts/verify_runtime_filtering.py [--node NODE_ID] [--base URL]

Auth/node resolve from (in order): CLI flags, env (CLAWMETRY_API_KEY /
CLAWMETRY_NODE_ID / CLAWMETRY_API_BASE), then ~/.clawmetry/config.json.

Exit 0 = all runtimes scope correctly; 1 = at least one leak/mismatch; 2 = setup
error (no key/node). Never throws past main()."""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request


def _load_config() -> dict:
    try:
        p = os.path.expanduser("~/.clawmetry/config.json")
        with open(p, "r", encoding="utf-8") as fh:
            return json.load(fh) or {}
    except Exception:
        return {}


def _get(base: str, path: str, api_key: str) -> dict | list | None:
    url = f"{base.rstrip('/')}/api/v1/{path.lstrip('/')}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  ! GET {path} failed: {e}")
        return None


def _session_count(resp) -> int | None:
    """v1 /sessions returns {data:[...]}; count its rows."""
    if not isinstance(resp, dict):
        return None
    data = resp.get("data")
    return len(data) if isinstance(data, list) else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--node", default=os.environ.get("CLAWMETRY_NODE_ID", ""))
    ap.add_argument("--base", default=os.environ.get("CLAWMETRY_API_BASE", "https://app.clawmetry.com"))
    ap.add_argument("--key", default=os.environ.get("CLAWMETRY_API_KEY", ""))
    args = ap.parse_args()

    cfg = _load_config()
    api_key = args.key or cfg.get("api_key", "")
    node = args.node or cfg.get("node_id", "")
    if not api_key or not node:
        print("ERROR: need an api_key and node_id (flags, env, or ~/.clawmetry/config.json)")
        return 2

    print(f"[verify-runtime-filtering] node={node} base={args.base}")

    # 1. Ground truth: the per-runtime session counts the node reports.
    rt_resp = _get(args.base, f"nodes/{node}/runtimes", api_key)
    runtimes = (rt_resp or {}).get("data") or (rt_resp or {}).get("runtimes") or []
    expected = {}
    for r in runtimes:
        rid = r.get("id") or r.get("runtime")
        cnt = r.get("sessions") if r.get("sessions") is not None else r.get("session_count")
        if rid:
            expected[rid] = cnt
    if not expected:
        print("ERROR: node reports no runtimes (nothing to verify)")
        return 2
    print(f"  runtimes: {expected}")

    failures: list[str] = []
    seen_counts: dict[str, int] = {}

    # 2. Each runtime's /sessions must scope to ~that runtime's count.
    for rid, exp_cnt in expected.items():
        resp = _get(args.base, f"sessions?node_id={node}&runtime={rid}", api_key)
        got = _session_count(resp)
        seen_counts[rid] = got if got is not None else -1
        ok = got is not None and (exp_cnt is None or got <= exp_cnt + 0)
        # The v1 sessions list is capped, so got should be <= reported count and
        # never the WHOLE-node total. A leak shows up as every runtime returning
        # the same (node-wide) number.
        status = "ok" if ok else "FAIL"
        print(f"  /sessions runtime={rid:<12} -> {got} (reported {exp_cnt})  [{status}]")
        if not ok:
            failures.append(f"{rid}: sessions returned {got}, expected <= {exp_cnt}")

    # 3. Cross-runtime invariant: not every runtime can return the SAME count
    #    (that's the classic "filter no-ops, everyone sees the node total" leak).
    distinct = set(v for v in seen_counts.values() if v >= 0)
    if len(expected) >= 2 and len(distinct) == 1:
        failures.append(
            f"all {len(expected)} runtimes returned the same session count "
            f"({distinct}) — the runtime filter is not scoping (aggregate leak)"
        )

    # 4. An absent runtime must return zero, not the node total.
    bogus = _get(args.base, f"sessions?node_id={node}&runtime=__nope__", api_key)
    bogus_n = _session_count(bogus)
    if bogus_n:
        failures.append(f"unknown runtime returned {bogus_n} sessions (should be 0)")
    else:
        print("  /sessions runtime=__nope__ -> 0  [ok]")

    print()
    if failures:
        print(f"FAILED ({len(failures)}):")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"PASS: all {len(expected)} runtimes scope correctly via the v1 API")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:  # never throw past main
        print(f"FATAL: {e}")
        sys.exit(2)
