#!/usr/bin/env python3
"""Keep the advertised runtime count in sync with the entitlement catalogue.

``clawmetry/entitlements.py`` is the source of truth: the supported runtime
count is ``len(FREE_RUNTIMES | PAID_RUNTIMES)``. That number also appears in
prose across the README, its translations, FLYWHEEL.md, ARCHITECTURE.md, the
CLI, the desktop onboarding copy and the device page, and every one of those
drifted apart before this script existed (2026-08-15: README said 14, PyPI
said 12, FLYWHEEL said 12, the catalogue said 20).

Usage::

    python3 scripts/sync_runtime_count.py            # rewrite every surface
    python3 scripts/sync_runtime_count.py --check    # report drift, exit 1

``tests/test_runtime_count_copy_sync.py`` calls :func:`check` so CI fails on
drift, and ``setup.py`` derives the PyPI summary from the same catalogue so
that surface cannot go stale at all.

When a number here is legitimately *not* the supported-runtime count (a tier
bullet counting free runtimes, a dated changelog line, a capacity estimate),
add it to :data:`EXEMPT` with the reason rather than reshaping the prose.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# "14 runtimes", "12 AI agent runtimes", "14+ runtimes", "20 agent runtimes".
COUNT_RE = re.compile(r"\b(\d{1,3})(\+?) ((?:AI )?(?:agent )?runtimes)\b")

# Directories that legitimately carry historic or unrelated numbers.
SKIP_DIRS = {
    ".git", ".worktrees", "node_modules", "__pycache__", ".venv", "venv",
    "build", "dist", ".mypy_cache", ".pytest_cache", "tests",
}
SKIP_FILES = {
    "CHANGELOG.md",          # dated history, must keep the number of its day
    "sync_runtime_count.py",  # this file's own docstring
}
SCAN_SUFFIXES = {".py", ".md", ".html", ".js", ".json", ".sh", ".ps1", ".cmd", ".yml", ".yaml"}

# (path suffix, substring that must appear on the line) -> why it is not the
# supported-runtime count. Matched lines are left alone by both check and fix.
EXEMPT: list[tuple[str, str, str]] = [
    ("clawmetry/entitlements.py", "2 runtimes", "free-tier count, not the total"),
    ("clawmetry/entitlements.py", "4 runtimes", "per-tier capacity, not the total"),
    ("routes/entitlement.py", "2 runtimes", "free-tier count in the API fallback"),
    ("clawmetry/sync.py", "10 runtimes", "rollup sizing estimate, not the catalogue"),
    ("docs/WHAT_USERS_WANT.md", "18 runtimes total", "dated research note"),
    ("clawmetry/runtime_memory.py", "other 17 runtimes", "historic bug narrative, means all-but-one"),
]

# The English README pairs the count with "OpenClaw, NemoClaw, Claude Code,
# OpenAI Codex & N more", so N is the total minus the four named runtimes.
NAMED_IN_TAGLINE = 4
MORE_RE = re.compile(r"& \d{1,3} more\b")

# The same phrase exists in the translated READMEs, but the wording differs per
# language ("y 10 mas", "et 10 autres", "kai 10 akoma", ...) and a regex sweep
# across 35 locales would silently mangle the ones it half-matched. Those are
# reported by --check instead of rewritten, so a human updates them knowingly.
MORE_RE_I18N = re.compile(r"[^\s]{1,3} ?\d{1,3} ?(?:more|más|mais|autres|ακόμα|weitere|более|أخرى|अन्य)\b")


def catalogue_count() -> int:
    """Supported runtime count, parsed (not imported) from entitlements.py."""
    src = (REPO / "clawmetry" / "entitlements.py").read_text(encoding="utf-8")
    total = 0
    for block in (
        r"FREE_RUNTIMES = frozenset\(\{(.*?)\}\)",
        r"PAID_RUNTIMES = frozenset\(\s*\{(.*?)\}\s*\)",
    ):
        m = re.search(block, src, re.S)
        if not m:
            raise SystemExit(f"could not parse {block!r} from entitlements.py")
        total += len(re.findall(r'"[a-z0-9_]+"', m.group(1)))
    if total < 2:
        raise SystemExit("parsed an implausible runtime count from entitlements.py")
    return total


def _is_exempt(rel: str, line: str) -> bool:
    return any(rel.endswith(path) and needle in line for path, needle, _ in EXEMPT)


def _files() -> list[Path]:
    out = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.suffix not in SCAN_SUFFIXES:
            continue
        if p.name in SKIP_FILES or SKIP_DIRS & set(p.relative_to(REPO).parts):
            continue
        out.append(p)
    return sorted(out)


def check(expected: int | None = None) -> list[tuple[str, int, str, str]]:
    """Return [(relpath, lineno, found, line)] for every stale count."""
    expected = catalogue_count() if expected is None else expected
    drift = []
    for path in _files():
        rel = str(path.relative_to(REPO))
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(lines, 1):
            if _is_exempt(rel, line):
                continue
            for m in COUNT_RE.finditer(line):
                if int(m.group(1)) != expected:
                    drift.append((rel, n, m.group(0), line.strip()))
            if rel == "README.md":
                for m in MORE_RE.finditer(line):
                    if m.group(0) != f"& {expected - NAMED_IN_TAGLINE} more":
                        drift.append((rel, n, m.group(0), line.strip()))
    return drift


def check_translated_taglines(expected: int | None = None) -> list[tuple[str, int, str]]:
    """Report "and N more" phrases in translated READMEs for manual review.

    Not part of :func:`check` because these are never rewritten automatically
    (see :data:`MORE_RE_I18N`), so failing CI on them would block every runtime
    addition on 35 translations.
    """
    expected = catalogue_count() if expected is None else expected
    want = expected - NAMED_IN_TAGLINE
    stale = []
    for path in sorted((REPO / "docs" / "i18n").rglob("README.md")):
        rel = str(path.relative_to(REPO))
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for m in MORE_RE_I18N.finditer(line):
                if str(want) not in m.group(0):
                    stale.append((rel, n, m.group(0).strip()))
    return stale


def fix(expected: int | None = None) -> list[str]:
    """Rewrite every stale count in place. Returns the paths touched."""
    expected = catalogue_count() if expected is None else expected
    touched = []
    for path in _files():
        rel = str(path.relative_to(REPO))
        try:
            original = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        out = []
        changed = False
        for line in original.splitlines(keepends=True):
            if _is_exempt(rel, line):
                out.append(line)
                continue
            new = COUNT_RE.sub(lambda m: f"{expected}{m.group(2)} {m.group(3)}", line)
            if rel == "README.md":
                new = MORE_RE.sub(f"& {expected - NAMED_IN_TAGLINE} more", new)
            changed |= new != line
            out.append(new)
        if changed:
            path.write_text("".join(out), encoding="utf-8")
            touched.append(rel)
    return touched


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="report drift, do not rewrite")
    args = ap.parse_args()

    expected = catalogue_count()

    def _report_translations() -> None:
        stale = check_translated_taglines(expected)
        if stale:
            print(f"\nnote: {len(stale)} translated tagline(s) still say the old "
                  f"'and N more' (want {expected - NAMED_IN_TAGLINE}); these are "
                  "never rewritten automatically:")
            for rel, n, found in stale:
                print(f"  {rel}:{n}: {found}")

    if args.check:
        drift = check(expected)
        if not drift:
            print(f"runtime count in sync at {expected} across every surface")
            _report_translations()
            return 0
        print(f"runtime count drift (catalogue says {expected}):\n")
        for rel, n, found, line in drift:
            print(f"  {rel}:{n}: {found!r}\n      {line}")
        print(f"\n{len(drift)} stale mention(s). Fix with: python3 {Path(__file__).relative_to(REPO)}")
        _report_translations()
        return 1

    touched = fix(expected)
    if not touched:
        print(f"runtime count already in sync at {expected}")
    else:
        print(f"rewrote {len(touched)} file(s) to {expected} runtimes:")
        for rel in touched:
            print(f"  {rel}")
    _report_translations()
    return 0


if __name__ == "__main__":
    sys.exit(main())
