"""User-facing copy carries no em-dashes or double-dashes (FLYWHEEL.md 1f3).

The rule is explicit, the user banned it directly, and FLYWHEEL records it as
burned twice before this. It was burned a third time on 2026-09-11: nine
CHANGELOG entries shipped to `main` with em-dashes in them, and 151 more sat in
older entries, because **nothing in CI checked**. A Drift Bot run noticed one,
by chance, days later.

FLYWHEEL even prescribes the remedy: "before sending any user-facing text ...
grep the payload for `-` or `--` and refuse to send if matched." This is that
grep, wired into a job so it runs whether or not anyone remembers.

Scope is deliberately CHANGELOG.md only. The rule covers more (landing copy,
banners, modal text), but those live in other repos or other formats; a guard
that tried to cover everything here would either be vacuous or fire on code.
One file, checked properly, beats a broad check nobody trusts.

NO EXEMPTIONS, including for quotations. An earlier version of this guard
skipped blockquote lines, on the reasoning that editing a user's words to
satisfy a style rule is worse than the violation. That framed a false binary
and put the guard at odds with the rule it enforces: FLYWHEEL bans these
characters in user-facing copy and carves out nothing for quotations, and a
published CHANGELOG entry is user-facing whoever wrote the sentence.

Standard editorial practice settles it. Punctuation inside a quote may be
adjusted as long as the reader can see it was, so the one entry that relied on
the exemption now reads "(punctuation normalised; wording verbatim)" and not a
word of what the founder said has changed.

The same reasoning covers describing a glyph: name it rather than print it.
"renders a dash placeholder" is true and clean; embedding the character in
order to be accurate is the same false binary.
"""
from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")

EM_DASH = "—"
#: `--` as prose, not `--flag`, `a--b`, or an HTML comment.
_DOUBLE_DASH = re.compile(r"(?<![-\w])--(?![-\w>])")

def _offending_lines():
    out = []
    with open(CHANGELOG, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if EM_DASH in line or _DOUBLE_DASH.search(line):
                out.append((n, line.rstrip()))
    return out


def test_the_changelog_exists():
    assert os.path.isfile(CHANGELOG), CHANGELOG


def test_no_em_dash_or_double_dash_in_the_changelog():
    bad = _offending_lines()
    if bad:
        shown = "\n".join(
            "  CHANGELOG.md:%d  %s" % (n, ln[:160]) for n, ln in bad[:12]
        )
        more = "" if len(bad) <= 12 else "\n  ... and %d more" % (len(bad) - 12)
        raise AssertionError(
            "%d CHANGELOG line(s) carry an em-dash or a double-dash, which "
            "FLYWHEEL.md 1f3 bans in user-facing copy:\n%s%s\n\n"
            "Use a comma, parenthetical, colon, or full stop. To describe the "
            "character itself, name it (\"a dash placeholder\") rather than "
            "printing it. Quoting someone is not an exemption: adjust the "
            "punctuation and say so, as in \"(punctuation normalised; wording "
            "verbatim)\"." % (len(bad), shown, more)
        )


def test_the_check_would_catch_a_violation():
    """Proving the guard goes RED rather than merely existing: the rule was
    burned three times precisely because nothing failed."""
    assert EM_DASH in "a sentence — with an em-dash"
    assert _DOUBLE_DASH.search("a sentence -- with a double dash")


def test_a_command_line_flag_is_not_a_double_dash_violation():
    """`--check` and `--update-baseline` appear all over these entries; a guard
    that flagged them would be turned off within a day."""
    assert not _DOUBLE_DASH.search("run `python3 scripts/x.py --check` first")
    assert not _DOUBLE_DASH.search("pass --update-baseline to ratchet down")


def test_a_blockquote_is_not_an_exemption():
    """The rule carves out nothing for quotations, so neither does this.

    An earlier version skipped blockquote lines and so disagreed with Drift Bot
    about the same file, which is worse than either answer alone.
    """
    import tempfile

    global CHANGELOG
    original = CHANGELOG
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False,
                                         encoding="utf-8") as fh:
            fh.write("> a quoted line with a double dash -- right here\n")
            fh.write("- A clean line with no banned punctuation.\n")
            CHANGELOG = fh.name
        bad = _offending_lines()
        assert [n for n, _ in bad] == [1], bad
    finally:
        CHANGELOG = original
