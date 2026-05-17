"""Tests for the "No OpenClaw or NVIDIA NemoClaw detected" empty-state.

Symptom: ClawMetry installs and registers as a node in cloud even when
the user has not installed any underlying agent. Every tab (Brain, AI
Model, Channels, Sessions) renders empty or shows stale data because
there is no agent producing events. Users see a broken-looking
dashboard and bounce.

The fix detects "no agent installed at all" at boot and surfaces an
explicit, persistent banner with install CTAs for both OpenClaw and
NVIDIA NemoClaw. Distinct from issue #1604 / PR #1631 (first-heartbeat
race) which handles the transient "agent installed but no heartbeat
yet" window — see the JS mutual-exclusion in ``checkAgentPresence``.

This suite pins five scenarios + the user-facing copy contract:
  1. No openclaw + no nemoclaw + empty local store → no-agent state
  2. OpenClaw installed + running, no first heartbeat yet → NOT the
     no-agent state (#1631's banner owns that window)
  3. OpenClaw installed + heartbeat received → normal dashboard
  4. NemoClaw installed only → normal dashboard
  5. Both installed → normal dashboard
plus the banner partial + JS contract assertions.
"""

from __future__ import annotations

import os

import pytest


# ── Shared monkeypatch helpers ───────────────────────────────────────────
def _reset_cache(monkeypatch):
    """Force a fresh detect_agent_install() call by clearing the 60s
    cache. Every scenario test depends on a fresh evaluation, otherwise
    test order would leak state across cases."""
    import dashboard as _d
    monkeypatch.setattr(
        _d, "_agent_presence_cache", {"ts": 0.0, "value": None}, raising=False
    )


def _force(monkeypatch, openclaw, nemoclaw, any_data):
    """Stub all three detectors so a test can drive the exact combo it
    wants without touching the real filesystem or DuckDB."""
    import dashboard as _d
    _reset_cache(monkeypatch)
    monkeypatch.setattr(_d, "_detect_openclaw_install", lambda: openclaw)
    monkeypatch.setattr(_d, "_detect_nemoclaw_install", lambda: nemoclaw)
    monkeypatch.setattr(_d, "_detect_any_local_data", lambda: any_data)


# ── Scenario 1: no openclaw + no nemoclaw + empty store → no-agent ──────
def test_no_agent_at_all_reports_no_agent_true(monkeypatch):
    """The exact predicate the banner JS gates on: ``no_agent === true``.

    If any of the three detectors returned True here it would mean either
    (a) the banner never shows on a truly empty machine (regression) or
    (b) we are silently masking a detection bug — both have caused real
    user-visible "broken dashboard" reports.
    """
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=False, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is True, (
        "with no openclaw + no nemoclaw + no local data the banner JS "
        "needs no_agent=true to render the empty state; got " + repr(payload)
    )
    assert payload["openclaw_detected"] is False
    assert payload["nemoclaw_detected"] is False
    assert payload["any_data"] is False
    assert payload["signals"] == [], (
        "signals list MUST be empty when nothing is detected so the UI "
        "does not display a misleading 'detected via X' tag"
    )


# ── Scenario 2: openclaw installed but heartbeat hasn't landed yet ──────
def test_openclaw_installed_but_no_heartbeat_is_NOT_no_agent_state(monkeypatch):
    """The first-heartbeat race is #1631's territory, NOT this PR's.

    If openclaw IS installed (PID file, workspace dir, anything) we must
    return ``no_agent=false`` so the persistent no-agent banner stays
    hidden and the transient "Setting up your node" banner from #1631
    owns the ~30s warm-up window. Showing both would be visually
    confusing and contradict each other.
    """
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=False, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False, (
        "openclaw installed → no_agent MUST be false even if no heartbeat "
        "yet (issue #1604 / PR #1631 owns that transient window)"
    )
    assert payload["openclaw_detected"] is True
    assert "openclaw" in payload["signals"]


# ── Scenario 3: openclaw installed + heartbeat → normal dashboard ───────
def test_openclaw_installed_and_data_present_is_normal_dashboard(monkeypatch):
    """The steady-state happy path. ``no_agent=false`` and BOTH the
    openclaw_detected flag AND the local-store signal must be set so
    the system-health card can show a green "OpenClaw OK" pill.
    """
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=False, any_data=True)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["openclaw_detected"] is True
    assert payload["any_data"] is True
    assert "openclaw" in payload["signals"]
    assert "local_data" in payload["signals"]


# ── Scenario 4: nemoclaw installed only → normal dashboard ──────────────
def test_nemoclaw_only_install_is_normal_dashboard(monkeypatch):
    """A pure NemoClaw user (no OpenClaw) must NOT see the no-agent
    banner. Per memory ``feedback_em_style_judgment`` we treat OpenClaw
    and NemoClaw as equal first-class agents — neither's absence alone
    triggers the empty state.
    """
    import dashboard as _d
    _force(monkeypatch, openclaw=False, nemoclaw=True, any_data=False)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False, (
        "nemoclaw alone is enough to hide the no-agent banner — they are "
        "treated as equal first-class agents (feedback_em_style_judgment)"
    )
    assert payload["nemoclaw_detected"] is True
    assert "nemoclaw" in payload["signals"]


# ── Scenario 5: both installed → normal dashboard ───────────────────────
def test_both_agents_installed_is_normal_dashboard(monkeypatch):
    """Belt-and-braces: both signals true MUST keep no_agent=false and
    surface BOTH in the signals list so the UI can attribute data
    correctly across the two agents.
    """
    import dashboard as _d
    _force(monkeypatch, openclaw=True, nemoclaw=True, any_data=True)
    payload = _d.detect_agent_install()
    assert payload["no_agent"] is False
    assert payload["openclaw_detected"] is True
    assert payload["nemoclaw_detected"] is True
    assert set(payload["signals"]) == {"openclaw", "nemoclaw", "local_data"}


# ── Cache contract: TTL prevents storming the FS on every tab switch ────
def test_detection_result_is_cached_for_60s(monkeypatch):
    """Every tab switch on the dashboard pings ``/api/agent-presence`` —
    without a cache that would re-stat the workspace + shell out to
    ``shutil.which`` on every page load. The 60s TTL is the contract.
    """
    import dashboard as _d
    _reset_cache(monkeypatch)
    calls = {"openclaw": 0, "nemoclaw": 0, "data": 0}

    def _oc():
        calls["openclaw"] += 1
        return False

    def _nc():
        calls["nemoclaw"] += 1
        return False

    def _da():
        calls["data"] += 1
        return False

    monkeypatch.setattr(_d, "_detect_openclaw_install", _oc)
    monkeypatch.setattr(_d, "_detect_nemoclaw_install", _nc)
    monkeypatch.setattr(_d, "_detect_any_local_data", _da)

    # First call: detectors run.
    _d.detect_agent_install()
    assert calls == {"openclaw": 1, "nemoclaw": 1, "data": 1}
    # Second call within TTL: detectors must NOT run again.
    _d.detect_agent_install()
    _d.detect_agent_install()
    assert calls == {"openclaw": 1, "nemoclaw": 1, "data": 1}, (
        "cache MUST suppress re-running the detectors within the 60s TTL — "
        "otherwise every tab switch storms the filesystem"
    )


# ── Banner partial + JS contract ────────────────────────────────────────
def _read_banners_html():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "clawmetry", "templates", "partials", "banners.html")
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _read_app_js():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(here, "clawmetry", "static", "js", "app.js")
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def test_no_agent_banner_partial_carries_both_install_ctas():
    """User-facing copy must name BOTH agents and offer install links
    for each. Per memory ``feedback_em_style_judgment`` we do NOT pick
    one over the other — listing both lets the user choose.
    """
    html = _read_banners_html()
    assert 'id="no-agent-banner"' in html, (
        "no-agent banner element must exist in banners.html partial"
    )
    # Copy MUST name both agents — the entire point of this PR.
    assert "OpenClaw" in html
    assert "NemoClaw" in html or "NVIDIA NemoClaw" in html
    # Both install CTAs must be present and clickable.
    assert "Install OpenClaw" in html
    assert "Install NVIDIA NemoClaw" in html or "Install NemoClaw" in html


def test_no_agent_banner_avoids_em_dashes_in_user_copy():
    """Per memory ``feedback_no_em_dashes_in_user_facing_copy``."""
    html = _read_banners_html()
    start = html.find('id="no-agent-banner"')
    assert start != -1
    # Grab a generous window covering the entire banner block.
    block = html[start:start + 2500]
    # Slice off after the closing </div> for THIS banner so we don't
    # accidentally lint siblings.
    end_marker = "<!-- Onboarding"
    end = block.find(end_marker)
    if end != -1:
        block = block[:end]
    assert "—" not in block, (
        "em-dash banned in user-facing no-agent banner copy "
        "(feedback_no_em_dashes_in_user_facing_copy.md)"
    )


def test_no_agent_js_does_not_reload_or_sign_out_on_transient_failure():
    """Per memory ``feedback_no_reload_in_bootstrap_e2e`` +
    ``feedback_persistent_sessions``: never page-reload or redirect to
    /login when ``/api/agent-presence`` returns transiently bad data.
    """
    js = _read_app_js()
    anchor = js.find("checkAgentPresence")
    assert anchor != -1, "checkAgentPresence must be defined in app.js"
    block = js[anchor:anchor + 5000]
    assert "location.reload" not in block, (
        "no-agent banner must not page-reload on transient empty state "
        "(feedback_no_reload_in_bootstrap_e2e.md)"
    )
    assert "/login" not in block, (
        "no-agent banner must not redirect to /login on transient empty "
        "state (feedback_persistent_sessions.md)"
    )


def test_no_agent_js_is_mutually_exclusive_with_first_heartbeat_banner():
    """If openclaw or nemoclaw IS detected (and we're just in the
    first-heartbeat warm-up window), the no-agent banner must hide and
    let #1631's onboarding-banner own that scenario. The two must
    never both display at once.
    """
    js = _read_app_js()
    anchor = js.find("checkAgentPresence")
    assert anchor != -1
    block = js[anchor:anchor + 5000]
    # When no_agent is true the JS hides the onboarding-banner so we
    # don't double up. Look for the explicit handoff.
    assert "onboarding-banner" in block, (
        "mutual-exclusion: when no_agent=true the JS must explicitly "
        "hide the onboarding-banner so the two banners never stack"
    )
    # And inversely it must reference its own element id.
    assert "no-agent-banner" in block


def test_no_agent_js_polls_at_least_every_minute():
    """The detection result is cached 60s server-side; the client poll
    cadence should match so users who install an agent mid-session see
    the banner disappear within a minute, not on the next page load.
    """
    js = _read_app_js()
    anchor = js.find("checkAgentPresence")
    assert anchor != -1
    block = js[anchor:anchor + 5000]
    assert "60000" in block, (
        "no-agent banner must re-poll at the 60s server-cache cadence so "
        "an agent installed mid-session clears the banner within ~1 min"
    )
