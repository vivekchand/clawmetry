"""The runtime paywall modal must present the REAL plan ladder (mirrors the
live clawmetry.com/pricing page, verified 2026-06-09) so a logged-in user
can understand Free / Starter / Pro and the self-hosted license option at
the exact conversion moment, instead of a vague two-path card."""
import os


def _modal_block():
    appjs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "clawmetry", "static", "js", "app.js")
    src = open(appjs).read()
    i = src.find("function _cmShowRuntimePaywall")
    assert i != -1
    return src[i:i + 6000]


def test_modal_shows_all_three_tiers_with_prices():
    block = _modal_block()
    assert "'Free', '$0 forever'" in block
    assert "starter: '$9'" in block and "pro: '$29'" in block, (
        "prices must live in the single _cmPlanPrices object"
    )
    assert "'Starter'" in block and "'Pro'" in block


def test_modal_mentions_self_hosted_license_and_pricing_link():
    block = _modal_block()
    assert "license key" in block, "self-hosted option must be mentioned"
    assert "clawmetry.com/pricing" in block, "must link to the full pricing page"
    assert "desk device" in block


def test_modal_copy_rules():
    block = _modal_block()
    assert "—" not in block, "no em-dashes in user-facing copy"
    assert "no credit card" in block
    # The trial CTA + telemetry wiring must survive the redesign.
    assert "_cmRtPaywallCTA" in block and "paywall_view" in block
