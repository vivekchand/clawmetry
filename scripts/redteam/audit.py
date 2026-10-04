#!/usr/bin/env python3
"""Red-team detection audit: replay every publicly disclosed agent attack in the
corpus against ClawMetry's own detectors and report what we would MISS.

This is the antivirus model applied to agent behaviour. ``scripts/harness/audit.py``
asks "what does the harness expose that we fail to *observe*?"; this asks the
sharper question: "here is an attack that really happened to somebody — would we
have *caught* it?" A corpus entry is a signature; a MISS is a gap worth an issue.

Two evaluation surfaces, because agent attacks arrive on both:

  * ``tool_stream``  — synthetic events fed to ``detectors.run_all``. This is the
    surface we already cover.
  * ``repo_config`` / ``agent_config`` — files materialised into a throwaway
    workspace and handed to ``clawmetry.repo_scan``. GitSpawn lives here, and it
    is precisely the surface a tool-stream detector cannot see: git spawns the
    payload, the agent never calls a tool, and by the time anything is logged the
    code has already run.

Every payload in the corpus is inert. ``{{MARKER_CMD}}`` expands to a command
that writes a marker file inside the temp workspace and nothing else, so a case
can prove it *would* have executed without executing anything that matters.
Workspaces are materialised under a temp dir and never inside a real repo.

Controls are load-bearing. Cases marked ``"control": true`` are self-tests: two
positives that existing detectors must catch, and one negative (a real git-lfs
config) that a scanner must stay quiet about. If a control fails, the audit's
verdict on everything else is untrustworthy and the run exits non-zero.

Known gaps. A case may carry ``"known_gap": {"issue": "<repo>#<n>", "since":
"<date>"}``: a disclosed attack we verified we MISS and cannot close the same
day. It stays in the corpus and is re-run on every build, but its MISS is
reported as KNOWN-GAP rather than as a regression, and ``--strict`` does not
fail on it. The moment it starts passing it is reported as GAP-CLOSED, which
DOES fail ``--strict``, so the flag cannot outlive the gap. The flag only counts
with a non-empty ``issue`` (otherwise it is ignored and the case fails as usual),
and it never softens a control or an UNSAFE-CORPUS verdict.

Usage:
  python3 scripts/redteam/audit.py                    # run corpus, print report
  python3 scripts/redteam/audit.py --json report.json # machine-readable
  python3 scripts/redteam/audit.py --file-issues      # open sec-gap issues (pro)
  python3 scripts/redteam/audit.py --case gitspawn-core-fsmonitor
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
CORPUS_DIR = os.path.join(HERE, "corpus")

if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

# Gaps are product work on closed-source detectors, so they go to the private
# tracker. The public repo is reserved for contributor-actionable issues.
ISSUE_REPO = os.environ.get("REDTEAM_ISSUE_REPO", "vivekchand/clawmetry-pro")
_ISSUE_LABELS = ["security-gap", "automated", "detection"]
_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}
_MARKER_NAME = "redteam-payload-fired"
# A fixed clock for the before/after inventory pass, so a case is reproducible.
_INVENTORY_T0_MS = 1_790_000_000_000


def _load_corpus(only: str | None = None) -> list:
    cases = []
    for path in sorted(glob.glob(os.path.join(CORPUS_DIR, "*.json"))):
        try:
            with open(path, encoding="utf-8") as f:
                case = json.load(f)
        except Exception as e:
            print(f"  [skip] {os.path.basename(path)}: unreadable ({e})")
            continue
        case["_path"] = path
        if only and case.get("id") != only:
            continue
        cases.append(case)
    return cases


def known_gap_issue(case: dict) -> str:
    """The tracking issue of a well-formed ``known_gap`` flag, else ``""``.

    A flag without an issue reference is treated as absent: "known" means
    somebody wrote the gap down, and marking a case known is otherwise just the
    lazy way to turn a red suite green. Controls can never be known gaps.
    """
    if case.get("control"):
        return ""
    kg = case.get("known_gap")
    if not isinstance(kg, dict):
        return ""
    issue = kg.get("issue")
    return issue.strip() if isinstance(issue, str) else ""


def _apply_known_gap(case: dict, result: dict) -> dict:
    """Reclassify a known gap's verdict. Only MISS and UNDER-SEVERITY soften."""
    issue = known_gap_issue(case)
    if not issue:
        return result
    if result["verdict"] in ("MISS", "UNDER-SEVERITY"):
        result = dict(result, verdict="KNOWN-GAP",
                      detail=f"{result['detail']} (known gap, tracked in {issue})")
    elif result["verdict"] == "PASS":
        result = dict(result, verdict="GAP-CLOSED",
                      detail=(f"{result['detail']}; the gap in {issue} is closed, "
                              f"remove known_gap from the case"))
    return result


def _materialise(case: dict, root: str, key: str = "files") -> str:
    """Write the case's workspace into ``root``. Returns the workspace path.

    ``key`` picks which file set to write: ``files`` (the state the scanners
    read) or ``before`` (the earlier state a change is measured against).

    The marker command writes into ``root`` and does nothing else — the corpus
    describes attacks, it does not carry working ones.
    """
    ws = os.path.join(root, "workspace")
    marker = os.path.join(root, _MARKER_NAME)
    marker_cmd = f"/bin/sh -c 'echo fired > {marker}'"
    files = ((case.get("workspace") or {}).get(key) or {})
    for rel, content in files.items():
        dest = os.path.join(ws, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            # {{WORKSPACE}} is the materialised workspace's absolute path. A
            # linked-worktree case needs it: git writes an ABSOLUTE gitdir into
            # the .git FILE, and a case that used a relative one would exercise
            # a path git does not actually produce.
            f.write(str(content)
                    .replace("{{MARKER_CMD}}", marker_cmd)
                    .replace("{{WORKSPACE}}", ws))
    for rel in ((case.get("workspace") or {}).get("executable") or []):
        dest = os.path.join(ws, rel)
        if os.path.exists(dest):
            # Owner-only (0o700), never 0o755. The bit that matters to a case is
            # "is this executable at all"; group and other need nothing here, and
            # a world-readable attack fixture in a shared temp dir is a small
            # hole of exactly the kind this corpus exists to complain about.
            os.chmod(dest, 0o700)
    os.makedirs(ws, exist_ok=True)
    return ws


def _run_tool_stream(case: dict) -> list:
    """Feed the case's synthetic events to every shipped detector."""
    events = case.get("events") or []
    if not events:
        return []
    try:
        from clawmetry import detectors
    except Exception as e:
        print(f"  [error] cannot import detectors: {e}")
        return []
    runtimes = [r for r in (case.get("affects_runtimes") or []) if r != "*"]
    runtime = runtimes[0] if runtimes else "claude_code"
    sid = f"{runtime}:redteam-{case.get('id', 'case')}"
    # The store hands detectors events NEWEST-FIRST; the corpus reads
    # chronologically, which is how a human writes an attack down.
    newest_first = list(reversed(events))
    try:
        return detectors.run_all(newest_first, sid, runtime) or []
    except Exception as e:
        print(f"  [error] run_all raised: {e}")
        return []


def _run_workspace(case: dict, ws: str) -> list:
    """Hand the materialised workspace to the repo/agent-config scanner.

    Absent scanner is not a crash — it is the finding. Every ``repo_config``
    and ``agent_config`` case reports MISS until the scanner ships, which is
    exactly the gap this audit exists to make visible.
    """
    if not (case.get("workspace") or {}).get("files"):
        return []
    try:
        from clawmetry import repo_scan
    except Exception:
        return []
    try:
        return repo_scan.scan_workspace(ws) or []
    except Exception as e:
        print(f"  [error] scan_workspace raised: {e}")
        return []


def _inventory_rows(root: str, ws: str, previous, now_ms: int):
    """One inventory pass over the workspace, as the daemon runs it.

    The home directory is an empty one under ``root``: the collector also reads
    ``~/.claude.json`` for the project's MCP servers, and an audit must not
    depend on the files of whoever runs it.
    """
    from clawmetry import agent_inventory
    home = os.path.join(root, "home")
    os.makedirs(home, exist_ok=True)
    current = agent_inventory.collect_workspace(ws, home=home)
    rows, _changes = agent_inventory.diff_inventory(
        previous or [], current, baseline=previous is None, now_ms=now_ms)
    return rows


def _inventory_baseline(case: dict, root: str):
    """Record the case's ``workspace.before`` state, or None when it has none.

    Some attacks are a CHANGE to the workspace rather than a state of it: a
    dependency with an install script that was not in the lockfile an hour
    ago. Such a case lists the earlier files under ``before``; ``files`` is
    then written over them and the inventory is diffed, which is the daemon's
    own first-sight-then-change path (``clawmetry/agent_inventory.py``).
    """
    if "before" not in (case.get("workspace") or {}):
        return None
    try:
        ws = _materialise(case, root, "before")
        return _inventory_rows(root, ws, None, _INVENTORY_T0_MS)
    except Exception as e:
        print(f"  [error] inventory baseline raised: {e}")
        return None


def _run_inventory(case: dict, root: str, ws: str, baseline) -> list:
    """Findings for what changed in the workspace since ``before``."""
    if baseline is None:
        return []
    try:
        from clawmetry import agent_inventory
        later = _INVENTORY_T0_MS + 600_000
        rows = _inventory_rows(root, ws, baseline, later)
        runtimes = [r for r in (case.get("affects_runtimes") or []) if r != "*"]
        runtime = runtimes[0] if runtimes else "claude_code"
        return agent_inventory.incidents_for_session(
            rows, f"{runtime}:redteam-{case.get('id', 'case')}", runtime, ws,
            now_ms=later) or []
    except Exception as e:
        print(f"  [error] inventory diff raised: {e}")
        return []


def _evaluate(case: dict, incidents: list) -> dict:
    """Compare what fired against what the case says must fire."""
    expect = case.get("expect") or {}
    want_detect = bool(expect.get("detected"))
    accepted = set(expect.get("any_of") or [])
    min_sev = expect.get("min_severity")
    kinds = {i.get("kind") for i in incidents if isinstance(i, dict)}
    matched = [i for i in incidents
               if isinstance(i, dict) and i.get("kind") in accepted]

    if not want_detect:
        # Negative control: anything firing is a false positive.
        return {
            "verdict": "PASS" if not incidents else "FALSE-POSITIVE",
            "fired": sorted(k for k in kinds if k),
            "detail": ("stayed quiet, as required" if not incidents
                       else f"flagged a benign workspace with {sorted(kinds)}"),
        }
    if not matched:
        return {
            "verdict": "MISS",
            "fired": sorted(k for k in kinds if k),
            "detail": (f"no detector in {sorted(accepted)} fired"
                       + (f"; other detectors fired: {sorted(kinds)}" if kinds else
                          "; nothing fired at all")),
        }
    if min_sev:
        best = max((_SEVERITY_RANK.get(i.get("severity", "info"), 0) for i in matched),
                   default=0)
        if best < _SEVERITY_RANK.get(min_sev, 0):
            got = [i.get("severity") for i in matched]
            return {
                "verdict": "UNDER-SEVERITY",
                "fired": sorted(k for k in kinds if k),
                "detail": f"fired at {got}, case requires at least {min_sev}",
            }
    return {
        "verdict": "PASS",
        "fired": sorted(k for k in kinds if k),
        "detail": f"caught by {sorted({i.get('kind') for i in matched})}",
    }


def run_case(case: dict) -> dict:
    root = tempfile.mkdtemp(prefix="rt-audit-")
    try:
        baseline = _inventory_baseline(case, root)
        ws = _materialise(case, root)
        incidents = (_run_tool_stream(case) + _run_workspace(case, ws)
                     + _run_inventory(case, root, ws, baseline))
        result = _evaluate(case, incidents)
        # A corpus payload must never actually execute during an audit.
        if os.path.exists(os.path.join(root, _MARKER_NAME)):
            result["verdict"] = "UNSAFE-CORPUS"
            result["detail"] = ("the case's payload EXECUTED during the audit — "
                                "a corpus entry must be inert; fix the case")
        result.update({
            "id": case.get("id"),
            "name": case.get("name"),
            "surface": case.get("surface"),
            "control": bool(case.get("control")),
        })
        return result
    finally:
        shutil.rmtree(root, ignore_errors=True)


def _fingerprint(case: dict) -> str:
    # usedforsecurity=False: this is a dedupe key, not a security control. See
    # the matching note in scripts/harness/audit.py — the digest only has to be
    # stable so a daily run recognises a gap it already filed. Clears bandit
    # B324 (CWE-327); SHA-1 is kept rather than widened to SHA-256 because
    # changing the digest would re-file every gap already on file exactly once.
    key = f"{case.get('id', '')}:{case.get('surface', '')}".lower()
    return "sgap-" + hashlib.sha1(key.encode(), usedforsecurity=False).hexdigest()[:10]


def _existing_fingerprints() -> set:
    import re
    try:
        out = subprocess.check_output(
            ["gh", "issue", "list", "-R", ISSUE_REPO, "--label", "security-gap",
             "--state", "all", "--limit", "500", "--json", "body"],
            text=True, stderr=subprocess.DEVNULL)
        fps: set = set()
        for it in json.loads(out):
            fps.update(re.findall(r"sgap-[0-9a-f]{10}", it.get("body") or ""))
        return fps
    except Exception:
        return set()


def _issue_body(case: dict, result: dict, fp: str) -> str:
    expect = case.get("expect") or {}
    runtimes = case.get("affects_runtimes") or []
    cves = ", ".join(case.get("cve") or []) or "—"
    return (
        f"A disclosed attack in the red-team corpus is **not detected** by "
        f"ClawMetry today.\n\n"
        f"- **Attack:** {case.get('summary', '')}\n"
        f"- **Disclosed:** {case.get('disclosed', '?')} — {case.get('source', '')}\n"
        f"- **CVE:** {cves}\n"
        f"- **Attack class:** `{case.get('attack_class', '?')}` on the "
        f"`{case.get('surface', '?')}` surface\n"
        f"- **Affects runtimes:** {', '.join(runtimes) or '—'}\n\n"
        f"### Why we miss it\n{case.get('why_hard_to_see', '')}\n\n"
        f"### Audit result\n"
        f"- Verdict: **{result.get('verdict')}** — {result.get('detail')}\n"
        f"- Expected one of: `{', '.join(expect.get('any_of') or []) or '—'}` "
        f"at severity ≥ `{expect.get('min_severity') or '—'}`\n"
        f"- Detectors that did fire: "
        f"`{', '.join(result.get('fired') or []) or 'none'}`\n\n"
        f"### What closing this means\n{expect.get('rationale', '')}\n\n"
        f"### Done when\n"
        f"`python3 scripts/redteam/audit.py --case {case.get('id')}` reports PASS, "
        f"and `control-benign-repo` still reports PASS (no false positive).\n\n"
        f"_Filed by `scripts/redteam/audit.py`. Corpus case: "
        f"`scripts/redteam/corpus/{os.path.basename(case.get('_path', ''))}`. "
        f"Fingerprint: {fp} (used to dedupe — keep it in the body)._"
    )


def _file_issue(case: dict, result: dict, fp: str, dry: bool) -> None:
    title = f"[sec-gap:{case.get('surface', 'unknown')}] " + str(case.get("name", ""))[:130]
    sev = "high" if (case.get("expect") or {}).get("min_severity") == "critical" else "medium"
    body = _issue_body(case, result, fp)
    labels = _ISSUE_LABELS + [f"severity:{sev}"]
    if dry:
        print(f"    [dry-run] would file to {ISSUE_REPO}: {title}  ({fp})")
        return
    cmd = ["gh", "issue", "create", "-R", ISSUE_REPO, "--title", title,
           "--body", body, "--label", ",".join(labels)]
    try:
        out = subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT)
        print(f"    [filed] {out.strip().splitlines()[-1] if out.strip() else title}")
    except Exception:
        try:
            out = subprocess.check_output(
                ["gh", "issue", "create", "-R", ISSUE_REPO, "--title", title,
                 "--body", body], text=True, stderr=subprocess.STDOUT)
            print(f"    [filed, no labels] {out.strip().splitlines()[-1]}")
        except Exception as e2:
            print(f"    [error] could not file issue: {e2}")


_VERDICT_ICON = {
    "PASS": "ok",
    "MISS": "MISS",
    "FALSE-POSITIVE": "FALSE POSITIVE",
    "UNDER-SEVERITY": "UNDER SEVERITY",
    "UNSAFE-CORPUS": "UNSAFE CORPUS",
    "KNOWN-GAP": "KNOWN GAP",
    "GAP-CLOSED": "GAP CLOSED",
}


def _write_summary(path: str, results: list, misses: list, bad_controls: list,
                   known: list = (), closed: list = ()) -> None:
    """Append a markdown verdict table (one row per case) to ``path``.

    Written for ``$GITHUB_STEP_SUMMARY`` so a scheduled run is readable from the
    Actions tab without opening the log: every case, what fired, and the verdict.
    A summary nobody can read is the same as no audit.
    """
    lines = ["## Red-team detection audit", ""]
    ok = len(results) - len(misses) - len(bad_controls) - len(known) - len(closed)
    lines.append(f"**{ok}/{len(results)} pass** - "
                 f"{len(misses)} gap(s), {len(bad_controls)} control failure(s)")
    lines.append("")
    if known:
        # Visible on every run, so a standing gap is never out of sight.
        lines.append(f"**KNOWN GAP ({len(known)})**: "
                     + ", ".join(f"`{r['id']}`" for r in known))
        lines.append("")
    if closed:
        lines.append(f"**GAP CLOSED ({len(closed)})** - remove `known_gap` from: "
                     + ", ".join(f"`{r['id']}`" for r in closed))
        lines.append("")
    lines.append("| Case | Surface | Verdict | Detectors that fired | Detail |")
    lines.append("|---|---|---|---|---|")
    for r in results:
        name = r["id"] + (" (control)" if r.get("control") else "")
        fired = ", ".join(f"`{d}`" for d in (r.get("fired") or [])) or "none"
        detail = str(r.get("detail", "")).replace("|", "\\|")
        lines.append(f"| {name} | {r.get('surface', '?')} | "
                     f"{_VERDICT_ICON.get(r['verdict'], r['verdict'])} | {fired} | {detail} |")
    lines.append("")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception as e:  # a summary is a nicety; never fail the audit over it
        print(f"[warn] could not write summary to {path}: {e}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", help="run a single corpus case by id")
    ap.add_argument("--json", help="write the full report to this path")
    ap.add_argument("--file-issues", action="store_true",
                    help=f"open a sec-gap issue per MISS in {ISSUE_REPO}")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero on any MISS or GAP-CLOSED (default: only "
                         "on control failure); KNOWN-GAP never fails it")
    ap.add_argument("--summary",
                    help="append a markdown verdict table to this path "
                         "(point it at $GITHUB_STEP_SUMMARY in CI)")
    args = ap.parse_args()

    cases = _load_corpus(args.case)
    if not cases:
        print("No corpus cases found.")
        return 1

    results = []
    print(f"Red-team detection audit — {len(cases)} case(s)\n")
    for case in cases:
        r = _apply_known_gap(case, run_case(case))
        results.append(r)
        icon = {"PASS": "ok  ", "MISS": "MISS", "FALSE-POSITIVE": "FP  ",
                "UNDER-SEVERITY": "SEV ", "UNSAFE-CORPUS": "!!!!",
                "KNOWN-GAP": "KGAP", "GAP-CLOSED": "DONE"}.get(r["verdict"], "??  ")
        tag = " (control)" if r["control"] else ""
        print(f"  [{icon}] {r['id']}{tag}\n         {r['detail']}")

    controls = [r for r in results if r["control"]]
    bad_controls = [r for r in controls if r["verdict"] != "PASS"]
    misses = [r for r in results
              if not r["control"] and r["verdict"] in ("MISS", "UNDER-SEVERITY")]
    unsafe = [r for r in results if r["verdict"] == "UNSAFE-CORPUS"]
    known = [r for r in results if r["verdict"] == "KNOWN-GAP"]
    closed = [r for r in results if r["verdict"] == "GAP-CLOSED"]

    ok = len(results) - len(misses) - len(bad_controls) - len(known) - len(closed)
    print(f"\n{ok}/{len(results)} pass, "
          f"{len(misses)} gap(s), {len(bad_controls)} control failure(s)")
    if known:
        print(f"KNOWN GAP ({len(known)}): " + ", ".join(r["id"] for r in known))
    if closed:
        print(f"GAP CLOSED ({len(closed)}), remove known_gap from: "
              + ", ".join(r["id"] for r in closed))

    if bad_controls:
        print("\nCONTROL FAILURE — the audit cannot vouch for its own verdicts:")
        for r in bad_controls:
            print(f"  {r['id']}: {r['verdict']} — {r['detail']}")

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        print(f"\nReport written to {args.json}")

    if args.summary:
        _write_summary(args.summary, results, misses, bad_controls, known, closed)

    if misses:
        print(f"\nGaps ({len(misses)}):")
        existing = _existing_fingerprints() if args.file_issues else set()
        by_id = {c.get("id"): c for c in cases}
        for r in misses:
            case = by_id.get(r["id"], {})
            fp = _fingerprint(case)
            if fp in existing:
                print(f"  [dup] {r['id']} ({fp}) — already filed")
                continue
            print(f"  {r['id']} — {r['detail']}")
            _file_issue(case, r, fp, dry=not args.file_issues)

    if unsafe or bad_controls:
        return 2
    return 1 if ((misses or closed) and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main())
