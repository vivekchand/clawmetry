#!/usr/bin/env python3
"""Find bandit `# nosec` comments that suppress EVERY test on their line.

Why this exists
---------------
`# nosec B608 - reason` suppresses only B608. A `# nosec` that resolves to no
test id at all suppresses every bandit test on that line. Bandit treats an
empty id set as "silence everything here" (`bandit.core.manager`.
`_parse_nosec_comment` returns an empty set, and the tester reads that as a
blanket skip), so the two forms look nearly identical in review and behave
completely differently.

The trap is that prose can become a directive. Bandit matches `#\\s*nosec`
anywhere in a comment, then reads whatever follows as test ids. A comment that
merely *mentions* `# nosec` while explaining something therefore turns into a
blanket suppression, and bandit reports nothing on that line ever again. That
is the same failure this workflow already gates on elsewhere: bandit ran, so
the report is not an outage, but on that one line "found nothing" is
indistinguishable from "never looked".

Bandit cannot report this itself -- a suppression is invisible to the thing it
suppresses -- which is why it is checked here.

The verdict is bandit's own: this imports bandit's regexes and its extension
manager rather than reimplementing the parse, so the two cannot drift.

Exit codes
----------
0  no blanket suppressions
1  at least one blanket suppression (a finding)
2  the check could not run -- an unknown result, not a clean one
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys
import tokenize

# Bandit's own exclusion list for this repo's scan, kept in step with the
# `-x` flag in .github/workflows/supply-chain.yml. A blanket nosec inside a
# directory bandit never scans suppresses nothing.
DEFAULT_EXCLUDES = "./node_modules,./.venv,./venv,./tests,./frontend,./.git"
# Directories that are never source for this purpose, excluded regardless.
ALWAYS_SKIP = {".git", "__pycache__", ".tox", ".mypy_cache", ".pytest_cache", "dist", "build"}


def _norm(root: str, raw: str) -> str:
    """Normalise one exclusion entry to an absolute path."""
    return os.path.normpath(os.path.join(root, raw.strip().lstrip("./")))


def find_blanket(root: str, excludes: list[str]) -> list[dict]:
    """Return every nosec comment under `root` that resolves to zero test ids."""
    # Imported here so an import failure is reported as "could not run"
    # (exit 2) rather than a traceback that reads like a clean scan.
    from bandit.core import extension_loader
    from bandit.core.manager import NOSEC_COMMENT, NOSEC_COMMENT_TESTS

    extman = extension_loader.MANAGER
    excluded = {_norm(root, e) for e in excludes if e.strip()}
    findings: list[dict] = []

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d
            for d in dirnames
            if d not in ALWAYS_SKIP
            and os.path.normpath(os.path.join(dirpath, d)) not in excluded
        ]
        for filename in sorted(filenames):
            if not filename.endswith(".py"):
                continue
            path = os.path.join(dirpath, filename)
            if os.path.normpath(path) in excluded:
                continue
            try:
                data = open(path, "rb").read()
                tokens = list(tokenize.tokenize(io.BytesIO(data).readline))
            except (OSError, tokenize.TokenError, SyntaxError, UnicodeDecodeError):
                # Unparseable source is bandit's problem to report, not this
                # check's: bandit cannot apply a nosec it cannot tokenize.
                continue

            for token in tokens:
                if token.type != tokenize.COMMENT:
                    continue
                match = NOSEC_COMMENT.search(token.string)
                if not match:
                    continue
                raw_tests = match.groupdict().get("tests")
                ids = set()
                if raw_tests:
                    for candidate in NOSEC_COMMENT_TESTS.finditer(raw_tests):
                        name = candidate.group(1)
                        if extman.check_id(name):
                            ids.add(name)
                        else:
                            resolved = extman.get_test_id(name)
                            if resolved:
                                ids.add(resolved)
                if ids:
                    continue  # scoped to named tests -- this is the correct form
                findings.append(
                    {
                        "path": os.path.relpath(path, root),
                        "line": token.start[0],
                        "comment": token.string.strip(),
                    }
                )
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="tree to scan (default: cwd)")
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDES,
        help="comma-separated paths to skip; mirrors bandit's -x",
    )
    parser.add_argument("--json", dest="json_out", help="write findings as JSON here")
    args = parser.parse_args(argv)

    try:
        findings = find_blanket(args.root, args.exclude.split(","))
    except Exception as exc:  # noqa: BLE001 -- any failure is "unknown", not "clean"
        print(f"check-blanket-nosec: could not run: {exc!r}", file=sys.stderr)
        return 2

    if args.json_out:
        try:
            os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
            with open(args.json_out, "w", encoding="utf-8") as handle:
                json.dump({"findings": findings}, handle, indent=2, sort_keys=True)
        except OSError as exc:
            print(f"check-blanket-nosec: could not write JSON: {exc!r}", file=sys.stderr)
            return 2

    if not findings:
        print("check-blanket-nosec: no blanket nosec suppressions.")
        return 0

    print(
        f"check-blanket-nosec: {len(findings)} nosec comment(s) suppress every "
        f"bandit test on their line:"
    )
    for finding in findings:
        print(f"  {finding['path']}:{finding['line']}")
        print(f"      {finding['comment']}")
    print(
        "\nName the tests being waived (`# nosec B608 - reason`). If the comment "
        "is prose that only mentions nosec, drop the `#` before the word so it "
        "stops parsing as a directive."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
