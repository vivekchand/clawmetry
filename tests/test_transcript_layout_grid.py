"""Guards for the replay layout and the Trail deep link.

Two founder-reported breakages, 2026-09-05, both in the Sessions replay:

1. ``.transcript-layout`` is a two-column grid: the message stream, then the
   sticky turn TOC (240px). Anything the replay *injects* into it at runtime
   is a third grid item, and an auto-placed third item takes the wide first
   column and shoves ``#transcript-messages`` into the 240px TOC column - the
   replay then renders as an overflowing strip pinned to the right with the
   left half of the page blank. ``#replay-load-earlier`` shipped that way
   once and was fixed with an inline ``grid-column``; ``#replay-tree-container``
   then repeated it verbatim when 0.12.811 moved its insert to the anchor's
   real parent. The fix is a CSS rule on the layout itself so the *next*
   injected node cannot repeat it, plus the inline style on each mount.

2. ``switchTab()`` highlights ``event.target`` when a tab has no nav item of
   its own (Trail is one: it reuses the Sessions entry). On a boot-time deep
   link - ``#trail=<runtime>:<sid>`` reloaded, bookmarked or shared - there is
   no click, ``window.event`` is the DOMContentLoaded event and its target is
   ``document``, which has no ``classList``. The TypeError threw out of
   ``switchTab`` *before* the per-tab loader dispatch, and the Trail page sat
   on its static "Opening the trail..." skeleton forever. The guard must test
   ``event.target.classList`` and not just ``event.target``.

Both are source-level guards on the served assets: the bugs are pure layout /
control flow in files with no build step, so the shipped text is the artifact.
"""

from __future__ import annotations

import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, ".."))
_APP_JS = os.path.join(_ROOT, "clawmetry", "static", "js", "app.js")
_CSS = os.path.join(_ROOT, "clawmetry", "static", "css", "dashboard.css")
_TRANSCRIPTS_HTML = os.path.join(
    _ROOT, "clawmetry", "templates", "tabs", "transcripts.html")


def _read(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


# ── 1. the grid cannot be hijacked by an injected sibling ────────────────────

def test_transcript_layout_is_still_a_two_column_grid():
    """If this changes, the guards below need re-thinking, not deleting."""
    css = _read(_CSS)
    assert re.search(
        r"\.transcript-layout\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\)\s+240px",
        css,
    ), "the two-column messages|TOC grid is gone - re-check the guards below"


def test_only_messages_and_toc_are_authored_grid_children():
    """The template must not add a third column-taking child by hand."""
    html = _read(_TRANSCRIPTS_HTML)
    block = re.search(
        r'<div class="transcript-layout">(.*?)</div>\s*<!--', html, re.S)
    assert block, "the .transcript-layout block moved - update this guard"
    ids = re.findall(r'id="([^"]+)"', block.group(1))
    assert ids == ["transcript-messages", "transcript-toc"], ids


def test_injected_children_span_the_grid_row():
    """The CSS rule that makes the layout immune to the next injected node."""
    css = _read(_CSS)
    assert re.search(
        r"\.transcript-layout\s*>\s*\*"
        r":not\(#transcript-messages\)"
        r":not\(\.transcript-toc\)\s*\{[^}]*grid-column:\s*1\s*/\s*-1",
        css,
    ), (
        "runtime-injected children of .transcript-layout must span the row, "
        "or they steal the messages column and squeeze the replay into the "
        "240px TOC column"
    )


@pytest.mark.parametrize("mount_id", ["replay-load-earlier", "replay-tree-container"])
def test_each_injected_mount_also_sets_grid_column_inline(mount_id: str):
    """Belt and braces: each mount is correct without the stylesheet too."""
    js = _read(_APP_JS)
    idx = js.index("'%s'" % mount_id)
    # The assignment lands within the creation block that follows the id.
    window = js[idx:idx + 2000]
    assert re.search(r"grid-?[Cc]olumn\s*[:=]\s*'?1 / -1", window), (
        "#%s is created without grid-column:1/-1 - as a plain auto-placed "
        "child of .transcript-layout it takes the messages column" % mount_id
    )


# ── 2. a deep-linked trail must reach its loader ─────────────────────────────

def test_switchtab_event_fallback_checks_classlist():
    js = _read(_APP_JS)
    uses = [m.start() for m in re.finditer(
        r"event\.target\.classList\.add\(", js)]
    assert len(uses) == 1, "expected exactly one nav fallback, got %d" % len(uses)
    # Everything from the enclosing `if (` up to the call is the guard chain.
    head = js.rindex("if (", 0, uses[0])
    chain = js[head:uses[0]]
    assert re.search(r"event\.target\.classList\s*(\)|&&)", chain), (
        "switchTab's no-nav-item fallback must guard event.target.classList: "
        "on a boot-time #trail= deep link window.event is DOMContentLoaded and "
        "its target is `document`, which has none - the TypeError skips the "
        "per-tab loader dispatch and the Trail page never loads.\n" + chain
    )


def test_trail_dispatch_still_follows_the_fallback():
    """The ordering that made the TypeError fatal - keep it visible."""
    js = _read(_APP_JS)
    fallback = js.index("event.target.classList.add(")
    dispatch = js.index("if (name === 'trail') {")
    assert fallback < dispatch, (
        "the loader dispatch moved above the nav fallback; if that is "
        "deliberate, this guard can go, but the classList check must stay"
    )
