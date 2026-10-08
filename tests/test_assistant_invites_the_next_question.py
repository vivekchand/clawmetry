"""The Assistant is the landing screen, so it has to invite the next question.

Founder report 2026-10-08, three findings on one screen:

1. The assistant ends most answers by proposing the next question ("Follow-up:
   would you like to compare Codex sessions with and without compaction?") and
   we rendered it as a sentence. The one moment the product invites you further
   was a dead end you had to retype by hand.
2. Answers were dense with inline [1] [2] [3] markers, one on nearly every
   clause, under a "Sources used" panel that already carries the full trail.
   "a lot of those references are confusing ... we need a crisp reply".
3. The page background carried a hardcoded rgba(15,111,255,.06) wash in BOTH
   themes: the LIGHT theme's blue laid over a near-black page, which is what
   "the bg color, something is odd" turned out to be.
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
ASSISTANT_JS = os.path.join(REPO, "clawmetry", "static", "js", "assistant.js")
ASSISTANT_CSS = os.path.join(REPO, "clawmetry", "static", "css", "assistant.css")
DASH_CSS = os.path.join(REPO, "clawmetry", "static", "css", "dashboard.css")


def _split(content):
    """Run the shipped splitFollowUps against one answer."""
    node = shutil.which("node")
    if not node:
        pytest.skip("node not available")
    src = open(ASSISTANT_JS, encoding="utf-8").read()
    start = src.index("  var FOLLOW_UP_LINE =")
    end = src.index("  function askQuestion(", start)
    harness = "%s\nconsole.log(JSON.stringify(splitFollowUps(%s)));\n" % (
        src[start:end], json.dumps(content))
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(harness)
        path = fh.name
    try:
        p = subprocess.run([node, path], capture_output=True, text=True, timeout=20)
        assert p.returncode == 0, p.stderr
        return json.loads(p.stdout.strip().splitlines()[-1])
    finally:
        os.unlink(path)


# ── the offer becomes something you can press ──────────────────────────────

def test_the_trailing_follow_up_becomes_a_question():
    out = _split("Codex carried the heaviest context.\n\n"
                 "Follow-up: would you like to compare Codex sessions with and "
                 "without compaction, to see how token growth differs?")
    assert out["questions"] == [
        "would you like to compare Codex sessions with and without compaction, "
        "to see how token growth differs?"]
    assert "Follow-up" not in out["body"], "the offer must leave the prose it was buried in"
    assert out["body"].strip().endswith("heaviest context.")


def test_an_answer_with_no_offer_is_untouched():
    text = "Codex carried the heaviest context. Claude Code ran lighter."
    out = _split(text)
    assert out["questions"] == [] and out["body"] == text


def test_a_follow_up_that_is_not_a_question_stays_in_the_prose():
    """"Follow-up: I checked the compaction events" is a statement about what
    we did, not an offer. Lifting it out would delete prose from the answer."""
    text = "Tokens are flat.\n\nFollow-up: I also checked the compaction events."
    out = _split(text)
    assert out["questions"] == [] and out["body"] == text


def test_a_mid_answer_mention_is_not_mistaken_for_the_offer():
    text = "Follow-up work is tracked separately.\n\nCodex carried the most context."
    out = _split(text)
    assert out["questions"] == [] and out["body"] == text


def test_several_offers_are_capped_and_each_stays_a_question():
    out = _split("Done.\n\nFollow-ups: Compare Codex with compaction? "
                 "Show the heaviest sessions? Break it down by day? And a fourth?")
    assert 1 <= len(out["questions"]) <= 3
    assert all(q.endswith("?") for q in out["questions"])


def test_the_chip_goes_through_the_composer_not_around_it():
    src = open(ASSISTANT_JS, encoding="utf-8").read()
    assert "requestSubmit" in src, (
        "a chip that posts directly would bypass the composer's busy, scope "
        "and readiness guards")


# ── crisp answers, sparing citations ───────────────────────────────────────

def test_the_prompt_no_longer_demands_a_marker_on_every_claim():
    src = open(os.path.join(REPO, "clawmetry", "assistant_service.py"),
               encoding="utf-8").read()
    assert "Cite evidence by its [number]." not in src, (
        "the unconditional rule is what produced a marker on nearly every "
        "clause")
    assert "Be crisp." in src
    for phrase in ("ONLY where the figure", "Sources panel"):
        assert phrase in src, "citations must be the exception that earns its place"


# ── the background ─────────────────────────────────────────────────────────

def test_the_page_wash_is_themed_not_hardcoded_blue():
    css = open(DASH_CSS, encoding="utf-8").read()
    assert "rgba(15,111,255,0.06)" not in css, (
        "the light theme's blue was washing over the dark page")
    assert "--page-wash" in css
    body = re.search(r"\n  body \{[^}]*\}", css).group(0)
    assert "var(--page-wash)" in body


def test_dark_mode_gets_a_neutral_wash():
    css = open(DASH_CSS, encoding="utf-8").read()
    dark = css[css.index('[data-theme="dark"]'):]
    wash = re.search(r"--page-wash:\s*([^;]+);", dark).group(1)
    assert "255, 255, 255" in wash or "255,255,255" in wash, (
        "a hue in the dark wash is the cast this fixed: %r" % wash)


def test_the_serif_has_one_name():
    css = open(DASH_CSS, encoding="utf-8").read()
    assert "--font-serif:" in css
    assert css.count("Iowan Old Style") == 1, "the stack was retyped again"


# ── the reading surface ────────────────────────────────────────────────────

def test_assistant_prose_is_a_reading_column():
    css = open(ASSISTANT_CSS, encoding="utf-8").read()
    rule = re.search(r"\.cm-assistant-message\.is-assistant \.cm-assistant-message-content \{[^}]*\}", css)
    assert rule, "assistant prose has no reading treatment"
    body = rule.group(0)
    assert "var(--font-serif" in body
    measure = int(re.search(r"max-width:\s*(\d+)ch", body).group(1))
    assert 55 <= measure <= 75, "line length outside a readable measure: %dch" % measure


def test_the_send_button_is_no_longer_the_loudest_thing():
    css = open(ASSISTANT_CSS, encoding="utf-8").read()
    rule = re.search(r"\n\.cm-assistant-send \{[^}]*\}", css).group(0)
    assert "background: var(--bg-accent)" not in rule, (
        "a filled accent button makes blue mean both 'primary' and 'info'")


def test_the_follow_up_chips_are_reachable_and_calm():
    css = open(ASSISTANT_CSS, encoding="utf-8").read()
    assert ".cm-assistant-followup:focus-visible" in css, "keyboard users need the ring"
    assert "prefers-reduced-motion" in css
