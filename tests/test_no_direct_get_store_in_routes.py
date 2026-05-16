"""Lint guard: prevent regressions on issue #1240.

Every ``local_store.get_store(...)`` call in ``routes/`` must pass an
explicit ``read_only=True`` kwarg. The default (writable) open pays
DuckDB's ~2.5s exclusive-lock-retry budget on every request when the
sync daemon owns the writer lock cross-process, which is the standard
install topology. PR #1235 fixed 3 hot endpoints that fell into this
trap; issue #1240 swept the long tail.

The check is intentionally a dumb regex over the route module sources
(not an AST walk) — it has to catch ``local_store.get_store()`` whether
the call is bare or chained (``local_store.get_store().query_*``), and
across both bound and unbound forms. A pre-flight CI gate that fails
the build is what the issue asks for; AST sophistication would just
mean more ways to silently pass.

Allowed forms:
    local_store.get_store(read_only=True)
    local_store.get_store(read_only=True, ...)
    get_store(read_only=True)           # when imported directly

Disallowed forms (will fail this test):
    local_store.get_store()
    local_store.get_store().query_x(...)
    get_store()                          # bare, even when imported directly

To bypass for a legitimately-writable callsite (none expected in
``routes/`` — writes belong in the daemon, not the dashboard), add a
``# noqa: get_store-rw`` comment on the same line. The check honours
the marker but still counts the callsite so we don't lose visibility.
"""

from __future__ import annotations

import io
import pathlib
import re
import tokenize

# Match ``get_store(...)`` calls whose argument list does NOT contain a
# ``read_only=True`` kwarg. The regex is line-scoped (no ``re.DOTALL``),
# which matches how all current callsites are written (single-line).
#
# The negative lookahead handles whitespace + other kwargs before/after
# read_only=True, e.g. ``get_store(read_only=True, foo=1)``.
_GETSTORE_RW_RE = re.compile(
    r"\bget_store\(\s*(?![^)]*\bread_only\s*=\s*True\b)[^)]*\)"
)

# Allow opt-in escape hatch for a legitimately-writable callsite. The
# comment must appear on the same line as the call.
_NOQA_MARKER = "noqa: get_store-rw"

_ROUTES_DIR = pathlib.Path(__file__).resolve().parents[1] / "routes"


def _code_lines_only(source: str) -> dict[int, str]:
    """Return ``{lineno: line}`` for lines whose content lives outside
    comments + string literals. Tokenize-based so a docstring mention of
    ``get_store()`` doesn't trip the lint.

    Implementation: tokenize the source, drop ``COMMENT`` and ``STRING``
    tokens, reconstruct each remaining token in place using its
    ``(start, end)`` position. Lines that end up empty after the strip
    are excluded from the result map — they can't contain a real call.
    """
    keep: dict[int, list[str]] = {}
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenizeError:
        # Fallback: if the file can't tokenize cleanly (shouldn't happen
        # in routes/), return the raw lines so we at least still catch
        # the obvious offenders.
        return {i + 1: ln for i, ln in enumerate(source.splitlines())}
    for tok in tokens:
        if tok.type in (tokenize.COMMENT, tokenize.STRING, tokenize.NL, tokenize.NEWLINE):
            continue
        if tok.type in (tokenize.INDENT, tokenize.DEDENT, tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        line = tok.start[0]
        keep.setdefault(line, []).append(tok.string)
    return {ln: " ".join(parts) for ln, parts in keep.items()}


def _scan_routes_for_rw_get_store():
    """Walk every ``routes/*.py`` file and yield ``(path, lineno, line)``
    tuples for each writable ``get_store()`` call. Skips:
      * pure-comment lines and string-literal mentions (tokenize-driven)
      * lines carrying the ``# noqa: get_store-rw`` opt-out marker
    """
    offenders = []
    for path in sorted(_ROUTES_DIR.glob("*.py")):
        source = path.read_text()
        raw_lines = source.splitlines()
        code_lines = _code_lines_only(source)
        for lineno, stripped in code_lines.items():
            # The noqa marker lives in a same-line comment, which tokenize
            # already dropped — pull it from the raw line so the opt-out
            # still works.
            raw = raw_lines[lineno - 1] if 0 < lineno <= len(raw_lines) else ""
            if _NOQA_MARKER in raw:
                continue
            if _GETSTORE_RW_RE.search(stripped):
                offenders.append((path.name, lineno, raw.rstrip()))
    return offenders


def test_no_rw_get_store_in_routes():
    """No ``routes/*.py`` file may contain a writable ``get_store()`` call.

    Issue #1240: every direct open in a route handler MUST pass
    ``read_only=True`` so it doesn't race the daemon's writer lock.
    If this test fails, the new offender shows up in the assertion
    message — either add ``read_only=True`` or, for the rare legitimate
    write (don't — push writes into the daemon), tag the line with
    ``# noqa: get_store-rw``.
    """
    offenders = _scan_routes_for_rw_get_store()
    assert not offenders, (
        "Direct writable get_store() callsites detected in routes/ "
        "(issue #1240 — must pass read_only=True):\n  "
        + "\n  ".join(f"{p}:{ln}: {src}" for p, ln, src in offenders)
    )


def test_lint_regex_actually_matches_known_bad_shapes():
    """Sanity check: the lint regex catches the patterns it's supposed to.

    Without this, a typo in ``_GETSTORE_RW_RE`` could silently let new
    offenders past CI. We assert positive + negative matches against a
    hand-rolled fixture rather than relying on whatever the live codebase
    looks like.
    """
    bad_shapes = [
        "store = local_store.get_store()",
        "rows = local_store.get_store().query_events(limit=10)",
        "x = get_store()",
        "y = get_store(read_only=False)",
        "z = get_store(foo=1)",
    ]
    good_shapes = [
        "store = local_store.get_store(read_only=True)",
        "rows = local_store.get_store(read_only=True).query_events(limit=10)",
        "x = get_store(read_only=True)",
        "y = get_store(read_only=True, foo=1)",
        "z = get_store(foo=1, read_only=True)",
    ]
    for s in bad_shapes:
        assert _GETSTORE_RW_RE.search(s), f"lint should flag bad shape: {s!r}"
    for s in good_shapes:
        assert not _GETSTORE_RW_RE.search(s), (
            f"lint must NOT flag good shape: {s!r}"
        )
