"""A scoped hero must name its runtime, not describe the machine.

Founder report 2026-10-07. The runtime switcher was on **Codex**, which was
genuinely idle, and the Overview hero read:

    YOUR AGENT
    It's idle right now.

directly beneath a red banner reading "CRITICAL: Your claude code agent
changed a lot of files at once ... About $5.00 at risk so far", and above a
needs-you strip reading "No agents running". A Claude Code session was
running at that moment.

Every number on that screen was correct. The hero's counts come from
``/api/live-sessions?runtime=codex`` and Codex really had nothing live. The
defect is that a RUNTIME-SCOPED measurement was phrased as a NODE-WIDE claim,
so one screen gave two opposite answers to "is my agent working?" and neither
sentence said which runtime it meant.

FLYWHEEL section 0a.2 states the rule for the other direction (a node-wide
number must not render silently under a runtime filter). This is the same
rule from the inside: a scoped number must not speak for the machine.

The headline block is extracted from the shipped ``app.js`` and run under
node, so a rewrite that drops the runtime cannot pass.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")
LOCALES = os.path.join(REPO, "clawmetry", "static", "locales", "en.json")


def _headline(working, waiting, live_known, runtime):
    """Run the shipped headline block for one state."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")
    src = open(APP_JS, encoding="utf-8").read()
    start = src.index("  // Headline. Say the number and let it carry the news")
    end = src.index("var _liveRows =", start)
    block = src[start:end]
    assert "_rtScoped" in block, "the scoped-naming logic is gone from the hero"
    harness = """
var _liveRt = %s, _working = %d, _waiting = %d, _liveKnown = %s, busy = _working > 0;
/* The evidence-freshness gate lives in the same block; these tests cover the
   BACKED path, so the evidence is current and the gate is open. Its own
   behaviour is pinned by tests/test_hero_refuses_unbacked_realtime_claim.py. */
var _live = {staleReason: '', processesLive: 0, evidenceAge: 5};
function _cmRuntimeLabel(k){ return ({codex:'Codex', claude_code:'Claude Code'})[k] || k; }
%s
console.log(JSON.stringify({headline: headline}));
""" % (json.dumps(runtime), working, waiting,
       "true" if live_known else "false", block)
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        p = subprocess.run([node, path], capture_output=True, text=True, timeout=20)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout.strip().splitlines()[-1])["headline"]
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# The reported screen
# ---------------------------------------------------------------------------

def test_an_idle_runtime_does_not_claim_the_machine_is_idle():
    h = _headline(working=0, waiting=0, live_known=True, runtime="codex")
    assert "Codex" in h, (
        "the hero spoke for the whole machine from one runtime's counts; this "
        "is the sentence that sat under a CRITICAL banner about a running "
        "Claude Code agent")
    assert h != "It’s idle right now."


def test_node_wide_keeps_the_original_sentence():
    assert _headline(0, 0, True, "all") == "It’s idle right now."
    assert _headline(1, 0, True, "all") == "It’s working right now."
    assert _headline(3, 0, True, "all") == "3 sessions are working right now."
    assert _headline(0, 1, True, "all") == "One session has gone quiet."
    assert _headline(0, 2, True, "all") == "2 sessions have gone quiet."


@pytest.mark.parametrize("working,waiting", [(1, 0), (3, 0), (0, 1), (0, 2), (0, 0)])
def test_every_scoped_state_names_the_runtime(working, waiting):
    h = _headline(working, waiting, True, "claude_code")
    assert "Claude Code" in h, "scoped state left unnamed: %r" % h


def test_the_unknown_state_is_unchanged():
    """"Nothing to report yet." is about our own reach, not a runtime."""
    assert _headline(0, 0, False, "codex") == "Nothing to report yet."


def test_the_recency_fallback_is_also_named():
    assert "Codex" in _headline(1, 0, False, "codex")


# ---------------------------------------------------------------------------
# The strip directly above it must agree
# ---------------------------------------------------------------------------

def test_the_strip_names_the_runtime_too():
    src = open(APP_JS, encoding="utf-8").read()
    assert "needs.none_running_runtime" in src, (
        "the needs-you strip still says a bare 'No agents running' under a "
        "runtime filter, which is the contradiction the hero fix removes")
    cat = json.load(open(LOCALES, encoding="utf-8"))
    assert cat["needs.none_running_runtime"] == "No {runtime} agents running"
    assert cat["needs.none_running"] == "No agents running", "node-wide copy changed"


def test_the_hoisting_trap_stays_closed():
    """`_scoped` is declared BELOW the headline block. Reading it there is
    hoisted-but-undefined, which silently reverts every assertion above."""
    src = open(APP_JS, encoding="utf-8").read()
    start = src.index("  // Headline. Say the number and let it carry the news")
    block = src[start:src.index("var _liveRows =", start)]
    code = "\n".join(ln for ln in block.split("\n")
                     if not ln.strip().startswith("//"))
    assert re.search(r"(?<![A-Za-z0-9_])_scoped\b", code) is None, (
        "the headline reads `_scoped`, which is hoisted-but-undefined there")
    assert "_rtScoped" in code, "the local replacement is gone"
