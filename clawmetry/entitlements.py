"""
clawmetry/entitlements.py — open-core entitlement resolution.

Single source of truth for "what does this tier unlock?"  Used by the Flask
app (routes/entitlement.py), the CLI, and the sync daemon so every layer
enforces the same limits without duplicating tables.

Design goals
------------
* **No network I/O** – pure in-process logic; callers already hold whatever
  session / node data they need.
* **Additive** – adding a new feature gate never breaks existing callers;
  unknown keys are simply absent from the resolved dict.
* **Testable in isolation** – ``resolve(tier)`` is a pure function.

Tier hierarchy (lowest → highest)
----------------------------------
  free  <  cloud_starter  <  cloud_pro  <  cloud_teams  <  cloud_enterprise

The module also exposes four *directional scalar what-if* helpers that the
new ``/api/entitlement/next-tier-feature-spec-at`` &
``/api/entitlement/previous-tier-feature-spec-at`` endpoints (and their
``-runtime-`` siblings) delegate to:

  next_tier_feature_spec_at(current_tier, feature)     → dict | None
  previous_tier_feature_spec_at(current_tier, feature) → dict | None
  next_tier_runtime_spec_at(current_tier, runtime)     → dict | None
  previous_tier_runtime_spec_at(current_tier, runtime) → dict | None
"""

from __future__ import annotations

import logging
import os
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier ordering
# ---------------------------------------------------------------------------

TIER_ORDER: List[str] = [
    "free",
    "cloud_starter",
    "cloud_pro",
    "cloud_teams",
    "cloud_enterprise",
]

_TIER_INDEX: Dict[str, int] = {t: i for i, t in enumerate(TIER_ORDER)}


def tier_rank(tier: str) -> int:
    """Return the numeric rank of *tier* (0 = free).  Unknown tiers → -1."""
    return _TIER_INDEX.get(tier, -1)


def next_tier(tier: str) -> Optional[str]:
    """Return the tier immediately above *tier*, or ``None`` if already at top."""
    idx = _TIER_INDEX.get(tier, -1)
    if idx < 0 or idx >= len(TIER_ORDER) - 1:
        return None
    return TIER_ORDER[idx + 1]


def previous_tier(tier: str) -> Optional[str]:
    """Return the tier immediately below *tier*, or ``None`` if already at bottom."""
    idx = _TIER_INDEX.get(tier, -1)
    if idx <= 0:
        return None
    return TIER_ORDER[idx - 1]


# ---------------------------------------------------------------------------
# Feature catalogue
# ---------------------------------------------------------------------------
# Each entry is keyed by *feature name* and holds per-tier specs.
# A tier that doesn't appear in a feature's table inherits the nearest lower
# tier that *does* appear (or the feature is unavailable).
#
# Spec fields are intentionally open-ended so callers can surface whatever
# the frontend needs without a schema migration.

_FEATURE_SPECS: Dict[str, Dict[str, Dict[str, Any]]] = {
    # --- session retention -------------------------------------------------
    "session_retention_days": {
        "free": {"limit": 7, "unit": "days"},
        "cloud_starter": {"limit": 30, "unit": "days"},
        "cloud_pro": {"limit": 90, "unit": "days"},
        "cloud_teams": {"limit": 365, "unit": "days"},
        "cloud_enterprise": {"limit": None, "unit": "days", "note": "unlimited"},
    },
    # --- seats / members ---------------------------------------------------
    "seats": {
        "free": {"limit": 1},
        "cloud_starter": {"limit": 3},
        "cloud_pro": {"limit": 10},
        "cloud_teams": {"limit": 50},
        "cloud_enterprise": {"limit": None, "note": "unlimited"},
    },
    # --- nodes (machines) --------------------------------------------------
    "nodes": {
        "free": {"limit": 1},
        "cloud_starter": {"limit": 3},
        "cloud_pro": {"limit": 10},
        "cloud_teams": {"limit": 50},
        "cloud_enterprise": {"limit": None, "note": "unlimited"},
    },
    # --- alert rules -------------------------------------------------------
    "alert_rules": {
        "free": {"limit": 3},
        "cloud_starter": {"limit": 10},
        "cloud_pro": {"limit": 50},
        "cloud_teams": {"limit": 200},
        "cloud_enterprise": {"limit": None, "note": "unlimited"},
    },
    # --- data export -------------------------------------------------------
    "data_export": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": True, "formats": ["csv"]},
        "cloud_pro": {"enabled": True, "formats": ["csv", "json", "parquet"]},
        "cloud_teams": {"enabled": True, "formats": ["csv", "json", "parquet", "arrow"]},
        "cloud_enterprise": {
            "enabled": True,
            "formats": ["csv", "json", "parquet", "arrow", "delta"],
        },
    },
    # --- SSO / SAML --------------------------------------------------------
    "sso": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": False},
        "cloud_pro": {"enabled": False},
        "cloud_teams": {"enabled": True, "protocols": ["oidc"]},
        "cloud_enterprise": {"enabled": True, "protocols": ["oidc", "saml"]},
    },
    # --- audit log ---------------------------------------------------------
    "audit_log": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": False},
        "cloud_pro": {"enabled": True, "retention_days": 30},
        "cloud_teams": {"enabled": True, "retention_days": 90},
        "cloud_enterprise": {"enabled": True, "retention_days": None, "note": "unlimited"},
    },
    # --- custom webhooks ---------------------------------------------------
    "webhooks": {
        "free": {"limit": 0},
        "cloud_starter": {"limit": 2},
        "cloud_pro": {"limit": 10},
        "cloud_teams": {"limit": 50},
        "cloud_enterprise": {"limit": None, "note": "unlimited"},
    },
    # --- API rate limit (requests/minute) ----------------------------------
    "api_rate_limit": {
        "free": {"rpm": 60},
        "cloud_starter": {"rpm": 300},
        "cloud_pro": {"rpm": 1_000},
        "cloud_teams": {"rpm": 5_000},
        "cloud_enterprise": {"rpm": None, "note": "unlimited"},
    },
    # --- OTLP ingest -------------------------------------------------------
    "otlp_ingest": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": True, "sources": ["metrics"]},
        "cloud_pro": {"enabled": True, "sources": ["metrics", "traces"]},
        "cloud_teams": {"enabled": True, "sources": ["metrics", "traces", "logs"]},
        "cloud_enterprise": {
            "enabled": True,
            "sources": ["metrics", "traces", "logs"],
            "custom_endpoints": True,
        },
    },
    # --- multi-region storage ----------------------------------------------
    "multi_region": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": False},
        "cloud_pro": {"enabled": False},
        "cloud_teams": {"enabled": True},
        "cloud_enterprise": {"enabled": True, "regions": "any"},
    },
    # --- priority support --------------------------------------------------
    "priority_support": {
        "free": {"sla_hours": None},
        "cloud_starter": {"sla_hours": 48},
        "cloud_pro": {"sla_hours": 24},
        "cloud_teams": {"sla_hours": 8},
        "cloud_enterprise": {"sla_hours": 1, "dedicated_csm": True},
    },
    # --- cost anomaly detection -------------------------------------------
    "cost_anomaly_detection": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": True, "sensitivity": "low"},
        "cloud_pro": {"enabled": True, "sensitivity": "medium"},
        "cloud_teams": {"enabled": True, "sensitivity": "high"},
        "cloud_enterprise": {"enabled": True, "sensitivity": "custom"},
    },
    # --- brain stream (SSE) -----------------------------------------------
    "brain_stream": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": True, "history_events": 100},
        "cloud_pro": {"enabled": True, "history_events": 1_000},
        "cloud_teams": {"enabled": True, "history_events": 10_000},
        "cloud_enterprise": {"enabled": True, "history_events": None, "note": "unlimited"},
    },
    # --- fleet view -------------------------------------------------------
    "fleet_view": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": False},
        "cloud_pro": {"enabled": True},
        "cloud_teams": {"enabled": True},
        "cloud_enterprise": {"enabled": True, "cross_region": True},
    },
    # --- budget enforcement proxy -----------------------------------------
    "budget_proxy": {
        "free": {"enabled": False},
        "cloud_starter": {"enabled": True, "actions": ["alert"]},
        "cloud_pro": {"enabled": True, "actions": ["alert", "throttle"]},
        "cloud_teams": {"enabled": True, "actions": ["alert", "throttle", "block"]},
        "cloud_enterprise": {
            "enabled": True,
            "actions": ["alert", "throttle", "block", "custom"],
        },
    },
}

# ---------------------------------------------------------------------------
# Runtime catalogue
# ---------------------------------------------------------------------------
# Runtime = the execution environment the agent runs in.  Different runtimes
# unlock different capabilities / integrations.

_RUNTIME_SPECS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "local": {
        "free": {"supported": True, "max_concurrent_agents": 1},
        "cloud_starter": {"supported": True, "max_concurrent_agents": 3},
        "cloud_pro": {"supported": True, "max_concurrent_agents": 10},
        "cloud_teams": {"supported": True, "max_concurrent_agents": 50},
        "cloud_enterprise": {"supported": True, "max_concurrent_agents": None},
    },
    "docker": {
        "free": {"supported": False},
        "cloud_starter": {"supported": True, "images": ["python", "node"]},
        "cloud_pro": {
            "supported": True,
            "images": ["python", "node", "rust", "go"],
            "custom_images": False,
        },
        "cloud_teams": {
            "supported": True,
            "images": "any",
            "custom_images": True,
            "registry": "ghcr",
        },
        "cloud_enterprise": {
            "supported": True,
            "images": "any",
            "custom_images": True,
            "registry": "any",
        },
    },
    "kubernetes": {
        "free": {"supported": False},
        "cloud_starter": {"supported": False},
        "cloud_pro": {"supported": False},
        "cloud_teams": {"supported": True, "namespaces": 1},
        "cloud_enterprise": {"supported": True, "namespaces": None, "note": "unlimited"},
    },
    "aws_lambda": {
        "free": {"supported": False},
        "cloud_starter": {"supported": False},
        "cloud_pro": {"supported": True, "regions": ["us-east-1", "eu-west-1"]},
        "cloud_teams": {"supported": True, "regions": "any"},
        "cloud_enterprise": {"supported": True, "regions": "any", "vpc": True},
    },
    "gcp_cloudrun": {
        "free": {"supported": False},
        "cloud_starter": {"supported": False},
        "cloud_pro": {"supported": True, "regions": ["us-central1", "europe-west1"]},
        "cloud_teams": {"supported": True, "regions": "any"},
        "cloud_enterprise": {"supported": True, "regions": "any", "vpc": True},
    },
    "azure_functions": {
        "free": {"supported": False},
        "cloud_starter": {"supported": False},
        "cloud_pro": {"supported": False},
        "cloud_teams": {"supported": True},
        "cloud_enterprise": {"supported": True, "private_endpoints": True},
    },
    "bare_metal": {
        "free": {"supported": False},
        "cloud_starter": {"supported": False},
        "cloud_pro": {"supported": False},
        "cloud_teams": {"supported": False},
        "cloud_enterprise": {"supported": True},
    },
}

# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------


@lru_cache(maxsize=128)
def _resolve_spec_for_tier(
    catalogue: str,  # "feature" | "runtime"
    name: str,
    tier: str,
) -> Optional[Dict[str, Any]]:
    """
    Resolve the spec for *name* at *tier*, walking down the tier ladder until
    a match is found.  Returns ``None`` if *name* is unknown or unavailable
    at any tier up to and including *tier*.
    """
    table = _FEATURE_SPECS if catalogue == "feature" else _RUNTIME_SPECS
    spec_map = table.get(name)
    if spec_map is None:
        return None

    idx = _TIER_INDEX.get(tier, -1)
    if idx < 0:
        return None

    # Walk from current tier downward until we find an entry.
    for rank in range(idx, -1, -1):
        t = TIER_ORDER[rank]
        if t in spec_map:
            return {"tier": t, "rank": rank, **spec_map[t]}

    return None


def resolve(tier: str) -> Dict[str, Any]:
    """
    Return the *full* entitlement dict for *tier*.

    The returned dict has two top-level keys:

    ``features``
        Mapping of feature-name → resolved spec dict (with injected ``tier``
        and ``rank`` fields showing which tier's row was used).

    ``runtimes``
        Same structure for runtime specs.
    """
    features: Dict[str, Any] = {}
    for name in _FEATURE_SPECS:
        spec = _resolve_spec_for_tier("feature", name, tier)
        if spec is not None:
            features[name] = spec

    runtimes: Dict[str, Any] = {}
    for name in _RUNTIME_SPECS:
        spec = _resolve_spec_for_tier("runtime", name, tier)
        if spec is not None:
            runtimes[name] = spec

    return {
        "tier": tier,
        "rank": _TIER_INDEX.get(tier, -1),
        "features": features,
        "runtimes": runtimes,
    }


# ---------------------------------------------------------------------------
# Directional scalar what-if helpers  (NEW — resolves #3385 conflict)
# ---------------------------------------------------------------------------
# These four helpers are the canonical implementation consumed by
# routes/entitlement.py for the four new endpoints.


def next_tier_feature_spec_at(
    current_tier: str,
    feature: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the feature spec that would apply at the *next* tier above
    *current_tier*, or ``None`` if already at the top tier or the feature
    is unknown.

    The returned dict includes ``next_tier`` and ``next_tier_rank`` keys in
    addition to the spec fields so callers can surface upgrade prompts.
    """
    nt = next_tier(current_tier)
    if nt is None:
        return None
    spec = _resolve_spec_for_tier("feature", feature, nt)
    if spec is None:
        return None
    return {
        "current_tier": current_tier,
        "next_tier": nt,
        "next_tier_rank": _TIER_INDEX[nt],
        "feature": feature,
        **spec,
    }


def previous_tier_feature_spec_at(
    current_tier: str,
    feature: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the feature spec that would apply at the *previous* tier below
    *current_tier*, or ``None`` if already at the bottom tier or the feature
    is unknown.

    Useful for downgrade-impact analysis.
    """
    pt = previous_tier(current_tier)
    if pt is None:
        return None
    spec = _resolve_spec_for_tier("feature", feature, pt)
    if spec is None:
        return None
    return {
        "current_tier": current_tier,
        "previous_tier": pt,
        "previous_tier_rank": _TIER_INDEX[pt],
        "feature": feature,
        **spec,
    }


def next_tier_runtime_spec_at(
    current_tier: str,
    runtime: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the runtime spec that would apply at the *next* tier above
    *current_tier*, or ``None`` if already at the top tier or the runtime
    is unknown.
    """
    nt = next_tier(current_tier)
    if nt is None:
        return None
    spec = _resolve_spec_for_tier("runtime", runtime, nt)
    if spec is None:
        return None
    return {
        "current_tier": current_tier,
        "next_tier": nt,
        "next_tier_rank": _TIER_INDEX[nt],
        "runtime": runtime,
        **spec,
    }


def previous_tier_runtime_spec_at(
    current_tier: str,
    runtime: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the runtime spec that would apply at the *previous* tier below
    *current_tier*, or ``None`` if already at the bottom tier or the runtime
    is unknown.

    Useful for downgrade-impact analysis.
    """
    pt = previous_tier(current_tier)
    if pt is None:
        return None
    spec = _resolve_spec_for_tier("runtime", runtime, pt)
    if spec is None:
        return None
    return {
        "current_tier": current_tier,
        "previous_tier": pt,
        "previous_tier_rank": _TIER_INDEX[pt],
        "runtime": runtime,
        **spec,
    }


# ---------------------------------------------------------------------------
# Convenience accessors
# ---------------------------------------------------------------------------


def feature_spec(tier: str, feature: str) -> Optional[Dict[str, Any]]:
    """Shorthand: resolve a single feature for *tier*."""
    return _resolve_spec_for_tier("feature", feature, tier)


def runtime_spec(tier: str, runtime: str) -> Optional[Dict[str, Any]]:
    """Shorthand: resolve a single runtime for *tier*."""
    return _resolve_spec_for_tier("runtime", runtime, tier)


def feature_names() -> List[str]:
    """Sorted list of all known feature names."""
    return sorted(_FEATURE_SPECS.keys())


def runtime_names() -> List[str]:
    """Sorted list of all known runtime names."""
    return sorted(_RUNTIME_SPECS.keys())


# ---------------------------------------------------------------------------
# Lock-reason helper (filesystem-backed, optional)
# ---------------------------------------------------------------------------
# Some deployments write a lock-reason file when a node is suspended; this
# helper surfaces it without crashing if the file is absent.

_lock_reason_lock = threading.Lock()


def lock_reason_for_node(node_id: str, workspace: Optional[str] = None) -> Optional[str]:
    """
    Read the lock reason for *node_id* from the workspace filesystem, or
    return ``None`` if no lock file exists or the workspace is unavailable.
    """
    if workspace is None:
        workspace = os.environ.get("OPENCLAW_HOME", os.path.expanduser("~/.openclaw"))
    try:
        lock_path = Path(workspace) / "nodes" / node_id / "lock_reason"
        with _lock_reason_lock:
            if lock_path.exists():
                return lock_path.read_text(encoding="utf-8").strip() or None
    except Exception as exc:  # pragma: no cover
        logger.warning("entitlements: lock_reason_path failed: %s", exc)
    return None
