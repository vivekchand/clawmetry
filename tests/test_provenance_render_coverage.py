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

``UNBADGED_CEILING`` and ``TAB_UNBADGED_CEILING`` may only ever be edited
DOWNWARD. If a change needs one raised, the change is adding an unlabelled
figure, which is the thing this file exists to stop.

Per tab (REQ-OBS-CEA-025, vivekchand/clawmetry#5937)
----------------------------------------------------
The whole-file count cannot say WHERE an unlabelled figure is, and a count
held under a ceiling can quietly trade a converted figure on a quiet panel
for a new one on the Overview hero. So the Overview, Usage and Sessions tabs
are also counted on their own, and their scope is discovered, not listed:

* a function belongs to a tab when it touches an element id that tab's
  template (``clawmetry/templates/tabs/<tab>.html``) defines;
* so do the helpers those functions call, down three levels, unless the
  helper touches ids of a different tab only;
* a money render is a line that builds a currency string, or a call to a
  local formatter that does (discovered the same way: a short function whose
  ``return`` builds one).

Criteria declared here:

* AC-OBS-CEA-025.10 -- the unbadged count on Overview, Usage and Sessions
  does not grow, discovered from the tab templates:
  ``test_each_tab_unbadged_money_renders_do_not_grow``,
  ``test_the_tab_discovery_reaches_the_cost_surfaces``.
* AC-OBS-CEA-025.8 -- the named cost surfaces render every figure through
  the shared component: ``test_the_named_cost_surfaces_route_every_figure``.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_JS = os.path.join(REPO, "clawmetry", "static", "js", "app.js")
TABS_DIR = os.path.join(REPO, "clawmetry", "templates", "tabs")

# A line that builds a currency string for the screen.
_MONEY_RENDER = re.compile(
    r"""(?:'\$'\s*\+|\+\s*'\$'|'\$'\+|"\$"\s*\+|'<\$0\.01'|'\$0\.00'|"\$0\.00")"""
)

# Routed through the shared component, so the figure carries its basis.
# ``cmFmtMoney`` alone does NOT count: sharing a formatter is reuse, not
# provenance, and this guard is about the badge. ``cmCostFigure`` is the
# shared figure for a cost whose basis may not have arrived yet (it badges
# whenever an entry exists and never invents one).
_BADGED = ("cmProv.figure", "cmProv.money", "cmProv.score", "cmProv.badge",
           "cmProv.costFigure", "cmMoney(", "cmScore(", "cmFigure(",
           "cmProvBadge(", "cmCostFigure(")

# Measured 2026-08-25, when the shared badge shipped. Ratchet only downward.
# 62 -> 43 (2026-09-14, #5937): the remaining Usage cards, the Overview hero
# chip and the Sessions transcript chips.
#
# It over-counts slightly: a plan price in the upgrade overlay and the two
# lines that DETECT the old "$0.00" placeholder both match the pattern and
# are not figures. Over-counting is the safe direction for a ratchet, and
# ``test_the_ceiling_is_not_padded`` keeps the slack from growing into room
# for a real one to hide in.
UNBADGED_CEILING = 43

# Per tab, discovered from the tab templates. Ratchet only downward.
# Overview's remainder is the run and cohort comparison panels, the anomaly
# panel, the waste summary and loop sources; Sessions' is similar runs and
# the orchestration panel. None of their payloads carries a basis yet.
TAB_UNBADGED_CEILING = {"overview": 24, "usage": 0, "transcripts": 5}

# The surfaces REQ-OBS-CEA-025.8 names, by the function that renders them.
# Each must render every money figure through the shared component.
NAMED_COST_SURFACES = {
    "overview": ("_renderOverviewHero", "_cmHeroCostChip"),
    "usage": ("_sfRender", "_renderEfficiencyCardInner", "_cmEffIdeaRowHtml",
              "renderCacheHitRateCard", "renderRoutingAdvisorCard",
              "loadCostForecast", "loadCacheRisk", "loadCompressionPotential",
              "loadCacheAnalytics", "renderCostComparison",
              "renderSpendOptimization", "renderPluginPieChart",
              "loadSkillAttribution", "loadAllSkills", "_skillCostTableHtml",
              "loadUsageByTeam"),
    "transcripts": ("_renderReplayEvent", "_renderTurnChapter"),
}

# A badged figure's legacy fallback branch usually lands a line or two below
# the shared call. Count the render as covered when the shared component
# appears anywhere in the few lines leading up to it.
_CONTEXT_LINES = 3


def _lines():
    return open(APP_JS, encoding="utf-8").read().splitlines()


def _is_badged(lines, i):
    window = "\n".join(lines[max(0, i - _CONTEXT_LINES):i + 1])
    return any(k in window for k in _BADGED)


def _unbadged():
    lines = _lines()
    out = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("*"):
            continue
        if not _MONEY_RENDER.search(line):
            continue
        if _is_badged(lines, i):
            continue
        out.append((i + 1, stripped))
    return out


# ── Discovery ────────────────────────────────────────────────────────────────

def _functions(lines):
    """Top-level function name -> list of (first line, end line) spans."""
    starts = [(i, m.group(1)) for i, line in enumerate(lines)
              for m in [re.match(r"^(?:async )?function ([\w$]+)\(", line)] if m]
    spans = {}
    for k, (i, name) in enumerate(starts):
        end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
        spans.setdefault(name, []).append((i, end))
    return spans


def _formatters(lines):
    """Names of short functions, at any depth, whose return builds money."""
    out = set()
    for i, line in enumerate(lines):
        m = re.search(r"\bfunction ([\w$]+)\s*\([^)]*\)\s*\{", line)
        if not m:
            continue
        body = [line[m.end():]]
        j = i
        while "}" not in body[-1] or body[-1].strip() not in ("}", "};") and j == i and not body[-1].rstrip().endswith("}"):
            j += 1
            if j >= len(lines) or j - i > 8:
                break
            body.append(lines[j])
            if lines[j].strip() in ("}", "};"):
                break
        if j - i > 8:
            continue
        text = "\n".join(body)
        if re.search(r"\breturn\b", text) and _MONEY_RENDER.search(text):
            out.add(m.group(1))
    return out


def _tab_ids():
    tabs = {}
    for fn in os.listdir(TABS_DIR):
        if fn.endswith(".html"):
            html = open(os.path.join(TABS_DIR, fn), encoding="utf-8").read()
            tabs[fn[:-5]] = set(re.findall(r'\bid="([^"]+)"', html))
    return tabs


def _ids_touched(text):
    return (set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]", text))
            | set(re.findall(r"querySelector(?:All)?\(\s*['\"]#([\w-]+)", text)))


def _tab_scope(tab, lines=None):
    """The functions that render ``tab``: seeds by template id, then callees."""
    lines = lines or _lines()
    funcs = _functions(lines)
    tabs = _tab_ids()

    def body(name):
        return "\n".join("\n".join(lines[a:b]) for a, b in funcs[name])

    owners = {}
    for name in funcs:
        touched = _ids_touched(body(name))
        owners[name] = {t for t, ids in tabs.items() if touched & ids}
    scope = {n for n, t in owners.items() if tab in t}
    frontier = set(scope)
    for _depth in range(3):
        nxt = set()
        for name in frontier:
            for callee in set(re.findall(r"\b([\w$]+)\s*\(", body(name))) & set(funcs):
                if callee in scope or (owners[callee] and tab not in owners[callee]):
                    continue
                nxt.add(callee)
        scope |= nxt
        frontier = nxt
    return scope, funcs


def _unbadged_in(names, funcs, lines, fmts):
    calls = [re.compile(r"(?<![\w.$])%s\s*\(" % re.escape(f)) for f in fmts]
    found = set()
    for name in names:
        for a, b in funcs.get(name, []):
            for i in range(a, b):
                line = lines[i]
                stripped = line.strip()
                if stripped.startswith("//") or stripped.startswith("*"):
                    continue
                is_def = re.search(r"\bfunction [\w$]+\s*\(", line)
                money = _MONEY_RENDER.search(line) or (
                    not is_def and any(c.search(line) for c in calls))
                if money and not _is_badged(lines, i):
                    found.add((i + 1, name, stripped[:110]))
    return sorted(found)


def _tab_unbadged(tab):
    lines = _lines()
    scope, funcs = _tab_scope(tab, lines)
    return _unbadged_in(scope, funcs, lines, _formatters(lines)), scope


# ── The guards ───────────────────────────────────────────────────────────────

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


def test_each_tab_unbadged_money_renders_do_not_grow():
    """AC-OBS-CEA-025.10: per tab, found from the tab's own template."""
    report = []
    for tab, ceiling in sorted(TAB_UNBADGED_CEILING.items()):
        found, _scope = _tab_unbadged(tab)
        if len(found) > ceiling:
            report.append("%s: %d unbadged money renders, ceiling %d\n%s" % (
                tab, len(found), ceiling,
                "\n".join("  app.js:%d %s: %s" % f for f in found)))
        # A ceiling far above the count is room for a new one to hide in.
        assert ceiling - len(found) <= 3, (
            "TAB_UNBADGED_CEILING[%r] is %d but only %d remain. Lower it."
            % (tab, ceiling, len(found)))
    assert not report, (
        "A dollar figure on these tabs renders with no basis. Route it through "
        "window.cmProv / window.cmCostFigure with the entry its payload "
        "sends:\n" + "\n".join(report))


def test_the_tab_discovery_reaches_the_cost_surfaces():
    """A discovery that found nothing would pass the ratchet vacuously. The
    renderers of every named surface must be inside their tab's scope."""
    for tab, names in NAMED_COST_SURFACES.items():
        scope, funcs = _tab_scope(tab)
        assert len(scope) >= 5, "%s tab discovery found %r" % (tab, scope)
        for name in names:
            assert name in funcs, "%s() is gone from app.js" % name
            assert name in scope, (
                "%s() renders the %s tab but discovery does not reach it" % (name, tab))


def test_the_named_cost_surfaces_route_every_figure():
    """AC-OBS-CEA-025.8: no money render in these functions skips the shared
    component, and each one actually calls it."""
    lines = _lines()
    funcs = _functions(lines)
    fmts = _formatters(lines)
    for tab, names in NAMED_COST_SURFACES.items():
        found = _unbadged_in(names, funcs, lines, fmts)
        assert not found, "%s tab: unlabelled cost renders:\n%s" % (
            tab, "\n".join("  app.js:%d %s: %s" % f for f in found))
        for name in names:
            text = "\n".join("\n".join(lines[a:b]) for a, b in funcs[name])
            # Either it calls the shared component itself, or it hands the
            # figure to another named renderer of the same tab that does.
            delegates = [n for n in names if n != name
                         and re.search(r"(?<![\w.$])%s\s*\(" % re.escape(n), text)]
            assert delegates or any(k in text for k in _BADGED + ("cmProv.text(",)), (
                "%s() renders no figure through the shared component" % name)


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
        ("_cmHeroCostChip(", "the Overview hero cost chip"),
        ("cmProv.of(data, 'messages[].cost_usd')", "the Sessions transcript chips"),
    ]:
        assert marker in src, "%s is no longer badged" % what
