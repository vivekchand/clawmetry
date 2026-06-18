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
handle 402 continue to work. ``required_tier`` is included so the UI can
route users to the *correct* upgrade CTA (Starter vs Pro vs Enterprise)
instead of a generic one.

Runtime gating
--------------
Some routes are scoped to a single runtime (e.g. the Claude Code dashboard)
or accept a runtime in a path/body parameter (e.g. the runtime ingest API).
For those, use :func:`gate_runtime` as a decorator when the runtime is known
at import time, or :func:`require_runtime` inline when it comes from the
request. Both share the same defensive contract as :func:`gate`: grace mode
+ free runtimes (``openclaw``, ``nemoclaw``) always pass through; any error
inside the entitlement lookup is swallowed and the request proceeds.
"""
from __future__ import annotations

from functools import wraps
from typing import Callable


def _required_tier(feature_key: str) -> str | None:
    """Minimum tier identifier that unlocks ``feature_key``.

    Returns a tier id from :mod:`clawmetry.entitlements` (e.g.
    ``"cloud_starter"``, ``"cloud_pro"``, ``"enterprise"``) or ``None`` for
    free features and unknown keys. Used to enrich the 402 body so the UI
    can render the right upgrade CTA without re-deriving tier logic in JS.
    Never raises: any lookup error returns ``None``.
    """
    try:
        from clawmetry import entitlements as _ent

        if feature_key in _ent.FREE_FEATURES:
            return None
        if feature_key in _ent.STARTER_FEATURES:
            return _ent.TIER_CLOUD_STARTER
        if feature_key in _ent.PRO_ONLY_FEATURES:
            return _ent.TIER_CLOUD_PRO
        if feature_key in _ent.ENTERPRISE_FEATURES:
            return _ent.TIER_ENTERPRISE
    except Exception:
        return None
    return None


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


def _required_tier_for_runtime(runtime: str) -> str | None:
    """Cheapest *purchasable* tier id that unlocks ``runtime``.

    Mirrors :func:`_required_tier` (the feature variant): the 402 body
    needs a target tier so the dashboard can render the correct upgrade
    CTA instead of a generic one. Defensive: any lookup error returns
    ``None`` so a flaky entitlement read still produces a valid 402 body.
    """
    try:
        from clawmetry import entitlements as _ent

        return _ent.min_tier_for_runtime(runtime)
    except Exception:
        return None


def require_runtime(runtime: str):
    """Inline gate for runtime-scoped routes that pick the runtime out of a
    path or body parameter at request time.

    Returns a Flask 402 ``upgrade_required`` response tuple when the install
    is not entitled to ``runtime``; returns ``None`` (let the request through)
    in grace mode, for free runtimes, or for any tier that already unlocks
    ``runtime``. Defensive: any error inside the entitlement read swallows
    to ``None`` so a flaky lookup never blocks a request that would otherwise
    succeed.

    Alias-tolerant: ``"claude-code"`` / ``"open-claw"`` / etc. are
    canonicalised via :func:`entitlements.canonical_runtime` before the
    entitlement check so an alias for a free runtime still passes through.

    The 402 body includes ``required_tier`` (the cheapest purchasable tier
    that unlocks the runtime) so the dashboard can render the correct
    upgrade CTA without re-deriving tier logic in JS.

    Typical usage::

        from clawmetry._gate import require_runtime

        @bp.route("/api/runtimes/<rt>/sessions")
        def list_sessions(rt: str):
            blocked = require_runtime(rt)
            if blocked is not None:
                return blocked
            ...
    """
    try:
        from flask import jsonify
        from clawmetry import entitlements as _ent

        raw = (runtime or "").strip().lower()
        try:
            rt = _ent.canonical_runtime(raw)
        except Exception:
            rt = raw
        en = _ent.get_entitlement()
        if en.allows_runtime(rt):
            return None
        return jsonify({
            "error": "upgrade_required",
            "runtime": rt,
            "tier": en.tier,
            "required_tier": _required_tier_for_runtime(rt),
            "hint": (
                "This runtime ships in the closed-source clawmetry-pro "
                "package. Install it with a license key or use Cloud Pro at "
                "clawmetry.com/pricing."
            ),
        }), 402
    except Exception:
        # A flaky entitlement read must never block the request path.
        return None


def gate_runtime(runtime_key: str) -> Callable:
    """Decorator factory: gate a Flask view on a specific runtime being
    entitled.

    Use when the runtime is known at decoration time (a route that only
    serves Claude Code data, say). For runtime-from-request routes, prefer
    :func:`require_runtime` inline so the gated value can vary per call.

    Mirrors :func:`gate` semantically: grace mode + free runtimes pass
    through; any entitlement-lookup error is swallowed and the request
    proceeds (the audit chain still records the call).
    """
    def deco(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            blocked = require_runtime(runtime_key)
            if blocked is not None:
                return blocked
            return fn(*args, **kwargs)
        return wrapper
    return deco
