"""Every alert that can reach the banner must have somewhere to go.

Founder-reported 2026-08-15, on a HIGH numbat finding pinned to the top of
the dashboard: "unable to understand what action I need to take... for the
first one I just see dismiss button — so what??"

The banner had a deep-link for exactly one alert type (``stuck_session``);
every other type, security findings included, offered only Dismiss. The fix
is ``_cmBannerDestination`` in static/js/app.js, which maps an alert to the
screen that answers it.

These tests pin the map to the set of types that can actually reach the
banner, so adding a new always-on monitor without a destination fails CI
instead of shipping another dead end.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_JS = REPO / "clawmetry" / "static" / "js" / "app.js"


def _destination_source():
    src = APP_JS.read_text(encoding="utf-8")
    start = src.index("function _cmBannerDestination(")
    end = src.index("\nasync function checkActiveAlerts(", start)
    return src[start:end]


def _handled_types():
    """Alert types the destination map explicitly answers."""
    body = _destination_source()
    return set(re.findall(r"type === '([a-z_]+)'", body))


def test_security_findings_have_a_destination():
    """The exact alert from the report must lead somewhere."""
    handled = _handled_types()
    assert "numbat_finding" in handled, (
        "A security finding can pin a red banner to the top of the dashboard. "
        "It must offer more than Dismiss."
    )
    assert "security_threat" in handled


def test_every_builtin_monitor_can_be_investigated():
    """No always-on monitor may fire into a dead end.

    BUILTIN_MONITORS is the list of things that can page the operator with
    no rule behind them — precisely the alerts they cannot anticipate, and
    so the ones that most need a next step.
    """
    from routes.alerts import BUILTIN_MONITORS

    handled = _handled_types()
    # 'security' (posture drift) and 'agent_error_rate'/'error_spike' fall
    # back to the banner text alone; they are node-wide states with no single
    # screen that explains them better than the message already does.
    exempt = {"security", "agent_error_rate", "error_spike"}
    orphans = sorted(
        m["alert_type"] for m in BUILTIN_MONITORS
        if m["alert_type"] not in handled and m["alert_type"] not in exempt
    )
    assert not orphans, (
        f"{orphans} can raise a banner with no rule behind them and offer no "
        f"way to investigate. Add a case to _cmBannerDestination in app.js."
    )


def test_stuck_session_deep_link_survived_the_refactor():
    """The one destination that already worked must not regress."""
    body = _destination_source()
    assert "stuck_session_" in body
    assert "goSession" in body
    assert "transcripts" in body


def test_destinations_point_at_real_tabs():
    """A destination that switches to a tab that doesn't exist is a dead end
    with extra steps."""
    body = _destination_source()
    tabs = set(re.findall(r"goTab\('([a-z-]+)'", body))
    assert tabs, "no goTab destinations parsed"
    tab_dir = REPO / "clawmetry" / "templates" / "tabs"
    for tab in tabs:
        assert (tab_dir / f"{tab}.html").exists(), (
            f"_cmBannerDestination routes to tab '{tab}', but "
            f"templates/tabs/{tab}.html does not exist."
        )


def test_security_destination_opens_the_findings_panel():
    """Landing on the Security tab is only useful if the finding is there.

    The findings panel is the piece that makes the Investigate button
    meaningful — before it, the Security tab could not display an ingested
    finding at all.
    """
    body = _destination_source()
    assert "loadSecurityFindings" in body
    assert "security-findings-panel" in body

    security_html = (REPO / "clawmetry" / "templates" / "tabs" / "security.html").read_text(encoding="utf-8")
    assert 'id="security-findings-panel"' in security_html
    assert 'id="security-findings-list"' in security_html

    app_js = APP_JS.read_text(encoding="utf-8")
    assert "/api/security-threats" in app_js, (
        "The findings panel must read the durable security_events log; the "
        "live-scan endpoint (/api/security/threats) never sees ingested "
        "findings."
    )
