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
    click interception depends on."""
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
    # Upgrade CTA points at the cloud upgrade flow with the harness attached.
    assert "app.clawmetry.com/upgrade" in body
    assert "source=runtime-switcher" in body
    # Both buttons present: dismiss + start trial.
    assert "_cmRtPaywallCancel" in body
    assert "Start free trial" in body
