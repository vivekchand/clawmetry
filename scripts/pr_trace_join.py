#!/usr/bin/env python3
"""PR -> agent-trace join prototype (see PRD-pr-trace.md §2).

Read-only. Measures how much of a repo's history can actually be joined to an
agent session, and by which tier:

  TIER A (deterministic)  commit trailer carrying a *local* session id that the
                          ClawMetry store knows. Requires the ClawMetry commit
                          hook (PRD §4a) — nothing in git history has this yet.

  TIER B (heuristic)      commit has a `Co-Authored-By: Claude*` trailer, and a
                          session for this repo's path was active in the store
                          within +/- WINDOW of the commit timestamp.

  UNJOINABLE              everything else.

NOTE ON A FALSE START: the vendor `Claude-Session:` trailer carries a *cloud*
id (`session_01…`) that appears NOWHERE as structured metadata in the local
transcript — a scan of 200 transcripts found it only inside tool inputs and
stdout (i.e. incidental text). There is no on-disk mapping from cloud id to
local session. That is why Tier A requires our own trailer.

Usage:
    python3 scripts/pr_trace_join.py [N_COMMITS]

Env: CLAWMETRY_REPO (default: cwd), CLAWMETRY_URL (default: localhost:8900).
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone

REPO = os.environ.get("CLAWMETRY_REPO", os.getcwd())
DASH = os.environ.get("CLAWMETRY_URL", "http://127.0.0.1:8900").rstrip("/")
WINDOW_S = int(os.environ.get("PR_TRACE_WINDOW_S", "7200"))  # +/- 2h
N = int(sys.argv[1]) if len(sys.argv) > 1 else 800

# Trailer we will write ourselves (PRD §4a). Value is a store session id.
OURS = re.compile(r"^Clawmetry-Session:\s*(\S+)\s*$", re.M)
COAUTH = re.compile(r"^Co-Authored-By:\s*Claude", re.M | re.I)
PRNUM = re.compile(r"\(#(\d+)\)\s*$")


def sh(*a):
    return subprocess.run(a, cwd=REPO, capture_output=True, text=True).stdout


def api(path):
    try:
        with urllib.request.urlopen(DASH + path, timeout=20) as r:
            return json.load(r)
    except Exception as e:
        return {"_err": str(e)[:90]}


def parse_ts(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


# ── 1. commits ───────────────────────────────────────────────────────────
raw = sh("git", "log", f"-{N}", "--pretty=format:%H%x1f%ct%x1f%s%x1f%b%x1e")
commits = []
for rec in raw.split("\x1e"):
    rec = rec.strip("\n")
    if not rec:
        continue
    parts = (rec.split("\x1f") + ["", "", ""])[:4]
    sha, ct, subj, body = parts
    m = PRNUM.search(subj)
    commits.append({
        "sha": sha[:9],
        "ts": int(ct) if ct.isdigit() else 0,
        "subj": subj,
        "pr": m.group(1) if m else None,
        "ours": OURS.findall(body),
        "coauth": bool(COAUTH.search(body)),
    })

# ── 2. sessions the store knows for this repo ────────────────────────────
rows = api("/api/local/sessions?limit=1000").get("rows") or []
sessions = []
for r in rows:
    st, up = parse_ts(r.get("started_at")), parse_ts(r.get("updated_at"))
    if st is None:
        continue
    sessions.append({**r, "_start": st, "_end": up or st})

repo_name = os.path.basename(os.path.realpath(REPO))


def heuristic_match(commit_ts):
    """Sessions overlapping the commit time within WINDOW_S."""
    out = []
    for s in sessions:
        if s["_start"] - WINDOW_S <= commit_ts <= s["_end"] + WINDOW_S:
            out.append(s)
    return out


# ── 3. classify ──────────────────────────────────────────────────────────
by_store = {r["session_id"]: r for r in rows}
tierA = [c for c in commits if any(t in by_store for t in c["ours"])]
tierB = [c for c in commits if c not in tierA and c["coauth"] and heuristic_match(c["ts"])]
with_pr = [c for c in commits if c["pr"]]

print("=" * 74)
print(f"PR -> TRACE JOIN   repo={repo_name}  commits={len(commits)}  window=+/-{WINDOW_S//60}m")
print("=" * 74)
print(f"  commits with a PR number                : {len(with_pr):>4}")
print(f"  TIER A  our trailer, resolves in store  : {len(tierA):>4}   <- needs PRD 4a hook")
print(f"  TIER B  Co-Authored-By + time overlap   : {len(tierB):>4}   <- heuristic, labeled")
print(f"  unjoinable                              : {len(commits)-len(tierA)-len(tierB):>4}")
print(f"  sessions in store                       : {len(rows):>4}")
print()

if not tierA:
    print("TIER A is 0 by construction: no commit in history carries a")
    print("`Clawmetry-Session:` trailer yet. That is the point of PRD 4a --")
    print("coverage starts the day the hook is installed, and cannot be")
    print("backfilled. See PRD-pr-trace.md 3a.")
    print()

# ── 4. what Tier B would offer, per PR ───────────────────────────────────
pr_map = defaultdict(lambda: {"commits": [], "cands": {}})
for c in tierB:
    if not c["pr"]:
        continue
    e = pr_map[c["pr"]]
    e["commits"].append(c)
    for s in heuristic_match(c["ts"]):
        e["cands"][s["session_id"]] = s

if pr_map:
    print(f"TIER-B CANDIDATE PRs: {len(pr_map)}  (heuristic -- never a headline number)")
    print("-" * 74)
    for pr, e in sorted(pr_map.items(), key=lambda kv: -int(kv[0]))[:10]:
        cands = list(e["cands"].values())
        cost = sum(s.get("cost_usd") or 0 for s in cands)
        print(f"#{pr}  {e['commits'][0]['subj'][:50]}")
        print(f"      commits={len(e['commits'])} candidate_sessions={len(cands)} "
              f"ambiguous={'YES' if len(cands) > 1 else 'no'} "
              f"upper_bound=${cost:.2f}")
    print()
    amb = sum(1 for e in pr_map.values() if len(e["cands"]) > 1)
    print(f"  {amb}/{len(pr_map)} PRs match more than one session -> attribution "
          f"must be reported as shared, not summed (PRD 3c).")
