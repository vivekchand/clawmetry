"""Every alert type the UI can create must reach a real evaluator.

Founder-reported 2026-08-15: the Alerts tab showed two rules toggled ON,
scoped "node-wide", reading "never triggered" — and they never could. The
tab POSTs the CLOUD vocabulary (``daily_spend``, ``node_offline``) while
``routes/alerts.py`` keyed its map on ``cost_daily``/``agent_offline``.
Neither matched, both fell through to the ``"anomaly"`` default, and
``dashboard.py``'s monitor loop has no ``anomaly`` branch. Silent zombie
rules: the operator believes they are covered and they are not.

The bug was only possible because three lists could drift apart with
nothing tying them together:

  1. ``EXAMPLE_RULES`` in ``clawmetry/static/js/alerts.js`` (what the UI sends)
  2. the routing tables in ``routes/alerts.py`` (where it goes)
  3. the ``rtype ==`` branches in ``dashboard.py`` (what actually evaluates)

These tests pin all three together. A new row on the Alerts tab now fails
CI until it is explicitly routed — to the in-process loop, to the daemon's
evaluator, or to the honest "no evaluator yet" bucket.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
ALERTS_JS = REPO / "clawmetry" / "static" / "js" / "alerts.js"
DASHBOARD_PY = REPO / "dashboard.py"


def _ui_alert_types():
    """Every ``alert_type`` in alerts.js EXAMPLE_RULES — i.e. every row a
    user can flip on."""
    src = ALERTS_JS.read_text(encoding="utf-8")
    block = re.search(r"const EXAMPLE_RULES = \[(.*?)\n  \];", src, re.S)
    assert block, "EXAMPLE_RULES not found in alerts.js — did the tab move?"
    types = re.findall(r"alert_type:\s*'([a-z_]+)'", block.group(1))
    assert types, "no alert_type entries parsed out of EXAMPLE_RULES"
    return types


def _loop_rtypes():
    """Every ``rtype == "..."`` branch in dashboard.py's monitor loop."""
    src = DASHBOARD_PY.read_text(encoding="utf-8")
    return set(re.findall(r'rtype == "([a-z_]+)"', src))


def test_every_ui_alert_type_is_routed():
    """No UI row may fall through to the silent-zombie default."""
    from routes import alerts

    unrouted = [
        t for t in _ui_alert_types()
        if t not in alerts._CLOUD_TO_LOCAL
        and t not in alerts._EVALUATOR_ONLY
        and t not in alerts.UNSUPPORTED_ALERT_TYPES
    ]
    assert not unrouted, (
        f"Alerts tab can create {unrouted}, which routes to no evaluator. "
        f"Add each to _CLOUD_TO_LOCAL (in-process branch), _EVALUATOR_ONLY "
        f"(daemon/DuckDB), or UNSUPPORTED_ALERT_TYPES (honest 'not yet')."
    )


def test_cloud_to_local_targets_all_have_a_loop_branch():
    """A key in _CLOUD_TO_LOCAL promises the in-process loop evaluates it.

    This is the exact assertion that would have caught the original bug:
    the map pointed ``agent_offline`` at ``agent_down``, which had no
    branch, so even the one type that *did* match the map was a no-op.
    """
    from routes import alerts

    branches = _loop_rtypes()
    missing = sorted({
        local for local in alerts._CLOUD_TO_LOCAL.values()
        if local not in branches
    })
    assert not missing, (
        f"_CLOUD_TO_LOCAL routes to {missing}, but dashboard.py's monitor "
        f"loop has no `rtype == \"<type>\"` branch for them — rules of that "
        f"type would save, render green, and never fire."
    )


def test_anomaly_is_never_a_routing_target():
    """``anomaly`` has no evaluator anywhere; it must not be a destination.

    It stays a legal *stored* value (mirrored _EVALUATOR_ONLY rules park
    there so the fleet loop skips them, and old rows still use it), but
    nothing may deliberately route a cloud type onto it as an evaluator.
    """
    from routes import alerts

    assert "anomaly" not in alerts._CLOUD_TO_LOCAL.values()
    assert "anomaly" not in alerts._LOCAL_EVALUABLE_TYPES


def test_local_evaluable_types_match_the_loop_exactly():
    """_LOCAL_EVALUABLE_TYPES drives the ``evaluator`` field the UI trusts.

    If it claims a type the loop dropped, the tab shows "armed" for a dead
    rule — the same lie in a new place.
    """
    from routes import alerts

    branches = _loop_rtypes()
    overclaimed = sorted(alerts._LOCAL_EVALUABLE_TYPES - branches)
    assert not overclaimed, (
        f"_LOCAL_EVALUABLE_TYPES claims {overclaimed} are evaluated in "
        f"dashboard.py, but no matching branch exists."
    )


@pytest.mark.parametrize("legacy,modern", [
    ("cost_daily", "daily_spend"),
    ("agent_offline", "node_offline"),
])
def test_legacy_aliases_still_map(legacy, modern):
    """Pre-0.12.711 clients POST the old spelling; both must land the same."""
    from routes import alerts

    assert alerts._CLOUD_TO_LOCAL[legacy] == alerts._CLOUD_TO_LOCAL[modern]
