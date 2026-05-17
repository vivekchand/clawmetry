"""MOAT bug-class gate: ban v3-shape silent-zero filter (refs #1582).

Prevents regression of the bug family that hit 6 surfaces on 2026-05-17:
``/api/token-attribution`` (#1583), ``/api/usage/forecast`` (#1571),
``/api/cost-optimizer`` (#1576), ``/api/automation-analysis`` (#1580),
plus the two bonus finds called out in #1582.

The shape of the bug
====================

OpenClaw v3's daemon (``clawmetry/sync.py::_parse_v3_event``) normalises
events into a v3 namespace before writing to DuckDB::

    pre-v3 shape          v3 daemon shape
    --------------        ---------------
    type='message'   →    event_type in {'assistant','model.completed','prompt.submitted','user'}
    type='user'      →    event_type='prompt.submitted' or 'user'
    type='assistant' →    event_type='assistant' or 'model.completed'

Any code that filters DuckDB rows with ``event_type == 'message'``
silently matches ZERO events on a real v3 install. The endpoint returns
``messages: []`` / ``cost: $0`` / ``patterns: []`` — looks like a healthy
empty state, but is really a silent miscount. Synthetic tests pass
because the test fixtures still use the pre-v3 ``type='message'`` shape
(see ``feedback_synthetic_tests_missed_real_event_shape.md``).

What this gate enforces
=======================

For every ``routes/*.py`` file we walk every line of executable code
(tokenize-driven so docstrings + comments don't trip) and flag any
equality check against the pre-v3 event-type names (``"message"``,
``"user"``, ``"assistant"``) that uses an event-type variable. The
forbidden shapes are::

    # Pattern A — dict access on the event envelope
    ev.get("type") == "message"
    ev["type"] == "message"
    obj.get("type") == "message"
    obj["type"] == "message"
    r.get("event_type") == "message"
    event.get("type") == "message"
    row.get("event_type") == "message"

    # Pattern B — variable equality, where the LHS name signals event-type
    event_type == "message"
    etype       == "message"
    ev_type     == "message"
    obj_type    == "message"
    kind        == "message"
    et          == "message"

    # Pattern C — SQL literal
    "WHERE event_type = 'message'"
    "WHERE type = 'message'"

How to legitimately use a pre-v3 name
=====================================

Some callsites legitimately need to match the pre-v3 shape — JSONL
fallback walkers reading the on-disk transcript format (which IS still
the pre-v3 shape per ``~/.openclaw/agents/main/sessions/*.jsonl``), or
defensive code that handles BOTH v3 and legacy in the same function.

To bypass the gate, tag the offending line with the inline marker::

    if etype == "message":   # v3-shape-gate: allow (reason: JSONL walker; on-disk shape is pre-v3)

The marker MUST appear on the same source line and MUST include a
``reason: …`` justification. A bare ``# v3-shape-gate: allow`` (no
reason) is rejected — the requirement is to force the next agent to
think about whether the new callsite is reading from JSONL (allowed) or
from DuckDB (the bug).

Historical fixes that motivated this gate
=========================================

Six surfaces shipped GREEN through synthetic tests on 2026-05-17 then
silently returned zeros on real v3 installs:

* PR #1571 — ``/api/usage/forecast`` (daily-rate projection 2x'd or
  dropped non-message ``tool.result`` rows).
* PR #1576 — ``/api/cost-optimizer`` (read from in-memory ring that
  resets every dashboard restart; v3 users saw permanent ``$0``).
* PR #1580 — ``/api/automation-analysis`` (read stale ``moltbot-*.log``
  paths that don't exist on v3 installs).
* PR #1583 — ``/api/token-attribution`` (legacy JSONL walker filtered
  ``ev['type'] == 'message'`` and returned empty messages).
* Eng N's PR #1578 — ``query_session_model_journey`` (filtered v2
  event names; same family per #1582 imperfection table).
* PR #1572 — ``/api/rate-limits`` (in-memory ring buffer; not strictly
  v3-shape but same silent-zero family per #1582).

After today's drain, all six are fixed. This gate keeps them fixed.
"""

from __future__ import annotations

import io
import pathlib
import re
import tokenize

# ─── Forbidden patterns ────────────────────────────────────────────────

# Pattern A — dict access on an event envelope. Catches ``ev.get("type")
# == "message"`` and ``r.get("event_type") == "message"`` and friends.
# The ``.get("type"|"event_type")`` or ``["type"|"event_type"]`` form is
# the smoking gun — any variable name is fair game because the dict key
# tells us this is event-type access.
_PATTERN_A = re.compile(
    r"""\b
        [a-zA-Z_][a-zA-Z0-9_]*           # any var name
        (?:
            \.get\(\s*['"](?:type|event_type)['"]\s*(?:,[^)]*)?\)   # .get("type") or .get("event_type"[, default])
          | \[\s*['"](?:type|event_type)['"]\s*\]                    # ["type"] or ["event_type"]
        )
        \s*==\s*
        ['"](?:message|user|assistant)['"]
    """,
    re.VERBOSE,
)

# Pattern B — variable equality where the LHS name is an event-type
# alias. We restrict the LHS names to a short list of conventional
# spellings to avoid false positives on unrelated variables. The most
# common in this codebase are ``event_type``, ``etype``, ``ev_type``,
# ``obj_type``, plus ``et`` and ``kind`` for the short-name variants.
_PATTERN_B = re.compile(
    r"""\b
        (?:event_type|etype|ev_type|obj_type|kind|et)
        \s*==\s*
        ['"](?:message|user|assistant)['"]
    """,
    re.VERBOSE,
)

# Pattern C — SQL string literal. Catches ``WHERE event_type = 'message'``
# and ``WHERE type = 'message'`` inside any Python string. The DuckDB
# events table column is ``event_type``; ``type`` is the JSONL-on-disk
# shape, so either form is a v3 silent-zero risk in a SQL string.
_PATTERN_C = re.compile(
    r"""WHERE\s+
        (?:event_type|type)
        \s*=\s*
        '(?:message|user|assistant)'
    """,
    re.VERBOSE | re.IGNORECASE,
)

# ─── Allow marker ──────────────────────────────────────────────────────

# Inline opt-out. Must include a ``reason: …`` justification so the
# author can't bypass the gate without explaining why. Same-line only —
# a marker on the previous line does NOT count.
_ALLOW_RE = re.compile(r"#\s*v3-shape-gate:\s*allow\s*\(\s*reason\s*:")

# ─── Scope ─────────────────────────────────────────────────────────────

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_ROUTES_DIR = _REPO_ROOT / "routes"


def _docstring_line_set(source: str) -> set[int]:
    """Return the set of line numbers that are part of a docstring.

    A "docstring" here is any STRING token whose value spans multiple
    lines OR which is the sole statement on its line (the canonical
    triple-quoted module/function/class docstring shape).

    Why this isn't ``_code_lines_only``: Pattern A needs to see the
    actual ``"message"`` string literal on the RHS of ``==``. Stripping
    every STRING token (the way ``tests/test_no_direct_get_store_in_routes.py``
    does it) would erase the very token the regex is looking for. Instead
    we identify multi-line string literals + their line ranges and tell
    the scanner to ignore those lines — that catches every docstring in
    practice without erasing inline string literals on real code lines.
    """
    docstring_lines: set[int] = set()
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except tokenize.TokenizeError:
        return docstring_lines
    for tok in tokens:
        if tok.type != tokenize.STRING:
            continue
        start_line, _ = tok.start
        end_line, _ = tok.end
        # Multi-line string → mark every line it spans as docstring.
        if end_line > start_line:
            for ln in range(start_line, end_line + 1):
                docstring_lines.add(ln)
    return docstring_lines


def _comment_only_line(line: str) -> bool:
    """True when the entire line is a comment (or blank)."""
    stripped = line.lstrip()
    return not stripped or stripped.startswith("#")


def _scan_file(path: pathlib.Path) -> list[tuple[str, int, str, str]]:
    """Walk a single ``routes/*.py`` file and return a list of
    ``(filename, lineno, pattern_id, raw_line)`` offenders.

    Skip rules: lines that are part of a triple-quoted docstring (so
    docstring mentions of the bug pattern don't trip the gate), lines
    that are pure comments, and any line carrying the
    ``# v3-shape-gate: allow (reason: …)`` inline marker.
    """
    source = path.read_text()
    raw_lines = source.splitlines()
    docstring_lines = _docstring_line_set(source)
    offenders: list[tuple[str, int, str, str]] = []

    for i, raw in enumerate(raw_lines, start=1):
        if i in docstring_lines:
            continue
        if _comment_only_line(raw):
            continue
        if _ALLOW_RE.search(raw):
            continue
        if _PATTERN_A.search(raw):
            offenders.append((path.name, i, "A", raw.rstrip()))
        if _PATTERN_B.search(raw):
            offenders.append((path.name, i, "B", raw.rstrip()))
        if _PATTERN_C.search(raw):
            offenders.append((path.name, i, "C", raw.rstrip()))

    return offenders


def _scan_routes() -> list[tuple[str, int, str, str]]:
    offenders: list[tuple[str, int, str, str]] = []
    for p in sorted(_ROUTES_DIR.glob("*.py")):
        offenders.extend(_scan_file(p))
    return offenders


# ─── The gate ──────────────────────────────────────────────────────────


def test_no_v3_shape_silent_zero_in_routes():
    """No ``routes/*.py`` may filter event types on pre-v3 names without
    an inline ``# v3-shape-gate: allow (reason: …)`` justification.

    If this test fails:

    1. Read the bug story at the top of this file.
    2. If your callsite reads DuckDB ``query_events`` rows or a SQL
       result over the ``events`` table — STOP. You're about to ship
       the bug. Filter on v3 names (``assistant``, ``model.completed``,
       ``prompt.submitted``, ``tool.call``, ``tool.result``) or use
       ``_CHAIN_TYPES``/``_MSG_IN``/``_MSG_OUT`` sets that already cover
       both shapes.
    3. If your callsite reads a JSONL transcript from disk (the on-disk
       shape IS pre-v3, intentionally) — tag the line with::

           # v3-shape-gate: allow (reason: JSONL on-disk walker)

    4. If your callsite handles BOTH shapes in the same function — tag
       the legacy branch with::

           # v3-shape-gate: allow (reason: handles legacy+v3 in same fn)
    """
    offenders = _scan_routes()
    if offenders:
        msg_lines = [
            "v3-shape silent-zero filter detected in routes/ (refs #1582):",
            "",
            "The bug: filtering DuckDB events on pre-v3 names "
            "(message/user/assistant) silently matches ZERO rows on real",
            "OpenClaw v3 installs (daemon writes assistant/model.completed/",
            "prompt.submitted/etc). Endpoint returns empty arrays; user",
            "sees $0 cost or empty messages with no error.",
            "",
            "Offenders:",
        ]
        for fn, lineno, pid, raw in offenders:
            msg_lines.append(f"  [Pattern {pid}] {fn}:{lineno}: {raw}")
        msg_lines.append("")
        msg_lines.append(
            "Fix: filter on v3 names instead, OR tag the line with "
            "`# v3-shape-gate: allow (reason: ...)` if you're reading a "
            "JSONL on-disk walker / handling both shapes legitimately."
        )
        raise AssertionError("\n".join(msg_lines))


# ─── Self-test: gate regex actually matches what it should ─────────────


def test_gate_regex_catches_known_bad_shapes():
    """Pin the regex behaviour so a typo in ``_PATTERN_*`` can't silently
    let new offenders past CI. Asserts positive matches for the bug
    shapes we've actually seen in #1571/#1576/#1580/#1583, and negative
    matches for legitimate-looking lines.
    """
    bad_A = [
        'if ev.get("type") == "message":',
        "if ev.get('type') == 'message':",
        'if ev["type"] == "message":',
        "if obj.get('type') == 'assistant':",
        'if r.get("event_type") == "message":',
        'if event.get("type") == "user":',
        # Default arg shouldn't save it — still a bug.
        'if ev.get("type", "") == "message":',
    ]
    bad_B = [
        'if etype == "message":',
        "if ev_type == 'assistant':",
        'if event_type == "user":',
        'elif obj_type == "message":',
        'if kind == "message":',
        'if et == "message":',
    ]
    bad_C = [
        'sql = "SELECT * FROM events WHERE event_type = \'message\'"',
        'q = """SELECT id FROM events WHERE type = \'assistant\' AND ts > ?"""',
    ]
    good = [
        # Tool name dispatch — not event type.
        'if tn == "message" or "tts" in tn:',
        # Role check inside message envelope — correct in both shapes.
        'if role == "user":',
        'if msg.get("role") == "assistant":',
        # v3 names — these are the FIX, not the bug.
        'if ev.get("event_type") == "model.completed":',
        'if etype == "prompt.submitted":',
        # Set membership covers both shapes — also the fix.
        'if etype in _CHAIN_TYPES:',
        # Block-type dispatch inside content blocks — not event type.
        'if btype == "text":',
        # Allow marker present.
        'if etype == "message":  # v3-shape-gate: allow (reason: JSONL walker)',
    ]
    for s in bad_A:
        assert _PATTERN_A.search(s), f"Pattern A should flag: {s!r}"
    for s in bad_B:
        assert _PATTERN_B.search(s), f"Pattern B should flag: {s!r}"
    for s in bad_C:
        assert _PATTERN_C.search(s), f"Pattern C should flag: {s!r}"
    for s in good:
        # `good` lines must NOT match A or B in their raw form
        # (the allow-marker example matches the regex but is excluded
        # at the file-scan layer; verify it's the marker, not the regex).
        if "v3-shape-gate" in s:
            assert _ALLOW_RE.search(s), f"allow marker should match: {s!r}"
            continue
        assert not _PATTERN_A.search(s), f"Pattern A FALSE POSITIVE: {s!r}"
        assert not _PATTERN_B.search(s), f"Pattern B FALSE POSITIVE: {s!r}"
        assert not _PATTERN_C.search(s), f"Pattern C FALSE POSITIVE: {s!r}"


def test_allow_marker_requires_reason():
    """A bare ``# v3-shape-gate: allow`` without a reason MUST NOT bypass
    the gate. The reason field is the whole point — it forces the next
    agent to justify why their callsite is legitimately reading the
    pre-v3 shape.
    """
    bare_marker = "# v3-shape-gate: allow"
    with_reason = "# v3-shape-gate: allow (reason: JSONL walker)"
    assert not _ALLOW_RE.search(bare_marker), (
        "bare marker without reason MUST NOT bypass the gate"
    )
    assert _ALLOW_RE.search(with_reason), (
        "marker WITH reason field must bypass the gate"
    )
