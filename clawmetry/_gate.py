"""Shared 402 ``upgrade_required`` decorator for entitlement-gated routes.

Routes that implement a Pro or Enterprise feature mark themselves with
``@gate("feature_key")``. The decorator:

* In grace mode (default), allows everything through unchanged.
* In enforce mode (``CLAWMETRY_ENFORCE=1``), checks
  :func:`Entitlement.allows_feature` and returns HTTP 402 with a structured
  error body if the install is not on a tier that unlocks the feature.
* Never crashes the request if the entitlement read itself fails (defensive
  fallback: allow through). The audit chain still records the call.

Example::

    from clawmetry._gate import gate

    @bp_assets.route("/api/assets", methods=["GET"])
    @gate("asset_registry")
    def list_assets():
        ...

The error shape matches what ``routes/audit.py`` and ``routes/otel_export.py``
have been returning by hand for months, so existing front-ends that already
handle 402 continue to work. ``required_tier`` is included so the dashboard
can route the user to the *correct* upgrade CTA (Starter vs Pro vs
Enterprise) without re-deriving tier logic in JavaScript.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable


def _required_tier(feature_key: str) -> str | None:
    """Cheapest tier identifier that unlocks ``feature_key``.

    Thin pass-through to :func:`entitlements.min_tier_for_feature` so the
    402 body has the right "Upgrade to ___" target without the caller
    needing to know the catalogue. Returns ``None`` for free features,
    unknown keys, or any lookup error — never raises.
    """
    try:
        from clawmetry import entitlements as _ent

        return _ent.min_tier_for_feature(feature_key)
    except Exception:
        return None


def gate(feature_key: str) -> Callable:
    """Decorator factory: gate a Flask view on an entitlement feature key.

    Returns 402 ``upgrade_required`` JSON when the install lacks the key.
    The body always carries ``required_tier`` (the cheapest purchasable
    tier id that unlocks the feature, or ``None`` for free/unknown keys)
    so the dashboard can render the correct upgrade CTA directly.
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            try:
                from flask import jsonify
                from clawmetry import entitlements as _ent

                en = _ent.get_entitlement()
                if not en.allows_feature(feature_key):
                    return jsonify({
                        "error": "upgrade_required",
                        "feature": feature_key,
                        "tier": en.tier,
                        "required_tier": _required_tier(feature_key),
                        "hint": (
                            "This is a paid feature on clawmetry.com/pricing. "
                            "Upgrade or set CLAWMETRY_ENFORCE=0 to disable enforcement."
                        ),
                    }), 402
            except Exception:
                # Never let a flaky entitlement read break the request path.
                # The audit chain still records the call; the worst that
                # happens is a paid feature briefly runs on a Free tier.
                pass
            return fn(*args, **kwargs)
        return wrapper
    return deco
