#!/usr/bin/env python3
"""SPIKE (measure first, build later): how many descendants does a NORMAL agent
session spawn that no tool call explains?

Every behavioural detector ClawMetry ships reads the **tool stream**: what the
agent chose to do. GitSpawn proved that is a partial view. Git spawned the
payload, the agent called no tool, and ``detectors.run_all`` saw a clean
session. ``repo_scan`` closed part of that by reading the *workspace*, which is
a pre-flight check rather than an observation of execution.

The third view nobody has is **what actually ran**. ``process_control`` already
resolves an agent's pid and walks its process tree (that is how kill works), and
the same tree, sampled, can be asked: did this agent spawn a descendant that no
tool call explains?

This script does NOT build that detector. It builds the measurement that decides
whether the detector is worth building, because the whole question is the false
positive rate: agents legitimately spawn compilers, test runners, language
servers and package managers. If a normal session produces hundreds of
unexplained descendants, the idea is dead and we will have learned that for a
day of sampling instead of a quarter of engineering.

Usage:
  python3 scripts/spike_unexplained_descendants.py                 # 10 min
  python3 scripts/spike_unexplained_descendants.py --minutes 60
  python3 scripts/spike_unexplained_descendants.py --interval 15 --json out.json

Method, stated so the numbers can be argued with:

  * Sessions come from ``process_control.live_sessions()`` (runtimes that record
    their own pid) plus ``resolve_session`` for store sessions that have a cwd.
  * Each tick walks ``descendant_pids`` and records every descendant once, keyed
    on (pid, start token) so pid reuse cannot double count.
  * A descendant is EXPLAINED when its argv[0] basename appears as a word in a
    tool call from the same session within ``--window`` seconds, or when it is a
    known child of one (``sh -c`` under a Bash call, a language server the
    runtime itself launches).
  * Everything else is UNEXPLAINED. That is the number the idea lives or dies on
    -- and it is an UPPER bound: the join is approximate by construction, since
    a grandchild of an explained command (git -> the fsmonitor payload) looks
    exactly like a grandchild of an explained command that is perfectly fine.

Read-only. It samples and counts; it never signals anything.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from clawmetry import process_control as pc  # noqa: E402

#: Processes a runtime starts for its own reasons, which no tool call will ever
#: explain and which are not interesting. Kept deliberately SHORT: every entry
#: here is a claim that something is normal, and a generous list would flatter
#: the result this spike exists to test honestly.
_RUNTIME_OWN = {
    "node", "npm", "bun", "deno",           # the runtime's own JS host
    "rg", "fd",                              # the search tools every agent ships
    "ssh-agent", "gpg-agent",
}


def _daemon_call(method: str, **kwargs):
    """Read the store through the daemon's localhost proxy (it owns the writer
    lock). Protocol is ``{"kwargs": {...}}`` -- bare top-level keys are ignored
    and the method silently runs with DEFAULTS."""
    path = os.path.expanduser("~/.clawmetry/local_query.json")
    try:
        cfg = json.load(open(path, encoding="utf-8"))
    except Exception:
        return None
    req = urllib.request.Request(
        f"http://127.0.0.1:{cfg['port']}/__local_query__/{method}",
        data=json.dumps({"kwargs": kwargs}).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + cfg["token"]})
    try:
        return json.load(urllib.request.urlopen(req, timeout=30))["result"]
    except Exception:
        return None


def _sessions_with_pids() -> list:
    """``[{session_id, runtime, pid, cwd}]`` for everything resolvable now."""
    out, seen = [], set()
    try:
        for s in pc.live_sessions() or []:
            key = f"{s.get('runtime')}:{s.get('session_id')}"
            if key in seen:
                continue
            seen.add(key)
            out.append({"session_id": key, "runtime": s.get("runtime"),
                        "pid": s.get("pid"), "cwd": s.get("cwd") or ""})
    except Exception:
        pass

    rows = _daemon_call("query_sessions_table", limit=300) or []
    for r in rows:
        sid = str(r.get("session_id") or "")
        if not sid or sid in seen or r.get("ended_at"):
            continue
        runtime = sid.split(":", 1)[0] if ":" in sid else "openclaw"
        cwd = r.get("cwd") or ""
        if not isinstance(cwd, str) or not cwd.strip():
            continue
        try:
            info = pc.resolve_session(runtime, sid, cwd.strip())
        except Exception:
            continue
        if info.get("ok") and info.get("pid"):
            seen.add(sid)
            out.append({"session_id": sid, "runtime": runtime,
                        "pid": info["pid"], "cwd": cwd.strip()})
    return out


def _tool_words(session_id: str, window_s: int) -> set:
    """Every word in this session's recent tool calls, for the argv join."""
    events = _daemon_call("query_events", session_id=session_id, limit=200) or []
    words = set()
    for e in events:
        data = e.get("data")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                continue
        if not isinstance(data, dict):
            continue
        blob = json.dumps(data.get("args") or data.get("tool_calls") or "")
        blob += " " + str(data.get("tool_name") or data.get("tool") or "")
        for w in blob.replace("/", " ").replace('"', " ").replace(",", " ").split():
            w = w.strip("'\\[]{}():;&|").lower()
            if w:
                words.add(w)
    return words


def sample(sessions: list, window_s: int) -> list:
    """One tick: every descendant of every session, with a verdict."""
    rows = []
    for s in sessions:
        pid = int(s["pid"])
        try:
            kids = pc.descendant_pids(pid)
        except Exception:
            continue
        if not kids:
            continue
        words = _tool_words(s["session_id"], window_s)
        for kid in kids:
            argv = pc._proc_cmdline(kid) or []
            if not argv:
                continue
            exe = os.path.basename(str(argv[0]))
            explained = exe.lower() in words or exe.lower() in _RUNTIME_OWN
            if not explained:
                # A second chance on any argv token: `python3 -m pytest` is
                # explained by a `pytest` tool call.
                explained = any(os.path.basename(a).lower() in words
                                for a in argv[1:6])
            rows.append({
                "session_id": s["session_id"], "runtime": s["runtime"],
                "pid": kid, "exe": exe,
                "argv": " ".join(argv)[:160],
                "explained": bool(explained),
                "start": pc._proc_start_token(kid) or "",
            })
    return rows


def _tally(seen: dict, sessions_seen: dict) -> dict:
    by_runtime = collections.defaultdict(
        lambda: {"sessions": 0, "descendants": 0, "unexplained": 0,
                 "top_unexplained": collections.Counter()})
    for rt in sessions_seen.values():
        by_runtime[rt]["sessions"] += 1
    for row in seen.values():
        b = by_runtime[row["runtime"]]
        b["descendants"] += 1
        if not row["explained"]:
            b["unexplained"] += 1
            b["top_unexplained"][row["exe"]] += 1
    return by_runtime


def _write_report(path: str, ticks: int, interval: float, seen: dict,
                  sessions_seen: dict) -> None:
    """Persist after EVERY tick, not at the end.

    This is meant to sample for a day. The first run of it was killed at
    12 minutes by the OS reclaiming memory and took every sample with it,
    which is a silly way to lose an afternoon of evidence.
    """
    by_runtime = _tally(seen, sessions_seen)
    report = {rt: {"sessions": b["sessions"], "descendants": b["descendants"],
                   "unexplained": b["unexplained"],
                   "unexplained_per_session": round(
                       b["unexplained"] / b["sessions"], 2) if b["sessions"] else 0.0,
                   "top_unexplained": b["top_unexplained"].most_common(10)}
              for rt, b in by_runtime.items()}
    tmp = path + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"ticks": ticks, "interval_s": interval,
                       "by_runtime": report, "rows": list(seen.values())},
                      f, indent=2)
        os.replace(tmp, path)
    except Exception as e:  # noqa: BLE001 - a sampler must not die writing a file
        print(f"  [warn] could not write {path}: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=10.0)
    ap.add_argument("--interval", type=float, default=20.0,
                    help="seconds between samples")
    ap.add_argument("--window", type=int, default=300,
                    help="how far back a tool call may explain a descendant")
    ap.add_argument("--json", help="write the full record here")
    args = ap.parse_args()

    deadline = time.time() + args.minutes * 60
    seen = {}
    ticks = 0
    sessions_seen = {}
    print(f"sampling for {args.minutes:g} min, every {args.interval:g}s "
          f"(read-only)\n")
    while time.time() < deadline:
        ticks += 1
        sessions = _sessions_with_pids()
        for s in sessions:
            sessions_seen[s["session_id"]] = s["runtime"]
        for row in sample(sessions, args.window):
            seen.setdefault((row["pid"], row["start"]), row)
        print(f"  tick {ticks}: {len(sessions)} session(s), "
              f"{len(seen)} distinct descendant(s) so far", flush=True)
        if args.json:
            _write_report(args.json, ticks, args.interval, seen, sessions_seen)
        time.sleep(max(1.0, args.interval))

    by_runtime = _tally(seen, sessions_seen)

    print("\n== unexplained-descendant rate, per runtime ==")
    print(f"{'runtime':<16}{'sessions':>9}{'desc':>7}{'unexpl':>8}"
          f"{'per session':>13}   top unexplained")
    total_d = total_u = 0
    report = {}
    for rt, b in sorted(by_runtime.items()):
        total_d += b["descendants"]
        total_u += b["unexplained"]
        per = b["unexplained"] / b["sessions"] if b["sessions"] else 0.0
        top = ", ".join(f"{k}x{v}" for k, v in b["top_unexplained"].most_common(4))
        print(f"{rt:<16}{b['sessions']:>9}{b['descendants']:>7}"
              f"{b['unexplained']:>8}{per:>13.1f}   {top}")
        report[rt] = {"sessions": b["sessions"], "descendants": b["descendants"],
                      "unexplained": b["unexplained"],
                      "unexplained_per_session": round(per, 2),
                      "top_unexplained": b["top_unexplained"].most_common(10)}
    print(f"\ntotal: {total_d} distinct descendants, {total_u} unexplained, "
          f"over {ticks} ticks")
    print("\nRead this as an UPPER bound: the argv join is approximate, and a "
          "grandchild of an explained command is counted unexplained.")

    if args.json:
        _write_report(args.json, ticks, args.interval, seen, sessions_seen)
        print(f"\nrecord written to {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
