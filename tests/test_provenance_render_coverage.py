"""The ratchet: the unbadged-figure surface may shrink, never grow.

WO-6 asks that no dollar amount or score render without a basis. The server
half of that is enforceable outright (``tests/test_provenance.py`` walks each
real payload and fails on any figure with no basis behind it). The frontend
half is a 29,000-line file with about sixty places that build a currency
string, written over two years, and converting all of them in one change
would be a diff nobody could review against a feature nobody could roll back.

So this guard does the next most useful thing: it counts what is left and
refuses to let that number go up. A new card that prints a dollar figure
without a basis fails here on the day it lands, and every conversion of an
old one lowers the ceiling below.

``UNBADGED_CEILING`` may only ever be edited DOWNWARD. If a change needs it
raised, the change is adding an unlabelled figure, which is the thing this
file exists to stop.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")

# A line that builds a currency string for the screen.
_MONEY_RENDER = re.compile(
    r"""(?:'\$'\s*\+|\+\s*'\$'|'\$'\+|"\$"\s*\+|'<\$0\.01'|'\$0\.00'|"\$0\.00")"""
)

# Routed through the shared component, so the figure carries its basis.
# ``cmFmtMoney`` alone does NOT count: sharing a formatter is reuse, not
# provenance, and this guard is about the badge.
_BADGED = ("cmProv.figure", "cmProv.money", "cmProv.score", "cmProv.badge",
           "cmMoney(", "cmScore(", "cmFigure(", "cmProvBadge(")

# Measured 2026-08-25, when the shared badge shipped. Ratchet only downward.
#
# It over-counts slightly: a plan price in the upgrade overlay and the two
# lines that DETECT the old "$0.00" placeholder both match the pattern and
# are not figures. Over-counting is the safe direction for a ratchet, and
# ``test_the_ceiling_is_not_padded`` keeps the slack from growing into room
# for a real one to hide in.
UNBADGED_CEILING = 63

# A badged figure's legacy fallback branch usually lands a line or two below
# the shared call. Count the render as covered when the shared component
# appears anywhere in the few lines leading up to it.
_CONTEXT_LINES = 3


def _unbadged():
    lines = open(APP_JS, encoding="utf-8").read().splitlines()
    out = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if not _MONEY_RENDER.search(line):
            continue
        window = "\n".join(lines[max(0, i - _CONTEXT_LINES):i + 1])
        if any(k in window for k in _BADGED):
            continue
        out.append((i + 1, stripped))
    return out


def test_the_unbadged_figure_surface_does_not_grow():
    pending = _unbadged()
    assert len(pending) <= UNBADGED_CEILING, (
        "%d money renders in app.js carry no basis, up from a ceiling of %d.\n"
        "A new dollar figure needs a provenance entry from its payload and a "
        "render through window.cmProv (static/js/provenance.js).\n"
        "Newly unbadged, or the ones to convert:\n%s"
        % (len(pending), UNBADGED_CEILING,
           "\n".join("  app.js:%d  %s" % (n, s[:110]) for n, s in pending)))


def test_the_ceiling_is_not_padded():
    """A ceiling well above the real count would let several unlabelled
    figures land before anyone noticed. Keep it tight."""
    pending = _unbadged()
    assert UNBADGED_CEILING - len(pending) <= 3, (
        "UNBADGED_CEILING is %d but only %d renders are unbadged. Lower it."
        % (UNBADGED_CEILING, len(pending)))


def test_at_least_the_cost_tab_figures_are_badged():
    """The ratchet alone would pass on a file where nothing was ever
    converted. Name the surfaces that must be done."""
    src = open(APP_JS, encoding="utf-8").read()
    for marker, what in [
        ("_cmCell('todayCost'", "the Cost tab period table"),
        ("cost-basis-badge", "the Overview spend tile"),
        ("loopRiskCell", "Guard's spend at risk"),
        ("costEntry", "the Top Sessions by cost table"),
        ("d.withheld", "withheld history buckets"),
    ]:
        assert marker in src, "%s is no longer badged" % what
