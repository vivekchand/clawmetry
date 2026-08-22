#!/usr/bin/env python3
"""Acceptance-criteria traceability gate.

Every acceptance criterion this repository implements (mirrored from 8090
Software Factory into ``docs/acceptance_criteria.json``) must be referenced by
at least one test under ``tests/``. A reference is simply the criterion's id --
``AC-OBS-CEA-001.2`` -- appearing anywhere in the test file: the module
docstring, a test docstring, or the test's name.

Why this exists
---------------
Drift Bot (FLYWHEEL.md 1f) answers "does this PR's diff *contradict* a
blueprint?". It is a changed-code check and it is good at that. It has no
opinion on whether code that nobody touched still *satisfies* a criterion that
was written months ago.

That gap has cost us real bugs. AC-OBS-CEA-001.2 has said "when a cost value
cannot be determined, the system shall identify it as unavailable rather than
report a zero value" since the requirement was written. PR #5079 -- "a failed
DuckDB read is not a window that cost $0.00" -- shipped in August 2026
violating it verbatim, and was found by a founder report in production, not by
CI. AC-OBS-002.3 and AC-GOV-001.3 forbid the same class in different words.
Prose in a document nobody can fail is not a guard.

The ratchet
-----------
Coverage is enforced as a one-way ratchet against
``docs/ac_coverage_baseline.json`` rather than as a hard 100% bar, because
demanding full coverage on day one would simply have meant not landing this at
all. The rules:

  * A criterion that has a test may never lose it.
  * A criterion added to the manifest must arrive with a test.
  * When new criteria gain coverage the baseline must be tightened in the same
    PR, so the number only ever goes down.

Usage
-----
    python3 scripts/check_ac_coverage.py --check             # CI gate
    python3 scripts/check_ac_coverage.py --report            # human summary
    python3 scripts/check_ac_coverage.py --update-baseline   # tighten ratchet
"""

import argparse
import json
import os
import re
import sys
from typing import Dict, List, Set

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST_PATH = os.path.join(REPO_ROOT, "docs", "acceptance_criteria.json")
BASELINE_PATH = os.path.join(REPO_ROOT, "docs", "ac_coverage_baseline.json")
TESTS_DIR = os.path.join(REPO_ROOT, "tests")

# This gate's own tests necessarily contain synthetic criterion ids ("does an
# unknown id get flagged?"), so scanning them would make the harness fail on
# its own fixtures. Excluded for the same reason a linter does not lint its
# test corpus. Keep this list at exactly one entry: any other file wanting an
# exemption is a file trying to dodge the gate.
SCAN_EXCLUDE = frozenset({os.path.join("tests", "test_ac_coverage_guard.py")})

# Matches AC-OBS-001.1, AC-OBS-CEA-002.5, AC-RSO-CWD-001.3, AC-CLOUD-RAAA-007.9.
_AC_ID = r"AC-[A-Z]+(?:-[A-Z]+)*-\d+\.\d+"

# A criterion counts as covered only when a line DECLARES it -- the id is the
# first thing on the line, optionally behind a bullet:
#
#     * AC-OBS-LADC-001.2 -- an unexpected record change is reported as failure
#
# A passing mention in prose does not count. This is not pedantry: the first
# draft of this gate matched the id anywhere in the file, and the sentence
# "Deliberately NOT claimed here: AC-OBS-CEA-001.2" promptly marked that
# criterion covered. A gate that can be satisfied by naming the thing you did
# not do is worse than no gate, because it reports a number people trust.
AC_DECLARATION = re.compile(r"^[ \t]*(?:[*+-][ \t]*)?(" + _AC_ID + r")\b", re.M)

# Every mention, declaration or not -- used only to catch typo'd/stale ids.
AC_MENTION = re.compile(r"\b" + _AC_ID + r"\b")


def _load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_manifest() -> dict:
    manifest = _load_json(MANIFEST_PATH)
    ids = [c["id"] for c in manifest["criteria"]]
    dupes = sorted({i for i in ids if ids.count(i) > 1})
    if dupes:
        raise SystemExit("manifest has duplicate criterion ids: %s" % ", ".join(dupes))
    return manifest


def scan_tests():
    """Scan tests/ and return (declared, mentioned).

    ``declared`` maps an ac id to the test files that DECLARE it (see
    AC_DECLARATION) and is what coverage is computed from. ``mentioned`` maps
    every id that appears at all, and exists only so a typo'd or stale id is
    still caught rather than silently ignored.
    """
    declared = {}  # type: Dict[str, Set[str]]
    mentioned = {}  # type: Dict[str, Set[str]]
    for dirpath, dirnames, filenames in os.walk(TESTS_DIR):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            if not name.endswith(".py"):
                continue
            path = os.path.join(dirpath, name)
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    text = fh.read()
            except OSError:
                continue
            rel = os.path.relpath(path, REPO_ROOT)
            if rel.replace(os.sep, "/") in {
                e.replace(os.sep, "/") for e in SCAN_EXCLUDE
            }:
                continue
            for ac in AC_DECLARATION.findall(text):
                declared.setdefault(ac, set()).add(rel)
            for ac in AC_MENTION.findall(text):
                mentioned.setdefault(ac, set()).add(rel)
    return declared, mentioned


def partition(manifest, declared, mentioned):
    """Split the manifest into covered / uncovered, and find unknown references.

    An "unknown" reference is a test citing an in-repo AC id that the manifest
    does not contain: either a typo, or a criterion that was renamed or deleted
    in the factory without the mirror being refreshed. Both are worth failing
    on -- a test that cites a criterion nobody can find proves nothing.
    """
    known = {c["id"] for c in manifest["criteria"]}
    in_repo = tuple(manifest["in_repo_prefixes"])
    external = tuple(manifest["external_prefixes"].keys())

    covered = sorted(i for i in known if i in declared)
    uncovered = sorted(known - set(declared))

    unknown = sorted(
        ac
        for ac in mentioned
        if ac not in known
        and ac.startswith(in_repo)
        and not ac.startswith(external)
    )
    return covered, uncovered, unknown


def cmd_report(manifest, declared, mentioned):
    covered, uncovered, unknown = partition(manifest, declared, mentioned)
    total = len(manifest["criteria"])
    pct = (100.0 * len(covered) / total) if total else 0.0

    by_doc = {}  # type: Dict[str, List[str]]
    for c in manifest["criteria"]:
        by_doc.setdefault(c["doc"], []).append(c["id"])

    print("Acceptance-criteria coverage: %d/%d (%.1f%%)\n" % (len(covered), total, pct))
    for doc in sorted(by_doc):
        ids = by_doc[doc]
        hit = [i for i in ids if i in declared]
        print("  %-40s %2d/%2d" % (doc, len(hit), len(ids)))

    if uncovered:
        print("\nUncovered (%d):" % len(uncovered))
        for ac in uncovered:
            print("  %s" % ac)
    if unknown:
        print("\nReferenced but not in the manifest (%d):" % len(unknown))
        for ac in unknown:
            print("  %s  <- %s" % (ac, ", ".join(sorted(mentioned[ac]))))
    return 0


def cmd_update_baseline(manifest, declared, mentioned):
    covered, uncovered, unknown = partition(manifest, declared, mentioned)
    if unknown:
        print("refusing to update the baseline while unknown AC ids are referenced:")
        for ac in unknown:
            print("  %s  <- %s" % (ac, ", ".join(sorted(mentioned[ac]))))
        return 1
    payload = {
        "_comment": [
            "Ratchet baseline for scripts/check_ac_coverage.py.",
            "'uncovered' is the set of acceptance criteria that currently have no",
            "test referencing them. This list may only ever SHRINK. CI fails when a",
            "criterion is added to it -- whether by a test regressing or by a new",
            "criterion landing untested -- and fails equally when the list is stale",
            "after coverage improves, so the ratchet is tightened in the same PR.",
            "Regenerate with: python3 scripts/check_ac_coverage.py --update-baseline",
        ],
        "covered_count": len(covered),
        "total_count": len(manifest["criteria"]),
        "uncovered": uncovered,
    }
    with open(BASELINE_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")
    print(
        "baseline written: %d/%d covered, %d uncovered"
        % (len(covered), len(manifest["criteria"]), len(uncovered))
    )
    return 0


def cmd_check(manifest, declared, mentioned):
    covered, uncovered, unknown = partition(manifest, declared, mentioned)
    baseline = _load_json(BASELINE_PATH)
    baseline_uncovered = set(baseline.get("uncovered", []))

    failures = []  # type: List[str]

    if unknown:
        failures.append(
            "Tests reference acceptance criteria that are not in the manifest.\n"
            "  Either the id is a typo, or the criterion was renamed/removed in the\n"
            "  factory and docs/acceptance_criteria.json needs re-syncing.\n"
            + "".join(
                "    %s  <- %s\n" % (ac, ", ".join(sorted(mentioned[ac])))
                for ac in unknown
            )
        )

    regressed = sorted(set(uncovered) - baseline_uncovered)
    if regressed:
        failures.append(
            "These acceptance criteria lost their test coverage (or landed without\n"
            "  any). Every criterion needs at least one test under tests/ citing its\n"
            "  id in a docstring or test name:\n"
            + "".join("    %s\n" % ac for ac in regressed)
        )

    newly_covered = sorted(baseline_uncovered - set(uncovered))
    if newly_covered:
        failures.append(
            "Coverage improved but the ratchet was not tightened. Run:\n"
            "    python3 scripts/check_ac_coverage.py --update-baseline\n"
            "  and commit docs/ac_coverage_baseline.json. Newly covered:\n"
            + "".join("    %s\n" % ac for ac in newly_covered)
        )

    stale = sorted(baseline_uncovered - {c["id"] for c in manifest["criteria"]})
    if stale:
        failures.append(
            "The baseline names criteria the manifest no longer has. Re-sync the\n"
            "  manifest, then run --update-baseline. Stale entries:\n"
            + "".join("    %s\n" % ac for ac in stale)
        )

    total = len(manifest["criteria"])
    if failures:
        print("AC traceability gate FAILED\n")
        for i, msg in enumerate(failures, 1):
            print("%d. %s" % (i, msg))
        return 1

    print(
        "AC traceability gate OK: %d/%d criteria covered, %d uncovered "
        "(ratchet holding)" % (len(covered), total, len(uncovered))
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true", help="CI gate (default in CI)")
    g.add_argument("--report", action="store_true", help="print a coverage summary")
    g.add_argument("--update-baseline", action="store_true", help="tighten the ratchet")
    args = ap.parse_args()

    manifest = load_manifest()
    declared, mentioned = scan_tests()

    if args.report:
        return cmd_report(manifest, declared, mentioned)
    if args.update_baseline:
        return cmd_update_baseline(manifest, declared, mentioned)
    return cmd_check(manifest, declared, mentioned)


if __name__ == "__main__":
    sys.exit(main())
