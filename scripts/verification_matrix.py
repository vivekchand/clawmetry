#!/usr/bin/env python3
"""Check the declared verification surface against reality.

``verification/matrix.json`` declares every product x platform x python cell
that must work. This script proves each declaration is real:

* every cell names a verifier that actually EXISTS (a workflow job, or a test
  file) -- so a cell cannot claim coverage that was deleted;
* every gated cell's verifier is a workflow that runs on ``pull_request``
  without a ``paths:`` filter -- a path-filtered workflow does not report on
  most PRs, so calling it "gated" would be a lie;
* the ratchets hold: open holes may only decrease, gated cells may only grow.

Why this exists: coverage used to be implied by whichever tests happened to
exist, and holes opened silently. Python 3.9 ran on Linux only; its one leg
executed ``tests/test_api.py`` and never imported the CLI; the API matrix
installed four dependencies and omitted duckdb and cryptography. Nobody chose
any of that -- it accreted. A declared matrix turns accretion into a diff.

Usage::

    python3 scripts/verification_matrix.py            # check, exit 1 on drift
    python3 scripts/verification_matrix.py --report   # human-readable table
    python3 scripts/verification_matrix.py --json     # machine-readable
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MATRIX_PATH = os.path.join(REPO_ROOT, "verification", "matrix.json")
WORKFLOW_DIR = os.path.join(REPO_ROOT, ".github", "workflows")

VALID_STATUS = {"gated", "continuous", "manual"}


def load_matrix(path: str = MATRIX_PATH) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def iter_cells(matrix: dict):
    """Yield (product_key, cell) for every declared cell."""
    for product_key, product in (matrix.get("products") or {}).items():
        for cell in product.get("cells") or []:
            yield product_key, cell


def _workflow_path(name: str) -> str:
    return os.path.join(WORKFLOW_DIR, name)


def _verifier_exists(verifier: str) -> tuple[bool, str]:
    """Does the thing this cell points at actually exist?

    Accepts three shapes:
      * ``some-workflow.yml::job-id``
      * ``some-workflow.yml``
      * ``tests/test_x.py`` (or any repo-relative path)

    A path naming another repository (``clawmetry-pro/...``) is treated as
    present-but-unverifiable: this script cannot see sibling repos, and
    pretending otherwise would be worse than saying so.
    """
    if verifier.startswith(("clawmetry-pro/", "clawmetry-cloud/", "clawmetry-hardware/", "clawmetry-landing/")):
        return True, "cross-repo (not checkable from here)"

    if "::" in verifier:
        workflow, job = verifier.split("::", 1)
        path = _workflow_path(workflow)
        if not os.path.isfile(path):
            return False, f"workflow {workflow} not found"
        with open(path, encoding="utf-8") as fh:
            source = fh.read()
        if f"\n  {job}:" not in source:
            return False, f"job {job!r} not found in {workflow}"
        return True, f"{workflow} job {job}"

    if verifier.endswith((".yml", ".yaml")):
        path = _workflow_path(verifier)
        if not os.path.isfile(path):
            return False, f"workflow {verifier} not found"
        return True, verifier

    path = os.path.join(REPO_ROOT, verifier)
    if os.path.isfile(path):
        return True, verifier
    # Allow a glob-ish declaration to match at least one file.
    if glob.glob(path):
        return True, verifier
    return False, f"path {verifier} not found"


def _runs_on_every_pr(workflow: str) -> tuple[bool, str]:
    """A gated verifier must actually report on every pull request."""
    path = _workflow_path(workflow)
    if not os.path.isfile(path):
        return False, "workflow missing"
    with open(path, encoding="utf-8") as fh:
        source = fh.read()

    head = source.split("\njobs:", 1)[0]
    lines = head.split("\n")

    # Locate `  pull_request:` at exactly two-space indent, then read its block:
    # every following line indented deeper than it. Naive string splitting gets
    # this wrong -- "\n  " also matches a four-space line, so the paths: filter
    # is skipped and a path-filtered workflow looks unconditional.
    pr_index = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in ("pull_request:", "pull_request:{}") and line.startswith("  ") and not line.startswith("   "):
            pr_index = i
            break
        # `pull_request:` with an inline value, e.g. `pull_request: {}`
        if stripped.startswith("pull_request:") and line.startswith("  ") and not line.startswith("   "):
            pr_index = i
            break

    if pr_index is None:
        return False, "no pull_request trigger"

    block: list[str] = []
    for line in lines[pr_index + 1:]:
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= 2:
            break
        block.append(line.strip())

    for entry in block:
        if entry.startswith("paths:") or entry.startswith("paths-ignore:"):
            return False, "pull_request has a paths: filter"

    return True, "runs on every PR"


def check(matrix: dict | None = None) -> list[dict]:
    """Return a list of problems. Empty means the declared surface is honest."""
    matrix = matrix or load_matrix()
    problems: list[dict] = []
    seen_ids: set = set()

    for product_key, cell in iter_cells(matrix):
        cid = cell.get("id", "<no id>")

        if cid in seen_ids:
            problems.append({"cell": cid, "problem": "duplicate cell id"})
        seen_ids.add(cid)

        status = cell.get("status")
        if status not in VALID_STATUS:
            problems.append(
                {"cell": cid, "problem": f"invalid status {status!r} (expected {sorted(VALID_STATUS)})"}
            )
            continue

        verifier = cell.get("verifier", "")
        if not verifier:
            problems.append({"cell": cid, "problem": "no verifier declared"})
            continue

        exists, detail = _verifier_exists(verifier)
        if not exists:
            problems.append(
                {
                    "cell": cid,
                    "problem": f"verifier does not exist: {detail}",
                    "product": product_key,
                }
            )
            continue

        if status == "gated" and "::" in verifier:
            workflow = verifier.split("::", 1)[0]
            ok, why = _runs_on_every_pr(workflow)
            if not ok:
                problems.append(
                    {
                        "cell": cid,
                        "problem": (
                            f"declared 'gated' but {workflow} {why}. A workflow "
                            "that does not report on every PR cannot gate a merge "
                            "-- mark the cell 'continuous' instead."
                        ),
                    }
                )

    # Ratchets.
    ratchets = matrix.get("ratchets") or {}
    open_holes = len(matrix.get("open_holes") or [])
    gated = sum(1 for _, c in iter_cells(matrix) if c.get("status") == "gated")

    max_holes = (ratchets.get("max_open_holes") or {}).get("value")
    if max_holes is not None and open_holes > max_holes:
        problems.append(
            {
                "cell": "<ratchet>",
                "problem": (
                    f"open_holes rose to {open_holes}, above the recorded "
                    f"{max_holes}. Known gaps may only shrink -- otherwise "
                    "'manual' becomes a dumping ground. Fix a hole, or lower "
                    "the bar deliberately and say why in the PR."
                ),
            }
        )

    min_gated = (ratchets.get("min_gated_cells") or {}).get("value")
    if min_gated is not None and gated < min_gated:
        problems.append(
            {
                "cell": "<ratchet>",
                "problem": (
                    f"gated cells fell to {gated}, below the recorded "
                    f"{min_gated}. Merge-blocking coverage may only grow."
                ),
            }
        )

    return problems


def summary(matrix: dict | None = None) -> dict:
    matrix = matrix or load_matrix()
    cells = [c for _, c in iter_cells(matrix)]
    counts = {s: sum(1 for c in cells if c.get("status") == s) for s in sorted(VALID_STATUS)}
    return {
        "total_cells": len(cells),
        "by_status": counts,
        "open_holes": len(matrix.get("open_holes") or []),
        "products": len(matrix.get("products") or {}),
    }


def _report(matrix: dict) -> None:
    s = summary(matrix)
    print("PRODUCT TRUTH MATRIX")
    print("=" * 72)
    print(
        f"{s['total_cells']} cells across {s['products']} products   "
        f"gated={s['by_status']['gated']}  "
        f"continuous={s['by_status']['continuous']}  "
        f"manual={s['by_status']['manual']}   "
        f"open holes={s['open_holes']}"
    )
    print()
    for product_key, product in (matrix.get("products") or {}).items():
        print(f"  {product.get('label', product_key)}")
        for cell in product.get("cells") or []:
            mark = {"gated": "[GATE]", "continuous": "[CONT]", "manual": "[MANU]"}[
                cell.get("status", "manual")
            ]
            plat = cell.get("platform", "-")
            py = cell.get("python", "-")
            print(f"    {mark} {cell['id']:<32} {plat:<16} py={py}")
        print()

    holes = matrix.get("open_holes") or []
    if holes:
        print("OPEN HOLES (counted, ratcheted -- may only shrink)")
        print("-" * 72)
        for hole in holes:
            print(f"  * {hole['id']} [{hole.get('owner', '?')}]")
            print(f"      {hole['detail']}")
            print(f"      impact: {hole['impact']}")
        print()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--report", action="store_true", help="print a readable table")
    ap.add_argument("--json", action="store_true", help="print machine-readable summary")
    args = ap.parse_args()

    matrix = load_matrix()

    if args.json:
        print(json.dumps({"summary": summary(matrix), "problems": check(matrix)}, indent=2))
        return 1 if check(matrix) else 0

    if args.report:
        _report(matrix)

    problems = check(matrix)
    if problems:
        print("VERIFICATION MATRIX DRIFT")
        print("=" * 72)
        for p in problems:
            print(f"  {p['cell']}: {p['problem']}")
        print()
        print(f"{len(problems)} problem(s). The declared surface does not match reality.")
        return 1

    s = summary(matrix)
    print(
        f"OK - {s['total_cells']} declared cells all resolve "
        f"({s['by_status']['gated']} gated, {s['by_status']['continuous']} continuous, "
        f"{s['by_status']['manual']} manual, {s['open_holes']} known holes)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
