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

It also writes **SUPPORTED_RUNTIMES.txt** at the repo root: the one
machine-readable export of the catalogue (id, label, tier, landing path,
plus the derived count and the canonical one-line blurb). That file is what
every *other* repo reads — clawmetry-pro, clawmetry-cloud and
clawmetry-landing each fetch it by raw URL instead of keeping their own
hand-typed list, which is how they ended up quoting 22, 14 and 12 runtimes
respectively while this repo said 30. It is generated, never hand-edited;
``--check`` fails when it is stale.

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
    ("clawmetry/entitlements.py", '"& 26 more" next to "30 runtimes"',
     "historic bug narrative: what the README ACTUALLY said before the "
     "marquee existed. Rewriting the 30 makes the sentence describe a state "
     "that never happened, which is worse than a stale number"),
    (".github/workflows/sync-github-about.yml", "26 AI agent runtimes",
     "quotes the stale blurb that workflow exists to prevent"),
]

# The English README pairs the count with the marquee names and "& N more",
# so N is the total minus however many names the marquee prints. Derived
# rather than typed: it was a literal 4 while the marquee grew, which is the
# same class of bug one layer down.
MORE_RE = re.compile(r"& \d{1,3} more\b")

# The generated export every other repo reads. See :func:`render_export`.
EXPORT_PATH = REPO / "SUPPORTED_RUNTIMES.txt"
EXPORT_RAW_URL = (
    "https://raw.githubusercontent.com/vivekchand/clawmetry/main/SUPPORTED_RUNTIMES.txt"
)

# GitHub caps a repository description at 350 characters, and silently
# truncates past it. The blurb is asserted under this by
# tests/test_supported_runtimes_file.py so a long runtime name cannot quietly
# cut the sentence in half on the repo page.
GITHUB_ABOUT_LIMIT = 350

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


def _entitlements_src() -> str:
    return (REPO / "clawmetry" / "entitlements.py").read_text(encoding="utf-8")


def _parse_block(src: str, pattern: str, what: str) -> str:
    m = re.search(pattern, src, re.S)
    if not m:
        raise SystemExit(f"could not parse {what} from entitlements.py")
    return m.group(1)


def catalogue() -> list[dict[str, str]]:
    """The full runtime catalogue, parsed (not imported) from entitlements.py.

    Parsed for the same reason :func:`catalogue_count` is: ``setup.py`` runs
    this before the package is importable, and importing ``entitlements``
    drags in nothing heavy today but has no guarantee not to tomorrow.

    Rows are sorted free-first, then by id, so the generated file has a
    stable diff — a new runtime shows up as one added line, not a reshuffle.
    """
    src = _entitlements_src()
    free = re.findall(
        r'"([a-z0-9_]+)"',
        _parse_block(src, r"FREE_RUNTIMES = frozenset\(\{(.*?)\}\)", "FREE_RUNTIMES"),
    )
    paid = re.findall(
        r'"([a-z0-9_]+)"',
        _parse_block(
            src, r"PAID_RUNTIMES = frozenset\(\s*\{(.*?)\}\s*\)", "PAID_RUNTIMES"
        ),
    )
    labels = dict(
        re.findall(
            r'"([a-z0-9_]+)": "([^"]+)"',
            _parse_block(src, r"RUNTIME_LABELS = \{(.*?)\n\}", "RUNTIME_LABELS"),
        )
    )
    paths = dict(
        re.findall(
            r'"([a-z0-9_]+)": "(/[^"]+)"',
            _parse_block(
                src, r"RUNTIME_LANDING_PATHS = \{(.*?)\n\}", "RUNTIME_LANDING_PATHS"
            ),
        )
    )
    rows = []
    for tier, ids in (("free", free), ("paid", paid)):
        for rid in sorted(ids):
            missing = [
                name
                for name, table in (("RUNTIME_LABELS", labels), ("RUNTIME_LANDING_PATHS", paths))
                if rid not in table
            ]
            if missing:
                raise SystemExit(f"runtime {rid!r} is missing from {', '.join(missing)}")
            rows.append(
                {"id": rid, "label": labels[rid], "tier": tier, "path": paths[rid]}
            )
    if len(rows) < 2:
        raise SystemExit("parsed an implausible catalogue from entitlements.py")
    return rows


def marquee() -> list[str]:
    """Runtime ids named by name in short copy (RUNTIME_MARQUEE)."""
    src = _entitlements_src()
    ids = re.findall(
        r'"([a-z0-9_]+)"',
        _parse_block(
            src, r"RUNTIME_MARQUEE: tuple\[str, \.\.\.\] = \((.*?)\)", "RUNTIME_MARQUEE"
        ),
    )
    if not ids:
        raise SystemExit("RUNTIME_MARQUEE parsed empty")
    return ids


def blurb(rows: list[dict[str, str]] | None = None) -> str:
    """The canonical one-line product description.

    This exact string is the GitHub repository "About" text, the PyPI
    summary and the landing meta description. It said "26 AI agent
    runtimes" on GitHub for weeks after the catalogue reached 30, because
    a repo description is *metadata* — no file, no diff, no CI. Now it is
    derived here and pushed by ``.github/workflows/sync-github-about.yml``.
    """
    rows = catalogue() if rows is None else rows
    labels = {r["id"]: r["label"] for r in rows}
    named = [labels[rid] for rid in marquee() if rid in labels]
    # NemoClaw is "NVIDIA NemoClaw" and Codex is "OpenAI Codex" in copy aimed
    # at people who have not heard of either; the catalogue label is the
    # in-product one, which is shorter.
    vendor = {"NemoClaw": "NVIDIA NemoClaw", "Codex": "OpenAI Codex"}
    named = [vendor.get(n, n) for n in named]
    return (
        "See your agent think. Zero-config observability & governance for "
        f"{len(rows)} AI agent runtimes: {', '.join(named)} & {len(rows) - len(named)} "
        "more. Live token costs, sessions, tool calls, crons."
    )


def render_export(rows: list[dict[str, str]] | None = None) -> str:
    """Render SUPPORTED_RUNTIMES.txt.

    Grammar, kept boring on purpose so a five-line parser in any language
    can read it (clawmetry-cloud parses it in Python, clawmetry-landing in
    node):

    * ``#`` comment lines and blank lines are ignored.
    * A line with no TAB is metadata: ``KEY = value``.
    * A line with TABs is a runtime: ``id<TAB>label<TAB>tier<TAB>path``.

    ``COUNT`` is written out even though it equals the number of runtime
    rows, because the consumers that only want the number should not have
    to parse the rows to get it.
    """
    rows = catalogue() if rows is None else rows
    free = [r for r in rows if r["tier"] == "free"]
    paid = [r for r in rows if r["tier"] == "paid"]
    out = [
        "# ClawMetry — the supported agent runtimes, and nothing else.",
        "#",
        "# GENERATED FILE — do not edit by hand; your edit will be overwritten.",
        "#",
        "# Source of truth:  clawmetry/entitlements.py",
        "#                   (FREE_RUNTIMES, PAID_RUNTIMES, RUNTIME_LABELS,",
        "#                    RUNTIME_LANDING_PATHS, RUNTIME_MARQUEE)",
        "# Regenerate:       python3 scripts/sync_runtime_count.py",
        "# Verify:           python3 scripts/sync_runtime_count.py --check",
        "#",
        "# Every other ClawMetry repo (clawmetry-pro, clawmetry-cloud,",
        "# clawmetry-landing) reads THIS file rather than keeping its own list.",
        "# Fetch it at:",
        f"#   {EXPORT_RAW_URL}",
        "#",
        "# Format",
        "# ------",
        "#   '#' comment, blank line          -> ignore",
        "#   line with no TAB                 -> metadata, 'KEY = value'",
        "#   line with TABs                   -> id <TAB> label <TAB> tier <TAB> landing_path",
        "#",
        "# 'tier' is 'free' (readable by the OSS package alone) or 'paid'",
        "# (read by the closed-source clawmetry-pro companion). 'landing_path'",
        "# is relative to https://clawmetry.com.",
        "",
        f"COUNT = {len(rows)}",
        f"FREE_COUNT = {len(free)}",
        f"PAID_COUNT = {len(paid)}",
        f"BLURB = {blurb(rows)}",
        "",
    ]
    for r in rows:
        out.append("\t".join((r["id"], r["label"], r["tier"], r["path"])))
    return "\n".join(out) + "\n"


def parse_export(text: str) -> tuple[dict[str, str], list[dict[str, str]]]:
    """Reference parser for SUPPORTED_RUNTIMES.txt — (metadata, runtimes).

    Lives here so the grammar has an executable definition the other repos
    can copy, and so the round-trip is testable.
    """
    meta: dict[str, str] = {}
    rows: list[dict[str, str]] = []
    for line in text.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line:
            rid, label, tier, path = line.split("\t")
            rows.append({"id": rid, "label": label, "tier": tier, "path": path})
        else:
            key, _, value = line.partition("=")
            meta[key.strip()] = value.strip()
    return meta, rows


def check_export() -> str | None:
    """Return an explanation if SUPPORTED_RUNTIMES.txt is stale, else None."""
    want = render_export()
    if not EXPORT_PATH.exists():
        return "SUPPORTED_RUNTIMES.txt is missing"
    have = EXPORT_PATH.read_text(encoding="utf-8")
    if have == want:
        return None
    _, have_rows = parse_export(have)
    _, want_rows = parse_export(want)
    have_ids = {r["id"] for r in have_rows}
    want_ids = {r["id"] for r in want_rows}
    added = sorted(want_ids - have_ids)
    removed = sorted(have_ids - want_ids)
    detail = []
    if added:
        detail.append(f"catalogue adds {added}")
    if removed:
        detail.append(f"catalogue drops {removed}")
    if not detail:
        detail.append("labels, tiers, paths or the blurb changed")
    return "SUPPORTED_RUNTIMES.txt is stale: " + "; ".join(detail)


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
                    if m.group(0) != f"& {expected - len(marquee())} more":
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
    want = expected - len(marquee())
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
                new = MORE_RE.sub(f"& {expected - len(marquee())} more", new)
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
    ap.add_argument(
        "--about",
        action="store_true",
        help="print the canonical one-line blurb (GitHub About / PyPI summary) and exit",
    )
    args = ap.parse_args()

    if args.about:
        print(blurb())
        return 0

    expected = catalogue_count()

    def _report_translations() -> None:
        stale = check_translated_taglines(expected)
        if stale:
            print(f"\nnote: {len(stale)} translated tagline(s) still say the old "
                  f"'and N more' (want {expected - len(marquee())}); these are "
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
        stale_export = check_export()
        if stale_export:
            print(f"\n{stale_export}\n  regenerate with: python3 "
                  f"{Path(__file__).relative_to(REPO)}")
            rc = 1
        else:
            print(f"SUPPORTED_RUNTIMES.txt in sync at {expected} runtimes")
        rc |= _report_channels()
        _report_translations()
        return rc

    if check_export():
        EXPORT_PATH.write_text(render_export(), encoding="utf-8")
        print(f"wrote {EXPORT_PATH.relative_to(REPO)} ({expected} runtimes)")

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
