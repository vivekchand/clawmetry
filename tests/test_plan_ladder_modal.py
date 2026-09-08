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


def _modal_copy():
    """The modal block with // comments stripped.

    test_modal_copy_rules asserts things about what the USER READS. Scanning
    the raw block also scans the comments, so an em dash in a note to the next
    engineer failed a test about user-facing copy. That is a false positive
    that trains people to weaken the rule; strip the comments instead."""
    out = []
    for line in _modal_block().split("\n"):
        # Naive but adequate here: these are single-line // notes, and a "//"
        # inside a string in this block would only ever ADD text to scan.
        idx = line.find("//")
        out.append(line if idx == -1 else line[:idx])
    return "\n".join(out)


def test_modal_shows_all_three_tiers_with_prices():
    block = _modal_block()
    assert "'Free', '$0 forever'" in block
    # Source of truth is the cloud Stripe catalog (cloud routes/api.py
    # _SUB_PRICING): starter 900 cents, pro 1900 cents. This assertion said
    # $29 for weeks after the values were correctly repriced to $19, so the
    # test was red on main and stopped being a signal. If a reprice lands,
    # change _SUB_PRICING first, then here.
    assert "starter: '$9'" in block and "pro: '$19'" in block, (
        "prices must live in the single _cmPlanPrices object and match "
        "cloud _SUB_PRICING (starter $9, pro $19)"
    )
    assert "'Starter'" in block and "'Pro'" in block


def test_modal_mentions_self_hosted_license_and_pricing_link():
    block = _modal_block()
    assert "license key" in block, "self-hosted option must be mentioned"
    assert "clawmetry.com/pricing" in block, "must link to the full pricing page"
    assert "desk device" in block


def test_modal_copy_rules():
    block = _modal_block()
    assert "—" not in _modal_copy(), "no em-dashes in user-facing copy"
    assert "no credit card" in block
    # The trial CTA + telemetry wiring must survive the redesign.
    assert "_cmRtPaywallCTA" in block and "paywall_view" in block
