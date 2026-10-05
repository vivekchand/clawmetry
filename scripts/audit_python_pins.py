#!/usr/bin/env python3
"""Audit every declared Python dependency file for known advisories.

Until now the "Python dependency audit" job ran exactly one command:

    pip-audit --requirement requirements.txt --strict

That audits the dashboard's own runtime range set and nothing else. Everything
else this repository declares in Python went unscanned:

  * the 34 hash-pinned sets in `.github/requirements/`, which are what the CI
    jobs actually install -- the scanners, the test harnesses, the release
    publisher, the pip bootstraps;
  * `deploy/self-hosted/otel-requirements.txt`, the OTLP decoder baked into the
    PUBLISHED, SIGNED self-hosted server image. That one is not CI-only: an
    advisory there ships to whoever runs that image.

Dependabot opens version bumps for those directories, so they do not freeze.
But a version bump is not an advisory gate: Dependabot proposes, a human
merges, and nothing in CI ever said "this pinned closure is named by a
published advisory". A `--require-hashes` pin is a guarantee about provenance,
not about soundness, and the two are easy to confuse precisely because the pin
looks so deliberate.

This script closes that: it audits every declared file, and it reports three
outcomes per file rather than one bit.

  CLEAN        pip-audit resolved the closure and found nothing.
  ACCEPTED     pip-audit found only advisories declared in
               `.github/requirements/audit-acceptance.json` for that file --
               pins sitting at the last release installable on the interpreter
               their job runs, where every fix needs a newer Python.
  UNAUDITABLE  pip-audit could not resolve the closure on this runner at all.
               Declared ones are reported every run and never counted as
               clean. An UNDECLARED one FAILS.

That last rule is the point of the exercise and the reason it is a script
rather than a shell loop. `pip-audit || true` over 36 files renders a scanner
outage, a Requires-Python wall and a missing system library as a green check,
which is the exact failure clawmetry-cloud #2546, clawmetry-pro #204 and
clawmetry-pro #300 were each filed for. A file with no verdict is a gap in
coverage and says so out loud.

Exit status is 0 only when every file is CLEAN, ACCEPTED, or declared
UNAUDITABLE. Any undeclared advisory, any undeclared resolve failure, and any
acceptance that no longer describes the tree exits 1.
"""

import argparse
import glob
import json
import os
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACCEPTANCE_PATH = os.path.join(".github", "requirements", "audit-acceptance.json")

# The declared Python dependency surface, in audit order.
#
# `requirements.txt` carries RANGES and is audited with a full transitive
# resolve, because the question it answers is "what does `pip install
# clawmetry` get a user today" -- auditing it --no-deps would describe the
# three direct names and miss the tree under them.
#
# Every other file is a `--require-hashes` set, which is already a complete
# resolved closure: the installer refuses anything not listed. Those are
# audited --no-deps, so the audit measures the artifacts the job installs
# rather than re-resolving a tree the job will never see.
RANGE_FILES = (
    "requirements.txt",
    # The desktop shell's build/dev set and the LangGraph OTLP recipe users
    # copy. Both name versions without hashes, so neither is a closure: a
    # transitive resolve is what reaches the tree underneath them.
    os.path.join("desktop", "requirements-dev.txt"),
    os.path.join("examples", "otel", "langgraph", "requirements.txt"),
)
PINNED_GLOBS = (
    os.path.join(".github", "requirements", "*.txt"),
    # Both halves of the published, signed self-hosted image: the OTLP decoder
    # and clawmetry's own runtime deps (#6269). These are the only files in
    # this audit whose advisories reach a user machine rather than a runner.
    os.path.join("deploy", "self-hosted", "*requirements.txt"),
)

_NOT_A_REQUIREMENTS_FILE = ("audit-acceptance.json",)


def discover(root=REPO_ROOT):
    """Return [(relpath, resolve_deps)] for every file this audit covers."""
    found = []
    for rel in RANGE_FILES:
        if os.path.isfile(os.path.join(root, rel)):
            found.append((rel, True))
    seen = {rel for rel, _ in found}
    for pattern in PINNED_GLOBS:
        for abspath in sorted(glob.glob(os.path.join(root, pattern))):
            rel = os.path.relpath(abspath, root).replace(os.sep, "/")
            if os.path.basename(rel) in _NOT_A_REQUIREMENTS_FILE:
                continue
            if rel not in seen:
                seen.add(rel)
                found.append((rel, False))
    return found


def load_acceptance(root=REPO_ROOT):
    with open(os.path.join(root, ACCEPTANCE_PATH)) as handle:
        data = json.load(handle)
    accepted = {}
    for rel, entries in (data.get("accepted_advisories") or {}).items():
        for entry in entries:
            for ident in entry["ids"]:
                accepted.setdefault(rel, set()).add((entry["package"].lower(), ident))
    unauditable = dict(data.get("unauditable") or {})
    return accepted, unauditable, data


def run_pip_audit(rel, resolve_deps, root=REPO_ROOT):
    """Return (reported, error). `reported` is a set of (package, advisory id)."""
    cmd = [
        sys.executable, "-m", "pip_audit",
        "--requirement", rel,
        "--format", "json",
        "--progress-spinner", "off",
    ]
    if not resolve_deps:
        cmd.append("--no-deps")
    proc = subprocess.run(
        cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    try:
        payload = json.loads(proc.stdout)
    except ValueError:
        # No parsable report means no verdict, whatever the exit status was.
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return None, " / ".join(tail[-3:])[:600] or "pip-audit produced no report"
    reported = set()
    skipped = []
    for dep in payload.get("dependencies", []):
        if dep.get("skip_reason"):
            # The old single-file step passed `--strict`, which fails when
            # pip-audit cannot audit a dependency it resolved. Keeping that
            # guarantee matters more here than it did there: a closure where
            # one name was silently skipped is a partial verdict wearing a
            # clean one. Reported as an error so the file lands in NO VERDICT
            # rather than CLEAN.
            skipped.append("%s (%s)" % (dep.get("name"), dep["skip_reason"]))
            continue
        for vuln in dep.get("vulns", []):
            reported.add((dep["name"].lower(), vuln["id"]))
    if skipped:
        return None, "pip-audit skipped %d dependency/dependencies: %s" % (
            len(skipped), ", ".join(skipped[:5])
        )
    return reported, None


# Statuses. CLEAN/ACCEPTED pass; UNAUDITABLE passes but is reported on every
# run; NO_VERDICT and FINDINGS fail.
CLEAN = "CLEAN"
ACCEPTED = "ACCEPTED"
UNAUDITABLE = "UNAUDITABLE"
NO_VERDICT = "NO VERDICT"
FINDINGS = "FINDINGS"


def classify(rel, reported, error, accepted, unauditable):
    """Decide one file's outcome. Pure, so the rules are testable without pip.

    Returns (status, note, failure_or_None). The rule that matters is the
    second branch: a file with no verdict and no declaration FAILS, because a
    scanner that could not run must never look like a scanner that found
    nothing.
    """
    declared_unauditable = rel in unauditable

    if error is not None:
        if declared_unauditable:
            return UNAUDITABLE, unauditable[rel]["reason"], None
        return NO_VERDICT, error, (
            "%s: pip-audit could not resolve this file, so it has no advisory "
            "verdict. If that is expected on this runner, declare it under "
            "`unauditable` in %s with the measured reason. Do not let it pass "
            "as clean.\n    %s" % (rel, ACCEPTANCE_PATH, error)
        )

    if declared_unauditable:
        return CLEAN, "declared unauditable, but resolved", (
            "%s is declared `unauditable` in %s, but pip-audit resolved it on "
            "this runner. Remove the declaration so the file is audited for "
            "real." % (rel, ACCEPTANCE_PATH)
        )

    undeclared = sorted(reported - accepted.get(rel, set()))
    if undeclared:
        detail = ", ".join("%s %s" % (pkg, ident) for pkg, ident in undeclared)
        return FINDINGS, "%d undeclared" % len(undeclared), (
            "%s: %d undeclared advisory/advisories: %s\n    Fix the pin if a fix "
            "is installable on the interpreter this file serves. If it is not, "
            "declare it under `accepted_advisories` in %s with the measured "
            "reason, and write the long form in the pin file's header."
            % (rel, len(undeclared), detail, ACCEPTANCE_PATH)
        )
    if reported:
        return ACCEPTED, "%d declared, 0 new" % len(reported), None
    return CLEAN, "", None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--list", action="store_true",
        help="print the files this audit covers and exit, without auditing",
    )
    args = parser.parse_args()

    files = discover()
    accepted, unauditable, _ = load_acceptance()

    if args.list:
        for rel, resolve_deps in files:
            mode = "resolve-deps" if resolve_deps else "no-deps"
            print("%-56s %s" % (rel, mode))
        return 0

    failures = []
    rows = []

    for rel, resolve_deps in files:
        reported, error = run_pip_audit(rel, resolve_deps)
        status, note, failure = classify(
            rel, reported, error, accepted, unauditable
        )
        rows.append((status, rel, note))
        if failure:
            failures.append(failure)

    width = max(len(rel) for _, rel, _ in rows)
    print("Python dependency audit -- %d declared files\n" % len(rows))
    for status, rel, note in rows:
        print("  %-12s %-*s %s" % (status, width, rel, note))

    counts = {}
    for status, _, _ in rows:
        counts[status] = counts.get(status, 0) + 1
    print("\n" + "  ".join("%s=%d" % kv for kv in sorted(counts.items())))

    if failures:
        print("\n%d problem(s):\n" % len(failures))
        for failure in failures:
            print("  - %s\n" % failure)
        return 1

    print("\nEvery declared Python dependency file has a verdict.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
