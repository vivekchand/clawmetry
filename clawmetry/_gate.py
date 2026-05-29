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
handle 402 continue to work.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable


def gate(feature_key: str) -> Callable:
    """Decorator factory: gate a Flask view on an entitlement feature key.

    Returns 402 ``upgrade_required`` JSON when the install lacks the key.
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
