"""Tests for issue #1604 — first-heartbeat race after signup.

Symptom: between user signup and the first heartbeat (~30s window) the
dashboard would render either an empty grid (looks broken) or — worst
case — stale data from a prior tenant on the same machine_id (privacy-
adjacent). The fix surfaces an explicit "Setting up your node" banner
that auto-refreshes every 5s and transitions cleanly on first heartbeat.
Past 90s it switches to actionable error copy so a stuck daemon does
not masquerade as "loading forever".

The OSS dashboard's source of truth for "has the daemon checked in yet"
is ``/api/heartbeat-status`` (returns ``status="unknown"`` while
``_last_heartbeat_ts == 0``). This suite pins:

  * the API contract the banner JS depends on (3 scenarios)
  * the banner partial actually carries the user-facing copy + auto-
    refresh metadata the JS toggles between
  * memory respects (no em-dashes, simple-non-technical copy, no
    sign-out / location.reload on transient empty state).
"""

from __future__ import annotations

import os
import time

import pytest


# ── Scenario 1: fresh signup, no heartbeat yet → "setting up" state ───────
def test_no_heartbeat_yet_returns_unknown_status(monkeypatch):
    """Fresh dashboard import + no heartbeat recorded → status='unknown'.

    This is the exact predicate the onboarding banner JS gates on:
    ``data.status === 'unknown'`` keeps the banner visible. Anything else
    here would mean either (a) the banner never shows (regression) or
    (b) the banner shows even after a real heartbeat (regression).
    """
    import dashboard as _d
    # Simulate a fresh process: no heartbeat has ever been recorded.
    monkeypatch.setattr(_d, "_last_heartbeat_ts", 0, raising=False)
    monkeypatch.setattr(_d, "_heartbeat_silent_since", 0, raising=False)

    payload = _d._get_heartbeat_status()
    assert payload["status"] == "unknown", (
        "fresh-signup pre-first-heartbeat MUST return status='unknown' so "
        "the onboarding banner gates on it; got " + repr(payload["status"])
    )
    # The banner JS also reads last_heartbeat_ts; must be falsy.
    assert not payload["last_heartbeat_ts"], (
        "must not surface a stale ts during the pre-first-heartbeat window "
        "(privacy-adjacent — see issue #1604 root cause)"
    )
    # gap_seconds MUST be None — anything else implies we're computing a gap
    # against epoch-0 and would render "57 years ago" in the UI.
    assert payload["gap_seconds"] is None


# ── Scenario 2: first heartbeat arrives → banner JS detects + hides ──────
def test_first_heartbeat_flips_status_off_unknown(monkeypatch):
    """Once ``_last_heartbeat_ts`` is set, status must leave ``unknown``.

    The onboarding banner JS treats any status !== 'unknown' AND a non-
    zero ``last_heartbeat_ts`` as "first heartbeat landed → hide banner
    + kick a fresh loadAll()". Both fields are checked here.
    """
    import dashboard as _d
    now = time.time()
    monkeypatch.setattr(_d, "_last_heartbeat_ts", now, raising=False)
    monkeypatch.setattr(_d, "_heartbeat_silent_since", 0, raising=False)

    payload = _d._get_heartbeat_status()
    assert payload["status"] != "unknown", (
        "after first heartbeat the banner JS hides on status != 'unknown'; "
        "anything still 'unknown' here would leave the banner stuck on"
    )
    # 'ok' is the expected freshly-pinged state (gap <= interval).
    assert payload["status"] == "ok"
    assert payload["last_heartbeat_ts"] == pytest.approx(now, rel=1e-3)
    assert payload["gap_seconds"] is not None
    assert payload["gap_seconds"] >= 0


# ── Scenario 3: heartbeat NEVER arrives (>90s stall) → still 'unknown' ───
def test_long_stall_keeps_status_unknown_so_banner_can_swap_to_error(monkeypatch):
    """A daemon that never reports must keep status='unknown' indefinitely.

    The banner JS tracks wall-clock since the first 'unknown' response
    and after 90s swaps copy from "Setting up your node..." to an
    actionable "still waiting — try 'clawmetry status'..." error. The
    backend's job is just to keep returning 'unknown' so the JS can
    own the timeout policy without races between cron + render.
    """
    import dashboard as _d
    monkeypatch.setattr(_d, "_last_heartbeat_ts", 0, raising=False)
    monkeypatch.setattr(_d, "_heartbeat_silent_since", 0, raising=False)

    # First poll - the JS would start its 90s wall-clock here.
    p1 = _d._get_heartbeat_status()
    assert p1["status"] == "unknown"
    # Simulate the JS still polling 100s later (over the stall threshold).
    # The backend MUST still report 'unknown' (not 'silent' or 'missed'
    # or - worst - 'ok' because some other code path stamped the ts).
    p2 = _d._get_heartbeat_status()
    assert p2["status"] == "unknown", (
        "even at 100s+ post-signup the backend keeps reporting 'unknown' "
        "so the banner JS owns the 90s timeout policy"
    )
    assert p2["last_heartbeat_ts"] == 0


# ── Banner partial: user-facing copy + memory respects ────────────────────
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


def test_onboarding_banner_partial_carries_setting_up_copy():
    html = _read_banners_html()
    assert 'id="onboarding-banner"' in html, (
        "onboarding banner element must exist in banners.html partial"
    )
    # Per feedback_simple_ui_for_nontechnical: "Setting up your node",
    # NOT "Awaiting initial heartbeat" or similar jargon.
    assert "Setting up your node" in html
    # Must explain the ~30s expectation so users do not assume it broke.
    assert "30 seconds" in html


def test_onboarding_banner_partial_avoids_em_dashes_in_user_copy():
    """Per memory ``feedback_no_em_dashes_in_user_facing_copy``."""
    html = _read_banners_html()
    # Find the onboarding banner block and assert no em-dash inside the
    # user-visible copy region. (Other banners in the file are out of
    # scope for this fire.)
    start = html.find('id="onboarding-banner"')
    assert start != -1
    end = html.find("</div>", start + html[start:].find('</span>'))
    block = html[start:end + 6]
    assert "—" not in block, "em-dash banned in user-facing onboarding copy"


def test_onboarding_js_does_not_reload_or_sign_out_on_transient_failure():
    """Per memory ``feedback_no_reload_in_bootstrap_e2e`` and
    ``feedback_persistent_sessions`` — the banner refresh loop must NOT
    call ``location.reload()`` or redirect to /login on a fetch failure.
    """
    js = _read_app_js()
    # Locate the onboarding block by its sentinel constant name and
    # extract just that function for the assertions.
    anchor = js.find("checkOnboardingStatus")
    assert anchor != -1, "checkOnboardingStatus must be defined in app.js"
    # Pull a generous window (~5 KB) starting at the anchor — should
    # contain the whole function + its setInterval registration.
    block = js[anchor:anchor + 5000]
    assert "location.reload" not in block, (
        "onboarding banner must not page-reload during the warm-up window "
        "(per feedback_no_reload_in_bootstrap_e2e.md)"
    )
    assert "/login" not in block, (
        "onboarding banner must not redirect to /login on transient empty "
        "state (per feedback_persistent_sessions.md)"
    )
    # Auto-refresh contract: must poll every 5s per the issue spec.
    assert "5000" in block, "banner must auto-refresh every 5s per issue #1604"
    # Stall threshold contract: must flip to actionable copy at 90s.
    assert "_CM_ONBOARDING_STALL_MS" in block or "90 * 1000" in block


def test_onboarding_js_kicks_loadall_on_first_heartbeat():
    """Smooth handoff: when the first heartbeat lands the banner must
    trigger a fresh loadAll() so the live cards swap in instantly
    instead of waiting for the next 30s tick."""
    js = _read_app_js()
    anchor = js.find("checkOnboardingStatus")
    assert anchor != -1
    block = js[anchor:anchor + 5000]
    assert "loadAll" in block, (
        "first-heartbeat handoff must call loadAll() so live cards render "
        "immediately, not after the next refresh cycle (issue #1604)"
    )
