#!/usr/bin/env python3
"""scripts/accuracy_harness/all.py — meta-runner for every accuracy harness.

Shells out to each sub-harness, parses its `summary: N pass / N drift`
line, prints a scoreboard, exits with worst status (0 PASS / 1 DRIFT /
2 ERROR). Consolidated GitHub-issue filing is deferred to a follow-up PR
— `file_consolidated_issue` only PRINTS what it would file today.

Sub-harnesses do NOT support --dry-run; the meta `--dry-run` short-
circuits before shelling out so the runner skeleton is provable without
spending real LLM budget.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HARNESSES: list[tuple[str, str]] = [
    ("tokens",    "scripts/accuracy_harness/tokens.py"),
    ("approvals", "scripts/accuracy_harness/approvals.py"),
    ("alerts",    "scripts/accuracy_harness/alerts.py"),
]

PER_HARNESS_TIMEOUT_S = 180
SUMMARY_RE = re.compile(r"summary:\s*(\d+)\s*pass\s*/\s*(\d+)\s*drift")
REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass
class HarnessResult:
    name: str
    exit_code: int       # 0/1/2 from sub-harness; 2 for timeout/exec error
    pass_count: int      # -1 if summary line unparseable
    drift_count: int     # -1 if summary line unparseable
    status: str          # "pass" | "drift" | "error"
    note: str = ""

    @property
    def parsed(self) -> bool:
        return self.pass_count >= 0 and self.drift_count >= 0


def run_one(name: str, rel_path: str) -> HarnessResult:
    abs_path = REPO_ROOT / rel_path
    if not abs_path.exists():
        return HarnessResult(name, 2, -1, -1, "error", f"missing: {rel_path}")
    try:
        proc = subprocess.run([sys.executable, str(abs_path)],
                              capture_output=True, text=True,
                              timeout=PER_HARNESS_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        return HarnessResult(name, 2, -1, -1, "error",
                             f"timed out after {PER_HARNESS_TIMEOUT_S}s")
    except Exception as e:
        return HarnessResult(name, 2, -1, -1, "error", f"exec failed: {e}")

    matches = SUMMARY_RE.findall(proc.stdout or "")
    if not matches:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()[-1:]
        return HarnessResult(name, max(proc.returncode, 2), -1, -1, "error",
                             f"unparseable summary; rc={proc.returncode}; tail={tail!r}")
    p, d = map(int, matches[-1])
    status = {0: "pass", 1: "drift"}.get(proc.returncode, "error")
    return HarnessResult(name, proc.returncode, p, d, status, f"rc={proc.returncode}")


def print_scoreboard(results: list[HarnessResult]) -> None:
    print()
    print("─" * 70)
    print(f"{'HARNESS':<12} {'STATUS':<7} {'PASS':>5} {'DRIFT':>6} {'EXIT':>5}  NOTE")
    print("─" * 70)
    for r in results:
        p = str(r.pass_count) if r.parsed else "?"
        d = str(r.drift_count) if r.parsed else "?"
        print(f"{r.name:<12} {r.status.upper():<7} {p:>5} {d:>6} {r.exit_code:>5}  {r.note}")
    print("─" * 70)
    total_p = sum(r.pass_count for r in results if r.parsed)
    total_d = sum(r.drift_count for r in results if r.parsed)
    n_err = sum(1 for r in results if r.status == "error")
    print(f"OVERALL: {total_p} pass / {total_d} drift across "
          f"{len(results)} harness(es) ({n_err} error)")


def overall_exit_code(results: list[HarnessResult]) -> int:
    if any(r.status == "error" for r in results): return 2
    if any(r.status == "drift" for r in results): return 1
    return 0


def file_consolidated_issue(results: list[HarnessResult]) -> None:
    # Skeleton — gh-issue filing lands in the follow-up PR. Print only.
    n_drifts = sum(r.drift_count for r in results if r.parsed and r.drift_count > 0)
    n_h = sum(1 for r in results if r.status != "pass")
    print(f"[meta] Would file consolidated issue: {n_drifts} drifts across "
          f"{n_h} harness(es) (filer not yet implemented)")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--harnesses", type=str, default="",
                   help=f"comma-separated subset (default: all). "
                        f"choices: {','.join(n for n, _ in HARNESSES)}")
    p.add_argument("--no-issue", action="store_true",
                   help="skip the (future) consolidated drift-issue filer")
    p.add_argument("--dry-run", action="store_true",
                   help="short-circuit before shelling out (sub-harnesses don't "
                        "support --dry-run yet, so it isn't passed through)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    selected = {n.strip() for n in args.harnesses.split(",") if n.strip()}
    plan = [(n, p) for n, p in HARNESSES if not selected or n in selected]
    if not plan:
        print(f"[meta] no harnesses match --harnesses={args.harnesses!r}",
              file=sys.stderr)
        return 2
    print(f"[meta] runner skeleton — {len(plan)} harness(es): "
          f"{', '.join(n for n, _ in plan)}")
    if args.dry_run:
        results = [HarnessResult(n, 0, 0, 0, "pass", "dry-run (skipped)")
                   for n, _ in plan]
    else:
        results = [run_one(n, p) for n, p in plan]
        for r in results:
            if r.status == "error":
                print(f"[meta] {r.name}: ERROR — {r.note}", file=sys.stderr)
    print_scoreboard(results)
    if not args.no_issue:
        file_consolidated_issue(results)
    return overall_exit_code(results)


if __name__ == "__main__":
    sys.exit(main())
