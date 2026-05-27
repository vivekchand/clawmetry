"""
clawmetry/entitlements.py — open-core entitlement resolution.

Single source of truth for "what is this install allowed to do". Everything
that gates a runtime or an advanced feature reads :func:`get_entitlement` —
nothing should gate on a hardcoded plan check scattered across routes.

Open-core model
---------------
* **FREE** (this OSS package): the OpenClaw runtime + NeMo governance + the
  core observability surface. Always available — no key, no network call.
* **PAID** (the closed-source ``clawmetry-pro`` package, fetched only with
  a valid license key or a cloud entitlement — it is *not* shipped in this
  repo): the other agent runtimes (Claude Code, Codex, Cursor, …), the
  advanced features (custom alerts, multi-node fleet, anomaly detection, …),
  and paid CLI capabilities.

  NeMo is a *governance feature*, not an agent runtime, so it stays FREE.
  The free runtime set is therefore ``{"openclaw"}``.

Resolution order (first hit wins), all cached
---------------------------------------------
1. A local signed license file (``~/.clawmetry/license.key``)  -> self-hosted Pro/Enterprise
2. A cloud plan cached from the last heartbeat                  -> cloud Free/Starter/Pro/Trial
3. else                                                         -> OSS free

Both (1) and (2) are stubs in this phase — (1) lands with the Ed25519 license
client, (2) when the daemon caches the heartbeat plan. Today this always
resolves to the OSS-free entitlement.

Rollout: GRACE vs ENFORCE
-------------------------
Until the announced enforce date this resolver runs in **GRACE** mode:
``Entitlement.grace`` is ``True`` and every ``allows_*`` check returns ``True``,
so wiring this in changes **no current behaviour** — the gate is present but
inert. Set ``CLAWMETRY_ENFORCE=1`` to turn enforcement on (the enforce-phase
release flips the default). The module never raises: any error falls back to
the OSS-free entitlement and logs a warning.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from dataclasses import dataclass, field

logger = logging.getLogger("clawmetry.entitlements")

# ── Tier identifiers ────────────────────────────────────────────────────────
TIER_OSS = "oss"
TIER_CLOUD_FREE = "cloud_free"
TIER_TRIAL = "trial"
TIER_CLOUD_STARTER = "cloud_starter"
TIER_CLOUD_PRO = "cloud_pro"
TIER_PRO = "pro"  # self-hosted Pro (license key)
TIER_ENTERPRISE = "enterprise"

# Tiers that unlock the paid (closed-source) layer.
_PAID_TIERS = frozenset(
    {TIER_TRIAL, TIER_CLOUD_STARTER, TIER_CLOUD_PRO, TIER_PRO, TIER_ENTERPRISE}
)

# ── Runtime catalogue ───────────────────────────────────────────────────────
# FREE: the OpenClaw runtime only. NeMo is governance, not a runtime.
FREE_RUNTIMES = frozenset({"openclaw"})

# PAID: every other agent runtime ClawMetry can observe. These ship in the
# closed-source ``clawmetry-pro`` package, not here — listed so the UI can
# render locked rows + an upgrade CTA, and so the gate has a known universe.
PAID_RUNTIMES = frozenset(
    {
        "claude_code",
        "codex",
        "cursor",
        "aider",
        "goose",
        "opencode",
        "qwen_code",
        "hermes",
        "picoclaw",
        "nanoclaw",
    }
)

ALL_RUNTIMES = FREE_RUNTIMES | PAID_RUNTIMES

# ── Feature catalogue ───────────────────────────────────────────────────────
# Core observability — always free. Keys are stable identifiers the route /
# UI layer checks via Entitlement.allows_feature(...).
FREE_FEATURES = frozenset(
    {
        "sessions",
        "transcripts",
        "usage",
        "brain",
        "flow",
        "tracing",
        "health",
        "logs",
        "crons",
        "channels",
        "nemo_governance",
        "overview",
    }
)

# Advanced features — part of the paid layer.
PAID_FEATURES = frozenset(
    {
        "multi_runtime",
        "custom_alerts",
        "alert_webhooks",
        "fleet",
        "anomaly_detection",
        "self_evolve",
        "cost_optimizer",
    }
)

# Enterprise-only features (a strict superset on top of paid).
ENTERPRISE_FEATURES = frozenset(
    {
        "otel_export",
        "sso",
        "audit_logs",
        "rbac",
        "air_gapped_license",
    }
)

ALL_FEATURES = FREE_FEATURES | PAID_FEATURES | ENTERPRISE_FEATURES

# Per-tier paid feature grants (free features are always included on top).
_TIER_FEATURES = {
    TIER_OSS: frozenset(),
    TIER_CLOUD_FREE: frozenset(),
    TIER_TRIAL: PAID_FEATURES,
    TIER_CLOUD_STARTER: PAID_FEATURES - {"self_evolve"},
    TIER_CLOUD_PRO: PAID_FEATURES,
    TIER_PRO: PAID_FEATURES,
    TIER_ENTERPRISE: PAID_FEATURES | ENTERPRISE_FEATURES,
}

# Tiers that unlock the paid runtimes.
_TIER_PAID_RUNTIMES = _PAID_TIERS

_LICENSE_PATH = os.path.expanduser("~/.clawmetry/license.key")
_CLOUD_PLAN_CACHE = os.path.expanduser("~/.clawmetry/cloud_plan.json")
_ENFORCE_ENABLE_VALUES = frozenset({"1", "true", "yes", "on"})
_CACHE_TTL_SECS = 60.0


def is_enforced() -> bool:
    """True when the paywall is live. Default OFF (grace) until the enforce
    release flips it. ``CLAWMETRY_ENFORCE=1`` (1/true/yes/on) turns it on."""
    return (
        os.environ.get("CLAWMETRY_ENFORCE", "").strip().lower()
        in _ENFORCE_ENABLE_VALUES
    )


@dataclass(frozen=True)
class Entitlement:
    """Resolved entitlement for this install. Immutable; rebuild via
    :func:`get_entitlement`."""

    tier: str = TIER_OSS
    source: str = "oss"  # "license" | "cloud" | "oss"
    node_limit: int = 1
    expiry: float | None = None  # epoch seconds; None = perpetual (OSS)
    features: frozenset = field(default_factory=lambda: FREE_FEATURES)
    runtimes: frozenset = field(default_factory=lambda: FREE_RUNTIMES)
    grace: bool = True

    @property
    def is_paid(self) -> bool:
        return self.tier in _PAID_TIERS

    @property
    def expired(self) -> bool:
        return self.expiry is not None and time.time() > self.expiry

    def allows_runtime(self, runtime: str) -> bool:
        """Whether ``runtime`` may be observed. In grace mode everything is
        allowed; otherwise free runtimes plus whatever the tier grants."""
        if self.grace:
            return True
        rt = (runtime or "").lower()
        if rt in FREE_RUNTIMES:
            return True
        if self.expired:
            return False
        return rt in self.runtimes

    def allows_feature(self, feature: str) -> bool:
        """Whether ``feature`` is unlocked. Grace mode allows everything."""
        if self.grace:
            return True
        if feature in FREE_FEATURES:
            return True
        if self.expired:
            return False
        return feature in self.features

    def to_dict(self) -> dict:
        return {
            "tier": self.tier,
            "source": self.source,
            "node_limit": self.node_limit,
            "expiry": self.expiry,
            "expired": self.expired,
            "is_paid": self.is_paid,
            "grace": self.grace,
            "enforced": not self.grace,
            "runtimes": sorted(self.runtimes),
            "features": sorted(self.features),
            "free_runtimes": sorted(FREE_RUNTIMES),
            "paid_runtimes": sorted(PAID_RUNTIMES),
            "all_runtimes": sorted(ALL_RUNTIMES),
        }


def _build(tier: str, source: str, node_limit: int = 1, expiry: float | None = None) -> Entitlement:
    """Assemble an Entitlement for ``tier`` with the right feature/runtime sets
    and the current grace flag."""
    paid_feats = _TIER_FEATURES.get(tier, frozenset())
    runtimes = FREE_RUNTIMES | PAID_RUNTIMES if tier in _TIER_PAID_RUNTIMES else FREE_RUNTIMES
    return Entitlement(
        tier=tier,
        source=source,
        node_limit=node_limit,
        expiry=expiry,
        features=FREE_FEATURES | paid_feats,
        runtimes=runtimes,
        grace=not is_enforced(),
    )


def _oss_free() -> Entitlement:
    """The always-available fallback: OSS free, perpetual, current grace flag."""
    return _build(TIER_OSS, "oss", node_limit=1, expiry=None)


def _read_local_license() -> Entitlement | None:
    """Resolve a self-hosted entitlement from ``~/.clawmetry/license.key``.

    Stub: signature verification + payload parsing land with the Ed25519
    license client (Phase 2). Until then a present file is ignored (returns
    None) so an unverified file can never grant access. Never raises."""
    try:
        if not os.path.isfile(_LICENSE_PATH):
            return None
        # Phase 2: verify Ed25519 signature against the embedded public key,
        # parse {tier, nodes, exp, features}, and _build(...) from it.
        logger.debug("license.key present but verification not yet wired (Phase 2)")
        return None
    except Exception as exc:  # never crash on a bad/locked file
        logger.warning("entitlements: license read failed: %s", exc)
        return None


def _read_cloud_plan() -> Entitlement | None:
    """Resolve a cloud entitlement from the plan the daemon caches off the
    heartbeat (``~/.clawmetry/cloud_plan.json``).

    Stub: the daemon does not write this cache yet (Phase 4). When present it
    is expected to hold ``{"plan": "cloud_pro", "node_limit": N,
    "expiry": epoch}``. Never raises."""
    try:
        if not os.path.isfile(_CLOUD_PLAN_CACHE):
            return None
        with open(_CLOUD_PLAN_CACHE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        plan = str(data.get("plan", "")).strip().lower()
        if plan not in _PAID_TIERS and plan not in (TIER_CLOUD_FREE,):
            return None
        return _build(
            plan,
            "cloud",
            node_limit=int(data.get("node_limit", 1) or 1),
            expiry=data.get("expiry"),
        )
    except Exception as exc:
        logger.warning("entitlements: cloud-plan read failed: %s", exc)
        return None


# ── cached resolution ────────────────────────────────────────────────────────
_lock = threading.Lock()
_cache: dict = {"ent": None, "ts": 0.0, "enforce": None}


def get_entitlement(force: bool = False) -> Entitlement:
    """Resolve (and cache) the current entitlement. Cheap by design — the
    FLYWHEEL performance budget forbids a per-request network call, so the
    result is cached for ``_CACHE_TTL_SECS``. The cache also busts when the
    enforce flag flips. Never raises: any failure returns OSS-free."""
    try:
        enforce = is_enforced()
        with _lock:
            fresh = (
                not force
                and _cache["ent"] is not None
                and _cache["enforce"] == enforce
                and (time.time() - _cache["ts"]) < _CACHE_TTL_SECS
            )
            if fresh:
                return _cache["ent"]
        ent = _read_local_license() or _read_cloud_plan() or _oss_free()
        with _lock:
            _cache.update(ent=ent, ts=time.time(), enforce=enforce)
        return ent
    except Exception as exc:
        logger.warning("entitlements: resolution failed, defaulting to OSS free: %s", exc)
        return _oss_free()


def invalidate() -> None:
    """Drop the cached entitlement (call after activating/removing a license)."""
    with _lock:
        _cache.update(ent=None, ts=0.0, enforce=None)


def available_runtimes() -> list[str]:
    """Runtimes the UI should expose. In grace mode that's every known
    runtime (so nothing disappears before enforcement); once enforced it's the
    entitled set. Locked-but-visible rendering is the UI's job (Phase 5)."""
    ent = get_entitlement()
    if ent.grace:
        return sorted(ALL_RUNTIMES)
    return sorted(ent.runtimes)
