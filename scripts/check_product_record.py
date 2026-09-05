#!/usr/bin/env python3
"""Every code change cites the product record that justified it.

FLYWHEEL.md section 0c: 8090 Software Factory is the product reviewer. The
requirement is where a change is justified, the blueprint is where it is
designed, the code is where it is built -- in that order. This makes the
first half checkable.

Burned 2026-08-25: four Observe-pillar changes were implemented first and the
Factory records written afterwards to turn drift-bot green. Six rounds
produced accurate mechanism and zero product context, and three defects a
reviewer would have caught went in with them -- a one-click irreversible data
delete with no confirmation among them. Nothing in CI noticed, because
nothing was looking.

A PR passes when its body EITHER cites a Factory record:

    https://factory.8090.ai/project/<uuid>/requirements/<uuid>
    https://factory.8090.ai/project/<uuid>/blueprints/<uuid>

or opts out ON PURPOSE, with a reason on the same line:

    No-PRD: typo in a log string
    No-PRD: revert of #1234

Docs-only, test-only and CI-only changes skip the check entirely -- writing
the record must not itself be gated on citing one. So do dependency
manifests and lockfiles: a version bump is justified by the advisory, not by
a requirement written first, and Dependabot cannot type an opt-out line.

Deliberately NOT a taste check. It cannot tell a real requirement from a
stub, and pretending otherwise would be theatre. What it does is make
"implement now, document later" require typing a sentence that says so, in a
place a human reads.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

FACTORY_LINK = re.compile(
    r"factory\.8090\.ai/project/[0-9a-f-]{8,}/"
    r"(requirements|blueprints)/[0-9a-f-]{8,}",
    re.I,
)
# Reason required: a bare "No-PRD:" is not an opt-out, it is a shrug.
OPT_OUT = re.compile(r"^\s*No-PRD:\s*(?P<reason>\S.*)$", re.I | re.M)

#: Paths that never need a product record. Everything else does.
EXEMPT_PREFIXES = (
    "docs/",
    ".github/",
    "scripts/",
    "tests/",
    "CHANGELOG.md",
    "README.md",
    "AGENTS.md",
    "CLAUDE.md",
    "FLYWHEEL.md",
)
EXEMPT_SUFFIXES = (".md", ".txt")

#: Dependency manifests and lockfiles, matched on the FULL basename so that
#: `mypackage.json` still needs a record.
#:
#: A version bump is a supply-chain change, not a product decision: what
#: justifies it is the advisory or the upstream release, and there is no
#: requirement to write first. The pip half of this was already true by
#: accident -- `requirements*.txt` is exempt via EXEMPT_SUFFIXES above -- so
#: pip Dependabot PRs have always merged while npm ones could not, and the
#: asymmetry was extension trivia rather than anybody's decision.
#:
#: What that cost: every npm advisory fix on this repo sat behind a gate it
#: had no way to satisfy. Dependabot does not write `No-PRD:` into a PR body
#: and cannot be configured to, so #5241/#5244/#5376 and their siblings were
#: unmergeable from the moment they opened -- one of them carrying a fix
#: rated high severity. A gate that blocks the security updates it was never
#: aimed at is a gate people route around.
#:
#: `package.json` is here alongside the lockfiles even though it also holds
#: `scripts`. That is consistent rather than a hole: `scripts/` and
#: `.github/` are already exempt, so build tooling sits outside this gate by
#: design, and `package.json` is the npm face of the same thing. A change
#: that IS a product decision still has `No-PRD:` to answer to.
EXEMPT_BASENAMES = (
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "yarn.lock",
    "pnpm-lock.yaml",
)


def changed_files(base: str, head: str) -> list[str]:
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            text=True, stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def needs_record(paths: list[str]) -> list[str]:
    """The changed paths that are product-visible code."""
    out = []
    for p in paths:
        if p.startswith(EXEMPT_PREFIXES) or p.endswith(EXEMPT_SUFFIXES):
            continue
        # Basename equality, not a suffix test: `frontend/package.json` is a
        # manifest, `mypackage.json` is a data file somebody wrote.
        if p.rsplit("/", 1)[-1] in EXEMPT_BASENAMES:
            continue
        out.append(p)
    return out


def main() -> int:
    body = os.environ.get("PR_BODY", "") or ""
    base = os.environ.get("BASE_SHA") or "origin/main"
    head = os.environ.get("HEAD_SHA") or "HEAD"

    code = needs_record(changed_files(base, head))
    if not code:
        print("product-record gate OK - no product-visible code changed")
        return 0

    if FACTORY_LINK.search(body):
        print("product-record gate OK - cites a Factory record "
              f"({len(code)} code file(s) changed)")
        return 0

    m = OPT_OUT.search(body)
    if m:
        print("product-record gate OK - explicit opt-out: "
              f"{m.group('reason').strip()[:120]}")
        return 0

    shown = "\n".join("    " + p for p in code[:12])
    more = f"\n    ... and {len(code) - 12} more" if len(code) > 12 else ""
    print(
        "product-record gate FAILED\n"
        "\n"
        f"This PR changes {len(code)} product-visible file(s):\n"
        f"{shown}{more}\n"
        "\n"
        "FLYWHEEL.md section 0c: 8090 Software Factory is the product reviewer,\n"
        "and a requirement written after the fact reviews nothing. Write the\n"
        "record FIRST - problem, who is hurt, non-goals, alternatives rejected,\n"
        "risk accepted - then link it in the PR body:\n"
        "\n"
        "    https://factory.8090.ai/project/<uuid>/requirements/<uuid>\n"
        "\n"
        "If this change genuinely does not need one, say so on purpose:\n"
        "\n"
        "    No-PRD: <one line saying why>\n"
        "\n"
        "Both are one line. The point is that skipping the review is a\n"
        "decision somebody typed, not a step that quietly did not happen.",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
