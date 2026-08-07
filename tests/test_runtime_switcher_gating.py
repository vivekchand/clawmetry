"""Snapshot tests for the runtime-switcher gating UI (issue #2293).

The runtime switcher in the dashboard header is the visible enforcement
surface for harness gating: under enforce, paid runtimes must render with a
🔒 affordance, clicking one must open the upgrade paywall, and the runtime
filter must NOT switch. These tests pin the load-bearing code paths in
``clawmetry/static/js/app.js`` so a refactor that removes the lock rendering
or the click interception is caught loudly.

Pure-Python snapshot tests rather than Playwright/jsdom because the test
runner has no browser engine, and the JS module is plain ES5 (no bundling) —
the code paths are visible to a regex scan. The wire contract on the data
side (``/api/runtimes`` returns ``locked=True`` for paid runtimes under
enforced OSS) is covered by ``tests/test_routes_runtimes.py``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

APP_JS = Path(__file__).resolve().parents[1] / "clawmetry" / "static" / "js" / "app.js"


@pytest.fixture(scope="module")
def app_js() -> str:
    return APP_JS.read_text(encoding="utf-8")


# ── data wiring ──────────────────────────────────────────────────────────────


def test_switcher_fetches_api_runtimes(app_js):
    """Switcher must fetch /api/runtimes to discover locked runtimes."""
    assert "/api/runtimes" in app_js
    assert "_cmLockedRuntimes" in app_js


# ── lock affordance: paid options render with 🔒 ─────────────────────────────


def test_switcher_renders_lock_emoji_for_locked_runtimes(app_js):
    """Locked runtimes render with a 🔒 prefix in the switcher dropdown.
    Under grace mode ``_cmLockedRuntimes`` is empty so nothing locks; under
    enforce + OSS the /api/runtimes response populates it and the locked
    branch fires."""
    assert "🔒" in app_js, "lock emoji missing from switcher JS"
    # The lock prefix and "Upgrade" hint must be inside an `_cmLockedRuntimes`
    # branch — i.e. only locked runtimes render this way.
    pattern = re.compile(
        r"_cmLockedRuntimes\[[^\]]+\][^}]*?🔒.*?Upgrade",
        re.DOTALL,
    )
    assert pattern.search(app_js), "lock affordance not gated by _cmLockedRuntimes"


# ── click intercept: paywall opens, runtime does NOT switch ──────────────────


def test_switcher_change_handler_intercepts_locked_clicks(app_js):
    """The header switcher's onChange handler must (1) revert the selection
    and (2) show the paywall when the chosen runtime is locked — instead of
    propagating the change to ``_cmSetRuntimeFilter``. Pins the
    runtime-does-not-switch invariant from issue #2293."""
    pattern = re.compile(
        r"function\s+_cmOnGlobalRuntimeChange\s*\([^)]*\)\s*\{(.*?)\n\}",
        re.DOTALL,
    )
    m = pattern.search(app_js)
    assert m, "_cmOnGlobalRuntimeChange not found"
    body = m.group(1)
    # Locked-branch guard must precede _cmSetRuntimeFilter so we don't switch.
    assert "_cmLockedRuntimes[val]" in body, "locked-runtime guard missing"
    assert "_cmShowRuntimePaywall" in body, "paywall not opened on locked click"
    # The locked branch must return before _cmSetRuntimeFilter is called.
    locked_idx = body.find("_cmShowRuntimePaywall")
    setfilter_idx = body.find("_cmSetRuntimeFilter")
    assert locked_idx >= 0
    assert setfilter_idx > locked_idx, (
        "locked guard does not return before _cmSetRuntimeFilter — "
        "runtime would still switch"
    )


# ── paywall content: harness label + upgrade CTA ─────────────────────────────


def test_runtime_paywall_overlay_present(app_js):
    """``_cmShowRuntimePaywall`` builds the overlay with the upgrade CTA and
    a paywall_view telemetry beacon — pins the contract the runtime-switcher
    click interception depends on.

    Founder spec (2026-07-30): a locked runtime must lead to sign-in -> trial
    license -> unlocked runtimes right here, never a pricing tab or an
    external cloud redirect (a self-hosted user choosing a trial must not be
    bounced to a cloud account page — that's the whole point of self-host).
    This test used to assert the OLD `app.clawmetry.com/upgrade` redirect,
    which had already been replaced by the local email+code trial flow below
    without the test being updated (live-hit 2026-08-06: an actual redirect
    regression on the separate bottom-right runtime-chip menu went unnoticed
    because this file only pinned the (correct) header dropdown's overlay,
    not the second switch point — see test_runtime_switcher_gating.py's
    chip-menu test)."""
    pattern = re.compile(
        r"function\s+_cmShowRuntimePaywall\s*\([^)]*\)\s*\{(.*?)\nfunction\s",
        re.DOTALL,
    )
    m = pattern.search(app_js)
    assert m, "_cmShowRuntimePaywall not found"
    body = m.group(1)
    # Telemetry: paywall_view event for funnel attribution.
    assert "paywall_view" in body
    assert "/api/paywall/event" in body
    # The CTA drives a local sign-in -> trial flow, not an external redirect.
    assert "/api/cloud-cta/send-otp" in body
    assert "/api/trial/activate" in body
    assert "app.clawmetry.com/upgrade" not in body, (
        "the in-dashboard paywall must not bounce a self-hosted user to the "
        "cloud account page — it activates the trial locally"
    )
    # Both buttons present: dismiss + start trial.
    assert "_cmRtPaywallCancel" in body
    assert "Start 7-day free trial" in body


def test_runtime_chip_locked_click_opens_local_paywall_not_cloud_redirect(app_js):
    """The bottom-right runtime chip (a second, self-described 'mirror' of
    the header switcher) must intercept a locked-runtime click the same way
    the header switcher does: open the local ``_cmShowRuntimePaywall`` modal,
    not bounce straight to the cloud account site.

    Live-hit 2026-08-06 (self-hosted trial user, reported directly): clicking
    a locked runtime in this chip's menu opened
    ``app.clawmetry.com/upgrade?source=runtime_chip`` in a new tab instead —
    a self-hosted user trying to start a local trial got redirected to a
    cloud account page with no bearing on their local install. The header
    dropdown's onChange handler (``_cmOnGlobalRuntimeChange``, tested above
    in ``test_switcher_change_handler_intercepts_locked_clicks``) already
    did this correctly; the chip's own click handler diverged."""
    pattern = re.compile(
        r"m\.addEventListener\('click',\s*function\s*\(ev\)\s*\{(.*?)\n\s*\}\);",
        re.DOTALL,
    )
    m = pattern.search(app_js)
    assert m, "runtime-chip menu click handler not found"
    body = m.group(1)
    assert "data-locked" in body, "locked-item branch missing from chip click handler"
    assert "_cmShowRuntimePaywall" in body, (
        "chip's locked-click branch must open the local paywall modal, "
        "same as the header switcher"
    )
    assert "window.open" not in body and "app.clawmetry.com" not in body, (
        "chip must not redirect a locked click to the cloud site — that "
        "strands a self-hosted user trying to start a local trial"
    )
