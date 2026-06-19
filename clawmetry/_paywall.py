"""Shared 402 ``upgrade_required`` body builder for OSS stub blueprints.

The ``@gate`` decorator in :mod:`clawmetry._gate` covers routes whose
implementation lives in this OSS repo — it short-circuits paid features
with a structured 402 when ``CLAWMETRY_ENFORCE=1``. But several blueprints
in ``routes/`` are pure *OSS stubs* whose real implementation ships in the
closed-source ``clawmetry-pro`` package and registers via the
``clawmetry.extensions`` entry point when installed. When ``clawmetry-pro``
is NOT installed the stub blueprint registers in its place and returns 402
unconditionally — there is nothing on this install to call.

Those stubs each used to hand-roll their own dict literal. Three of them
(``routes/selfevolve.py``, ``routes/runtime_ingest.py``,
``routes/nemoclaw.py``) were missing ``tier``, and none of them carried
``required_tier`` — so the dashboard could not render the right
"Upgrade to ___" CTA off the 402 body, the way it already does for
``@gate`` 402s.

This module centralises the body so a stub blueprint just does::

    from clawmetry._paywall import upgrade_required_body

    @bp.route("/api/foo")
    def foo_stub():
        return jsonify(upgrade_required_body("self_evolve")), 402

and the wire shape stays in lockstep with what ``@gate`` returns. The
helper resolves the install's *current* tier and the feature's *minimum
unlock tier* at request time, with both lookups defensive — any
entitlements-module failure degrades to ``tier="oss"`` /
``required_tier=None`` so the body still serialises.
"""
from __future__ import annotations

import logging

logger = logging.getLogger("clawmetry.paywall")


_DEFAULT_HINT = (
    "This feature ships in the closed-source ``clawmetry-pro`` package. "
    "Install it with a valid license key, or use ClawMetry Cloud at "
    "clawmetry.com/pricing."
)


def upgrade_required_body(
    feature_key: str,
    *,
    hint: str | None = None,
) -> dict:
    """Build a 402 ``upgrade_required`` JSON body for an OSS stub route.

    Returns a dict whose shape matches ``@gate``'s 402 body so frontends can
    handle stub-blueprint 402s and gate-decorator 402s with the same code::

        {
            "error": "upgrade_required",
            "feature": "<feature_key>",
            "tier": "<current install tier>",
            "required_tier": "<min purchasable tier or None>",
            "hint": "<human-readable copy>",
        }

    ``feature_key`` is the entitlement feature id the stub stands in for
    (``self_evolve``, ``custom_runtime_ingest``, ...). It is echoed in the
    body verbatim so the UI can branch on it without re-deriving the route
    -> feature mapping.

    ``hint`` overrides the default copy. Pass a feature-specific message
    when the default ("install clawmetry-pro or use Cloud") is too generic
    -- e.g. the audit-log stub wants to mention Enterprise specifically.

    The current tier is read via :func:`entitlements.get_entitlement`; the
    minimum unlock tier via :func:`entitlements.min_tier_for_feature`. Both
    are wrapped in try/except so a flaky entitlements read collapses to
    ``tier="oss"`` / ``required_tier=None`` instead of crashing the request.

    Never raises.
    """
    tier = "oss"
    required_tier: str | None = None
    try:
        from clawmetry import entitlements as _ent

        try:
            tier = _ent.get_entitlement().tier
        except Exception as exc:
            logger.warning(
                "_paywall: tier read failed for feature %r: %s",
                feature_key,
                exc,
            )
        try:
            required_tier = _min_tier_for_feature(_ent, feature_key)
        except Exception as exc:
            logger.warning(
                "_paywall: min-tier lookup for feature %r failed: %s",
                feature_key,
                exc,
            )
    except Exception as exc:  # entitlements module itself unimportable
        logger.warning("_paywall: entitlements import failed: %s", exc)

    return {
        "error": "upgrade_required",
        "feature": feature_key,
        "tier": tier,
        "required_tier": required_tier,
        "hint": hint or _DEFAULT_HINT,
    }


def _min_tier_for_feature(ent_module, feature_key: str) -> str | None:
    """Map ``feature_key`` to the cheapest purchasable tier id that unlocks it.

    Thin wrapper over :func:`entitlements.min_tier_for_feature` -- the
    canonical purchasable-tier resolver also used by ``Entitlement.min_tier_for``,
    ``/api/entitlement/required-tier`` and :func:`clawmetry._gate._required_tier`
    -- so the feature->tier mapping lives in exactly one place and the OSS-stub
    402 body can never drift from the ``@gate`` 402 body. ``TIER_OSS`` (returned
    for free features) collapses to ``None`` so the body's ``required_tier`` is
    ``None`` for a free key and the UI short-circuits the upgrade CTA, matching
    the prior in-module if-tree exactly.

    Catalogue-set membership is read via ``getattr`` defaults on
    :func:`min_tier_for_feature` indirectly: a stubbed-out ``ent_module``
    without the canonical helper falls back to ``None`` via the swallowed
    ``AttributeError`` -- the body builder's outer try/except still degrades
    cleanly to ``required_tier=None``.
    """
    key = (feature_key or "").strip()
    if not key:
        return None
    resolver = getattr(ent_module, "min_tier_for_feature", None)
    if resolver is None:
        return None
    tier = resolver(key)
    if tier is None:
        return None
    if tier == getattr(ent_module, "TIER_OSS", "oss"):
        return None
    return tier
