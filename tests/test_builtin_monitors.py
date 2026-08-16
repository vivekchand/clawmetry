"""The always-on monitor list must match what actually fires.

Founder-reported 2026-08-15: two red banners sat above an Alerts tab where
every rule was toggled off — "how did it alert when all of the alerts are
disabled??". The monitors that produced them are hardcoded ``_fire_alert``
calls with no rule lookup and no enabled check, and nothing in the product
listed them. ``BUILTIN_MONITORS`` is that list.

A published list that silently drifts from the code is worse than no list:
it becomes a confident wrong answer. These tests keep it honest in both
directions — every documented monitor must exist in the code, and the doc
must not invent monitors that don't.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Every module that may call _fire_alert with a hardcoded alert_type.
_SOURCES = [
    REPO / "dashboard.py",
    REPO / "routes" / "infra.py",
    REPO / "routes" / "health.py",
    REPO / "routes" / "usage.py",
]


def _fired_alert_types():
    """Scrape ``alert_type="..."`` from every _fire_alert call site."""
    found = set()
    for path in _SOURCES:
        if not path.exists():
            continue
        found |= set(
            re.findall(r'alert_type=["\']([a-z_]+)["\']',
                       path.read_text(encoding="utf-8"))
        )
    assert found, "no alert_type call sites found — did _fire_alert move?"
    return found


def test_every_documented_monitor_actually_fires():
    """No phantom entries: each listed monitor exists as a real call site."""
    from routes.alerts import BUILTIN_MONITORS

    fired = _fired_alert_types()
    phantom = sorted(
        m["alert_type"] for m in BUILTIN_MONITORS
        if m["alert_type"] not in fired
    )
    assert not phantom, (
        f"BUILTIN_MONITORS advertises {phantom}, but nothing calls "
        f"_fire_alert with those types. Remove them or fix the name — the "
        f"Alerts tab renders this list as fact."
    )


def test_every_hardcoded_fire_is_documented():
    """No hidden monitors: anything that can page the user is listed.

    This is the assertion that would have caught the original complaint.
    ``numbat_finding`` and ``heartbeat_silent`` both fired into the banner
    while the Alerts tab showed nothing that could explain either one.
    """
    from routes.alerts import BUILTIN_MONITORS

    documented = {m["alert_type"] for m in BUILTIN_MONITORS}
    # Types raised only by user-created rules are covered by the Alerts tab
    # itself, so they need no builtin entry.
    rule_driven = {"stuck_session", "unproductive_burn", "budget_abort",
                   "authority_violation", "spike", "token_spike",
                   "session_cost", "daily_threshold_breached"}
    undocumented = sorted(_fired_alert_types() - documented - rule_driven)
    assert not undocumented, (
        f"{undocumented} can fire a banner with no alert rule behind it and "
        f"is not in BUILTIN_MONITORS, so the Alerts tab cannot explain it. "
        f"Add an entry (or add it to rule_driven if a rule really gates it)."
    )


def test_monitor_entries_are_well_formed():
    """The tab renders these fields directly; none may be blank."""
    from routes.alerts import BUILTIN_MONITORS

    seen = set()
    for m in BUILTIN_MONITORS:
        for field in ("alert_type", "label", "watches", "channels", "source"):
            assert m.get(field), f"{m.get('alert_type')} is missing {field}"
        assert m["alert_type"] not in seen, f"duplicate {m['alert_type']}"
        seen.add(m["alert_type"])
        assert isinstance(m["channels"], list) and m["channels"]


def test_builtins_endpoint_is_not_paywalled():
    """Knowing what watches you is not a paid feature.

    Matches the decorator line specifically — the function's own docstring
    mentions ``@gate`` while explaining why it has none.
    """
    src = (REPO / "routes" / "alerts.py").read_text(encoding="utf-8")
    route = src.index('"/api/alerts/builtins"')
    decorators = src[src.rindex("\n@", 0, route):route]
    assert "@gate(" not in decorators, (
        "/api/alerts/builtins is gated — the always-on monitors fire for "
        "every user, so every user must be able to see them."
    )
