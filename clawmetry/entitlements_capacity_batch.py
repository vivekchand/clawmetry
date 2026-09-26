"""
clawmetry/entitlements_capacity_batch.py — has_capacity_batch + has_capacity_batch_at.

Short module extracted so Drift Bot can read the public API at the head of
entitlements.py via the re-export there. Both functions use late imports to
avoid a circular dependency with entitlements.py. Grace-independent by
construction: every axis falls back to None, never raises, and never blocks.

Re-exported from clawmetry.entitlements as part of the public surface.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("clawmetry.entitlements")


def has_capacity_batch(
    *,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> dict:
    """Per-axis boolean grants for every supplied capacity axis in one pass.

    Boolean-gate twin of :func:`~clawmetry.entitlements.tiers_for_capacity_batch`
    on the three capacity axes.  Delegates per-axis to
    :func:`~clawmetry.entitlements.has_channel_count` /
    :func:`~clawmetry.entitlements.has_retention_window` /
    :func:`~clawmetry.entitlements.has_node_count`.

    ``retention_days=None`` means *unset* -- NOT *unlimited* (matches
    ``tiers_for_capacity_batch`` on the same axis). Never raises.

    Envelope shape::

        {
          "channels":       <bool> | None,
          "retention_days": <bool> | None,
          "nodes":          <bool> | None,
        }
    """
    try:
        from clawmetry import entitlements as _ent

        return {
            "channels": (
                _ent.has_channel_count(channels)
                if channels is not None
                else None
            ),
            "retention_days": (
                _ent.has_retention_window(retention_days)
                if retention_days is not None
                else None
            ),
            "nodes": (
                _ent.has_node_count(nodes)
                if nodes is not None
                else None
            ),
        }
    except Exception as exc:
        logger.warning(
            "entitlements: has_capacity_batch failed: %s", exc
        )
        return {
            "channels": None,
            "retention_days": None,
            "nodes": None,
        }


def has_capacity_batch_at(
    perspective_tier: str,
    *,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> dict | None:
    """Hypothetical-perspective sibling of :func:`has_capacity_batch`.

    Per-axis boolean grants for every supplied capacity axis, scoped by a
    caller-supplied ``perspective_tier``.  Delegates per-axis to
    :func:`~clawmetry.entitlements.has_channel_count_at` /
    :func:`~clawmetry.entitlements.has_retention_window_at` /
    :func:`~clawmetry.entitlements.has_node_count_at`.

    Returns ``None`` for empty / unknown ``perspective_tier`` (caller renders
    "unknown tier" / 404).  ``retention_days=None`` means *unset*, NOT
    *unlimited*.  Grace-independent by construction.  Never raises.

    Envelope shape mirrors :func:`has_capacity_batch` exactly.
    """
    try:
        p = (perspective_tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not p:
        return None
    try:
        from clawmetry import entitlements as _ent

        if p not in _ent._TIER_ORDER:
            return None
        return {
            "channels": (
                _ent.has_channel_count_at(p, channels)
                if channels is not None
                else None
            ),
            "retention_days": (
                _ent.has_retention_window_at(p, retention_days)
                if retention_days is not None
                else None
            ),
            "nodes": (
                _ent.has_node_count_at(p, nodes)
                if nodes is not None
                else None
            ),
        }
    except Exception as exc:
        logger.warning(
            "entitlements: has_capacity_batch_at failed: %s", exc
        )
        return {
            "channels": None,
            "retention_days": None,
            "nodes": None,
        }
