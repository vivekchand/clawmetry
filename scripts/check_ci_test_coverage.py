#!/usr/bin/env python3
"""CI test-file coverage ratchet.

Every tests/test_*.py file must appear in at least one .github/workflows/*.yml
file, or CI will silently never run it. This repo uses explicit file lists, not
a catch-all ``pytest tests/`` (documented in CLAUDE.md), so the failure mode is
invisible: the test passes locally, the PR goes green, and the guard never runs
again.

This script measures the gap and enforces it as a one-way ratchet against
``docs/ci_test_coverage_baseline.json``:

  * The unlisted-file count may never GROW above the baseline.
  * When tests that were previously unlisted get wired into a workflow job,
    the baseline must be tightened in the same PR.

Usage
-----
    python3 scripts/check_ci_test_coverage.py --check             # CI gate
    python3 scripts/check_ci_test_coverage.py --report            # human summary
    python3 scripts/check_ci_test_coverage.py --update-baseline   # tighten ratchet

Related: issue #5813 -- "82% of the test suite runs in no CI job"

Recorded as "A test named in no workflow runs in no job" in the Release
Verification and Merge Gating blueprint, which carries the contracts (the
count may never grow; tightening is explicit via --update-baseline) and the
ADR for why this records the debt and fails only on GROWTH rather than
demanding a 933-file cleanup before anything else can merge.

One limit worth knowing: this checks that a file is NAMED in a workflow, not
that the job can run it. A test wired into a job without its dependencies
collects nothing and pytest exits 5 -- listed, and still never executed.
"""

import argparse
import json
import os
import re
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TESTS_DIR = os.path.join(REPO_ROOT, "tests")
WORKFLOWS_DIR = os.path.join(REPO_ROOT, ".github", "workflows")
BASELINE_PATH = os.path.join(REPO_ROOT, "docs", "ci_test_coverage_baseline.json")


def _collect_test_files():
    """Return sorted list of test file basenames under tests/."""
    names = []
    for entry in os.listdir(TESTS_DIR):
        if entry.startswith("test_") and entry.endswith(".py"):
            names.append(entry)
    return sorted(names)


def _collect_workflow_text():
    """Return the concatenated text of all workflow YAML files."""
    chunks = []
    for entry in sorted(os.listdir(WORKFLOWS_DIR)):
        if not (entry.endswith(".yml") or entry.endswith(".yaml")):
            continue
        path = os.path.join(WORKFLOWS_DIR, entry)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                chunks.append(fh.read())
        except OSError:
            pass
    return "\n".join(chunks)


def compute_coverage():
    """Return (listed, unlisted) as sorted lists of test file basenames."""
    all_tests = _collect_test_files()
    workflow_text = _collect_workflow_text()

    listed = []
    unlisted = []
    for name in all_tests:
        pattern = r"\b" + re.escape(name) + r"\b"
        if re.search(pattern, workflow_text):
            listed.append(name)
        else:
            unlisted.append(name)
    return listed, unlisted


def _load_baseline():
    if not os.path.exists(BASELINE_PATH):
        raise SystemExit(
            "Baseline not found: %s\n"
            "Run: python3 scripts/check_ci_test_coverage.py --update-baseline"
            % BASELINE_PATH
        )
    with open(BASELINE_PATH, "r", encoding="utf-8") as fh:
        return json.load(fh)


def cmd_report():
    listed, unlisted = compute_coverage()
    total = len(listed) + len(unlisted)
    pct = (100.0 * len(unlisted) / total) if total else 0.0
    print(
        "CI test-file coverage: %d listed, %d unlisted of %d total (%.0f%% unlisted)\n"
        % (len(listed), len(unlisted), total, pct)
    )
    if unlisted:
        print("Unlisted test files (%d):" % len(unlisted))
        for name in unlisted:
            print("  tests/%s" % name)
    return 0


def cmd_update_baseline():
    listed, unlisted = compute_coverage()
    total = len(listed) + len(unlisted)
    payload = {
        "_comment": [
            "Ratchet baseline for scripts/check_ci_test_coverage.py.",
            "'unlisted_max' is the maximum number of tests/test_*.py files",
            "that may be absent from all .github/workflows/*.yml files.",
            "CI fails when the unlisted count GROWS above this number.",
            "Ratchet down by running --update-baseline after wiring new tests in.",
            "Related: issue #5813",
        ],
        "total": total,
        "listed": len(listed),
        "unlisted_max": len(unlisted),
    }
    os.makedirs(os.path.dirname(BASELINE_PATH), exist_ok=True)
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(
        "baseline written: %d listed, %d unlisted (max allowed: %d)"
        % (len(listed), len(unlisted), len(unlisted))
    )
    return 0


def cmd_check():
    listed, unlisted = compute_coverage()
    baseline = _load_baseline()
    unlisted_max = int(baseline.get("unlisted_max", 0))
    baseline_total = int(baseline.get("total", 0))

    current_total = len(listed) + len(unlisted)
    failures = []

    if len(unlisted) > unlisted_max:
        overage = len(unlisted) - unlisted_max
        failures.append(
            "CI test-file coverage ratchet exceeded: %d unlisted (max %d, over by %d).\n"
            "  Every tests/test_*.py file must be named in at least one\n"
            "  .github/workflows/*.yml file, or it will never run in CI.\n"
            "  Add the new test file to a workflow job in the same PR.\n"
            "  All currently unlisted files (%d):\n"
            % (len(unlisted), unlisted_max, overage, len(unlisted))
            + "".join("    tests/%s\n" % name for name in unlisted)
        )

    if len(unlisted) < unlisted_max and current_total <= baseline_total:
        # Coverage improved without new test files being added -- previously
        # unlisted tests were wired into a workflow. Tighten the ratchet.
        failures.append(
            "CI test-file coverage improved but the ratchet was not tightened.\n"
            "  unlisted: %d (was: %d). Run:\n"
            "    python3 scripts/check_ci_test_coverage.py --update-baseline\n"
            "  and commit docs/ci_test_coverage_baseline.json.\n"
            % (len(unlisted), unlisted_max)
        )

    if failures:
        print("CI test-file coverage ratchet FAILED\n")
        for i, msg in enumerate(failures, 1):
            print("%d. %s" % (i, msg))
        return 1

    print(
        "CI test-file coverage ratchet OK: %d listed, %d unlisted "
        "(max allowed: %d)" % (len(listed), len(unlisted), unlisted_max)
    )
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="CI gate (exits 1 on regression)")
    g.add_argument("--report", action="store_true", help="print a human-readable summary")
    g.add_argument(
        "--update-baseline", action="store_true", help="tighten the ratchet"
    )
    args = ap.parse_args()

    if args.report:
        return cmd_report()
    if args.update_baseline:
        return cmd_update_baseline()
    return cmd_check()


if __name__ == "__main__":
    sys.exit(main())
