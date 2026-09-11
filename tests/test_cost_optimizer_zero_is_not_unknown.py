"""The cost optimizer must not print a hole as "$0.000".

`provenance.js` exists for exactly this failure, and says so in its own header:

    A failed read once shipped as "$0.00" and was read, correctly, as a real
    result: a zero and a hole are identical once they are formatted. Here they
    never share a shape.

The Cost tiles use it (`window.cmProv.money`). `loadCostOptimizerData` did not:

    var todayCost = data.todayCost || 0;
    ... '$' + todayCost.toFixed(3)

`|| 0` turns null, undefined and a missing key into a confident `$0.000`.

Measured on the hosted dashboard 2026-09-11, `/api/cost-optimizer` returned
`todayCost: 0` and `projectedMonthlyCost: 0` while the same snapshot carried
`spending.today = 272.361546` with a full provenance block (basis "derived",
formula, source, window). The modal rendered `$0.000` over a real $272 day.
The cloud half of that is clawmetry-cloud#2322; this is the renderer half, so
that an absent figure can never again be painted as free usage.

Static checks over the shipped bundle. The behavioural claim, that `cmMoney`
renders an absent figure and a measured zero differently, is a property of
`provenance.js` and is exercised there.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APP_JS = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
PROV_JS = (
    REPO / "clawmetry" / "static" / "js" / "provenance.js"
).read_text(encoding="utf-8")


def _optimizer_body() -> str:
    """`loadCostOptimizerData`, `//` comments stripped.

    The comments quote the old expression to explain why it was wrong, so
    matching raw text would assert against the explanation rather than the
    code.
    """
    i = APP_JS.index("function loadCostOptimizerData(")
    j = APP_JS.index("\nfunction ", i + 10)
    return "\n".join(
        ln for ln in APP_JS[i:j].splitlines() if not ln.lstrip().startswith("//")
    )


def test_the_provenance_module_is_still_the_one_place():
    """If this ever stops existing, the guards below are meaningless."""
    assert "window.cmMoney" in PROV_JS
    assert "cmProv" in PROV_JS


def test_cost_overview_does_not_coalesce_a_missing_figure_to_zero():
    body = _optimizer_body()
    assert "data.todayCost || 0" not in body, (
        "`|| 0` is back: a missing or null cost renders as a confident $0.000"
    )
    assert "data.projectedMonthlyCost || 0" not in body, (
        "`|| 0` is back on the projection"
    )


def test_cost_overview_renders_through_the_provenance_formatter():
    body = _optimizer_body()
    assert "cmMoney" in body, (
        "the cost overview does not use cmMoney, so an absent figure and a "
        "real $0.00 render identically again"
    )
    for key in ("todayCost", "projectedMonthlyCost"):
        assert re.search(rf"_costCell\(\s*'{key}'", body), (
            f"{key} is not rendered through the provenance-aware cell"
        )


def test_no_raw_tofixed_on_a_cost_in_the_overview():
    """`.toFixed` on a possibly-absent cost is the shape of the bug, whatever
    the coalesce looks like."""
    body = _optimizer_body()
    # Anchor on code, not on the section comment: the comments are stripped.
    i = body.index("cost-overview-header")
    overview = body[i:body.index("expensiveOps", i)]
    assert "todayCost.toFixed" not in overview
    assert "monthCost.toFixed" not in overview


def test_the_fallback_path_does_not_invent_a_second_unknown_convention():
    """A bundle without provenance.js must still not print $0.000 for a hole.
    It says 'not available', matching the module's own wording, rather than
    inventing a third way to say the same thing."""
    body = _optimizer_body()
    i = body.index("_costCell")
    cell = body[i:i + 700]
    assert "not available" in cell, (
        "the no-provenance fallback has no unknown branch, so older bundles "
        "keep printing a fabricated zero"
    )
