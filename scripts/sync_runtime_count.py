#!/usr/bin/env python3
"""Keep advertised counts in sync with the entitlement catalogue.

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

The same script also checks the **chat-channel** count against
``ALL_CHANNELS``, which drifted the same way and for the same reason
(2026-09-05: ``ALL_CHANNELS`` had 23, CLAUDE.md / FLYWHEEL.md / AGENTS.md
said 21 and PRD.md said 22). That half is report-only, with its own
:data:`CHANNEL_EXEMPT`: the phrasing varies too much across surfaces
("21 chat channels", "21 chat-channel adapters") to rewrite unattended.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# "14 runtimes", "12 AI agent runtimes", "14+ runtimes", "20 agent runtimes".
COUNT_RE = re.compile(r"\b(\d{1,3})(\+?) ((?:AI )?(?:agent )?runtimes)\b")

# The same phrase with the line wrapped between the number and the noun.
# Hand-wrapped markdown does this constantly and the line-by-line scan below
# cannot see it: README.md carried "all 26\nruntimes" from 2026-08-25 (#5202)
# to 2026-09-05 while --check reported the count in sync at 30, and two
# translations inherited it. Applied to PROSE_SUFFIXES only,
# because in Python a newline between a number and the word `runtimes` is
# usually two unrelated statements ("open_count = 0\n    runtimes = ...").
WRAPPED_COUNT_RE = re.compile(
    r"\b(\d{1,3})(\+?)\n([ \t]*)((?:AI )?(?:agent )?runtimes)\b"
)
PROSE_SUFFIXES = {".md", ".html"}

# "21 chat channels", "21 chat-channel adapters". Same drift class as the
# runtime count, against clawmetry/entitlements.py:ALL_CHANNELS.
CHANNEL_COUNT_RE = re.compile(r"\b(\d{1,3}) chat[- ]channels?\b")

# Same shape as EXEMPT: counts that are legitimately not the catalogue size.
CHANNEL_EXEMPT: list[tuple[str, str, str]] = [
    ("routes/channels.py", "6 chat channels", "per-tier capacity example"),
    ("routes/entitlement.py", "6 chat channels", "per-tier capacity example"),
]

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

# The tagline names four runtimes and leaves the product names untranslated,
# so this string is on that line in all 35 locales and almost nowhere else.
# It is what keeps MORE_RE_I18N off unrelated prose.
TAGLINE_ANCHOR = "Codex"


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


def channel_count() -> int:
    """Chat-channel count, parsed (not imported) from entitlements.py.

    ``ALL_CHANNELS`` and ``sync._CHANNEL_DIRS`` are kept 1:1 by
    ``tests/test_entitlement_channel_catalog.py``; this reads the catalogue for
    the same reason :func:`catalogue_count` does, so the check runs without
    importing a module that pulls in Flask and DuckDB.
    """
    src = (REPO / "clawmetry" / "entitlements.py").read_text(encoding="utf-8")
    m = re.search(r"ALL_CHANNELS: tuple\[str, \.\.\.\] = \((.*?)\)", src, re.S)
    if not m:
        raise SystemExit("could not parse ALL_CHANNELS from entitlements.py")
    total = len(re.findall(r'"[a-z0-9_]+"', m.group(1)))
    if total < 2:
        raise SystemExit("parsed an implausible channel count from entitlements.py")
    return total


def check_channel_count(expected: int | None = None) -> list[tuple[str, int, str, str]]:
    """Return [(relpath, lineno, found, line)] for every stale channel count.

    Same failure as the runtime count, one catalogue over: CLAUDE.md,
    FLYWHEEL.md and AGENTS.md all said "21 chat-channel adapters" while
    ``ALL_CHANNELS`` had grown to 23. Markdown, HTML and Python are scanned;
    there is no fixer, because the phrasing varies too much to rewrite
    safely ("21 chat channels", "21 chat-channel adapters").
    """
    expected = channel_count() if expected is None else expected
    drift = []
    for path in _files():
        if path.suffix not in PROSE_SUFFIXES and path.suffix != ".py":
            continue
        rel = str(path.relative_to(REPO))
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            continue
        for n, line in enumerate(lines, 1):
            if any(
                rel.endswith(suffix) and needle in line
                for suffix, needle, _ in CHANNEL_EXEMPT
            ):
                continue
            for m in CHANNEL_COUNT_RE.finditer(line):
                if int(m.group(1)) != expected:
                    drift.append((rel, n, m.group(0), line.strip()))
    return drift


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

        if path.suffix in PROSE_SUFFIXES:
            text = "\n".join(lines)
            for m in WRAPPED_COUNT_RE.finditer(text):
                if int(m.group(1)) == expected:
                    continue
                n = text[: m.start()].count("\n") + 1
                if _is_exempt(rel, lines[n - 1]):
                    continue
                found = m.group(0).replace("\n", " ")
                drift.append((rel, n, found, lines[n - 1].strip()))
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
            # Only the tagline line. MORE_RE_I18N is loose by necessity (it
            # spans 35 languages), so on ordinary prose it fires on things
            # like "2 mais difíceis" -- pt-BR was reported stale for months
            # while its tagline was correct, which is how a warning stops
            # being read. TAGLINE_ANCHOR is untranslated in every locale.
            if TAGLINE_ANCHOR not in line:
                continue
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
        joined = "".join(out)
        if path.suffix in PROSE_SUFFIXES:

            def _rewrap(m, _text=joined):
                line = _text[: m.start()].rsplit("\n", 1)[-1] + m.group(0)
                if _is_exempt(rel, line):
                    return m.group(0)
                return f"{expected}{m.group(2)}\n{m.group(3)}{m.group(4)}"

            rewrapped = WRAPPED_COUNT_RE.sub(_rewrap, joined)
            changed |= rewrapped != joined
            joined = rewrapped
        if changed:
            path.write_text(joined, encoding="utf-8")
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

    channels = channel_count()

    def _report_channels() -> int:
        """Chat-channel drift. Reported, never rewritten: see the docstring."""
        stale = check_channel_count(channels)
        if not stale:
            print(f"chat-channel count in sync at {channels}")
            return 0
        print(f"\nchat-channel count drift (ALL_CHANNELS has {channels}):\n")
        for rel, n, found, line in stale:
            print(f"  {rel}:{n}: {found!r}\n      {line}")
        print(f"\n{len(stale)} stale mention(s). Edit the prose to say {channels}.")
        return 1

    if args.check:
        drift = check(expected)
        rc = 0
        if not drift:
            print(f"runtime count in sync at {expected} across every surface")
        else:
            print(f"runtime count drift (catalogue says {expected}):\n")
            for rel, n, found, line in drift:
                print(f"  {rel}:{n}: {found!r}\n      {line}")
            print(f"\n{len(drift)} stale mention(s). Fix with: python3 {Path(__file__).relative_to(REPO)}")
            rc = 1
        rc |= _report_channels()
        _report_translations()
        return rc

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
