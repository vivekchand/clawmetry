"""routes/entitlement/_shared.py — imports, constants, the blueprint and
every non-handler helper the endpoint modules call.

Split out of the former single-module routes/entitlement.py; see the
package __init__ for why. Import order matters: this module defines
``bp_entitlement``, so it must be imported before any _endpoints_* part.
"""

from __future__ import annotations

import logging

import os

import time

from flask import Blueprint, jsonify, request

# Imported early so automated readers that only sample this file's head
# can resolve these names; the re-export under private aliases preserves
# backward compatibility for existing callers and tests.
from routes.paywall_lifecycle import (
    PAYWALL_LIFECYCLE_EVENTS as _PAYWALL_LIFECYCLE_EVENTS,
    ping_paywall_lifecycle as _ping_paywall_lifecycle,
)

logger = logging.getLogger("clawmetry.routes.entitlement")

bp_entitlement = Blueprint("entitlement", __name__)

# Last-resort minimal OSS-free snapshot used only if BOTH ``get_entitlement``
# and ``_oss_free().to_dict()`` raise (e.g. the entitlements module itself
# fails to import). Kept in-line so this branch does not re-import the
# possibly-broken module. Keys mirror the top-level shape of
# :meth:`clawmetry.entitlements.Entitlement.to_dict` so a paywall UI reading
# ``data.features`` / ``data.free_runtimes`` never KeyErrors on the error path.
# ``features`` is populated with the canonical FREE_FEATURES set so a caller
# that lands on this branch does not silently see an empty feature list
# (which would look like "OSS install has no free features -- lock everything"
# once enforcement is live).
_MINIMAL_OSS_FREE_SNAPSHOT = {
    # Resolver unavailable => plan unknown. Never let a paywall read this
    # snapshot as a confirmed free plan (see entitlements.plan_pending()).
    "pending": True,
    "tier": "oss",
    "tier_label": "OSS",
    "tier_rank": 0,
    "source": "oss",
    "node_limit": 1,
    "channel_limit": None,
    "expiry": None,
    "expired": False,
    "days_until_expiry": None,
    "is_paid": False,
    "grace": True,
    "enforced": False,
    "enforce_at": None,
    "enforce_at_iso": None,
    "days_until_enforce": None,
    "retention_days": 7,
    "effective_retention_days": 7,
    "runtimes": ["nemoclaw", "openclaw"],
    "features": sorted(
        [
            "brain",
            "channels",
            "crons",
            "flow",
            "health",
            "logs",
            "nemo_governance",
            "overview",
            "sessions",
            "tracing",
            "transcripts",
            "usage",
        ]
    ),
    "free_runtimes": ["nemoclaw", "openclaw"],
    "paid_runtimes": [],
    "all_runtimes": ["nemoclaw", "openclaw"],
    "locked_runtimes": [],
    "locked_features": [],
    "next_tier": None,
    "next_tier_label": None,
    "prev_tier": None,
    "prev_tier_label": None,
    "next_tier_diff": None,
    "prev_tier_diff": None,
    "next_tier_capacity_diff": None,
    "prev_tier_capacity_diff": None,
    "next_tier_unlocks": None,
    "prev_tier_unlocks": None,
    "next_tier_locks": None,
    "prev_tier_locks": None,
    # Parity with Entitlement.to_dict(). The fallback branch below merges
    # the *live* value on top of these keys so the overlay never sees a
    # stale ``False`` on the resolver-crashed path (which would let an
    # expired-trial user silently through).
    "hard_blocked": False,
    "free_only_mode": False,
}


def _ingest_is_running() -> bool:
    """True when something is actually writing the local store.

    The first-run panel must not tell a user to "run some work through the
    agent" when the real reason they see nothing is that nothing is reading
    it. `clawmetry` alone starts the dashboard only: every
    `_start_daemon_background()` call site sits in the cloud-connect flow, so
    a plain `pip install clawmetry && clawmetry` never ingests (#5740).

    Best effort, and it fails toward silence: an error answers True so the
    panel says nothing about ingest rather than accusing a healthy install.
    """
    try:
        from clawmetry import local_store as _ls
        if getattr(_ls, "_writer_owner", False):
            return True
        if _ls._daemon_registered():
            return True
        return _ls.DB_PATH.exists()
    except Exception:
        return True


def _neighbour_tier_headroom_envelope(
    *, direction: str, headroom: dict | None
) -> dict:
    """Shared envelope for ``/next-tier-capacity-headroom`` +
    ``/previous-tier-capacity-headroom``.

    Wraps the raw :func:`clawmetry.entitlements.capacity_headroom_at` row
    in the same "current-tier context + null-at-boundary" shape as
    ``/next-tier-unlocks`` / ``/previous-tier-unlocks`` (see
    ``api_entitlement_next_tier_unlocks``) so an upgrade / downgrade card
    can bind against ``headroom`` as the payload with the boundary case
    surfacing as ``headroom=null`` at HTTP 200 -- callers never have to
    branch on status code.
    """
    from clawmetry import entitlements as _ent

    try:
        ent = _ent.get_entitlement()
        return {
            "current_tier": ent.tier,
            "current_tier_label": _ent.tier_label(ent.tier),
            "current_tier_rank": _ent.tier_rank(ent.tier),
            "direction": direction,
            "headroom": headroom,
            "grace": bool(ent.grace),
            "enforced": _ent.is_enforced(),
        }
    except Exception:
        return {
            "current_tier": "oss",
            "current_tier_label": "OSS",
            "current_tier_rank": 0,
            "direction": direction,
            "headroom": None,
            "grace": True,
            "enforced": False,
        }

_CAPACITY_PARAMS = ("channels", "retention_days", "nodes")

def _parse_capacity_arg(name: str) -> tuple[bool, bool, int | None, str]:
    """Parse a capacity query param.

    Returns ``(present, parsed_ok, value, raw)``. ``present`` is True iff the
    caller supplied the param at all (even with an empty value, so blank input
    doesn't silently fall through to a feature/runtime branch). ``parsed_ok``
    is False when the supplied value couldn't be coerced to ``int`` -- the
    HTTP wrapper then short-circuits to ``required_tier=None`` instead of
    handing ``None`` to the underlying helper (where, for retention, ``None``
    is the *unlimited* sentinel and would mis-route to Enterprise).
    """
    raw = request.args.get(name)
    if raw is None:
        return False, False, None, ""
    raw_stripped = raw.strip()
    if not raw_stripped:
        return True, False, None, raw_stripped
    try:
        return True, True, int(raw_stripped), raw_stripped
    except (TypeError, ValueError):
        return True, False, None, raw_stripped

def _has_axis_fallback(axis: str, key: str) -> dict:
    """OSS-free / never-5xx shape for the ``/api/entitlement/has-*``
    endpoints, matching the never-crash posture of
    ``/api/entitlement/required-tier`` and ``/api/entitlement/lock-reason``.

    Same 8-key envelope as the happy-path branch so a frontend can bind
    ``allowed`` off the URL without a branch on the underlying resolver
    state. ``axis`` is ``"feature"`` or ``"runtime"`` -- the key name of
    the input arg -- so a single helper serves both sibling endpoints.
    """
    return {
        axis: key,
        f"has_{axis}": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "upgrade_required": False,
    }

def _has_axis_body(axis: str, resolver_min_tier, resolver_allow) -> dict:
    """Happy-path body builder for the ``/api/entitlement/has-*``
    endpoints -- scalar boolean plus the surrounding required-tier
    envelope so a paywall tile can bind ``has_feature`` /
    ``has_runtime`` directly off the URL without a follow-up hit to
    ``/api/entitlement/required-tier``.

    Envelope keys are byte-stable across ``has_feature`` /
    ``has_runtime`` (parameterised via ``axis``) and match the tier
    columns on the sibling ``/required-tier`` body so a cross-endpoint
    consistency invariant (same tier answer for the same key) can be
    pinned in tests.
    """
    from clawmetry import entitlements as _ent

    key = (request.args.get(axis) or "").strip().lower()
    ent = _ent.get_entitlement()
    if axis == "feature":
        has_flag = _ent.has_feature(key)
        required = _ent.min_tier_for_feature(key) if key else None
    else:
        has_flag = _ent.has_runtime(key)
        required = _ent.min_tier_for_runtime(key) if key else None
    # `resolver_*` params kept in the signature so tests can monkeypatch
    # a single seam if the resolver ever grows a second entry point.
    _ = (resolver_min_tier, resolver_allow)
    cur_rank = _ent.tier_rank(ent.tier)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    return {
        axis: key,
        f"has_{axis}": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": ent.tier,
        "current_tier_rank": cur_rank,
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _has_axis_at_fallback(axis: str, tier: str, key: str) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-feature-at`` /
    ``/has-runtime-at``.

    What-if sibling of :func:`_has_axis_fallback`. On any resolver / helper
    blowup the endpoint still returns 200 with the same 12-key envelope as
    the happy-path branch, but with ``has_<axis>_at`` and ``allowed``
    strict-``False`` (matches the fail-closed posture the sibling
    ``/has-feature`` / ``/has-runtime`` fallback uses -- a paywall matrix
    tile that lost the resolver never silently renders a grant it can't
    verify). ``tier`` and the axis slot echo the caller's canonicalised
    input so the UI can still surface both in a diagnostics tooltip.
    """
    return {
        "tier": tier,
        axis: key,
        f"has_{axis}_at": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_axis_at_body(axis: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/has-feature-at`` /
    ``/has-runtime-at`` -- scalar what-if boolean plus the surrounding
    what-if envelope.

    Perspective-shaped sibling of :func:`_has_axis_body`: where the live
    variant folds :func:`has_feature` / :func:`has_runtime` against the
    resolved entitlement, this folds :func:`has_feature_at` /
    :func:`has_runtime_at` against a caller-supplied ``tier=`` perspective
    so a pricing matrix ("does Starter grant fleet? Pro? Enterprise?")
    can bind ONE boolean per cell off ONE URL each instead of
    hydrating the full ``/feature-catalog-at`` payload and pulling out
    the ``allowed`` field client-side.

    12-key envelope (adds ``tier`` + ``perspective_tier_rank`` +
    ``grace`` / ``enforced`` on top of the sibling ``/has-feature`` shape)::

        {
          "tier":                  "<perspective tier id>" | "",
          "feature":               "<canonicalised id>"    | "",
          "has_feature_at":        <bool>,
          "allowed":               <bool>,             # alias of has_feature_at
          "required_tier":         "<tier id>" | null, # min_tier_for_<axis>
          "required_tier_label":   "<label>"  | null,
          "required_tier_rank":    <int>,              # -1 when required_tier null
          "perspective_tier_rank": <int>,              # -1 when tier unknown/blank
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,             # live resolver grace bit
          "enforced":              <bool>,
        }

    Runtime-axis alias canonicalisation: the endpoint layer calls
    :func:`canonical_runtime` on the raw ``runtime`` arg before delegating
    to :func:`has_runtime_at`, matching the ``/has-runtime`` endpoint's
    own upstream posture. This lets ``?runtime=claude-code`` collapse to
    the granted ``claude_code`` at the URL layer even though the scalar
    itself is strict (no alias resolution at scalar level -- see
    :func:`has_runtime_at`).

    Never 4xxs (missing / blank / unknown tier or axis id -> 200 with
    ``has_<axis>_at=False``, mirroring the ``/has-feature`` posture). The
    ``perspective_tier_rank`` slot is ``-1`` for an unknown perspective
    so a UI can distinguish "typo perspective" from "valid perspective
    that just doesn't grant this axis". Never 5xxs.
    """
    from clawmetry import entitlements as _ent

    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    if axis == "feature":
        raw_key = request.args.get("feature")
        key = (raw_key or "").strip().lower()
    else:
        raw_key = request.args.get("runtime")
        # Canonicalise runtime alias upstream of the strict scalar
        # (``has_runtime_at`` does not resolve aliases -- see the
        # scalar docstring for rationale), matching the sibling
        # ``/has-runtime`` endpoint's own upstream-canonicalise pattern.
        raw_stripped = (raw_key or "").strip().lower()
        try:
            key = _ent.canonical_runtime(raw_stripped) or raw_stripped
        except Exception:
            key = raw_stripped
    if axis == "feature":
        has_flag = _ent.has_feature_at(tier, key)
        required = _ent.min_tier_for_feature(key) if key else None
    else:
        has_flag = _ent.has_runtime_at(tier, key)
        required = _ent.min_tier_for_runtime(key) if key else None
    ent = _ent.get_entitlement()
    cur_rank = _ent.tier_rank(ent.tier)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    # Rank of the perspective tier itself, so a paywall matrix can sort
    # cells by tier without a follow-up ``/tier-rank`` call. ``-1`` when
    # the perspective is unknown / blank (matches the ``required_tier_rank``
    # sentinel for a not-resolved tier).
    persp_rank = _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
    return {
        "tier": tier,
        axis: key,
        f"has_{axis}_at": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "perspective_tier_rank": persp_rank,
        "current_tier": ent.tier,
        "current_tier_rank": cur_rank,
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }

def _has_channel_count_fallback(count_raw: str) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-channel-count``.

    Fail-closed on ``has_channel_count`` (matches the sibling
    ``/api/entitlement/has-feature`` / ``/has-runtime`` fallback) so a paywall
    tile that lost the resolver doesn't silently grant a capacity that might be
    over-quota. ``count`` is echoed as ``None`` and ``count_raw`` as the
    stripped input so a UI can still surface the offending value in a diagnostic
    tooltip. 10-key envelope, byte-stable with the happy-path branch.
    """
    return {
        "count": None,
        "count_raw": count_raw,
        "has_channel_count": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "upgrade_required": False,
    }

def _has_channel_count_at_fallback(tier: str, count_raw: str) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-channel-count-at``.

    What-if sibling of :func:`_has_channel_count_fallback`. On any resolver /
    helper blowup the endpoint still returns 200 with the same 13-key
    envelope as the happy-path branch, but with ``has_channel_count_at`` and
    ``allowed`` strict-``False`` (matches the fail-closed posture the
    sibling ``/has-feature-at`` / ``/has-runtime-at`` / ``/has-node-count-at``
    and ``/has-channel-count`` fallbacks use -- a paywall matrix tile that
    lost the resolver never silently reports a grant it cannot verify).
    ``tier`` and ``count_raw`` echo the caller's canonicalised inputs so
    the UI can still surface both in a diagnostics tooltip.
    """
    return {
        "tier": tier,
        "count": None,
        "count_raw": count_raw,
        "has_channel_count_at": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_retention_window_fallback(days_raw: str, unlimited: bool) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-retention-window``.

    Fail-closed on ``has_retention_window`` (matches the sibling
    ``/api/entitlement/has-feature`` / ``/has-runtime`` / ``/has-channel-count``
    fallback) so a paywall tile that lost the resolver doesn't silently grant
    a history window that might exceed the paid cap. ``days`` is echoed as
    ``None`` and ``days_raw`` as the stripped input so a UI can still surface
    the offending value in a diagnostic tooltip. ``unlimited`` mirrors the
    happy-path field so callers can bind off it without a branch on the
    fallback state. 11-key envelope, byte-stable with the happy-path branch.
    """
    return {
        "days": None,
        "days_raw": days_raw,
        "unlimited": unlimited,
        "has_retention_window": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "upgrade_required": False,
    }

def _has_retention_window_at_fallback(
    tier: str, days_raw: str, unlimited: bool
) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-retention-window-at``.

    What-if sibling of :func:`_has_retention_window_fallback`. On any
    resolver / helper blowup the endpoint still returns 200 with the same
    14-key envelope as the happy-path branch, but with
    ``has_retention_window_at`` and ``allowed`` strict-``False`` (matches
    the fail-closed posture the sibling ``/has-feature-at`` /
    ``/has-runtime-at`` / ``/has-channel-count-at`` /
    ``/has-node-count-at`` fallbacks use -- a paywall matrix tile that
    lost the resolver never silently reports a grant it cannot verify).
    ``tier``, ``days_raw`` and ``unlimited`` echo the caller's
    canonicalised inputs so the UI can still surface all three in a
    diagnostics tooltip.
    """
    return {
        "tier": tier,
        "days": None,
        "days_raw": days_raw,
        "unlimited": unlimited,
        "has_retention_window_at": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_node_count_fallback(count_raw: str) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-node-count``.

    Fail-closed on ``has_node_count`` (matches the sibling
    ``/api/entitlement/has-feature`` / ``/has-runtime`` / ``/has-channel-count``
    fallbacks) so a fleet paywall tile that lost the resolver doesn't silently
    grant a node count that might be over-quota. ``count`` is echoed as
    ``None`` and ``count_raw`` as the stripped input so a UI can still surface
    the offending value in a diagnostic tooltip. 10-key envelope, byte-stable
    with the happy-path branch.
    """
    return {
        "count": None,
        "count_raw": count_raw,
        "has_node_count": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "upgrade_required": False,
    }

def _has_node_count_at_fallback(tier: str, count_raw: str) -> dict:
    """OSS-free / never-5xx shape for ``/api/entitlement/has-node-count-at``.

    What-if sibling of :func:`_has_node_count_fallback`. On any resolver /
    helper blowup the endpoint still returns 200 with the same 13-key
    envelope as the happy-path branch, but with ``has_node_count_at`` and
    ``allowed`` strict-``False`` (matches the fail-closed posture the
    sibling ``/has-feature-at`` / ``/has-runtime-at`` and
    ``/has-node-count`` fallbacks use -- a fleet pricing matrix tile that
    lost the resolver never silently reports a grant it cannot verify).
    ``tier`` and ``count_raw`` echo the caller's canonicalised inputs so
    the UI can still surface both in a diagnostics tooltip.
    """
    return {
        "tier": tier,
        "count": None,
        "count_raw": count_raw,
        "has_node_count_at": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_node_count_batch_row_to_body(
    row: dict, count_raw: str, cur_rank: int
) -> dict:
    """Translate a :func:`has_node_count_batch` scalar row into the endpoint
    body row shape.

    Rekeys ``has`` -> ``has_node_count`` / ``allowed`` (matches the
    singular ``/api/entitlement/has-node-count`` body), replaces the
    normalised-str ``key`` with an int ``count`` (or ``null`` on non-int
    input) plus the caller's raw ``count_raw`` echo (matches the
    singular endpoint's ``count`` / ``count_raw`` pair), and layers a
    conjugated human ``label`` ("1 node" / "5 nodes"; matches
    :func:`_capacity_batch_row_to_body`) plus a per-row
    ``upgrade_required`` bit computed against the shared ``cur_rank`` so
    a paywall matrix tile can bind it directly without a second lookup.

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape (``count=null``, ``has_node_count=false``, ``allowed=false``,
    ``required_tier=null``, ``upgrade_required=false``) so the batch keeps
    building.
    """
    try:
        n = int(row.get("key"))
        count: int | None = n
        label = f"{n} node" if n == 1 else f"{n} nodes"
    except (TypeError, ValueError):
        count = None
        label = None
    req_rank = row.get("required_tier_rank")
    if req_rank is None:
        req_rank = -1
    has_flag = bool(row.get("has"))
    required = row.get("required_tier")
    return {
        "count": count,
        "count_raw": count_raw,
        "kind": "node_count",
        "label": label,
        "has_node_count": has_flag,
        "allowed": has_flag,
        "unknown": bool(row.get("unknown")),
        "required_tier": required,
        "required_tier_label": row.get("required_tier_label"),
        "required_tier_rank": req_rank,
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _has_node_count_batch_fallback() -> dict:
    """Grace-shape fallback body for ``/api/entitlement/has-node-count-batch``.

    Sibling of :func:`_min_tier_for_capacity_batch_fallback` on the
    same axis: on a resolver crash the pricing surface keeps rendering
    with an empty ``rows`` list instead of a stack trace. Envelope
    mirrors the happy-path body so a caller does not have to branch on
    the error shape.
    """
    return {
        "kind": "node_count",
        "count": 0,
        "rows": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_channel_count_batch_row_to_body(
    row: dict, count_raw: str, cur_rank: int
) -> dict:
    """Translate a :func:`has_channel_count_batch` scalar row into the
    endpoint body row shape.

    Channel-axis twin of :func:`_has_node_count_batch_row_to_body`.
    Rekeys ``has`` -> ``has_channel_count`` / ``allowed`` (matches the
    singular ``/api/entitlement/has-channel-count`` body), replaces the
    normalised-str ``key`` with an int ``count`` (or ``null`` on non-int
    input) plus the caller's raw ``count_raw`` echo, and layers a
    conjugated human ``label`` ("1 channel" / "5 channels"; matches
    :func:`_capacity_batch_row_to_body`) plus a per-row
    ``upgrade_required`` bit computed against the shared ``cur_rank``.

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape.
    """
    try:
        n = int(row.get("key"))
        count: int | None = n
        label = f"{n} channel" if n == 1 else f"{n} channels"
    except (TypeError, ValueError):
        count = None
        label = None
    req_rank = row.get("required_tier_rank")
    if req_rank is None:
        req_rank = -1
    has_flag = bool(row.get("has"))
    required = row.get("required_tier")
    return {
        "count": count,
        "count_raw": count_raw,
        "kind": "channel_count",
        "label": label,
        "has_channel_count": has_flag,
        "allowed": has_flag,
        "unknown": bool(row.get("unknown")),
        "required_tier": required,
        "required_tier_label": row.get("required_tier_label"),
        "required_tier_rank": req_rank,
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _has_channel_count_batch_fallback() -> dict:
    """Grace-shape fallback body for
    ``/api/entitlement/has-channel-count-batch``. Sibling of
    :func:`_has_node_count_batch_fallback` on the same axis: on a
    resolver crash the pricing surface keeps rendering with an empty
    ``rows`` list instead of a stack trace. Envelope mirrors the
    happy-path body so a caller does not have to branch on the error
    shape.
    """
    return {
        "kind": "channel_count",
        "count": 0,
        "rows": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_retention_window_batch_row_to_body(
    row: dict, days_raw: str, cur_rank: int
) -> dict:
    """Translate a :func:`has_retention_window_batch` scalar row into the
    endpoint body row shape.

    Retention-axis twin of :func:`_has_channel_count_batch_row_to_body`
    with one wrinkle: the ``"unlimited"`` row surfaces with ``days=null``
    and ``unlimited=true`` / ``label="unlimited"`` -- matching the
    singular ``/api/entitlement/has-retention-window`` body's ``unlimited``
    axis semantics. All other rows carry the parsed int in ``days`` and
    the conjugated ``label`` ("1 day" / "5 days").

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape.
    """
    key = row.get("key")
    days: int | None
    unlimited = False
    if isinstance(key, str) and key == "unlimited":
        days = None
        label = "unlimited"
        unlimited = True
    else:
        try:
            n = int(key)
            days = n
            label = f"{n} day" if n == 1 else f"{n} days"
        except (TypeError, ValueError):
            days = None
            label = None
    req_rank = row.get("required_tier_rank")
    if req_rank is None:
        req_rank = -1
    has_flag = bool(row.get("has"))
    required = row.get("required_tier")
    return {
        "days": days,
        "days_raw": days_raw,
        "unlimited": unlimited,
        "kind": "retention_window",
        "label": label,
        "has_retention_window": has_flag,
        "allowed": has_flag,
        "unknown": bool(row.get("unknown")),
        "required_tier": required,
        "required_tier_label": row.get("required_tier_label"),
        "required_tier_rank": req_rank,
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _has_retention_window_batch_fallback() -> dict:
    """Grace-shape fallback body for
    ``/api/entitlement/has-retention-window-batch``. Sibling of
    :func:`_has_node_count_batch_fallback` /
    :func:`_has_channel_count_batch_fallback` on the same axis: on a
    resolver crash the pricing surface keeps rendering with an empty
    ``rows`` list instead of a stack trace.
    """
    return {
        "kind": "retention_window",
        "count": 0,
        "rows": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_fallback(axis: str, tokens: list[str]) -> dict:
    """OSS-free / never-5xx envelope for the plural ``/api/entitlement/has-features``
    and ``/api/entitlement/has-runtimes`` endpoints.

    Mirrors the fail-closed posture the singular ``/api/entitlement/has-feature``
    / ``/has-runtime`` and ``/api/entitlement/has-channel-count`` fallbacks
    carry: on a resolver blowup the endpoint still returns 200 with the same
    envelope shape as the happy path, but with ``has_<axis>``/``allowed`` False
    so a paywall tile that lost the resolver doesn't silently grant a bundle
    it can't evaluate. ``tokens`` echoes the caller's raw input list into
    ``unknown`` so a diagnostics tooltip can still surface the offending set.
    """
    key = f"has_{axis}"
    return {
        axis: [],
        "unknown": list(tokens),
        "kind": axis,
        "count": 0,
        key: False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
        "upgrade_required": False,
    }

def _has_bundle_body(axis: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/has-features`` /
    ``/api/entitlement/has-runtimes``.

    Splits the caller's CSV into ``known`` / ``unknown`` against the
    entitlement's ``ALL_FEATURES`` / ``ALL_RUNTIMES`` id set (with runtime-
    alias canonicalisation for the runtimes axis) so the UI can surface a
    diagnostics list of tokens the resolver couldn't place. The scalar
    boolean ``has_<axis>`` is delegated to :func:`has_features` /
    :func:`has_runtimes` against the ORIGINAL CSV -- unknown tokens
    collapse the bundle to ``False`` there so the endpoint stays byte-parity
    with the scalar's typo-catches-at-callsite posture (a UI that binds
    ``allowed`` off this URL can't accidentally render "granted" for a
    typo'd feature id). ``required_tier`` is resolved against the ``known``
    subset for parity with the ``/api/entitlement/min-tier-for-<axis>``
    envelope (which does the same known/unknown split).
    """
    from clawmetry import entitlements as _ent

    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list[str] = []
    unknown: list[str] = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    # Scalar boolean: only ``True`` when every input token resolved to a
    # granted known id (delegates to the plural scalars on the canonicalised
    # ``known`` list). ``unknown`` tokens collapse the bundle to ``False``
    # for the same typo-catches-at-callsite reason the singular
    # ``has_feature("BOGUS")`` returns ``False`` -- a UI can still surface
    # the offending set via the ``unknown`` slot.
    if tokens and not unknown and known:
        has_flag = (
            _ent.has_features(known)
            if axis == "features"
            else _ent.has_runtimes(known)
        )
    else:
        has_flag = False

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    return {
        axis: known,
        "unknown": unknown,
        "kind": axis,
        "count": len(known),
        f"has_{axis}": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _has_bundle_at_fallback(axis: str, tier: str, tokens: list[str]) -> dict:
    """OSS-free / never-5xx envelope for the plural what-if endpoints
    ``/api/entitlement/has-features-at`` and ``/has-runtimes-at``.

    What-if sibling of :func:`_has_bundle_fallback`, in the same relationship
    :func:`_has_axis_at_fallback` has to :func:`_has_axis_fallback`. On any
    resolver / helper blowup the endpoint still returns 200 with the same
    15-key envelope as the happy path, but with ``has_<axis>_at`` and
    ``allowed`` strict-``False`` (matches the fail-closed posture the sibling
    ``/has-feature-at`` / ``/has-runtime-at`` fallback uses -- a paywall
    matrix tile that lost the resolver never silently renders a bundle grant
    it can't verify). ``tier`` and ``tokens`` echo the caller's canonicalised
    input so the UI can still surface both in a diagnostics tooltip.
    """
    key = f"has_{axis}_at"
    return {
        "tier": tier,
        axis: [],
        "unknown": list(tokens),
        "kind": axis,
        "count": 0,
        key: False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_at_body(axis: str) -> dict:
    """Happy-path body builder for the plural what-if endpoints
    ``/api/entitlement/has-features-at`` and ``/has-runtimes-at``.

    Perspective-shaped sibling of :func:`_has_bundle_body`: where the live
    variant folds :func:`has_features` / :func:`has_runtimes` against the
    resolved entitlement, this folds :func:`has_features_at` /
    :func:`has_runtimes_at` against a caller-supplied ``tier=`` perspective
    so a pricing matrix that gates on a bundle ("does Starter grant fleet +
    otel_export + sso? Pro? Enterprise?") can bind ONE boolean per cell off
    ONE URL each, instead of hydrating the full ``/feature-catalog-at``
    payload and AND-folding the ``allowed`` fields client-side.

    Envelope shape (15 keys, byte-stable across every input branch)::

        {
          "tier":                  "<perspective tier id>" | "",
          "features"/"runtimes":   [<known ids>],       # known-only, dedup, first-seen
          "unknown":               [<tokens>],           # dropped tokens, echoed raw
          "kind":                  "features"/"runtimes",
          "count":                 <int>,               # len(known)
          "has_<axis>_at":         <bool>,              # scalar over the ORIGINAL CSV
          "allowed":               <bool>,              # alias of has_<axis>_at
          "required_tier":         "<tier id>" | null,  # min_tier_for_<axis>(known)
          "required_tier_label":   "<label>"  | null,
          "required_tier_rank":    <int>,               # -1 when null
          "perspective_tier_rank": <int>,               # -1 when tier unknown/blank
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,              # LIVE resolver grace bit
          "enforced":              <bool>,
        }

    Runtime-axis alias canonicalisation is applied per-token upstream of the
    strict scalar (:func:`has_runtimes_at` does not resolve aliases -- see
    the scalar docstring), matching the sibling :func:`_has_bundle_body`
    posture on the ``/has-runtimes`` endpoint exactly.

    Never 4xxs (missing / blank / unknown tier or all-unknown CSV -> 200
    with ``has_<axis>_at=false``, matching the sibling ``/has-features``
    posture -- a paywall matrix tile binds ``allowed`` directly without a
    pre-validation round-trip). The ``perspective_tier_rank`` slot is ``-1``
    for an unknown perspective so a UI can distinguish "typo perspective"
    from "valid perspective that just doesn't grant this bundle". Never
    5xxs.
    """
    from clawmetry import entitlements as _ent

    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list[str] = []
    unknown: list[str] = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    # Scalar what-if: only ``True`` when every input token resolved to a
    # granted known id under ``tier``'s static grant map. ``unknown`` tokens
    # collapse the bundle to ``False`` for the same typo-catches-at-callsite
    # reason the singular ``has_feature_at("pro", "BOGUS")`` returns ``False``
    # -- a UI can still surface the offending set via the ``unknown`` slot.
    if tokens and not unknown and known and tier and tier in _ent._TIER_ORDER:
        has_flag = (
            _ent.has_features_at(tier, known)
            if axis == "features"
            else _ent.has_runtimes_at(tier, known)
        )
    else:
        has_flag = False

    ent = _ent.get_entitlement()
    cur_rank = _ent.tier_rank(ent.tier)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    persp_rank = _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
    return {
        "tier": tier,
        axis: known,
        "unknown": unknown,
        "kind": axis,
        "count": len(known),
        f"has_{axis}_at": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "perspective_tier_rank": persp_rank,
        "current_tier": ent.tier,
        "current_tier_rank": cur_rank,
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }

def _missing_bundle_fallback(axis: str, tokens: list) -> dict:
    """OSS-free / never-5xx envelope for the ``/api/entitlement/missing-features``
    and ``/api/entitlement/missing-runtimes`` endpoints.

    Complement of :func:`_has_bundle_fallback`: on a resolver blowup the
    endpoint still returns 200 with the same envelope shape as the happy
    path, but with ``missing=[]`` (matches the ``[]`` module scalar returns
    on error) and the ``any_missing`` rollup ``False`` so a diagnostics tile
    wired off this URL does not silently render a denial banner on a resolver
    hiccup. ``tokens`` echoes the caller's raw input list into ``unknown``
    so the tooltip can still surface the caller-supplied set for debugging.
    """
    return {
        axis: [],
        "unknown": list(tokens),
        "missing": [],
        "kind": axis,
        "count": 0,
        "missing_count": 0,
        "any_missing": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
        "upgrade_required": False,
    }

def _missing_bundle_body(axis: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-features`` /
    ``/api/entitlement/missing-runtimes``.

    Row-detail complement of :func:`_has_bundle_body`: where ``has-features``
    /``has-runtimes`` fold the bundle to ONE boolean, this preserves the
    per-item denial list so a paywall diagnostics tile ("you're missing
    fleet, sso -- upgrade to unlock") can bind the exact set off ONE URL
    without walking the ``/has-batch`` matrix and filtering ``has=False``
    client-side.

    Splits the caller's CSV into ``known`` / ``unknown`` against the
    entitlement's ``ALL_FEATURES`` / ``ALL_RUNTIMES`` id set (with runtime-
    alias canonicalisation for the runtimes axis). ``missing`` is delegated
    to :func:`missing_features` / :func:`missing_runtimes` against the
    ORIGINAL CSV so unknown tokens surface in the denial list (matches the
    scalar's typo-catches-at-callsite posture -- a UI can still separate
    unknown vs known-but-denied via the ``unknown`` slot). ``required_tier``
    is resolved against the ``known`` subset for parity with the sibling
    ``/api/entitlement/min-tier-for-<axis>`` envelope.
    """
    from clawmetry import entitlements as _ent

    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        missing = _ent.missing_features(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        # Canonicalise upstream of the scalar so an alias input
        # (``claude-code``) collapses to the granted runtime
        # (``claude_code``) here instead of surfacing in ``missing`` --
        # matches the :func:`_has_bundle_body` upstream-canonicalise
        # pattern for the sibling ``/has-runtimes`` endpoint, and dedups
        # an alias-and-canonical pair to one entry before the scalar
        # sees it.
        canon_tokens: list = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        missing = _ent.missing_runtimes(canon_tokens)
        required = _ent.min_tier_for_runtimes(known) if known else None

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    return {
        axis: known,
        "unknown": unknown,
        "missing": list(missing),
        "kind": axis,
        "count": len(known),
        "missing_count": len(missing),
        "any_missing": bool(missing) or bool(unknown),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _missing_bundle_at_fallback(axis: str, tier: str, tokens: list) -> dict:
    """OSS-free / never-5xx envelope for the perspective-shaped complement
    endpoints ``/api/entitlement/missing-features-at`` and
    ``/api/entitlement/missing-runtimes-at``.

    What-if sibling of :func:`_missing_bundle_fallback`, in the same
    relationship :func:`_has_bundle_at_fallback` has to
    :func:`_has_bundle_fallback`. On any resolver / helper blowup the
    endpoint still returns 200 with the same 17-key envelope as the happy
    path, but with ``missing=[]`` (matches the ``[]`` module scalar
    returns on error) and the ``any_missing`` / ``upgrade_required``
    rollups ``False`` so a paywall matrix tile that lost the resolver
    doesn't silently render a denial banner it can no longer justify.
    ``tier`` and ``tokens`` echo the caller's input into ``tier`` /
    ``unknown`` so the tooltip can still surface the caller-supplied set
    for debugging.
    """
    return {
        "tier": tier,
        axis: [],
        "unknown": list(tokens),
        "missing": [],
        "kind": axis,
        "count": 0,
        "missing_count": 0,
        "any_missing": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
        "upgrade_required": False,
    }

def _missing_bundle_at_body(axis: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-features-at``
    /``/api/entitlement/missing-runtimes-at``.

    Perspective-shaped sibling of :func:`_missing_bundle_body`: where the
    live variant folds :func:`missing_features` / :func:`missing_runtimes`
    against the resolved entitlement, this folds
    :func:`missing_features_at` / :func:`missing_runtimes_at` against a
    caller-supplied ``tier=`` perspective so a pricing matrix that gates
    on a bundle ("which of fleet + otel_export + sso would still be
    locked at Starter? at Pro?") can bind the per-item denial list off
    ONE URL per cell, instead of walking the ``/has-batch`` matrix and
    filtering ``has=False`` client-side.

    Envelope shape (17 keys, byte-stable across every input branch)::

        {
          "tier":                  "<perspective tier id>" | "",
          "features"/"runtimes":   [<known ids>],       # known-only, dedup, first-seen
          "unknown":               [<tokens>],           # dropped tokens, echoed raw
          "missing":               [<subset denied at tier>],
          "kind":                  "features"/"runtimes",
          "count":                 <int>,               # len(known)
          "missing_count":         <int>,               # len(missing)
          "any_missing":           <bool>,              # missing != [] OR unknown != []
          "required_tier":         "<tier id>" | null,  # min_tier_for_<axis>(known)
          "required_tier_label":   "<label>"  | null,
          "required_tier_rank":    <int>,               # -1 when null
          "perspective_tier_rank": <int>,               # -1 when tier unknown/blank
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,              # LIVE resolver grace bit
          "enforced":              <bool>,
          "upgrade_required":      <bool>,              # required_rank > perspective_rank
        }

    Runtime-axis alias canonicalisation is applied per-token upstream of
    the strict scalar (:func:`missing_runtimes_at` does not resolve
    aliases -- see the scalar docstring), matching the sibling
    :func:`_missing_bundle_body` posture on the ``/missing-runtimes``
    endpoint exactly (upstream canonicalise dedups an alias-and-canonical
    pair to ONE row before the scalar sees it).

    ``upgrade_required`` compares ``required_tier`` against the
    PERSPECTIVE rank (not the live current rank) so a pricing-matrix row
    that binds this field reads "no upgrade needed at this tier" (False
    when perspective >= required) vs "upgrade needed beyond this tier"
    -- diverges deliberately from :func:`_missing_bundle_body`'s
    live-current comparison, matching the ``_at`` slot's what-if
    convention.

    Never 4xxs (missing / blank / unknown tier or all-unknown CSV -> 200
    with ``missing=[]``, matching the sibling ``/missing-features``
    posture -- a paywall matrix tile binds ``missing`` directly without
    a pre-validation round-trip). The ``perspective_tier_rank`` slot is
    ``-1`` for an unknown perspective so a UI can distinguish "typo
    perspective" from "valid perspective that grants everything". Never
    5xxs.
    """
    from clawmetry import entitlements as _ent

    raw_tier = request.args.get("tier")
    tier = (raw_tier or "").strip().lower()
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        # scalar delegate receives the raw CSV so unknown tokens surface
        # in ``missing`` (matches the sibling ``/missing-features``
        # scalar-vs-endpoint parity contract).
        if tier and tier in _ent._TIER_ORDER:
            missing = _ent.missing_features_at(tier, tokens)
        else:
            # unknown perspective: fail-open on the diagnostic (same as
            # scalar); ``missing`` empty, ``unknown`` still populated.
            missing = []
        required = _ent.min_tier_for_features(known) if known else None
    else:
        # Canonicalise upstream of the scalar so an alias input
        # (``claude-code``) collapses to the granted runtime
        # (``claude_code``) here instead of surfacing in ``missing`` --
        # matches the :func:`_missing_bundle_body` upstream-canonicalise
        # pattern for the sibling ``/missing-runtimes`` endpoint, and
        # dedups an alias-and-canonical pair to ONE entry before the
        # scalar sees it.
        canon_tokens: list = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        if tier and tier in _ent._TIER_ORDER:
            missing = _ent.missing_runtimes_at(tier, canon_tokens)
        else:
            missing = []
        required = _ent.min_tier_for_runtimes(known) if known else None

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None
    persp_rank = (
        _ent.tier_rank(tier) if tier and tier in _ent._TIER_ORDER else -1
    )
    upgrade_required = (
        bool(required) and persp_rank >= 0 and req_rank > persp_rank
    )
    return {
        "tier": tier,
        axis: known,
        "unknown": unknown,
        "missing": list(missing),
        "kind": axis,
        "count": len(known),
        "missing_count": len(missing),
        "any_missing": bool(missing) or bool(unknown),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "perspective_tier_rank": persp_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
        "upgrade_required": upgrade_required,
    }

def _missing_bundle_at_batch_fallback(
    axis: str, tier_tokens: list, feature_or_runtime_tokens: list
) -> dict:
    """OSS-free / never-5xx envelope for
    ``/api/entitlement/missing-features-at-batch`` /
    ``/api/entitlement/missing-runtimes-at-batch``.

    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]``
    (matches the ``{"tiers": [], "unknown": []}`` scalar fallback in
    :func:`_normalise_csv`-style batch helpers), and every ``count`` /
    ``any_missing`` roll-up ``0`` / ``False`` so a pricing-matrix column
    that lost the resolver doesn't silently render a denial banner it
    can no longer justify. Caller-supplied tier and axis tokens echo
    into ``unknown_tiers`` / ``unknown`` for debugging.
    """
    return {
        axis: [],
        "unknown": list(feature_or_runtime_tokens),
        "unknown_tiers": list(tier_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_bundle_at_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-features-at-batch`` /
    ``/api/entitlement/missing-runtimes-at-batch``.

    Batch what-if sibling of :func:`_missing_bundle_at_body`: where the
    ``_at`` variant folds ONE (perspective, bundle) pair, this fixes the
    bundle and sweeps across N perspective tiers, returning one row per
    tier with the per-item denial list plus the surrounding tier
    envelope so a pricing-matrix column ("out of {fleet, sso}, which
    are still locked at OSS vs Cloud Starter vs Cloud Pro vs
    Enterprise?") hydrates the whole column off ONE URL instead of N
    calls to ``/missing-features-at``.

    Envelope shape (byte-stable across every input branch)::

        {
          "features"/"runtimes":  [<known ids>],          # known-only, dedup, first-seen
          "unknown":              [<feature/runtime tokens dropped>],
          "unknown_tiers":        [<tier tokens dropped>],
          "kind":                 "features"/"runtimes",
          "count":                <int>,                  # len(known)
          "tiers": [
            {
              "tier":                  "<id>",
              "tier_label":            "...",
              "tier_rank":             <int>,
              "missing":               [<subset denied at tier>],
              "missing_count":         <int>,
              "any_missing":           <bool>,
              "required_tier":         "<id>" | null,     # min_tier_for_<axis>(known)
              "required_tier_label":   "<label>" | null,
              "required_tier_rank":    <int>,             # -1 when null
              "upgrade_required":      <bool>,            # required_rank > tier_rank
            },
            ...
          ],
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,                # LIVE resolver grace bit
          "enforced":              <bool>,
        }

    Runtime-axis alias canonicalisation is applied per-token upstream of
    the strict scalar (:func:`missing_runtimes_at_batch` inherits the
    strict-scalar posture from :func:`missing_runtimes_at`), matching
    the sibling :func:`_missing_bundle_at_body` posture on the
    ``/missing-runtimes-at`` endpoint exactly (upstream canonicalise
    dedups an alias-and-canonical pair to ONE row before the scalar
    sees it).

    Per-row ``upgrade_required`` compares ``required_tier`` against
    each ROW's tier rank (not the live current rank) so a pricing-matrix
    row that binds this field reads "no upgrade needed at this tier"
    vs "upgrade needed beyond this tier" -- matches the ``_at`` slot's
    what-if convention.

    Never 4xxs (missing / blank / unknown tiers or all-unknown CSV -> 200
    with ``tiers=[]``, matching the sibling ``/missing-features-at``
    posture). Never 5xxs.
    """
    from clawmetry import entitlements as _ent

    tier_tokens = _parse_csv_arg("tiers")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        scalar_tokens = tokens
        required = _ent.min_tier_for_features(known) if known else None
        batch = _ent.missing_features_at_batch(tier_tokens, scalar_tokens)
    else:
        # Canonicalise upstream of the strict scalar so an alias input
        # (``claude-code``) collapses to the granted runtime
        # (``claude_code``) here instead of surfacing in each row's
        # ``missing`` -- matches the sibling ``_missing_bundle_at_body``
        # upstream-canonicalise pattern for the ``/missing-runtimes-at``
        # endpoint, and dedups an alias-and-canonical pair to ONE entry
        # before the scalar sees it.
        canon_tokens: list = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        scalar_tokens = canon_tokens
        required = _ent.min_tier_for_runtimes(known) if known else None
        batch = _ent.missing_runtimes_at_batch(tier_tokens, scalar_tokens)

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            tid = row.get("tier")
            row_missing = list(row.get("missing", []))
        except AttributeError:
            continue
        row_rank = row.get("tier_rank", _ent.tier_rank(tid))
        upgrade_required = (
            bool(required) and row_rank >= 0 and req_rank > row_rank
        )
        tiers_out.append(
            {
                "tier": tid,
                "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                "tier_rank": row_rank,
                "missing": row_missing,
                "missing_count": len(row_missing),
                "any_missing": bool(row_missing) or bool(unknown),
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": upgrade_required,
            }
        )

    return {
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_bundle_at_batch_fallback(
    axis: str, tier_tokens: list, feature_or_runtime_tokens: list
) -> dict:
    """OSS-free / never-5xx envelope for
    ``/api/entitlement/has-features-at-batch`` /
    ``/api/entitlement/has-runtimes-at-batch``.

    Boolean-fold sibling of :func:`_missing_bundle_at_batch_fallback`. On
    any resolver / helper blowup the endpoint still returns 200 with the
    same envelope shape as the happy path but with ``tiers=[]`` and every
    fold-rollup fail-closed (``allowed_count=0`` / ``all_allowed=False`` /
    ``any_allowed=False``) so a pricing-matrix column that lost the
    resolver never silently renders a bundle grant it can't verify --
    matches the sibling ``/has-features-at`` fallback's fail-closed
    posture byte-for-byte. Caller-supplied tier and axis tokens echo
    into ``unknown_tiers`` / ``unknown`` for debugging.
    """
    return {
        axis: [],
        "unknown": list(feature_or_runtime_tokens),
        "unknown_tiers": list(tier_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "allowed_count": 0,
        "all_allowed": False,
        "any_allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_at_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/has-features-at-batch`` /
    ``/api/entitlement/has-runtimes-at-batch``.

    Batch what-if sibling of :func:`_has_bundle_at_body`: where the
    ``_at`` variant folds ONE (perspective, bundle) pair, this fixes the
    bundle and sweeps across N perspective tiers, returning one row per
    tier with the fold boolean plus the surrounding tier envelope so a
    pricing-matrix column ("does OSS grant {fleet, sso}? Cloud Starter?
    Cloud Pro? Enterprise?") hydrates the whole column off ONE URL
    instead of N calls to ``/has-features-at``. Boolean-fold complement
    of :func:`_missing_bundle_at_batch_body` (per-item denial list); the
    two share the envelope shape (same tier normalisation, same
    known / unknown split, same required-tier rollup) so a UI can render
    "is this granted?" and "which items are still locked?" side by side
    off the two paired endpoints.

    Envelope shape (byte-stable across every input branch)::

        {
          "features"/"runtimes":  [<known ids>],          # known-only, dedup, first-seen
          "unknown":              [<feature/runtime tokens dropped>],
          "unknown_tiers":        [<tier tokens dropped>],
          "kind":                 "features"/"runtimes",
          "count":                <int>,                  # len(known)
          "tiers": [
            {
              "tier":                  "<id>",
              "tier_label":            "...",
              "tier_rank":             <int>,
              "has_<axis>_at":         <bool>,            # fold vs ROW's tier
              "allowed":               <bool>,            # alias of has_<axis>_at
              "required_tier":         "<id>" | null,     # min_tier_for_<axis>(known)
              "required_tier_label":   "<label>" | null,
              "required_tier_rank":    <int>,             # -1 when null
              "upgrade_required":      <bool>,            # required_rank > tier_rank
            },
            ...
          ],
          "allowed_count":         <int>,                 # #rows with has_<axis>_at=true
          "all_allowed":           <bool>,                # every row granted
          "any_allowed":           <bool>,                # at least one row granted
          "required_tier":         "<id>" | null,         # bundle-level rollup
          "required_tier_label":   "<label>" | null,
          "required_tier_rank":    <int>,
          "current_tier":          "<live tier id>",
          "current_tier_rank":     <int>,
          "grace":                 <bool>,                # LIVE resolver grace bit
          "enforced":              <bool>,
        }

    Runtime-axis alias canonicalisation is applied per-token upstream of
    the strict scalar (:func:`has_runtimes_at_batch` inherits the
    strict-scalar posture from :func:`has_runtimes_at`), matching the
    sibling :func:`_missing_bundle_at_batch_body` /
    ``/missing-runtimes-at-batch`` upstream-canonicalise pattern
    byte-for-byte (an alias-and-canonical pair dedups to ONE row before
    the scalar sees it).

    Per-row ``upgrade_required`` compares ``required_tier`` against each
    ROW's tier rank (not the live current rank) so a pricing-matrix row
    that binds this field reads "no upgrade needed at this tier" vs
    "upgrade needed beyond this tier" -- matches the sibling
    :func:`_missing_bundle_at_batch_body` convention.

    ``all_allowed`` folds row.allowed AND-wise (empty ``tiers`` -> False
    to inherit the fail-closed fold posture the singular
    :func:`has_features_at` uses on empty input). ``any_allowed`` folds
    OR-wise (empty ``tiers`` -> False). ``allowed_count`` is the sum of
    per-row boolean grants so a pricing-matrix header can render "3 of 5
    tiers grant this bundle" off one field.

    Never 4xxs (missing / blank / unknown tiers or all-unknown CSV -> 200
    with ``tiers=[]``, matching the sibling ``/has-features-at`` posture).
    Never 5xxs.
    """
    from clawmetry import entitlements as _ent

    tier_tokens = _parse_csv_arg("tiers")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        scalar_tokens = tokens
        required = _ent.min_tier_for_features(known) if known else None
        batch = _ent.has_features_at_batch(tier_tokens, scalar_tokens)
    else:
        # Canonicalise upstream of the strict scalar so an alias input
        # (``claude-code``) collapses to the granted runtime
        # (``claude_code``) here instead of collapsing the row to
        # ``False`` -- matches the sibling ``_missing_bundle_at_batch_body``
        # upstream-canonicalise pattern for the ``/missing-runtimes-at-batch``
        # endpoint, and dedups an alias-and-canonical pair to ONE entry
        # before the scalar sees it.
        canon_tokens: list = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        scalar_tokens = canon_tokens
        required = _ent.min_tier_for_runtimes(known) if known else None
        batch = _ent.has_runtimes_at_batch(tier_tokens, scalar_tokens)

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    tiers_out: list[dict] = []
    fold_key = f"has_{axis}_at"
    for row in batch.get("tiers", []) or []:
        try:
            tid = row.get("tier")
            row_allowed = bool(row.get(fold_key, False))
        except AttributeError:
            continue
        row_rank = row.get("tier_rank", _ent.tier_rank(tid))
        upgrade_required = (
            bool(required) and row_rank >= 0 and req_rank > row_rank
        )
        # An unknown token in the bundle collapses the endpoint-level fold
        # to ``False`` on EVERY row (matches the singular
        # ``_has_bundle_at_body`` posture: ``unknown != []`` -> ``allowed=False``).
        endpoint_allowed = row_allowed and not unknown and bool(known)
        tiers_out.append(
            {
                "tier": tid,
                "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                "tier_rank": row_rank,
                fold_key: endpoint_allowed,
                "allowed": endpoint_allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": upgrade_required,
            }
        )

    allowed_count = sum(1 for r in tiers_out if r["allowed"])
    all_allowed = bool(tiers_out) and all(r["allowed"] for r in tiers_out)
    any_allowed = any(r["allowed"] for r in tiers_out)

    return {
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "allowed_count": allowed_count,
        "all_allowed": all_allowed,
        "any_allowed": any_allowed,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_bundle_at_path_fallback(
    axis: str,
    from_tier: str,
    to_tier: str,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the path-shaped complement
    endpoints ``/api/entitlement/missing-features-at-path`` and
    ``/api/entitlement/missing-runtimes-at-path``.

    Path-shaped sibling of :func:`_missing_bundle_at_fallback`. On any
    resolver / helper blowup the endpoint still returns 200 with the
    same envelope shape as the happy path, but ``path=[]`` and every
    rollup zeroed out so a pricing-page walkthrough that lost the
    resolver doesn't silently render a denial column it can no longer
    justify. ``from`` / ``to`` / ``tokens`` echo the caller's input into
    the envelope + ``unknown`` so the tooltip can still surface the
    caller-supplied set for debugging. ``direction`` collapses to
    ``"identity"`` when ``from == to`` (matches the happy-path branch
    for that case) and ``"unknown"`` otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        axis: [],
        "unknown": list(tokens),
        "path": [],
        "kind": axis,
        "count": 0,
        "path_length": 0,
        "any_missing": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_bundle_at_path_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-features-at-path`` /
    ``/api/entitlement/missing-runtimes-at-path``.

    Path-shaped sibling of :func:`_missing_bundle_at_body`: fixes ONE
    bundle and sweeps across every rung between ``from=`` and ``to=``,
    returning one row per rung with the per-item denial list at that rung
    plus the surrounding path envelope. Where ``/missing-features-at``
    folds ONE (perspective, bundle) cell, this folds a whole path of
    (rung, bundle) cells off ONE URL so an upgrade-walkthrough UI can
    render "at which tier does each of these unlock?" without first
    calling ``/tier-path`` for the rung list and then N calls to
    ``/missing-features-at``.

    Envelope shape mirrors ``/api/entitlement/feature-catalog-path``
    exactly for the walk-metadata keys (``from`` / ``from_label`` /
    ``from_rank`` / ``to`` / ``to_label`` / ``to_rank`` / ``direction``
    / ``path``) so a client already binding the catalog path envelope
    can bind this one with the same shape reader, and adds the axis-
    shared bundle metadata (``features``/``runtimes`` / ``unknown`` /
    ``kind`` / ``count`` / ``path_length`` / ``any_missing``), the
    bundle rollup (``required_tier`` / ``required_tier_label`` /
    ``required_tier_rank``) and the live resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``).

    Per-rung row shape byte-equals the scalar
    :func:`missing_features_at_path` / :func:`missing_runtimes_at_path`
    return: ``{tier, tier_label, tier_rank, missing}``. A parity test
    pins per-rung ``missing`` byte-equals
    ``/missing-features-at?tier=<rung>&features=<bundle>``'s ``.missing``
    for the same (rung, bundle) pair.

    Runtime-axis alias canonicalisation is applied per-token upstream
    of the strict scalar (:func:`missing_runtimes_at_path` inherits
    :func:`missing_runtimes_at`'s strict-alias posture at scalar layer),
    matching the sibling ``/missing-runtimes-at`` upstream-canonicalise
    pattern -- alias-and-canonical pair dedups to ONE entry in
    ``runtimes`` before the scalar sees it, so it also dedups to ONE
    entry in every rung's ``missing`` list.

    ``any_missing`` is ``True`` iff any rung's ``missing`` list is
    non-empty OR ``unknown`` is non-empty (matches the sibling
    ``/missing-features-at`` rollup semantics extended over the path).

    ``required_tier`` folds through :func:`min_tier_for_features` /
    :func:`min_tier_for_runtimes` against the KNOWN-only subset (matches
    the sibling ``/missing-features-at`` envelope's rollup contract),
    NOT the path endpoints -- the rollup answers "what's the cheapest
    tier that grants this bundle" independent of the walked window, so
    a caller can pin the two-way comparison (path window vs cheapest-
    grant tier) off ONE round-trip.

    ``direction`` mirrors :func:`_missing_bundle_at_path_body`'s sibling
    ``/feature-catalog-path`` values: ``upgrade`` | ``downgrade`` |
    ``lateral`` | ``identity``.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown CSV
    -> 200 with ``path=[]`` on the unknown-endpoint branch, matching the
    sibling ``/missing-features-at`` posture). Never 5xxs: any helper
    blowup collapses to :func:`_missing_bundle_at_path_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    if axis == "features":
        path = _ent.missing_features_at_path(from_tier, to_tier, canon_tokens)
    else:
        path = _ent.missing_runtimes_at_path(from_tier, to_tier, canon_tokens)

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    if path is None:
        # Unknown endpoint(s) -- fall through to the empty-path envelope so
        # the client never 4xxs; ``direction`` reads ``"unknown"``.
        direction = "unknown"
        path_out: list = []
        from_label = None
        to_label = None
        from_rank = -1
        to_rank = -1
    else:
        path_out = list(path)
        from_rank = _ent.tier_rank(from_tier)
        to_rank = _ent.tier_rank(to_tier)
        from_label = _ent.tier_label(from_tier)
        to_label = _ent.tier_label(to_tier)
        if from_tier == to_tier:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"

    any_missing = bool(unknown) or any(
        bool(row.get("missing")) for row in path_out
    )

    return {
        "from": from_tier,
        "from_label": from_label,
        "from_rank": from_rank,
        "to": to_tier,
        "to_label": to_label,
        "to_rank": to_rank,
        "direction": direction,
        axis: known,
        "unknown": unknown,
        "path": path_out,
        "kind": axis,
        "count": len(known),
        "path_length": len(path_out),
        "any_missing": any_missing,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_bundle_at_path_fallback(
    axis: str,
    from_tier: str,
    to_tier: str,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the path-shaped boolean-fold
    endpoints ``/api/entitlement/has-features-at-path`` and
    ``/api/entitlement/has-runtimes-at-path``.

    Path-shaped sibling of :func:`_has_bundle_at_batch_fallback` and
    boolean-fold complement of :func:`_missing_bundle_at_path_fallback`.
    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path, but ``path=[]`` and every
    fold-rollup fail-closed (``allowed_count=0`` / ``all_allowed=False``
    / ``any_allowed=False``) so a pricing-page walkthrough that lost the
    resolver never silently renders a bundle grant it can't verify --
    matches the sibling ``/has-features-at-batch`` fallback's fail-closed
    posture byte-for-byte. ``from`` / ``to`` / ``tokens`` echo the
    caller's input into the envelope + ``unknown`` so the tooltip can
    still surface the caller-supplied set for debugging. ``direction``
    collapses to ``"identity"`` when ``from == to`` (matches the happy-
    path branch for that case) and ``"unknown"`` otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        axis: [],
        "unknown": list(tokens),
        "path": [],
        "kind": axis,
        "count": 0,
        "path_length": 0,
        "allowed_count": 0,
        "all_allowed": False,
        "any_allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_at_path_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/has-features-at-path`` /
    ``/api/entitlement/has-runtimes-at-path``.

    Path-shaped sibling of :func:`_has_bundle_at_batch_body`: fixes ONE
    bundle and sweeps across every rung between ``from=`` and ``to=``,
    returning one row per rung with the fold boolean at that rung plus
    the surrounding path envelope. Boolean-fold complement of
    :func:`_missing_bundle_at_path_body` (per-item denial list); the two
    paired path endpoints share the walk-metadata envelope so a UI can
    render "is this bundle granted at this rung?" and "which items are
    still locked at this rung?" side by side without a second rung walk.

    Envelope shape mirrors :func:`_missing_bundle_at_path_body` for the
    walk-metadata keys (``from`` / ``from_label`` / ``from_rank`` /
    ``to`` / ``to_label`` / ``to_rank`` / ``direction`` / ``path``) so a
    client already binding the ``/missing-features-at-path`` /
    ``/feature-catalog-path`` envelope can bind this one with the same
    shape reader. The axis-shared bundle metadata (``features`` /
    ``runtimes`` / ``unknown`` / ``kind`` / ``count`` / ``path_length``)
    matches byte-for-byte, and the boolean-fold rollup
    (``allowed_count`` / ``all_allowed`` / ``any_allowed``) mirrors
    :func:`_has_bundle_at_batch_body` extended over the path so the
    same field bindings work on both.

    Per-rung row shape byte-equals the scalar
    :func:`has_features_at_path` / :func:`has_runtimes_at_path` return:
    ``{tier, tier_label, tier_rank, has_<axis>_at}``. A parity test pins
    per-rung ``has_<axis>_at`` byte-equals
    ``/has-features-at?tier=<rung>&features=<bundle>``'s ``.allowed``
    for the same (rung, bundle) pair.

    Runtime-axis alias canonicalisation is applied per-token upstream
    of the strict scalar (:func:`has_runtimes_at_path` inherits
    :func:`has_runtimes_at`'s strict-alias posture at scalar layer),
    matching the sibling ``/has-runtimes-at`` /
    ``/has-runtimes-at-batch`` upstream-canonicalise pattern -- alias-
    and-canonical pair dedups to ONE entry in ``runtimes`` before the
    scalar sees it, so it also dedups to ONE fold input on every rung.

    Endpoint-level fold semantics inherit :func:`_has_bundle_at_batch_body`
    byte-for-byte: an unknown token in the bundle collapses the
    endpoint-level fold to ``False`` on EVERY rung (``unknown != []`` ->
    every row's ``has_<axis>_at`` reads ``False``), so a bundle typo
    fails-closed at the endpoint layer the same way it fails-closed on
    the singular ``/has-features-at`` endpoint.

    ``allowed_count`` is the sum of per-row boolean grants across the
    walked path so a walkthrough header can render "granted at 2 of 4
    rungs" off one field. ``all_allowed`` folds per-row ``has_<axis>_at``
    AND-wise (empty ``path`` -> False, to inherit the fail-closed fold
    posture the singular :func:`has_features_at` uses on empty input).
    ``any_allowed`` folds OR-wise (empty ``path`` -> False).

    ``required_tier`` folds through :func:`min_tier_for_features` /
    :func:`min_tier_for_runtimes` against the KNOWN-only subset (matches
    the sibling ``/has-features-at-batch`` envelope's rollup contract),
    NOT the path endpoints -- the rollup answers "what's the cheapest
    tier that grants this bundle" independent of the walked window, so
    a caller can pin the two-way comparison (path window vs cheapest-
    grant tier) off ONE round-trip.

    ``direction`` mirrors :func:`_missing_bundle_at_path_body`'s
    ``/feature-catalog-path`` values: ``upgrade`` | ``downgrade`` |
    ``lateral`` | ``identity``.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown CSV
    -> 200 with ``path=[]`` on the unknown-endpoint branch, matching the
    sibling ``/has-features-at`` posture). Never 5xxs: any helper blowup
    collapses to :func:`_has_bundle_at_path_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    if axis == "features":
        path = _ent.has_features_at_path(from_tier, to_tier, canon_tokens)
    else:
        path = _ent.has_runtimes_at_path(from_tier, to_tier, canon_tokens)

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    fold_key = f"has_{axis}_at"

    if path is None:
        # Unknown endpoint(s) -- fall through to the empty-path envelope so
        # the client never 4xxs; ``direction`` reads ``"unknown"``.
        direction = "unknown"
        path_out: list = []
        from_label = None
        to_label = None
        from_rank = -1
        to_rank = -1
    else:
        # An unknown token in the bundle collapses the endpoint-level fold
        # to ``False`` on EVERY rung (matches the singular ``_has_bundle_at_body``
        # posture: ``unknown != []`` -> ``allowed=False``).
        endpoint_ok = not unknown and bool(known)
        path_out = []
        for row in path:
            try:
                tid = row.get("tier")
                row_allowed = bool(row.get(fold_key, False))
            except AttributeError:
                continue
            endpoint_allowed = row_allowed and endpoint_ok
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                    "tier_rank": row.get("tier_rank", _ent.tier_rank(tid)),
                    fold_key: endpoint_allowed,
                }
            )
        from_rank = _ent.tier_rank(from_tier)
        to_rank = _ent.tier_rank(to_tier)
        from_label = _ent.tier_label(from_tier)
        to_label = _ent.tier_label(to_tier)
        if from_tier == to_tier:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"

    allowed_count = sum(1 for r in path_out if r.get(fold_key))
    all_allowed = bool(path_out) and all(r.get(fold_key) for r in path_out)
    any_allowed = any(r.get(fold_key) for r in path_out)

    return {
        "from": from_tier,
        "from_label": from_label,
        "from_rank": from_rank,
        "to": to_tier,
        "to_label": to_label,
        "to_rank": to_rank,
        "direction": direction,
        axis: known,
        "unknown": unknown,
        "path": path_out,
        "kind": axis,
        "count": len(known),
        "path_length": len(path_out),
        "allowed_count": allowed_count,
        "all_allowed": all_allowed,
        "any_allowed": any_allowed,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_bundle_at_path_batch_fallback(
    axis: str,
    from_tier: str,
    to_tokens: list,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the path-batch complement
    endpoints ``/api/entitlement/missing-features-at-path-batch`` and
    ``/api/entitlement/missing-runtimes-at-path-batch``.

    Batch-path sibling of :func:`_missing_bundle_at_path_fallback`. On
    any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]``
    and every rollup zeroed / dropped so a pricing-comparison surface
    that lost the resolver doesn't silently render a denial matrix it
    can no longer justify. ``from`` / ``unknown_tiers`` echo the
    caller's input so a debugging tooltip can still surface the
    dropped destinations, and ``unknown`` echoes the axis tokens.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        axis: [],
        "unknown": list(tokens),
        "unknown_tiers": list(to_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_bundle_at_path_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-features-at-path-batch`` /
    ``/api/entitlement/missing-runtimes-at-path-batch``.

    Batch-path sibling of :func:`_missing_bundle_at_path_body` (which
    walks the rungs between ONE ``(from, to)`` pair): this walks the
    rungs between ONE ``from`` and N candidate destinations in ONE
    round-trip. Multi-destination twin of the path-shaped
    ``/tier-unlocks-path-batch`` (same fan-out shape, per-item denial
    body instead of marginal-grant body) and matrix-shaped cousin of
    ``/missing-features-at-batch`` (which fans out over perspective
    tiers rather than destinations).

    Envelope shape (byte-stable across every input branch)::

        {
          "from":               "<tier id>",
          "from_label":         "...",
          "from_rank":          <int>,
          "features"/"runtimes":[<known ids>],
          "unknown":            [<axis tokens dropped>],
          "unknown_tiers":      [<destination ids dropped>],
          "kind":               "features"/"runtimes",
          "count":              <int>,                # len(known)
          "tiers": [
            {
              "to":          "<id>",
              "to_label":    "...",
              "to_rank":     <int>,
              "direction":   "upgrade" | "downgrade" | "lateral" | "identity",
              "path":        [<missing_*_at_path row>, ...],
              "path_length": <int>,
              "any_missing": <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/missing-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` (and the runtime twin) for the same ``(from, to,
    bundle)`` triple -- a parity test pins this so the scalar and
    batch path what-if complement helpers cannot drift.

    Runtime-axis alias canonicalisation is applied per-token upstream
    of the strict scalar (:func:`missing_runtimes_at_path_batch`
    inherits :func:`missing_runtimes_at_path`'s strict-alias posture
    at scalar layer), matching the sibling ``/missing-runtimes-at-path``
    upstream-canonicalise pattern -- alias-and-canonical pair dedups
    to ONE entry in ``runtimes`` before the scalar sees it, so it
    also dedups to ONE entry in every rung's ``missing`` list.

    Per-destination ``any_missing`` is ``True`` iff any rung in that
    destination's ``path`` has a non-empty ``missing`` list OR the
    top-level ``unknown`` list is non-empty (matches the singular
    ``/missing-features-at-path`` rollup semantics applied per
    destination). ``required_tier`` folds through
    :func:`min_tier_for_features` / :func:`min_tier_for_runtimes`
    against the KNOWN-only subset (matches the sibling
    ``/missing-features-at-path`` envelope's rollup contract),
    independent of any per-destination endpoint.

    Never 4xxs (missing / blank / unknown ``from`` -> 200 with
    ``tiers=[]``, matching the sibling ``/missing-features-at-batch``
    posture -- a pricing-comparison matrix binds ``tiers`` directly
    without a pre-validation round-trip). Never 5xxs: any helper
    blowup collapses to :func:`_missing_bundle_at_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _parse_csv_arg("to")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    if axis == "features":
        batch = _ent.missing_features_at_path_batch(
            from_tier, to_tokens, canon_tokens
        )
    else:
        batch = _ent.missing_runtimes_at_path_batch(
            from_tier, to_tokens, canon_tokens
        )

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    if batch is None:
        # Unknown / blank ``from`` -- fall through to the empty-tiers envelope
        # so the client never 4xxs, matching the ``/missing-*-at-batch``
        # posture. ``unknown_tiers`` still echoes the caller's ``to=`` set for
        # debugging.
        return {
            "from": from_tier,
            "from_label": None,
            "from_rank": -1,
            axis: known,
            "unknown": unknown,
            "unknown_tiers": list(to_tokens),
            "kind": axis,
            "count": len(known),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        any_missing = bool(unknown) or any(
            bool(r.get("missing")) for r in path
        )
        tiers_out.append(
            {
                "to": row.get("to"),
                "to_label": row.get("to_label"),
                "to_rank": row.get("to_rank", -1),
                "direction": row.get("direction"),
                "path": path,
                "path_length": len(path),
                "any_missing": any_missing,
            }
        )

    return {
        "from": from_tier,
        "from_label": _ent.tier_label(from_tier),
        "from_rank": _ent.tier_rank(from_tier),
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_bundle_at_path_batch_fallback(
    axis: str,
    from_tier: str,
    to_tokens: list,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the path-batch boolean-fold
    endpoints ``/api/entitlement/has-features-at-path-batch`` and
    ``/api/entitlement/has-runtimes-at-path-batch``.

    Path-batch sibling of :func:`_has_bundle_at_path_fallback` and
    boolean-fold complement of :func:`_missing_bundle_at_path_batch_fallback`.
    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]``
    and every rollup fail-closed (``allowed_count`` / ``all_allowed`` /
    ``any_allowed`` zeroed) so a pricing-comparison surface that lost
    the resolver never silently renders a bundle grant matrix it cannot
    justify -- matches the sibling ``/has-features-at-batch`` fallback's
    fail-closed posture byte-for-byte. ``from`` / ``unknown_tiers`` echo
    the caller's input so a debugging tooltip can still surface the
    dropped destinations, and ``unknown`` echoes the axis tokens.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        axis: [],
        "unknown": list(tokens),
        "unknown_tiers": list(to_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_at_path_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/has-features-at-path-batch`` /
    ``/api/entitlement/has-runtimes-at-path-batch``.

    Path-batch sibling of :func:`_has_bundle_at_path_body` (which walks
    the rungs between ONE ``(from, to)`` pair): this walks the rungs
    between ONE ``from`` and N candidate destinations in ONE round-trip.
    Multi-destination twin of the path-shaped
    ``/missing-features-at-path-batch`` (same fan-out shape, per-rung
    fold-boolean body instead of per-item denial body) and matrix-shaped
    cousin of ``/has-features-at-batch`` (which fans out over
    perspective tiers rather than destinations).

    Envelope shape (byte-stable across every input branch)::

        {
          "from":               "<tier id>",
          "from_label":         "...",
          "from_rank":          <int>,
          "features"/"runtimes":[<known ids>],
          "unknown":            [<axis tokens dropped>],
          "unknown_tiers":      [<destination ids dropped>],
          "kind":               "features"/"runtimes",
          "count":              <int>,                # len(known)
          "tiers": [
            {
              "to":            "<id>",
              "to_label":      "...",
              "to_rank":       <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_*_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,
              "all_allowed":   <bool>,
              "any_allowed":   <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/has-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` (and the runtime twin) for the same ``(from, to,
    bundle)`` triple -- a parity test pins this so the scalar and
    batch path what-if boolean-fold helpers cannot drift.

    Runtime-axis alias canonicalisation is applied per-token upstream
    of the strict scalar (:func:`has_runtimes_at_path_batch` inherits
    :func:`has_runtimes_at_path`'s strict-alias posture at scalar
    layer), matching the sibling ``/has-runtimes-at-path``
    upstream-canonicalise pattern -- alias-and-canonical pair dedups
    to ONE entry in ``runtimes`` before the scalar sees it, so it
    also dedups to ONE fold input on every rung of every destination.

    Endpoint-level fold semantics inherit :func:`_has_bundle_at_path_body`
    byte-for-byte: an unknown token in the bundle collapses the
    endpoint-level fold to ``False`` on EVERY rung of EVERY destination
    (``unknown != []`` -> every row's ``has_<axis>_at`` reads ``False``),
    so a bundle typo fails-closed at the endpoint layer the same way it
    fails-closed on the singular ``/has-features-at-path`` endpoint.

    Per-destination ``allowed_count`` is the sum of per-row boolean
    grants across that destination's walked path so a walkthrough header
    can render "granted at 2 of 4 rungs" off one field per destination.
    Per-destination ``all_allowed`` folds per-row ``has_<axis>_at``
    AND-wise (empty ``path`` -> False, to inherit the fail-closed fold
    posture the singular :func:`has_features_at` uses on empty input).
    Per-destination ``any_allowed`` folds OR-wise (empty ``path`` ->
    False).

    ``required_tier`` folds through :func:`min_tier_for_features` /
    :func:`min_tier_for_runtimes` against the KNOWN-only subset
    (matches the sibling ``/has-features-at-batch`` envelope's rollup
    contract), independent of any per-destination endpoint.

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/has-features-at-batch`` posture -- a pricing-comparison
    matrix binds ``tiers`` directly without a pre-validation
    round-trip). Never 5xxs: any helper blowup collapses to
    :func:`_has_bundle_at_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _parse_csv_arg("to")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    if axis == "features":
        batch = _ent.has_features_at_path_batch(
            from_tier, to_tokens, canon_tokens
        )
    else:
        batch = _ent.has_runtimes_at_path_batch(
            from_tier, to_tokens, canon_tokens
        )

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    fold_key = f"has_{axis}_at"

    if batch is None:
        # Unknown / blank ``from`` -- fall through to the empty-tiers envelope
        # so the client never 4xxs, matching the ``/has-*-at-batch`` posture.
        # ``unknown_tiers`` still echoes the caller's ``to=`` set for
        # debugging.
        return {
            "from": from_tier,
            "from_label": None,
            "from_rank": -1,
            axis: known,
            "unknown": unknown,
            "unknown_tiers": list(to_tokens),
            "kind": axis,
            "count": len(known),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    # An unknown token in the bundle collapses the endpoint-level fold
    # to ``False`` on EVERY rung of EVERY destination (matches the
    # singular ``_has_bundle_at_path_body`` posture: ``unknown != []`` ->
    # ``has_*_at=False`` on every row).
    endpoint_ok = not unknown and bool(known)

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            raw_path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        path_out: list[dict] = []
        for r in raw_path:
            try:
                tid = r.get("tier")
                row_allowed = bool(r.get(fold_key, False))
            except AttributeError:
                continue
            endpoint_allowed = row_allowed and endpoint_ok
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": r.get("tier_label", _ent.tier_label(tid)),
                    "tier_rank": r.get("tier_rank", _ent.tier_rank(tid)),
                    fold_key: endpoint_allowed,
                }
            )
        allowed_count = sum(1 for r in path_out if r.get(fold_key))
        all_allowed = bool(path_out) and all(
            r.get(fold_key) for r in path_out
        )
        any_allowed = any(r.get(fold_key) for r in path_out)
        tiers_out.append(
            {
                "to": row.get("to"),
                "to_label": row.get("to_label"),
                "to_rank": row.get("to_rank", -1),
                "direction": row.get("direction"),
                "path": path_out,
                "path_length": len(path_out),
                "allowed_count": allowed_count,
                "all_allowed": all_allowed,
                "any_allowed": any_allowed,
            }
        )

    return {
        "from": from_tier,
        "from_label": _ent.tier_label(from_tier),
        "from_rank": _ent.tier_rank(from_tier),
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_bundle_from_path_batch_fallback(
    axis: str,
    to_tier: str,
    from_tokens: list,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the source-side path-batch
    boolean-fold endpoints
    ``/api/entitlement/has-features-from-path-batch`` and
    ``/api/entitlement/has-runtimes-from-path-batch``.

    Source-axis batch sibling of :func:`_has_bundle_at_path_batch_fallback`
    (destination-side batch) and boolean-fold analogue of
    :func:`_missing_bundle_at_path_batch_fallback` for the source axis.
    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]`` and
    every rollup zeroed / dropped so a source-side upgrade-comparison
    surface that lost the resolver doesn't silently render a grant
    matrix it can no longer justify. ``to`` / ``unknown_tiers`` echo the
    caller's input so a debugging tooltip can still surface the dropped
    sources, and ``unknown`` echoes the axis tokens.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        axis: [],
        "unknown": list(tokens),
        "unknown_tiers": list(from_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_bundle_from_path_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/has-features-from-path-batch`` /
    ``/api/entitlement/has-runtimes-from-path-batch``.

    Source-axis batch sibling of :func:`_has_bundle_at_path_batch_body`
    (which walks the rungs between ONE ``from`` and N candidate
    destinations): this walks the rungs between N candidate sources and
    ONE ``to`` in ONE round-trip. Mirror-direction twin of the
    ``/has-*-at-path-batch`` family and boolean-fold complement of the
    source-side missing family at the batch layer.

    Envelope shape (byte-stable across every input branch)::

        {
          "to":                 "<tier id>",
          "to_label":           "...",
          "to_rank":            <int>,
          "features"/"runtimes":[<known ids>],
          "unknown":            [<axis tokens dropped>],
          "unknown_tiers":      [<source ids dropped>],
          "kind":               "features"/"runtimes",
          "count":              <int>,                # len(known)
          "tiers": [
            {
              "from":          "<id>",
              "from_label":    "...",
              "from_rank":     <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_*_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,                 # rungs where fold=True
              "all_allowed":   <bool>,                # every rung True
              "any_allowed":   <bool>,                # any rung True
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/has-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` (and the runtime twin) for the same ``(from, to,
    bundle)`` triple -- a parity test pins this so the scalar and
    source-batch path what-if boolean-fold helpers cannot drift.

    Runtime-axis alias canonicalisation is applied per-token upstream of
    the strict scalar (:func:`has_runtimes_from_path_batch` inherits
    :func:`has_runtimes_at_path`'s strict-alias posture at scalar layer),
    matching the sibling ``/has-runtimes-at-path`` upstream-canonicalise
    pattern -- alias-and-canonical pair dedups to ONE entry in
    ``runtimes`` before the scalar sees it, so it also dedups to ONE
    fold input on every rung.

    Endpoint-level fold semantics inherit :func:`_has_bundle_at_path_body`
    byte-for-byte: an unknown token in the bundle collapses per-rung
    ``has__at`` to ``False`` on EVERY rung of EVERY source (fail-closed
    at the endpoint layer the same way the destination-side batch fails-
    closed on ``/has-features-at-path``).

    Per-source ``allowed_count`` / ``all_allowed`` / ``any_allowed``
    fold over that source's ``path`` rows exactly like the singular
    ``/has-features-at-path`` fold-rollup does over its own path (an
    empty path -> ``allowed_count=0`` / ``all_allowed=False`` /
    ``any_allowed=False``, matching the identity branch). ``required_tier``
    folds through :func:`min_tier_for_features` /
    :func:`min_tier_for_runtimes` against the KNOWN-only subset (matches
    the sibling ``/has-features-at-path`` envelope's rollup contract).

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-unknown
    source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-at-batch`` posture -- a source-side comparison
    matrix binds ``tiers`` directly without a pre-validation round-
    trip). Never 5xxs: any helper blowup collapses to
    :func:`_has_bundle_from_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_to = request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    from_tokens = _parse_csv_arg("from")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    # Endpoint-level fail-closed on any unknown bundle token, mirroring the
    # ``/has-features-at-path-batch`` posture: pass an obviously-unknown
    # canonical token to the scalar so every rung of every source folds to
    # False. This preserves the "typo -> denial on every rung" contract at
    # the endpoint layer even after alias canonicalisation dropped duplicates.
    if unknown:
        scalar_tokens = ["__clawmetry_unknown_bundle_token__"]
    else:
        scalar_tokens = list(canon_tokens)

    if axis == "features":
        batch = _ent.has_features_from_path_batch(
            from_tokens, to_tier, scalar_tokens
        )
    else:
        batch = _ent.has_runtimes_from_path_batch(
            from_tokens, to_tier, scalar_tokens
        )

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    if batch is None:
        return {
            "to": to_tier,
            "to_label": None,
            "to_rank": -1,
            axis: known,
            "unknown": unknown,
            "unknown_tiers": list(from_tokens),
            "kind": axis,
            "count": len(known),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    fold_key = "has_features_at" if axis == "features" else "has_runtimes_at"
    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        allowed_count = sum(1 for r in path if bool(r.get(fold_key)))
        path_length = len(path)
        all_allowed = path_length > 0 and allowed_count == path_length
        any_allowed = allowed_count > 0
        tiers_out.append(
            {
                "from": row.get("from"),
                "from_label": row.get("from_label"),
                "from_rank": row.get("from_rank", -1),
                "direction": row.get("direction"),
                "path": path,
                "path_length": path_length,
                "allowed_count": allowed_count,
                "all_allowed": all_allowed,
                "any_allowed": any_allowed,
            }
        )

    return {
        "to": to_tier,
        "to_label": _ent.tier_label(to_tier),
        "to_rank": _ent.tier_rank(to_tier),
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_bundle_from_path_batch_fallback(
    axis: str,
    to_tier: str,
    from_tokens: list,
    tokens: list,
) -> dict:
    """OSS-free / never-5xx envelope for the source-side path-batch
    complement endpoints
    ``/api/entitlement/missing-features-from-path-batch`` and
    ``/api/entitlement/missing-runtimes-from-path-batch``.

    Source-axis batch sibling of :func:`_missing_bundle_at_path_batch_fallback`
    (destination-side batch) and complement-shaped sibling of
    :func:`_has_bundle_from_path_batch_fallback` (boolean-fold source-
    batch). On any resolver / helper blowup the endpoint still returns
    200 with the same envelope shape as the happy path but with
    ``tiers=[]`` and every rollup zeroed / dropped so a source-side
    plan-change comparison surface that lost the resolver doesn't
    silently render a denial matrix it can no longer justify. ``to`` /
    ``unknown_tiers`` echo the caller's input so a debugging tooltip
    can still surface the dropped sources, and ``unknown`` echoes the
    axis tokens.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        axis: [],
        "unknown": list(tokens),
        "unknown_tiers": list(from_tokens),
        "kind": axis,
        "count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_bundle_from_path_batch_body(axis: str) -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-features-from-path-batch`` /
    ``/api/entitlement/missing-runtimes-from-path-batch``.

    Source-axis batch sibling of :func:`_missing_bundle_at_path_batch_body`
    (which walks the rungs between ONE ``from`` and N candidate
    destinations): this walks the rungs between N candidate sources and
    ONE ``to`` in ONE round-trip. Mirror-direction twin of the
    ``/missing-*-at-path-batch`` family and complement-shaped sibling
    of the source-side boolean-fold ``/has-*-from-path-batch`` family
    at the batch layer, in the same relationship
    ``/missing-features-at-path`` has to ``/has-features-at-path``.

    Envelope shape (byte-stable across every input branch)::

        {
          "to":                 "<tier id>",
          "to_label":           "...",
          "to_rank":            <int>,
          "features"/"runtimes":[<known ids>],
          "unknown":            [<axis tokens dropped>],
          "unknown_tiers":      [<source ids dropped>],
          "kind":               "features"/"runtimes",
          "count":              <int>,                # len(known)
          "tiers": [
            {
              "from":        "<id>",
              "from_label":  "...",
              "from_rank":   <int>,
              "direction":   "upgrade" | "downgrade" | "lateral" | "identity",
              "path":        [<missing_*_at_path row>, ...],
              "path_length": <int>,
              "any_missing": <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,               # -1 when null
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row byte-equals a row from
    ``/missing-features-at-path?from=<from>&to=<to>&features=<bundle>``'s
    ``.path`` (and the runtime twin) for the same ``(from, to,
    bundle)`` triple -- a parity test pins this so the scalar and
    source-batch path what-if complement helpers cannot drift.

    Runtime-axis alias canonicalisation is applied per-token upstream
    of the strict scalar (:func:`missing_runtimes_from_path_batch`
    inherits :func:`missing_runtimes_at_path`'s strict-alias posture
    at scalar layer), matching the sibling ``/missing-runtimes-at-path``
    upstream-canonicalise pattern -- alias-and-canonical pair dedups
    to ONE entry in ``runtimes`` before the scalar sees it, so it
    also dedups to ONE entry in every per-source rung's ``missing``
    list.

    Per-source ``any_missing`` is ``True`` iff any rung in that
    source's ``path`` has a non-empty ``missing`` list OR the
    top-level ``unknown`` list is non-empty (matches the singular
    ``/missing-features-at-path`` rollup semantics applied per
    source, and mirrors the destination-side batch's per-destination
    ``any_missing`` derivation byte-for-byte). ``required_tier`` folds
    through :func:`min_tier_for_features` / :func:`min_tier_for_runtimes`
    against the KNOWN-only subset (matches the sibling
    ``/missing-features-at-path`` envelope's rollup contract),
    independent of any per-source endpoint.

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-from-path-batch`` posture -- a source-side
    comparison matrix binds ``tiers`` directly without a pre-
    validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_missing_bundle_from_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_to = request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    from_tokens = _parse_csv_arg("from")
    param = "features" if axis == "features" else "runtimes"
    tokens = _parse_csv_arg(param)

    known: list = []
    unknown: list = []
    if axis == "features":
        for fid in tokens:
            if fid in _ent.ALL_FEATURES:
                if fid not in known:
                    known.append(fid)
            elif fid not in unknown:
                unknown.append(fid)
        canon_tokens: list = list(tokens)
        required = _ent.min_tier_for_features(known) if known else None
    else:
        canon_tokens = []
        canon_seen: set = set()
        for rid_raw in tokens:
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in canon_seen:
                continue
            canon_seen.add(rid)
            canon_tokens.append(rid)
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known:
                    known.append(rid)
            elif rid not in unknown:
                unknown.append(rid_raw)
        required = _ent.min_tier_for_runtimes(known) if known else None

    if axis == "features":
        batch = _ent.missing_features_from_path_batch(
            from_tokens, to_tier, canon_tokens
        )
    else:
        batch = _ent.missing_runtimes_from_path_batch(
            from_tokens, to_tier, canon_tokens
        )

    env = _resolver_envelope(_ent)
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    if batch is None:
        return {
            "to": to_tier,
            "to_label": None,
            "to_rank": -1,
            axis: known,
            "unknown": unknown,
            "unknown_tiers": list(from_tokens),
            "kind": axis,
            "count": len(known),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        any_missing = bool(unknown) or any(
            bool(r.get("missing")) for r in path
        )
        tiers_out.append(
            {
                "from": row.get("from"),
                "from_label": row.get("from_label"),
                "from_rank": row.get("from_rank", -1),
                "direction": row.get("direction"),
                "path": path,
                "path_length": len(path),
                "any_missing": any_missing,
            }
        )

    return {
        "to": to_tier,
        "to_label": _ent.tier_label(to_tier),
        "to_rank": _ent.tier_rank(to_tier),
        axis: known,
        "unknown": unknown,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "kind": axis,
        "count": len(known),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_all_fallback() -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all``.

    Mirrors the fail-closed posture the sibling ``_has_bundle_fallback``
    carries: on a resolver blowup the endpoint still returns 200 with the
    same envelope shape as the happy path, but ``has_all`` / ``allowed``
    ``False`` and every axis marked ``supplied=False`` so a paywall tile
    that lost the resolver doesn't silently grant a mixed bundle it can
    no longer evaluate.
    """
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": [],
        "unknown_runtimes": [],
        "supplied_axes": [],
        "supplied_count": 0,
        "has_all": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
        "upgrade_required": False,
    }

def _has_all_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all``.

    Aggregate mixed-axis fold sibling of ``_has_bundle_body`` (which folds
    ONE single-axis CSV). Applies the same per-axis normalisation each
    single-axis endpoint already does -- CSV known/unknown split for
    features and runtimes (runtime-alias canonicalisation upstream so
    ``claude-code`` -> ``claude_code``); capacity axes parsed via
    :func:`_parse_capacity_arg` so a blank / non-int value collapses the
    axis to ``False`` in the fold rather than short-circuiting through
    the underlying scalar's ``retention_days=None`` "unlimited" branch
    (which would mis-route the aggregate to Enterprise-only).

    Every axis is OPTIONAL -- a caller can supply any non-empty subset
    of the five kwargs and the fold answers off just those axes. The
    envelope always carries every axis' slot for byte-stable shape
    across every URL branch (``None`` / ``[]`` for unsupplied axes).

    The scalar boolean ``has_all`` is delegated to
    :func:`clawmetry.entitlements.has_all` against the SUPPLIED axis
    values (unsupplied axes pass ``None`` verbatim), so this endpoint
    stays byte-parity with the module scalar. Unknown feature / runtime
    tokens collapse ``has_all`` to ``False`` (matches
    :func:`has_features` / :func:`has_runtimes` typo posture); a caller
    can still surface the offending tokens via ``unknown_features`` /
    ``unknown_runtimes``. Missing / blank / non-int capacity value on a
    SUPPLIED axis collapses ``has_all`` to ``False`` (matches the
    singular capacity scalars' strict-``False`` typo posture); a UI can
    distinguish "supplied but blank" from "unsupplied" via the
    ``supplied_axes`` list.

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the same
    supplied axes (known ids only on the grant axes) for parity with
    the singular ``/api/entitlement/required-tier`` envelope.
    """
    from clawmetry import entitlements as _ent

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Endpoint-layer short-circuits to ``False`` (matches the singular
    # scalars' strict-``False`` typo posture without handing the module
    # scalar a sentinel):
    #   * a supplied-but-unparseable capacity axis
    #   * unknown feature / runtime tokens on a supplied grant axis
    #   * a supplied grant axis whose CSV was empty / all-unknown
    # Otherwise delegate to the module scalar off the CANONICALISED
    # known-only lists so envelope-vs-scalar parity holds byte-exact
    # (runtime-alias canonicalisation is an endpoint-layer concern; the
    # singular :func:`has_runtime` scalar strict-checks against
    # :data:`ALL_RUNTIMES` and would otherwise reject ``claude-code``).
    if (
        (channels_present and not channels_ok)
        or (retention_present and not retention_ok)
        or (nodes_present and not nodes_ok)
        or (features_supplied and (unknown_features or not known_features))
        or (runtimes_supplied and (unknown_runtimes or not known_runtimes))
    ):
        has_flag = False
    else:
        has_flag = _ent.has_all(
            features=known_features if features_supplied else None,
            runtimes=known_runtimes if runtimes_supplied else None,
            channels=channels_n if channels_present else None,
            retention_days=retention_n if retention_present else None,
            nodes=nodes_n if nodes_present else None,
        )

    # ``required_tier`` folds through ``min_tier_for_all`` against the
    # KNOWN-only subsets for parity with ``/api/entitlement/required-tier``
    # (which resolves off the known/unknown split, not raw input).
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    return {
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "has_all": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

_HAS_ALL_AT_KEYS = (
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "has_all_at",
    "allowed",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
)

def _has_all_at_fallback(perspective_tier: str) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-at``.

    Mirrors :func:`_has_all_fallback` on the LIVE sibling with the
    perspective slot layered on top: on a resolver blowup the endpoint
    still returns 200 with the same envelope shape as the happy path,
    but ``has_all_at`` / ``allowed`` ``False`` and every axis empty so a
    pricing-matrix cell that lost the resolver doesn't silently grant a
    hypothetical bundle it can no longer evaluate.

    ``perspective_tier_label`` / ``perspective_tier_rank`` fall back to
    ``None`` / ``-1`` (matches the sibling ``min-tier-batch-at``
    fallback envelope) so the envelope shape stays byte-stable across
    every input branch, including the resolver-blowup fallback.
    """
    return {
        "perspective_tier": perspective_tier,
        "perspective_tier_label": None,
        "perspective_tier_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": [],
        "unknown_runtimes": [],
        "supplied_axes": [],
        "supplied_count": 0,
        "has_all_at": False,
        "allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_at_body(perspective_tier: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all-at``.

    Perspective-shaped sibling of :func:`_has_all_body`: applies the same
    per-axis normalisation (CSV known/unknown split for features and
    runtimes with runtime-alias canonicalisation; capacity axes parsed
    via :func:`_parse_capacity_arg` so a blank / non-int value collapses
    the axis to ``False`` in the fold) then delegates to
    :func:`clawmetry.entitlements.has_all_at` against the SUPPLIED axis
    values so this endpoint stays byte-parity with the module scalar.

    Every axis is OPTIONAL -- a caller can supply any (or none) of the
    five kwargs; the fold answers off just those axes and every
    unsupplied axis is skipped (contributes ``True`` to the fold). The
    envelope always carries every axis' slot for byte-stable shape
    across every URL branch. No-axes-supplied collapses ``has_all_at``
    to ``False`` (matches :func:`has_all_at` empty-``False`` posture
    byte-for-byte).

    Grace-independent by construction: :func:`has_all_at` delegates to
    the static-per-tier ``_at`` singular scalars, so this endpoint's
    ``has_all_at`` bit is IDENTICAL under grace vs enforce for the same
    (perspective, bundle) pair -- diverges deliberately from the LIVE
    ``/has-all`` sibling (which grants every fully-known bundle in
    grace via the resolver's grace pass-through). Whole point of the
    ``_at`` slot: ``/has-all-at?tier=oss&features=fleet`` returns
    ``has_all_at=false`` even in grace (because OSS statically does not
    grant ``fleet``), whereas LIVE ``/has-all?features=fleet`` reports
    ``true`` for it via :attr:`Entitlement.grace` pass-through.

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-only
    subsets for parity with the LIVE ``/api/entitlement/has-all``
    envelope. Perspective-independent by design (delegates to
    :func:`min_tier_for_all`, which walks the static per-tier caps);
    matches ``min_tier_for_all_at``'s pinned parity contract.
    """
    from clawmetry import entitlements as _ent

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    if (
        (channels_present and not channels_ok)
        or (retention_present and not retention_ok)
        or (nodes_present and not nodes_ok)
        or (features_supplied and (unknown_features or not known_features))
        or (runtimes_supplied and (unknown_runtimes or not known_runtimes))
    ):
        has_flag = False
    else:
        has_flag = _ent.has_all_at(
            perspective_tier,
            features=known_features if features_supplied else None,
            runtimes=known_runtimes if runtimes_supplied else None,
            channels=channels_n if channels_present else None,
            retention_days=retention_n if retention_present else None,
            nodes=nodes_n if nodes_present else None,
        )

    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    return {
        "perspective_tier": perspective_tier,
        "perspective_tier_label": _ent.tier_label(perspective_tier),
        "perspective_tier_rank": _ent.tier_rank(perspective_tier),
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "has_all_at": bool(has_flag),
        "allowed": bool(has_flag),
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

_MISSING_ALL_AT_KEYS = (
    "perspective_tier",
    "perspective_tier_label",
    "perspective_tier_rank",
    "features",
    "runtimes",
    "channels",
    "retention_days",
    "nodes",
    "unknown_features",
    "unknown_runtimes",
    "supplied_axes",
    "supplied_count",
    "missing_count",
    "any_missing",
    "required_tier",
    "required_tier_label",
    "required_tier_rank",
    "current_tier",
    "current_tier_rank",
    "grace",
    "enforced",
)

def _missing_all_at_fallback(perspective_tier: str) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-at``.

    Mirrors :func:`_has_all_at_fallback` on the paired boolean-fold sibling
    with the ``has_all_at`` / ``allowed`` slots swapped for the row-detail
    ``missing_count`` / ``any_missing`` rollups: on a resolver blowup the
    endpoint still returns 200 with the same envelope shape as the happy
    path, but every per-axis missing slot empty and ``any_missing=False``
    so a paywall diagnostics tile that lost the resolver doesn't silently
    render a denial banner it can no longer justify.

    ``perspective_tier_label`` / ``perspective_tier_rank`` fall back to
    ``None`` / ``-1`` (matches the sibling ``has-all-at`` fallback
    envelope) so the envelope shape stays byte-stable across every input
    branch, including the resolver-blowup fallback.
    """
    return {
        "perspective_tier": perspective_tier,
        "perspective_tier_label": None,
        "perspective_tier_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": [],
        "unknown_runtimes": [],
        "supplied_axes": [],
        "supplied_count": 0,
        "missing_count": 0,
        "any_missing": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_at_body(perspective_tier: str) -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-all-at``.

    Perspective-shaped row-detail sibling of :func:`_has_all_at_body`:
    applies the same per-axis normalisation (CSV known/unknown split for
    features and runtimes with runtime-alias canonicalisation; capacity
    axes parsed via :func:`_parse_capacity_arg` so a blank / non-int value
    surfaces the raw string in the per-axis missing slot) then delegates
    to :func:`clawmetry.entitlements.missing_all_at` against the SUPPLIED
    axis values so this endpoint stays byte-parity with the module
    scalar on the per-axis missing detail.

    Every axis is OPTIONAL -- a caller can supply any (or none) of the
    five kwargs; the envelope always carries every axis' slot for
    byte-stable shape across every URL branch. No-axes-supplied returns
    every per-axis slot empty and ``any_missing=False`` (matches
    :func:`missing_all_at` empty-per-axis posture byte-for-byte and
    mirrors ``/has-all-at``'s empty-``False`` posture).

    Grace-independent by construction: :func:`missing_all_at` delegates
    to the static-per-tier ``_at`` singular scalars, so this endpoint's
    per-axis missing detail is IDENTICAL under grace vs enforce for the
    same (perspective, bundle) pair -- diverges deliberately from the
    LIVE ``/missing-all`` sibling (which reports every per-axis slot
    empty for a fully-known bundle in grace via the resolver's grace
    pass-through). Whole point of the ``_at`` slot:
    ``/missing-all-at?tier=oss&features=fleet`` returns
    ``features=["fleet"]`` even in grace (because OSS statically does
    not grant ``fleet``), whereas LIVE ``/missing-all?features=fleet``
    reports ``features=[]`` for it via :attr:`Entitlement.grace`
    pass-through.

    Unknown feature / runtime tokens are SURFACED inside the per-axis
    ``features`` / ``runtimes`` missing lists AND echoed in
    ``unknown_features`` / ``unknown_runtimes`` for a diagnostics
    tooltip (matches the LIVE ``/missing-all`` unknown-surface posture).
    A supplied-but-unparseable capacity axis surfaces the raw string in
    that slot so a UI can flag the typo.

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-only
    subsets for parity with the ``/has-all`` and ``/has-all-at``
    envelopes.
    """
    from clawmetry import entitlements as _ent

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Delegate per-grant-axis to the scalar so the endpoint stays
    # byte-parity with :func:`missing_all_at` on the known-only subsets;
    # unknown tokens are appended AFTER the scalar so the endpoint's
    # diagnostics surface is a strict superset of the module scalar's
    # (matches the LIVE ``/missing-all`` sibling posture byte-for-byte).
    features_missing: list = []
    if features_supplied:
        features_missing = list(
            _ent.missing_features_at(perspective_tier, known_features)
        )
        for token in unknown_features:
            if token not in features_missing:
                features_missing.append(token)

    runtimes_missing: list = []
    if runtimes_supplied:
        runtimes_missing = list(
            _ent.missing_runtimes_at(perspective_tier, known_runtimes)
        )
        for token in unknown_runtimes:
            if token not in runtimes_missing:
                runtimes_missing.append(token)

    # Capacity axes: raw string surfaces on a supplied-but-unparseable
    # value so a UI can flag the typo; otherwise the scalar's per-axis
    # missing rule (SUPPLIED int if denied, None otherwise).
    def _capacity_missing(present: bool, ok: bool, n, raw, denied_fn):
        if not present:
            return None
        if not ok:
            return raw
        try:
            return n if not denied_fn(perspective_tier, n) else None
        except Exception:
            return None

    channels_missing = _capacity_missing(
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
        _ent.has_channel_count_at,
    )
    retention_missing = _capacity_missing(
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
        _ent.has_retention_window_at,
    )
    nodes_missing = _capacity_missing(
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
        _ent.has_node_count_at,
    )

    missing_count = 0
    if features_missing:
        missing_count += 1
    if runtimes_missing:
        missing_count += 1
    if channels_missing is not None:
        missing_count += 1
    if retention_missing is not None:
        missing_count += 1
    if nodes_missing is not None:
        missing_count += 1

    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    return {
        "perspective_tier": perspective_tier,
        "perspective_tier_label": _ent.tier_label(perspective_tier),
        "perspective_tier_rank": _ent.tier_rank(perspective_tier),
        "features": features_missing,
        "runtimes": runtimes_missing,
        "channels": channels_missing,
        "retention_days": retention_missing,
        "nodes": nodes_missing,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "missing_count": missing_count,
        "any_missing": missing_count > 0,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_all_at_path_fallback(
    from_tier: str,
    to_tier: str,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-at-path``.

    Aggregate mixed-axis path sibling of :func:`_missing_bundle_at_path_fallback`
    (single-axis path) and row-detail complement of
    :func:`_has_all_at_path_fallback` (paired boolean-fold path). On any
    resolver / helper blowup the endpoint still returns 200 with the
    same envelope shape as the happy path, but ``path=[]`` and every
    row-detail rollup fail-open (``denied_count=0`` /
    ``all_denied=False`` / ``any_denied=False``) so a pricing-page
    walkthrough that lost the resolver never silently renders a denial
    banner it can no longer justify. ``from`` / ``to`` / caller-supplied
    token lists echo into the envelope + ``unknown_features`` /
    ``unknown_runtimes`` so a debugging tooltip still surfaces the
    caller-supplied set. ``direction`` collapses to ``"identity"`` when
    ``from == to`` (matches the happy-path branch for that case) and
    ``"unknown"`` otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "path": [],
        "path_length": 0,
        "denied_count": 0,
        "all_denied": False,
        "any_denied": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_at_path_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-all-at-path``.

    Aggregate mixed-axis path sibling of :func:`_missing_bundle_at_path_body`
    (single-axis path) and row-detail complement of
    :func:`_has_all_at_path_body` (paired boolean-fold path). Fixes ONE
    5-axis mixed bundle and sweeps across every rung between ``from=``
    and ``to=``, returning one row per rung with the per-axis missing
    rollup at that rung plus the surrounding path envelope.

    Envelope shape mirrors :func:`_has_all_at_path_body` for the walk-
    metadata keys (``from`` / ``from_label`` / ``from_rank`` / ``to`` /
    ``to_label`` / ``to_rank`` / ``direction`` / ``path``) so a client
    already binding the ``/has-all-at-path`` /
    ``/missing-features-at-path`` / ``/feature-catalog-path`` envelope
    can bind this one with the same shape reader. The mixed-axis bundle
    metadata (``features`` / ``runtimes`` / ``channels`` /
    ``retention_days`` / ``nodes`` / ``unknown_features`` /
    ``unknown_runtimes`` / ``supplied_axes`` / ``supplied_count``)
    matches :func:`_missing_all_at_body` byte-for-byte so a caller
    already binding the singular ``/missing-all-at`` envelope can bind
    this one with the same axis reader. The row-detail rollup
    (``denied_count`` / ``all_denied`` / ``any_denied``) mirrors
    :func:`_missing_bundle_at_path_body`'s ``any_missing`` extended
    over the aggregate mixed-axis fold, and the LIVE resolver envelope
    (``current_tier`` / ``current_tier_rank`` / ``grace`` /
    ``enforced``) matches the rest of the family.

    Per-rung row shape byte-equals the scalar
    :func:`clawmetry.entitlements.missing_all_at_path` return:
    ``{tier, tier_label, tier_rank, missing: {features, runtimes,
    channels, retention_days, nodes}}``. A parity test pins per-rung
    ``missing`` byte-equals ``/missing-all-at?tier=<rung>&<same
    bundle>`` for the same (rung, bundle) pair -- so any future
    contract change on either side has to update both.

    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream of the strict scalar. Alias-and-
    canonical pair dedups to ONE entry in ``runtimes`` and therefore
    ONE entry in every rung's per-axis missing list.

    Endpoint-level typo posture: unknown feature / runtime tokens are
    SURFACED inside each rung's per-axis ``missing["features"]`` /
    ``missing["runtimes"]`` list AND echoed in ``unknown_features`` /
    ``unknown_runtimes`` for a diagnostics tooltip (matches
    :func:`_missing_all_at_body` unknown-surface posture byte-for-byte).
    A supplied-but-unparseable capacity axis surfaces the raw string in
    that rung's per-axis capacity slot on every rung so a UI can flag
    the typo -- the row-detail complement of the boolean-fold sibling's
    fail-closed-``False`` posture.

    ``denied_count`` sums the count of rungs that carry ANY per-axis
    denial across the walked path so a walkthrough header can render
    "denied at 2 of 4 rungs" off one field. ``all_denied`` folds per-
    row any-denial AND-wise (empty ``path`` -> ``False`` to mirror the
    boolean-fold sibling's empty-path posture). ``any_denied`` folds
    OR-wise (empty ``path`` -> ``False``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/missing-all-at`` and
    ``/has-all-at-path`` envelopes' rollup contract) NOT the path
    endpoints -- the rollup answers "what's the cheapest tier that
    grants this whole bundle" independent of the walked window so a
    caller can pin the two-way comparison (path window vs cheapest-
    grant tier) off ONE round-trip.

    ``direction`` mirrors :func:`_has_all_at_path_body`'s values:
    ``upgrade`` | ``downgrade`` | ``lateral`` | ``identity`` |
    ``unknown``.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown /
    non-int bundle -> 200 with ``path=[]`` on the unknown-endpoint
    branch, or every rung's per-axis missing surfaces the unknown token
    on the unknown-token branch, matching the sibling
    ``/missing-features-at-path`` posture). Never 5xxs: any helper
    blowup collapses to :func:`_missing_all_at_path_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Delegate the walk to the scalar. Pass CANONICAL known-only token
    # lists (upstream alias canonicalisation matches the sibling
    # ``/missing-all-at``); the scalar answers off those. Unknown token
    # / non-int capacity surfacing is layered ON TOP per-row below so
    # the endpoint diagnostics surface is a strict superset of the
    # module scalar's (matches the LIVE ``/missing-all`` / singular
    # ``/missing-all-at`` sibling posture byte-for-byte).
    path = _ent.missing_all_at_path(
        from_tier,
        to_tier,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]

    if path is None:
        # Unknown endpoint(s) -- fall through to the empty-path envelope
        # so the client never 4xxs; ``direction`` reads ``"unknown"``.
        direction = "unknown"
        path_out: list = []
        from_label = None
        to_label = None
        from_rank = -1
        to_rank = -1
    else:
        path_out = []
        for row in path:
            try:
                tid = row.get("tier")
                base_missing = row.get("missing") or {}
            except AttributeError:
                continue

            feat_missing: list = list(base_missing.get("features") or [])
            for token in unknown_features:
                if token not in feat_missing:
                    feat_missing.append(token)

            rt_missing: list = list(base_missing.get("runtimes") or [])
            for token in unknown_runtimes:
                if token not in rt_missing:
                    rt_missing.append(token)

            # Non-int capacity: surface the raw string on EVERY rung
            # (row-detail typo posture, mirrors the singular
            # ``/missing-all-at`` capacity branch); parseable-and-
            # denied surfaces the int; unsupplied / parseable-and-
            # granted stays None.
            if channels_present and not channels_ok:
                channels_slot = channels_raw
            else:
                channels_slot = base_missing.get("channels")
            if retention_present and not retention_ok:
                retention_slot = retention_raw
            else:
                retention_slot = base_missing.get("retention_days")
            if nodes_present and not nodes_ok:
                nodes_slot = nodes_raw
            else:
                nodes_slot = base_missing.get("nodes")

            missing_dict = {
                "features": feat_missing,
                "runtimes": rt_missing,
                "channels": channels_slot,
                "retention_days": retention_slot,
                "nodes": nodes_slot,
            }
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                    "tier_rank": row.get("tier_rank", _ent.tier_rank(tid)),
                    "missing": missing_dict,
                }
            )
        from_rank = _ent.tier_rank(from_tier)
        to_rank = _ent.tier_rank(to_tier)
        from_label = _ent.tier_label(from_tier)
        to_label = _ent.tier_label(to_tier)
        if from_tier == to_tier:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"

    def _row_any_denied(row) -> bool:
        m = row.get("missing") or {}
        for k, v in m.items():
            if isinstance(v, list):
                if v:
                    return True
            elif v is not None:
                return True
        return False

    denied_count = sum(1 for r in path_out if _row_any_denied(r))
    all_denied = bool(path_out) and all(_row_any_denied(r) for r in path_out)
    any_denied = any(_row_any_denied(r) for r in path_out)

    # Required-tier rollup: fold through min_tier_for_all against the
    # KNOWN-only subset (matches ``/missing-all-at`` byte-for-byte). If
    # the bundle is all-unknown / no-axes-supplied the rollup collapses
    # to None -- matches the singular endpoint.
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    return {
        "from": from_tier,
        "from_label": from_label,
        "from_rank": from_rank,
        "to": to_tier,
        "to_label": to_label,
        "to_rank": to_rank,
        "direction": direction,
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "path": path_out,
        "path_length": len(path_out),
        "denied_count": denied_count,
        "all_denied": all_denied,
        "any_denied": any_denied,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_all_at_batch_fallback(
    tier_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-at-batch``.

    Mixed-axis batch sibling of :func:`_has_all_at_fallback` (single-
    perspective) and :func:`_has_bundle_at_batch_fallback` (single-axis
    batch). On any resolver / helper blowup the endpoint still returns
    200 with the same envelope shape as the happy path but with
    ``tiers=[]`` and every fold-rollup fail-closed (``allowed_count=0`` /
    ``all_allowed=False`` / ``any_allowed=False``) so a pricing-matrix
    column that lost the resolver never silently renders a bundle grant
    it can't verify. Caller-supplied tier / feature / runtime tokens
    echo into ``unknown_tiers`` / ``unknown_features`` /
    ``unknown_runtimes`` for debugging.
    """
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(tier_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "allowed_count": 0,
        "all_allowed": False,
        "any_allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_at_batch_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all-at-batch``.

    Batch what-if sibling of :func:`_has_all_at_body`: where the single-
    perspective ``/has-all-at`` folds ONE ``(perspective_tier, bundle)``
    pair, this fixes the bundle and sweeps across N perspective tiers,
    returning one row per tier with the aggregate mixed-axis fold boolean
    plus the surrounding tier envelope. Mixed-axis extension of
    :func:`_has_bundle_at_batch_body` (single-axis batch): where the
    ``/has-features-at-batch`` / ``/has-runtimes-at-batch`` variants
    answer "does each tier admit this single-axis bundle?", this one
    answers "does each tier admit the whole subscription state?" so a
    pricing-matrix column hydrates the mixed-axis grant off ONE URL
    instead of five ``_at-batch`` round-trips + a client-side AND-chain.

    Every axis is OPTIONAL -- a caller can supply any (or none) of the
    five axis kwargs; the fold answers off just those axes per row and
    every unsupplied axis is skipped (contributes ``True`` to each row's
    fold). The envelope always carries every axis' slot for byte-stable
    shape across every URL branch. No axes supplied collapses every
    row's ``has_all_at`` to ``False`` (matches :func:`has_all_at` /
    :func:`_has_all_at_body` empty-``False`` posture byte-for-byte).

    Grace-independent by construction: :func:`has_all_at_batch`
    delegates per-row to :func:`has_all_at`, which reads the static per-
    tier grant tables via the singular ``_at`` scalars -- so each row's
    ``has_all_at`` bit is IDENTICAL under grace vs enforce for the same
    ``(row.tier, bundle)`` pair, and diverges deliberately from the LIVE
    ``/has-all`` sibling (which grants every fully-known bundle in grace
    via the resolver's grace pass-through). Whole point of the ``_at``
    slot: ``/has-all-at-batch?tiers=oss,cloud_pro&features=fleet``
    returns the ``oss`` row's ``has_all_at=false`` even in grace
    (because OSS statically does not grant ``fleet``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subsets for parity with the LIVE ``/api/entitlement/has-all``
    envelope. Perspective-independent by design; the same bundle rollup
    is also echoed into each row via ``required_tier`` /
    ``required_tier_label`` / ``required_tier_rank`` so a per-row cell
    can render "cheapest tier that unlocks this bundle" alongside
    "granted at this row's tier" off one row bind.

    Per-row ``upgrade_required`` compares the bundle-level
    ``required_tier`` against each ROW's tier rank (not the live current
    rank), matching the sibling :func:`_has_bundle_at_batch_body`
    convention: a pricing-matrix row that binds this field reads "no
    upgrade needed at this tier" vs "upgrade needed beyond this tier".

    Runtime-alias canonicalisation is applied per-token upstream of the
    strict scalar (:func:`has_all_at_batch` inherits the strict-scalar
    posture from :func:`has_runtimes_at`), matching the sibling
    :func:`_has_bundle_at_batch_body` upstream-canonicalise pattern
    byte-for-byte (an alias-and-canonical pair dedups to ONE entry in
    ``runtimes`` before the scalar sees it).

    ``all_allowed`` folds row.allowed AND-wise (empty ``tiers`` ->
    False to inherit the fail-closed fold posture the singular
    :func:`has_all_at` uses on empty input). ``any_allowed`` folds
    OR-wise (empty ``tiers`` -> False). ``allowed_count`` is the sum
    of per-row boolean grants so a pricing-matrix header can render
    "3 of 5 tiers grant this bundle" off one field.

    An unknown token in the bundle (unknown feature id / unknown
    runtime id / non-int capacity) collapses the endpoint-level fold
    to ``False`` on EVERY row (matches the sibling
    :func:`_has_bundle_at_batch_body` and :func:`_has_all_at_body`
    posture: an ``unknown != []`` axis or a non-parseable capacity
    denies every row).

    Envelope shape (21 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet"],           # known ids only
          "runtimes":            ["claude_code"],     # canonicalised, known only
          "channels":            5 | null,            # parsed int or null
          "retention_days":      30 | null,
          "nodes":               2 | null,
          "unknown_features":    ["bogus"],           # tokens not in ALL_FEATURES
          "unknown_runtimes":    [],                  # tokens not in ALL_RUNTIMES
          "unknown_tiers":       ["bogus"],           # tier tokens dropped
          "supplied_axes":       ["features", "channels"],
          "supplied_count":      2,
          "tiers": [
            {
              "tier":                "cloud_pro",
              "tier_label":          "Pro",
              "tier_rank":           <int>,
              "has_all_at":          true,            # fold vs ROW's tier
              "allowed":             true,            # alias of has_all_at
              "required_tier":       "cloud_pro" | null,
              "required_tier_label": "Pro" | null,
              "required_tier_rank":  <int>,           # -1 when null
              "upgrade_required":    <bool>           # req_rank > row.tier_rank
            }, ...
          ],
          "allowed_count":       <int>,               # #rows with has_all_at=true
          "all_allowed":         <bool>,              # every row granted
          "any_allowed":         <bool>,              # at least one row granted
          "required_tier":       "cloud_pro" | null,  # bundle-level rollup
          "required_tier_label": "Pro" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,              # LIVE resolver grace bit
          "enforced":            <bool>
        }
    """
    from clawmetry import entitlements as _ent

    tier_tokens = _parse_csv_arg("tiers")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # An unknown token on ANY axis (or a non-int on a capacity axis)
    # collapses the endpoint-level fold to ``False`` on every row --
    # matches the sibling ``_has_all_at_body`` / ``_has_bundle_at_batch_body``
    # posture so a paywall matrix can't silently render a grant for a
    # bundle that already has a callsite typo in it.
    endpoint_denies_all = (
        (channels_present and not channels_ok)
        or (retention_present and not retention_ok)
        or (nodes_present and not nodes_ok)
        or (features_supplied and (unknown_features or not known_features))
        or (runtimes_supplied and (unknown_runtimes or not known_runtimes))
    )

    if endpoint_denies_all:
        batch = {"tiers": [], "unknown": []}
        # Still walk the tier tokens so ``unknown_tiers`` echoes the
        # bogus perspective ids caller-side even when the bundle already
        # denies every row -- keeps the envelope shape stable across
        # every input branch and matches the sibling
        # ``_has_bundle_at_batch_body`` upstream-canonicalise pattern.
        for tid_raw in tier_tokens:
            tid = (tid_raw or "").strip().lower()
            if not tid or tid not in _ent._TIER_ORDER:
                batch["unknown"].append(tid_raw)
                continue
            batch["tiers"].append(
                {
                    "tier": tid,
                    "tier_label": _ent.tier_label(tid),
                    "tier_rank": _ent._TIER_RANK.get(tid, -1),
                    "has_all_at": False,
                }
            )
    else:
        batch = _ent.has_all_at_batch(
            tier_tokens,
            features=known_features if features_supplied else None,
            runtimes=known_runtimes if runtimes_supplied else None,
            channels=channels_n if channels_present else None,
            retention_days=retention_n if retention_present else None,
            nodes=nodes_n if nodes_present else None,
        )

    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            tid = row.get("tier")
            row_allowed = bool(row.get("has_all_at", False))
        except AttributeError:
            continue
        row_rank = row.get("tier_rank", _ent.tier_rank(tid))
        upgrade_required = (
            bool(required) and row_rank >= 0 and req_rank > row_rank
        )
        tiers_out.append(
            {
                "tier": tid,
                "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                "tier_rank": row_rank,
                "has_all_at": row_allowed,
                "allowed": row_allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": upgrade_required,
            }
        )

    allowed_count = sum(1 for r in tiers_out if r["allowed"])
    all_allowed = bool(tiers_out) and all(r["allowed"] for r in tiers_out)
    any_allowed = any(r["allowed"] for r in tiers_out)

    return {
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "allowed_count": allowed_count,
        "all_allowed": all_allowed,
        "any_allowed": any_allowed,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_all_at_path_fallback(
    from_tier: str,
    to_tier: str,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-at-path``.

    Aggregate mixed-axis sibling of :func:`_has_bundle_at_path_fallback`
    (single-axis path) and path-shaped complement of
    :func:`_has_all_at_batch_fallback` (multi-perspective batch). On any
    resolver / helper blowup the endpoint still returns 200 with the
    same envelope shape as the happy path, but ``path=[]`` and every
    fold-rollup fail-closed (``allowed_count=0`` / ``all_allowed=False``
    / ``any_allowed=False``) so a pricing-page walkthrough that lost
    the resolver never silently renders a bundle grant it can't verify
    -- matches the sibling ``/has-features-at-path`` /
    ``/has-runtimes-at-path`` fallback's fail-closed posture byte-for-
    byte. ``from`` / ``to`` / caller-supplied token lists echo into the
    envelope + ``unknown_features`` / ``unknown_runtimes`` so a
    debugging tooltip still surfaces the caller-supplied set.
    ``direction`` collapses to ``"identity"`` when ``from == to``
    (matches the happy-path branch for that case) and ``"unknown"``
    otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "path": [],
        "path_length": 0,
        "allowed_count": 0,
        "all_allowed": False,
        "any_allowed": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_at_path_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all-at-path``.

    Aggregate mixed-axis path sibling of :func:`_has_bundle_at_path_body`
    (single-axis path) and path-shaped complement of
    :func:`_has_all_at_batch_body` (multi-perspective batch). Fixes ONE
    5-axis mixed bundle and sweeps across every rung between ``from=``
    and ``to=``, returning one row per rung with the aggregate
    ``has_all_at`` fold plus the surrounding path envelope.

    Envelope shape mirrors :func:`_has_bundle_at_path_body` for the
    walk-metadata keys (``from`` / ``from_label`` / ``from_rank`` /
    ``to`` / ``to_label`` / ``to_rank`` / ``direction`` / ``path``) so a
    client already binding the ``/has-features-at-path`` /
    ``/missing-features-at-path`` / ``/feature-catalog-path`` envelope
    can bind this one with the same shape reader. The mixed-axis bundle
    metadata (``features`` / ``runtimes`` / ``channels`` /
    ``retention_days`` / ``nodes`` / ``unknown_features`` /
    ``unknown_runtimes`` / ``supplied_axes`` / ``supplied_count``)
    matches :func:`_has_all_at_body` byte-for-byte so a caller already
    binding the singular ``/has-all-at`` envelope can bind this one
    with the same axis reader. The fold rollup (``allowed_count`` /
    ``all_allowed`` / ``any_allowed``) mirrors
    :func:`_has_bundle_at_path_body` extended over the aggregate mixed-
    axis fold, and the LIVE resolver envelope (``current_tier`` /
    ``current_tier_rank`` / ``grace`` / ``enforced``) matches the rest
    of the family.

    Per-rung row shape byte-equals the scalar
    :func:`clawmetry.entitlements.has_all_at_path` return:
    ``{tier, tier_label, tier_rank, has_all_at}``. A parity test pins
    per-rung ``has_all_at`` byte-equals
    ``/has-all-at?tier=<rung>&<same bundle>``'s ``has_all_at`` for the
    same (rung, bundle) pair -- so any future contract change on either
    side has to update both.

    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream of the strict scalar (matches the
    sibling ``/has-all-at`` / ``/has-all-at-batch`` upstream-
    canonicalise pattern). Alias-and-canonical pair dedups to ONE entry
    in ``runtimes`` and therefore ONE fold input on every rung.

    Endpoint-level fold semantics: an unknown feature or runtime token
    OR a non-int capacity value collapses the endpoint-level fold to
    ``False`` on EVERY rung (``unknown_features != []`` / non-int
    capacity -> every row's ``has_all_at`` reads ``False``) so a bundle
    typo fails-closed at the endpoint layer the same way it fails-
    closed on the singular ``/has-all-at`` endpoint. No axes supplied
    collapses every row to ``False`` (matches ``/has-all-at`` empty-
    ``False`` posture).

    ``allowed_count`` sums per-row grants across the walked path so a
    walkthrough header can render "granted at 2 of 4 rungs" off one
    field. ``all_allowed`` folds per-row ``has_all_at`` AND-wise (empty
    ``path`` -> ``False`` to inherit the fail-closed fold posture from
    the singular helper). ``any_allowed`` folds OR-wise (empty
    ``path`` -> ``False``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/has-all-at`` envelope's rollup
    contract) NOT the path endpoints -- the rollup answers "what's the
    cheapest tier that grants this whole bundle" independent of the
    walked window so a caller can pin the two-way comparison (path
    window vs cheapest-grant tier) off ONE round-trip.

    ``direction`` mirrors :func:`_has_bundle_at_path_body`'s values:
    ``upgrade`` | ``downgrade`` | ``lateral`` | ``identity`` |
    ``unknown``.

    Never 4xxs (missing / blank / unknown endpoints, or all-unknown /
    non-int bundle -> 200 with ``path=[]`` on the unknown-endpoint
    branch, or every rung's ``has_all_at=False`` on the unknown-token
    branch, matching the sibling ``/has-features-at-path`` posture).
    Never 5xxs: any helper blowup collapses to
    :func:`_has_all_at_path_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    from_tier = (raw_from or "").strip().lower()
    to_tier = (raw_to or "").strip().lower()

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Delegate the walk to the scalar. Pass CANONICAL known-only token
    # lists (upstream alias canonicalisation matches the sibling
    # ``/has-all-at``); the fold answers off those. The endpoint-level
    # collapse below handles typo / non-int input independent of the
    # scalar's own posture so a bundle typo fails-closed the same way
    # the singular endpoint fails-closed.
    path = _ent.has_all_at_path(
        from_tier,
        to_tier,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]

    if path is None:
        # Unknown endpoint(s) -- fall through to the empty-path envelope so
        # the client never 4xxs. ``direction`` reads ``"unknown"`` unless
        # the two endpoints happen to be equal string-wise, in which case
        # the scalar would have returned ``[]`` on the identity branch --
        # but here we're on the unknown branch, so keep ``"unknown"``.
        direction = "unknown"
        path_out: list = []
        from_label = None
        to_label = None
        from_rank = -1
        to_rank = -1
    else:
        # Endpoint-level typo collapse: an unknown token OR a non-int
        # capacity (i.e. supplied-and-not-ok) OR no-axes-supplied
        # collapses EVERY rung's ``has_all_at`` to ``False`` (matches
        # the singular ``/has-all-at`` empty-/typo-``False`` posture).
        endpoint_ok = (
            bool(supplied_axes)
            and not unknown_features
            and not unknown_runtimes
            and not (features_supplied and not known_features)
            and not (runtimes_supplied and not known_runtimes)
            and not (channels_present and not channels_ok)
            and not (retention_present and not retention_ok)
            and not (nodes_present and not nodes_ok)
        )
        path_out = []
        for row in path:
            try:
                tid = row.get("tier")
                row_allowed = bool(row.get("has_all_at", False))
            except AttributeError:
                continue
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                    "tier_rank": row.get("tier_rank", _ent.tier_rank(tid)),
                    "has_all_at": row_allowed and endpoint_ok,
                }
            )
        from_rank = _ent.tier_rank(from_tier)
        to_rank = _ent.tier_rank(to_tier)
        from_label = _ent.tier_label(from_tier)
        to_label = _ent.tier_label(to_tier)
        if from_tier == to_tier:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"

    allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
    all_allowed = bool(path_out) and all(
        r.get("has_all_at") for r in path_out
    )
    any_allowed = any(r.get("has_all_at") for r in path_out)

    # Required-tier rollup: fold through min_tier_for_all against the
    # KNOWN-only subset (matches ``/has-all-at`` byte-for-byte). If the
    # bundle is all-unknown / no-axes-supplied the rollup collapses to
    # None -- matches the singular endpoint.
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    return {
        "from": from_tier,
        "from_label": from_label,
        "from_rank": from_rank,
        "to": to_tier,
        "to_label": to_label,
        "to_rank": to_rank,
        "direction": direction,
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "path": path_out,
        "path_length": len(path_out),
        "allowed_count": allowed_count,
        "all_allowed": all_allowed,
        "any_allowed": any_allowed,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_all_at_path_batch_fallback(
    from_tier: str,
    to_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-at-path-batch``.

    Aggregate mixed-axis batch-path sibling of :func:`_has_all_at_path_fallback`
    (single-destination path). On any resolver / helper blowup the endpoint
    still returns 200 with the same envelope shape as the happy path but
    with ``tiers=[]`` and every fold-rollup fail-closed on the boolean-fold
    side so a pricing-comparison matrix that lost the resolver never
    silently renders a bundle grant it can't verify. Caller-supplied
    destination / feature / runtime tokens echo into ``unknown_tiers`` /
    ``unknown_features`` / ``unknown_runtimes`` for debugging.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(to_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_at_path_batch_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all-at-path-batch``.

    Aggregate mixed-axis batch-path sibling of :func:`_has_all_at_path_body`
    (single destination) and boolean-fold complement of
    :func:`_missing_all_at_path_batch_body` (row-detail path-batch). Fixes
    ONE 5-axis mixed bundle and sweeps across every rung between ``from=``
    and each of the N candidate destinations in ``to=`` in ONE round-trip,
    returning per-destination path lists of aggregate ``has_all_at`` fold
    rows.

    Envelope shape (byte-stable across every input branch)::

        {
          "from":               "<tier id>",
          "from_label":         "...",
          "from_rank":          <int>,
          "features":           [<known ids>],
          "runtimes":           [<known ids>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_features":   [...],
          "unknown_runtimes":   [...],
          "unknown_tiers":      [...],
          "supplied_axes":      [...],
          "supplied_count":     <int>,
          "tiers": [
            {
              "to":            "<id>",
              "to_label":      "...",
              "to_rank":       <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_all_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,
              "all_allowed":   <bool>,
              "any_allowed":   <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/has-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for the
    same triple -- pinned by the parity tests so the scalar and batch
    path what-if boolean-fold helpers cannot drift. Per-destination
    path lengths can legitimately differ (the rungs walked depend on
    the destination), matching :func:`_missing_bundle_at_path_batch_body`
    posture.

    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream of the strict scalar. Alias-and-
    canonical pair dedups to ONE entry in ``runtimes`` and therefore
    ONE fold input on every rung of every destination.

    Endpoint-level fold semantics: an unknown feature or runtime token
    OR a non-int capacity value collapses the endpoint-level fold to
    ``False`` on EVERY rung of EVERY destination (matches the singular
    ``/has-all-at-path`` typo-``False`` posture applied per destination).
    No axes supplied collapses every row to ``False`` (matches the
    ``/has-all-at`` empty-``False`` posture).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/has-all-at`` /
    ``/has-all-at-path`` envelopes' rollup contract), independent of
    any per-destination endpoint.

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/has-features-at-path-batch`` posture -- a pricing-
    comparison matrix binds ``tiers`` directly without a pre-
    validation round-trip). Never 5xxs: any helper blowup collapses
    to :func:`_has_all_at_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _parse_csv_arg("to")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    batch = _ent.has_all_at_path_batch(
        from_tier,
        to_tokens,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    # Endpoint-level typo collapse: an unknown token OR a non-int
    # capacity (i.e. supplied-and-not-ok) OR no-axes-supplied collapses
    # EVERY rung of EVERY destination's ``has_all_at`` to ``False``
    # (matches the singular ``/has-all-at-path`` empty-/typo-``False``
    # posture applied per destination).
    endpoint_ok = (
        bool(supplied_axes)
        and not unknown_features
        and not unknown_runtimes
        and not (features_supplied and not known_features)
        and not (runtimes_supplied and not known_runtimes)
        and not (channels_present and not channels_ok)
        and not (retention_present and not retention_ok)
        and not (nodes_present and not nodes_ok)
    )

    if batch is None:
        return {
            "from": from_tier,
            "from_label": None,
            "from_rank": -1,
            "features": known_features,
            "runtimes": known_runtimes,
            "channels": channels_n if channels_present and channels_ok else None,
            "retention_days": (
                retention_n if retention_present and retention_ok else None
            ),
            "nodes": nodes_n if nodes_present and nodes_ok else None,
            "unknown_features": unknown_features,
            "unknown_runtimes": unknown_runtimes,
            "unknown_tiers": list(to_tokens),
            "supplied_axes": supplied_axes,
            "supplied_count": len(supplied_axes),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        path_out: list[dict] = []
        for prow in path:
            try:
                tid = prow.get("tier")
                row_allowed = bool(prow.get("has_all_at", False))
            except AttributeError:
                continue
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": prow.get(
                        "tier_label", _ent.tier_label(tid)
                    ),
                    "tier_rank": prow.get(
                        "tier_rank", _ent.tier_rank(tid)
                    ),
                    "has_all_at": row_allowed and endpoint_ok,
                }
            )
        allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
        all_allowed = bool(path_out) and all(
            r.get("has_all_at") for r in path_out
        )
        any_allowed = any(r.get("has_all_at") for r in path_out)
        tiers_out.append(
            {
                "to": row.get("to"),
                "to_label": row.get("to_label"),
                "to_rank": row.get("to_rank", -1),
                "direction": row.get("direction"),
                "path": path_out,
                "path_length": len(path_out),
                "allowed_count": allowed_count,
                "all_allowed": all_allowed,
                "any_allowed": any_allowed,
            }
        )

    return {
        "from": from_tier,
        "from_label": _ent.tier_label(from_tier),
        "from_rank": _ent.tier_rank(from_tier),
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_all_at_path_batch_fallback(
    from_tier: str,
    to_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-at-path-batch``.

    Row-detail sibling of :func:`_has_all_at_path_batch_fallback` on the
    aggregate what-if batch-path seat. On any resolver / helper blowup
    the endpoint still returns 200 with the same envelope shape as the
    happy path but with ``tiers=[]`` and every fold-rollup fail-open on
    the row-detail side (``denied_count=0`` / ``all_denied=False`` /
    ``any_denied=False`` when materialised per destination) so a
    pricing-comparison matrix that lost the resolver never silently
    renders a bundle denial it can't justify. Mirrors
    :func:`_has_all_at_path_batch_fallback` byte-for-byte on the axis-
    echo slots so a UI wiring both boolean-fold and row-detail matrices
    off the same body-builder gets byte-stable envelopes across every
    input branch on both endpoints.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(to_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_at_path_batch_body() -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-all-at-path-batch``.

    Aggregate mixed-axis batch-path sibling of
    :func:`_missing_all_at_path_body` (single destination) and row-detail
    complement of :func:`_has_all_at_path_batch_body` (paired boolean-
    fold batch-path). Fixes ONE 5-axis mixed bundle and sweeps across
    every rung between ``from=`` and each of the N candidate destinations
    in ``to=`` in ONE round-trip, returning per-destination path lists of
    aggregate ``missing`` row-detail rows.

    Envelope shape (byte-stable across every input branch)::

        {
          "from":               "<tier id>",
          "from_label":         "...",
          "from_rank":          <int>,
          "features":           [<known ids>],
          "runtimes":           [<known ids>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_features":   [...],
          "unknown_runtimes":   [...],
          "unknown_tiers":      [...],
          "supplied_axes":      [...],
          "supplied_count":     <int>,
          "tiers": [
            {
              "to":           "<id>",
              "to_label":     "...",
              "to_rank":      <int>,
              "direction":    "upgrade" | "downgrade" | "lateral" | "identity",
              "path":         [<missing_all_at_path row>, ...],
              "path_length":  <int>,
              "denied_count": <int>,
              "all_denied":   <bool>,
              "any_denied":   <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/missing-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for
    the same triple -- pinned by the parity tests. Per-destination path
    lengths can legitimately differ, matching
    ``/missing-features-at-path-batch`` /
    ``/missing-runtimes-at-path-batch`` posture.

    Runtime-alias canonicalisation is applied per-token upstream of the
    strict scalar. Endpoint-level typo posture: unknown feature / runtime
    tokens are SURFACED inside each rung's per-axis
    ``missing["features"]`` / ``missing["runtimes"]`` list AND echoed in
    ``unknown_features`` / ``unknown_runtimes`` for a diagnostics tooltip
    (matches :func:`_missing_all_at_path_body` per destination). A
    supplied-but-unparseable capacity axis surfaces the raw string in
    that rung's per-axis capacity slot on every rung of every
    destination.

    Per-destination ``denied_count`` sums the count of rungs that carry
    ANY per-axis denial across that destination's path; ``all_denied``
    folds AND-wise (empty path -> ``False``); ``any_denied`` folds OR-
    wise (empty path -> ``False``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/missing-all-at-path`` envelope's
    rollup contract), independent of any per-destination endpoint.

    Never 4xxs (missing / blank / unknown ``from``, or empty / all-
    unknown destination CSV -> 200 with ``tiers=[]``, matching the
    sibling ``/missing-features-at-path-batch`` posture). Never 5xxs:
    any helper blowup collapses to
    :func:`_missing_all_at_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_from = request.args.get("from")
    from_tier = (raw_from or "").strip().lower()
    to_tokens = _parse_csv_arg("to")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    batch = _ent.missing_all_at_path_batch(
        from_tier,
        to_tokens,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    if batch is None:
        return {
            "from": from_tier,
            "from_label": None,
            "from_rank": -1,
            "features": known_features,
            "runtimes": known_runtimes,
            "channels": channels_n if channels_present and channels_ok else None,
            "retention_days": (
                retention_n if retention_present and retention_ok else None
            ),
            "nodes": nodes_n if nodes_present and nodes_ok else None,
            "unknown_features": unknown_features,
            "unknown_runtimes": unknown_runtimes,
            "unknown_tiers": list(to_tokens),
            "supplied_axes": supplied_axes,
            "supplied_count": len(supplied_axes),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    def _row_any_denied(row) -> bool:
        m = row.get("missing") or {}
        for k, v in m.items():
            if isinstance(v, list):
                if v:
                    return True
            elif v is not None:
                return True
        return False

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        path_out: list[dict] = []
        for prow in path:
            try:
                tid = prow.get("tier")
                base_missing = prow.get("missing") or {}
            except AttributeError:
                continue
            feat_missing: list = list(base_missing.get("features") or [])
            for token in unknown_features:
                if token not in feat_missing:
                    feat_missing.append(token)
            rt_missing: list = list(base_missing.get("runtimes") or [])
            for token in unknown_runtimes:
                if token not in rt_missing:
                    rt_missing.append(token)
            if channels_present and not channels_ok:
                channels_slot = channels_raw
            else:
                channels_slot = base_missing.get("channels")
            if retention_present and not retention_ok:
                retention_slot = retention_raw
            else:
                retention_slot = base_missing.get("retention_days")
            if nodes_present and not nodes_ok:
                nodes_slot = nodes_raw
            else:
                nodes_slot = base_missing.get("nodes")
            missing_dict = {
                "features": feat_missing,
                "runtimes": rt_missing,
                "channels": channels_slot,
                "retention_days": retention_slot,
                "nodes": nodes_slot,
            }
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": prow.get(
                        "tier_label", _ent.tier_label(tid)
                    ),
                    "tier_rank": prow.get(
                        "tier_rank", _ent.tier_rank(tid)
                    ),
                    "missing": missing_dict,
                }
            )
        denied_count = sum(1 for r in path_out if _row_any_denied(r))
        all_denied = bool(path_out) and all(
            _row_any_denied(r) for r in path_out
        )
        any_denied = any(_row_any_denied(r) for r in path_out)
        tiers_out.append(
            {
                "to": row.get("to"),
                "to_label": row.get("to_label"),
                "to_rank": row.get("to_rank", -1),
                "direction": row.get("direction"),
                "path": path_out,
                "path_length": len(path_out),
                "denied_count": denied_count,
                "all_denied": all_denied,
                "any_denied": any_denied,
            }
        )

    return {
        "from": from_tier,
        "from_label": _ent.tier_label(from_tier),
        "from_rank": _ent.tier_rank(from_tier),
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _has_all_from_path_batch_fallback(
    to_tier: str,
    from_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-from-path-batch``.

    Mirror-direction source-batch sibling of
    :func:`_has_all_at_path_batch_fallback` (destination-side batch). On
    any resolver / helper blowup the endpoint still returns 200 with the
    same envelope shape as the happy path but with ``tiers=[]`` and
    every fold-rollup fail-closed on the boolean-fold side so a source-
    side pricing-comparison matrix that lost the resolver never silently
    renders a bundle grant it can't verify. Caller-supplied source /
    feature / runtime tokens echo into ``unknown_tiers`` /
    ``unknown_features`` / ``unknown_runtimes`` for debugging.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(from_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_from_path_batch_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/has-all-from-path-batch``.

    Mirror-direction source-batch sibling of
    :func:`_has_all_at_path_batch_body` (destination-side batch) and
    boolean-fold complement of :func:`_missing_all_from_path_batch_body`
    (source-batch row-detail). Fixes ONE 5-axis mixed bundle and sweeps
    across every rung between each of the N candidate sources in
    ``from=`` and the shared destination in ``to=`` in ONE round-trip,
    returning per-source path lists of aggregate ``has_all_at`` fold
    rows.

    Envelope shape (byte-stable across every input branch)::

        {
          "to":                 "<tier id>",
          "to_label":           "...",
          "to_rank":            <int>,
          "features":           [<known ids>],
          "runtimes":           [<known ids>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_features":   [...],
          "unknown_runtimes":   [...],
          "unknown_tiers":      [...],
          "supplied_axes":      [...],
          "supplied_count":     <int>,
          "tiers": [
            {
              "from":          "<id>",
              "from_label":    "...",
              "from_rank":     <int>,
              "direction":     "upgrade" | "downgrade" | "lateral" | "identity",
              "path":          [<has_all_at_path row>, ...],
              "path_length":   <int>,
              "allowed_count": <int>,
              "all_allowed":   <bool>,
              "any_allowed":   <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/has-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for the
    same triple -- pinned by the parity tests so the scalar and source-
    batch path what-if boolean-fold helpers cannot drift. Per-source
    path lengths can legitimately differ (the rungs walked depend on
    the source), matching :func:`_has_bundle_from_path_batch_body` /
    :func:`_has_all_at_path_batch_body` posture.

    Runtime-alias canonicalisation (``claude-code`` -> ``claude_code``)
    is applied per-token upstream of the strict scalar. Alias-and-
    canonical pair dedups to ONE entry in ``runtimes`` and therefore
    ONE fold input on every rung of every source.

    Endpoint-level fold semantics: an unknown feature or runtime token
    OR a non-int capacity value collapses the endpoint-level fold to
    ``False`` on EVERY rung of EVERY source (matches the singular
    ``/has-all-at-path`` typo-``False`` posture applied per source).
    No axes supplied collapses every row to ``False`` (matches the
    ``/has-all-at`` empty-``False`` posture).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/has-all-at`` /
    ``/has-all-at-path`` envelopes' rollup contract), independent of
    any per-source endpoint.

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/has-features-from-path-batch`` /
    ``/has-all-at-path-batch`` posture -- a source-side comparison
    matrix binds ``tiers`` directly without a pre-validation round-
    trip). Never 5xxs: any helper blowup collapses to
    :func:`_has_all_from_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_to = request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    from_tokens = _parse_csv_arg("from")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    batch = _ent.has_all_from_path_batch(
        from_tokens,
        to_tier,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    # Endpoint-level typo collapse: an unknown token OR a non-int
    # capacity (i.e. supplied-and-not-ok) OR no-axes-supplied collapses
    # EVERY rung of EVERY source's ``has_all_at`` to ``False`` (matches
    # the singular ``/has-all-at-path`` empty-/typo-``False`` posture
    # applied per source).
    endpoint_ok = (
        bool(supplied_axes)
        and not unknown_features
        and not unknown_runtimes
        and not (features_supplied and not known_features)
        and not (runtimes_supplied and not known_runtimes)
        and not (channels_present and not channels_ok)
        and not (retention_present and not retention_ok)
        and not (nodes_present and not nodes_ok)
    )

    if batch is None:
        return {
            "to": to_tier,
            "to_label": None,
            "to_rank": -1,
            "features": known_features,
            "runtimes": known_runtimes,
            "channels": channels_n if channels_present and channels_ok else None,
            "retention_days": (
                retention_n if retention_present and retention_ok else None
            ),
            "nodes": nodes_n if nodes_present and nodes_ok else None,
            "unknown_features": unknown_features,
            "unknown_runtimes": unknown_runtimes,
            "unknown_tiers": list(from_tokens),
            "supplied_axes": supplied_axes,
            "supplied_count": len(supplied_axes),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        path_out: list[dict] = []
        for prow in path:
            try:
                tid = prow.get("tier")
                row_allowed = bool(prow.get("has_all_at", False))
            except AttributeError:
                continue
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": prow.get(
                        "tier_label", _ent.tier_label(tid)
                    ),
                    "tier_rank": prow.get(
                        "tier_rank", _ent.tier_rank(tid)
                    ),
                    "has_all_at": row_allowed and endpoint_ok,
                }
            )
        allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
        all_allowed = bool(path_out) and all(
            r.get("has_all_at") for r in path_out
        )
        any_allowed = any(r.get("has_all_at") for r in path_out)
        tiers_out.append(
            {
                "from": row.get("from"),
                "from_label": row.get("from_label"),
                "from_rank": row.get("from_rank", -1),
                "direction": row.get("direction"),
                "path": path_out,
                "path_length": len(path_out),
                "allowed_count": allowed_count,
                "all_allowed": all_allowed,
                "any_allowed": any_allowed,
            }
        )

    return {
        "to": to_tier,
        "to_label": _ent.tier_label(to_tier),
        "to_rank": _ent.tier_rank(to_tier),
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_all_from_path_batch_fallback(
    to_tier: str,
    from_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-from-path-batch``.

    Row-detail sibling of :func:`_has_all_from_path_batch_fallback` on
    the aggregate what-if source-batch path seat. On any resolver /
    helper blowup the endpoint still returns 200 with the same envelope
    shape as the happy path but with ``tiers=[]`` and every fold-rollup
    fail-open on the row-detail side (``denied_count=0`` /
    ``all_denied=False`` / ``any_denied=False`` when materialised per
    source) so a source-side pricing-comparison matrix that lost the
    resolver never silently renders a bundle denial it can't justify.
    Mirrors :func:`_has_all_from_path_batch_fallback` byte-for-byte on
    the axis-echo slots so a UI wiring both boolean-fold and row-detail
    matrices off the same body-builder gets byte-stable envelopes across
    every input branch on both endpoints.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(from_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_from_path_batch_body() -> dict:
    """Happy-path body builder for
    ``/api/entitlement/missing-all-from-path-batch``.

    Mirror-direction source-batch sibling of
    :func:`_missing_all_at_path_batch_body` (destination-side batch) and
    row-detail complement of :func:`_has_all_from_path_batch_body`
    (paired source-batch boolean-fold). Fixes ONE 5-axis mixed bundle
    and sweeps across every rung between each of the N candidate sources
    in ``from=`` and the shared destination in ``to=`` in ONE round-
    trip, returning per-source path lists of aggregate ``missing`` row-
    detail rows.

    Envelope shape (byte-stable across every input branch)::

        {
          "to":                 "<tier id>",
          "to_label":           "...",
          "to_rank":            <int>,
          "features":           [<known ids>],
          "runtimes":           [<known ids>],
          "channels":           <int|null>,
          "retention_days":     <int|null>,
          "nodes":              <int|null>,
          "unknown_features":   [...],
          "unknown_runtimes":   [...],
          "unknown_tiers":      [...],
          "supplied_axes":      [...],
          "supplied_count":     <int>,
          "tiers": [
            {
              "from":         "<id>",
              "from_label":   "...",
              "from_rank":    <int>,
              "direction":    "upgrade" | "downgrade" | "lateral" | "identity",
              "path":         [<missing_all_at_path row>, ...],
              "path_length":  <int>,
              "denied_count": <int>,
              "all_denied":   <bool>,
              "any_denied":   <bool>,
            },
            ...
          ],
          "required_tier":       "<id>" | null,
          "required_tier_label": "<label>" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,
          "enforced":            <bool>,
        }

    Each ``tiers[].path`` row is byte-identical to a row from
    ``/missing-all-at-path?from=<from>&to=<to>&<bundle>``'s ``.path`` for
    the same triple -- pinned by the parity tests. Per-source path
    lengths can legitimately differ, matching
    ``/missing-features-from-path-batch`` /
    ``/missing-runtimes-from-path-batch`` /
    ``/missing-all-at-path-batch`` posture.

    Runtime-alias canonicalisation is applied per-token upstream of the
    strict scalar. Endpoint-level typo posture: unknown feature /
    runtime tokens are SURFACED inside each rung's per-axis
    ``missing["features"]`` / ``missing["runtimes"]`` list AND echoed in
    ``unknown_features`` / ``unknown_runtimes`` for a diagnostics
    tooltip (matches :func:`_missing_all_at_path_batch_body` per source).
    A supplied-but-unparseable capacity axis surfaces the raw string in
    that rung's per-axis capacity slot on every rung of every source.

    Per-source ``denied_count`` sums the count of rungs that carry ANY
    per-axis denial across that source's path; ``all_denied`` folds
    AND-wise (empty path -> ``False``); ``any_denied`` folds OR-wise
    (empty path -> ``False``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subset (matches the singular ``/missing-all-at-path`` envelope's
    rollup contract), independent of any per-source endpoint.

    Never 4xxs (missing / blank / unknown ``to``, or empty / all-
    unknown source CSV -> 200 with ``tiers=[]``, matching the sibling
    ``/missing-features-from-path-batch`` posture). Never 5xxs: any
    helper blowup collapses to
    :func:`_missing_all_from_path_batch_fallback`.
    """
    from clawmetry import entitlements as _ent

    raw_to = request.args.get("to")
    to_tier = (raw_to or "").strip().lower()
    from_tokens = _parse_csv_arg("from")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    batch = _ent.missing_all_from_path_batch(
        from_tokens,
        to_tier,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    if batch is None:
        return {
            "to": to_tier,
            "to_label": None,
            "to_rank": -1,
            "features": known_features,
            "runtimes": known_runtimes,
            "channels": channels_n if channels_present and channels_ok else None,
            "retention_days": (
                retention_n if retention_present and retention_ok else None
            ),
            "nodes": nodes_n if nodes_present and nodes_ok else None,
            "unknown_features": unknown_features,
            "unknown_runtimes": unknown_runtimes,
            "unknown_tiers": list(from_tokens),
            "supplied_axes": supplied_axes,
            "supplied_count": len(supplied_axes),
            "tiers": [],
            "required_tier": required,
            "required_tier_label": required_label,
            "required_tier_rank": req_rank,
            "current_tier": env["current_tier"],
            "current_tier_rank": env["current_tier_rank"],
            "grace": env["grace"],
            "enforced": env["enforced"],
        }

    def _row_any_denied(row) -> bool:
        m = row.get("missing") or {}
        for k, v in m.items():
            if isinstance(v, list):
                if v:
                    return True
            elif v is not None:
                return True
        return False

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            path = list(row.get("path", []) or [])
        except AttributeError:
            continue
        path_out: list[dict] = []
        for prow in path:
            try:
                tid = prow.get("tier")
                base_missing = prow.get("missing") or {}
            except AttributeError:
                continue
            feat_missing: list = list(base_missing.get("features") or [])
            for token in unknown_features:
                if token not in feat_missing:
                    feat_missing.append(token)
            rt_missing: list = list(base_missing.get("runtimes") or [])
            for token in unknown_runtimes:
                if token not in rt_missing:
                    rt_missing.append(token)
            if channels_present and not channels_ok:
                channels_slot = channels_raw
            else:
                channels_slot = base_missing.get("channels")
            if retention_present and not retention_ok:
                retention_slot = retention_raw
            else:
                retention_slot = base_missing.get("retention_days")
            if nodes_present and not nodes_ok:
                nodes_slot = nodes_raw
            else:
                nodes_slot = base_missing.get("nodes")
            missing_dict = {
                "features": feat_missing,
                "runtimes": rt_missing,
                "channels": channels_slot,
                "retention_days": retention_slot,
                "nodes": nodes_slot,
            }
            path_out.append(
                {
                    "tier": tid,
                    "tier_label": prow.get(
                        "tier_label", _ent.tier_label(tid)
                    ),
                    "tier_rank": prow.get(
                        "tier_rank", _ent.tier_rank(tid)
                    ),
                    "missing": missing_dict,
                }
            )
        denied_count = sum(1 for r in path_out if _row_any_denied(r))
        all_denied = bool(path_out) and all(
            _row_any_denied(r) for r in path_out
        )
        any_denied = any(_row_any_denied(r) for r in path_out)
        tiers_out.append(
            {
                "from": row.get("from"),
                "from_label": row.get("from_label"),
                "from_rank": row.get("from_rank", -1),
                "direction": row.get("direction"),
                "path": path_out,
                "path_length": len(path_out),
                "denied_count": denied_count,
                "all_denied": all_denied,
                "any_denied": any_denied,
            }
        )

    return {
        "to": to_tier,
        "to_label": _ent.tier_label(to_tier),
        "to_rank": _ent.tier_rank(to_tier),
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_all_at_batch_fallback(
    tier_tokens: list,
    feature_tokens: list,
    runtime_tokens: list,
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-at-batch``.

    Row-detail sibling of :func:`_has_all_at_batch_fallback` on the
    aggregate what-if seat. On any resolver / helper blowup the endpoint
    still returns 200 with the same envelope shape as the happy path but
    with ``tiers=[]`` and every fold-rollup fail-open on the row-detail
    side (``denied_count=0`` / ``all_denied=False`` / ``any_denied=False``)
    so a pricing-matrix column that lost the resolver never silently
    renders a bundle denial it can't justify. Caller-supplied tier /
    feature / runtime tokens echo into ``unknown_tiers`` /
    ``unknown_features`` / ``unknown_runtimes`` for debugging. Mirrors
    :func:`_has_all_at_batch_fallback` byte-for-byte on the axis-echo
    slots (features / runtimes / channels / retention_days / nodes /
    unknown_features / unknown_runtimes / unknown_tiers / supplied_axes /
    supplied_count / required_tier / required_tier_label /
    required_tier_rank / current_tier / current_tier_rank / grace /
    enforced) so a UI wiring both boolean-fold and row-detail matrices
    off the same body-builder gets byte-stable envelopes across every
    input branch on both endpoints. The only per-envelope divergence is
    the aggregation fold slot -- boolean-fold: allowed_count /
    all_allowed / any_allowed; row-detail: denied_count / all_denied /
    any_denied.
    """
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": list(feature_tokens),
        "unknown_runtimes": list(runtime_tokens),
        "unknown_tiers": list(tier_tokens),
        "supplied_axes": [],
        "supplied_count": 0,
        "tiers": [],
        "denied_count": 0,
        "all_denied": False,
        "any_denied": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_at_batch_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-all-at-batch``.

    Batch what-if row-detail complement of :func:`_has_all_at_batch_body`:
    where the paired boolean-fold sibling collapses each
    ``(perspective_tier, bundle)`` pair to a single ``has_all_at`` bool,
    this returns WHAT is missing on each supplied axis of the same 5-axis
    bundle for the same N perspectives so a paywall diagnostics matrix
    ("out of {fleet, sso, claude_code, 100 channels, 90d retention, 100
    nodes}, which axes are still blocked at OSS vs Cloud Starter vs
    Cloud Pro vs Enterprise?") hydrates the per-axis denial column off
    ONE URL instead of five ``_at-batch`` row-detail round-trips + a
    client-side per-axis stitch.

    Mixed-axis extension of :func:`_missing_bundle_at_batch_body` (single-
    axis batch row-detail): where the ``/missing-features-at-batch`` /
    ``/missing-runtimes-at-batch`` variants answer "which items of this
    single-axis bundle are denied at each tier?", this one answers
    "which axes of the whole subscription state are denied at each
    tier?" so a paywall walkthrough hydrates the mixed-axis per-axis
    denial column off ONE URL.

    Every axis is OPTIONAL -- a caller can supply any (or none) of the
    five axis kwargs; the row-detail answers off just those axes per row
    and every unsupplied axis is skipped (``missing.features`` /
    ``missing.runtimes`` -> ``[]`` on that row; capacity axis -> ``null``).
    The envelope always carries every axis' slot for byte-stable shape
    across every URL branch.

    Grace-independent by construction: :func:`missing_all_at_batch`
    delegates per-row to :func:`missing_all_at`, which reads the static
    per-tier grant tables via the singular ``_at`` scalars -- so each
    row's ``missing`` dict is IDENTICAL under grace vs enforce for the
    same ``(row.tier, bundle)`` pair, and diverges deliberately from the
    LIVE ``/missing-all`` sibling (which reports every axis empty for
    a fully-known bundle in grace via the resolver's grace pass-through).
    Whole point of the ``_at`` slot:
    ``/missing-all-at-batch?tiers=oss,cloud_pro&features=fleet``
    returns the ``oss`` row's ``missing.features=["fleet"]`` even in
    grace (because OSS statically does not grant ``fleet``).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-
    only subsets for parity with the LIVE ``/api/entitlement/missing-all``
    envelope. Perspective-independent by design; the same bundle rollup
    is also echoed into each row via ``required_tier`` /
    ``required_tier_label`` / ``required_tier_rank`` so a per-row cell
    can render "cheapest tier that unlocks this bundle" alongside the
    per-axis denial detail off one row bind.

    Per-row ``upgrade_required`` compares the bundle-level
    ``required_tier`` against each ROW's tier rank (not the live current
    rank), matching the sibling :func:`_missing_bundle_at_batch_body` /
    :func:`_has_all_at_batch_body` convention: a pricing-matrix row
    reads "no upgrade needed at this tier" vs "upgrade needed beyond
    this tier".

    Per-row ``missing_count`` folds axis-wise: a per-axis list
    contributes its ``len(...)``; each capacity axis contributes ``1``
    when denied (non-``None`` on the row's ``missing`` slot). Same
    semantic as :func:`missing_features_at_batch` /
    :func:`missing_runtimes_at_batch` extended over five axes.

    Per-row ``any_missing`` folds ``bool(any per-axis denial on the
    row) or bool(endpoint-level unknown_features or unknown_runtimes)``
    -- matches the sibling :func:`_missing_bundle_at_batch_body`
    posture byte-for-byte (an unknown token in the bundle is surfaced
    per-row as "yes, something's missing" even though the singular
    ``_at`` scalars fail-open on unknowns per-axis; the pricing tooltip
    reads the unknown list separately).

    Runtime-alias canonicalisation is applied per-token upstream of the
    strict scalar (:func:`missing_all_at_batch` inherits the strict-
    scalar posture from :func:`missing_runtimes_at`), matching the
    sibling :func:`_missing_bundle_at_batch_body` and
    :func:`_has_all_at_batch_body` upstream-canonicalise pattern byte-
    for-byte (an alias-and-canonical pair dedups to ONE entry in
    ``runtimes`` before the scalar sees it).

    ``denied_count`` counts per-row ``any_missing`` truthy (empty
    ``tiers`` -> 0). ``all_denied`` is truthy iff ``tiers`` is non-
    empty AND every row's ``any_missing`` is truthy (empty ``tiers``
    -> False so the fail-open / grace path can't silently render "every
    tier denies this bundle"). ``any_denied`` is truthy iff any row's
    ``any_missing`` is truthy (empty ``tiers`` -> False).

    Envelope shape (21 keys, byte-stable across every input branch)::

        {
          "features":            ["fleet"],           # known ids only
          "runtimes":            ["claude_code"],     # canonicalised, known only
          "channels":            5 | null,            # parsed int or null
          "retention_days":      30 | null,
          "nodes":               2 | null,
          "unknown_features":    ["bogus"],           # tokens not in ALL_FEATURES
          "unknown_runtimes":    [],                  # tokens not in ALL_RUNTIMES
          "unknown_tiers":       ["bogus"],           # tier tokens dropped
          "supplied_axes":       ["features", "channels"],
          "supplied_count":      2,
          "tiers": [
            {
              "tier":                "cloud_pro",
              "tier_label":          "Pro",
              "tier_rank":           <int>,
              "missing": {
                  "features":       [<subset denied at row.tier>],
                  "runtimes":       [<subset denied at row.tier>],
                  "channels":       <supplied int if denied at row.tier, else null>,
                  "retention_days": <supplied int if denied at row.tier, else null>,
                  "nodes":          <supplied int if denied at row.tier, else null>,
              },
              "missing_count":       <int>,          # sum of denied axes on row
              "any_missing":         <bool>,         # row-denial OR endpoint-unknown
              "required_tier":       "cloud_pro" | null,
              "required_tier_label": "Pro" | null,
              "required_tier_rank":  <int>,          # -1 when null
              "upgrade_required":    <bool>          # req_rank > row.tier_rank
            }, ...
          ],
          "denied_count":        <int>,               # #rows with any_missing=true
          "all_denied":          <bool>,              # every row has any denial
          "any_denied":          <bool>,              # at least one row has any denial
          "required_tier":       "cloud_pro" | null,  # bundle-level rollup
          "required_tier_label": "Pro" | null,
          "required_tier_rank":  <int>,
          "current_tier":        "<live tier id>",
          "current_tier_rank":   <int>,
          "grace":               <bool>,              # LIVE resolver grace bit
          "enforced":            <bool>
        }
    """
    from clawmetry import entitlements as _ent

    tier_tokens = _parse_csv_arg("tiers")

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        _channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        _retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        _nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Only the known subset reaches the strict scalar -- unknown feature /
    # runtime tokens are surfaced separately via ``unknown_features`` /
    # ``unknown_runtimes`` and folded into per-row ``any_missing`` at
    # emit time. Non-int capacity axes are dropped from the scalar
    # (matches :func:`missing_all_at` non-int-``None`` swallow posture);
    # the paired ``/has-all-at-batch`` collapses every row's fold to
    # ``False`` on the same input via the boolean scalar's strict typo
    # posture -- callers wanting the strict typo-``False`` posture read
    # the paired boolean fold.
    batch = _ent.missing_all_at_batch(
        tier_tokens,
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    required_label = _ent.tier_label(required) if required else None
    req_rank = _ent.tier_rank(required) if required else -1

    unknown_any = bool(unknown_features) or bool(unknown_runtimes)

    tiers_out: list[dict] = []
    for row in batch.get("tiers", []) or []:
        try:
            tid = row.get("tier")
            row_missing = row.get("missing") or {}
        except AttributeError:
            continue
        if not isinstance(row_missing, dict):
            row_missing = {}
        missing_features_row = list(row_missing.get("features") or [])
        missing_runtimes_row = list(row_missing.get("runtimes") or [])
        missing_channels_row = row_missing.get("channels")
        missing_retention_row = row_missing.get("retention_days")
        missing_nodes_row = row_missing.get("nodes")
        row_rank = row.get("tier_rank", _ent.tier_rank(tid))
        upgrade_required = (
            bool(required) and row_rank >= 0 and req_rank > row_rank
        )
        row_missing_count = (
            len(missing_features_row)
            + len(missing_runtimes_row)
            + (1 if missing_channels_row is not None else 0)
            + (1 if missing_retention_row is not None else 0)
            + (1 if missing_nodes_row is not None else 0)
        )
        row_any_missing = bool(row_missing_count) or unknown_any
        tiers_out.append(
            {
                "tier": tid,
                "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                "tier_rank": row_rank,
                "missing": {
                    "features": missing_features_row,
                    "runtimes": missing_runtimes_row,
                    "channels": missing_channels_row,
                    "retention_days": missing_retention_row,
                    "nodes": missing_nodes_row,
                },
                "missing_count": row_missing_count,
                "any_missing": row_any_missing,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": upgrade_required,
            }
        )

    denied_count = sum(1 for r in tiers_out if r["any_missing"])
    all_denied = bool(tiers_out) and all(r["any_missing"] for r in tiers_out)
    any_denied = any(r["any_missing"] for r in tiers_out)

    return {
        "features": known_features,
        "runtimes": known_runtimes,
        "channels": channels_n if channels_present and channels_ok else None,
        "retention_days": (
            retention_n if retention_present and retention_ok else None
        ),
        "nodes": nodes_n if nodes_present and nodes_ok else None,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "unknown_tiers": list(batch.get("unknown", []) or []),
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "tiers": tiers_out,
        "denied_count": denied_count,
        "all_denied": all_denied,
        "any_denied": any_denied,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": env["current_tier_rank"],
        "grace": env["grace"],
        "enforced": env["enforced"],
    }

def _missing_all_fallback() -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all``.

    Row-detail sibling of :func:`_has_all_fallback`. On a resolver blowup the
    endpoint still returns 200 with the same envelope shape as the happy
    path, but every per-axis missing slot is empty (``[]`` / ``None``) and
    the ``any_missing`` / ``upgrade_required`` rollups are ``False`` so a
    paywall tile that lost the resolver doesn't render a denial banner it
    can no longer justify. Matches ``_has_all_fallback`` on every shared
    slot (envelope key set is a strict superset -- extra keys are the
    per-axis missing counters).
    """
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_features": [],
        "unknown_runtimes": [],
        "supplied_axes": [],
        "supplied_count": 0,
        "missing_count": 0,
        "any_missing": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
        "upgrade_required": False,
    }

def _missing_all_body() -> dict:
    """Happy-path body builder for ``/api/entitlement/missing-all``.

    Row-detail complement of :func:`_has_all_body`: same per-axis
    normalisation, same runtime-alias canonicalisation, same
    known/unknown split -- but instead of folding the answer to ONE
    boolean ``has_all``, this returns the exact per-axis denial detail
    a paywall diagnostics tile needs to render "you're missing X, Y --
    upgrade to unlock" off ONE URL.

    Delegates the per-axis fold to :func:`clawmetry.entitlements.missing_all`
    against the CANONICALISED known-only subsets so envelope-vs-scalar
    parity holds byte-exact (matches ``_has_all_body`` posture). Unknown
    tokens are ECHOED inside the per-axis missing list (canonicalised to
    ``.strip().lower()`` for features; runtime-alias resolved for
    runtimes) so a caller sees the full denial roster in one place;
    ``unknown_features`` / ``unknown_runtimes`` still split them out for
    a tooltip that wants to distinguish "denied by tier" from "not a real
    id". Supplied-but-unparseable capacity axis surfaces the raw string
    in that axis' slot (matches the singular ``missing_features`` scalar's
    typo-catches-at-callsite posture on the grant axes).

    ``required_tier`` folds through
    :func:`clawmetry.entitlements.min_tier_for_all` against the KNOWN-only
    subsets for parity with ``/api/entitlement/has-all`` and
    ``/api/entitlement/required-tier``.
    """
    from clawmetry import entitlements as _ent

    features_raw = request.args.get("features")
    runtimes_raw = request.args.get("runtimes")

    known_features: list[str] = []
    unknown_features: list[str] = []
    features_supplied = features_raw is not None
    if features_supplied:
        for fid in _parse_csv_arg("features"):
            if fid in _ent.ALL_FEATURES:
                if fid not in known_features:
                    known_features.append(fid)
            elif fid not in unknown_features:
                unknown_features.append(fid)

    known_runtimes: list[str] = []
    unknown_runtimes: list[str] = []
    runtimes_supplied = runtimes_raw is not None
    if runtimes_supplied:
        for rid_raw in _parse_csv_arg("runtimes"):
            rid = _ent.canonical_runtime(rid_raw) or rid_raw
            if rid in _ent.ALL_RUNTIMES:
                if rid not in known_runtimes:
                    known_runtimes.append(rid)
            elif rid_raw not in unknown_runtimes:
                unknown_runtimes.append(rid_raw)

    (
        channels_present,
        channels_ok,
        channels_n,
        channels_raw,
    ) = _parse_capacity_arg("channels")
    (
        retention_present,
        retention_ok,
        retention_n,
        retention_raw,
    ) = _parse_capacity_arg("retention_days")
    (
        nodes_present,
        nodes_ok,
        nodes_n,
        nodes_raw,
    ) = _parse_capacity_arg("nodes")

    supplied_axes: list[str] = []
    if features_supplied:
        supplied_axes.append("features")
    if runtimes_supplied:
        supplied_axes.append("runtimes")
    if channels_present:
        supplied_axes.append("channels")
    if retention_present:
        supplied_axes.append("retention_days")
    if nodes_present:
        supplied_axes.append("nodes")

    # Delegate to the module scalar off the CANONICALISED known-only
    # lists for envelope-vs-scalar parity (unsupplied axes pass ``None``
    # verbatim so the delegate can distinguish "supplied but empty" from
    # "unsupplied", matching ``has_all``'s posture).
    scalar = _ent.missing_all(
        features=known_features if features_supplied else None,
        runtimes=known_runtimes if runtimes_supplied else None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    # Layer unknown tokens ONTO the per-axis missing list (append at the
    # end, dedup preserved). A caller wiring a single "these ids are
    # blocking the upgrade" tooltip off ``features`` / ``runtimes`` sees
    # the full denial roster; a caller who wants the split still reads
    # ``unknown_features`` / ``unknown_runtimes`` alone.
    missing_features_out: list[str] = list(scalar.get("features") or [])
    if features_supplied:
        for u in unknown_features:
            if u not in missing_features_out:
                missing_features_out.append(u)

    missing_runtimes_out: list[str] = list(scalar.get("runtimes") or [])
    if runtimes_supplied:
        for u in unknown_runtimes:
            if u not in missing_runtimes_out:
                missing_runtimes_out.append(u)

    # Capacity axes: the scalar returns the parsed int on denial. When
    # the caller supplied an UNPARSEABLE value the scalar can't compute
    # a denial (the delegate has_channel_count returns False on non-int
    # too so ``missing_all=... has_all=False`` remains coherent) -- we
    # echo the raw string here so a UI can still surface the typo.
    channels_missing = scalar.get("channels")
    if channels_present and not channels_ok:
        channels_missing = channels_raw
    retention_missing = scalar.get("retention_days")
    if retention_present and not retention_ok:
        retention_missing = retention_raw
    nodes_missing = scalar.get("nodes")
    if nodes_present and not nodes_ok:
        nodes_missing = nodes_raw

    # ``missing_count`` folds: 1 per non-empty per-axis slot on the
    # capacity axes + len(list) on the grant axes. Matches the paired
    # ``has_all`` sense (``missing_count == 0`` iff every supplied axis
    # is granted).
    missing_count = (
        len(missing_features_out)
        + len(missing_runtimes_out)
        + (1 if channels_missing is not None else 0)
        + (1 if retention_missing is not None else 0)
        + (1 if nodes_missing is not None else 0)
    )

    any_missing = missing_count > 0

    required = _ent.min_tier_for_all(
        features=known_features or None,
        runtimes=known_runtimes or None,
        channels=channels_n if channels_present and channels_ok else None,
        retention_days=(
            retention_n if retention_present and retention_ok else None
        ),
        nodes=nodes_n if nodes_present and nodes_ok else None,
    )

    env = _resolver_envelope(_ent)
    cur_rank = env["current_tier_rank"]
    req_rank = _ent.tier_rank(required) if required else -1
    required_label = _ent.tier_label(required) if required else None

    return {
        "features": missing_features_out,
        "runtimes": missing_runtimes_out,
        "channels": channels_missing,
        "retention_days": retention_missing,
        "nodes": nodes_missing,
        "unknown_features": unknown_features,
        "unknown_runtimes": unknown_runtimes,
        "supplied_axes": supplied_axes,
        "supplied_count": len(supplied_axes),
        "missing_count": missing_count,
        "any_missing": any_missing,
        "required_tier": required,
        "required_tier_label": required_label,
        "required_tier_rank": req_rank,
        "current_tier": env["current_tier"],
        "current_tier_rank": cur_rank,
        "grace": env["grace"],
        "enforced": env["enforced"],
        "upgrade_required": bool(required) and req_rank > cur_rank,
    }

def _parse_csv_arg(name: str) -> list[str]:
    """Parse a comma-separated query arg into a normalised id list.

    Empty / whitespace tokens are dropped; remaining tokens are lowercased and
    deduplicated while preserving first-seen order so the response payload is
    stable. ``features=otel_export,,sso,otel_export`` -> ``["otel_export", "sso"]``.
    Never raises (a missing arg returns ``[]``).
    """
    raw = request.args.get(name, "") or ""
    out: list[str] = []
    seen: set[str] = set()
    for token in raw.split(","):
        t = token.strip().lower()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append(t)
    return out

def _has_batch_fallback() -> dict:
    """OSS-free / never-5xx envelope for ``/api/entitlement/has-batch``.

    Fail-closed on the ``has_all`` rollup (matches the singular
    ``/api/entitlement/has-feature`` / ``/has-runtime`` fallbacks): a paywall
    matrix that lost the resolver must not silently render every row as
    granted. All axis slots collapse to the "not supplied" sentinel so a UI
    can still diff against the request shape.
    """
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "has_all": False,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_batch_rollup(batch: dict) -> bool:
    """Fold every emitted row in ``batch`` to ONE ``has_all`` boolean.

    ``True`` iff every emitted row is ``has=True`` AND ``unknown=False`` --
    matches the strict-typo-fail-closed posture of :func:`has_features` /
    :func:`has_runtimes` in the plural fold sibling (a single unknown-id
    row flips the rollup to ``False`` so a typo does not silently render
    as granted). A batch with no rows at all (every axis was "not
    supplied") returns ``True`` vacuously -- the endpoint 400s on that
    input before this rollup runs, so callers never see the vacuous case
    on a live URL.
    """
    for axis in ("features", "runtimes"):
        for row in batch.get(axis) or []:
            if row.get("unknown") or not row.get("has"):
                return False
    for axis in ("channels", "retention_days", "nodes"):
        row = batch.get(axis)
        if row is None:
            continue
        if row.get("unknown") or not row.get("has"):
            return False
    return True

def _has_batch_at_fallback(tier_in: str) -> dict:
    """Grace-shape fallback body for ``/api/entitlement/has-batch-at``.

    Perspective-carrying sibling of :func:`_has_batch_fallback`: on a
    resolver crash the pricing walkthrough keeps rendering with empty
    per-axis rows AND its "from <perspective>" copy still has its
    placeholders. Fail-closed on the ``has_all`` rollup for the same
    reason :func:`_has_batch_fallback` does -- a paywall matrix that
    lost the resolver must not silently render every row as granted.

    Never raises: any tier-metadata blowup falls back to the raw
    ``tier_in`` string and rank ``-1``.
    """
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
    except Exception:
        label = tier_in
        rank = -1
    return {
        "perspective_tier": tier_in,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "has_all": False,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _license_expiry_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two expiry endpoints
    both need (``days_left``, ``has_license``, ``expired``). Lives in the
    handler layer -- not in :mod:`clawmetry.license` -- because
    ``has_license`` is an install-state fact rather than a license-payload
    fact, and both endpoints below need the pair together.

    Never raises: any underlying failure collapses to
    ``{days_left: None, has_license: False, expired: False}`` so callers
    keep the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
    except Exception as exc:
        logger.debug("_license_expiry_snapshot: underlying read failed: %s", exc)
        return {"days_left": None, "has_license": False, "expired": False}
    if not isinstance(info, dict):
        return {"days_left": None, "has_license": False, "expired": False}
    days = info.get("days_left")
    days_left = days if isinstance(days, int) else None
    status = info.get("status")
    return {
        "days_left": days_left,
        "has_license": True,
        "expired": status == "expired",
    }

def _license_tier_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two tier endpoints
    both need (``tier``, ``has_license``, ``valid``). Lives in the
    handler layer -- not in :mod:`clawmetry.license` -- because
    ``has_license`` is an install-state fact rather than a license-payload
    fact, and both endpoints below need the pair together so a UI cannot
    catch them disagreeing on ``has_license`` for the same install.

    Never raises: any underlying failure collapses to
    ``{tier: None, has_license: False, valid: False}`` so callers keep
    the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        tier = _lic.license_tier()
    except Exception as exc:
        logger.debug("_license_tier_snapshot: underlying read failed: %s", exc)
        return {"tier": None, "has_license": False, "valid": False}
    if not isinstance(info, dict):
        return {"tier": None, "has_license": False, "valid": False}
    return {
        "tier": tier,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_gate_snapshot() -> dict:
    """Shared one-shot read of the installed-license state for the boolean-gate
    endpoints below.

    Reads :func:`clawmetry.license.current_license_info` ONCE so the paired
    ``/api/license/is-expired`` and ``/api/license/is-perpetual`` endpoints
    can't disagree on ``has_license`` / ``status`` for the same key -- a UI
    that binds both in the same tile always sees a consistent snapshot.

    Never raises. Any introspection failure (import error, corrupt install,
    cryptography-lib mismatch) collapses to the no-license shape so the
    endpoint stack never 5xxs; the "expired" / "perpetual" gates degrade to
    ``False`` on that branch, matching the module-level scalar helpers'
    OSS-free posture.
    """
    info = None
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
    except Exception as exc:
        logger.debug("_license_gate_snapshot: error: %s", exc)
        info = None
    has_license = info is not None
    status = info.get("status") if info else None
    exp = info.get("exp") if info else None
    return {
        "has_license": has_license,
        "status": status,
        "has_exp": bool(has_license and exp is not None),
        # An "invalid-signature" branch collapses ``exp`` to ``None`` on
        # purpose (we don't trust an unsigned body) -- rule it out here so a
        # forged file can't masquerade as "perpetual" via the gate endpoint.
        "expired": bool(has_license and status == "expired"),
        "perpetual": bool(has_license and status != "invalid" and exp is None),
    }

def _pro_install_snapshot() -> dict:
    """Shared helper: read once, derive the quartet the two ``installed_at``-
    derived endpoints both need (``installed_at``, ``age_days``,
    ``marker_present``, ``installed``). Lives in the handler layer -- not
    in :mod:`clawmetry.license` -- because ``marker_present`` /
    ``installed`` are install-state facts rather than marker-payload
    facts, and both endpoints below need them together so a UI cannot
    catch them disagreeing on the same install.

    ``installed_at`` mirrors :func:`clawmetry.license.pro_installed_at` --
    the raw epoch surfaced by the marker, unmodified. ``age_days`` mirrors
    :func:`clawmetry.license.pro_install_age_days` -- floor-divided from
    seconds, clamped to ``max(0, ...)`` so a clock-skewed
    ``installed_at`` in the future never renders as a negative age.

    ``marker_present`` is deliberately independent of ``installed``: an
    operator can have the marker on disk (wheel was provisioned
    yesterday) even when Python cannot currently import
    ``clawmetry-pro`` (wheel was pip-uninstalled since), and the paywall-
    debug tile that binds these endpoints wants to see that disagreement
    rather than have it collapsed into a single boolean.

    Never raises: any underlying failure collapses to
    ``{installed_at: None, age_days: None, marker_present: False,
    installed: False}`` so callers keep the "no marker" branch shape.
    """
    try:
        from clawmetry import license as _lic

        installed_at = _lic.pro_installed_at()
        age = _lic.pro_install_age_days()
        installed = _lic.pro_installed()
    except Exception as exc:
        logger.debug("_pro_install_snapshot: underlying read failed: %s", exc)
        return {
            "installed_at": None,
            "age_days": None,
            "marker_present": False,
            "installed": False,
        }
    marker_present = installed_at is not None
    return {
        "installed_at": installed_at,
        "age_days": age,
        "marker_present": marker_present,
        "installed": bool(installed),
    }

def _license_nodes_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two node-limit endpoints
    both need (``nodes``, ``has_license``, ``valid``). Lives in the handler
    layer -- not in :mod:`clawmetry.license` -- because ``has_license`` is
    an install-state fact rather than a license-payload fact, and both
    endpoints below need the pair together so a UI cannot catch them
    disagreeing on ``has_license`` for the same install.

    Never raises: any underlying failure collapses to
    ``{nodes: None, has_license: False, valid: False}`` so callers keep the
    "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        nodes = _lic.license_nodes()
    except Exception as exc:
        logger.debug("_license_nodes_snapshot: underlying read failed: %s", exc)
        return {"nodes": None, "has_license": False, "valid": False}
    if not isinstance(info, dict):
        return {"nodes": None, "has_license": False, "valid": False}
    return {
        "nodes": nodes,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_presence_snapshot() -> dict:
    """Shared one-shot read for the two install-state gate endpoints below.

    Reads :func:`clawmetry.license.has_license` and
    :func:`clawmetry.license.current_license_info` together so the paired
    ``/api/license/present`` and ``/api/license/valid`` endpoints can't
    disagree on ``present`` / ``status`` for the same install -- a UI that
    binds both in the same tile always sees a consistent snapshot.

    Returned dict::

        {
          "present": <bool>,              # is a license file on disk at all?
          "valid": <bool>,                # signature-valid AND not expired
          "status": <str|null>,           # "active"/"expired"/"invalid"/None
        }

    Never raises. Any introspection failure (import error, corrupt install,
    cryptography-lib mismatch) collapses to
    ``{present: False, valid: False, status: None}`` so the endpoint stack
    never 5xxs, matching the OSS-free posture of the surrounding license
    endpoints.
    """
    try:
        from clawmetry import license as _lic

        present = bool(_lic.has_license())
        info = _lic.current_license_info() if present else None
    except Exception as exc:
        logger.debug("_license_presence_snapshot: error: %s", exc)
        return {"present": False, "valid": False, "status": None}
    status = info.get("status") if isinstance(info, dict) else None
    valid = bool(isinstance(info, dict) and info.get("valid"))
    return {
        "present": present,
        "valid": valid,
        "status": status,
    }

def _license_subject_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two subject endpoints
    both need (``subject``, ``has_license``, ``valid``). Lives in the
    handler layer -- not in :mod:`clawmetry.license` -- because
    ``has_license`` is an install-state fact rather than a license-payload
    fact, and both endpoints below need the pair together so a UI cannot
    catch them disagreeing on ``has_license`` for the same install.

    Never raises: any underlying failure collapses to
    ``{subject: None, has_license: False, valid: False}`` so callers keep
    the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        subject = _lic.license_subject()
    except Exception as exc:
        logger.debug("_license_subject_snapshot: underlying read failed: %s", exc)
        return {"subject": None, "has_license": False, "valid": False}
    if not isinstance(info, dict):
        return {"subject": None, "has_license": False, "valid": False}
    return {
        "subject": subject,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_subject_at_snapshot() -> dict:
    """Shared one-shot read for the ``/api/license/subject-at`` endpoint
    below.

    Reads :func:`clawmetry.license.license_subject` (current-time
    subject), :func:`clawmetry.license.current_license_info` (for
    ``has_license`` / ``valid`` NOW), and
    :func:`clawmetry.license.license_expires_at` (for the
    ``expires_at`` field the sibling perspective-epoch tiles all carry)
    ONCE so a UI binding both the current-time endpoint and this
    perspective-epoch endpoint in the same tile can't catch them
    disagreeing on ``subject`` / ``expires_at`` / ``has_license`` /
    ``valid`` for the same install -- mirrors the
    ``_license_subject_snapshot`` + ``_license_tier_at_snapshot``
    pattern used by the current-time subject pair and the
    perspective-epoch tier scalar.

    ``subject`` here is the CURRENT-time subject (matches
    :func:`clawmetry.license.license_subject`); the perspective-epoch
    subject (``subject_at``) is derived per-request by the endpoint via
    :func:`clawmetry.license.license_subject_at` and lives on top of
    this snapshot -- keeping ``subject`` in the shared read guarantees
    a UI that renders "as of <date> vs now" tiles side-by-side can
    never catch them disagreeing on the current-time reference.

    Never raises. Any introspection failure collapses to the OSS-free
    branch shape (``subject=None``, ``expires_at=None``,
    ``has_license=False``, ``valid=False``) so the endpoint never 5xxs
    -- same posture as the surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        subject = _lic.license_subject()
        info = _lic.current_license_info()
        expires = _lic.license_expires_at()
    except Exception as exc:
        logger.debug("_license_subject_at_snapshot: underlying read failed: %s", exc)
        return {
            "subject": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(subject, str):
        subject = None
    if info is None or not isinstance(info, dict):
        return {
            "subject": subject,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "subject": subject,
        "expires_at": expires,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_permissions_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two permission-hygiene
    endpoints both need (``permissions_safe``, ``file_mode``,
    ``has_license``). Lives in the handler layer -- not in
    :mod:`clawmetry.license` -- because ``has_license`` is an install-state
    fact rather than a license-payload fact, and both endpoints below need
    the trio together so a UI cannot catch them disagreeing on
    ``has_license`` for the same install.

    Deliberately independent of signature validity: the on-disk mode is a
    file-hygiene fact, not a license-payload fact, so a tampered or expired
    key file still surfaces its real ``file_mode`` here -- exactly the
    state a "tighten file permissions" affordance needs to render.

    Never raises: any underlying failure collapses to
    ``{permissions_safe: None, file_mode: None, has_license: False}`` so
    callers keep the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        has = _lic.has_license() if hasattr(_lic, "has_license") else os.path.isfile(
            _lic.LICENSE_PATH
        )
        perms = _lic.license_permissions_safe()
        mode = _lic.license_file_mode()
    except Exception as exc:
        logger.debug("_license_permissions_snapshot: underlying read failed: %s", exc)
        return {"permissions_safe": None, "file_mode": None, "has_license": False}
    return {
        "permissions_safe": perms,
        "file_mode": mode,
        "has_license": bool(has),
    }

def _license_issued_snapshot() -> dict:
    """Shared helper: read once, derive the quartet the two ``iat``-derived
    endpoints both need (``issued_at``, ``age_days``, ``has_license``,
    ``valid``). Lives in the handler layer -- not in
    :mod:`clawmetry.license` -- because ``has_license`` is an install-state
    fact rather than a license-payload fact, and both endpoints below need
    the pair together so a UI cannot catch them disagreeing on
    ``has_license`` for the same install.

    Deliberately lenient on expiry, matching the ``license_issued_at`` /
    ``license_age_days`` posture: a signed-but-lapsed key still surfaces
    its real ``issued_at`` / ``age_days`` so a support/audit tile can
    render "issued 800 days ago" without special-casing the expired
    branch. The ``valid`` field independently carries the "signature-valid
    AND not expired" signal for callers that DO want to hide the row on
    lapsed keys.

    Never raises: any underlying failure collapses to
    ``{issued_at: None, age_days: None, has_license: False, valid: False}``
    so callers keep the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        issued = _lic.license_issued_at()
        age = _lic.license_age_days()
    except Exception as exc:
        logger.debug("_license_issued_snapshot: underlying read failed: %s", exc)
        return {
            "issued_at": None,
            "age_days": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(info, dict):
        return {
            "issued_at": None,
            "age_days": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "issued_at": issued,
        "age_days": age,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_state_snapshot() -> dict:
    """Shared one-shot read for the paired ``/api/license/state`` and
    ``/api/license/is-state`` endpoints below.

    Reads :func:`clawmetry.license.license_state` and
    :func:`clawmetry.license.current_license_info` ONCE so a UI binding
    both endpoints in the same tile can't catch them disagreeing on
    ``state`` / ``has_license`` / ``valid`` for the same install --
    mirrors the ``_license_tier_snapshot`` / ``_license_issued_snapshot``
    pattern used by the tier + issued-at endpoint pairs.

    Never raises. Any introspection failure collapses to the OSS-free
    branch shape (``state="no_license"``, ``has_license=False``,
    ``valid=False``) so the endpoint stack never 5xxs -- same posture as
    the surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        state = _lic.license_state()
        info = _lic.current_license_info()
    except Exception as exc:
        logger.debug("_license_state_snapshot: underlying read failed: %s", exc)
        return {"state": "no_license", "has_license": False, "valid": False}
    if not isinstance(state, str):
        state = "no_license"
    if info is None:
        return {"state": state, "has_license": False, "valid": False}
    if not isinstance(info, dict):
        return {"state": state, "has_license": False, "valid": False}
    return {
        "state": state,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_pubkey_fingerprint_snapshot() -> dict:
    """Shared helper: read once, derive the trio the two pubkey-fingerprint
    endpoints both need (``pubkey_fingerprint_sha256``,
    ``pubkey_fingerprint_short``, ``valid``). Lives in the handler layer so a
    UI binding both endpoints cannot catch them disagreeing on the trust
    anchor for the same install.

    ``valid`` here means the EMBEDDED PUBKEY parses -- distinct from
    ``/api/license/valid`` (signature-valid + not expired). A tampered
    ``_PUBLIC_KEY_PEM`` collapses ``valid`` to ``False`` even without any
    license file installed, exactly matching the trust-anchor semantic a
    supply-chain / attestation tile needs.

    Never raises: any underlying failure collapses to
    ``{pubkey_fingerprint_sha256: None, pubkey_fingerprint_short: None,
    valid: False}`` so callers keep the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        fp = _lic.pubkey_fingerprint()
    except Exception as exc:
        logger.debug(
            "_license_pubkey_fingerprint_snapshot: underlying read failed: %s",
            exc,
        )
        return {
            "pubkey_fingerprint_sha256": None,
            "pubkey_fingerprint_short": None,
            "valid": False,
        }
    short = fp[:16] if isinstance(fp, str) and fp else None
    return {
        "pubkey_fingerprint_sha256": fp if isinstance(fp, str) and fp else None,
        "pubkey_fingerprint_short": short,
        "valid": bool(fp) and isinstance(fp, str),
    }

def _license_expires_snapshot() -> dict:
    """Shared helper: read once, derive the quartet the two ``exp``-derived
    endpoints both need (``expires_at``, ``days_until_expiry``,
    ``has_license``, ``valid``). Lives in the handler layer -- not in
    :mod:`clawmetry.license` -- because ``has_license`` is an install-state
    fact rather than a license-payload fact, and both endpoints below need
    the pair together so a UI cannot catch them disagreeing on
    ``has_license`` for the same install.

    Deliberately lenient on expiry, matching the ``license_expires_at`` /
    ``days_until_expiry`` posture: a signed-but-lapsed key still surfaces
    its real ``expires_at`` (with a negative ``days_until_expiry``) so a
    support/audit tile can render "expired 12 days ago" without special-
    casing the expired branch. The ``valid`` field independently carries
    the "signature-valid AND not expired" signal for callers that DO want
    to hide the row on lapsed keys.

    Never raises: any underlying failure collapses to
    ``{expires_at: None, days_until_expiry: None, has_license: False,
    valid: False}`` so callers keep the "OSS-free" branch shape.
    """
    try:
        from clawmetry import license as _lic

        info = _lic.current_license_info()
        expires = _lic.license_expires_at()
        days = _lic.days_until_expiry()
    except Exception as exc:
        logger.debug("_license_expires_snapshot: underlying read failed: %s", exc)
        return {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(info, dict):
        return {
            "expires_at": None,
            "days_until_expiry": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "expires_at": expires,
        "days_until_expiry": days,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_state_at_snapshot() -> dict:
    """Shared one-shot read for the paired ``/api/license/state-at`` and
    ``/api/license/is-state-at`` endpoints below.

    Reads :func:`clawmetry.license.license_state` (current-time state),
    :func:`clawmetry.license.current_license_info` (for ``has_license`` /
    ``valid`` NOW), and :func:`clawmetry.license.license_expires_at`
    (for the ``expires_at`` field the sibling perspective-epoch tiles
    all carry) ONCE so a UI binding both endpoints in the same tile
    can't catch them disagreeing on ``state`` / ``expires_at`` /
    ``has_license`` / ``valid`` for the same install -- mirrors the
    ``_license_state_snapshot`` + ``_license_expires_snapshot`` pattern
    used by the current-time state pair and the ``exp``-derived
    perspective-epoch trio.

    ``state`` here is the CURRENT-time state (matches
    :func:`clawmetry.license.license_state`); the perspective-epoch
    state (``state_at``) is derived per-request by each endpoint via
    :func:`clawmetry.license.license_state_at` and lives on top of this
    snapshot -- keeping ``state`` in the shared read guarantees a UI
    that renders "as of <date> vs now" tiles side-by-side can never
    catch them disagreeing on the current-time reference.

    Never raises. Any introspection failure collapses to the OSS-free
    branch shape (``state="no_license"``, ``expires_at=None``,
    ``has_license=False``, ``valid=False``) so the endpoint stack never
    5xxs -- same posture as the surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        state = _lic.license_state()
        info = _lic.current_license_info()
        expires = _lic.license_expires_at()
    except Exception as exc:
        logger.debug("_license_state_at_snapshot: underlying read failed: %s", exc)
        return {
            "state": "no_license",
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(state, str):
        state = "no_license"
    if info is None:
        return {
            "state": state,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(info, dict):
        return {
            "state": state,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "state": state,
        "expires_at": expires,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _parse_license_epochs_csv(param: str = "epochs"):
    """Shared query-string pre-parser for the three ``/api/license/
    *-at-batch`` endpoints below.

    Returns ``(raw_tokens, err)``:

      * ``raw_tokens`` -- a list of stripped, non-empty tokens taken
        from the ``epochs`` query parameter in first-seen order. The
        underlying batch helpers own de-dup + int-coercion; the caller
        here only needs to hand them the ordered token list.
      * ``err`` -- ``"missing"`` when ``?epochs=`` is absent or blank
        after stripping / commas so the caller can return ``400
        missing epochs`` uniformly across the trio, ``None`` otherwise.

    Tokens are NOT int-coerced here on purpose: the batch helpers admit
    "bad" tokens (``bool``, non-numeric string, ``None``) as their own
    row so callers can identify the offending entry in the response
    rather than having the 400 hide the whole batch on a single typo.
    """
    raw = request.args.get(param)
    if raw is None:
        return [], "missing"
    tokens = [tok.strip() for tok in str(raw).split(",")]
    tokens = [tok for tok in tokens if tok]
    if not tokens:
        return [], "missing"
    return tokens, None

def _parse_license_days_csv(param: str = "days"):
    """Shared query-string pre-parser for the days-axis batch endpoint
    below.

    Mirrors :func:`_parse_license_epochs_csv` but on the ``days``
    axis: returns ``(raw_tokens, err)`` where ``err == "missing"`` when
    ``?days=`` is absent or blank after stripping / commas so the caller
    can return ``400 missing days`` uniformly, ``None`` otherwise.
    Tokens are NOT int-coerced here on purpose: the batch helper admits
    "bad" tokens (``bool``, non-numeric string, ``None``, negative int)
    as their own row so callers can identify the offending threshold in
    the response rather than having the ``400`` hide the whole batch on
    a single typo.
    """
    raw = request.args.get(param)
    if raw is None:
        return [], "missing"
    tokens = [tok.strip() for tok in str(raw).split(",")]
    tokens = [tok for tok in tokens if tok]
    if not tokens:
        return [], "missing"
    return tokens, None

def _license_tier_at_snapshot() -> dict:
    """Shared one-shot read for the paired ``/api/license/tier-at`` and
    ``/api/license/tier-at-batch`` endpoints below.

    Reads :func:`clawmetry.license.license_tier` (current-time tier),
    :func:`clawmetry.license.current_license_info` (for ``has_license`` /
    ``valid`` NOW), and :func:`clawmetry.license.license_expires_at`
    (for the ``expires_at`` field the sibling perspective-epoch tiles
    all carry) ONCE so a UI binding both endpoints in the same tile
    can't catch them disagreeing on ``tier`` / ``expires_at`` /
    ``has_license`` / ``valid`` for the same install -- mirrors the
    ``_license_tier_snapshot`` + ``_license_expires_snapshot`` /
    ``_license_state_at_snapshot`` pattern used by the current-time
    tier pair and the state-derived perspective-epoch trio.

    ``tier`` here is the CURRENT-time tier (matches
    :func:`clawmetry.license.license_tier`); the perspective-epoch
    tier (``tier_at``) is derived per-request by each endpoint via
    :func:`clawmetry.license.license_tier_at` and lives on top of this
    snapshot -- keeping ``tier`` in the shared read guarantees a UI
    that renders "as of <date> vs now" tiles side-by-side can never
    catch them disagreeing on the current-time reference.

    Never raises. Any introspection failure collapses to the OSS-free
    branch shape (``tier=None``, ``expires_at=None``,
    ``has_license=False``, ``valid=False``) so the endpoint stack
    never 5xxs -- same posture as the surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        tier = _lic.license_tier()
        info = _lic.current_license_info()
        expires = _lic.license_expires_at()
    except Exception as exc:
        logger.debug("_license_tier_at_snapshot: underlying read failed: %s", exc)
        return {
            "tier": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    if not isinstance(tier, str):
        tier = None
    if info is None or not isinstance(info, dict):
        return {
            "tier": tier,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "tier": tier,
        "expires_at": expires,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

def _license_features_at_snapshot() -> dict:
    """Shared one-shot read for the paired ``/api/license/features-at``
    and ``/api/license/features-at-batch`` endpoints below.

    Reads :func:`clawmetry.license.license_features` (current-time
    features list), :func:`clawmetry.license.current_license_info` (for
    ``has_license`` / ``valid`` NOW), and
    :func:`clawmetry.license.license_expires_at` (for the ``expires_at``
    field the sibling perspective-epoch tiles all carry) ONCE so a UI
    binding both endpoints in the same tile can't catch them disagreeing
    on ``features`` / ``expires_at`` / ``has_license`` / ``valid`` for
    the same install -- mirrors the ``_license_state_at_snapshot``
    pattern used by the state-derived perspective-epoch trio.

    ``features`` here is the CURRENT-time features list (matches
    :func:`clawmetry.license.license_features`); the perspective-epoch
    features list (``features_at``) is derived per-request by each
    endpoint via :func:`clawmetry.license.license_features_at` and
    lives on top of this snapshot -- keeping ``features`` in the shared
    read guarantees a UI that renders "as of <date> vs now" tiles
    side-by-side can never catch them disagreeing on the current-time
    reference.

    Never raises. Any introspection failure collapses to the OSS-free
    branch shape (``features=None``, ``expires_at=None``,
    ``has_license=False``, ``valid=False``) so the endpoint stack never
    5xxs -- same posture as the surrounding license endpoints.
    """
    try:
        from clawmetry import license as _lic

        feats = _lic.license_features()
        info = _lic.current_license_info()
        expires = _lic.license_expires_at()
    except Exception as exc:
        logger.debug(
            "_license_features_at_snapshot: underlying read failed: %s", exc
        )
        return {
            "features": None,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    if feats is not None and not isinstance(feats, list):
        feats = None
    if info is None or not isinstance(info, dict):
        return {
            "features": feats,
            "expires_at": None,
            "has_license": False,
            "valid": False,
        }
    return {
        "features": feats,
        "expires_at": expires,
        "has_license": True,
        "valid": bool(info.get("valid")),
    }

_PAYWALL_DISTINCT_DIMS = ("event", "feature", "harness", "source", "plan_chosen")

def _route_actor() -> str:
    try:
        for h in ("X-Actor", "X-Forwarded-For"):
            v = request.headers.get(h, "") or ""
            v = v.split(",")[0].strip()
            if v:
                return v[:128]
        return (request.remote_addr or "")[:128]
    except Exception:
        return ""

def _activate_envelope(ok, message, error=None):
    """Full-shape envelope for ``/api/license/activate``.

    Every branch (missing-key, healthy-success, healthy-failure,
    introspection-exception) carries the SAME field set so a UI can
    render `data.ok` + `data.message` uniformly without special-casing
    which keys are present. ``error`` is populated on the two failure
    branches for back-compat with the pre-shape-parity consumers that
    read `data.error`; healthy branches leave it ``None``. Mirrors the
    parity contract PR #4047 landed for ``/status`` + ``/verify``.
    """
    return {"ok": bool(ok), "message": str(message), "error": error}

def _deactivate_envelope(ok, removed, message="", error=None):
    """Full-shape envelope for ``/api/license/deactivate``.

    Every branch (healthy-noop, healthy-removed, remove-failed,
    introspection-exception) carries ``{ok, removed, message, error}``
    so a UI can bind to ``data.removed`` uniformly without checking
    whether it's the exception branch (which used to drop the field
    entirely). ``message`` is populated on every branch; ``error`` is
    populated only on the two failure branches for back-compat.
    """
    return {
        "ok": bool(ok),
        "removed": bool(removed),
        "message": str(message),
        "error": error,
    }

def _next_prev_tier_axis_spec_grace_body(
    axis: str, item: str | None
) -> dict:
    """Fallback envelope shared by the four bare next/previous per-axis
    spec routes. Keeps the shape identical to the happy path so a
    resolver failure never breaks a paywall tooltip client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        axis: item or "",
        "target": None,
        "target_label": None,
        "target_rank": None,
        "row": None,
        "grace": True,
        "enforced": False,
    }

def _next_prev_tier_channel_catalog_grace_body() -> dict:
    """Fallback envelope shared by the two next/previous channel-catalog
    routes. Keeps the shape identical to the happy path so a resolver
    failure never breaks an upgrade-preview panel client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "channels": [],
        "grace": True,
        "enforced": False,
    }

def _next_prev_tier_axis_catalog_grace_body(axis: str) -> dict:
    """Fallback envelope shared by the next/previous feature- and
    runtime-catalog routes. Same shape as the happy path so a resolver
    failure never breaks an upgrade-preview matrix client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        axis: [],
        "grace": True,
        "enforced": False,
    }

def _next_prev_tier_axis_spec_batch_grace_body(axis: str) -> dict:
    """Fallback envelope shared by the four bare next/previous per-axis
    spec-batch routes. Keeps the shape identical to the happy path so a
    resolver failure never breaks a paywall matrix client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        axis: [],
        "unknown": [],
        "grace": True,
        "enforced": False,
    }

def _next_prev_lock_reason_grace_body(key: str, kind: str) -> dict:
    """Fallback envelope shared by the bare next/previous lock-reason
    routes. Keeps the shape identical to the happy path so a resolver
    failure never breaks a paywall tooltip client-side."""
    return {
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "key": key,
        "kind": kind,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "reason": None,
        "locked": False,
        "allowed": True,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "upgrade_required": False,
        "grace": True,
        "enforced": False,
    }

def _next_prev_lock_reason(direction: str):
    """Shared handler body for ``/{next,previous}-tier-lock-reason``.

    Current-relative sibling of the ``_next_prev_lock_reason_at`` handler
    -- takes no ``tier=`` (the source is the resolved entitlement) and
    walks :meth:`Entitlement.next_tier_lock_reason` /
    :meth:`Entitlement.previous_tier_lock_reason` instead of the source-
    parameterised ``_at`` module helpers, matching the pattern of
    ``/next-tier-feature-spec`` vs ``/next-tier-feature-spec-at``.

    Mirrors the axis-parsing contract of ``/lock-reason`` /
    ``/lock-reason-at`` (exactly one of ``feature=`` / ``runtime=`` /
    ``channels=`` / ``retention_days=`` / ``nodes=``). ``target`` /
    ``reason`` collapse to ``null`` at the rung edge (ceiling for
    ``next``, floor for ``previous``) so the surface stays 200.

    ``direction`` is ``"next"`` or ``"previous"``. Never 5xxs: resolver
    failure short-circuits to the grace-shape envelope so the paywall
    surface stays mute.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason"
    try:
        from clawmetry import entitlements as _ent

        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            channels_ok,
            channels_n,
            channels_raw,
        ) = _parse_capacity_arg("channels")
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _parse_capacity_arg("retention_days")
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime_in),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
                        )
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, channels=, "
                            "retention_days=, or nodes="
                        )
                    }
                ),
                400,
            )

        if feature and feature not in _ent.ALL_FEATURES:
            return (
                jsonify(
                    {
                        "error": "unknown feature",
                        "which": "feature",
                        "feature": feature,
                    }
                ),
                404,
            )
        canonical_rt = None
        if runtime_in:
            canonical_rt = _ent.canonical_runtime(runtime_in)
            if not canonical_rt or canonical_rt not in _ent.ALL_RUNTIMES:
                return (
                    jsonify(
                        {
                            "error": "unknown runtime",
                            "which": "runtime",
                            "runtime": runtime_in,
                        }
                    ),
                    404,
                )

        ent = _ent.get_entitlement()
        if direction == "next":
            target = ent.next_purchasable_tier()
            walk = ent.next_tier_lock_reason
        else:
            target = ent.previous_purchasable_tier()
            walk = ent.previous_tier_lock_reason

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = walk(feature, kind=kind) if target else None
            allowed = reason is None
        elif runtime_in:
            key, kind = canonical_rt, "runtime"
            required = _ent.min_tier_for_runtime(canonical_rt)
            reason = walk(canonical_rt, kind=kind) if target else None
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok and target:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = walk(str(channels_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_channel_count(channels_n)
                    if channels_ok
                    else None
                )
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok and target:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = walk(str(retention_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_retention_window(retention_n)
                    if retention_ok
                    else None
                )
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok and target:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = walk(str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_node_count(nodes_n)
                    if nodes_ok
                    else None
                )
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(ent.tier)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "current_tier": ent.tier,
                "current_tier_label": _ent.tier_label(ent.tier),
                "current_tier_rank": cur_rank,
                "key": key,
                "kind": kind,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
                "grace": bool(ent.grace),
                "enforced": _ent.is_enforced(),
            }
        )
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
        else:
            key, kind = "", ""
        return jsonify(_next_prev_lock_reason_grace_body(key, kind))

def _next_prev_lock_reason_at(direction: str):
    """Shared handler body for ``/{next,previous}-tier-lock-reason-at``.

    Mirrors the axis-parsing contract of ``/api/entitlement/lock-reason-at``
    (exactly one of ``feature=`` / ``runtime=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=``) and the ceiling/floor envelope shape of
    ``/next-tier-feature-spec-at`` / ``/previous-tier-feature-spec-at``
    (``target`` / ``target_label`` / ``target_rank`` collapse to ``null``
    at the rung edge, lock fields collapse to the grace-shape unlocked
    row so the surface keeps rendering).

    ``direction`` is ``"next"`` or ``"previous"``: picks
    :func:`entitlements._next_purchasable_tier_after` vs
    :func:`entitlements._previous_purchasable_tier_before` and the matching
    log-name. Never 5xxs: synthesis failure short-circuits to the
    grace-shape envelope with ``target=null`` so the paywall surface stays
    mute.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    log_name = f"api_entitlement_{direction}_tier_lock_reason_at"
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        (
            channels_present,
            channels_ok,
            channels_n,
            channels_raw,
        ) = _parse_capacity_arg("channels")
        (
            retention_present,
            retention_ok,
            retention_n,
            retention_raw,
        ) = _parse_capacity_arg("retention_days")
        (
            nodes_present,
            nodes_ok,
            nodes_n,
            nodes_raw,
        ) = _parse_capacity_arg("nodes")

        supplied = [
            bool(feature),
            bool(runtime_in),
            channels_present,
            retention_present,
            nodes_present,
        ]
        n_supplied = sum(1 for s in supplied if s)
        if n_supplied == 0:
            return (
                jsonify(
                    {
                        "error": (
                            "supply exactly one of feature=<id>, runtime=<id>, "
                            "channels=<int>, retention_days=<int>, or "
                            "nodes=<int>"
                        )
                    }
                ),
                400,
            )
        if n_supplied > 1:
            return (
                jsonify(
                    {
                        "error": (
                            "supply only one of feature=, runtime=, channels=, "
                            "retention_days=, or nodes="
                        )
                    }
                ),
                400,
            )

        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            walk = _ent.next_tier_lock_reason_at
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            walk = _ent.previous_tier_lock_reason_at

        if feature:
            key, kind = feature, "feature"
            required = _ent.min_tier_for_feature(feature)
            reason = walk(tier_in, feature, kind=kind) if target else None
            allowed = reason is None
        elif runtime_in:
            rt = _ent.canonical_runtime(runtime_in)
            key, kind = rt or runtime_in, "runtime"
            required = _ent.min_tier_for_runtime(rt) if rt else None
            reason = (
                walk(tier_in, rt or runtime_in, kind=kind) if target else None
            )
            allowed = reason is None
        elif channels_present:
            key, kind = channels_raw, "channels"
            if channels_ok and target:
                required = _ent.min_tier_for_channel_count(channels_n)
                reason = walk(tier_in, str(channels_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_channel_count(channels_n)
                    if channels_ok
                    else None
                )
                reason = None
                allowed = True
        elif retention_present:
            key, kind = retention_raw, "retention_days"
            if retention_ok and target:
                required = _ent.min_tier_for_retention_window(retention_n)
                reason = walk(tier_in, str(retention_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_retention_window(retention_n)
                    if retention_ok
                    else None
                )
                reason = None
                allowed = True
        else:
            key, kind = nodes_raw, "nodes"
            if nodes_ok and target:
                required = _ent.min_tier_for_node_count(nodes_n)
                reason = walk(tier_in, str(nodes_n), kind=kind)
                allowed = reason is None
            else:
                required = (
                    _ent.min_tier_for_node_count(nodes_n)
                    if nodes_ok
                    else None
                )
                reason = None
                allowed = True

        cur_rank = _ent.tier_rank(tier_in)
        req_rank = _ent.tier_rank(required) if required else -1
        required_label = _ent.tier_label(required) if required else None
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": cur_rank,
                "key": key,
                "kind": kind,
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": (
                    _ent.tier_rank(target) if target else None
                ),
                "reason": reason,
                "locked": reason is not None,
                "allowed": allowed,
                "required_tier": required,
                "required_tier_label": required_label,
                "required_tier_rank": req_rank,
                "upgrade_required": bool(required) and req_rank > cur_rank,
            }
        )
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        feature = (request.args.get("feature") or "").strip().lower()
        runtime_in = (request.args.get("runtime") or "").strip().lower()
        channels_raw = (request.args.get("channels") or "").strip()
        retention_raw = (request.args.get("retention_days") or "").strip()
        nodes_raw = (request.args.get("nodes") or "").strip()
        if feature:
            key, kind = feature, "feature"
        elif runtime_in:
            key, kind = runtime_in, "runtime"
        elif channels_raw:
            key, kind = channels_raw, "channels"
        elif retention_raw:
            key, kind = retention_raw, "retention_days"
        elif nodes_raw:
            key, kind = nodes_raw, "nodes"
        else:
            key, kind = "", ""
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "key": key,
                "kind": kind,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "reason": None,
                "locked": False,
                "allowed": True,
                "required_tier": None,
                "required_tier_label": None,
                "required_tier_rank": -1,
                "upgrade_required": False,
            }
        )

def _next_prev_lock_reason_at_batch(direction: str):
    """Shared body for the ``/next-tier-lock-reason-at-batch`` and
    ``/previous-tier-lock-reason-at-batch`` endpoints. ``direction`` is
    ``"next"`` or ``"previous"``.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason_at_batch"
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_lock_reason_at_batch(
                tier_in,
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_lock_reason_at_batch(
                tier_in,
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        ent = _ent.get_entitlement()
        batch["tier"] = tier_in
        batch["tier_label"] = _ent.tier_label(tier_in)
        batch["tier_rank"] = _ent.tier_rank(tier_in)
        batch["target"] = target
        batch["target_label"] = _ent.tier_label(target) if target else None
        batch["target_rank"] = _ent.tier_rank(target) if target else None
        batch["current_tier"] = ent.tier
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        return jsonify(
            {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "current_tier": "oss",
                "current_tier_rank": 0,
                "grace": True,
                "enforced": False,
            }
        )

def _next_prev_tier_feature_spec_at_batch(
    direction: str,
):
    """Shared helper for the two ``/api/entitlement/{next,previous}-tier-
    feature-spec-at-batch`` handlers.

    ``direction`` selects the rung helper (``next`` / ``previous``).
    Returned envelope shape is identical for both directions so the
    paywall surface can swap one URL for the other without re-deriving
    the row schema.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        features = _parse_csv_arg("features")
        if not features:
            return jsonify({"error": "supply features=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_feature_spec_at_batch(tier_in, features)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_feature_spec_at_batch(tier_in, features)
        if batch is None:
            batch = {"features": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "features": batch.get("features", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_feature_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "features": [],
                "unknown": [],
            }
        )

def _next_prev_tier_runtime_spec_at_batch(
    direction: str,
):
    """Runtime-axis twin of :func:`_next_prev_tier_feature_spec_at_batch`.
    Aliases are canonicalised one layer below in the helper -- this
    wrapper just shuttles the supplied CSV through ``_parse_csv_arg``
    and lets the helper de-duplicate, mirroring ``/runtime-spec-path-
    batch``.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        runtimes = _parse_csv_arg("runtimes")
        if not runtimes:
            return jsonify({"error": "supply runtimes=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_runtime_spec_at_batch(tier_in, runtimes)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_runtime_spec_at_batch(tier_in, runtimes)
        if batch is None:
            batch = {"runtimes": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "runtimes": batch.get("runtimes", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_runtime_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "runtimes": [],
                "unknown": [],
            }
        )

def _next_prev_tier_channel_spec_at_batch(
    direction: str,
):
    """Shared helper for the two ``/api/entitlement/{next,previous}-tier-
    channel-spec-at-batch`` handlers.

    Channel-axis twin of :func:`_next_prev_tier_feature_spec_at_batch`
    / :func:`_next_prev_tier_runtime_spec_at_batch`. ``direction``
    selects the rung helper (``next`` / ``previous``). Returned
    envelope shape is identical for both directions so the paywall
    surface can swap one URL for the other without re-deriving the row
    schema.
    """
    raw_tier = request.args.get("tier")
    tier_in = (raw_tier or "").strip().lower()
    if not tier_in:
        return jsonify({"error": "missing tier"}), 400
    try:
        from clawmetry import entitlements as _ent

        if tier_in not in _ent._TIER_ORDER:
            return (
                jsonify(
                    {"error": "unknown tier", "which": "tier", "tier": tier_in}
                ),
                404,
            )
        channels = _parse_csv_arg("channels")
        if not channels:
            return jsonify({"error": "supply channels=<csv>"}), 400
        if direction == "next":
            target = _ent._next_purchasable_tier_after(tier_in)
            batch = _ent.next_tier_channel_spec_at_batch(tier_in, channels)
        else:
            target = _ent._previous_purchasable_tier_before(tier_in)
            batch = _ent.previous_tier_channel_spec_at_batch(tier_in, channels)
        if batch is None:
            batch = {"channels": [], "unknown": []}
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": _ent.tier_label(tier_in),
                "tier_rank": _ent.tier_rank(tier_in),
                "target": target,
                "target_label": _ent.tier_label(target) if target else None,
                "target_rank": _ent.tier_rank(target) if target else None,
                "channels": batch.get("channels", []),
                "unknown": batch.get("unknown", []),
            }
        )
    except Exception as exc:
        logger.warning(
            "api_entitlement_%s_tier_channel_spec_at_batch: error: %s",
            direction,
            exc,
        )
        return jsonify(
            {
                "tier": tier_in,
                "tier_label": None,
                "tier_rank": -1,
                "target": None,
                "target_label": None,
                "target_rank": None,
                "channels": [],
                "unknown": [],
            }
        )

def _next_prev_lock_reason_batch_grace_body() -> dict:
    """Fallback envelope for the resolved-tier lock-reason batch routes.
    Shape mirrors the happy path (5-axis empty rows + tier / target
    echo) so a resolver failure never breaks a paywall matrix client-
    side."""
    return {
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "current_tier": "oss",
        "current_tier_label": "OSS",
        "current_tier_rank": 0,
        "target": None,
        "target_label": None,
        "target_rank": None,
        "grace": True,
        "enforced": False,
    }

def _next_prev_lock_reason_batch(direction: str):
    """Shared handler body for
    ``/api/entitlement/{next,previous}-tier-lock-reason-batch``.

    Current-relative sibling of the ``_next_prev_lock_reason_at_batch``
    handler -- takes no ``tier=`` (the source is the resolved
    entitlement) and walks
    :meth:`Entitlement.next_tier_lock_reason_batch` /
    :meth:`Entitlement.previous_tier_lock_reason_batch` instead of the
    source-parameterised ``_at_batch`` module helpers, matching the
    pattern of ``/next-tier-feature-spec-batch`` vs
    ``/next-tier-feature-spec-at-batch``.

    Mirrors the axis-parsing contract of the ``_at_batch`` handler (at
    least one of ``features=`` / ``runtimes=`` / ``channels=`` /
    ``retention_days=`` / ``nodes=``). Body is byte-identical to
    ``/lock-reasons-at-batch?tier=<target>&...`` for the resolved
    ``target = ent.next_purchasable_tier()`` (or
    ``previous_purchasable_tier()``), same as
    ``/next-tier-lock-reason-at-batch`` is byte-identical for
    caller-supplied ``tier``. ``target`` collapses to ``null`` at the
    rung edge (ceiling for ``next``, floor for ``previous``) while
    every supplied item still renders a grace-shape row so the paywall
    matrix's row count stays stable.

    ``direction`` is ``"next"`` or ``"previous"``. Never 5xxs: resolver
    failure short-circuits to the grace-shape envelope so the paywall
    surface stays mute.
    """
    log_name = f"api_entitlement_{direction}_tier_lock_reason_batch"
    try:
        from clawmetry import entitlements as _ent

        features = _parse_csv_arg("features")
        runtimes = _parse_csv_arg("runtimes")
        (_, channels_ok, channels_n, _) = _parse_capacity_arg("channels")
        (_, retention_ok, retention_n, _) = _parse_capacity_arg(
            "retention_days"
        )
        (_, nodes_ok, nodes_n, _) = _parse_capacity_arg("nodes")

        if (
            not features
            and not runtimes
            and not channels_ok
            and not retention_ok
            and not nodes_ok
        ):
            return (
                jsonify(
                    {
                        "error": (
                            "supply at least one of features=<csv>, "
                            "runtimes=<csv>, channels=<int>, "
                            "retention_days=<int>, or nodes=<int>"
                        )
                    }
                ),
                400,
            )

        ent = _ent.get_entitlement()
        if direction == "next":
            target = ent.next_purchasable_tier()
            batch = ent.next_tier_lock_reason_batch(
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        else:
            target = ent.previous_purchasable_tier()
            batch = ent.previous_tier_lock_reason_batch(
                features=features or None,
                runtimes=runtimes or None,
                channels=channels_n if channels_ok else None,
                retention_days=retention_n if retention_ok else None,
                nodes=nodes_n if nodes_ok else None,
            )
        if batch is None:
            batch = {
                "features": [],
                "runtimes": [],
                "channels": None,
                "retention_days": None,
                "nodes": None,
            }
        batch["current_tier"] = ent.tier
        batch["current_tier_label"] = _ent.tier_label(ent.tier)
        batch["current_tier_rank"] = _ent.tier_rank(ent.tier)
        batch["target"] = target
        batch["target_label"] = _ent.tier_label(target) if target else None
        batch["target_rank"] = _ent.tier_rank(target) if target else None
        batch["grace"] = bool(ent.grace)
        batch["enforced"] = _ent.is_enforced()
        return jsonify(batch)
    except Exception as exc:
        logger.warning("%s: error: %s", log_name, exc)
        return jsonify(_next_prev_lock_reason_batch_grace_body())

def _resolver_envelope(_ent) -> dict:
    ent = _ent.get_entitlement()
    return {
        "current_tier": ent.tier,
        "current_tier_rank": _ent.tier_rank(ent.tier),
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }

def _tiers_for_capacity_perval_fallback(kind: str) -> dict:
    """Grace-shape fallback body for the three per-value
    ``/tiers-for-<capacity-axis>-batch`` endpoints. Never 5xxs: on a
    resolver crash the pricing surface keeps rendering with an empty
    ``rows`` list instead of a stack trace. Envelope mirrors the happy-
    path body so a caller does not have to branch on the error shape.
    """
    return {
        "kind": kind,
        "count": 0,
        "rows": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _parse_tiers_for_capacity_batch_csv(name: str, unlimited_ok: bool):
    """Parse a comma-separated ``/tiers-for-<axis>-batch`` query arg.

    Empty / whitespace tokens are dropped. When ``unlimited_ok`` is
    True the case-insensitive string ``"unlimited"`` is emitted
    verbatim (the retention helper routes it to the ``None``
    sentinel); otherwise it passes through unmodified and collapses to
    the all-``None`` row shape via the helper's non-int branch. Non-
    int tokens on the two count axes pass through unmodified so
    :func:`clawmetry.entitlements._tiers_for_capacity_batch` yields
    the documented all-``None`` row for them.

    Returns ``(values, err)`` where ``err`` is ``None`` on success,
    ``"missing"`` when the arg is absent, blank, or contains only
    commas / whitespace (endpoint should 400). Never raises.
    """
    raw = request.args.get(name)
    if raw is None or not raw.strip():
        return [], "missing"
    out: list = []
    for token in raw.split(","):
        t = token.strip()
        if not t:
            continue
        if unlimited_ok and t.lower() == "unlimited":
            out.append("unlimited")
            continue
        out.append(t)
    if not out:
        return [], "missing"
    return out, None

def _tiers_for_capacity_perval_at_body(_ent, tier_in: str, kind: str, rows):
    """Assemble the response envelope for a
    ``tiers-for-<capacity-axis>-at-batch`` endpoint.

    Layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard per-value tiers-for
    batch envelope so a pricing-matrix walkthrough surface can render
    the "from <perspective>" copy off one round-trip, matching how
    ``/tiers-for-capacity-batch-at`` layers perspective onto the
    per-axis grant-axis batch. Never raises.
    """
    return {
        "kind": kind,
        "count": len(rows),
        "rows": rows,
        "perspective_tier": tier_in,
        "perspective_tier_label": _ent.tier_label(tier_in),
        "perspective_tier_rank": _ent.tier_rank(tier_in),
        **_resolver_envelope(_ent),
    }

def _tiers_for_capacity_perval_at_fallback(tier_in: str, kind: str) -> dict:
    """Grace-shape fallback body for the three per-value
    ``tiers-for-<capacity-axis>-at-batch`` endpoints. Same never-5xx
    posture as :func:`_tiers_for_capacity_perval_fallback` with the
    perspective envelope layered on so a caller can still render the
    "from <perspective>" copy with placeholders on a resolver crash.
    """
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
    except Exception:
        label = tier_in
        rank = 0
    return {
        "kind": kind,
        "count": 0,
        "rows": [],
        "perspective_tier": tier_in,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _perspective_envelope(_ent, p: str) -> dict:
    ent = _ent.get_entitlement()
    return {
        "perspective_tier": p,
        "perspective_tier_label": _ent.tier_label(p),
        "perspective_tier_rank": _ent.tier_rank(p),
        "current_tier": ent.tier,
        "current_tier_rank": _ent.tier_rank(ent.tier),
        "grace": bool(ent.grace),
        "enforced": _ent.is_enforced(),
    }

def _perspective_fallback(p: str) -> dict:
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(p)
        rank = _ent.tier_rank(p)
    except Exception:
        label = p
        rank = 0
    return {
        "perspective_tier": p,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _min_tier_for_capacity_fallback(item, kind: str) -> dict:
    """Grace-shape fallback body for the three ``min-tier-for-<capacity-axis>``
    endpoints. Never 5xxs: on a resolver crash the pricing surface keeps
    rendering with ``required_tier=null`` instead of a stack trace.
    """
    return {
        "item": item,
        "kind": kind,
        "label": None,
        "free": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _min_tier_for_capacity_body(
    _ent, item, kind: str, label: str, required
) -> dict:
    """Assemble the response body for a ``min-tier-for-<capacity-axis>``
    endpoint. Uniform ``required_tier*`` naming across the three capacity
    axes (channel_count, node_count, retention_window) so a paywall UI
    switching axes reads the same envelope, and byte-identical to the
    ``required_tier*`` naming the plural grant-axis siblings
    (``/min-tier-for-features`` / ``/min-tier-for-runtimes``) use.

    ``free`` is derived from the min-tier helper's own answer (matching
    the sibling ``/tiers-for-<axis>`` endpoint's ``free`` semantics for
    every currently-defined cap): if the cheapest admitting tier IS
    :data:`TIER_OSS`, the request fits in the free floor.
    """
    return {
        "item": item,
        "kind": kind,
        "label": label,
        "free": bool(required == _ent.TIER_OSS),
        "required_tier": required,
        "required_tier_label": (
            _ent.tier_label(required) if required else None
        ),
        "required_tier_rank": (
            _ent.tier_rank(required) if required else -1
        ),
        **_resolver_envelope(_ent),
    }

def _min_tier_for_capacity_at_body(
    _ent, tier_in: str, item, kind: str, label, required
) -> dict:
    """Assemble the response body for a ``min-tier-for-<capacity-axis>-at``
    endpoint. Layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard capacity body so a
    pricing-matrix walkthrough surface can render the "from <perspective>"
    copy off one round-trip, matching how ``/min-tier-for-features-at`` /
    ``/min-tier-for-runtimes-at`` layer perspective onto the grant-axis
    bodies. Never raises.
    """
    return {
        "item": item,
        "kind": kind,
        "label": label,
        "free": bool(required == _ent.TIER_OSS),
        "required_tier": required,
        "required_tier_label": (
            _ent.tier_label(required) if required else None
        ),
        "required_tier_rank": (
            _ent.tier_rank(required) if required else -1
        ),
        "perspective_tier": tier_in,
        "perspective_tier_label": _ent.tier_label(tier_in),
        "perspective_tier_rank": _ent.tier_rank(tier_in),
        **_resolver_envelope(_ent),
    }

def _min_tier_for_capacity_at_fallback(
    tier_in: str, item, kind: str
) -> dict:
    """Grace-shape fallback body for the three
    ``min-tier-for-<capacity-axis>-at`` endpoints. Same never-5xx posture
    as :func:`_min_tier_for_capacity_fallback` with the perspective envelope
    left null so a caller can still render the "from <perspective>" copy
    with placeholders on a resolver crash.
    """
    return {
        "item": item,
        "kind": kind,
        "label": None,
        "free": False,
        "required_tier": None,
        "required_tier_label": None,
        "required_tier_rank": -1,
        "perspective_tier": tier_in,
        "perspective_tier_label": None,
        "perspective_tier_rank": -1,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _capacity_batch_row_to_body(row: dict, endpoint_kind: str) -> dict:
    """Translate a :func:`min_tier_for_channel_count_batch` /
    :func:`min_tier_for_node_count_batch` /
    :func:`min_tier_for_retention_window_batch` helper row into the
    endpoint body row shape.

    Rekeys ``min_tier*`` -> ``required_tier*`` so each row is byte-
    identical to the bare singular endpoint body (minus the resolver
    envelope). Adds an ``item`` field (int on the two count axes;
    ``null`` on the unlimited retention row) and a human ``label``
    matching the singular endpoint's conjugation ("1 channel" /
    "5 channels" / "unlimited") so a UI can render each row through
    the existing singular-endpoint components without reshaping.

    ``endpoint_kind`` is one of ``"channel_count"`` / ``"node_count"``
    / ``"retention_window"`` (the singular endpoint's ``kind``, NOT
    the helper's ``kind``).

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape so the batch keeps building.
    """
    key = row.get("key")
    if endpoint_kind == "retention_window" and key == "unlimited":
        item: int | None = None
        label = "unlimited"
    else:
        try:
            item = int(key)
        except (TypeError, ValueError):
            item = None
            label = None
        else:
            if endpoint_kind == "channel_count":
                label = f"{item} channel" if item == 1 else f"{item} channels"
            elif endpoint_kind == "node_count":
                label = f"{item} node" if item == 1 else f"{item} nodes"
            else:
                label = f"{item} day" if item == 1 else f"{item} days"
    return {
        "item": item,
        "kind": endpoint_kind,
        "label": label,
        "free": bool(row.get("free")),
        "required_tier": row.get("min_tier"),
        "required_tier_label": row.get("min_tier_label"),
        "required_tier_rank": (
            row.get("min_tier_rank")
            if row.get("min_tier_rank") is not None
            else -1
        ),
    }

def _min_tier_for_capacity_batch_fallback(kind: str) -> dict:
    """Grace-shape fallback body for the three per-value
    ``min-tier-for-<capacity-axis>-batch`` endpoints. Never 5xxs: on a
    resolver crash the pricing surface keeps rendering with an empty
    ``rows`` list instead of a stack trace. Envelope mirrors the happy-
    path body so a caller does not have to branch on the error shape.
    """
    return {
        "kind": kind,
        "count": 0,
        "rows": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _parse_capacity_batch_csv(name: str, unlimited_ok: bool):
    """Parse a comma-separated capacity-batch query arg.

    Empty / whitespace tokens are dropped. Duplicates by normalised key
    are dropped preserving first-seen order so the response payload is
    stable. When ``unlimited_ok`` is True the case-insensitive string
    ``"unlimited"`` is emitted verbatim (the helper routes it to the
    None sentinel); otherwise it collapses to the all-``None`` row
    shape via passthrough. Non-int tokens on the two count axes pass
    through unmodified so :func:`_min_tier_for_capacity_batch` yields
    the documented all-``None`` row for them.

    Returns ``(values, err)`` where ``err`` is ``None`` on success,
    ``"missing"`` when the arg is absent or blank end-to-end (endpoint
    should 400). Never raises.
    """
    raw = request.args.get(name)
    if raw is None or not raw.strip():
        return [], "missing"
    out: list = []
    for token in raw.split(","):
        t = token.strip()
        if not t:
            continue
        if unlimited_ok and t.lower() == "unlimited":
            out.append("unlimited")
            continue
        out.append(t)
    if not out:
        return [], "missing"
    return out, None

def _min_tier_for_capacity_at_batch_body(_ent, tier_in: str, kind: str, rows):
    """Assemble the response envelope for a
    ``min-tier-for-<capacity-axis>-at-batch`` endpoint.

    Layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard capacity-batch
    envelope so a pricing-matrix walkthrough surface can render the
    "from <perspective>" copy off one round-trip, matching how
    ``/min-tier-for-features-at-batch`` layers perspective onto the
    grant-axis batches. Never raises.
    """
    return {
        "kind": kind,
        "count": len(rows),
        "rows": rows,
        "perspective_tier": tier_in,
        "perspective_tier_label": _ent.tier_label(tier_in),
        "perspective_tier_rank": _ent.tier_rank(tier_in),
        **_resolver_envelope(_ent),
    }

def _min_tier_for_capacity_at_batch_fallback(tier_in: str, kind: str) -> dict:
    """Grace-shape fallback body for the three
    ``min-tier-for-<capacity-axis>-at-batch`` endpoints. Same never-5xx
    posture as :func:`_min_tier_for_capacity_batch_fallback` with the
    perspective envelope layered on so a caller can still render the
    "from <perspective>" copy with placeholders on a resolver crash.
    """
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
    except Exception:
        label = tier_in
        rank = 0
    return {
        "kind": kind,
        "count": 0,
        "rows": [],
        "perspective_tier": tier_in,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _min_tier_for_bundle_row_to_body(row: dict, list_key: str) -> dict:
    """Rename the batch helper's ``min_tier*`` keys to the endpoint's
    ``required_tier*`` keys so per-row bodies stay byte-identical to
    the bare singular endpoint body (minus the resolver envelope). The
    helper's ``list_key`` selects whether the axis list is
    ``features`` or ``runtimes``. Never raises: a missing key surfaces
    as the empty-row shape.
    """
    return {
        list_key: list(row.get(list_key) or []),
        "unknown": list(row.get("unknown") or []),
        "kind": row.get("kind"),
        "count": int(row.get("count") or 0),
        "required_tier": row.get("min_tier"),
        "required_tier_label": row.get("min_tier_label"),
        "required_tier_rank": (
            row.get("min_tier_rank")
            if row.get("min_tier_rank") is not None
            else -1
        ),
        "free": bool(row.get("free")),
    }

def _parse_bundles_body(body, key: str = "bundles"):
    """Extract a list of bundles from a JSON POST body.

    Accepts ``{"bundles": [[...], [...]]}`` (canonical) plus a couple of
    tolerant shorthands so a mis-shaped caller does not hit a 500:

    * A single bundle (``{"bundles": ["fleet", "sso"]}``) is treated
      as ONE bundle rather than a list of scalars, matching how the
      singular endpoint reads a bare CSV.
    * ``None`` / missing ``bundles`` -- returns ``([], "missing")``
      so the caller can 400.
    * A non-list ``bundles`` value returns
      ``([], "bundles_must_be_list")``.

    Returns ``(bundles, err)`` where ``err`` is ``None`` on success.
    Never raises.
    """
    if not isinstance(body, dict):
        return [], "bundles_must_be_list"
    raw = body.get(key)
    if raw is None:
        return [], "missing"
    if not isinstance(raw, (list, tuple)):
        return [], "bundles_must_be_list"
    if not raw:
        return [], "empty"
    if all(isinstance(x, str) for x in raw):
        return [list(raw)], None
    out = []
    for bundle in raw:
        if bundle is None:
            out.append([])
            continue
        if isinstance(bundle, str):
            out.append([bundle])
            continue
        try:
            out.append(list(bundle))
        except TypeError:
            out.append([])
    return out, None

def _missing_bundle_row_body(row: dict, list_key: str) -> dict:
    """Row-body helper for the ``/missing-<axis>-bundle-batch`` endpoints.

    Row-detail sibling of :func:`_min_tier_for_bundle_row_to_body` on
    the boolean-fold slot's complement seat. Row schema mirrors the
    reverse-lookup helper on the axis-echo slots (``features`` /
    ``runtimes`` / ``unknown`` / ``kind`` / ``count``) with the
    ``min_tier*`` triple / ``free`` slots swapped for a single
    ``missing`` list matching the singular
    ``/api/entitlement/missing-features`` /
    ``/api/entitlement/missing-runtimes`` body's ``missing`` slot.

    Never raises: missing / non-list slots surface as the empty-row
    shape.
    """
    return {
        list_key: list(row.get(list_key) or []),
        "unknown": list(row.get("unknown") or []),
        "kind": row.get("kind"),
        "count": int(row.get("count") or 0),
        "missing": list(row.get("missing") or []),
    }

def _parse_aggregate_bundles_body(body, key: str = "bundles"):
    """Extract a list of aggregate 5-axis bundle dicts from a JSON POST body.

    Unlike :func:`_parse_bundles_body` (which expects list-of-list-of-
    strings for the single-axis feature / runtime bundle batches), each
    row here is a dict carrying up to five keys -- ``features``,
    ``runtimes``, ``channels``, ``retention_days``, ``nodes`` -- matching
    the ``/api/entitlement/required-tier-batch`` GET query args on a
    per-bundle basis. This is the parser for the aggregate
    ``/required-tier-bundle-batch`` family.

    Accepts::

        {"bundles": [
            {"features": ["fleet"], "runtimes": ["claude_code"]},
            {"channels": 5, "retention_days": 30},
            {}
        ]}

    Plus a single-bundle shorthand ``{"bundles": {"features": [...]}}``
    (a bare dict) so the caller does not have to wrap a single bundle in
    a list. Missing / non-list / non-dict-and-non-list values follow the
    same error posture as :func:`_parse_bundles_body`:

    * ``None`` / missing ``bundles`` -- ``([], "missing")``
    * scalar / non-list-non-dict -- ``([], "bundles_must_be_list")``
    * empty ``[]`` -- ``([], "empty")``

    Non-dict row entries (e.g. a bare list or scalar inside ``bundles``)
    collapse to an empty ``{}`` dict so the aggregate fold still emits a
    stable row rather than a 500 -- matches the never-crash posture of
    :func:`_parse_bundles_body`. Returns ``(bundles, err)`` with ``err``
    ``None`` on success.
    """
    if not isinstance(body, dict):
        return [], "bundles_must_be_list"
    raw = body.get(key)
    if raw is None:
        return [], "missing"
    if isinstance(raw, dict):
        return [dict(raw)], None
    if not isinstance(raw, (list, tuple)):
        return [], "bundles_must_be_list"
    if not raw:
        return [], "empty"
    out = []
    for bundle in raw:
        if isinstance(bundle, dict):
            out.append(dict(bundle))
        else:
            out.append({})
    return out, None

def _has_bundle_row_body(row: dict, list_key: str) -> dict:
    """Normalise a ``has_features_bundle_batch`` /
    ``has_runtimes_bundle_batch`` helper row for the endpoint response.

    Boolean-fold sibling of :func:`_min_tier_for_bundle_row_to_body`:
    same ``list_key`` / ``unknown`` / ``kind`` / ``count`` axes, but the
    tier slots are swapped for a single ``has_<axis>`` bool matching the
    fold-slot name on the singular ``/api/entitlement/has-features`` /
    ``/has-runtimes`` endpoint body. Never raises; a missing key
    surfaces as the empty-row shape with ``has_<axis>=False`` so the
    batch envelope is byte-stable across every branch.
    """
    fold_key = f"has_{list_key}"
    return {
        list_key: list(row.get(list_key) or []),
        "unknown": list(row.get("unknown") or []),
        "kind": row.get("kind"),
        "count": int(row.get("count") or 0),
        fold_key: bool(row.get(fold_key)),
    }

def _has_bundle_row_at_body(row: dict, list_key: str) -> dict:
    """Perspective-shaped sibling of :func:`_has_bundle_row_body`.

    Same ``list_key`` / ``unknown`` / ``kind`` / ``count`` axes, but the
    fold slot is renamed ``has_<axis>_at`` matching the singular scalar
    ``has_features_at`` / ``has_runtimes_at`` name on
    :func:`clawmetry.entitlements.has_features_bundle_batch_at` /
    :func:`clawmetry.entitlements.has_runtimes_bundle_batch_at`. Kept
    beside :func:`_has_bundle_row_body` so a future per-row envelope
    tweak (extra keys, coercion) has ONE obvious edit-site per family
    instead of drifting between the LIVE and the perspective endpoints.
    Never raises; a missing key surfaces as the empty-row shape with
    ``has_<axis>_at=False``.
    """
    fold_key = f"has_{list_key}_at"
    return {
        list_key: list(row.get(list_key) or []),
        "unknown": list(row.get("unknown") or []),
        "kind": row.get("kind"),
        "count": int(row.get("count") or 0),
        fold_key: bool(row.get(fold_key)),
    }

def _missing_bundle_row_at_body(row: dict, list_key: str) -> dict:
    """Row-body helper for the ``/missing-<axis>-bundle-batch-at`` endpoints.

    Perspective-shaped sibling of :func:`_missing_bundle_row_body` on the
    row-detail complement seat. Row schema mirrors the LIVE helper on the
    axis-echo slots (``<list_key>`` / ``unknown`` / ``kind`` / ``count``)
    with the fold slot renamed ``missing_<axis>_at`` matching the
    singular scalar ``missing_features_at`` / ``missing_runtimes_at`` name
    on :func:`clawmetry.entitlements.missing_features_bundle_batch_at` /
    :func:`clawmetry.entitlements.missing_runtimes_bundle_batch_at`. Kept
    beside :func:`_missing_bundle_row_body` so a future per-row envelope
    tweak (extra keys, coercion) has ONE obvious edit-site per family
    instead of drifting between the LIVE and the perspective endpoints.
    Never raises; a missing key surfaces as the empty-row shape with
    ``missing_<axis>_at=[]``.
    """
    fold_key = f"missing_{list_key}_at"
    return {
        list_key: list(row.get(list_key) or []),
        "unknown": list(row.get("unknown") or []),
        "kind": row.get("kind"),
        "count": int(row.get("count") or 0),
        fold_key: list(row.get(fold_key) or []),
    }

def _min_tier_for_all_row_to_body(row: dict) -> dict:
    """Rename the aggregate batch helper's ``required_tier*`` keys through
    unchanged (they already match the endpoint body), coerce the axis
    lists to lists, and default a missing rank to ``-1``.

    Kept alongside :func:`_min_tier_for_bundle_row_to_body` so future
    per-row envelope adjustments (extra keys, capacity coercion) have
    one obvious edit-site per family instead of drifting inside the
    endpoint bodies. Never raises: a missing key surfaces as the
    empty-row shape.
    """
    return {
        "features": list(row.get("features") or []),
        "runtimes": list(row.get("runtimes") or []),
        "channels": row.get("channels"),
        "retention_days": row.get("retention_days"),
        "nodes": row.get("nodes"),
        "required_tier": row.get("required_tier"),
        "required_tier_label": row.get("required_tier_label"),
        "required_tier_rank": (
            row.get("required_tier_rank")
            if row.get("required_tier_rank") is not None
            else -1
        ),
        "free": bool(row.get("free")),
    }

def _has_all_bundle_row_to_body(row: dict) -> dict:
    """Coerce the aggregate boolean-fold batch helper's per-row dict to
    a stable endpoint body shape: pass ``features`` / ``runtimes`` axis
    echoes through as lists, capacity axes through as int-or-``None``,
    and the ``has_all`` fold as a bool.

    Kept alongside :func:`_min_tier_for_all_row_to_body` so future per-
    row envelope adjustments (extra keys, capacity coercion) have one
    obvious edit-site per family instead of drifting inside the
    endpoint bodies. Never raises: a missing key surfaces as the
    empty-row shape.
    """
    return {
        "features": list(row.get("features") or []),
        "runtimes": list(row.get("runtimes") or []),
        "channels": row.get("channels"),
        "retention_days": row.get("retention_days"),
        "nodes": row.get("nodes"),
        "has_all": bool(row.get("has_all")),
    }

def _has_all_bundle_row_at_to_body(row: dict) -> dict:
    """Perspective-shaped sibling of :func:`_has_all_bundle_row_to_body`.

    Byte-identical to the LIVE row body except the fold slot is renamed
    ``has_all_at`` so a UI wiring both endpoints can distinguish the
    two answers on the same ``(bundle,)`` cell.
    """
    return {
        "features": list(row.get("features") or []),
        "runtimes": list(row.get("runtimes") or []),
        "channels": row.get("channels"),
        "retention_days": row.get("retention_days"),
        "nodes": row.get("nodes"),
        "has_all_at": bool(row.get("has_all_at")),
    }

def _parse_single_bundle_body(body, key: str = "bundle"):
    """Extract ONE aggregate 5-axis bundle dict from a JSON POST body.

    Singular sibling of :func:`_parse_aggregate_bundles_body` for the
    scalar ``/has-all-bundle`` / ``/has-all-bundle-at`` endpoints. Accepts
    either ``{"bundle": {"features": ["fleet"], ...}}`` (the wrapped
    form matching every other singular POST body in this module) or the
    bare-dict shorthand ``{"features": ["fleet"], ...}`` (so a caller
    can post the same body they would GET on ``/has-all`` as one dict
    without an outer wrapper).

    Returns ``(bundle, err)`` with ``err`` ``None`` on success, or one
    of:

    * ``bundle_must_be_object`` -- the top-level body is not a dict,
      OR ``body[key]`` is present but is not a dict.
    * ``missing`` -- neither ``body[key]`` nor a bare shorthand is
      present (i.e. body is ``{}`` or contains only unrelated keys).

    A blank ``body[key]={}`` (explicit empty bundle) is a valid input
    and returns ``({}, None)`` -- the fold layer collapses it to the
    stable empty row (``has_all=False``) matching the ``has_all`` empty
    posture.
    """
    if not isinstance(body, dict):
        return None, "bundle_must_be_object"
    if key in body:
        raw = body.get(key)
        if raw is None:
            return None, "missing"
        if not isinstance(raw, dict):
            return None, "bundle_must_be_object"
        return dict(raw), None
    # Shorthand: bare-dict body IS the bundle (matches /has-all GET args).
    known = ("features", "runtimes", "channels", "retention_days", "nodes")
    if any(axis in body for axis in known):
        return {axis: body[axis] for axis in known if axis in body}, None
    return None, "missing"

def _has_all_bundle_at_path_fallback(
    from_tier: str, to_tier: str
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-bundle-at-path``.

    Path-shaped bundle sibling of :func:`_has_all_at_path_fallback`
    (kwargs-shaped path). On any resolver / helper blowup the endpoint
    still returns 200 with the same envelope shape as the happy path,
    but ``path=[]`` and every fold rollup fail-closed (``allowed_count=0``
    / ``all_allowed=False`` / ``any_allowed=False``) so a pricing-page
    walkthrough that lost the resolver never silently renders a bundle
    grant it can't verify. ``direction`` collapses to ``"identity"``
    when ``from == to`` (matches the happy-path branch for that case)
    and ``"unknown"`` otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "path": [],
        "path_length": 0,
        "allowed_count": 0,
        "all_allowed": False,
        "any_allowed": False,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_bundle_at_path_fallback(
    from_tier: str, to_tier: str
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-bundle-at-path``.

    Row-detail path-shaped bundle sibling of
    :func:`_missing_all_at_path_fallback` (kwargs-shaped path) and
    row-detail complement of :func:`_has_all_bundle_at_path_fallback`.
    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path, but ``path=[]`` and
    every row-detail rollup fail-open (``denied_count=0`` /
    ``all_denied=False`` / ``any_denied=False``) so a pricing-page
    walkthrough that lost the resolver never silently renders a denial
    banner it can no longer justify. ``direction`` collapses to
    ``"identity"`` when ``from == to`` (matches the happy-path branch
    for that case) and ``"unknown"`` otherwise.
    """
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "path": [],
        "path_length": 0,
        "denied_count": 0,
        "all_denied": False,
        "any_denied": False,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_bundle_at_path_batch_fallback(
    from_tier: str, to_tokens: list
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-bundle-at-path-batch``.

    Bundle-shaped batch-path sibling of
    :func:`_has_all_at_path_batch_fallback` (kwargs-shaped batch-path)
    and destination-batch sibling of
    :func:`_has_all_bundle_at_path_fallback` (singular destination). On
    any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]`` so
    a pricing-comparison matrix that lost the resolver never silently
    renders a bundle grant it can't verify. Caller-supplied destination
    tokens echo into ``unknown_tiers`` for debugging.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_tiers": list(to_tokens),
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_bundle_at_path_batch_fallback(
    from_tier: str, to_tokens: list
) -> dict:
    """Never-5xx envelope for
    ``/api/entitlement/missing-all-bundle-at-path-batch``.

    Row-detail bundle-shaped batch-path sibling of
    :func:`_missing_all_at_path_batch_fallback` (kwargs-shaped batch-
    path) and destination-batch sibling of
    :func:`_missing_all_bundle_at_path_fallback` (singular destination).
    On any resolver / helper blowup the endpoint still returns 200 with
    the same envelope shape as the happy path but with ``tiers=[]`` so
    a pricing-comparison matrix that lost the resolver never silently
    renders a denial it can no longer justify. Mirrors
    :func:`_has_all_bundle_at_path_batch_fallback` byte-for-byte on the
    axis-echo slots so a UI wiring both boolean-fold and row-detail
    matrices off the same body-builder gets byte-stable envelopes
    across every input branch on both endpoints.
    """
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_tiers": list(to_tokens),
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_all_bundle_batch_at_path_fallback(
    from_tier: str, to_tier: str
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/has-all-bundle-batch-at-path``."""
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "bundles": [],
        "count": 0,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_bundle_batch_at_path_fallback(
    from_tier: str, to_tier: str
) -> dict:
    """Never-5xx envelope for ``/api/entitlement/missing-all-bundle-batch-at-path``."""
    direction = "identity" if from_tier and from_tier == to_tier else "unknown"
    return {
        "from": from_tier,
        "from_label": None,
        "from_rank": -1,
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "direction": direction,
        "bundles": [],
        "count": 0,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _bundle_batch_path_row_out(
    cell: dict, row_to_body, fold_key: str
) -> dict:
    """Coerce one per-bundle cell from has_all_bundle_batch_at_path /
    missing_all_bundle_batch_at_path to a stable endpoint body.
    """
    from clawmetry import entitlements as _ent

    path_in = cell.get("path") or []
    path_out: list[dict] = []
    for row in path_in:
        try:
            tid = row.get("tier")
        except AttributeError:
            continue
        path_out.append(
            {
                "tier": tid,
                "tier_label": row.get("tier_label", _ent.tier_label(tid)),
                "tier_rank": row.get("tier_rank", _ent.tier_rank(tid)),
                **row_to_body(row),
            }
        )
    body = {
        "bundle_index": int(cell.get("bundle_index") or 0),
        "features": list(cell.get("features") or []),
        "runtimes": list(cell.get("runtimes") or []),
        "channels": cell.get("channels"),
        "retention_days": cell.get("retention_days"),
        "nodes": cell.get("nodes"),
        "path": path_out,
        "path_length": len(path_out),
    }
    if fold_key == "has_all_at":
        allowed_count = sum(1 for r in path_out if r.get("has_all_at"))
        body["allowed_count"] = allowed_count
        body["all_allowed"] = bool(path_out) and all(
            r.get("has_all_at") for r in path_out
        )
        body["any_allowed"] = any(r.get("has_all_at") for r in path_out)
    else:
        denied_count = sum(
            1
            for r in path_out
            if any(
                v
                for v in (r.get("missing") or {}).values()
                if v not in (None, [])
            )
        )
        body["denied_count"] = denied_count
        body["all_denied"] = bool(path_out) and all(
            any(
                v
                for v in (r.get("missing") or {}).values()
                if v not in (None, [])
            )
            for r in path_out
        )
        body["any_denied"] = any(
            any(
                v
                for v in (r.get("missing") or {}).values()
                if v not in (None, [])
            )
            for r in path_out
        )
    return body

def _parse_from_tiers_bundle_body(body):
    """Extract ``(from_tiers_list, bundle_dict, err)`` from a POST body
    for the ``/has-all-bundle-from-path-batch`` /
    ``/missing-all-bundle-from-path-batch`` endpoints.

    Body shape (canonical)::

        {"from_tiers": ["oss", "cloud_starter"],
         "bundle": {"features": ["fleet"], "runtimes": ["claude_code"],
                    "channels": 5, "retention_days": 30, "nodes": 2}}

    Also accepts the bare-bundle shorthand where the top-level body
    carries the bundle axes inline alongside ``from_tiers`` (matches
    the ``_parse_single_bundle_body`` shorthand posture)::

        {"from_tiers": ["oss"], "features": ["fleet"], "runtimes": [...]}

    Returns ``(from_tiers, bundle, None)`` on success or one of:

    * ``bundle_must_be_object`` -- body is not a dict OR
      ``body["bundle"]`` is present but not a dict.
    * ``missing`` -- neither ``body["bundle"]`` nor a bare-axis
      shorthand is present.

    Missing / non-list ``from_tiers`` normalises to ``[]`` so a
    caller that forgot the key hits the empty-source branch (the
    scalar's happy-path posture on empty sources) instead of a 400.
    ``from_tiers`` may itself be a CSV string (matches
    ``/has-features-from-path-batch`` GET semantics for a POST
    caller stitching a CSV).
    """
    if not isinstance(body, dict):
        return [], None, "bundle_must_be_object"
    raw_from = body.get("from_tiers")
    if raw_from is None:
        from_tiers: list = []
    elif isinstance(raw_from, str):
        from_tiers = [tok.strip() for tok in raw_from.split(",") if tok.strip()]
    elif isinstance(raw_from, (list, tuple)):
        from_tiers = [str(x) for x in raw_from]
    else:
        from_tiers = []
    if "bundle" in body:
        raw_bundle = body.get("bundle")
        if raw_bundle is None:
            return from_tiers, None, "missing"
        if not isinstance(raw_bundle, dict):
            return from_tiers, None, "bundle_must_be_object"
        return from_tiers, dict(raw_bundle), None
    # Shorthand: bare-axis body IS the bundle alongside from_tiers.
    known = ("features", "runtimes", "channels", "retention_days", "nodes")
    if any(axis in body for axis in known):
        return (
            from_tiers,
            {axis: body[axis] for axis in known if axis in body},
            None,
        )
    return from_tiers, None, "missing"

def _has_all_bundle_from_path_batch_fallback(
    to_tier: str, from_tiers: list
) -> dict:
    """Never-5xx envelope for
    ``/api/entitlement/has-all-bundle-from-path-batch``.

    Source-axis batch bundle-shaped sibling of
    :func:`_has_all_bundle_at_path_fallback` (singular-path bundle)
    and bundle-shape twin of :func:`_has_bundle_from_path_batch_fallback`
    (source-batch kwargs). On any resolver / helper blowup the
    endpoint still returns 200 with the same envelope shape as the
    happy path but with ``tiers=[]`` / ``count=0`` / axis echoes empty
    so a source-side pricing surface that lost the resolver never
    silently renders a grant matrix it can't verify. ``to`` /
    ``unknown_tiers`` echo the caller's input so a debugging tooltip
    can still surface the dropped sources.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_tiers": list(from_tiers),
        "count": 0,
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_bundle_from_path_batch_fallback(
    to_tier: str, from_tiers: list
) -> dict:
    """Never-5xx envelope for
    ``/api/entitlement/missing-all-bundle-from-path-batch``.

    Row-detail complement of
    :func:`_has_all_bundle_from_path_batch_fallback`. Same envelope
    shape with the per-source rollups renamed for the missing seat:
    ``allowed_count`` / ``all_allowed`` / ``any_allowed`` become
    ``denied_count`` / ``all_denied`` / ``any_denied`` inside each
    ``tiers[]`` entry.
    """
    return {
        "to": to_tier,
        "to_label": None,
        "to_rank": -1,
        "features": [],
        "runtimes": [],
        "channels": None,
        "retention_days": None,
        "nodes": None,
        "unknown_tiers": list(from_tiers),
        "count": 0,
        "tiers": [],
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _missing_all_bundle_row_at_to_body(row: dict) -> dict:
    """Perspective-shaped row-body sibling of
    :func:`_has_all_bundle_row_at_to_body` for
    ``/api/entitlement/missing-all-bundle-batch-at``.

    Byte-identical to the boolean-fold ``_at`` row body on the axis-
    echo slots (``features`` / ``runtimes`` / ``channels`` /
    ``retention_days`` / ``nodes``) with the ``has_all_at`` bool
    swapped for a per-axis ``missing`` dict matching
    :func:`clawmetry.entitlements.missing_all_at`'s return shape.

    Kept alongside :func:`_has_all_bundle_row_at_to_body` and
    :func:`_has_all_bundle_row_to_body` so future per-row envelope
    adjustments have one obvious edit-site per family instead of
    drifting inside the endpoint bodies. Never raises: a missing key
    surfaces as the empty-row shape.
    """
    missing = row.get("missing") or {}
    if not isinstance(missing, dict):
        missing = {}
    return {
        "features": list(row.get("features") or []),
        "runtimes": list(row.get("runtimes") or []),
        "channels": row.get("channels"),
        "retention_days": row.get("retention_days"),
        "nodes": row.get("nodes"),
        "missing": {
            "features": list(missing.get("features") or []),
            "runtimes": list(missing.get("runtimes") or []),
            "channels": missing.get("channels"),
            "retention_days": missing.get("retention_days"),
            "nodes": missing.get("nodes"),
        },
    }

def _missing_all_bundle_row_to_body(row: dict) -> dict:
    """Row-body helper for ``/api/entitlement/missing-all-bundle-batch``.

    Row-detail sibling of :func:`_has_all_bundle_row_to_body` on the
    aggregate LIVE seat. Byte-identical on the axis-echo slots
    (``features`` / ``runtimes`` / ``channels`` / ``retention_days`` /
    ``nodes``) with the ``has_all`` bool swapped for a per-axis
    ``missing`` dict matching :func:`missing_all`'s return shape.

    Kept alongside :func:`_has_all_bundle_row_to_body` and
    :func:`_min_tier_for_all_row_to_body` so future per-row envelope
    adjustments have one obvious edit-site per family instead of
    drifting inside the endpoint bodies. Never raises: a missing key
    surfaces as the empty-row shape.
    """
    missing = row.get("missing") or {}
    if not isinstance(missing, dict):
        missing = {}
    return {
        "features": list(row.get("features") or []),
        "runtimes": list(row.get("runtimes") or []),
        "channels": row.get("channels"),
        "retention_days": row.get("retention_days"),
        "nodes": row.get("nodes"),
        "missing": {
            "features": list(missing.get("features") or []),
            "runtimes": list(missing.get("runtimes") or []),
            "channels": missing.get("channels"),
            "retention_days": missing.get("retention_days"),
            "nodes": missing.get("nodes"),
        },
    }

# ── /api/entitlement/runtime-detection ──────────────────────────────────────
# Presence-detect every supported runtime and decorate each row with the
# resolved entitlement view (allowed/locked + required_tier). Lets the
# dashboard render a single card answering "what's on this machine, what
# would unlock" without shell-scraping the CLI. Grace-mode compatible: rows
# always report the intrinsic locked-if-enforced picture so the paywall UI
# stays honest, and the ``allowed`` bit reflects only the entitlement's
# ``runtimes`` set -- the grace-vs-enforce toggle lives on the top-level
# ``grace`` / ``enforced`` fields for the UI to interpret.
#
# Response shape::
#
#     {
#       "current_tier": "oss",
#       "current_tier_label": "OSS",
#       "grace": true,
#       "enforced": false,
#       "probes": [
#         {"id": "openclaw", "label": "OpenClaw", "free": true,
#          "found": true, "allowed": true,
#          "required_tier": "oss", "required_tier_label": "OSS"},
#         {"id": "claude_code", "label": "Claude Code", "free": false,
#          "found": true, "allowed": false,
#          "required_tier": "cloud_starter",
#          "required_tier_label": "Cloud Starter"},
#         ...
#       ],
#       "counts": {
#         "total": 14,
#         "detected": 3,
#         "detected_free": 1,
#         "detected_locked": 2,
#         "unlocked": 2,
#         "locked": 12
#       },
#       "detected_locked": ["claude_code", "cursor"],
#       "actionable_tier": "cloud_starter",
#       "actionable_tier_label": "Cloud Starter"
#     }
#
# Read-only. Never raises: on any failure at any stage the endpoint returns
# a neutral empty envelope (``probes: []`` + zeroed counts) with the current
# tier the resolver could still supply.
_EMPTY_RUNTIME_DETECTION = {
    "current_tier": "oss",
    "current_tier_label": "OSS",
    "grace": True,
    "enforced": False,
    # Resolver unavailable => we do not know the plan. Never let an upsell
    # surface read this envelope as "confirmed free".
    "pending": True,
    "probes": [],
    "counts": {
        "total": 0,
        "detected": 0,
        "detected_free": 0,
        "detected_locked": 0,
        "unlocked": 0,
        "locked": 0,
    },
    "detected_locked": [],
    "actionable_tier": None,
    "actionable_tier_label": None,
}

def _runtime_detection_counts(probes: list) -> dict:
    """Aggregate row for ``/api/entitlement/runtime-detection``. Pure fn."""
    total = len(probes)
    detected = sum(1 for r in probes if r.get("found"))
    detected_free = sum(
        1 for r in probes if r.get("found") and r.get("free")
    )
    detected_locked = sum(
        1 for r in probes if r.get("found") and not r.get("allowed")
    )
    unlocked = sum(1 for r in probes if r.get("allowed"))
    locked = total - unlocked
    return {
        "total": total,
        "detected": detected,
        "detected_free": detected_free,
        "detected_locked": detected_locked,
        "unlocked": unlocked,
        "locked": locked,
    }

def _has_node_count_at_batch_row_to_body(row: dict, count_raw: str) -> dict:
    """Translate a :func:`has_node_count_at_batch` scalar row into the
    endpoint body row shape.

    Perspective-shaped batch sibling of
    :func:`_has_node_count_batch_row_to_body`. Rekeys ``has`` ->
    ``has_node_count_at`` / ``allowed`` (matches the singular
    ``/api/entitlement/has-node-count-at`` body), replaces the
    normalised-str ``key`` with an int ``count`` (or ``null`` on non-
    int input) plus the caller's raw ``count_raw`` echo, and layers a
    conjugated human ``label`` ("1 node" / "5 nodes") matching the
    sibling ``/min-tier-for-node-count-at-batch`` shape.

    Drops the ``upgrade_required`` bit that
    :func:`_has_node_count_batch_row_to_body` carries: this is the
    perspective-shaped ``_at`` slot, so "would tier X admit this?" is
    the row's whole point -- comparing that answer against the LIVE
    current-tier rank would double-count the perspective in the paywall
    matrix cell (matches the singular ``/has-node-count-at`` sibling,
    which omits ``upgrade_required`` for the same reason).

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape so the batch keeps building.
    """
    try:
        n = int(row.get("key"))
        count: int | None = n
        label = f"{n} node" if n == 1 else f"{n} nodes"
    except (TypeError, ValueError):
        count = None
        label = None
    req_rank = row.get("required_tier_rank")
    if req_rank is None:
        req_rank = -1
    has_flag = bool(row.get("has"))
    return {
        "count": count,
        "count_raw": count_raw,
        "kind": "node_count",
        "label": label,
        "has_node_count_at": has_flag,
        "allowed": has_flag,
        "unknown": bool(row.get("unknown")),
        "required_tier": row.get("required_tier"),
        "required_tier_label": row.get("required_tier_label"),
        "required_tier_rank": req_rank,
    }

def _has_node_count_at_batch_fallback(tier_in: str) -> dict:
    """Grace-shape fallback body for
    ``/api/entitlement/has-node-count-at-batch``. Sibling of
    :func:`_has_node_count_batch_fallback` with the perspective envelope
    layered on: on a resolver crash the pricing surface keeps rendering
    with an empty ``rows`` list instead of a stack trace, and the "from
    <perspective>" copy still has its placeholders.

    Never raises: any tier-metadata blowup falls back to the raw
    ``tier_in`` string and rank ``0``.
    """
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
    except Exception:
        label = tier_in
        rank = 0
    return {
        "kind": "node_count",
        "count": 0,
        "rows": [],
        "perspective_tier": tier_in,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }

def _has_capacity_at_batch_row_to_body(
    row: dict, raw_token: str, endpoint_kind: str, has_flag_key: str
) -> dict:
    """Translate a :func:`has_channel_count_at_batch` /
    :func:`has_retention_window_at_batch` scalar row into the endpoint
    body row shape.

    Perspective-shaped batch sibling of
    :func:`_has_node_count_batch_row_to_body`. Rekeys ``has`` ->
    ``has_<kind>_at`` / ``allowed`` (matches the singular
    ``/api/entitlement/has-<kind>-at`` body), replaces the normalised-
    str ``key`` with an int ``count`` / ``days`` (or ``null`` on the
    unlimited-retention row and on non-int input) plus the caller's
    raw echo, and layers a conjugated human ``label`` matching the
    sibling ``/min-tier-for-<kind>-at-batch`` shape. The unlimited-
    retention row carries ``unlimited=true`` / ``label="unlimited"``.

    Drops the ``upgrade_required`` bit that
    :func:`_has_node_count_batch_row_to_body` carries: this is the
    perspective-shaped ``_at`` slot, so "would tier X admit this?" is
    the row's whole point -- comparing that answer against the LIVE
    current-tier rank would double-count the perspective in the paywall
    matrix cell (matches the singular ``/has-<kind>-at`` sibling, which
    omits ``upgrade_required`` for the same reason).

    Never raises: missing keys / bad rows surface as the all-``None``
    row shape so the batch keeps building.
    """
    key = row.get("key")
    body: dict = {
        "kind": endpoint_kind,
    }
    if endpoint_kind == "retention_window":
        if key == "unlimited":
            body["days"] = None
            body["days_raw"] = raw_token
            body["unlimited"] = True
            body["label"] = "unlimited"
        else:
            try:
                n = int(key)
                body["days"] = n
                body["label"] = f"{n} day" if n == 1 else f"{n} days"
            except (TypeError, ValueError):
                body["days"] = None
                body["label"] = None
            body["days_raw"] = raw_token
            body["unlimited"] = False
    else:
        try:
            n = int(key)
            body["count"] = n
            body["label"] = f"{n} channel" if n == 1 else f"{n} channels"
        except (TypeError, ValueError):
            body["count"] = None
            body["label"] = None
        body["count_raw"] = raw_token
    has_flag = bool(row.get("has"))
    body[has_flag_key] = has_flag
    body["allowed"] = has_flag
    body["unknown"] = bool(row.get("unknown"))
    body["required_tier"] = row.get("required_tier")
    body["required_tier_label"] = row.get("required_tier_label")
    req_rank = row.get("required_tier_rank")
    body["required_tier_rank"] = -1 if req_rank is None else req_rank
    return body

def _has_capacity_at_batch_body(
    _ent, tier_in: str, endpoint_kind: str, rows: list
) -> dict:
    """Assemble the response envelope for a
    ``has-<capacity-axis>-at-batch`` endpoint.

    Layers ``perspective_tier`` / ``perspective_tier_label`` /
    ``perspective_tier_rank`` on top of the standard capacity-batch
    envelope so a pricing-matrix walkthrough surface can render the
    "from <perspective>" copy off one round-trip, matching how
    :func:`_min_tier_for_capacity_at_batch_body` layers perspective
    onto the reverse-lookup batches on the same axes. Never raises.
    """
    return {
        "kind": endpoint_kind,
        "count": len(rows),
        "rows": rows,
        "perspective_tier": tier_in,
        "perspective_tier_label": _ent.tier_label(tier_in),
        "perspective_tier_rank": _ent.tier_rank(tier_in),
        **_resolver_envelope(_ent),
    }

def _has_capacity_at_batch_fallback(tier_in: str, endpoint_kind: str) -> dict:
    """Grace-shape fallback body for the two
    ``has-<capacity-axis>-at-batch`` endpoints. Same never-5xx posture
    as :func:`_min_tier_for_capacity_at_batch_fallback` on the sibling
    reverse-lookup batches with the perspective envelope layered on so
    a caller can still render the "from <perspective>" copy with
    placeholders on a resolver crash.
    """
    try:
        from clawmetry import entitlements as _ent

        label = _ent.tier_label(tier_in)
        rank = _ent.tier_rank(tier_in)
    except Exception:
        label = tier_in
        rank = 0
    return {
        "kind": endpoint_kind,
        "count": 0,
        "rows": [],
        "perspective_tier": tier_in,
        "perspective_tier_label": label,
        "perspective_tier_rank": rank,
        "current_tier": "oss",
        "current_tier_rank": 0,
        "grace": True,
        "enforced": False,
    }
