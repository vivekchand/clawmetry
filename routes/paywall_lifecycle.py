"""routes/paywall_lifecycle.py — the paywall beacons that reach the funnel.

The trial hard-block overlay (``clawmetry/static/js/app.js``) posts two
beacons to ``POST /api/paywall/event``:

    hard_block_view            the overlay was rendered to a user
    hard_block_checkout_click  that user clicked through to pay

Until 0.12.821 both were written ONLY to an in-process rolling store on the
user's own machine (``clawmetry/_paywall_events.py``, read back by
``/api/paywall/events/*``) and forwarded nowhere. Checked against cloud
analytics on 2026-09-06: zero rows for either, ever. So on the one surface
where somebody is looking straight at a price, we recorded nothing, and the
funnel could not separate "saw a price and declined" from "never reached
one" — the only question a pricing decision actually turns on.

This module is deliberately tiny and deliberately its OWN file. It was
first written inline in ``routes/entitlement.py``, which is ~47,700 lines;
every automated reader that samples the head of a file (Drift Bot among
them) concluded the function did not exist and reported the whole module as
missing from the repository. A 60-line concern that three different tools
need to find is a module, not a footnote in the largest file we ship.

Spec: REQ "Free Answer at the Gate, and a Visible Paywall"
(cd0b3dc3-ca5c-49ad-a4c0-dec01f122d12), AC-FREE-002; blueprint component
``#PaywallBeaconForwarder``.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# The overlay's two beacons, mapped to the lifecycle event names the cloud
# funnel understands. This is an ALLOWLIST, not a passthrough: the local
# rolling store keeps receiving every beacon, and only these two leave the
# machine. The cloud must carry the same two names in
# ``routes/install.py::_ALLOWED_EVENTS`` or they are dropped with no insert
# and no error.
PAYWALL_LIFECYCLE_EVENTS = {
    "hard_block_view": "paywall_view",
    "hard_block_checkout_click": "paywall_checkout_click",
}


def ping_paywall_lifecycle(body: dict) -> None:
    """Mirror the two paywall beacons into the anonymous lifecycle ping.

    Rides ``clawmetry.telemetry`` rather than a new channel so it inherits
    the existing privacy contract unchanged: an anonymous install id, no
    account, no email, no hostname, no workspace path, no runtime data, and
    every opt-out already honoured (``CLAWMETRY_NO_TELEMETRY``,
    ``DO_NOT_TRACK``, ``~/.clawmetry/notelemetry``). ``ping_once`` dedups on
    disk, so an overlay that re-renders on every background poll still sends
    one row per install — the funnel wants installs, not renders.

    Never raises: a telemetry failure must not change the 204 the beacon
    endpoint already returns.
    """
    try:
        event = PAYWALL_LIFECYCLE_EVENTS.get(str((body or {}).get("event", "")))
        if not event:
            return
        from clawmetry import telemetry as _telemetry

        try:
            from dashboard import __version__ as _ver
        except Exception:
            _ver = "unknown"
        _telemetry.ping_once(event, _ver)
    except Exception as exc:
        logger.debug("paywall_lifecycle: ping skipped: %s", exc)


__all__ = ["PAYWALL_LIFECYCLE_EVENTS", "ping_paywall_lifecycle"]
