"""Only the needs-you strip may claim a session is waiting on you.

The Overview hero had a bucket derived purely from age — last output between
2 and 10 minutes ago — and rendered it as "One session is waiting on you."
That state is equally consistent with the agent thinking, running a long
tool, or being dead. Its own sub-line said so: "Nothing has produced output
in the last two minutes." The headline contradicted its own subtitle.

Once the needs-you strip shipped, the two rendered on the SAME page, and
could disagree: "Nothing needs you right now" directly above "1 session is
waiting on you". Same question, two answers, one screen.

"Waiting on you" is a claim only the strip can make, because only it has
evidence — a runtime that reported a prompt, an unanswered approval in the
queue, or a tool call that hung past the dwell threshold. This test keeps the
claim where the evidence is. The two components sit ~7,500 lines apart in
app.js, so nothing else would catch it drifting back.
"""

from __future__ import annotations

import pathlib
import re

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_JS = ROOT / "clawmetry" / "static" / "js" / "app.js"


@pytest.fixture(scope="module")
def app_js() -> str:
    return APP_JS.read_text(encoding="utf-8")


def _claim_lines(js: str, pattern: str):
    """Non-comment lines matching a claim pattern, with line numbers."""
    out = []
    for n, line in enumerate(js.splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if re.search(pattern, line):
            out.append((n, stripped[:100]))
    return out


def test_age_alone_never_claims_waiting_on_you(app_js):
    """The hero renders from `counts.waiting`, which is an age bucket."""
    hits = _claim_lines(app_js, r"waiting on you")
    assert not hits, (
        "'waiting on you' is asserted outside the needs-you strip:\n"
        + "\n".join(f"  app.js:{n}  {t}" for n, t in hits)
        + "\nThat phrasing needs evidence (a reported prompt, a pending "
          "approval, or a hung tool call). An age bucket has none."
    )


def test_the_strip_still_makes_the_claim(app_js):
    """The inverse: the component that DOES have evidence must still say it,
    or this test would pass on a page that never tells anyone anything."""
    assert "needs.confident" in app_js
    assert "needs.one_waiting" in app_js and "needs.n_waiting" in app_js


def test_quiet_wording_matches_its_own_subtitle(app_js):
    """The sub-line explains a silence window; the headline must agree."""
    assert "has gone quiet" in app_js or "have gone quiet" in app_js, (
        "the age bucket should describe silence, not intent")
    assert "Nothing has produced output in the last two minutes" in app_js, (
        "the honest sub-line disappeared — if the window changed, the "
        "headline wording should be revisited with it")
