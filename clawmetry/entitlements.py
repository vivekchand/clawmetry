"""
clawmetry/entitlements.py — open-core entitlement resolution.

Single source of truth for "what is this install allowed to do". Everything
that gates a runtime or an advanced feature reads :func:`get_entitlement` —
nothing should gate on a hardcoded plan check scattered across routes.

Open-core model
---------------
* **FREE** (this OSS package): the OpenClaw + NVIDIA NemoClaw runtimes +
  NeMo governance + the core observability surface. Always available — no
  key, no network call.
* **PAID** (the closed-source ``clawmetry-pro`` package, fetched only with
  a valid license key or a cloud entitlement — it is *not* shipped in this
  repo): the other agent runtimes (Claude Code, Codex, Cursor, …), the
  advanced features (custom alerts, multi-node fleet, anomaly detection, …),
  and paid CLI capabilities.

  NeMo governance (policy enforcement on top of any runtime) remains a free
  *feature* (``nemo_governance``). The ``nemoclaw`` agent runtime is also
  free and sits alongside ``openclaw`` in ``FREE_RUNTIMES``.

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
# FREE: the OpenClaw and NVIDIA NemoClaw runtimes. NeMo *governance* (policy
# enforcement) is a separate free feature; ``nemoclaw`` here is the agent
# runtime itself, which is part of the free tier alongside ``openclaw``.
FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw"})

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

# Display labels for every known runtime.
RUNTIME_LABELS = {
    "openclaw": "OpenClaw",
    "nemoclaw": "NemoClaw",
    "claude_code": "Claude Code",
    "codex": "Codex",
    "cursor": "Cursor",
    "aider": "Aider",
    "goose": "Goose",
    "opencode": "opencode",
    "qwen_code": "Qwen Code",
    "hermes": "Hermes",
    "picoclaw": "PicoClaw",
    "nanoclaw": "NanoClaw",
}

_TIER_ORDER = (
    TIER_OSS,
    TIER_CLOUD_FREE,
    TIER_TRIAL,
    TIER_CLOUD_STARTER,
    TIER_CLOUD_PRO,
    TIER_PRO,
    TIER_ENTERPRISE,
)

RUNTIME_ALIASES = {
    "claude-code": "claude_code",
    "claudecode": "claude_code",
    "qwen-code": "qwen_code",
    "qwencode": "qwen_code",
    "open-code": "opencode",
    "open_code": "opencode",
    "open-claw": "openclaw",
    "open_claw": "openclaw",
    "nemo-claw": "nemoclaw",
    "nemo_claw": "nemoclaw",
    "pico-claw": "picoclaw",
    "pico_claw": "picoclaw",
    "nano-claw": "nanoclaw",
    "nano_claw": "nanoclaw",
}

TIER_LABELS = {
    TIER_OSS: "OSS",
    TIER_CLOUD_FREE: "Free",
    TIER_TRIAL: "Trial",
    TIER_CLOUD_STARTER: "Starter",
    TIER_CLOUD_PRO: "Pro",
    TIER_PRO: "Self-hosted Pro",
    TIER_ENTERPRISE: "Enterprise",
}

FEATURE_LABELS = {
    "sessions": "Sessions",
    "transcripts": "Transcripts",
    "usage": "Usage",
    "brain": "Brain",
    "flow": "Flow",
    "tracing": "Tracing",
    "health": "Health",
    "logs": "Logs",
    "crons": "Crons",
    "channels": "Channels",
    "nemo_governance": "NeMo Governance",
    "overview": "Overview",
    "multi_runtime": "Multi-runtime",
    "fleet": "Multi-node fleet",
    "cloud_sync": "Cloud sync",
    "all_channels": "All channels",
    "approval_queue": "Approval queue",
    "budget_limits": "Budget limits",
    "per_runtime_health_timeline": "Per-runtime health timeline",
    "per_run_waste_flags": "Per-run waste flags",
    "per_run_compare": "Per-run compare",
    "error_triage": "Error triage",
    "self_evolve": "Self-Evolve",
    "asset_registry": "Asset registry",
    "eval_suite": "Eval suite",
    "tool_policy": "Tool policy",
    "otel_export": "OTel export",
    "custom_webhooks": "Custom webhooks",
    "custom_runtime_ingest": "Custom runtime ingest",
    "custom_alerts": "Custom alerts",
    "alert_webhooks": "Alert webhooks",
    "anomaly_detection": "Anomaly detection",
    "cost_optimizer": "Cost optimizer",
    "siem_export": "SIEM export",
    "sso": "SSO",
    "audit_logs": "Audit logs",
    "rbac": "RBAC",
    "air_gapped_license": "Air-gapped license",
    "custom_data_residency": "Custom data residency",
}

_ALIAS_FEATURES = frozenset(
    {"custom_alerts", "alert_webhooks", "anomaly_detection", "cost_optimizer"}
)


# ── Feature catalogue ───────────────────────────────────────────────────────
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

STARTER_FEATURES = frozenset(
    {
        "multi_runtime",
        "fleet",
        "cloud_sync",
        "all_channels",
        "approval_queue",
        "budget_limits",
        "per_runtime_health_timeline",
    }
)

PRO_ONLY_FEATURES = frozenset(
    {
        "per_run_waste_flags",
        "per_run_compare",
        "error_triage",
        "self_evolve",
        "asset_registry",
        "eval_suite",
        "tool_policy",
        "otel_export",
        "custom_webhooks",
        "custom_runtime_ingest",
        "custom_alerts",
        "alert_webhooks",
        "anomaly_detection",
        "cost_optimizer",
    }
)

PAID_FEATURES = STARTER_FEATURES | PRO_ONLY_FEATURES

ENTERPRISE_FEATURES = frozenset(
    {
        "siem_export",
        "sso",
        "audit_logs",
        "rbac",
        "air_gapped_license",
        "custom_data_residency",
    }
)

ALL_FEATURES = FREE_FEATURES | PAID_FEATURES | ENTERPRISE_FEATURES

_TIER_FEATURES = {
    TIER_OSS: frozenset(),
    TIER_CLOUD_FREE: frozenset(),
    TIER_TRIAL: PAID_FEATURES,
    TIER_CLOUD_STARTER: STARTER_FEATURES,
    TIER_CLOUD_PRO: PAID_FEATURES,
    TIER_PRO: PAID_FEATURES,
    TIER_ENTERPRISE: PAID_FEATURES | ENTERPRISE_FEATURES,
}

_TIER_RETENTION_DAYS = {
    TIER_OSS: 7,
    TIER_CLOUD_FREE: 7,
    TIER_TRIAL: 30,
    TIER_CLOUD_STARTER: 30,
    TIER_CLOUD_PRO: 90,
    TIER_PRO: 90,
    TIER_ENTERPRISE: None,
}

_FREE_CHANNEL_LIMIT = 3
_TIER_CHANNEL_LIMIT = {
    TIER_OSS: _FREE_CHANNEL_LIMIT,
    TIER_CLOUD_FREE: _FREE_CHANNEL_LIMIT,
    TIER_TRIAL: None,
    TIER_CLOUD_STARTER: None,
    TIER_CLOUD_PRO: None,
    TIER_PRO: None,
    TIER_ENTERPRISE: None,
}

# Node-count cap per tier. OSS / Cloud Free are a single-node grant; every paid
# tier is license-bound (the actual node_limit comes off the license payload or
# cached cloud plan), so the static per-tier ceiling here is the *unlimited*
# sentinel ``None``. ``min_tier_for_node_count`` walks this map the same way
# ``min_tier_for_channel_count`` walks ``_TIER_CHANNEL_LIMIT`` so all four
# capacity axes resolve off a single shape.
_FREE_NODE_LIMIT = 1
_TIER_NODE_LIMIT = {
    TIER_OSS: _FREE_NODE_LIMIT,
    TIER_CLOUD_FREE: _FREE_NODE_LIMIT,
    TIER_TRIAL: None,
    TIER_CLOUD_STARTER: None,
    TIER_CLOUD_PRO: None,
    TIER_PRO: None,
    TIER_ENTERPRISE: None,
}

_TIER_PAID_RUNTIMES = _PAID_TIERS

_PURCHASABLE_TIERS = (
    TIER_OSS,
    TIER_CLOUD_FREE,
    TIER_CLOUD_STARTER,
    TIER_CLOUD_PRO,
    TIER_PRO,
    TIER_ENTERPRISE,
)

_TIER_RANK = {
    TIER_OSS: 0,
    TIER_CLOUD_FREE: 0,
    TIER_CLOUD_STARTER: 1,
    TIER_TRIAL: 2,
    TIER_CLOUD_PRO: 2,
    TIER_PRO: 2,
    TIER_ENTERPRISE: 3,
}

_LICENSE_PATH = os.path.expanduser("~/.clawmetry/license.key")
_CLOUD_PLAN_CACHE = os.path.expanduser("~/.clawmetry/cloud_plan.json")
_ENFORCE_ENABLE_VALUES = frozenset({"1", "true", "yes", "on"})
_CACHE_TTL_SECS = 60.0
_ENFORCE_AT_ENV = "CLAWMETRY_ENFORCE_AT"
_RETENTION_OVERRIDE_ENV = "CLAWMETRY_RETENTION_DAYS"


def is_enforced() -> bool:
    """True when the paywall is live. Default OFF (grace) until the enforce
    release flips it. ``CLAWMETRY_ENFORCE=1`` (1/true/yes/on) turns it on."""
    return (
        os.environ.get("CLAWMETRY_ENFORCE", "").strip().lower()
        in _ENFORCE_ENABLE_VALUES
    )


def enforce_at_epoch() -> float | None:
    """Resolve the announced enforce-at moment from ``CLAWMETRY_ENFORCE_AT``.
    Accepts ISO date, ISO datetime, or epoch seconds. Never raises."""
    raw = os.environ.get(_ENFORCE_AT_ENV, "").strip()
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError:
        pass
    try:
        from datetime import datetime, timezone

        s = raw.replace("Z", "+00:00") if raw.endswith("Z") else raw
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception as exc:
        logger.warning("entitlements: bad CLAWMETRY_ENFORCE_AT %r: %s", raw, exc)
        return None


def _capacity_transition(before: int | None, after: int | None) -> dict:
    """Encode one capacity-axis transition between two tiers.

    ``None`` is the unlimited sentinel on either side. ``delta`` is
    ``after - before`` only when both ends are finite; ``None`` whenever
    either side is unlimited. ``unlocked`` flips True when a finite cap
    goes unlimited (the "now unlimited" CTA copy); ``locked`` flips True
    when an unlimited cap becomes finite (the cancellation-warning copy).
    The pair is mutually exclusive, so callers can pick either side
    without having to infer direction from ``delta``'s sign.
    """
    try:
        unlocked = before is not None and after is None
        locked = before is None and after is not None
        if before is None or after is None:
            delta: int | None = None
        else:
            try:
                delta = int(after) - int(before)
            except (TypeError, ValueError):
                delta = None
        return {
            "before": before,
            "after": after,
            "delta": delta,
            "unlocked": unlocked,
            "locked": locked,
        }
    except Exception:
        return {
            "before": before,
            "after": after,
            "delta": None,
            "unlocked": False,
            "locked": False,
        }


@dataclass(frozen=True)
class Entitlement:
    """Resolved entitlement for this install. Immutable; rebuild via
    :func:`get_entitlement`."""

    tier: str = TIER_OSS
    source: str = "oss"  # "license" | "cloud" | "oss"
    node_limit: int = 1
    expiry: float | None = None
    features: frozenset = field(default_factory=lambda: FREE_FEATURES)
    runtimes: frozenset = field(default_factory=lambda: FREE_RUNTIMES)
    grace: bool = True

    @property
    def is_paid(self) -> bool:
        return self.tier in _PAID_TIERS

    @property
    def expired(self) -> bool:
        return self.expiry is not None and time.time() > self.expiry

    def days_until_expiry(self) -> int | None:
        try:
            if self.expiry is None:
                return None
            remaining = float(self.expiry) - time.time()
            if remaining <= 0:
                return 0
            return int(remaining // 86400)
        except (TypeError, ValueError):
            return None

    def expires_within(self, days: int) -> bool:
        remaining = self.days_until_expiry()
        if remaining is None:
            return False
        try:
            threshold = max(0, int(days))
        except (TypeError, ValueError):
            return False
        return remaining <= threshold

    def allows_runtime(self, runtime: str) -> bool:
        if self.grace:
            return True
        return self.entitled_runtime(runtime)

    def entitled_runtime(self, runtime: str) -> bool:
        rt = (runtime or "").lower()
        if rt in FREE_RUNTIMES:
            return True
        if self.expired:
            return False
        return rt in self.runtimes

    def allows_feature(self, feature: str) -> bool:
        if self.grace:
            return True
        if feature in FREE_FEATURES:
            return True
        if self.expired:
            return False
        return feature in self.features

    def allows_node_count(self, current: int) -> bool:
        if self.grace:
            return True
        try:
            n = int(current)
        except (TypeError, ValueError):
            return True
        if n <= 0:
            return True
        if self.expired:
            return n <= 1
        if self.node_limit is None or int(self.node_limit) <= 0:
            return True
        return n <= int(self.node_limit)

    def locked_runtimes(self) -> tuple[str, ...]:
        try:
            return tuple(sorted(rt for rt in PAID_RUNTIMES if not self.allows_runtime(rt)))
        except Exception:
            return ()

    def locked_features(self) -> tuple[str, ...]:
        try:
            paid_universe = PAID_FEATURES | ENTERPRISE_FEATURES
            return tuple(sorted(f for f in paid_universe if not self.allows_feature(f)))
        except Exception:
            return ()

    def min_tier_for(self, key: str) -> str | None:
        k = (key or "").strip().lower()
        if not k:
            return None
        if k in ALL_FEATURES:
            return min_tier_for_feature(k)
        if k in ALL_RUNTIMES:
            return min_tier_for_runtime(k)
        return None

    def next_purchasable_tier(self) -> str | None:
        try:
            current_rank = max(0, tier_rank(self.tier))
            for candidate in _PURCHASABLE_TIERS:
                if tier_rank(candidate) > current_rank:
                    return candidate
            return None
        except Exception as exc:
            logger.warning("entitlements: next_purchasable_tier failed: %s", exc)
            return None

    def previous_purchasable_tier(self) -> str | None:
        try:
            current_rank = max(0, tier_rank(self.tier))
            lower_ranks = sorted(
                {tier_rank(t) for t in _PURCHASABLE_TIERS if 0 <= tier_rank(t) < current_rank},
                reverse=True,
            )
            if not lower_ranks:
                return None
            target_rank = lower_ranks[0]
            cluster = [t for t in _PURCHASABLE_TIERS if tier_rank(t) == target_rank]
            if not cluster:
                return None
            if self.source == "cloud":
                cloud_pick = next((t for t in cluster if t.startswith("cloud_")), None)
                if cloud_pick is not None:
                    return cloud_pick
            else:
                self_hosted_pick = next(
                    (t for t in cluster if not t.startswith("cloud_")), None,
                )
                if self_hosted_pick is not None:
                    return self_hosted_pick
            return cluster[0]
        except Exception as exc:
            logger.warning("entitlements: previous_purchasable_tier failed: %s", exc)
            return None

    def capacity_diff(self, target_tier: str) -> dict:
        """Per-axis capacity transition from this entitlement to ``target_tier``.

        Companion to :meth:`upgrade_diff` / :meth:`downgrade_diff`: those
        enumerate feature / runtime adds-or-losses; this one covers the three
        capacity axes (channels, retention, nodes) that the CTA card needs to
        say *"channel cap 3 -> unlimited"* alongside *"unlocks claude_code"*.

        Direction-agnostic: each axis carries a ``before`` / ``after`` /
        ``delta`` triple plus mutually-exclusive ``unlocked`` / ``locked``
        booleans, so the same payload renders for upgrade and downgrade CTAs.
        ``None`` on either side is the unlimited sentinel; ``delta`` is only
        finite when both sides are.

        Unknown / empty ``target_tier`` returns the fallback shape (target
        echoed, every axis ``None``). Never raises.
        """
        try:
            tt = (target_tier or "").strip().lower()
            if tt not in _TIER_FEATURES:
                return {
                    "target": tt,
                    "channel_limit": None,
                    "retention_days": None,
                    "node_limit": None,
                }
            return {
                "target": tt,
                "channel_limit": _capacity_transition(
                    self.channel_limit(),
                    _TIER_CHANNEL_LIMIT.get(tt, _FREE_CHANNEL_LIMIT),
                ),
                "retention_days": _capacity_transition(
                    self.event_retention_days(),
                    _TIER_RETENTION_DAYS.get(tt, 7),
                ),
                "node_limit": _capacity_transition(
                    self.node_limit,
                    _TIER_NODE_LIMIT.get(tt, _FREE_NODE_LIMIT),
                ),
            }
        except Exception as exc:
            logger.warning("entitlements: capacity_diff failed: %s", exc)
            return {
                "target": target_tier or "",
                "channel_limit": None,
                "retention_days": None,
                "node_limit": None,
            }

    def next_tier_capacity_diff(self) -> dict | None:
        try:
            target = self.next_purchasable_tier()
            if target is None:
                return None
            return self.capacity_diff(target)
        except Exception as exc:
            logger.warning("entitlements: next_tier_capacity_diff failed: %s", exc)
            return None

    def previous_tier_capacity_diff(self) -> dict | None:
        try:
            target = self.previous_purchasable_tier()
            if target is None:
                return None
            return self.capacity_diff(target)
        except Exception as exc:
            logger.warning("entitlements: previous_tier_capacity_diff failed: %s", exc)
            return None

    def upgrade_diff(self, target_tier: str) -> dict:
        try:
            tt = (target_tier or "").strip().lower()
            target_paid_feats = _TIER_FEATURES.get(tt)
            if target_paid_feats is None:
                return {"target": tt, "added_features": [], "added_runtimes": []}
            target_feats = FREE_FEATURES | target_paid_feats
            if tt == TIER_ENTERPRISE:
                target_feats = target_feats | ENTERPRISE_FEATURES
            target_runtimes = (
                FREE_RUNTIMES | PAID_RUNTIMES
                if tt in _TIER_PAID_RUNTIMES
                else FREE_RUNTIMES
            )
            return {
                "target": tt,
                "added_features": sorted(target_feats - self.features),
                "added_runtimes": sorted(target_runtimes - self.runtimes),
            }
        except Exception as exc:
            logger.warning("entitlements: upgrade_diff failed: %s", exc)
            return {"target": target_tier or "", "added_features": [], "added_runtimes": []}

    def downgrade_diff(self, target_tier: str) -> dict:
        try:
            tt = (target_tier or "").strip().lower()
            target_paid_feats = _TIER_FEATURES.get(tt)
            if target_paid_feats is None:
                return {"target": tt, "lost_features": [], "lost_runtimes": []}
            target_feats = FREE_FEATURES | target_paid_feats
            if tt == TIER_ENTERPRISE:
                target_feats = target_feats | ENTERPRISE_FEATURES
            target_runtimes = (
                FREE_RUNTIMES | PAID_RUNTIMES
                if tt in _TIER_PAID_RUNTIMES
                else FREE_RUNTIMES
            )
            return {
                "target": tt,
                "lost_features": sorted(self.features - target_feats),
                "lost_runtimes": sorted(self.runtimes - target_runtimes),
            }
        except Exception as exc:
            logger.warning("entitlements: downgrade_diff failed: %s", exc)
            return {"target": target_tier or "", "lost_features": [], "lost_runtimes": []}

    def next_tier_diff(self) -> dict | None:
        try:
            target = self.next_purchasable_tier()
            if target is None:
                return None
            return self.upgrade_diff(target)
        except Exception as exc:
            logger.warning("entitlements: next_tier_diff failed: %s", exc)
            return None

    def previous_tier_diff(self) -> dict | None:
        try:
            target = self.previous_purchasable_tier()
            if target is None:
                return None
            return self.downgrade_diff(target)
        except Exception as exc:
            logger.warning("entitlements: previous_tier_diff failed: %s", exc)
            return None

    def next_tier_unlocks(self) -> dict | None:
        """One-rung-up unlocks row in :func:`tier_unlocks` shape.

        Convenience for ``tier_unlocks(self.next_purchasable_tier())`` so an
        upgrade-CTA card can render the marginal "what's new at the next
        rung" payload (with full ``tier`` / ``previous_tier`` metadata)
        without first looking up the next purchasable tier. Returns ``None``
        at the ceiling (no rung above to upgrade to) and never raises --
        a resolver failure short-circuits to ``None`` so a CTA surface
        keeps rendering instead of 500-ing.
        """
        try:
            target = self.next_purchasable_tier()
            if target is None:
                return None
            return tier_unlocks(target)
        except Exception as exc:
            logger.warning("entitlements: next_tier_unlocks failed: %s", exc)
            return None

    def previous_tier_unlocks(self) -> dict | None:
        """One-rung-down unlocks row in :func:`tier_unlocks` shape.

        Convenience for ``tier_unlocks(self.previous_purchasable_tier())`` --
        the marginal-unlocks row of the rung immediately below current.
        Useful for "you'd still keep X / you've already unlocked Y at your
        current tier" copy on a downgrade confirmation card, paired with
        :meth:`previous_tier_diff` (which carries the same marginal in
        ``downgrade_diff`` shape). Returns ``None`` at the floor (no rung
        below) and never raises.
        """
        try:
            target = self.previous_purchasable_tier()
            if target is None:
                return None
            return tier_unlocks(target)
        except Exception as exc:
            logger.warning("entitlements: previous_tier_unlocks failed: %s", exc)
            return None

    def next_tier_locks(self) -> dict | None:
        """One-rung-up locks row in :func:`tier_locks` shape.

        Marginal-loss companion to :meth:`next_tier_unlocks` and the fourth
        member of the ``next_tier_*`` family alongside :meth:`next_tier_diff`
        (full ``upgrade_diff`` shape), :meth:`next_tier_unlocks` (marginal
        grants in ``tier_unlocks`` shape), and :meth:`next_tier_capacity_diff`
        (capacity-only marginal).

        Convenience for ``tier_locks(self.next_purchasable_tier())`` -- the
        marginal-locks row of the rung immediately above current as a
        tier-property (``lost_features`` / ``lost_runtimes`` are what that
        rung first loses vs the rung above *it*, NOT vs the caller). Useful
        as a symmetric detail row alongside :meth:`next_tier_unlocks` on a
        pricing-table cell so the rung above carries both its first-grant
        and first-loss copy off ONE entitlement round-trip; collapses to
        empty loss lists at the ladder's ceiling (Enterprise's
        :func:`tier_locks` row has no rung above to step down from).

        Returns ``None`` at the resolver's ceiling (no next purchasable
        rung to look up) and never raises -- a resolver failure
        short-circuits to ``None`` so the CTA surface keeps rendering
        instead of 500-ing.
        """
        try:
            target = self.next_purchasable_tier()
            if target is None:
                return None
            return tier_locks(target)
        except Exception as exc:
            logger.warning("entitlements: next_tier_locks failed: %s", exc)
            return None

    def previous_tier_locks(self) -> dict | None:
        """One-rung-down locks row in :func:`tier_locks` shape.

        Symmetric companion to :meth:`previous_tier_unlocks` -- where the
        unlocks form returns the rung-below's *first-grant* row (a tier
        property), this returns the rung-below's *first-loss* row.

        Convenience for ``tier_locks(self.previous_purchasable_tier())``;
        the row's ``lost_features`` / ``lost_runtimes`` are what the rung
        below first loses vs the rung above it -- and since "the rung
        above" the previous purchasable tier is *exactly the caller's
        current tier* in the simple single-step downgrade case, this
        row's loss lists byte-equal the caller's marginal loss when
        stepping down by one rung. Pair with :meth:`previous_tier_diff`
        (which carries the same marginal in ``downgrade_diff`` shape) on
        a step-down confirmation card.

        Returns ``None`` at the resolver's floor (no previous purchasable
        rung to look up) and never raises -- a resolver failure
        short-circuits to ``None`` so the confirmation surface keeps
        rendering instead of 500-ing.
        """
        try:
            target = self.previous_purchasable_tier()
            if target is None:
                return None
            return tier_locks(target)
        except Exception as exc:
            logger.warning("entitlements: previous_tier_locks failed: %s", exc)
            return None

    def next_tier_spec(self) -> dict | None:
        """One-rung-up full :func:`tier_spec_at`-shape descriptor.

        Convenience for ``tier_spec_at(self.tier, self.next_purchasable_tier())``
        so a pricing-table cell or upgrade-CTA card can render the full
        tier-row (``id``, ``label``, ``is_paid``, ``is_current``, ``rank``,
        ``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
        ``node_limit``, ``features``, ``runtimes``) for the rung above
        current off ONE entitlement round-trip, alongside :meth:`next_tier_diff`
        (full ``upgrade_diff`` row), :meth:`next_tier_unlocks` (marginal
        grants), :meth:`next_tier_locks` (marginal losses), and
        :meth:`next_tier_capacity_diff` (capacity-only marginal).

        Delegates to :func:`tier_spec_at` (not :func:`tier_spec`) so the
        ``is_current`` field is anchored on ``self.tier`` rather than the
        live resolver -- and since the target is by definition strictly
        above ``self.tier``, ``is_current`` is always ``False`` on the
        returned row. Returns ``None`` at the resolver's ceiling (no next
        purchasable rung) and never raises: a resolver failure short-
        circuits to ``None`` so the CTA surface keeps rendering instead
        of 500-ing.
        """
        try:
            target = self.next_purchasable_tier()
            if target is None:
                return None
            return tier_spec_at(self.tier, target)
        except Exception as exc:
            logger.warning("entitlements: next_tier_spec failed: %s", exc)
            return None

    def previous_tier_spec(self) -> dict | None:
        """One-rung-down full :func:`tier_spec_at`-shape descriptor.

        Symmetric companion to :meth:`next_tier_spec`. Convenience for
        ``tier_spec_at(self.tier, self.previous_purchasable_tier())`` --
        the full row of the rung immediately below current, useful on a
        downgrade-confirmation card alongside :meth:`previous_tier_diff`
        (full ``downgrade_diff`` row), :meth:`previous_tier_unlocks` (what
        that rung first granted), :meth:`previous_tier_locks` (what that
        rung first lost), and :meth:`previous_tier_capacity_diff`
        (capacity-only marginal).

        Delegates to :func:`tier_spec_at` so the ``is_current`` field is
        anchored on ``self.tier`` rather than the live resolver -- and
        since the target is by definition strictly below ``self.tier``,
        ``is_current`` is always ``False`` on the returned row. Returns
        ``None`` at the resolver's floor (no previous purchasable rung)
        and never raises -- a resolver failure short-circuits to ``None``
        so the confirmation surface keeps rendering instead of 500-ing.
        """
        try:
            target = self.previous_purchasable_tier()
            if target is None:
                return None
            return tier_spec_at(self.tier, target)
        except Exception as exc:
            logger.warning("entitlements: previous_tier_spec failed: %s", exc)
            return None

    def grace_remaining_days(self) -> int | None:
        at = enforce_at_epoch()
        if at is None:
            return None
        remaining = (at - time.time()) / 86400.0
        return int(remaining) if remaining > 0 else 0

    def lock_reason(self, item: str, *, kind: str | None = None) -> str | None:
        try:
            k = (item or "").strip().lower()
            if not k or len(k) > 256:
                return None
            if self.grace:
                return None
            inferred_kind = kind
            if inferred_kind is None:
                if k in ALL_RUNTIMES:
                    inferred_kind = "runtime"
                elif k in ALL_FEATURES:
                    inferred_kind = "feature"
                else:
                    return None
            if inferred_kind == "runtime":
                if k not in ALL_RUNTIMES:
                    return None
                if k in FREE_RUNTIMES:
                    return None
                if self.expired:
                    return f"License expired; '{k}' runtime requires a valid subscription."
                if self.allows_runtime(k):
                    return None
                return f"Paid runtime '{k}' requires Starter or above."
            if inferred_kind == "feature":
                if k not in ALL_FEATURES:
                    return None
                if k in FREE_FEATURES:
                    return None
                if self.expired:
                    return f"License expired; '{k}' feature requires a valid subscription."
                if self.allows_feature(k):
                    return None
                req = min_tier_for_feature(k)
                lbl = tier_label(req) if req else "Paid"
                return f"'{k}' feature requires {lbl} or above."
            if inferred_kind == "channels":
                try:
                    n = int(k)
                except (TypeError, ValueError):
                    return None
                if n <= 0:
                    return None
                if self.allows_channel_count(n):
                    return None
                if self.expired:
                    return (
                        f"License expired; {n} channels requires a valid "
                        f"subscription."
                    )
                cap = self.channel_limit()
                cap_str = str(cap) if cap is not None else "unlimited"
                req = min_tier_for_channel_count(n)
                lbl = tier_label(req) if req else "Paid"
                return (
                    f"{n} channels exceeds the {tier_label(self.tier)} cap of "
                    f"{cap_str}; requires {lbl} or above."
                )
            if inferred_kind == "retention_days":
                try:
                    n = int(k)
                except (TypeError, ValueError):
                    return None
                if n <= 0:
                    return None
                if self.allows_retention_window(n):
                    return None
                if self.expired:
                    return (
                        f"License expired; {n}-day retention requires a valid "
                        f"subscription."
                    )
                cap = self.event_retention_days()
                cap_str = f"{cap} days" if cap is not None else "unlimited"
                req = min_tier_for_retention_window(n)
                lbl = tier_label(req) if req else "Paid"
                return (
                    f"{n}-day retention exceeds the {tier_label(self.tier)} "
                    f"cap of {cap_str}; requires {lbl} or above."
                )
            if inferred_kind == "nodes":
                try:
                    n = int(k)
                except (TypeError, ValueError):
                    return None
                if n <= 0:
                    return None
                if self.allows_node_count(n):
                    return None
                if self.expired:
                    return (
                        f"License expired; {n} nodes requires a valid "
                        f"subscription."
                    )
                # node_limit comes off the license payload (per-grant), not the
                # static per-tier map. <=0 is the unlimited sentinel licenses
                # use for Enterprise.
                lim = self.node_limit
                cap_str = (
                    str(lim) if isinstance(lim, int) and lim > 0 else "unlimited"
                )
                req = min_tier_for_node_count(n)
                lbl = tier_label(req) if req else "Paid"
                return (
                    f"{n} nodes exceeds the {tier_label(self.tier)} cap of "
                    f"{cap_str}; requires {lbl} or above."
                )
            return None
        except Exception:
            return None

    def event_retention_days(self) -> int | None:
        return _TIER_RETENTION_DAYS.get(self.tier, 7)

    def effective_retention_days(self, env_override: object = None) -> int | None:
        try:
            cap = self.event_retention_days()
            raw = env_override
            if raw is None:
                raw = os.environ.get(_RETENTION_OVERRIDE_ENV, "")
            try:
                raw_str = str(raw).strip()
            except Exception:
                return cap
            if not raw_str:
                return cap
            try:
                ev = int(raw_str)
            except (TypeError, ValueError):
                logger.debug(
                    "entitlements: ignoring non-integer %s=%r",
                    _RETENTION_OVERRIDE_ENV, raw_str,
                )
                return cap
            if ev < 1:
                logger.debug(
                    "entitlements: ignoring non-positive %s=%d",
                    _RETENTION_OVERRIDE_ENV, ev,
                )
                return cap
            if cap is None:
                return ev
            return min(ev, cap)
        except Exception as exc:
            logger.debug("entitlements: effective_retention_days fallback: %s", exc)
            try:
                return self.event_retention_days()
            except Exception:
                return None

    def allows_retention_window(self, days: int | None) -> bool:
        if self.grace:
            return True
        if days is not None and days <= 0:
            return True
        if self.expired:
            return False
        cap = self.event_retention_days()
        if cap is None:
            return True
        if days is None:
            return False
        return days <= cap

    def channel_limit(self) -> int | None:
        if self.grace:
            return None
        return _TIER_CHANNEL_LIMIT.get(self.tier, _FREE_CHANNEL_LIMIT)

    def allows_channel_count(self, current: int) -> bool:
        if self.grace:
            return True
        try:
            n = int(current)
        except (TypeError, ValueError):
            return True
        if n <= 0:
            return True
        if self.expired:
            return n <= _FREE_CHANNEL_LIMIT
        lim = self.channel_limit()
        return lim is None or n <= lim

    def to_dict(self) -> dict:
        enforce_at = enforce_at_epoch()
        enforce_at_iso: str | None = None
        if enforce_at is not None:
            try:
                from datetime import datetime, timezone

                enforce_at_iso = (
                    datetime.fromtimestamp(enforce_at, tz=timezone.utc)
                    .isoformat()
                    .replace("+00:00", "Z")
                )
            except Exception:
                enforce_at_iso = None
        return {
            "tier": self.tier,
            "tier_label": tier_label(self.tier),
            "tier_rank": tier_rank(self.tier),
            "source": self.source,
            "node_limit": self.node_limit,
            "channel_limit": self.channel_limit(),
            "expiry": self.expiry,
            "expired": self.expired,
            "days_until_expiry": self.days_until_expiry(),
            "is_paid": self.is_paid,
            "grace": self.grace,
            "enforced": not self.grace,
            "enforce_at": enforce_at,
            "enforce_at_iso": enforce_at_iso,
            "days_until_enforce": self.grace_remaining_days(),
            "retention_days": self.event_retention_days(),
            "effective_retention_days": self.effective_retention_days(),
            "runtimes": sorted(self.runtimes),
            "features": sorted(self.features),
            "free_runtimes": sorted(FREE_RUNTIMES),
            "paid_runtimes": sorted(PAID_RUNTIMES),
            "all_runtimes": sorted(ALL_RUNTIMES),
            "locked_runtimes": list(self.locked_runtimes()),
            "locked_features": list(self.locked_features()),
            "next_tier": self.next_purchasable_tier(),
            "next_tier_label": (
                tier_label(self.next_purchasable_tier())
                if self.next_purchasable_tier() is not None
                else None
            ),
            "prev_tier": self.previous_purchasable_tier(),
            "prev_tier_label": (
                tier_label(self.previous_purchasable_tier())
                if self.previous_purchasable_tier() is not None
                else None
            ),
            "next_tier_diff": self.next_tier_diff(),
            "prev_tier_diff": self.previous_tier_diff(),
            "next_tier_capacity_diff": self.next_tier_capacity_diff(),
            "prev_tier_capacity_diff": self.previous_tier_capacity_diff(),
            "next_tier_unlocks": self.next_tier_unlocks(),
            "prev_tier_unlocks": self.previous_tier_unlocks(),
            "next_tier_locks": self.next_tier_locks(),
            "prev_tier_locks": self.previous_tier_locks(),
        }


def _build(tier: str, source: str, node_limit: int = 1, expiry: float | None = None) -> Entitlement:
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
    return _build(TIER_OSS, "oss", node_limit=1, expiry=None)


def _read_local_license() -> Entitlement | None:
    try:
        if not os.path.isfile(_LICENSE_PATH):
            return None
        from clawmetry import license as _lic

        return _lic.load_license(_LICENSE_PATH)
    except Exception as exc:
        logger.warning("entitlements: license read failed: %s", exc)
        return None


def _read_cloud_plan() -> Entitlement | None:
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
_last_emitted_tier: str | None = None


def _maybe_emit_change(ent: Entitlement) -> None:
    global _last_emitted_tier
    try:
        with _lock:
            if _last_emitted_tier == ent.tier:
                return
            previous = _last_emitted_tier
            _last_emitted_tier = ent.tier
        try:
            from clawmetry import extensions as _ext
        except Exception:
            return
        try:
            _ext.emit(
                "entitlement.changed",
                {
                    "previous_tier": previous,
                    "tier": ent.tier,
                    "source": ent.source,
                    "is_paid": ent.is_paid,
                    "grace": ent.grace,
                },
            )
        except Exception as exc:
            logger.debug("entitlements: emit failed: %s", exc)
    except Exception as exc:
        logger.debug("entitlements: change-emit skipped: %s", exc)


def get_entitlement(force: bool = False) -> Entitlement:
    """Resolve (and cache) the current entitlement. Never raises."""
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
        _maybe_emit_change(ent)
        return ent
    except Exception as exc:
        logger.warning("entitlements: resolution failed, defaulting to OSS free: %s", exc)
        return _oss_free()


def invalidate() -> None:
    with _lock:
        _cache.update(ent=None, ts=0.0, enforce=None)


def upgrade_diff(target_tier: str) -> dict:
    try:
        return get_entitlement().upgrade_diff(target_tier)
    except Exception as exc:
        logger.warning("entitlements: upgrade_diff (module) failed: %s", exc)
        return {"target": target_tier or "", "added_features": [], "added_runtimes": []}


def downgrade_diff(target_tier: str) -> dict:
    try:
        return get_entitlement().downgrade_diff(target_tier)
    except Exception as exc:
        logger.warning("entitlements: downgrade_diff (module) failed: %s", exc)
        return {"target": target_tier or "", "lost_features": [], "lost_runtimes": []}


def tier_diff(from_tier: str, to_tier: str) -> dict | None:
    """Arbitrary-endpoint diff between two tiers.

    Generalises :func:`upgrade_diff` / :func:`downgrade_diff` (which pin one
    endpoint to the resolved entitlement) to ANY pair of known tiers, so a
    "Compare A vs B" pricing-page widget can render the transition between
    any two rungs without first switching the resolver. The payload carries
    both directions on every call so the same shape covers an upgrade, a
    downgrade, a lateral (same-rank, different id) and an identity (same
    tier) -- the consumer reads the ``direction`` tag instead of inferring
    it from the deltas.

    Both endpoints accept any id in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is unreachable via the purchasable-only
    helpers but is a valid hypothetical destination for "what would a
    14-day trial unlock right now" copy). Unknown ids on either side
    short-circuit to ``None`` -- the same posture as :func:`preview` /
    :func:`tier_unlocks` -- so a paywall surface keeps rendering instead
    of 500-ing.

    Response shape::

        {
          "from":             "<tier id>",
          "from_label":       "...",
          "from_rank":        <int>,
          "to":               "<tier id>",
          "to_label":         "...",
          "to_rank":          <int>,
          "direction":        "upgrade" | "downgrade" | "lateral" | "identity",
          "added_features":   [...],   # in `to` but not in `from`
          "lost_features":    [...],   # in `from` but not in `to`
          "added_runtimes":   [...],
          "lost_runtimes":    [...],
          "capacity_changes": {
              "channel_limit":   {before, after, delta, unlocked, locked},
              "retention_days":  {before, after, delta, unlocked, locked},
              "node_limit":      {before, after, delta, unlocked, locked},
          },
        }

    The ``added_*`` / ``lost_*`` lists are sorted for byte-stable output,
    so a snapshot diff against a fixture stays deterministic. Set-identity:
    by construction ``tier_diff(X, Y)['added_features']`` byte-equals
    ``tier_diff(Y, X)['lost_features']`` (and likewise for runtimes) -- the
    same swap-the-endpoints invariant the upgrade/downgrade pair holds
    against the current entitlement, lifted to arbitrary endpoints.
    Pinned in the test suite so a future reshuffle of the tier grant sets
    can't silently desync the two views.

    Never raises: a resolver failure logs a warning and returns ``None``
    so the surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        from_feats = FREE_FEATURES | _TIER_FEATURES.get(f, frozenset())
        if f == TIER_ENTERPRISE:
            from_feats = from_feats | ENTERPRISE_FEATURES
        to_feats = FREE_FEATURES | _TIER_FEATURES.get(t, frozenset())
        if t == TIER_ENTERPRISE:
            to_feats = to_feats | ENTERPRISE_FEATURES
        from_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if f in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        to_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if t in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if f == t:
            direction = "identity"
        elif from_rank == to_rank:
            direction = "lateral"
        elif to_rank > from_rank:
            direction = "upgrade"
        else:
            direction = "downgrade"
        return {
            "from": f,
            "from_label": tier_label(f),
            "from_rank": from_rank,
            "to": t,
            "to_label": tier_label(t),
            "to_rank": to_rank,
            "direction": direction,
            "added_features": sorted(to_feats - from_feats),
            "lost_features": sorted(from_feats - to_feats),
            "added_runtimes": sorted(to_runtimes - from_runtimes),
            "lost_runtimes": sorted(from_runtimes - to_runtimes),
            "capacity_changes": {
                "channel_limit": _capacity_transition(
                    _TIER_CHANNEL_LIMIT.get(f, _FREE_CHANNEL_LIMIT),
                    _TIER_CHANNEL_LIMIT.get(t, _FREE_CHANNEL_LIMIT),
                ),
                "retention_days": _capacity_transition(
                    _TIER_RETENTION_DAYS.get(f, 7),
                    _TIER_RETENTION_DAYS.get(t, 7),
                ),
                "node_limit": _capacity_transition(
                    _TIER_NODE_LIMIT.get(f, _FREE_NODE_LIMIT),
                    _TIER_NODE_LIMIT.get(t, _FREE_NODE_LIMIT),
                ),
            },
        }
    except Exception as exc:
        logger.warning("entitlements: tier_diff failed: %s", exc)
        return None


def tier_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise path between two tiers.

    Generalises :func:`upgrade_path` / :func:`downgrade_path` (which pin
    one endpoint to the resolved entitlement) to ANY pair of known tiers
    -- the path analogue of :func:`tier_diff`. Lets a "Compare A vs B"
    pricing-page widget render the *sequence of rungs* between any two
    tiers (and the marginal transition at each rung) without first
    switching the resolver.

    The walk visits every purchasable tier strictly between ``from_tier``
    and ``to_tier`` plus the destination ``to_tier`` itself, in tier-rank
    order. Same-rank siblings *between* the endpoints are both included
    (matching :func:`upgrade_path`'s ladder shape); same-rank siblings of
    the destination are excluded so the path terminates exactly at
    ``to_tier`` and not at one of its rank peers. Each row is the
    :func:`tier_diff` payload between the previous step in the path (or
    ``from_tier`` for the first row) and the current rung -- so each row
    is a marginal step diff, and a consumer can fold the rows to
    reconstruct the cumulative ``tier_diff(from_tier, to_tier)`` shape.

    Endpoint semantics match :func:`tier_diff`: both ids accept any entry
    in :data:`_TIER_FEATURES` (including :data:`TIER_TRIAL`, which is not
    purchasable -- it is excluded from the walked rungs but is a valid
    endpoint for the marginal-step computation). Identity (``from == to``)
    returns ``[]`` -- no rungs to walk. Lateral (same rank, different id)
    returns a single-row path: ``[tier_diff(from, to)]``. Unknown ids on
    either side short-circuit to ``None``.

    Never raises: a resolver failure logs a warning and returns ``None``
    so a pricing-page surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            row = tier_diff(f, t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        prev_step = f
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = tier_diff(prev_step, tid)
            if row is not None:
                path.append(row)
                prev_step = tid
        return path
    except Exception as exc:
        logger.warning("entitlements: tier_path failed: %s", exc)
        return None


def tier_diff_batch() -> list[dict]:
    """Full marginal ``tier_diff`` for every purchasable tier in one pass.

    Plural sibling of :func:`tier_diff` and the "all-slices-in-one-row"
    member of the batch family alongside :func:`tier_unlocks_batch`
    (feature/runtime grant slice), :func:`tier_locks_batch` (feature/
    runtime loss slice) and :func:`capacity_diff_batch` (capacity slice).
    Where each of those siblings carries a single slice of the per-rung
    transition, ``tier_diff_batch`` carries ALL slices (``added_features``
    + ``lost_features`` + ``added_runtimes`` + ``lost_runtimes`` +
    ``capacity_changes``) in one row so a pricing-page table can render
    the full marginal column off **one** round-trip instead of N calls
    to ``/tier-diff``.

    Anchor matches :func:`tier_unlocks_batch`: each row is the
    :func:`tier_diff` payload between the next-lower-rank purchasable
    tier (the upgrade source) and the current tier. At the floor
    (``TIER_OSS`` / ``TIER_CLOUD_FREE``) there is no rung below, so the
    row collapses to ``tier_diff(tid, tid)`` -- an identity row with
    ``from == to``, ``direction == "identity"`` and all marginal lists
    empty. Consumers that want the floor's *cumulative* grant should
    pair with :func:`preview_batch` (whose floor row carries the full
    free grant); ``tier_diff_batch`` keeps every row byte-stable with a
    valid :func:`tier_diff` payload so the singular and the batch never
    diverge in shape.

    Rows are sorted by tier rank ascending (cheapest -> most capable)
    and, within the same rank, by tier id so the ordering is stable
    across calls and byte-stable against :func:`tier_unlocks_batch` /
    :func:`tier_locks_batch` / :func:`capacity_diff_batch` /
    :func:`preview_batch` (the five batches walk
    :data:`_PURCHASABLE_TIERS` in the same ``(rank, id)`` order so a
    pricing table lines up rung-for-rung without client-side re-sort).
    The trial tier is excluded -- it is not purchasable, same posture as
    the other batches.

    Each non-floor row's ``added_features`` byte-equals the same row in
    :func:`tier_unlocks_batch`'s ``features`` slot (and ditto for
    ``added_runtimes`` / ``runtimes``); each non-floor row's
    ``capacity_changes`` byte-equals the per-rung step in
    :func:`capacity_diff_path` (``TIER_OSS``, ``TIER_ENTERPRISE``). Both
    are pinned in the test suite so the batches can never silently drift
    apart.

    Decoupled from the resolved entitlement (walks the static per-tier
    maps), so grace vs enforce yields identical rows -- pinned in the
    test suite via a grace/enforce reload roundtrip.

    Never raises: if the helper blows up the function returns ``[]`` so
    the pricing-page UI keeps rendering instead of 500-ing.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target_rank = _TIER_RANK.get(tid, -1)
            prev_id: str | None = None
            prev_rank_seen = -1
            for cand in _PURCHASABLE_TIERS:
                cand_rank = _TIER_RANK.get(cand, -1)
                if 0 <= cand_rank < target_rank and cand_rank > prev_rank_seen:
                    prev_id = cand
                    prev_rank_seen = cand_rank
            anchor = prev_id if prev_id is not None else tid
            row = tier_diff(anchor, tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_diff_batch failed: %s", exc)
        return []


def next_tier_diff() -> dict | None:
    try:
        return get_entitlement().next_tier_diff()
    except Exception as exc:
        logger.warning("entitlements: next_tier_diff (module) failed: %s", exc)
        return None


def previous_tier_diff() -> dict | None:
    try:
        return get_entitlement().previous_tier_diff()
    except Exception as exc:
        logger.warning("entitlements: previous_tier_diff (module) failed: %s", exc)
        return None


def next_tier_unlocks() -> dict | None:
    """Module-level :meth:`Entitlement.next_tier_unlocks` against the resolved
    entitlement. Never raises."""
    try:
        return get_entitlement().next_tier_unlocks()
    except Exception as exc:
        logger.warning("entitlements: next_tier_unlocks (module) failed: %s", exc)
        return None


def previous_tier_unlocks() -> dict | None:
    """Module-level :meth:`Entitlement.previous_tier_unlocks` against the
    resolved entitlement. Never raises."""
    try:
        return get_entitlement().previous_tier_unlocks()
    except Exception as exc:
        logger.warning("entitlements: previous_tier_unlocks (module) failed: %s", exc)
        return None


def next_tier_locks() -> dict | None:
    """Module-level :meth:`Entitlement.next_tier_locks` against the resolved
    entitlement. Never raises."""
    try:
        return get_entitlement().next_tier_locks()
    except Exception as exc:
        logger.warning("entitlements: next_tier_locks (module) failed: %s", exc)
        return None


def previous_tier_locks() -> dict | None:
    """Module-level :meth:`Entitlement.previous_tier_locks` against the
    resolved entitlement. Never raises."""
    try:
        return get_entitlement().previous_tier_locks()
    except Exception as exc:
        logger.warning("entitlements: previous_tier_locks (module) failed: %s", exc)
        return None


def next_tier_spec() -> dict | None:
    """Module-level :meth:`Entitlement.next_tier_spec` against the resolved
    entitlement. Never raises."""
    try:
        return get_entitlement().next_tier_spec()
    except Exception as exc:
        logger.warning("entitlements: next_tier_spec (module) failed: %s", exc)
        return None


def previous_tier_spec() -> dict | None:
    """Module-level :meth:`Entitlement.previous_tier_spec` against the
    resolved entitlement. Never raises."""
    try:
        return get_entitlement().previous_tier_spec()
    except Exception as exc:
        logger.warning("entitlements: previous_tier_spec (module) failed: %s", exc)
        return None


def capacity_diff(target_tier: str) -> dict:
    try:
        return get_entitlement().capacity_diff(target_tier)
    except Exception as exc:
        logger.warning("entitlements: capacity_diff (module) failed: %s", exc)
        return {
            "target": target_tier or "",
            "channel_limit": None,
            "retention_days": None,
            "node_limit": None,
        }


def next_tier_capacity_diff() -> dict | None:
    try:
        return get_entitlement().next_tier_capacity_diff()
    except Exception as exc:
        logger.warning("entitlements: next_tier_capacity_diff (module) failed: %s", exc)
        return None


def previous_tier_capacity_diff() -> dict | None:
    try:
        return get_entitlement().previous_tier_capacity_diff()
    except Exception as exc:
        logger.warning("entitlements: previous_tier_capacity_diff (module) failed: %s", exc)
        return None


def _capacity_row(from_tier: str, to_tier: str) -> dict:
    """Build one ``capacity_diff``-shape row for an arbitrary ``from -> to`` pair.

    Singular-helper-shape row (``target``, ``channel_limit``, ``retention_days``,
    ``node_limit``) computed off the static per-tier caps, NOT off the resolved
    entitlement -- so a path / pair caller can compose marginal capacity steps
    without pinning either side to the resolver.
    """
    return {
        "target": to_tier,
        "channel_limit": _capacity_transition(
            _TIER_CHANNEL_LIMIT.get(from_tier, _FREE_CHANNEL_LIMIT),
            _TIER_CHANNEL_LIMIT.get(to_tier, _FREE_CHANNEL_LIMIT),
        ),
        "retention_days": _capacity_transition(
            _TIER_RETENTION_DAYS.get(from_tier, 7),
            _TIER_RETENTION_DAYS.get(to_tier, 7),
        ),
        "node_limit": _capacity_transition(
            _TIER_NODE_LIMIT.get(from_tier, _FREE_NODE_LIMIT),
            _TIER_NODE_LIMIT.get(to_tier, _FREE_NODE_LIMIT),
        ),
    }


def capacity_diff_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise capacity-transition path between two tiers.

    Capacity-only path companion to :func:`tier_path` -- where the parent
    helper returns the full :func:`tier_diff` payload per rung (added /
    lost features + runtimes + ``capacity_changes``), this helper returns
    just the singular :func:`capacity_diff` shape per rung
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``)
    so a capacity-only pricing widget can render the per-rung channel /
    retention / node transitions off **one** round-trip without paying
    for the feature / runtime set diff on every row.

    Pairs with the ``*-batch`` family: :func:`capacity_diff_batch` walks
    every purchasable tier as a cumulative "what does capacity look like
    at each rung off the resolver" ladder; this helper walks an
    arbitrary ``from -> to`` segment as a marginal "what happens to
    capacity at each step between two endpoints" ladder. Same rung
    semantics as :func:`tier_path`: visit every purchasable tier strictly
    between ``from_tier`` and ``to_tier`` plus the destination
    ``to_tier`` itself, in tier-rank order (ascending for an upgrade,
    descending for a downgrade); same-rank siblings between the
    endpoints are both included, same-rank siblings of the destination
    are excluded so the path terminates exactly at ``to_tier``.

    Each row's ``before`` side comes off the previous step's static
    caps (or ``from_tier`` for the first row), so a consumer can fold
    the rows to reconstruct the cumulative
    ``tier_diff(from_tier, to_tier)['capacity_changes']`` shape. This is
    deliberately decoupled from the resolved entitlement -- the path is
    a hypothetical "if I walked from X to Y, what would each rung cost
    me in capacity" view, not a "what would it cost from where I am
    now" view (that's what :func:`capacity_diff_batch` is for).

    Endpoint semantics match :func:`tier_diff` / :func:`tier_path`: both
    ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- excluded from the
    walked rungs but is a valid endpoint for the marginal-step
    computation). Identity (``from == to``) returns ``[]`` -- no rungs
    to walk. Lateral (same rank, different id) returns a single-row
    path: ``[_capacity_row(from, to)]``. Unknown ids on either side
    short-circuit to ``None``.

    Never raises: a resolver failure logs a warning and returns ``None``
    so a pricing-page surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            return [_capacity_row(f, t)]
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        prev_step = f
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            path.append(_capacity_row(prev_step, tid))
            prev_step = tid
        return path
    except Exception as exc:
        logger.warning("entitlements: capacity_diff_path failed: %s", exc)
        return None


def capacity_diff_batch() -> list[dict]:
    """Per-tier capacity transition for every purchasable tier in one pass.

    Plural sibling of :func:`capacity_diff`. Where the singular helper
    answers "what would the channel cap / retention / node cap look like
    at tier X" one tier at a time, the batch returns the same payload
    shape for every entry in :data:`_PURCHASABLE_TIERS` so a pricing-page
    table can render the capacity column off **one** round-trip instead
    of N calls to ``/capacity-diff``.

    Direction-agnostic capacity companion to the existing pricing-page
    batches: pair with :func:`tier_unlocks_batch` (marginal feature/
    runtime grant per rung), :func:`tier_locks_batch` (marginal feature/
    runtime loss per rung) and :func:`preview_batch` (cumulative shape
    per rung) to render the full "what's at X / what's new at X / what
    you'd give up at X / capacity at X" pricing-table view without
    client-side composition.

    Rows are sorted by tier rank ascending (cheapest -> most capable)
    and, within the same rank, by tier id so the ordering is stable
    across calls and byte-stable against :func:`tier_unlocks_batch` /
    :func:`tier_locks_batch` / :func:`preview_batch` (the four batches
    walk :data:`_PURCHASABLE_TIERS` in the same ``(rank, id)`` order so
    a pricing table lines up rung-for-rung without client-side re-sort).
    The trial tier is excluded (mirrors :func:`preview_batch` / the
    other batches -- it is not purchasable).

    Each row carries the singular :func:`capacity_diff` payload exactly
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``)
    so per-axis ``{before, after, delta, unlocked, locked}`` triples
    render identically off the batch and the singular endpoint. The
    ``before`` side comes off the resolved entitlement, so under grace
    the per-axis caps collapse to the unlimited (``None``) sentinel --
    same posture as the singular helper.

    Never raises: if the resolver blows up the helper returns ``[]``
    so the UI keeps rendering instead of 500-ing.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            out.append(capacity_diff(tid))
        return out
    except Exception as exc:
        logger.warning("entitlements: capacity_diff_batch failed: %s", exc)
        return []


def preview(target_tier: str) -> dict | None:
    """Render the :meth:`Entitlement.to_dict` shape for a hypothetical tier.

    Companion to :func:`upgrade_diff` / :func:`downgrade_diff`: where those
    answer "what would change", ``preview`` answers "what would the resulting
    Entitlement *look like*" -- the full denormalised shape the upgrade-CTA
    card renders ("Cloud Pro: 365-day retention, unlimited channels, claude_code
    + codex + ... unlocked"). Returns ``None`` for an unknown tier id and never
    raises.

    The previewed Entitlement is always rendered with ``grace=False`` so the
    concrete per-tier limits (``channel_limit``, ``retention_days``) surface --
    a grace-mode preview would zero those out and defeat the purpose. Source
    is tagged ``"preview"`` so the UI never mistakes it for a live entitlement.
    """
    try:
        tt = (target_tier or "").strip().lower()
        if tt not in _PURCHASABLE_TIERS:
            return None
        paid_feats = _TIER_FEATURES.get(tt, frozenset())
        runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if tt in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        ent = Entitlement(
            tier=tt,
            source="preview",
            node_limit=1,
            expiry=None,
            features=FREE_FEATURES | paid_feats,
            runtimes=runtimes,
            grace=False,
        )
        return ent.to_dict()
    except Exception as exc:
        logger.warning("entitlements: preview failed: %s", exc)
        return None


def preview_batch() -> list[dict]:
    """Cumulative ``Entitlement.to_dict`` shape for every purchasable tier
    in one pass.

    Plural sibling of :func:`preview`. Where the singular helper answers
    "what would the resulting Entitlement *look like* at tier X" one tier
    at a time, the batch returns the same denormalised row for every
    entry in :data:`_PURCHASABLE_TIERS` so a pricing-page table can render
    the full "Cloud Pro: 90-day retention, unlimited channels, claude_code
    unlocked" matrix off **one** round-trip instead of N calls to
    ``/preview``.

    Cumulative-state companion to :func:`tier_unlocks_batch` (marginal
    grant per rung) and :func:`tier_locks_batch` (marginal loss per rung):
    pair them to render the "what's at X / what's new at X / what you'd
    give up at X" three-column view of a pricing table without
    client-side composition.

    Rows are sorted by tier rank ascending (cheapest -> most capable)
    and, within the same rank, by tier id so the ordering is stable
    across calls and byte-stable against :func:`tier_unlocks_batch` /
    :func:`tier_locks_batch` (the three batches walk
    :data:`_PURCHASABLE_TIERS` in the same ``(rank, id)`` order so a
    pricing table lines up rung-for-rung without client-side re-sort).
    The trial tier is excluded (mirrors :func:`preview`, which returns
    ``None`` for non-purchasable tiers).

    Each row carries the full ``Entitlement.to_dict`` shape with
    ``source="preview"`` and ``grace=False`` -- same posture as
    :func:`preview` so the concrete per-tier capacity
    (``channel_limit``, ``retention_days``, ``node_limit``) surfaces. A
    grace-mode preview would zero those out and defeat the purpose.

    Same-rank tiers (e.g. ``TIER_CLOUD_PRO`` and ``TIER_PRO`` both at
    rank 2) are both returned, since callers may key off the tier id
    rather than the rank. Consumers that want a deduped pricing ladder
    can drop duplicates by ``tier_rank``.

    Never raises: if the resolver blows up the helper returns ``[]``
    so the UI keeps rendering instead of 500-ing.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = preview(tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: preview_batch failed: %s", exc)
        return []


def _preview_row(tier: str) -> dict | None:
    """Cumulative preview row for an arbitrary known tier.

    Private builder for :func:`preview_path`: mirrors :func:`preview` but
    accepts any id in :data:`_TIER_FEATURES` (including :data:`TIER_TRIAL`,
    which the singular :func:`preview` rejects because it is not
    purchasable), so a path that anchors a lateral or trial endpoint
    still resolves the cumulative-state row. Same posture as
    :func:`_unlocks_row` for :func:`tier_unlocks_path` -- the path
    walker only emits these via rungs that are themselves in
    :data:`_PURCHASABLE_TIERS`, so trial only surfaces here when the
    destination itself is trial (the lateral branch).

    Source is tagged ``"preview"`` and ``grace=False`` so concrete
    per-tier capacity (``channel_limit``, ``retention_days``,
    ``node_limit``) surfaces in the row -- a grace-mode preview would
    zero those out and defeat the purpose. Returns ``None`` on unknown
    ids and never raises.
    """
    try:
        tt = (tier or "").strip().lower()
        if tt not in _TIER_FEATURES:
            return None
        paid_feats = _TIER_FEATURES.get(tt, frozenset())
        runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if tt in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        ent = Entitlement(
            tier=tt,
            source="preview",
            node_limit=1,
            expiry=None,
            features=FREE_FEATURES | paid_feats,
            runtimes=runtimes,
            grace=False,
        )
        return ent.to_dict()
    except Exception as exc:
        logger.warning("entitlements: _preview_row failed: %s", exc)
        return None


def preview_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise cumulative-state path between two tiers.

    Cumulative-state analogue of :func:`tier_path` (full ``tier_diff``
    per rung), :func:`capacity_diff_path` (capacity-only per rung),
    :func:`tier_unlocks_path` (marginal grants per rung) and
    :func:`tier_locks_path` (marginal losses per rung) -- the fifth and
    final member of the ``_path`` family, the path-shaped sibling of
    :func:`preview_batch`. Where the four marginal/diff paths answer
    "what *changes* at each rung", this one answers "what does the
    resulting Entitlement *look like* at each rung" -- the cumulative
    ``Entitlement.to_dict`` snapshot at every step between ``from_tier``
    and ``to_tier``, so an upgrade-walkthrough surface can render the
    "Cloud Pro: 90-day retention, unlimited channels, claude_code
    unlocked" card at each rung off ONE round-trip without re-deriving
    capacity in JS.

    Per-rung row shape matches :func:`preview` exactly -- the full
    ``Entitlement.to_dict`` shape with ``source="preview"`` and
    ``grace=False`` -- so a UI that already renders a ``/preview`` row
    needs zero new shape code to render a row off this path.

    Walk semantics mirror :func:`tier_path` /
    :func:`capacity_diff_path` / :func:`tier_unlocks_path` /
    :func:`tier_locks_path` byte-for-byte (same ``_PURCHASABLE_TIERS``
    filter + same sort key + same destination-sibling exclusion), so the
    rung ``tier`` ids from this helper match the rung ``to`` ids from
    those four helpers identically -- the five paths line up
    rung-for-rung. Same-rank siblings strictly between the endpoints are
    both included (matching :func:`tier_path`'s ladder shape); same-rank
    siblings of the destination are excluded so the path terminates
    exactly at ``to_tier``.

    Direction semantics (all rows share the same cumulative-snapshot
    shape; only the sequence changes):

    * ``upgrade`` (ascending) -- rows climb cumulatively from the rung
      above ``from_tier`` toward ``to_tier``; the natural "what does my
      surface look like at each step up" walkthrough.
    * ``downgrade`` (descending) -- rows shrink cumulatively rung by
      rung; the cancellation-walkthrough counterpart.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the cumulative preview at ``to_tier``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`tier_diff`: both
    ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- it is excluded from
    the walked intermediate rungs but is a valid endpoint via the
    lateral branch). Unknown ids on either side short-circuit to
    ``None``.

    Resolver-independent: walks the static per-tier maps, so flipping
    enforce on yields byte-identical rows -- same property the rest of
    the ``_path`` family guarantees.

    Never raises: a resolver failure logs a warning and returns ``None``
    so an upgrade-walkthrough surface keeps rendering instead of
    breaking.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            row = _preview_row(t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = _preview_row(tid)
            if row is not None:
                path.append(row)
        return path
    except Exception as exc:
        logger.warning("entitlements: preview_path failed: %s", exc)
        return None


def tier_unlocks(target_tier: str) -> dict | None:
    """Per-tier marginal unlocks: features + runtimes that first become
    available *at* ``target_tier`` -- the set difference between this
    tier's grant and the next-lower purchasable tier's grant.

    Companion to :func:`preview` (cumulative state at a tier): where
    ``preview`` answers "what would the resulting Entitlement *look like*",
    ``tier_unlocks`` answers "what does this tier *first* unlock vs the
    tier below it" -- the "what's new in Pro vs Starter" view a
    pricing-page row or upgrade-CTA card uses.

    The "tier below" is the highest-rank entry in :data:`_PURCHASABLE_TIERS`
    whose rank is strictly less than ``target_tier``'s rank (trial is
    excluded from purchasables, so a promotional grant never shows up as
    the upgrade source). When ``target_tier`` sits at the floor (rank 0 --
    :data:`TIER_OSS` / :data:`TIER_CLOUD_FREE`) ``previous_tier`` is
    ``None`` and the marginal collapses to the full free grant
    (``FREE_FEATURES`` / ``FREE_RUNTIMES``).

    Returns ``None`` for an unknown tier id (including :data:`TIER_TRIAL`,
    which is not purchasable) and never raises.
    """
    try:
        tid = (target_tier or "").strip().lower()
        if tid not in _PURCHASABLE_TIERS:
            return None
        target_rank = _TIER_RANK.get(tid, -1)
        prev_id: str | None = None
        prev_rank = -1
        for cand in _PURCHASABLE_TIERS:
            cand_rank = _TIER_RANK.get(cand, -1)
            if 0 <= cand_rank < target_rank and cand_rank > prev_rank:
                prev_id = cand
                prev_rank = cand_rank
        this_feats = FREE_FEATURES | _TIER_FEATURES.get(tid, frozenset())
        this_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if tid in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        if prev_id is None:
            prev_feats: frozenset = frozenset()
            prev_runtimes: frozenset = frozenset()
        else:
            prev_feats = FREE_FEATURES | _TIER_FEATURES.get(prev_id, frozenset())
            prev_runtimes = (
                FREE_RUNTIMES | PAID_RUNTIMES
                if prev_id in _TIER_PAID_RUNTIMES
                else FREE_RUNTIMES
            )
        return {
            "tier": tid,
            "tier_label": tier_label(tid),
            "tier_rank": tier_rank(tid),
            "previous_tier": prev_id,
            "previous_tier_label": tier_label(prev_id) if prev_id else None,
            "previous_tier_rank": tier_rank(prev_id) if prev_id else None,
            "features": sorted(this_feats - prev_feats),
            "runtimes": sorted(this_runtimes - prev_runtimes),
        }
    except Exception as exc:
        logger.warning("entitlements: tier_unlocks failed: %s", exc)
        return None


def tier_unlocks_batch() -> list[dict]:
    """Marginal unlocks for every purchasable tier in one pass.

    Plural sibling of :func:`tier_unlocks`. Where the singular helper
    answers "what does *this* tier first unlock vs the tier below it"
    one tier at a time, the batch returns the same row shape for every
    entry in :data:`_PURCHASABLE_TIERS` so a pricing-page table can
    render the full "what's new in X" column off **one** round-trip
    instead of N calls to ``/tier-unlocks``.

    Rows are sorted by tier rank ascending (cheapest -> most capable)
    and, within the same rank, by tier id so the ordering is stable
    across calls. The trial tier is excluded (mirrors
    :func:`tier_unlocks`, which returns ``None`` for non-purchasable
    tiers); the floor tiers (``TIER_OSS`` / ``TIER_CLOUD_FREE``) appear
    with ``previous_tier=None`` and their marginal collapses to the
    full free grant -- same shape the singular helper returns.

    Same-rank tiers (e.g. ``TIER_CLOUD_PRO`` and ``TIER_PRO`` both at
    rank 2) are both returned, since callers may key off the tier id
    rather than the rank. Consumers that want a deduped pricing ladder
    can drop duplicates by ``tier_rank``.

    Never raises: if the resolver blows up the helper returns ``[]``
    so the UI keeps rendering instead of 500-ing.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = tier_unlocks(tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_unlocks_batch failed: %s", exc)
        return []


def _unlocks_row(from_tier: str, to_tier: str) -> dict | None:
    """Single marginal-unlocks row between two arbitrary tiers, with the
    source carried as ``previous_tier`` (path-chained, **not** the global
    next-lower-purchasable-tier anchor used by :func:`tier_unlocks`).

    Private builder for :func:`tier_unlocks_path`: each row is "what the
    `to` rung first unlocks vs the previous step in the walked path" so a
    consumer can fold the per-rung rows to reconstruct the cumulative
    ``tier_diff(from, to)['added_*']`` shape -- the same chain-property
    :func:`tier_path` and :func:`capacity_diff_path` enforce on their rows.

    Returns ``None`` on unknown ids and never raises -- the path walker
    drops ``None`` rows on the floor so a pricing surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        from_feats = FREE_FEATURES | _TIER_FEATURES.get(f, frozenset())
        if f == TIER_ENTERPRISE:
            from_feats = from_feats | ENTERPRISE_FEATURES
        to_feats = FREE_FEATURES | _TIER_FEATURES.get(t, frozenset())
        if t == TIER_ENTERPRISE:
            to_feats = to_feats | ENTERPRISE_FEATURES
        from_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if f in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        to_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if t in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        return {
            "tier": t,
            "tier_label": tier_label(t),
            "tier_rank": tier_rank(t),
            "previous_tier": f,
            "previous_tier_label": tier_label(f),
            "previous_tier_rank": tier_rank(f),
            "features": sorted(to_feats - from_feats),
            "runtimes": sorted(to_runtimes - from_runtimes),
        }
    except Exception as exc:
        logger.warning("entitlements: _unlocks_row failed: %s", exc)
        return None


def tier_unlocks_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise unlock path between two tiers.

    Unlocks-focused analogue of :func:`tier_path` and unlocks-focused
    path analogue of :func:`tier_unlocks` -- the third member of the
    ``_path`` family alongside :func:`tier_path` (full ``tier_diff`` per
    rung) and :func:`capacity_diff_path` (capacity-only per rung). Lets
    an "upgrade-walkthrough" surface render only the *newly-unlocked*
    features + runtimes at each rung between any two tiers off ONE
    round-trip, without the noise of the capacity axes or the symmetric
    ``lost_*`` lists that :func:`tier_path` carries.

    Per-rung row shape matches :func:`tier_unlocks` exactly --
    ``tier``, ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes`` -- with one critical difference: ``previous_tier`` is
    the **previous step in the walked path** (or ``from_tier`` for the
    first row), NOT the global "next-lower purchasable tier" anchor
    :func:`tier_unlocks` uses. The path-chained source guarantees
    ``row[i]['tier'] == row[i+1]['previous_tier']`` so a consumer can
    fold ``features`` / ``runtimes`` across rows to reconstruct the
    cumulative ``tier_diff(from_tier, to_tier)['added_*']`` shape -- the
    same chain-property :func:`tier_path` and :func:`capacity_diff_path`
    enforce on their rows.

    The walk visits every purchasable tier strictly between ``from_tier``
    and ``to_tier`` plus the destination ``to_tier`` itself, in tier-rank
    order (ascending or descending depending on direction). Same-rank
    siblings *between* the endpoints are both included (matching
    :func:`tier_path`'s ladder shape); same-rank siblings of the
    destination are excluded so the path terminates exactly at
    ``to_tier``. Rung walk is byte-stable against :func:`tier_path` and
    :func:`capacity_diff_path` (same ``_PURCHASABLE_TIERS`` filter +
    same sort key + same destination-sibling exclusion).

    Direction semantics:

    * ``upgrade`` (ascending) -- each row's ``features`` / ``runtimes``
      are the marginal grant at that rung. The natural "what do I get if
      I climb this far" walkthrough.
    * ``downgrade`` (descending) -- each row's ``features`` /
      ``runtimes`` are typically empty (you're losing things, not
      unlocking them); use :func:`tier_path` or
      :func:`tier_locks_path` for the marginal-loss view of a
      downgrade. The path still walks rungs so a UI keyed off rung
      shape keeps working; the empty lists are the correct "unlocks"
      answer.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the set difference between the two same-rank tier grants.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`tier_diff`: both
    ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- it is excluded from
    the walked rungs but is a valid endpoint for the marginal-step
    computation). Unknown ids on either side short-circuit to ``None``.

    Never raises: a resolver failure logs a warning and returns ``None``
    so an upgrade-walkthrough surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            row = _unlocks_row(f, t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        prev_step = f
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = _unlocks_row(prev_step, tid)
            if row is not None:
                path.append(row)
                prev_step = tid
        return path
    except Exception as exc:
        logger.warning("entitlements: tier_unlocks_path failed: %s", exc)
        return None


def tier_locks(target_tier: str) -> dict | None:
    """Per-tier marginal locks: features + runtimes that disappear when
    you *descend to* ``target_tier`` from the next-higher purchasable
    tier -- the marginal-loss companion to :func:`tier_unlocks`.

    Where ``tier_unlocks(X)`` answers "what does X *first* unlock vs the
    tier below it" (the upgrade-step marginal grant), ``tier_locks(X)``
    answers "what does X *first* lose vs the tier above it" (the
    downgrade-step marginal loss) -- the "what you'd be giving up by
    stepping down to Starter from Pro" view a per-rung downgrade-warning
    row uses, paired with :func:`downgrade_path` (cumulative state at a
    rung) the way :func:`tier_unlocks` is paired with :func:`upgrade_path`.

    The "tier above" is the *lowest*-rank entry in :data:`_PURCHASABLE_TIERS`
    whose rank is strictly *greater* than ``target_tier``'s rank (trial is
    excluded from purchasables, so a promotional grant never shows up as
    the downgrade source). When ``target_tier`` sits at the ceiling
    (:data:`TIER_ENTERPRISE`) ``next_tier`` is ``None`` and the marginal
    collapses to empty loss lists -- there is no rung above to step down
    from.

    Set-identity: by construction the marginal loss at ``X`` equals the
    marginal unlock at the next-higher purchasable tier above ``X``,
    just attributed to the destination (the rung you land on) rather
    than the source (the rung you stepped off). So
    ``tier_locks(X)['lost_features']`` byte-equals
    ``tier_unlocks(next_tier(X))['features']``, and likewise for runtimes
    -- pinned in the test suite so a future reshuffle of the tier grant
    sets can't silently desync the two views.

    Returns ``None`` for an unknown tier id (including :data:`TIER_TRIAL`,
    which is not purchasable) and never raises -- a resolver failure
    short-circuits to ``None`` so a downgrade-warning surface keeps
    rendering instead of 500-ing.
    """
    try:
        tid = (target_tier or "").strip().lower()
        if tid not in _PURCHASABLE_TIERS:
            return None
        target_rank = _TIER_RANK.get(tid, -1)
        next_candidates = sorted(
            (
                c
                for c in _PURCHASABLE_TIERS
                if _TIER_RANK.get(c, -1) > target_rank
            ),
            key=lambda c: (_TIER_RANK.get(c, -1), c),
        )
        next_id: str | None = next_candidates[0] if next_candidates else None
        this_feats = FREE_FEATURES | _TIER_FEATURES.get(tid, frozenset())
        this_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if tid in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        if next_id is None:
            next_feats: frozenset = frozenset()
            next_runtimes: frozenset = frozenset()
        else:
            next_feats = FREE_FEATURES | _TIER_FEATURES.get(next_id, frozenset())
            next_runtimes = (
                FREE_RUNTIMES | PAID_RUNTIMES
                if next_id in _TIER_PAID_RUNTIMES
                else FREE_RUNTIMES
            )
        return {
            "tier": tid,
            "tier_label": tier_label(tid),
            "tier_rank": tier_rank(tid),
            "next_tier": next_id,
            "next_tier_label": tier_label(next_id) if next_id else None,
            "next_tier_rank": tier_rank(next_id) if next_id else None,
            "lost_features": sorted(next_feats - this_feats),
            "lost_runtimes": sorted(next_runtimes - this_runtimes),
        }
    except Exception as exc:
        logger.warning("entitlements: tier_locks failed: %s", exc)
        return None


def tier_locks_batch() -> list[dict]:
    """Marginal locks for every purchasable tier in one pass.

    Plural sibling of :func:`tier_locks`. Where the singular helper
    answers "what does *this* tier first lose vs the tier above it"
    one tier at a time, the batch returns the same row shape for every
    entry in :data:`_PURCHASABLE_TIERS` so a downgrade-warning surface
    can render the full "what you'd give up at X" column off **one**
    round-trip instead of N calls to ``/tier-locks``.

    Marginal-loss companion to :func:`tier_unlocks_batch`: where the
    unlocks batch is the upgrade-CTA column on a pricing table, this
    is the downgrade-warning column on the same row -- pair them to
    render an "if you stay / if you drop" two-tone matrix without any
    client-side composition.

    Rows are sorted by tier rank ascending (cheapest -> most capable)
    and, within the same rank, by tier id so the ordering is stable
    across calls and byte-stable against :func:`tier_unlocks_batch`'s
    ordering. The trial tier is excluded (mirrors :func:`tier_locks`,
    which returns ``None`` for non-purchasable tiers); the ceiling
    tier (:data:`TIER_ENTERPRISE`) appears with ``next_tier=None`` and
    its marginal collapses to empty loss lists -- same shape the
    singular helper returns.

    Same-rank tiers (e.g. ``TIER_CLOUD_PRO`` and ``TIER_PRO`` both at
    rank 2) are both returned, since callers may key off the tier id
    rather than the rank. Consumers that want a deduped pricing ladder
    can drop duplicates by ``tier_rank``.

    Never raises: if the resolver blows up the helper returns ``[]``
    so the UI keeps rendering instead of 500-ing.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = tier_locks(tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_locks_batch failed: %s", exc)
        return []


def _locks_row(from_tier: str, to_tier: str) -> dict | None:
    """Single marginal-locks row between two arbitrary tiers, with the
    source carried as ``next_tier`` (path-chained, **not** the global
    next-higher-purchasable-tier anchor used by :func:`tier_locks`).

    Private builder for :func:`tier_locks_path`: each row is "what the
    ``to`` rung first *loses* vs the previous step in the walked path"
    so a consumer can fold the per-rung rows to reconstruct the
    cumulative ``tier_diff(from, to)['lost_*']`` shape -- the marginal-
    loss mirror of :func:`_unlocks_row` (which folds to
    ``tier_diff(...)['added_*']``).

    Returns ``None`` on unknown ids and never raises -- the path walker
    drops ``None`` rows on the floor so a downgrade-warning surface
    keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        from_feats = FREE_FEATURES | _TIER_FEATURES.get(f, frozenset())
        if f == TIER_ENTERPRISE:
            from_feats = from_feats | ENTERPRISE_FEATURES
        to_feats = FREE_FEATURES | _TIER_FEATURES.get(t, frozenset())
        if t == TIER_ENTERPRISE:
            to_feats = to_feats | ENTERPRISE_FEATURES
        from_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if f in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        to_runtimes = (
            FREE_RUNTIMES | PAID_RUNTIMES
            if t in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        return {
            "tier": t,
            "tier_label": tier_label(t),
            "tier_rank": tier_rank(t),
            "next_tier": f,
            "next_tier_label": tier_label(f),
            "next_tier_rank": tier_rank(f),
            "lost_features": sorted(from_feats - to_feats),
            "lost_runtimes": sorted(from_runtimes - to_runtimes),
        }
    except Exception as exc:
        logger.warning("entitlements: _locks_row failed: %s", exc)
        return None


def tier_locks_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise marginal-loss path between two tiers.

    Marginal-loss mirror of :func:`tier_unlocks_path` and the fourth
    member of the ``_path`` family alongside :func:`tier_path` (full
    ``tier_diff`` per rung), :func:`capacity_diff_path` (capacity-only
    per rung), and :func:`tier_unlocks_path` (marginal grant per rung).
    Lets a "downgrade-walkthrough" surface render only the *newly-lost*
    features + runtimes at each rung between any two tiers off ONE
    round-trip, without the noise of the capacity axes or the symmetric
    ``added_*`` lists :func:`tier_path` carries.

    Per-rung row shape matches :func:`tier_locks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes`` -- with
    one critical difference: ``next_tier`` is the **previous step in
    the walked path** (or ``from_tier`` for the first row), NOT the
    global "next-higher purchasable tier" anchor :func:`tier_locks`
    uses. The path-chained source guarantees
    ``row[i]['tier'] == row[i+1]['next_tier']`` so a consumer can fold
    ``lost_features`` / ``lost_runtimes`` across rows to reconstruct the
    cumulative ``tier_diff(from_tier, to_tier)['lost_*']`` shape -- the
    same chain-property :func:`tier_path`, :func:`capacity_diff_path`,
    and :func:`tier_unlocks_path` enforce on their rows.

    The walk visits every purchasable tier strictly between ``from_tier``
    and ``to_tier`` plus the destination ``to_tier`` itself, in tier-rank
    order (ascending or descending depending on direction). Same-rank
    siblings *between* the endpoints are both included (matching
    :func:`tier_path`'s ladder shape); same-rank siblings of the
    destination are excluded so the path terminates exactly at
    ``to_tier``. Rung walk is byte-stable against :func:`tier_path`,
    :func:`capacity_diff_path`, and :func:`tier_unlocks_path` (same
    ``_PURCHASABLE_TIERS`` filter + same sort key + same destination-
    sibling exclusion).

    Direction semantics:

    * ``downgrade`` (descending) -- each row's ``lost_features`` /
      ``lost_runtimes`` are the marginal loss at that rung. The natural
      "what do I give up if I drop this far" walkthrough.
    * ``upgrade`` (ascending) -- each row's ``lost_features`` /
      ``lost_runtimes`` are typically empty (you're gaining things, not
      losing them); use :func:`tier_unlocks_path` for the marginal-grant
      view of an upgrade. The path still walks rungs so a UI keyed off
      rung shape keeps working; the empty lists are the correct "locks"
      answer.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the set difference (``from`` minus ``to``) between the
      two same-rank tier grants.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`tier_unlocks_path`:
    both ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- it is excluded from
    the walked rungs but is a valid endpoint for the marginal-step
    computation). Unknown ids on either side short-circuit to ``None``.

    Never raises: a resolver failure logs a warning and returns ``None``
    so a downgrade-walkthrough surface keeps rendering.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            row = _locks_row(f, t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        prev_step = f
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = _locks_row(prev_step, tid)
            if row is not None:
                path.append(row)
                prev_step = tid
        return path
    except Exception as exc:
        logger.warning("entitlements: tier_locks_path failed: %s", exc)
        return None


def upgrade_path() -> list[dict]:
    """Ordered marginal-unlock ladder from the resolved tier upward.

    Where :func:`tier_unlocks` answers "what does tier X unlock vs the
    tier below it" for one named tier, ``upgrade_path`` answers "which
    tiers are still available to me, and what does each one unlock as I
    climb" -- the sequenced view an upgrade flow renders ("Starter adds
    these runtimes, then Pro adds these features, then Enterprise adds
    SSO + audit").

    Walks :data:`_PURCHASABLE_TIERS` sorted by ``(tier_rank, tier_id)``,
    filters to entries whose rank is strictly *greater* than the resolved
    entitlement's rank, and folds :func:`tier_unlocks` over each. Same-rank
    siblings (e.g. ``TIER_CLOUD_PRO`` and ``TIER_PRO`` both at rank 2) both
    appear so a caller keyed off the tier id keeps working; rank-deduped
    consumers can collapse by ``tier_rank`` client-side.

    The marginal stored on each row is :func:`tier_unlocks`'s answer (vs
    the absolute next-lower purchasable tier in the catalogue) -- *not*
    "vs the previous step in the path". So the union of the rows is
    direction-agnostic and matches the corresponding rows from a
    full-ladder ``tier_unlocks_batch``-style call, while the *selection*
    of rows is current-tier-relative.

    Returns an empty list when the resolved tier already sits at the top
    of the purchasable ladder (Enterprise), and never raises -- a resolver
    failure short-circuits to ``[]`` so an upgrade-CTA surface keeps
    rendering instead of breaking.
    """
    try:
        ent = get_entitlement()
        current_rank = _TIER_RANK.get(ent.tier, -1)
        ordered = sorted(
            _PURCHASABLE_TIERS,
            key=lambda t: (_TIER_RANK.get(t, -1), t),
        )
        path: list[dict] = []
        for tid in ordered:
            cand_rank = _TIER_RANK.get(tid, -1)
            if cand_rank <= current_rank:
                continue
            row = tier_unlocks(tid)
            if row is not None:
                path.append(row)
        return path
    except Exception as exc:
        logger.warning("entitlements: upgrade_path failed: %s", exc)
        return []


def downgrade_path() -> list[dict]:
    """Ordered cumulative-loss ladder from the resolved tier downward.

    Direction-flipped sibling of :func:`upgrade_path`: where the upgrade
    ladder walks purchasable tiers strictly *above* the caller and folds
    :func:`tier_unlocks` over each, this walks purchasable tiers strictly
    *below* the caller and folds :meth:`Entitlement.downgrade_diff` over
    each. The destination view a downgrade-warning CTA renders ("dropping
    to Starter loses claude_code + custom_alerts; dropping to Free also
    loses retention beyond 7 days and every paid runtime").

    Rows are sorted by ``(-tier_rank, tier_id)`` so the closest-to-current
    rung sits first and same-rank siblings (e.g. ``TIER_CLOUD_FREE`` and
    ``TIER_OSS`` both at rank 0) appear in stable lexicographic order. Each
    row is the ``downgrade_diff`` shape augmented with destination tier
    metadata + the caller's current-tier context::

        {
          "target":             "<tier id>",
          "target_label":       "<display>",
          "target_rank":        <int>,
          "current_tier":       "<resolved tier id>",
          "current_tier_label": "<display>",
          "current_tier_rank":  <int>,
          "lost_features":      [...],
          "lost_runtimes":      [...],
        }

    Cumulative not marginal: ``lost_features`` / ``lost_runtimes`` on each
    row reflect the *full* delta between the caller's resolved entitlement
    and that row's destination -- so the lists strictly grow as the path
    descends and consumers can render "if you drop to X, here's everything
    you'd lose" without summing rows client-side. The marginal-per-rung
    view (analogue of :func:`tier_unlocks`) is a separate future helper;
    this one mirrors :func:`upgrade_path`'s *selection* (current-tier-relative
    catalogue walk) rather than its *row shape*.

    Returns an empty list when the resolved tier already sits at the floor
    of the purchasable ladder (no rung below to descend to) and never raises
    -- a resolver failure short-circuits to ``[]`` so a downgrade-warning
    surface keeps rendering instead of breaking.
    """
    try:
        ent = get_entitlement()
        current_rank = _TIER_RANK.get(ent.tier, -1)
        current_label = tier_label(ent.tier)
        ordered = sorted(
            _PURCHASABLE_TIERS,
            key=lambda t: (-_TIER_RANK.get(t, -1), t),
        )
        path: list[dict] = []
        for tid in ordered:
            cand_rank = _TIER_RANK.get(tid, -1)
            if cand_rank < 0 or cand_rank >= current_rank:
                continue
            diff = ent.downgrade_diff(tid)
            path.append(
                {
                    "target": tid,
                    "target_label": tier_label(tid),
                    "target_rank": cand_rank,
                    "current_tier": ent.tier,
                    "current_tier_label": current_label,
                    "current_tier_rank": current_rank,
                    "lost_features": list(diff.get("lost_features") or []),
                    "lost_runtimes": list(diff.get("lost_runtimes") or []),
                }
            )
        return path
    except Exception as exc:
        logger.warning("entitlements: downgrade_path failed: %s", exc)
        return []


def resolution_diagnostic() -> dict:
    out: dict = {
        "license_path": _LICENSE_PATH,
        "license_present": False,
        "license_size_bytes": 0,
        "cloud_plan_path": _CLOUD_PLAN_CACHE,
        "cloud_plan_present": False,
        "cloud_plan_size_bytes": 0,
        "enforce_env": os.environ.get("CLAWMETRY_ENFORCE"),
        "is_enforced": False,
        "cache_age_seconds": None,
        "cache_ttl_seconds": _CACHE_TTL_SECS,
        "cache_hit_next_call": False,
        "cache_cached_tier": None,
        "retention_override_env_name": _RETENTION_OVERRIDE_ENV,
        "retention_override_env_value": os.environ.get(_RETENTION_OVERRIDE_ENV),
    }
    try:
        out["is_enforced"] = is_enforced()
    except Exception as exc:
        logger.warning("resolution_diagnostic: is_enforced failed: %s", exc)
    try:
        st = os.stat(_LICENSE_PATH)
        out["license_present"] = True
        out["license_size_bytes"] = int(st.st_size)
    except FileNotFoundError:
        pass
    except Exception as exc:
        out["license_error"] = str(exc)
    try:
        st = os.stat(_CLOUD_PLAN_CACHE)
        out["cloud_plan_present"] = True
        out["cloud_plan_size_bytes"] = int(st.st_size)
    except FileNotFoundError:
        pass
    except Exception as exc:
        out["cloud_plan_error"] = str(exc)
    try:
        with _lock:
            ts = float(_cache.get("ts") or 0.0)
            cached_ent = _cache.get("ent")
            cached_enforce = _cache.get("enforce")
        if ts > 0.0:
            age = max(0.0, time.time() - ts)
            out["cache_age_seconds"] = round(age, 3)
            out["cache_hit_next_call"] = (
                cached_ent is not None
                and cached_enforce == out["is_enforced"]
                and age < _CACHE_TTL_SECS
            )
            if cached_ent is not None:
                out["cache_cached_tier"] = getattr(cached_ent, "tier", None)
    except Exception as exc:
        out["cache_error"] = str(exc)
    return out


def available_runtimes() -> list[str]:
    ent = get_entitlement()
    if ent.grace:
        return sorted(ALL_RUNTIMES)
    return sorted(ent.runtimes)


def canonical_runtime(runtime: str) -> str:
    try:
        rt = (runtime or "").strip().lower()
    except Exception:
        return ""
    if not rt:
        return ""
    if rt in ALL_RUNTIMES:
        return rt
    return RUNTIME_ALIASES.get(rt, rt)


def runtime_label(runtime: str) -> str:
    rt = canonical_runtime(runtime)
    return RUNTIME_LABELS.get(rt, rt)


def runtime_tier(runtime: str) -> str:
    try:
        rt = (runtime or "").strip().lower()
    except (AttributeError, TypeError):
        return "starter"
    return "free" if rt in FREE_RUNTIMES else "starter"


def tier_label(tier: str) -> str:
    t = (tier or "").strip().lower()
    if not t:
        return TIER_LABELS[TIER_OSS]
    label = TIER_LABELS.get(t)
    if label is not None:
        return label
    return t.replace("_", " ").title()


def tier_rank(tier: str) -> int:
    """Comparable rank for ``tier`` (higher = unlocks more). Returns ``-1`` for
    unknown tiers. See :data:`_TIER_RANK` for the canonical numbering."""
    return _TIER_RANK.get((tier or "").strip().lower(), -1)


def next_purchasable_tier() -> str | None:
    try:
        return get_entitlement().next_purchasable_tier()
    except Exception as exc:
        logger.warning("entitlements: next_purchasable_tier (module) failed: %s", exc)
        return None


def previous_purchasable_tier() -> str | None:
    try:
        return get_entitlement().previous_purchasable_tier()
    except Exception as exc:
        logger.warning("entitlements: previous_purchasable_tier (module) failed: %s", exc)
        return None


def min_tier_for_feature(feature: str) -> str | None:
    f = (feature or "").strip().lower()
    if not f:
        return None
    if f in FREE_FEATURES:
        return TIER_OSS
    for tier in _PURCHASABLE_TIERS:
        if tier in (TIER_OSS, TIER_CLOUD_FREE):
            continue
        if f in _TIER_FEATURES.get(tier, frozenset()):
            return tier
    return None


def min_tier_for_runtime(runtime: str) -> str | None:
    rt = (runtime or "").strip().lower()
    if not rt:
        return None
    if rt in FREE_RUNTIMES:
        return TIER_OSS
    if rt in PAID_RUNTIMES:
        return TIER_CLOUD_STARTER
    return None


def _tier_row(tier: str) -> dict:
    return {
        "id": tier,
        "label": tier_label(tier),
        "rank": tier_rank(tier),
        "purchasable": tier in _PURCHASABLE_TIERS,
    }


def tiers_for_feature(feature: str) -> dict | None:
    """Inverse of :func:`min_tier_for_feature`: list **every** tier that
    grants ``feature`` (not just the cheapest one).

    Where ``min_tier_for_feature`` answers "what's the cheapest tier
    that unlocks X" -- a single id used by the upgrade-CTA -- this
    helper returns the full "Available in: Pro, Self-hosted Pro,
    Trial, Enterprise" availability list a pricing-page row or
    feature tooltip renders. Walks :data:`_TIER_ORDER` so the
    promotional ``trial`` tier appears alongside the purchasable
    plans (each row carries ``purchasable`` so the UI can dim or
    badge it).

    Rows are sorted by ``(tier_rank, tier_id)`` for stable output.
    ``min_tier`` matches :func:`min_tier_for_feature` (trial
    excluded -- not a plan a customer picks).

    Returns ``None`` for empty / unknown feature ids and never raises.
    """
    try:
        f = (feature or "").strip().lower()
        if not f or f not in ALL_FEATURES:
            return None
        carriers: list[str] = []
        for tier in _TIER_ORDER:
            paid_feats = _TIER_FEATURES.get(tier, frozenset())
            if f in FREE_FEATURES or f in paid_feats:
                carriers.append(tier)
        rows = [
            _tier_row(t)
            for t in sorted(carriers, key=lambda t: (tier_rank(t), t))
        ]
        min_t = min_tier_for_feature(f)
        return {
            "item": f,
            "kind": "feature",
            "label": feature_label(f),
            "free": f in FREE_FEATURES,
            "min_tier": min_t,
            "min_tier_label": tier_label(min_t) if min_t else None,
            "min_tier_rank": tier_rank(min_t) if min_t else None,
            "tiers": rows,
        }
    except Exception as exc:
        logger.warning("entitlements: tiers_for_feature failed: %s", exc)
        return None


def tiers_for_runtime(runtime: str) -> dict | None:
    """Inverse of :func:`min_tier_for_runtime`: list every tier that
    grants ``runtime``.

    FREE_RUNTIMES are granted at every tier in :data:`_TIER_ORDER`;
    PAID_RUNTIMES are granted at every tier in
    :data:`_TIER_PAID_RUNTIMES` (trial, starter, cloud_pro, self-hosted
    pro, enterprise). Rows sorted ``(rank, id)``; trial appears
    alongside purchasable plans with ``purchasable=False`` so the UI
    can render it as a separate promotional badge.

    Returns ``None`` for empty / unknown runtime ids and never raises.
    Accepts the canonical id (``claude_code``) or any registered alias
    (``claude-code``).
    """
    try:
        rt = canonical_runtime(runtime)
        if not rt or rt not in ALL_RUNTIMES:
            return None
        carriers: list[str] = []
        is_free = rt in FREE_RUNTIMES
        is_paid = rt in PAID_RUNTIMES
        for tier in _TIER_ORDER:
            if is_free:
                carriers.append(tier)
            elif is_paid and tier in _TIER_PAID_RUNTIMES:
                carriers.append(tier)
        rows = [
            _tier_row(t)
            for t in sorted(carriers, key=lambda t: (tier_rank(t), t))
        ]
        min_t = min_tier_for_runtime(rt)
        return {
            "item": rt,
            "kind": "runtime",
            "label": runtime_label(rt),
            "free": is_free,
            "min_tier": min_t,
            "min_tier_label": tier_label(min_t) if min_t else None,
            "min_tier_rank": tier_rank(min_t) if min_t else None,
            "tiers": rows,
        }
    except Exception as exc:
        logger.warning("entitlements: tiers_for_runtime failed: %s", exc)
        return None


def tiers_for_batch() -> dict:
    """Full availability ladder for every known feature *and* runtime in
    one pass. Plural sibling of :func:`tiers_for_feature` /
    :func:`tiers_for_runtime` and the inverse of the existing
    ``min_tier_for_*`` resolvers: where the singular helpers answer
    "which tiers grant *this* item" one id at a time -- the shape a
    pricing-page row uses -- the batch returns the same row shape for
    every entry in :data:`ALL_FEATURES` and :data:`ALL_RUNTIMES` so a
    pricing-table or feature-comparison matrix UI can render the full
    "Available in X" grid off **one** round-trip instead of an N+1
    fan-out across ``/api/entitlement/tiers-for``.

    Response shape::

        {
          "features": [<tiers_for_feature row>, ...],
          "runtimes": [<tiers_for_runtime row>, ...],
        }

    Feature rows are sorted by ``(feature_tier_rank, id)`` so the free
    surface appears first, then Starter, Pro, Enterprise -- the same
    order :func:`feature_catalog` uses, so a UI that joins the two
    surfaces (catalog row + availability ladder) sees a consistent
    ordering. Runtime rows put :data:`FREE_RUNTIMES` first (alpha
    within), then :data:`PAID_RUNTIMES` (alpha within), mirroring
    :func:`runtime_catalog`.

    Each row matches its singular helper exactly (``item``, ``kind``,
    ``label``, ``free``, ``min_tier``, ``min_tier_label``,
    ``min_tier_rank``, ``tiers``) so callers can pass a row to existing
    components without reshaping. Aliases (``custom_alerts``,
    ``alert_webhooks``, ``anomaly_detection``, ``cost_optimizer``) are
    surfaced alongside their canonical features -- they each carry a
    distinct id used by the dashboard, and the catalog already lists
    them.

    Never raises: if the resolver blows up the helper returns
    ``{"features": [], "runtimes": []}`` so the pricing UI keeps
    rendering instead of 500-ing.
    """
    try:
        features: list[dict] = []
        for fid in sorted(
            ALL_FEATURES,
            key=lambda f: (_FEATURE_TIER_RANK.get(feature_tier(f), 9), f),
        ):
            row = tiers_for_feature(fid)
            if row is not None:
                features.append(row)
        runtimes: list[dict] = []
        for rt in sorted(FREE_RUNTIMES):
            row = tiers_for_runtime(rt)
            if row is not None:
                runtimes.append(row)
        for rt in sorted(PAID_RUNTIMES):
            row = tiers_for_runtime(rt)
            if row is not None:
                runtimes.append(row)
        return {"features": features, "runtimes": runtimes}
    except Exception as exc:
        logger.warning("entitlements: tiers_for_batch failed: %s", exc)
        return {"features": [], "runtimes": []}


def min_tier_for_channel_count(count: int) -> str | None:
    """Return the cheapest *purchasable* tier id whose channel-adapter cap fits
    ``count`` configured channels. Closes the symmetry gap with
    :func:`min_tier_for_feature` / :func:`min_tier_for_runtime` so the lock
    affordance on the channels surface ("you have 5 channels -- Available in
    Starter") reads from the same single source of truth.

    Walks :data:`_PURCHASABLE_TIERS` (cheapest -> most capable, trial excluded
    -- it is a promotional grant, not a plan a customer can pick from a price
    page) and returns the first tier whose ``_TIER_CHANNEL_LIMIT`` value is
    either ``None`` (unlimited) or ``>= count``.

    Semantics:

    * ``count <= 0`` -- collapses to :data:`TIER_OSS`. A zero/negative count is
      either "not measured yet" or trivially satisfied; either way the free
      floor covers it (matches :meth:`Entitlement.allows_channel_count`'s
      grace-on-zero contract).
    * Non-int ``count`` -- returns ``None`` so a caller can distinguish "free"
      from "couldn't parse". Never raises.
    * Otherwise -- the first tier whose cap admits ``count``, falling back to
      :data:`TIER_ENTERPRISE` if every finite cap is exceeded (Enterprise is
      unlimited, so this is always a safe ceiling).
    """
    try:
        n = int(count)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return TIER_OSS
    for tier in _PURCHASABLE_TIERS:
        cap = _TIER_CHANNEL_LIMIT.get(tier, _FREE_CHANNEL_LIMIT)
        if cap is None or n <= cap:
            return tier
    return TIER_ENTERPRISE


def min_tier_for_retention_window(days: int | None) -> str | None:
    """Return the cheapest *purchasable* tier id whose event-retention cap fits
    a ``days`` history window. Companion to :func:`min_tier_for_channel_count`
    so the history-range toggle ("7 / 30 / 90 / all") can render "Available in
    <tier>" copy off the same canonical reverse lookup the other gates use.

    Walks :data:`_PURCHASABLE_TIERS` (cheapest -> most capable, trial excluded)
    and returns the first tier whose ``_TIER_RETENTION_DAYS`` value either
    matches the unlimited request (``days is None``) or admits the finite
    window.

    Semantics:

    * ``days is None`` (caller asked for unlimited history) -- returns the
      first tier whose cap is ``None``, i.e. :data:`TIER_ENTERPRISE`. Mirrors
      :meth:`Entitlement.allows_retention_window` which only grants ``None``
      to Enterprise.
    * ``days <= 0`` -- collapses to :data:`TIER_OSS`. Asking for zero history
      is trivially satisfied by the free floor (same posture as
      :meth:`Entitlement.allows_retention_window`).
    * Non-int ``days`` (other than the explicit ``None``) -- returns ``None``
      so a caller can distinguish "free" from "couldn't parse". Never raises.
    * Otherwise -- the first tier whose cap admits ``days``, falling back to
      :data:`TIER_ENTERPRISE` if every finite cap is exceeded.
    """
    if days is None:
        for tier in _PURCHASABLE_TIERS:
            if _TIER_RETENTION_DAYS.get(tier, 7) is None:
                return tier
        return TIER_ENTERPRISE
    try:
        n = int(days)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return TIER_OSS
    for tier in _PURCHASABLE_TIERS:
        cap = _TIER_RETENTION_DAYS.get(tier, 7)
        if cap is None or n <= cap:
            return tier
    return TIER_ENTERPRISE


def min_tier_for_node_count(count: int) -> str | None:
    """Return the cheapest *purchasable* tier id whose node-count cap admits
    ``count`` registered nodes. Closes the fourth axis (alongside
    :func:`min_tier_for_feature` / :func:`min_tier_for_runtime` /
    :func:`min_tier_for_channel_count` / :func:`min_tier_for_retention_window`)
    so the fleet-page upgrade affordance ("you have 4 nodes -- Available in
    Starter") reads from the same single source of truth.

    Walks :data:`_PURCHASABLE_TIERS` (cheapest -> most capable, trial excluded
    -- it is a promotional grant, not a plan a customer can pick from a price
    page) and returns the first tier whose ``_TIER_NODE_LIMIT`` value is either
    ``None`` (unlimited) or ``>= count``.

    Semantics mirror :func:`min_tier_for_channel_count` exactly so the four
    capacity axes are interchangeable from the caller's perspective:

    * ``count <= 0`` -- collapses to :data:`TIER_OSS`. A zero/negative count is
      either "no nodes registered yet" or trivially satisfied; either way the
      free floor covers it (matches :meth:`Entitlement.allows_node_count`'s
      grace-on-zero contract).
    * Non-int ``count`` -- returns ``None`` so a caller can distinguish "free"
      from "couldn't parse". Never raises.
    * Otherwise -- the first tier whose cap admits ``count``, falling back to
      :data:`TIER_ENTERPRISE` if every finite cap is exceeded (Enterprise is
      unlimited, so this is always a safe ceiling).
    """
    try:
        n = int(count)
    except (TypeError, ValueError):
        return None
    if n <= 0:
        return TIER_OSS
    for tier in _PURCHASABLE_TIERS:
        cap = _TIER_NODE_LIMIT.get(tier, _FREE_NODE_LIMIT)
        if cap is None or n <= cap:
            return tier
    return TIER_ENTERPRISE


def min_tier_for_features(features) -> str | None:
    """Cheapest *purchasable* tier admitting **all** ``features`` at once.

    Plural sibling of :func:`min_tier_for_feature`. A dashboard wiring "you
    are using fleet + otel_export + sso -- Available in Enterprise" has to
    resolve the most-constraining feature in the set; this helper folds the
    per-item lookups + max-by-rank in one place so callers don't reinvent
    the walk (and so all five capacity axes look symmetric from the caller's
    side: feature/runtime singular + features/runtimes plural).

    Semantics:

    * Empty / ``None`` iterable -- returns ``None``. "I asked for nothing"
      has no upgrade target, distinct from "I asked for free features"
      (which returns :data:`TIER_OSS`). Same posture as the singular helper
      returning ``None`` for empty input.
    * Unknown items contribute nothing -- they are skipped, not treated as
      a constraint, so a typo doesn't silently mis-route to Enterprise. If
      **every** item is unknown / empty, the helper returns ``None``.
    * All-known-free items -- returns :data:`TIER_OSS` (same as the singular
      free-feature path).
    * Mixed -- returns the highest-rank ``min_tier_for_feature`` across the
      set (the most-constraining feature wins).
    * Non-iterable input -- returns ``None``. Never raises.
    """
    try:
        if features is None:
            return None
        items = list(features)
    except TypeError:
        return None
    tiers: list[str] = []
    for f in items:
        t = min_tier_for_feature(f)
        if t is not None:
            tiers.append(t)
    if not tiers:
        return None
    return max(tiers, key=tier_rank)


def min_tier_for_runtimes(runtimes) -> str | None:
    """Cheapest *purchasable* tier admitting **all** ``runtimes`` at once.

    Plural sibling of :func:`min_tier_for_runtime`. Today every paid runtime
    unlocks at :data:`TIER_CLOUD_STARTER`, so for a set containing any paid
    runtime the answer is always Starter -- but the helper is provided for
    API symmetry with :func:`min_tier_for_features` (so a caller batching
    feature+runtime asks reads off one shape) and to stay correct if the
    paid-runtime tier mapping ever becomes per-runtime.

    Semantics mirror :func:`min_tier_for_features` exactly:

    * Empty / ``None`` iterable -- returns ``None``.
    * Unknown items contribute nothing (skipped); all-unknown -- ``None``.
    * All-free items -- :data:`TIER_OSS`.
    * Mixed -- the highest-rank ``min_tier_for_runtime`` across the set.
    * Non-iterable input -- ``None``. Never raises.
    """
    try:
        if runtimes is None:
            return None
        items = list(runtimes)
    except TypeError:
        return None
    tiers: list[str] = []
    for rt in items:
        t = min_tier_for_runtime(rt)
        if t is not None:
            tiers.append(t)
    if not tiers:
        return None
    return max(tiers, key=tier_rank)


def min_tier_for_all(
    *,
    features=None,
    runtimes=None,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> str | None:
    """Cheapest *purchasable* tier admitting **all** supplied constraints at
    once across every capacity axis.

    Aggregate sibling of :func:`min_tier_for_features` /
    :func:`min_tier_for_runtimes` / :func:`min_tier_for_channel_count` /
    :func:`min_tier_for_retention_window` / :func:`min_tier_for_node_count`.
    A dashboard surface that mixes axes ("fleet + claude_code + 5 channels +
    30-day retention + 2 nodes -- what tier covers everything?") gets a
    single tier id back instead of N round-trips + max-by-rank on the client.

    The capacity axes use ``None`` as the "axis not supplied" sentinel so a
    caller can omit any subset and the helper just skips them. Critically,
    ``retention_days=None`` here means *unset*, NOT *unlimited* -- asking
    for the unlimited-retention tier is the singular
    :func:`min_tier_for_retention_window` (``days=None``) call's job and
    would mis-route the aggregate to Enterprise.

    Semantics mirror the plural helpers exactly:

    * No constraints supplied -- returns ``None`` (matches the "nothing
      asked" posture of the plural helpers).
    * Any axis collapses to ``None`` (empty iterable / non-int / all-
      unknown items) -- that axis contributes nothing, the result is
      resolved off the remaining axes.
    * All axes collapse to ``None`` -- returns ``None``.
    * Otherwise -- the highest-rank tier across the per-axis answers (the
      most-constraining axis wins).
    * Never raises.
    """
    try:
        tiers: list[str] = []
        if features is not None:
            t = min_tier_for_features(features)
            if t is not None:
                tiers.append(t)
        if runtimes is not None:
            t = min_tier_for_runtimes(runtimes)
            if t is not None:
                tiers.append(t)
        if channels is not None:
            t = min_tier_for_channel_count(channels)
            if t is not None:
                tiers.append(t)
        if retention_days is not None:
            t = min_tier_for_retention_window(retention_days)
            if t is not None:
                tiers.append(t)
        if nodes is not None:
            t = min_tier_for_node_count(nodes)
            if t is not None:
                tiers.append(t)
        if not tiers:
            return None
        return max(tiers, key=tier_rank)
    except Exception as exc:
        logger.warning("entitlements: min_tier_for_all failed: %s", exc)
        return None


def affordable_tiers(
    *,
    features=None,
    runtimes=None,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> list[dict] | None:
    """Every *purchasable* tier admitting **all** supplied constraints, ordered
    by rank ascending.

    Plural sibling of :func:`min_tier_for_all` (which returns only the floor).
    Same arg shape, same per-axis ``None`` "not supplied" sentinels, same
    never-raise contract. Lets a pricing-page surface render "you need at
    least Starter; Pro and Enterprise also qualify" off ONE round-trip
    instead of resolving the floor and then walking the catalog client-side.

    Row schema (one per qualifying tier)::

        {
            "tier":       "<id>",
            "tier_label": "<human>",
            "tier_rank":  <int>,
            "is_minimum": <bool>,   # True on the first (cheapest) row only.
        }

    Ordering: ``tier_rank`` ascending, same-rank ties broken by tier id
    alphabetical so the row sequence is deterministic and byte-stable across
    invocations.

    Semantics mirror :func:`min_tier_for_all` exactly:

    * No constraints supplied -- returns ``None`` (matches the "nothing
      asked" posture of :func:`min_tier_for_all`).
    * Any axis collapses to ``None`` (empty iterable / non-int / all-unknown
      items) -- that axis contributes nothing, the floor is resolved off the
      remaining axes.
    * All axes collapse to ``None`` -- returns ``None``.
    * Otherwise -- the full list of purchasable tiers with rank ``>=`` the
      floor, ordered as above. ``TIER_TRIAL`` is intentionally excluded
      (matches every other path/batch helper, which walk ``_PURCHASABLE_TIERS``).
    * Never raises.

    Decoupled from the resolved entitlement so grace vs enforce yields
    identical lists -- this is the hypothetical "given these requirements,
    which tiers qualify" view, complementing the resolver-pinned
    :func:`min_tier_for_all` flow.
    """
    try:
        if (
            features is None
            and runtimes is None
            and channels is None
            and retention_days is None
            and nodes is None
        ):
            return None
        floor = min_tier_for_all(
            features=features,
            runtimes=runtimes,
            channels=channels,
            retention_days=retention_days,
            nodes=nodes,
        )
        if floor is None:
            return None
        floor_rank = tier_rank(floor)
        candidates = sorted(
            (t for t in _PURCHASABLE_TIERS if tier_rank(t) >= floor_rank),
            key=lambda t: (tier_rank(t), t),
        )
        out: list[dict] = []
        for idx, tier in enumerate(candidates):
            out.append(
                {
                    "tier": tier,
                    "tier_label": tier_label(tier),
                    "tier_rank": tier_rank(tier),
                    "is_minimum": idx == 0,
                }
            )
        return out
    except Exception as exc:
        logger.warning("entitlements: affordable_tiers failed: %s", exc)
        return None


def lock_reason(item: str, *, kind: str | None = None) -> str | None:
    try:
        return get_entitlement().lock_reason(item, kind=kind)
    except Exception:
        return None


def _normalise_csv(items) -> list[str]:
    if items is None:
        return []
    if isinstance(items, str):
        raw = items.split(",")
    else:
        try:
            raw = list(items)
        except TypeError:
            return []
    out: list[str] = []
    seen: set[str] = set()
    for tok in raw:
        try:
            s = str(tok).strip().lower()
        except Exception:
            continue
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _lock_row(ent, key: str, kind: str) -> dict:
    try:
        if kind == "feature":
            allowed = ent.allows_feature(key)
            required = min_tier_for_feature(key)
        elif kind == "runtime":
            allowed = ent.allows_runtime(key)
            required = min_tier_for_runtime(key)
        elif kind == "channels":
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": str(key),
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                }
            allowed = ent.allows_channel_count(n)
            required = min_tier_for_channel_count(n)
            key = str(n)
        elif kind == "retention_days":
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": str(key),
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                }
            allowed = ent.allows_retention_window(n)
            required = min_tier_for_retention_window(n)
            key = str(n)
        elif kind == "nodes":
            try:
                n = int(key)
            except (TypeError, ValueError):
                return {
                    "key": str(key),
                    "kind": kind,
                    "reason": None,
                    "locked": False,
                    "allowed": True,
                    "required_tier": None,
                    "required_tier_label": None,
                    "required_tier_rank": -1,
                }
            allowed = ent.allows_node_count(n)
            required = min_tier_for_node_count(n)
            key = str(n)
        else:
            allowed = True
            required = None
        reason = ent.lock_reason(key, kind=kind)
        return {
            "key": key,
            "kind": kind,
            "reason": reason,
            "locked": reason is not None,
            "allowed": allowed,
            "required_tier": required,
            "required_tier_label": tier_label(required) if required else None,
            "required_tier_rank": tier_rank(required) if required else -1,
        }
    except Exception:
        return {
            "key": str(key),
            "kind": kind,
            "reason": None,
            "locked": False,
            "allowed": True,
            "required_tier": None,
            "required_tier_label": None,
            "required_tier_rank": -1,
        }


def lock_reasons_batch(
    *,
    features=None,
    runtimes=None,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> dict:
    """Per-item lock reasons for every supplied item across all 5 axes in one
    pass.

    Plural sibling of :func:`lock_reason`. While
    :func:`min_tier_for_all` / ``/required-tier-batch`` collapse the answer to
    the single most-constraining tier, this helper preserves the per-item
    detail so a Settings or paywall matrix UI can render N rows with their
    individual reasons + per-row required tier off **one** call instead of N
    round-trips to ``/lock-reason``.

    Shape::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason`` (``None`` when not
    locked / unknown id / grace mode), ``locked``, ``allowed``,
    ``required_tier``, ``required_tier_label``, ``required_tier_rank``.

    The capacity axes (``channels`` / ``retention_days`` / ``nodes``) use
    ``None`` as the "axis not supplied" sentinel and the corresponding key
    in the returned dict is ``None``. Mirrors ``min_tier_for_all`` exactly:
    ``retention_days=None`` here means *unset*, NOT *unlimited*.

    Grace mode (the default until enforcement flips on): every row has
    ``reason=None`` / ``locked=False`` / ``allowed=True`` -- the helper does
    not invent locks. Never raises: a resolver failure short-circuits to the
    grace-shape rows so the UI keeps rendering.
    """
    feats = _normalise_csv(features)
    rts = _normalise_csv(runtimes)
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: lock_reasons_batch falling back to grace: %s", exc)
        ent = _oss_free()
    out: dict = {
        "features": [_lock_row(ent, f, "feature") for f in feats],
        "runtimes": [_lock_row(ent, r, "runtime") for r in rts],
        "channels": _lock_row(ent, channels, "channels") if channels is not None else None,
        "retention_days": (
            _lock_row(ent, retention_days, "retention_days")
            if retention_days is not None
            else None
        ),
        "nodes": _lock_row(ent, nodes, "nodes") if nodes is not None else None,
    }
    return out


def feature_label(feature: str) -> str:
    fid = (feature or "").strip().lower()
    return FEATURE_LABELS.get(fid, fid)


_FEATURE_TIER_ORDER = (
    (TIER_OSS, FREE_FEATURES),
    (TIER_CLOUD_STARTER, STARTER_FEATURES),
    (TIER_CLOUD_PRO, PRO_ONLY_FEATURES),
    (TIER_ENTERPRISE, ENTERPRISE_FEATURES),
)


def feature_tier(feature: str) -> str:
    fid = (feature or "").strip().lower()
    for tier, bucket in _FEATURE_TIER_ORDER:
        if fid in bucket:
            return tier
    return TIER_OSS


_FEATURE_TIER_RANK = {
    TIER_OSS: 0,
    TIER_CLOUD_STARTER: 1,
    TIER_CLOUD_PRO: 2,
    TIER_ENTERPRISE: 3,
}


def _feature_tier_ids(feature: str) -> list[str]:
    """Compact id-only sibling of :func:`tiers_for_feature` (just the
    ladder of tier ids that grant ``feature``). Used to enrich the
    feature catalog row so a matrix UI doesn't need a per-row roundtrip
    to ``/api/entitlement/tiers-for`` to know which columns to tick."""
    body = tiers_for_feature(feature)
    if body is None:
        return []
    return [row["id"] for row in body.get("tiers", [])]


def _runtime_tier_ids(runtime: str) -> list[str]:
    """Compact id-only sibling of :func:`tiers_for_runtime`."""
    body = tiers_for_runtime(runtime)
    if body is None:
        return []
    return [row["id"] for row in body.get("tiers", [])]


def _feature_spec_row(ent: "Entitlement", fid: str) -> dict:
    """Build the single feature row shape that ``feature_catalog()`` and
    :func:`feature_spec` both return. Centralised so the scalar and bulk
    accessors cannot drift (a parity test pins this)."""
    tier = feature_tier(fid)
    is_free = fid in FREE_FEATURES
    allowed = ent.allows_feature(fid)
    if is_free:
        entitled = True
    elif ent.expired:
        entitled = False
    else:
        entitled = fid in ent.features
    return {
        "id": fid,
        "label": feature_label(fid),
        "tier": tier,
        "tiers": _feature_tier_ids(fid),
        "free": is_free,
        "allowed": allowed,
        "locked": (not is_free) and (not allowed),
        "entitled": entitled,
        "alias": fid in _ALIAS_FEATURES,
    }


def _runtime_spec_row(ent: "Entitlement", rt: str) -> dict:
    """Build the single runtime row shape that ``runtime_catalog()`` and
    :func:`runtime_spec` both return. Centralised so the scalar and bulk
    accessors cannot drift (a parity test pins this)."""
    if rt in FREE_RUNTIMES:
        return {
            "id": rt,
            "label": runtime_label(rt),
            "free": True,
            "tier": "free",
            "tiers": _runtime_tier_ids(rt),
            "allowed": True,
            "locked": False,
            "entitled": True,
        }
    allowed = ent.allows_runtime(rt)
    return {
        "id": rt,
        "label": runtime_label(rt),
        "free": False,
        "tier": "starter",
        "tiers": _runtime_tier_ids(rt),
        "allowed": allowed,
        "locked": not allowed,
        "entitled": ent.entitled_runtime(rt),
    }


def feature_catalog() -> list[dict]:
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: feature_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    return [
        _feature_spec_row(ent, fid)
        for fid in sorted(
            ALL_FEATURES,
            key=lambda f: (_FEATURE_TIER_RANK.get(feature_tier(f), 9), f),
        )
    ]


def runtime_catalog() -> list[dict]:
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: runtime_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    out: list[dict] = []
    for rt in sorted(FREE_RUNTIMES):
        out.append(_runtime_spec_row(ent, rt))
    for rt in sorted(PAID_RUNTIMES):
        out.append(_runtime_spec_row(ent, rt))
    return out


def feature_spec(feature: str) -> dict | None:
    """Scalar sibling of :func:`feature_catalog`: return the single
    catalogue row for ``feature`` (case-insensitive, trimmed), or
    ``None`` for empty / unknown ids.

    Lets a feature-detail page or upgrade tooltip hydrate against one
    feature in one round-trip instead of fetching the full catalogue
    and filtering client-side. The returned row matches a row from
    :func:`feature_catalog` exactly -- a parity test pins this.

    Never raises: on resolver failure the row is still built against
    the OSS-free fallback (matches the catalogue's never-crash
    contract)."""
    try:
        f = (feature or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not f or f not in ALL_FEATURES:
        return None
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: feature_spec falling back to grace: %s", exc)
        ent = _oss_free()
    try:
        return _feature_spec_row(ent, f)
    except Exception as exc:
        logger.warning("entitlements: feature_spec row build failed: %s", exc)
        return None


def runtime_spec(runtime: str) -> dict | None:
    """Scalar sibling of :func:`runtime_catalog`: return the single
    catalogue row for ``runtime`` (canonicalised via
    :func:`canonical_runtime`, so aliases like ``claude-code`` resolve
    to ``claude_code``), or ``None`` for empty / unknown ids.

    Lets a runtime-detail page or upgrade tooltip hydrate against one
    runtime in one round-trip instead of fetching the full catalogue
    and filtering client-side. The returned row matches a row from
    :func:`runtime_catalog` exactly -- a parity test pins this.

    Never raises: on resolver failure the row is still built against
    the OSS-free fallback (matches the catalogue's never-crash
    contract)."""
    rt = canonical_runtime(runtime)
    if not rt or rt not in ALL_RUNTIMES:
        return None
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: runtime_spec falling back to grace: %s", exc)
        ent = _oss_free()
    try:
        return _runtime_spec_row(ent, rt)
    except Exception as exc:
        logger.warning("entitlements: runtime_spec row build failed: %s", exc)
        return None


def feature_spec_batch(features) -> dict:
    """Plural sibling of :func:`feature_spec`: return spec rows for a
    caller-supplied subset of feature ids in one pass.

    Where :func:`feature_catalog` returns rows for *every* known feature,
    this lets a paywall matrix UI hydrate only the N rows it is about to
    render off **one** round-trip instead of N calls to
    ``/api/entitlement/feature-spec``. Each returned row is byte-identical
    to a row from :func:`feature_catalog` -- a parity test pins this so
    the scalar / bulk / batch accessors cannot drift.

    Shape::

        {
          "features": [<spec_row>, ...],   # one per known supplied id, in supply order
          "unknown":  ["bogus_id", ...],   # supplied ids not in ALL_FEATURES, in supply order
        }

    Supplied ids are normalised via :func:`_normalise_csv` (whitespace
    stripped, lowercased, duplicates dropped while preserving first-seen
    order) so the response is stable across repeated calls. Empty input
    returns ``{"features": [], "unknown": []}`` -- the HTTP wrapper turns
    that into a 400, this helper does not raise.

    Grace mode (the default until enforcement flips on): every row reports
    ``locked=False`` / ``allowed=True`` -- this helper does not invent
    locks. Never raises: a resolver failure short-circuits to the OSS-free
    fallback so the matrix keeps rendering.
    """
    feats = _normalise_csv(features)
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: feature_spec_batch falling back to grace: %s", exc)
        ent = _oss_free()
    rows: list[dict] = []
    unknown: list[str] = []
    for fid in feats:
        if fid in ALL_FEATURES:
            try:
                rows.append(_feature_spec_row(ent, fid))
            except Exception as exc:
                logger.warning(
                    "entitlements: feature_spec_batch row %r failed: %s", fid, exc
                )
                unknown.append(fid)
        else:
            unknown.append(fid)
    return {"features": rows, "unknown": unknown}


def runtime_spec_batch(runtimes) -> dict:
    """Plural sibling of :func:`runtime_spec`: return spec rows for a
    caller-supplied subset of runtime ids in one pass.

    Mirrors :func:`feature_spec_batch` for the runtime axis. Lets a
    runtime-matrix UI ("show me the lock state for the 4 runtimes
    detected on this node") hydrate off **one** round-trip instead of N
    calls to ``/api/entitlement/runtime-spec``. Each returned row is
    byte-identical to a row from :func:`runtime_catalog`.

    Supplied ids are normalised via :func:`_normalise_csv` and then
    canonicalised via :func:`canonical_runtime`, so aliases (``claude-code``
    -> ``claude_code``) resolve the same way they do on
    ``/api/entitlement/runtime-spec``. Duplicates that collapse after
    aliasing (e.g. ``claude-code,claude_code``) only contribute one row;
    later aliases that already mapped to a seen canonical id drop into
    the response in their first-seen position.

    Shape::

        {
          "runtimes": [<spec_row>, ...],   # one per known supplied id, in (canonical) first-seen order
          "unknown":  ["bogus_id", ...],   # supplied ids not in ALL_RUNTIMES after canonicalisation
        }

    Grace mode (the default until enforcement flips on): every row reports
    ``locked=False`` / ``allowed=True``. Never raises: a resolver failure
    short-circuits to the OSS-free fallback so the matrix keeps rendering.
    """
    rts = _normalise_csv(runtimes)
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: runtime_spec_batch falling back to grace: %s", exc)
        ent = _oss_free()
    rows: list[dict] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for raw in rts:
        rt = canonical_runtime(raw)
        if rt and rt in ALL_RUNTIMES:
            if rt in seen:
                continue
            seen.add(rt)
            try:
                rows.append(_runtime_spec_row(ent, rt))
            except Exception as exc:
                logger.warning(
                    "entitlements: runtime_spec_batch row %r failed: %s", rt, exc
                )
                unknown.append(raw)
        else:
            unknown.append(raw)
    return {"runtimes": rows, "unknown": unknown}


def tier_catalog() -> list[dict]:
    try:
        ent = get_entitlement()
        current = ent.tier
    except Exception as exc:
        logger.warning("entitlements: tier_catalog falling back to OSS-free: %s", exc)
        current = TIER_OSS
    out: list[dict] = []
    paid_runtimes_sorted = sorted(PAID_RUNTIMES)
    for rank, tier in enumerate(_TIER_ORDER):
        paid_feats = _TIER_FEATURES.get(tier, frozenset())
        unlocks_paid = tier in _TIER_PAID_RUNTIMES
        out.append(
            {
                "id": tier,
                "label": tier_label(tier),
                "is_paid": tier in _PAID_TIERS,
                "is_current": tier == current,
                "rank": rank,
                "unlocks_paid_runtimes": unlocks_paid,
                "retention_days": _TIER_RETENTION_DAYS.get(tier, 7),
                "channel_limit": _TIER_CHANNEL_LIMIT.get(tier, _FREE_CHANNEL_LIMIT),
                "node_limit": _TIER_NODE_LIMIT.get(tier, _FREE_NODE_LIMIT),
                "features": sorted(paid_feats),
                "runtimes": list(paid_runtimes_sorted) if unlocks_paid else [],
            }
        )
    return out


def _hypothetical_entitlement(tier: str) -> "Entitlement":
    """Build an enforce-mode :class:`Entitlement` for a hypothetical ``tier``.

    Backs :func:`feature_catalog_at` / :func:`runtime_catalog_at`: synthesises
    the feature + runtime sets the resolver would have produced if the install
    were on ``tier`` today, without touching the live resolved entitlement
    (and without caching it -- callers always get a fresh row from the static
    constant tables). ``grace`` is forced off so ``allowed`` actually reflects
    the per-tier feature/runtime grant; a grace-on row would report everything
    allowed and defeat the what-if purpose.
    """
    paid_feats = _TIER_FEATURES.get(tier, frozenset())
    rts = (FREE_RUNTIMES | PAID_RUNTIMES) if tier in _TIER_PAID_RUNTIMES else FREE_RUNTIMES
    return Entitlement(
        tier=tier,
        source="hypothetical",
        node_limit=1,
        expiry=None,
        features=FREE_FEATURES | paid_feats,
        runtimes=rts,
        grace=False,
    )


def feature_catalog_at(tier: str) -> list[dict] | None:
    """What-if sibling of :func:`feature_catalog`: catalog rows with the
    ``allowed`` / ``locked`` / ``entitled`` fields computed as if the install
    were on ``tier``.

    The row shape is identical to :func:`feature_catalog` (same keys, same
    ordering) so a pricing-comparison UI can swap between "current state" and
    "if I were on Pro" without reshaping anything client-side. Catalogue-
    derived fields (``id``, ``label``, ``tier``, ``tiers``, ``free``,
    ``alias``) are unchanged; the resolution-dependent fields are recomputed
    against a synthetic Entitlement built off the static per-tier feature
    grant in :data:`_TIER_FEATURES`.

    Returns ``None`` for empty / unknown tier ids (caller renders "unknown
    tier" / 404). Never raises: a synthesis failure short-circuits to the
    OSS-free fallback so the catalogue still renders.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: feature_catalog_at falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    out: list[dict] = []
    for fid in sorted(
        ALL_FEATURES,
        key=lambda f: (_FEATURE_TIER_RANK.get(feature_tier(f), 9), f),
    ):
        ftier = feature_tier(fid)
        is_free = fid in FREE_FEATURES
        allowed = ent.allows_feature(fid)
        if is_free:
            entitled = True
        elif ent.expired:
            entitled = False
        else:
            entitled = fid in ent.features
        out.append(
            {
                "id": fid,
                "label": feature_label(fid),
                "tier": ftier,
                "tiers": _feature_tier_ids(fid),
                "free": is_free,
                "allowed": allowed,
                "locked": (not is_free) and (not allowed),
                "entitled": entitled,
                "alias": fid in _ALIAS_FEATURES,
            }
        )
    return out


def runtime_catalog_at(tier: str) -> list[dict] | None:
    """What-if sibling of :func:`runtime_catalog`: catalog rows with the
    ``allowed`` / ``locked`` / ``entitled`` fields computed as if the install
    were on ``tier``.

    Mirrors :func:`feature_catalog_at` for runtimes -- same row shape as
    :func:`runtime_catalog`, same ordering (free runtimes first, then paid,
    alpha within each bucket). Accepts canonical ids; tier alias resolution
    via the standard trim+lowercase pipeline matches :func:`tier_spec`.

    Returns ``None`` for empty / unknown tier ids and never raises (a
    synthesis failure short-circuits to the OSS-free fallback).
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: runtime_catalog_at falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    out: list[dict] = []
    for rt in sorted(FREE_RUNTIMES):
        out.append(
            {
                "id": rt,
                "label": runtime_label(rt),
                "free": True,
                "tier": "free",
                "tiers": _runtime_tier_ids(rt),
                "allowed": True,
                "locked": False,
                "entitled": True,
            }
        )
    for rt in sorted(PAID_RUNTIMES):
        allowed = ent.allows_runtime(rt)
        out.append(
            {
                "id": rt,
                "label": runtime_label(rt),
                "free": False,
                "tier": "starter",
                "tiers": _runtime_tier_ids(rt),
                "allowed": allowed,
                "locked": not allowed,
                "entitled": ent.entitled_runtime(rt),
            }
        )
    return out


def tier_spec(tier: str) -> dict | None:
    """Scalar variant of :func:`tier_catalog`: full descriptor for a single
    tier in one shot.

    Catalogue-derived, user-context-free — the answer is identical in grace
    and enforce mode and does not depend on the resolved entitlement. The
    only resolution-dependent field is ``is_current`` (whether *this* install
    is on the named tier today); resolution failures degrade to
    ``is_current=False`` so the row still renders.

    Returns ``None`` for empty / unknown tier ids (caller renders "unknown
    tier" / 404) and never raises.

    Each entry mirrors a row from ``tier_catalog`` exactly so a pricing-page
    column can be hydrated off one round-trip instead of fetching the full
    catalogue and filtering client-side::

        {
          "id":                     "<tier>",       # canonical key
          "label":                  "<Display>",    # falls back to titlecased id
          "is_paid":                bool,           # _PAID_TIERS membership
          "is_current":             bool,           # this install's resolved tier
          "rank":                   int,            # tier_rank() value (>=0)
          "unlocks_paid_runtimes":  bool,           # PAID_RUNTIMES granted at this tier
          "retention_days":         int | None,     # None = unlimited (Enterprise)
          "channel_limit":          int,
          "node_limit":             int,
          "features":               [<id>, ...],    # paid features carried (free always granted on top)
          "runtimes":               [<id>, ...],    # PAID_RUNTIMES carried, [] when unlocks_paid_runtimes is False
        }
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        ent = get_entitlement()
        current = ent.tier
    except Exception as exc:
        logger.warning("entitlements: tier_spec falling back to OSS-free: %s", exc)
        current = TIER_OSS
    paid_feats = _TIER_FEATURES.get(t, frozenset())
    unlocks_paid = t in _TIER_PAID_RUNTIMES
    paid_runtimes_sorted = sorted(PAID_RUNTIMES)
    return {
        "id": t,
        "label": tier_label(t),
        "is_paid": t in _PAID_TIERS,
        "is_current": t == current,
        "rank": _TIER_ORDER.index(t),
        "unlocks_paid_runtimes": unlocks_paid,
        "retention_days": _TIER_RETENTION_DAYS.get(t, 7),
        "channel_limit": _TIER_CHANNEL_LIMIT.get(t, _FREE_CHANNEL_LIMIT),
        "node_limit": _TIER_NODE_LIMIT.get(t, _FREE_NODE_LIMIT),
        "features": sorted(paid_feats),
        "runtimes": list(paid_runtimes_sorted) if unlocks_paid else [],
    }


def tier_catalog_at(tier: str) -> list[dict] | None:
    """What-if sibling of :func:`tier_catalog`: the full tier ladder with
    ``is_current`` recomputed as if the install were on ``tier`` instead of
    the live resolved entitlement.

    The row shape, ordering, and every other field are identical to
    :func:`tier_catalog` (catalogue-derived, user-context-free) -- only the
    ``is_current`` flag shifts. Lets a pricing-comparison UI render the
    same ladder as :func:`tier_catalog` from the perspective of any
    hypothetical tier without first switching the live resolver.

    Returns ``None`` for empty / unknown tier ids (caller renders "unknown
    tier" / 404). Never raises: a catalogue failure short-circuits to the
    OSS-floor view (ladder with ``is_current`` pinned on :data:`TIER_OSS`)
    so the surface still renders.

    Companion to :func:`feature_catalog_at` / :func:`runtime_catalog_at`
    (which recompute the catalogue's resolution-dependent fields against a
    hypothetical Entitlement). This one only needs to flip the
    ``is_current`` boolean -- every other field on a tier row is already
    catalogue-derived -- so it shares the static per-tier maps with
    :func:`tier_catalog` rather than synthesising a full
    :class:`Entitlement`.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    out: list[dict] = []
    paid_runtimes_sorted = sorted(PAID_RUNTIMES)
    for rank, tid in enumerate(_TIER_ORDER):
        paid_feats = _TIER_FEATURES.get(tid, frozenset())
        unlocks_paid = tid in _TIER_PAID_RUNTIMES
        out.append(
            {
                "id": tid,
                "label": tier_label(tid),
                "is_paid": tid in _PAID_TIERS,
                "is_current": tid == t,
                "rank": rank,
                "unlocks_paid_runtimes": unlocks_paid,
                "retention_days": _TIER_RETENTION_DAYS.get(tid, 7),
                "channel_limit": _TIER_CHANNEL_LIMIT.get(tid, _FREE_CHANNEL_LIMIT),
                "node_limit": _TIER_NODE_LIMIT.get(tid, _FREE_NODE_LIMIT),
                "features": sorted(paid_feats),
                "runtimes": list(paid_runtimes_sorted) if unlocks_paid else [],
            }
        )
    return out


def tier_spec_at(tier: str, target: str) -> dict | None:
    """Scalar what-if sibling of :func:`tier_catalog_at`: the single tier
    descriptor for ``target`` with ``is_current`` computed as if the install
    were on ``tier``.

    Pairs with :func:`tier_spec` (scalar against the LIVE resolved
    entitlement) the same way :func:`tier_catalog_at` pairs with
    :func:`tier_catalog`. Lets a pricing-comparison tooltip hydrate against
    ONE tier descriptor from the perspective of a hypothetical install in
    one round-trip instead of fetching the full ``tier_catalog_at`` payload
    and filtering client-side.

    The returned row matches the row from :func:`tier_catalog_at` whose
    ``id == target`` exactly -- a parity test pins this so the scalar and
    bulk what-if accessors cannot drift. Catalogue-derived fields (``id``,
    ``label``, ``is_paid``, ``rank``, ``unlocks_paid_runtimes``,
    ``retention_days``, ``channel_limit``, ``node_limit``, ``features``,
    ``runtimes``) come straight from the static per-tier maps; only the
    ``is_current`` boolean shifts to reflect the hypothetical perspective.

    Returns ``None`` for empty / unknown ``tier`` or ``target`` ids (caller
    renders "unknown tier" / 404). Never raises: a catalogue failure short-
    circuits to the OSS-floor view (row with ``is_current=False``) so the
    surface still renders.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        g = (target or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not g or g not in _TIER_ORDER:
        return None
    paid_feats = _TIER_FEATURES.get(g, frozenset())
    unlocks_paid = g in _TIER_PAID_RUNTIMES
    paid_runtimes_sorted = sorted(PAID_RUNTIMES)
    return {
        "id": g,
        "label": tier_label(g),
        "is_paid": g in _PAID_TIERS,
        "is_current": g == t,
        "rank": _TIER_ORDER.index(g),
        "unlocks_paid_runtimes": unlocks_paid,
        "retention_days": _TIER_RETENTION_DAYS.get(g, 7),
        "channel_limit": _TIER_CHANNEL_LIMIT.get(g, _FREE_CHANNEL_LIMIT),
        "node_limit": _TIER_NODE_LIMIT.get(g, _FREE_NODE_LIMIT),
        "features": sorted(paid_feats),
        "runtimes": list(paid_runtimes_sorted) if unlocks_paid else [],
    }


def feature_spec_at(tier: str, feature: str) -> dict | None:
    """Scalar what-if sibling of :func:`feature_catalog_at`: the single
    catalogue row for ``feature`` with ``allowed`` / ``locked`` /
    ``entitled`` computed as if the install were on ``tier``.

    Pairs with :func:`feature_spec` (scalar against the LIVE resolved
    entitlement) the same way :func:`feature_catalog_at` pairs with
    :func:`feature_catalog`. Lets a pricing-comparison tooltip hydrate
    against ONE feature at a hypothetical tier in one round-trip instead
    of fetching the full ``feature_catalog_at`` payload and filtering
    client-side.

    The returned row matches a row from :func:`feature_catalog_at`
    exactly -- a parity test pins this so the scalar and bulk accessors
    cannot drift.

    Returns ``None`` for empty / unknown tier or feature ids (caller
    renders "unknown tier" / "unknown feature" / 404). Never raises: a
    synthesis failure short-circuits to the OSS-free fallback so the
    row still renders.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        f = (feature or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not f or f not in ALL_FEATURES:
        return None
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: feature_spec_at falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    try:
        return _feature_spec_row(ent, f)
    except Exception as exc:
        logger.warning("entitlements: feature_spec_at row build failed: %s", exc)
        return None


def runtime_spec_at(tier: str, runtime: str) -> dict | None:
    """Scalar what-if sibling of :func:`runtime_catalog_at`: the single
    catalogue row for ``runtime`` with ``allowed`` / ``locked`` /
    ``entitled`` computed as if the install were on ``tier``.

    Pairs with :func:`runtime_spec` (scalar against the LIVE resolved
    entitlement) the same way :func:`runtime_catalog_at` pairs with
    :func:`runtime_catalog`. Accepts aliases (``claude-code`` ->
    ``claude_code``) via :func:`canonical_runtime` so the URL surface
    matches what callers already pass to ``/api/entitlement/required-tier``.

    The returned row matches a row from :func:`runtime_catalog_at`
    exactly -- a parity test pins this so the scalar and bulk accessors
    cannot drift.

    Returns ``None`` for empty / unknown tier or runtime ids (caller
    renders "unknown tier" / "unknown runtime" / 404). Never raises: a
    synthesis failure short-circuits to the OSS-free fallback so the
    row still renders.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    rt = canonical_runtime(runtime)
    if not rt or rt not in ALL_RUNTIMES:
        return None
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: runtime_spec_at falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    try:
        return _runtime_spec_row(ent, rt)
    except Exception as exc:
        logger.warning("entitlements: runtime_spec_at row build failed: %s", exc)
        return None


def feature_spec_at_batch(tier: str, features) -> dict | None:
    """What-if + batch sibling of :func:`feature_spec_batch`: return spec
    rows for a caller-supplied subset of feature ids, with ``allowed`` /
    ``locked`` / ``entitled`` computed as if the install were on ``tier``.

    Composes :func:`feature_spec_at` (scalar what-if) and
    :func:`feature_spec_batch` (live batch) -- same shape as the batch
    helper, same hypothetical perspective as the ``_at`` helper. Lets a
    pricing-comparison matrix UI ("here is what 6 features look like on
    Cloud Pro") hydrate the N visible rows off ONE round-trip instead of
    N calls to :func:`feature_spec_at`.

    Each returned row is byte-identical to a row from
    :func:`feature_catalog_at` -- a parity test pins this so the scalar
    what-if (`feature_spec_at`) and bulk what-if (`feature_catalog_at`)
    and batch what-if accessors cannot drift.

    Shape::

        {
          "features": [<spec_row>, ...],   # one per known supplied id, in supply order
          "unknown":  ["bogus_id", ...],   # supplied ids not in ALL_FEATURES, in supply order
        }

    Returns ``None`` for empty / unknown ``tier`` (caller renders "unknown
    tier" / 404). Supplied feature ids are normalised via
    :func:`_normalise_csv`; an empty feature list returns
    ``{"features": [], "unknown": []}`` -- the HTTP wrapper turns that
    into a 400, this helper does not raise.

    Never raises: a synthesis failure short-circuits to the OSS-free
    fallback so the matrix keeps rendering.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    feats = _normalise_csv(features)
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: feature_spec_at_batch falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    rows: list[dict] = []
    unknown: list[str] = []
    for fid in feats:
        if fid in ALL_FEATURES:
            try:
                rows.append(_feature_spec_row(ent, fid))
            except Exception as exc:
                logger.warning(
                    "entitlements: feature_spec_at_batch row %r failed: %s",
                    fid,
                    exc,
                )
                unknown.append(fid)
        else:
            unknown.append(fid)
    return {"features": rows, "unknown": unknown}


def runtime_spec_at_batch(tier: str, runtimes) -> dict | None:
    """What-if + batch sibling of :func:`runtime_spec_batch`: return spec
    rows for a caller-supplied subset of runtime ids, with ``allowed`` /
    ``locked`` / ``entitled`` computed as if the install were on ``tier``.

    Mirrors :func:`feature_spec_at_batch` for the runtime axis; together
    they let a pricing-comparison matrix UI hydrate a viewport's worth
    of feature + runtime rows at a hypothetical tier off TWO calls
    instead of N + M.

    Aliases are canonicalised via :func:`canonical_runtime`
    (``claude-code`` -> ``claude_code``) and aliases that collapse to a
    canonical id already in the response are silently de-duplicated --
    same behaviour as :func:`runtime_spec_batch`.

    Each returned row is byte-identical to a row from
    :func:`runtime_catalog_at` (parity-pinned by the tests below).

    Shape::

        {
          "runtimes": [<spec_row>, ...],   # one per known supplied id, in (canonical) first-seen order
          "unknown":  ["bogus_id", ...],   # supplied ids not in ALL_RUNTIMES after canonicalisation
        }

    Returns ``None`` for empty / unknown ``tier``. Never raises: a
    synthesis failure short-circuits to the OSS-free fallback so the
    matrix keeps rendering.
    """
    try:
        t = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    rts = _normalise_csv(runtimes)
    try:
        ent = _hypothetical_entitlement(t)
    except Exception as exc:
        logger.warning(
            "entitlements: runtime_spec_at_batch falling back to OSS-free: %s", exc
        )
        ent = _oss_free()
    rows: list[dict] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for raw in rts:
        rt = canonical_runtime(raw)
        if rt and rt in ALL_RUNTIMES:
            if rt in seen:
                continue
            seen.add(rt)
            try:
                rows.append(_runtime_spec_row(ent, rt))
            except Exception as exc:
                logger.warning(
                    "entitlements: runtime_spec_at_batch row %r failed: %s",
                    rt,
                    exc,
                )
                unknown.append(raw)
        else:
            unknown.append(raw)
    return {"runtimes": rows, "unknown": unknown}


def lock_reason_at(
    perspective_tier: str, item: str, *, kind: str | None = None
) -> str | None:
    """What-if sibling of :func:`lock_reason`: the lock-reason string for
    ``item`` (interpreted as ``kind``) computed as if the install were on
    ``perspective_tier``, NOT against the live resolved entitlement.

    Pairs with :func:`feature_spec_at` / :func:`runtime_spec_at` /
    :func:`tier_spec_at` -- where those return the catalog row at a
    hypothetical tier, this returns the human-readable lock sentence the
    paywall surface renders ("``'sso' feature requires Cloud Pro or
    above.``"). Lets a pricing-comparison tooltip preview the lock copy
    a downgrade would surface BEFORE the user commits, without
    consulting the live resolver.

    Synthesises a fresh :class:`Entitlement` for ``perspective_tier``
    with ``grace=False`` and the per-tier capacity caps
    (``_TIER_NODE_LIMIT`` / ``_TIER_CHANNEL_LIMIT`` /
    ``_TIER_RETENTION_DAYS`` flow off ``self.tier`` already), so the
    capacity axes (``channels`` / ``retention_days`` / ``nodes``)
    resolve correctly at the hypothetical tier rather than against the
    OSS single-node default the unparameterised ``_hypothetical_entitlement``
    uses for feature/runtime-only callers.

    ``kind`` follows :meth:`Entitlement.lock_reason`: ``"feature"`` /
    ``"runtime"`` / ``"channels"`` / ``"retention_days"`` / ``"nodes"``
    explicitly; ``None`` lets the inner method infer ``feature`` vs
    ``runtime`` from the id (capacity axes can't be inferred, so pass
    ``kind=`` for those).

    Returns ``None`` for empty / unknown perspective tier (caller renders
    "unknown tier" / 404), for ids the inner method considers
    unlockable (free features / runtimes, empty keys, malformed
    capacity counts), or when the perspective is unenforceable. Never
    raises: a synthesis failure short-circuits to ``None`` so the
    tooltip silently hides instead of crashing the UI.
    """
    try:
        t = (perspective_tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        paid_feats = _TIER_FEATURES.get(t, frozenset())
        rts = (
            (FREE_RUNTIMES | PAID_RUNTIMES)
            if t in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        ent = Entitlement(
            tier=t,
            source="hypothetical",
            node_limit=_TIER_NODE_LIMIT.get(t, _FREE_NODE_LIMIT),
            expiry=None,
            features=FREE_FEATURES | paid_feats,
            runtimes=rts,
            grace=False,
        )
    except Exception as exc:
        logger.warning(
            "entitlements: lock_reason_at synthesis failed: %s", exc
        )
        return None
    try:
        return ent.lock_reason(item, kind=kind)
    except Exception as exc:
        logger.warning("entitlements: lock_reason_at lookup failed: %s", exc)
        return None


def lock_reasons_at_batch(
    perspective_tier: str,
    *,
    features=None,
    runtimes=None,
    channels: int | None = None,
    retention_days: int | None = None,
    nodes: int | None = None,
) -> dict | None:
    """What-if sibling of :func:`lock_reasons_batch`: per-item lock-reason
    rows for every supplied item across all 5 axes, computed as if the
    install were on ``perspective_tier``.

    Pairs with :func:`lock_reason_at` the same way :func:`lock_reasons_batch`
    pairs with :func:`lock_reason` -- where the scalar what-if returns one
    sentence for one item, this returns the full N-row matrix in one pass
    so a pricing-comparison matrix UI can preview the lock copy a
    downgrade-to-target would surface for many items BEFORE the user
    commits, without N round-trips to ``/lock-reason-at``.

    Synthesises a fresh :class:`Entitlement` for ``perspective_tier`` (with
    grace=False and the per-tier capacity caps off ``_TIER_NODE_LIMIT``)
    rather than calling :func:`_hypothetical_entitlement`, for the same
    reason :func:`lock_reason_at` does: the unparameterised helper
    hard-codes ``node_limit=1`` because its catalog-row callers don't
    expose node counts, but the capacity axes here (``nodes`` etc.) must
    resolve against the perspective tier's true cap.

    Shape (byte-identical to :func:`lock_reasons_batch`)::

        {
          "features":       [<row>, ...],
          "runtimes":       [<row>, ...],
          "channels":       <row> | None,
          "retention_days": <row> | None,
          "nodes":          <row> | None,
        }

    Each ``<row>`` carries ``key``, ``kind``, ``reason``, ``locked``,
    ``allowed``, ``required_tier``, ``required_tier_label``,
    ``required_tier_rank`` -- the same 8 keys :func:`_lock_row` emits.

    Returns ``None`` for empty / unknown perspective tier (caller renders
    404). Never raises: a synthesis failure short-circuits to the
    grace-shape rows so the matrix keeps rendering. Capacity axes use
    ``None`` as the "axis not supplied" sentinel: ``retention_days=None``
    here means *unset*, NOT *unlimited* -- matches
    :func:`lock_reasons_batch` exactly.
    """
    try:
        t = (perspective_tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    feats = _normalise_csv(features)
    rts = _normalise_csv(runtimes)
    try:
        paid_feats = _TIER_FEATURES.get(t, frozenset())
        rt_set = (
            (FREE_RUNTIMES | PAID_RUNTIMES)
            if t in _TIER_PAID_RUNTIMES
            else FREE_RUNTIMES
        )
        ent = Entitlement(
            tier=t,
            source="hypothetical",
            node_limit=_TIER_NODE_LIMIT.get(t, _FREE_NODE_LIMIT),
            expiry=None,
            features=FREE_FEATURES | paid_feats,
            runtimes=rt_set,
            grace=False,
        )
    except Exception as exc:
        logger.warning(
            "entitlements: lock_reasons_at_batch synthesis failed: %s", exc
        )
        ent = _oss_free()
    out: dict = {
        "features": [_lock_row(ent, f, "feature") for f in feats],
        "runtimes": [_lock_row(ent, r, "runtime") for r in rts],
        "channels": (
            _lock_row(ent, channels, "channels") if channels is not None else None
        ),
        "retention_days": (
            _lock_row(ent, retention_days, "retention_days")
            if retention_days is not None
            else None
        ),
        "nodes": _lock_row(ent, nodes, "nodes") if nodes is not None else None,
    }
    return out


def tier_unlocks_at(tier: str, target: str) -> dict | None:
    """Scalar what-if sibling of :func:`tier_unlocks`: marginal unlocks for
    ``target`` (features + runtimes that first become available at the
    destination) computed against the caller-supplied ``tier`` rather than
    the global next-lower-purchasable-tier anchor :func:`tier_unlocks` uses.

    Pairs with :func:`tier_unlocks` (live, anchored to the next-lower
    purchasable tier) the same way :func:`tier_spec_at` pairs with
    :func:`tier_spec`: same row shape, hypothetical source. Lets a
    pricing-comparison tooltip render "what's new in B vs A" for any
    ``(A, B)`` pair in one round-trip -- the single-hop view of
    ``tier_unlocks_path(A, B)`` that elides intermediate rungs and just
    reports the cumulative ``A -> B`` marginal grant.

    Row shape matches :func:`tier_unlocks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``previous_tier``, ``previous_tier_label``,
    ``previous_tier_rank``, ``features``, ``runtimes`` -- with one
    difference: ``previous_tier`` is the caller-supplied ``tier`` (the
    scalar what-if source), NOT the global next-lower-purchasable anchor
    :func:`tier_unlocks` uses, and NOT the previous walked rung
    :func:`tier_unlocks_path` carries. ``features`` / ``runtimes`` byte-
    equal ``tier_diff(tier, target)['added_features']`` /
    ``['added_runtimes']`` -- a parity test pins this so the scalar
    what-if and the cumulative diff cannot drift.

    Both endpoints accept any tier id in :data:`_TIER_ORDER` (including
    :data:`TIER_TRIAL`), matching :func:`_unlocks_row` and the other ``_at``
    family helpers; the live :func:`tier_unlocks` blocks ``trial`` because
    it routes an upgrade CTA, but this scalar what-if is for hypothetical
    comparison and does not.

    Direction is *not* normalised: when ``target_rank <= tier_rank`` (a
    downgrade or identity pair) ``features`` / ``runtimes`` collapse to
    empty lists -- you unlock nothing going down. Use :func:`tier_locks_at`
    for the marginal-loss view of a downgrade.

    Returns ``None`` for empty / unknown ``tier`` or ``target`` ids (caller
    renders "unknown tier" / 404). Never raises: a builder failure
    short-circuits to ``None`` so the tooltip surface stays mute instead
    of breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_ORDER:
        return None
    try:
        t = (target or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        return _unlocks_row(a, t)
    except Exception as exc:
        logger.warning("entitlements: tier_unlocks_at failed: %s", exc)
        return None


def tier_locks_at(tier: str, target: str) -> dict | None:
    """Scalar what-if sibling of :func:`tier_locks`: marginal losses for
    ``target`` (features + runtimes that disappear at the destination)
    computed against the caller-supplied ``tier`` rather than the global
    next-higher-purchasable-tier anchor :func:`tier_locks` uses.

    Marginal-loss mirror of :func:`tier_unlocks_at` and pairs with
    :func:`tier_locks` (live, anchored to the next-higher purchasable tier)
    the same way :func:`tier_spec_at` pairs with :func:`tier_spec`. Lets a
    downgrade-warning tooltip render "what you'd give up dropping from A
    to B" for any ``(A, B)`` pair in one round-trip -- the single-hop view
    of ``tier_locks_path(A, B)`` that elides intermediate rungs and just
    reports the cumulative ``A -> B`` marginal loss.

    Row shape matches :func:`tier_locks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes`` -- with one
    difference: ``next_tier`` is the caller-supplied ``tier`` (the scalar
    what-if source you're stepping down FROM), NOT the global
    next-higher-purchasable anchor :func:`tier_locks` uses, and NOT the
    previous walked rung :func:`tier_locks_path` carries.
    ``lost_features`` / ``lost_runtimes`` byte-equal
    ``tier_diff(tier, target)['lost_features']`` / ``['lost_runtimes']``
    -- a parity test pins this so the scalar what-if and the cumulative
    diff cannot drift.

    Both endpoints accept any tier id in :data:`_TIER_ORDER` (including
    :data:`TIER_TRIAL`), matching :func:`_locks_row` and the other ``_at``
    family helpers; the live :func:`tier_locks` blocks ``trial`` because
    it routes a downgrade warning, but this scalar what-if is for
    hypothetical comparison and does not.

    Direction is *not* normalised: when ``target_rank >= tier_rank`` (an
    upgrade or identity pair) ``lost_features`` / ``lost_runtimes``
    collapse to empty lists -- you lose nothing going up. Use
    :func:`tier_unlocks_at` for the marginal-grant view of an upgrade.

    Returns ``None`` for empty / unknown ``tier`` or ``target`` ids (caller
    renders "unknown tier" / 404). Never raises: a builder failure
    short-circuits to ``None`` so the tooltip surface stays mute instead
    of breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_ORDER:
        return None
    try:
        t = (target or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_ORDER:
        return None
    try:
        return _locks_row(a, t)
    except Exception as exc:
        logger.warning("entitlements: tier_locks_at failed: %s", exc)
        return None


def tier_unlocks_at_batch(tier: str) -> list[dict] | None:
    """What-if + batch sibling of :func:`tier_unlocks_batch`: marginal
    unlocks against the caller-supplied ``tier`` for every purchasable
    tier as a target, in one pass.

    Composes :func:`tier_unlocks_at` (scalar what-if) and
    :func:`tier_unlocks_batch` (live batch): same row shape and ordering
    as the live batch helper, same hypothetical perspective as the
    ``_at`` helper. Lets a pricing-comparison matrix UI render the
    "marginal unlocks vs <hypothetical-tier>" column for every rung off
    **one** round-trip instead of N calls to
    :func:`tier_unlocks_at`.

    Each row is byte-identical to ``tier_unlocks_at(tier, target)`` for
    the same ``(tier, target)`` pair -- a parity test pins this so the
    batch what-if cannot drift from the scalar what-if (the same
    invariant ``feature_spec_at_batch`` / ``runtime_spec_at_batch``
    enforce against their scalar siblings).

    Rows are sorted by ``(tier_rank, tier_id)`` ascending -- byte-
    stable against :func:`tier_unlocks_batch`'s ordering so a UI can
    swap the live anchor for a hypothetical perspective without
    re-sorting client-side. Same-rank sibling tiers (``cloud_pro`` /
    ``pro`` both at rank 2) are both returned.

    Target list is :data:`_PURCHASABLE_TIERS` (trial excluded), matching
    :func:`tier_unlocks_batch`. The source ``tier`` accepts any id in
    :data:`_TIER_ORDER` including :data:`TIER_TRIAL` -- the lenient
    ``_at`` posture, since the source is hypothetical and may legitimately
    answer "what would Cloud Pro unlock vs a trial install?".

    Returns ``None`` for empty / unknown source ``tier`` (caller renders
    "unknown tier" / 404). Never raises: a builder failure short-circuits
    to ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_ORDER:
        return None
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = _unlocks_row(a, tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_unlocks_at_batch failed: %s", exc)
        return []


def tier_locks_at_batch(tier: str) -> list[dict] | None:
    """What-if + batch sibling of :func:`tier_locks_batch`: marginal
    losses against the caller-supplied ``tier`` for every purchasable
    tier as a target, in one pass.

    Marginal-loss mirror of :func:`tier_unlocks_at_batch` and pairs
    with :func:`tier_locks_batch` the same way
    :func:`tier_unlocks_at_batch` pairs with :func:`tier_unlocks_batch`
    -- the downgrade-warning column on the same matrix the unlocks
    batch renders the upgrade-CTA column for, pivoted around a
    hypothetical perspective tier.

    Each row is byte-identical to ``tier_locks_at(tier, target)`` for
    the same ``(tier, target)`` pair -- a parity test pins this so the
    batch what-if cannot drift from the scalar what-if.

    Rows are sorted by ``(tier_rank, tier_id)`` ascending -- byte-
    stable against :func:`tier_locks_batch`'s ordering and against
    :func:`tier_unlocks_at_batch` for the same source tier so a UI can
    fold the two responses into an "if you upgrade / if you downgrade"
    matrix without re-sorting client-side. Same-rank sibling tiers are
    both returned.

    Target list is :data:`_PURCHASABLE_TIERS` (trial excluded), matching
    :func:`tier_locks_batch`. The source ``tier`` accepts any id in
    :data:`_TIER_ORDER` including :data:`TIER_TRIAL` -- the lenient
    ``_at`` posture.

    Returns ``None`` for empty / unknown source ``tier``. Never raises:
    a builder failure short-circuits to ``[]`` so the matrix keeps
    rendering.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_ORDER:
        return None
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = _locks_row(a, tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_locks_at_batch failed: %s", exc)
        return []


def capacity_diff_at(tier: str, target: str) -> dict | None:
    """Scalar what-if sibling of :func:`capacity_diff`: per-axis capacity
    transition (channels / retention / nodes) from a caller-supplied
    ``tier`` to ``target``, computed off the static per-tier caps rather
    than the resolved entitlement :func:`capacity_diff` anchors to.

    Pairs with :func:`capacity_diff` (live, anchored to the resolver) the
    same way :func:`tier_unlocks_at` pairs with :func:`tier_unlocks`:
    same row shape, hypothetical source. Lets a pricing-comparison
    tooltip render "capacity at B vs A" for any ``(A, B)`` pair in one
    round-trip -- the single-hop view of :func:`capacity_diff_path` that
    elides intermediate rungs and just reports the cumulative
    ``A -> B`` marginal capacity step.

    Row shape matches :func:`capacity_diff` exactly -- ``target``,
    ``channel_limit``, ``retention_days``, ``node_limit`` where each
    axis is the ``{before, after, delta, unlocked, locked}`` triple
    :func:`_capacity_transition` builds. The ``before`` side comes off
    the static per-tier caps (not the resolved entitlement), so the
    helper is independent of grace mode and the per-axis caps do NOT
    collapse to the unlimited sentinel the way :func:`capacity_diff`
    does under grace -- the ``_at`` posture is "if I were at A, what
    would B cost", not "from where I am now".

    Each row is byte-identical to the destination row of
    :func:`capacity_diff_path` for the same ``(tier, target)`` pair --
    a parity test pins this so the scalar what-if and the path-walker
    cannot drift (the same invariant ``tier_unlocks_at`` already
    enforces against :func:`tier_unlocks_path`).

    Both endpoints accept any tier id in :data:`_TIER_FEATURES`
    (including :data:`TIER_TRIAL`), matching :func:`_capacity_row` and
    the other ``_at`` family helpers; the live :func:`capacity_diff`
    accepts any id but anchors ``before`` to the resolver, while this
    scalar what-if anchors ``before`` to the caller-supplied ``tier``.

    Direction is *not* normalised: an upgrade pair flips ``unlocked``
    on axes that go from a finite cap to unlimited; a downgrade pair
    flips ``locked`` on axes that go from unlimited to a finite cap;
    identity / lateral-rank pairs collapse every axis to a no-op
    triple (``before == after``, ``delta == 0`` or ``None``, both flags
    ``False``).

    Returns ``None`` for empty / unknown ``tier`` or ``target`` ids
    (caller renders "unknown tier" / 404). Never raises: a builder
    failure short-circuits to ``None`` so the tooltip surface stays
    mute instead of breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_FEATURES:
        return None
    try:
        t = (target or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not t or t not in _TIER_FEATURES:
        return None
    try:
        return _capacity_row(a, t)
    except Exception as exc:
        logger.warning("entitlements: capacity_diff_at failed: %s", exc)
        return None


def capacity_diff_at_batch(tier: str) -> list[dict] | None:
    """What-if + batch sibling of :func:`capacity_diff_batch`: per-axis
    capacity-transition rows for every purchasable tier as a target,
    computed against the caller-supplied ``tier`` rather than the
    resolved entitlement :func:`capacity_diff_batch` anchors to.

    Composes :func:`capacity_diff_at` (scalar what-if) and
    :func:`capacity_diff_batch` (live batch): same row shape and
    ordering as the live batch helper, same hypothetical perspective
    as the ``_at`` helper. Lets a pricing-comparison matrix UI render
    the "capacity vs <hypothetical-tier>" column for every rung off
    **one** round-trip instead of N calls to :func:`capacity_diff_at`.

    Each row is byte-identical to ``capacity_diff_at(tier, target)``
    for the same ``(tier, target)`` pair -- a parity test pins this so
    the batch what-if cannot drift from the scalar what-if (the same
    invariant ``tier_unlocks_at_batch`` / ``tier_locks_at_batch`` enforce
    against their scalar siblings).

    Rows are sorted by ``(tier_rank, tier_id)`` ascending -- byte-
    stable against :func:`capacity_diff_batch`'s ordering, against
    :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` for the
    same source tier, and against :func:`preview_batch`, so a UI can
    fold the four responses into a single "what's at X / new at X /
    lost at X / capacity at X" matrix without re-sorting client-side.
    Same-rank sibling tiers (``cloud_pro`` / ``pro`` both at rank 2)
    are both returned.

    Target list is :data:`_PURCHASABLE_TIERS` (trial excluded), matching
    :func:`capacity_diff_batch`. The source ``tier`` accepts any id in
    :data:`_TIER_FEATURES` including :data:`TIER_TRIAL` -- the lenient
    ``_at`` posture, since the source is hypothetical and may
    legitimately answer "what would Cloud Pro cost in capacity vs a
    trial install?".

    Returns ``None`` for empty / unknown source ``tier`` (caller renders
    "unknown tier" / 404). Never raises: a builder failure short-circuits
    to ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_FEATURES:
        return None
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = _capacity_row(a, tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: capacity_diff_at_batch failed: %s", exc)
        return []


def tier_diff_at_batch(tier: str) -> list[dict] | None:
    """What-if + batch sibling of :func:`tier_diff_batch`: full marginal
    :func:`tier_diff` payload between the caller-supplied ``tier`` and
    every purchasable tier as a target, in one pass.

    Composes :func:`tier_diff` (arbitrary-endpoint diff) and
    :func:`tier_diff_batch` (live walking batch): same row shape as the
    live batch, but every row's ``from`` side is anchored to the caller-
    supplied ``tier`` instead of the per-rung next-lower-purchasable
    anchor :func:`tier_diff_batch` carries. Lets a pricing-comparison
    matrix UI render the "full marginal vs <hypothetical-tier>" column
    for every rung off **one** round-trip instead of N calls to
    :func:`tier_diff`.

    The "all-slices-in-one-row" member of the ``_at`` batch family
    alongside :func:`tier_unlocks_at_batch` (feature/runtime grant
    slice), :func:`tier_locks_at_batch` (feature/runtime loss slice)
    and :func:`capacity_diff_at_batch` (capacity slice). Where each of
    those siblings carries a single slice of the per-rung transition,
    ``tier_diff_at_batch`` carries ALL slices (``added_features`` +
    ``lost_features`` + ``added_runtimes`` + ``lost_runtimes`` +
    ``capacity_changes``) in one row so a UI can render the whole
    matrix off one call instead of three.

    Each row is byte-identical to ``tier_diff(tier, target)`` for the
    same ``(tier, target)`` pair -- a parity test pins this so the
    batch what-if cannot drift from :func:`tier_diff` (the same
    invariant ``tier_unlocks_at_batch`` / ``tier_locks_at_batch`` /
    ``capacity_diff_at_batch`` enforce against their scalar siblings).

    Per-slice parity with the other ``_at`` batches: each row's
    ``added_features`` byte-equals ``tier_unlocks_at_batch(tier)``'s
    ``features`` slot for the same target (and ditto for
    ``added_runtimes``); each row's ``lost_features`` byte-equals
    ``tier_locks_at_batch(tier)``'s ``lost_features`` slot for the
    same target (and ditto for ``lost_runtimes``); each row's
    ``capacity_changes`` byte-equals the per-axis triples
    ``capacity_diff_at_batch(tier)`` carries for the same target.
    Pinned in the test suite so the four ``_at`` batches can never
    silently drift apart.

    Rows are sorted by ``(tier_rank, tier_id)`` ascending -- byte-
    stable against :func:`tier_diff_batch`'s ordering and against
    :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` /
    :func:`capacity_diff_at_batch` for the same source tier, so a UI
    can fold the four responses into a single matrix without re-
    sorting client-side. Same-rank sibling tiers (``cloud_pro`` /
    ``pro`` both at rank 2) are both returned.

    Target list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`tier_diff_batch`. The source ``tier`` accepts any
    id in :data:`_TIER_FEATURES` including :data:`TIER_TRIAL` -- the
    lenient ``_at`` posture, since the source is hypothetical and may
    legitimately answer "what would Cloud Pro grant vs a trial
    install?".

    Identity row (target matches source) collapses to ``tier_diff(t,
    t)`` -- ``direction == "identity"`` with empty marginal lists and
    no-op capacity triples -- so a UI rendering "from X you're already
    at X" copy gets a real row instead of a missing entry.

    Decoupled from the resolved entitlement (walks the static per-tier
    maps), so grace vs enforce yields identical rows.

    Returns ``None`` for empty / unknown source ``tier`` (caller
    renders "unknown tier" / 404). Never raises: a builder failure
    short-circuits to ``[]`` so the matrix keeps rendering instead of
    breaking.
    """
    try:
        a = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not a or a not in _TIER_FEATURES:
        return None
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            row = tier_diff(a, tid)
            if row is not None:
                out.append(row)
        return out
    except Exception as exc:
        logger.warning("entitlements: tier_diff_at_batch failed: %s", exc)
        return []


def _next_purchasable_tier_after(tier: str) -> str | None:
    """Pure helper: next strictly-higher-rank entry in
    :data:`_PURCHASABLE_TIERS` after ``tier``, ties broken by the order
    of declaration in :data:`_PURCHASABLE_TIERS`.

    Mirrors :meth:`Entitlement.next_purchasable_tier` but takes a
    caller-supplied source tier instead of resolving the live
    entitlement -- the source-anchored pure stepper the ``_at`` family
    needs so its scalar what-if helpers do not depend on the resolver.

    The tie-break (rank-only, declaration-order otherwise) intentionally
    elides the cloud-vs-self-hosted preference the live method applies:
    the ``_at`` family is for hypothetical comparison and should be
    deterministic on the static catalogue, not driven by which install
    flavour the resolver is currently in.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`,
    rank 2 -- "next strictly above trial" resolves to enterprise,
    matching how :meth:`Entitlement.next_purchasable_tier` walks past
    same-rank trial when called from a trial entitlement).

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (enterprise -- nothing strictly above). Never raises.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        src_rank = _TIER_RANK.get(src, -1)
        for cand in _PURCHASABLE_TIERS:
            if _TIER_RANK.get(cand, -1) > src_rank:
                return cand
        return None
    except Exception as exc:
        logger.warning("entitlements: _next_purchasable_tier_after failed: %s", exc)
        return None


def next_tier_unlocks_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.next_tier_unlocks`:
    marginal unlocks row at the rung above the caller-supplied ``tier``,
    in :func:`tier_unlocks` shape.

    Convenience for ``tier_unlocks(_next_purchasable_tier_after(tier))``
    -- the source-anchored equivalent of the live method, so a pricing
    page can render "what's new at the next rung above X" for any X
    without first having to ask the resolver and without monkey-patching
    the entitlement context. Pairs with :func:`next_tier_locks_at` (the
    marginal-loss view of the same rung) on a hypothetical pricing
    matrix cell.

    Row shape matches :func:`tier_unlocks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``previous_tier``, ``previous_tier_label``,
    ``previous_tier_rank``, ``features``, ``runtimes``. The row IS the
    tier-property row of the rung above (its ``previous_tier`` is that
    rung's natural next-lower purchasable, NOT the caller-supplied
    ``tier``) -- the same posture :meth:`Entitlement.next_tier_unlocks`
    surfaces via the live resolver. Callers who want the source-anchored
    ``previous_tier`` should use :func:`tier_unlocks_at` directly with
    the explicit ``(tier, target)`` pair.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture, since the source is hypothetical
    and may legitimately answer "what would step Trial -> Enterprise
    unlock?".

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (no rung strictly above). Never raises: a builder failure short-
    circuits to ``None`` so the CTA surface stays mute instead of
    breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return tier_unlocks(target)
    except Exception as exc:
        logger.warning("entitlements: next_tier_unlocks_at failed: %s", exc)
        return None


def next_tier_locks_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.next_tier_locks`:
    marginal locks row at the rung above the caller-supplied ``tier``,
    in :func:`tier_locks` shape.

    Marginal-loss mirror of :func:`next_tier_unlocks_at` and pairs
    with :meth:`Entitlement.next_tier_locks` (live, source pinned to
    the resolver) the same way :func:`tier_locks_at` pairs with
    :func:`tier_locks`. Convenience for
    ``tier_locks(_next_purchasable_tier_after(tier))`` -- the source-
    anchored equivalent of the live method, so a pricing page can
    render "what does the rung above X first lose vs the rung above
    IT" for any X without first asking the resolver.

    Row shape matches :func:`tier_locks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes``. The row
    IS the tier-property row of the rung above (its ``next_tier`` is
    that rung's natural next-higher purchasable, NOT the caller-
    supplied ``tier``) -- the same posture
    :meth:`Entitlement.next_tier_locks` surfaces via the live resolver.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (no rung strictly above). At the rung where the next-above IS the
    ladder ceiling (enterprise as ``_next_purchasable_tier_after``'s
    answer) the returned row carries ``next_tier=None`` and empty
    ``lost_*`` lists -- :func:`tier_locks` shape for "this rung has no
    rung above to step down from", not ``None``.

    Never raises: a builder failure short-circuits to ``None`` so the
    CTA surface stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return tier_locks(target)
    except Exception as exc:
        logger.warning("entitlements: next_tier_locks_at failed: %s", exc)
        return None


def _previous_purchasable_tier_before(tier: str) -> str | None:
    """Pure helper: next strictly-lower-rank entry in
    :data:`_PURCHASABLE_TIERS` before ``tier``, picking the *highest*
    rank strictly below the source and breaking same-rank ties by the
    order of declaration in :data:`_PURCHASABLE_TIERS`.

    Source-anchored mirror of :func:`_next_purchasable_tier_after`. The
    live :meth:`Entitlement.previous_purchasable_tier` applies a cloud-
    vs-self-hosted tie-break against the resolved entitlement's
    ``source``; this helper intentionally elides that preference for
    the same reason :func:`_next_purchasable_tier_after` does -- the
    ``_at`` family is for hypothetical comparison and must be
    deterministic on the static catalogue, not driven by which install
    flavour the resolver is currently in.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`,
    rank 2 -- "next strictly below trial" resolves to cloud_starter,
    rank 1). Returns ``None`` for empty / unknown ``tier`` and at the
    floor (oss / cloud_free -- nothing strictly below). Never raises.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        src_rank = _TIER_RANK.get(src, -1)
        lower_ranks = [
            r for r in (_TIER_RANK.get(t, -1) for t in _PURCHASABLE_TIERS)
            if 0 <= r < src_rank
        ]
        if not lower_ranks:
            return None
        target_rank = max(lower_ranks)
        for cand in _PURCHASABLE_TIERS:
            if _TIER_RANK.get(cand, -1) == target_rank:
                return cand
        return None
    except Exception as exc:
        logger.warning("entitlements: _previous_purchasable_tier_before failed: %s", exc)
        return None


def previous_tier_unlocks_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.previous_tier_unlocks`:
    marginal unlocks row at the rung below the caller-supplied ``tier``,
    in :func:`tier_unlocks` shape.

    Source-anchored mirror of :func:`next_tier_unlocks_at`. Convenience
    for ``tier_unlocks(_previous_purchasable_tier_before(tier))`` -- the
    source-anchored equivalent of the live method, so a downgrade-CTA
    or pricing-comparison page can render "what would still be granted
    at the rung below X" for any hypothetical ``X`` without first
    asking the resolver and without monkey-patching the entitlement
    context. Pairs with :func:`previous_tier_locks_at` (the marginal-
    loss view of the same rung) on a hypothetical pricing matrix cell.

    Row shape matches :func:`tier_unlocks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``previous_tier``,
    ``previous_tier_label``, ``previous_tier_rank``, ``features``,
    ``runtimes``. The row IS the tier-property row of the rung below
    (its ``previous_tier`` is that rung's natural next-lower
    purchasable, NOT the caller-supplied ``tier``) -- the same posture
    :meth:`Entitlement.previous_tier_unlocks` surfaces via the live
    resolver. Callers who want the source-anchored ``previous_tier``
    should use :func:`tier_unlocks_at` directly with the explicit
    ``(tier, target)`` pair.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the floor
    (oss / cloud_free -- no rung strictly below). Never raises: a
    builder failure short-circuits to ``None`` so the CTA surface stays
    mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return tier_unlocks(target)
    except Exception as exc:
        logger.warning("entitlements: previous_tier_unlocks_at failed: %s", exc)
        return None


def previous_tier_locks_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.previous_tier_locks`:
    marginal locks row at the rung below the caller-supplied ``tier``,
    in :func:`tier_locks` shape.

    Marginal-loss mirror of :func:`previous_tier_unlocks_at` and pairs
    with :meth:`Entitlement.previous_tier_locks` (live, source pinned to
    the resolver) the same way :func:`tier_locks_at` pairs with
    :func:`tier_locks`. Convenience for
    ``tier_locks(_previous_purchasable_tier_before(tier))`` -- the
    source-anchored equivalent of the live method, so a pricing page
    can render "what does the rung below X first lose vs the rung
    above IT" for any hypothetical ``X`` without asking the resolver.

    Row shape matches :func:`tier_locks` exactly -- ``tier``,
    ``tier_label``, ``tier_rank``, ``next_tier``, ``next_tier_label``,
    ``next_tier_rank``, ``lost_features``, ``lost_runtimes``. The row IS
    the tier-property row of the rung below (its ``next_tier`` is that
    rung's natural next-higher purchasable, NOT the caller-supplied
    ``tier``).

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the floor
    (oss / cloud_free -- no rung strictly below). Never raises: a
    builder failure short-circuits to ``None`` so the CTA surface stays
    mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return tier_locks(target)
    except Exception as exc:
        logger.warning("entitlements: previous_tier_locks_at failed: %s", exc)
        return None


def _next_at_envelope(source: str, builder) -> dict:
    """Private builder for the ``next_tier_*_at_batch`` rows.

    Resolves ``target = _next_purchasable_tier_after(source)`` and pairs
    the source/target tier metadata with the row produced by ``builder``
    (one of :func:`tier_unlocks` / :func:`tier_locks`) into the same
    envelope shape the scalar what-if endpoints surface:

        ``{tier, tier_label, tier_rank, target, target_label, target_rank, row}``

    ``row`` collapses to ``None`` at the source-side ceiling (source ==
    enterprise -- no rung strictly above), matching the scalar helpers.
    A builder failure short-circuits to ``row=None`` on the populated
    envelope so the batch keeps the per-source row visible instead of
    dropping it -- the same posture
    :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` apply to
    their per-row failures.

    Never raises: every fallback collapses to a fully-populated envelope
    with ``row=None`` so a pricing-matrix UI can render the source rung
    even when its target row could not be built.
    """
    src = (source or "").strip().lower()
    target = _next_purchasable_tier_after(src) if src in _TIER_ORDER else None
    row: dict | None = None
    if target is not None:
        try:
            row = builder(target)
        except Exception as exc:
            logger.warning(
                "entitlements: _next_at_envelope builder failed for %s: %s",
                target,
                exc,
            )
            row = None
    return {
        "tier": src,
        "tier_label": tier_label(src) if src in _TIER_ORDER else None,
        "tier_rank": tier_rank(src) if src in _TIER_ORDER else -1,
        "target": target,
        "target_label": tier_label(target) if target else None,
        "target_rank": tier_rank(target) if target else None,
        "row": row,
    }


def next_tier_unlocks_at_batch() -> list[dict]:
    """Batch sibling of :func:`next_tier_unlocks_at`: one
    ``next-tier-unlocks-at`` envelope per purchasable source tier, in
    one pass.

    Composes :func:`next_tier_unlocks_at` (scalar what-if) and
    :func:`tier_unlocks_batch` (live batch): same envelope shape per row
    as the scalar ``/api/entitlement/next-tier-unlocks-at`` endpoint
    surfaces, same source axis as :func:`tier_unlocks_batch`. Lets a
    pricing-comparison matrix UI render the "what's new at the rung
    above each rung" upgrade-CTA column off **one** round-trip instead
    of N calls to :func:`next_tier_unlocks_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/next-tier-unlocks-at?tier=<source>`` response
    body for the same source (sans the resolver-context fields the
    route adds around the helper output) -- a parity test pins this so
    the batch what-if cannot drift from the scalar what-if (the same
    invariant :func:`tier_unlocks_at_batch` enforces against
    :func:`tier_unlocks_at`).

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`tier_unlocks_batch`'s ordering and
    against :func:`tier_locks_at_batch` for the same source so a UI can
    fold the two responses into an upgrade-CTA column without re-sorting
    client-side. Same-rank sibling tiers (``cloud_pro`` / ``pro`` both
    at rank 2) are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded), matching
    :func:`tier_unlocks_batch`. The source-side ceiling (enterprise as
    source -- no rung strictly above) surfaces with ``target=None`` and
    ``row=None`` rather than being dropped, so the matrix keeps a row
    for every purchasable rung.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            out.append(_next_at_envelope(tid, tier_unlocks))
        return out
    except Exception as exc:
        logger.warning("entitlements: next_tier_unlocks_at_batch failed: %s", exc)
        return []


def next_tier_locks_at_batch() -> list[dict]:
    """Batch sibling of :func:`next_tier_locks_at`: one
    ``next-tier-locks-at`` envelope per purchasable source tier, in one
    pass.

    Marginal-loss mirror of :func:`next_tier_unlocks_at_batch` and pairs
    with :func:`tier_locks_batch` the same way
    :func:`next_tier_unlocks_at_batch` pairs with
    :func:`tier_unlocks_batch` -- the downgrade-warning column on the
    same matrix the unlocks batch renders the upgrade-CTA column for,
    pivoted around the natural next-above rung for each source.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/next-tier-locks-at?tier=<source>`` response body
    for the same source (sans the resolver-context fields the route
    adds around the helper output) -- a parity test pins this so the
    batch what-if cannot drift from the scalar what-if.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`next_tier_unlocks_at_batch` for the
    same source so a UI can fold the two responses into an
    upgrade-CTA + downgrade-warning matrix without re-sorting
    client-side.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded). The
    source-side ceiling (enterprise as source -- no rung strictly
    above) surfaces with ``target=None`` and ``row=None``.

    At a source rung whose next-above IS the ladder ceiling
    (``cloud_pro`` / ``pro`` -> ``enterprise``) the row carries
    ``next_tier=None`` and empty ``lost_*`` lists -- :func:`tier_locks`
    shape for "the target has no rung above to step down from", NOT
    ``None`` on the envelope.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope; an unexpected top-level
    failure short-circuits to ``[]``.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            out.append(_next_at_envelope(tid, tier_locks))
        return out
    except Exception as exc:
        logger.warning("entitlements: next_tier_locks_at_batch failed: %s", exc)
        return []


def _previous_at_envelope(source: str, builder) -> dict:
    """Private builder for the ``previous_tier_*_at_batch`` rows.

    Mirror of :func:`_next_at_envelope` (next-tier batch) pivoted to the
    rung *below* the source. Resolves
    ``target = _previous_purchasable_tier_before(source)`` and pairs the
    source/target tier metadata with the row produced by ``builder``
    (one of :func:`tier_unlocks` / :func:`tier_locks`) into the same
    envelope shape the scalar ``/previous-tier-*-at`` endpoints surface:

        ``{tier, tier_label, tier_rank, target, target_label, target_rank, row}``

    ``row`` collapses to ``None`` at the floor of the source axis (oss
    / cloud_free -- no rung strictly below), matching the scalar
    helpers. A builder failure short-circuits to ``row=None`` on the
    populated envelope so the batch keeps the per-source row visible
    instead of dropping it -- the same posture
    :func:`tier_unlocks_at_batch` / :func:`tier_locks_at_batch` apply
    to their per-row failures.

    Never raises: every fallback collapses to a fully-populated
    envelope with ``row=None`` so a pricing-matrix UI can render the
    source rung even when its target row could not be built.
    """
    src = (source or "").strip().lower()
    target = _previous_purchasable_tier_before(src) if src in _TIER_ORDER else None
    row: dict | None = None
    if target is not None:
        try:
            row = builder(target)
        except Exception as exc:
            logger.warning(
                "entitlements: _previous_at_envelope builder failed for %s: %s",
                target,
                exc,
            )
            row = None
    return {
        "tier": src,
        "tier_label": tier_label(src) if src in _TIER_ORDER else None,
        "tier_rank": tier_rank(src) if src in _TIER_ORDER else -1,
        "target": target,
        "target_label": tier_label(target) if target else None,
        "target_rank": tier_rank(target) if target else None,
        "row": row,
    }


def previous_tier_unlocks_at_batch() -> list[dict]:
    """Batch sibling of :func:`previous_tier_unlocks_at`: one
    ``previous-tier-unlocks-at`` envelope per purchasable source tier,
    in one pass.

    Source-anchored downgrade-side mirror of
    :func:`next_tier_unlocks_at_batch`. Composes
    :func:`previous_tier_unlocks_at` (scalar what-if) and
    :func:`tier_unlocks_batch` (live batch): same envelope shape per
    row as the scalar ``/api/entitlement/previous-tier-unlocks-at``
    endpoint surfaces, same source axis as :func:`tier_unlocks_batch`.
    Lets a pricing-comparison matrix UI render the "what would still
    be granted at the rung below each rung" downgrade-CTA column off
    **one** round-trip instead of N calls to
    :func:`previous_tier_unlocks_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/previous-tier-unlocks-at?tier=<source>``
    response body for the same source (sans the resolver-context
    fields the route adds around the helper output) -- a parity test
    pins this so the batch what-if cannot drift from the scalar
    what-if (the same invariant :func:`tier_unlocks_at_batch` enforces
    against :func:`tier_unlocks_at`).

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`tier_unlocks_batch`'s ordering and
    against :func:`previous_tier_locks_at_batch` for the same source so
    a UI can fold the two responses into a downgrade-CTA column without
    re-sorting client-side. Same-rank sibling tiers (``cloud_pro`` /
    ``pro`` both at rank 2) are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`tier_unlocks_batch`. The source-side floor
    (``oss`` / ``cloud_free`` as source -- no rung strictly below)
    surfaces with ``target=None`` and ``row=None`` rather than being
    dropped, so the matrix keeps a row for every purchasable rung.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            out.append(_previous_at_envelope(tid, tier_unlocks))
        return out
    except Exception as exc:
        logger.warning("entitlements: previous_tier_unlocks_at_batch failed: %s", exc)
        return []


def previous_tier_locks_at_batch() -> list[dict]:
    """Batch sibling of :func:`previous_tier_locks_at`: one
    ``previous-tier-locks-at`` envelope per purchasable source tier,
    in one pass.

    Marginal-loss mirror of :func:`previous_tier_unlocks_at_batch` and
    pairs with :func:`tier_locks_batch` the same way
    :func:`previous_tier_unlocks_at_batch` pairs with
    :func:`tier_unlocks_batch` -- the downgrade-warning column on the
    same matrix the previous-unlocks batch renders the downgrade-CTA
    column for, pivoted around the natural next-below rung for each
    source.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/previous-tier-locks-at?tier=<source>`` response
    body for the same source (sans the resolver-context fields the
    route adds around the helper output) -- a parity test pins this so
    the batch what-if cannot drift from the scalar what-if.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`previous_tier_unlocks_at_batch` for
    the same source so a UI can fold the two responses into a
    downgrade-CTA + downgrade-warning matrix without re-sorting
    client-side.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded). The
    source-side floor (``oss`` / ``cloud_free`` as source -- no rung
    strictly below) surfaces with ``target=None`` and ``row=None``.

    At a source rung whose next-below IS the ladder floor
    (``cloud_starter`` -> ``oss``) the row carries populated
    ``lost_features`` / ``lost_runtimes`` lists -- :func:`tier_locks`
    shape against the floor's next-above rung -- NOT ``None`` on the
    envelope.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope; an unexpected top-level
    failure short-circuits to ``[]``.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            out.append(_previous_at_envelope(tid, tier_locks))
        return out
    except Exception as exc:
        logger.warning("entitlements: previous_tier_locks_at_batch failed: %s", exc)
        return []


def next_tier_diff_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.next_tier_diff`:
    full :func:`tier_diff` row from the caller-supplied ``tier`` to the
    next rung above it.

    Source-anchored equivalent of :meth:`Entitlement.next_tier_diff`,
    which pins ``from`` to the resolved entitlement. Convenience for
    ``tier_diff(tier, _next_purchasable_tier_after(tier))`` so a pricing-
    comparison or upgrade-CTA card can render the full upgrade payload
    (``added_*``, ``lost_*``, ``capacity_changes``, ``direction``) for
    any hypothetical source rung without first asking the resolver and
    without monkey-patching the entitlement context. Pairs with
    :func:`next_tier_unlocks_at` / :func:`next_tier_locks_at` (the
    marginal-grant / marginal-loss views of the same step) on a
    hypothetical pricing matrix cell.

    Unlike :func:`next_tier_unlocks_at` -- which surfaces the target's
    own ``tier_unlocks`` row (target-anchored, ``previous_tier`` is the
    target's natural next-lower purchasable, NOT the caller-supplied
    source) -- this helper pins **both** endpoints, so the row's
    ``from`` is byte-equal to the caller-supplied ``tier``. That mirrors
    the live :meth:`Entitlement.next_tier_diff` posture
    (``upgrade_diff(self.tier, next_purchasable_tier())``) and is the
    natural shape for a two-endpoint diff.

    Row shape matches :func:`tier_diff` exactly -- ``from``,
    ``from_label``, ``from_rank``, ``to``, ``to_label``, ``to_rank``,
    ``direction``, ``added_features``, ``lost_features``,
    ``added_runtimes``, ``lost_runtimes``, ``capacity_changes``.
    ``direction`` is always ``"upgrade"`` for any purchasable source
    that has a strictly-higher rung above (the floor-to-step is always
    an upgrade); from ``trial`` (rank 2) ``direction`` is ``"upgrade"``
    too since the next strictly-higher purchasable resolves to
    enterprise (rank 3).

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture, since the source is hypothetical
    and may legitimately answer "what would step Trial -> Enterprise
    diff to?".

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (no rung strictly above). Never raises: a builder failure short-
    circuits to ``None`` so the CTA surface stays mute instead of
    breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return tier_diff(src, target)
    except Exception as exc:
        logger.warning("entitlements: next_tier_diff_at failed: %s", exc)
        return None


def previous_tier_diff_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.previous_tier_diff`:
    full :func:`tier_diff` row from the caller-supplied ``tier`` to the
    next rung below it.

    Source-anchored mirror of :func:`next_tier_diff_at` and downgrade-
    side counterpart of the live :meth:`Entitlement.previous_tier_diff`
    (which pins ``from`` to the resolved entitlement). Convenience for
    ``tier_diff(tier, _previous_purchasable_tier_before(tier))`` so a
    downgrade-confirmation card or pricing-comparison cell can render
    the full step-down payload for any hypothetical source rung without
    first asking the resolver.

    Like :func:`next_tier_diff_at` (and unlike
    :func:`previous_tier_unlocks_at`, which surfaces the target's own
    ``tier_unlocks`` row), this helper pins **both** endpoints, so the
    row's ``from`` is byte-equal to the caller-supplied ``tier``. That
    mirrors the live :meth:`Entitlement.previous_tier_diff` posture
    (``downgrade_diff(self.tier, previous_purchasable_tier())``) and
    is the natural shape for a two-endpoint diff.

    Row shape matches :func:`tier_diff` exactly. ``direction`` is
    always ``"downgrade"`` for any purchasable source that has a
    strictly-lower rung below; from ``trial`` (rank 2) ``direction``
    is ``"downgrade"`` since the next strictly-lower purchasable
    resolves to cloud_starter (rank 1).

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the floor
    (oss / cloud_free -- no rung strictly below). Never raises: a
    builder failure short-circuits to ``None`` so the CTA surface stays
    mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return tier_diff(src, target)
    except Exception as exc:
        logger.warning("entitlements: previous_tier_diff_at failed: %s", exc)
        return None


def _diff_at_envelope(source: str, target: str | None) -> dict:
    """Private builder for the ``{next,previous}_tier_diff_at_batch`` rows.

    Two-endpoint counterpart of :func:`_next_at_envelope` /
    :func:`_previous_at_envelope`: those carry a single-endpoint row
    (the target's own ``tier_unlocks`` / ``tier_locks``); this one
    carries a two-endpoint row pinned on both ``source`` and ``target``
    via :func:`tier_diff` -- the "all-slices-in-one-row" shape the
    scalar ``next_tier_diff_at`` / ``previous_tier_diff_at`` helpers
    surface.

    Envelope shape matches the unlocks / locks ``_at`` envelopes
    byte-for-byte so a UI can fold the three batches into one
    pricing-comparison matrix without re-keying::

        ``{tier, tier_label, tier_rank, target, target_label, target_rank, row}``

    ``row`` collapses to ``None`` at the ladder ceiling / floor of the
    source axis (``target is None``) and on a :func:`tier_diff` builder
    failure, matching the scalar diff helpers. Never raises -- every
    fallback collapses to a fully-populated envelope with ``row=None``
    so the batch keeps the per-source row visible even when its
    target row could not be built.
    """
    src = (source or "").strip().lower()
    row: dict | None = None
    if target is not None:
        try:
            row = tier_diff(src, target)
        except Exception as exc:
            logger.warning(
                "entitlements: _diff_at_envelope builder failed for %s->%s: %s",
                src,
                target,
                exc,
            )
            row = None
    return {
        "tier": src,
        "tier_label": tier_label(src) if src in _TIER_ORDER else None,
        "tier_rank": tier_rank(src) if src in _TIER_ORDER else -1,
        "target": target,
        "target_label": tier_label(target) if target else None,
        "target_rank": tier_rank(target) if target else None,
        "row": row,
    }


def next_tier_diff_at_batch() -> list[dict]:
    """Batch sibling of :func:`next_tier_diff_at`: one
    ``next-tier-diff-at`` envelope per purchasable source tier, in one
    pass.

    Composes :func:`next_tier_diff_at` (scalar what-if) and
    :func:`tier_diff_batch` (live batch) -- same envelope shape per row
    as the scalar ``/api/entitlement/next-tier-diff-at`` endpoint
    surfaces, same source axis as :func:`tier_diff_batch`. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    above each rung" upgrade-CTA column off **one** round-trip instead
    of N calls to :func:`next_tier_diff_at`.

    The "all-slices-in-one-row" member of the ``next_tier_*_at_batch``
    family alongside :func:`next_tier_unlocks_at_batch` (feature /
    runtime grant slice) and :func:`next_tier_locks_at_batch`
    (feature / runtime loss slice). Where each of those siblings
    carries a single slice of the per-rung transition, this batch
    carries ALL slices (``added_features`` + ``lost_features`` +
    ``added_runtimes`` + ``lost_runtimes`` + ``capacity_changes``) in
    one row so a UI can render the whole upgrade matrix off one call
    instead of two.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/next-tier-diff-at?tier=<source>`` response body
    for the same source (sans the resolver-context fields the route
    adds around the helper output) -- a parity test pins this so the
    batch what-if cannot drift from the scalar what-if (the same
    invariant :func:`next_tier_unlocks_at_batch` enforces against
    :func:`next_tier_unlocks_at`).

    Per-slice parity with the other ``next_*_at_batch`` siblings:
    each envelope's ``row.added_features`` byte-equals
    :func:`next_tier_unlocks_at_batch`'s ``row.features`` slot for the
    same source (and ditto for ``added_runtimes``); each envelope's
    ``row.lost_features`` byte-equals :func:`next_tier_locks_at_batch`'s
    ``row.lost_features`` slot for the same source (and ditto for
    ``lost_runtimes``). Pinned in the test suite so the three
    ``next_*_at_batch`` siblings can never silently drift apart.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`next_tier_unlocks_at_batch` /
    :func:`next_tier_locks_at_batch` so a UI can fold the three
    responses into one matrix without re-sorting client-side.
    Same-rank sibling tiers (``cloud_pro`` / ``pro`` both at rank 2)
    are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`tier_diff_batch`. The source-side ceiling
    (``enterprise`` as source -- no rung strictly above) surfaces with
    ``target=None`` and ``row=None`` rather than being dropped, so the
    matrix keeps a row for every purchasable rung.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _next_purchasable_tier_after(tid)
            out.append(_diff_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning("entitlements: next_tier_diff_at_batch failed: %s", exc)
        return []


def previous_tier_diff_at_batch() -> list[dict]:
    """Batch sibling of :func:`previous_tier_diff_at`: one
    ``previous-tier-diff-at`` envelope per purchasable source tier, in
    one pass.

    Source-anchored downgrade-side mirror of
    :func:`next_tier_diff_at_batch`. Composes
    :func:`previous_tier_diff_at` (scalar what-if) and
    :func:`tier_diff_batch` (live batch) -- same envelope shape per row
    as the scalar ``/api/entitlement/previous-tier-diff-at`` endpoint
    surfaces, same source axis as :func:`tier_diff_batch`. Lets a
    pricing-comparison matrix UI render the "full marginal vs the rung
    below each rung" downgrade-CTA column off **one** round-trip
    instead of N calls to :func:`previous_tier_diff_at`.

    The "all-slices-in-one-row" member of the
    ``previous_tier_*_at_batch`` family alongside
    :func:`previous_tier_unlocks_at_batch` (feature / runtime grant
    slice on a downgrade) and :func:`previous_tier_locks_at_batch`
    (feature / runtime loss slice on a downgrade). Where each of those
    siblings carries a single slice of the per-rung transition, this
    batch carries ALL slices in one row so a UI can render the whole
    downgrade matrix off one call instead of two.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/previous-tier-diff-at?tier=<source>`` response
    body for the same source (sans the resolver-context fields the
    route adds around the helper output) -- a parity test pins this so
    the batch what-if cannot drift from the scalar what-if.

    Per-slice parity with the other ``previous_*_at_batch`` siblings:
    each envelope's ``row.added_features`` byte-equals
    :func:`previous_tier_unlocks_at_batch`'s ``row.features`` slot for
    the same source (and ditto for ``added_runtimes``); each
    envelope's ``row.lost_features`` byte-equals
    :func:`previous_tier_locks_at_batch`'s ``row.lost_features`` slot
    for the same source (and ditto for ``lost_runtimes``). Pinned in
    the test suite so the three ``previous_*_at_batch`` siblings can
    never silently drift apart.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`previous_tier_unlocks_at_batch` /
    :func:`previous_tier_locks_at_batch` so a UI can fold the three
    responses into one matrix without re-sorting client-side.
    Same-rank sibling tiers (``cloud_pro`` / ``pro`` both at rank 2)
    are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`tier_diff_batch`. The source-side floor
    (``oss`` / ``cloud_free`` as source -- no rung strictly below)
    surfaces with ``target=None`` and ``row=None`` rather than being
    dropped, so the matrix keeps a row for every purchasable rung.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _previous_purchasable_tier_before(tid)
            out.append(_diff_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_diff_at_batch failed: %s", exc
        )
        return []


def next_tier_capacity_diff_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.next_tier_capacity_diff`:
    per-axis capacity transition (channels / retention / nodes) from the
    caller-supplied ``tier`` to the rung above it.

    Capacity-only narrow lens of :func:`next_tier_diff_at` -- the latter
    returns the FULL :func:`tier_diff` payload (``added_*`` + ``lost_*``
    + ``capacity_changes`` + ``direction``) for the same step; this
    helper returns only the capacity slice (the
    ``{target, channel_limit, retention_days, node_limit}`` shape
    :func:`capacity_diff` / :func:`capacity_diff_at` already publish).
    Source-anchored equivalent of the live
    :meth:`Entitlement.next_tier_capacity_diff` instance method which
    pins the source to the resolved entitlement -- convenience for
    ``capacity_diff_at(tier, _next_purchasable_tier_after(tier))`` so a
    capacity-only tooltip on a pricing-comparison cell can render the
    upgrade-side capacity delta for any hypothetical source rung off
    **one** round-trip, without first hitting ``/api/entitlement`` and
    without monkey-patching the entitlement context.

    Row shape matches :func:`capacity_diff_at` exactly -- ``target``,
    ``channel_limit``, ``retention_days``, ``node_limit`` where each
    capacity axis is the ``{before, after, delta, unlocked, locked}``
    triple :func:`_capacity_transition` builds. ``before`` comes off the
    static per-tier caps anchored at the caller-supplied ``tier`` (NOT
    the resolved entitlement), so the helper is independent of grace
    mode and the per-axis caps do NOT collapse to the unlimited sentinel
    the way live :func:`capacity_diff` does under grace -- the ``_at``
    posture is "if I were at A, what's the capacity at the next rung",
    not "from where I am now".

    Each row is byte-identical to ``capacity_diff_at(tier,
    _next_purchasable_tier_after(tier))`` for the same source -- pinned
    in the test suite so the singular helper cannot drift from the
    explicit composition.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture, since the source is hypothetical
    and may legitimately answer "what would step Trial -> Enterprise
    cost in capacity?".

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (no rung strictly above -- enterprise as source). Never raises: a
    builder failure short-circuits to ``None`` so the tooltip surface
    stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return capacity_diff_at(src, target)
    except Exception as exc:
        logger.warning(
            "entitlements: next_tier_capacity_diff_at failed: %s", exc
        )
        return None


def previous_tier_capacity_diff_at(tier: str) -> dict | None:
    """Scalar what-if sibling of
    :meth:`Entitlement.previous_tier_capacity_diff`: per-axis capacity
    transition from the caller-supplied ``tier`` to the rung below it.

    Capacity-only narrow lens of :func:`previous_tier_diff_at` and
    source-anchored downgrade-side mirror of
    :func:`next_tier_capacity_diff_at`. Convenience for
    ``capacity_diff_at(tier, _previous_purchasable_tier_before(tier))``
    so a downgrade-confirmation tooltip can render the step-down
    capacity delta for any hypothetical source rung off **one** round-
    trip, without first hitting ``/api/entitlement``.

    Row shape matches :func:`capacity_diff_at` exactly. Like
    :func:`next_tier_capacity_diff_at` the ``before`` side comes off
    the static per-tier caps anchored at the caller-supplied ``tier``
    (NOT the resolved entitlement) -- the helper is independent of
    grace mode and never returns the unlimited sentinel.

    Each row is byte-identical to ``capacity_diff_at(tier,
    _previous_purchasable_tier_before(tier))`` for the same source --
    pinned in the test suite so the singular helper cannot drift from
    the explicit composition.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the floor
    (no rung strictly below -- oss / cloud_free as source). Never
    raises: a builder failure short-circuits to ``None``.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return capacity_diff_at(src, target)
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_capacity_diff_at failed: %s", exc
        )
        return None


def _capacity_diff_at_envelope(source: str, target: str | None) -> dict:
    """Private builder for the ``{next,previous}_tier_capacity_diff_at_batch``
    rows.

    Capacity-only narrow-lens mirror of :func:`_diff_at_envelope`:
    where that builder carries the full :func:`tier_diff` row, this
    one carries the capacity-only :func:`_capacity_row` shape
    (``target``, ``channel_limit``, ``retention_days``, ``node_limit``)
    pinned on both ``source`` and ``target``.

    Envelope shape matches :func:`_diff_at_envelope` byte-for-byte on
    the source/target metadata so a UI can fold the diff batch and the
    capacity batch into one pricing-comparison matrix without
    re-keying::

        ``{tier, tier_label, tier_rank, target, target_label, target_rank, row}``

    ``row`` collapses to ``None`` at the ladder ceiling / floor of the
    source axis (``target is None``) and on a builder failure,
    matching the diff envelope's posture. Never raises -- every
    fallback collapses to a fully-populated envelope with ``row=None``
    so the batch keeps the per-source row visible even when its
    per-pair capacity row could not be built.
    """
    src = (source or "").strip().lower()
    row: dict | None = None
    if target is not None:
        try:
            row = capacity_diff_at(src, target)
        except Exception as exc:
            logger.warning(
                "entitlements: _capacity_diff_at_envelope builder failed for %s->%s: %s",
                src,
                target,
                exc,
            )
            row = None
    return {
        "tier": src,
        "tier_label": tier_label(src) if src in _TIER_ORDER else None,
        "tier_rank": tier_rank(src) if src in _TIER_ORDER else -1,
        "target": target,
        "target_label": tier_label(target) if target else None,
        "target_rank": tier_rank(target) if target else None,
        "row": row,
    }


def next_tier_capacity_diff_at_batch() -> list[dict]:
    """Batch sibling of :func:`next_tier_capacity_diff_at`: one
    ``next-tier-capacity-diff-at`` envelope per purchasable source
    tier, in one pass.

    Capacity-only narrow-lens mirror of :func:`next_tier_diff_at_batch`:
    where that batch returns the full :func:`tier_diff` payload for
    each ``source -> next-above-source`` pair, this batch returns only
    the capacity slice (the ``{target, channel_limit, retention_days,
    node_limit}`` shape :func:`capacity_diff_at` publishes). Lets a
    pricing-comparison matrix UI render the "capacity at the rung
    above each rung" upgrade tooltip column off **one** round-trip
    instead of N calls to :func:`next_tier_capacity_diff_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/next-tier-capacity-diff-at?tier=<source>``
    response body for the same source (sans the resolver-context
    fields the route adds around the helper output) -- a parity test
    pins this so the batch what-if cannot drift from the scalar
    what-if (the same invariant :func:`next_tier_diff_at_batch`
    enforces against :func:`next_tier_diff_at`).

    Per-slice parity with :func:`next_tier_diff_at_batch`: each
    envelope's ``row`` byte-equals the corresponding diff batch
    envelope's ``row.capacity_changes`` for the same source -- pinned
    so the capacity batch cannot silently desync from the full diff
    batch as the catalogue evolves.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`next_tier_diff_at_batch` /
    :func:`next_tier_unlocks_at_batch` / :func:`next_tier_locks_at_batch`
    so a UI can fold the four responses into one matrix without
    re-sorting client-side. Same-rank sibling tiers (``cloud_pro`` /
    ``pro`` both at rank 2) are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`next_tier_diff_at_batch`. The source-side ceiling
    (``enterprise`` as source -- no rung strictly above) surfaces with
    ``target=None`` and ``row=None`` rather than being dropped, so the
    matrix keeps a row for every purchasable rung.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _next_purchasable_tier_after(tid)
            out.append(_capacity_diff_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning(
            "entitlements: next_tier_capacity_diff_at_batch failed: %s", exc
        )
        return []


def previous_tier_capacity_diff_at_batch() -> list[dict]:
    """Batch sibling of :func:`previous_tier_capacity_diff_at`: one
    ``previous-tier-capacity-diff-at`` envelope per purchasable source
    tier, in one pass.

    Source-anchored downgrade-side mirror of
    :func:`next_tier_capacity_diff_at_batch` and capacity-only narrow
    lens of :func:`previous_tier_diff_at_batch`. Lets a pricing-
    comparison matrix UI render the "capacity at the rung below each
    rung" downgrade tooltip column off **one** round-trip instead of N
    calls to :func:`previous_tier_capacity_diff_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/previous-tier-capacity-diff-at?tier=<source>``
    response body for the same source (sans the resolver-context
    fields the route adds around the helper output) -- a parity test
    pins this so the batch what-if cannot drift from the scalar
    what-if.

    Per-slice parity with :func:`previous_tier_diff_at_batch`: each
    envelope's ``row`` byte-equals the corresponding diff batch
    envelope's ``row.capacity_changes`` for the same source -- pinned
    so the capacity batch cannot silently desync from the full diff
    batch.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`previous_tier_diff_at_batch` /
    :func:`previous_tier_unlocks_at_batch` /
    :func:`previous_tier_locks_at_batch` so a UI can fold the four
    responses into one matrix without re-sorting client-side. Same-
    rank sibling tiers are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching :func:`previous_tier_diff_at_batch`. The source-side
    floor (``oss`` / ``cloud_free`` as source -- no rung strictly
    below) surfaces with ``target=None`` and ``row=None`` rather than
    being dropped, so the matrix keeps a row for every purchasable
    rung.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _previous_purchasable_tier_before(tid)
            out.append(_capacity_diff_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_capacity_diff_at_batch failed: %s",
            exc,
        )
        return []


def next_tier_spec_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.next_tier_spec`:
    full :func:`tier_spec_at`-shape descriptor of the rung above the
    caller-supplied ``tier``, with ``is_current`` computed as if the
    install were on ``tier``.

    Source-anchored equivalent of :meth:`Entitlement.next_tier_spec`,
    which pins the perspective to the resolved entitlement. Convenience
    for ``tier_spec_at(tier, _next_purchasable_tier_after(tier))`` so a
    pricing-table cell can render the full tier-row of the rung above
    any hypothetical source rung without first asking the resolver and
    without monkey-patching the entitlement context. Pairs with
    :func:`next_tier_diff_at` (full ``upgrade_diff`` payload),
    :func:`next_tier_unlocks_at` / :func:`next_tier_locks_at` (the
    marginal-grant / marginal-loss views), and
    :func:`next_tier_capacity_diff_at` (capacity-only) on the same
    hypothetical pricing-matrix cell.

    The returned row matches :func:`tier_spec_at(tier, target)` for the
    resolved ``target = _next_purchasable_tier_after(tier)`` exactly --
    a parity test pins this so the scalar accessors cannot drift. The
    ``is_current`` field is always ``False`` (target is by definition
    strictly above source, so it cannot equal it).

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture, matching the other ``next_*_at``
    helpers.

    Returns ``None`` for empty / unknown ``tier`` and at the ceiling
    (no rung strictly above -- enterprise as source). Never raises:
    a builder failure short-circuits to ``None`` so the CTA surface
    stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return tier_spec_at(src, target)
    except Exception as exc:
        logger.warning("entitlements: next_tier_spec_at failed: %s", exc)
        return None


def previous_tier_spec_at(tier: str) -> dict | None:
    """Scalar what-if sibling of :meth:`Entitlement.previous_tier_spec`:
    full :func:`tier_spec_at`-shape descriptor of the rung below the
    caller-supplied ``tier``, with ``is_current`` computed as if the
    install were on ``tier``.

    Source-anchored mirror of :func:`next_tier_spec_at` and downgrade-
    side counterpart of the live :meth:`Entitlement.previous_tier_spec`
    (which pins the perspective to the resolved entitlement).
    Convenience for ``tier_spec_at(tier, _previous_purchasable_tier_before(tier))``
    so a downgrade-confirmation card or pricing-comparison cell can
    render the full tier-row of the rung below any hypothetical source
    rung without first asking the resolver.

    Like :func:`next_tier_spec_at` the row matches
    :func:`tier_spec_at(tier, target)` for the resolved
    ``target = _previous_purchasable_tier_before(tier)`` exactly, and
    the ``is_current`` field is always ``False`` (target is by definition
    strictly below source, so it cannot equal it).

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` and at the floor
    (oss / cloud_free as source -- no rung strictly below). Never
    raises: a builder failure short-circuits to ``None`` so the
    confirmation surface stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return tier_spec_at(src, target)
    except Exception as exc:
        logger.warning("entitlements: previous_tier_spec_at failed: %s", exc)
        return None


def _spec_at_envelope(source: str, target: str | None) -> dict:
    """Private builder for the ``{next,previous}_tier_spec_at_batch`` rows.

    Spec-shaped sibling of :func:`_diff_at_envelope` and
    :func:`_capacity_diff_at_envelope`: where those builders carry the
    full :func:`tier_diff` row / capacity-only :func:`capacity_diff_at`
    row pinned on both endpoints, this one carries the cumulative
    :func:`tier_spec_at` row (the ``{id, label, is_paid, is_current,
    rank, unlocks_paid_runtimes, retention_days, channel_limit,
    node_limit, features, runtimes}`` shape ``tier_spec_at`` publishes)
    pinned on both ``source`` and ``target``.

    Envelope shape matches the diff / capacity ``_at`` envelopes
    byte-for-byte on the source / target metadata so a UI can fold the
    four batches into one pricing-comparison matrix without re-keying::

        ``{tier, tier_label, tier_rank, target, target_label, target_rank, row}``

    ``row`` collapses to ``None`` at the ladder ceiling / floor of the
    source axis (``target is None``) and on a :func:`tier_spec_at`
    builder failure, matching the diff / capacity envelopes. Never
    raises -- every fallback collapses to a fully-populated envelope
    with ``row=None`` so the batch keeps the per-source row visible
    even when its per-pair spec row could not be built.
    """
    src = (source or "").strip().lower()
    row: dict | None = None
    if target is not None:
        try:
            row = tier_spec_at(src, target)
        except Exception as exc:
            logger.warning(
                "entitlements: _spec_at_envelope builder failed for %s->%s: %s",
                src,
                target,
                exc,
            )
            row = None
    return {
        "tier": src,
        "tier_label": tier_label(src) if src in _TIER_ORDER else None,
        "tier_rank": tier_rank(src) if src in _TIER_ORDER else -1,
        "target": target,
        "target_label": tier_label(target) if target else None,
        "target_rank": tier_rank(target) if target else None,
        "row": row,
    }


def next_tier_spec_at_batch() -> list[dict]:
    """Batch sibling of :func:`next_tier_spec_at`: one
    ``next-tier-spec-at`` envelope per purchasable source tier, in one
    pass.

    Spec-shaped sibling of :func:`next_tier_diff_at_batch` (full
    :func:`tier_diff` payload), :func:`next_tier_unlocks_at_batch`
    (marginal grants), :func:`next_tier_locks_at_batch` (marginal
    losses), and :func:`next_tier_capacity_diff_at_batch` (capacity-only
    diff). Where the diff batches answer "what *changes* at the rung
    above each rung", this batch answers "what does the rung above each
    rung *look like*" -- the cumulative :func:`tier_spec_at` row
    (``id``, ``label``, ``is_paid``, ``is_current``, ``rank``,
    ``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
    ``node_limit``, ``features``, ``runtimes``) so a pricing-comparison
    matrix UI can render the "full descriptor of the rung above each
    rung" upgrade-CTA column off **one** round-trip instead of N calls
    to :func:`next_tier_spec_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/next-tier-spec-at?tier=<source>`` response body
    for the same source (sans the resolver-context fields the route
    adds around the helper output) -- a parity test pins this so the
    batch what-if cannot drift from the scalar what-if (the same
    invariant :func:`next_tier_diff_at_batch` enforces against
    :func:`next_tier_diff_at`).

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`next_tier_diff_at_batch` /
    :func:`next_tier_unlocks_at_batch` / :func:`next_tier_locks_at_batch`
    / :func:`next_tier_capacity_diff_at_batch` so a UI can fold the
    five responses into one matrix without re-sorting client-side.
    Same-rank sibling tiers (``cloud_pro`` / ``pro`` both at rank 2)
    are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching the other ``next_*_at_batch`` siblings. The source-side
    ceiling (``enterprise`` as source -- no rung strictly above)
    surfaces with ``target=None`` and ``row=None`` rather than being
    dropped, so the matrix keeps a row for every purchasable rung.

    Each populated ``row``'s ``is_current`` field is always ``False``
    (target is by definition strictly above source, so it cannot equal
    it) -- mirrors :func:`next_tier_spec_at`.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _next_purchasable_tier_after(tid)
            out.append(_spec_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning("entitlements: next_tier_spec_at_batch failed: %s", exc)
        return []


def previous_tier_spec_at_batch() -> list[dict]:
    """Batch sibling of :func:`previous_tier_spec_at`: one
    ``previous-tier-spec-at`` envelope per purchasable source tier, in
    one pass.

    Source-anchored downgrade-side mirror of
    :func:`next_tier_spec_at_batch` and spec-shaped sibling of
    :func:`previous_tier_diff_at_batch`,
    :func:`previous_tier_unlocks_at_batch`,
    :func:`previous_tier_locks_at_batch`, and
    :func:`previous_tier_capacity_diff_at_batch`. Lets a pricing-
    comparison matrix UI render the "full descriptor of the rung below
    each rung" downgrade-confirmation column off **one** round-trip
    instead of N calls to :func:`previous_tier_spec_at`.

    Each envelope is byte-equal to the scalar
    ``/api/entitlement/previous-tier-spec-at?tier=<source>`` response
    body for the same source (sans the resolver-context fields the
    route adds around the helper output) -- a parity test pins this so
    the batch what-if cannot drift from the scalar what-if.

    Envelopes are sorted by source ``(tier_rank, tier_id)`` ascending
    -- byte-stable against :func:`previous_tier_diff_at_batch` /
    :func:`previous_tier_unlocks_at_batch` /
    :func:`previous_tier_locks_at_batch` /
    :func:`previous_tier_capacity_diff_at_batch` so a UI can fold the
    five responses into one matrix without re-sorting client-side.
    Same-rank sibling tiers are both returned.

    Source list is :data:`_PURCHASABLE_TIERS` (trial excluded),
    matching the other ``previous_*_at_batch`` siblings. The
    source-side floor (``oss`` / ``cloud_free`` as source -- no rung
    strictly below) surfaces with ``target=None`` and ``row=None``
    rather than being dropped, so the matrix keeps a row for every
    purchasable rung.

    Each populated ``row``'s ``is_current`` field is always ``False``
    (target is by definition strictly below source) -- mirrors
    :func:`previous_tier_spec_at`.

    Decoupled from the resolved entitlement (walks the static
    catalogue), so grace vs enforce yields identical rows.

    Never raises: a per-source builder failure collapses to
    ``row=None`` on the populated envelope so the surrounding envelope
    stays visible; an unexpected top-level failure short-circuits to
    ``[]`` so the matrix keeps rendering instead of breaking.
    """
    try:
        out: list[dict] = []
        ordered = sorted(
            _PURCHASABLE_TIERS, key=lambda t: (_TIER_RANK.get(t, -1), t)
        )
        for tid in ordered:
            target = _previous_purchasable_tier_before(tid)
            out.append(_spec_at_envelope(tid, target))
        return out
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_spec_at_batch failed: %s", exc
        )
        return []


def next_tier_feature_spec_at(tier: str, feature: str) -> dict | None:
    """Scalar what-if sibling of :func:`next_tier_spec_at` projected onto a
    SINGLE feature: the :func:`feature_spec_at`-shape catalogue row for
    ``feature`` evaluated on the rung above the caller-supplied ``tier``.

    Feature-axis projection of :func:`next_tier_spec_at` (full tier-row
    descriptor of the rung above the source) and feature-side mirror of
    :func:`next_tier_runtime_spec_at`. Convenience for
    ``feature_spec_at(_next_purchasable_tier_after(tier), feature)`` so a
    pricing-table cell can ask "does THIS feature unlock at my next
    rung?" off ONE round-trip without first walking the catalogue or
    asking the resolver. Pairs with :func:`previous_tier_feature_spec_at`
    on the downgrade side and with :func:`next_tier_runtime_spec_at` /
    :func:`previous_tier_runtime_spec_at` on the runtime axis.

    The returned row matches :func:`feature_spec_at(target, feature)` for
    the resolved ``target = _next_purchasable_tier_after(tier)`` exactly
    -- a parity test pins this so the scalar projection cannot drift
    from the full-row sibling.

    Accepts any id in :data:`_TIER_ORDER` for ``tier`` (including
    :data:`TIER_TRIAL`) -- the lenient ``_at`` posture, matching the
    other ``next_*_at`` helpers.

    Returns ``None`` for empty / unknown ``tier`` or ``feature`` and at
    the ceiling (no rung strictly above -- enterprise as source). Never
    raises: a builder failure short-circuits to ``None`` so the CTA
    surface stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        f = (feature or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not f or f not in ALL_FEATURES:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return feature_spec_at(target, f)
    except Exception as exc:
        logger.warning("entitlements: next_tier_feature_spec_at failed: %s", exc)
        return None


def previous_tier_feature_spec_at(tier: str, feature: str) -> dict | None:
    """Scalar what-if sibling of :func:`previous_tier_spec_at` projected
    onto a SINGLE feature: the :func:`feature_spec_at`-shape catalogue
    row for ``feature`` evaluated on the rung below the caller-supplied
    ``tier``.

    Source-anchored mirror of :func:`next_tier_feature_spec_at` and
    downgrade-confirmation counterpart on the feature axis. Convenience
    for ``feature_spec_at(_previous_purchasable_tier_before(tier),
    feature)`` so a downgrade-confirmation card can ask "does THIS
    feature still unlock at my previous rung?" off ONE round-trip
    without re-walking the catalogue.

    Like :func:`next_tier_feature_spec_at` the row matches
    :func:`feature_spec_at(target, feature)` for the resolved
    ``target = _previous_purchasable_tier_before(tier)`` exactly.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`)
    -- the lenient ``_at`` posture.

    Returns ``None`` for empty / unknown ``tier`` or ``feature`` and at
    the floor (``oss`` / ``cloud_free`` as source -- no rung strictly
    below). Never raises: a builder failure short-circuits to ``None``
    so the confirmation surface stays mute instead of breaking.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    try:
        f = (feature or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not f or f not in ALL_FEATURES:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return feature_spec_at(target, f)
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_feature_spec_at failed: %s", exc
        )
        return None


def next_tier_runtime_spec_at(tier: str, runtime: str) -> dict | None:
    """Scalar what-if sibling of :func:`next_tier_spec_at` projected onto a
    SINGLE runtime: the :func:`runtime_spec_at`-shape catalogue row for
    ``runtime`` evaluated on the rung above the caller-supplied ``tier``.

    Runtime-axis projection of :func:`next_tier_spec_at` and runtime-side
    mirror of :func:`next_tier_feature_spec_at`. Convenience for
    ``runtime_spec_at(_next_purchasable_tier_after(tier), runtime)`` so a
    pricing-table cell can ask "does THIS runtime unlock at my next
    rung?" off ONE round-trip without first walking the catalogue.

    Accepts aliases (``claude-code`` -> ``claude_code``) via
    :func:`canonical_runtime` so the URL surface matches what callers
    already pass to ``/api/entitlement/required-tier`` and
    ``/runtime-spec-at``.

    The returned row matches :func:`runtime_spec_at(target, runtime)`
    for the resolved ``target = _next_purchasable_tier_after(tier)``
    exactly -- a parity test pins this so the scalar projection cannot
    drift from the full-row sibling.

    Accepts any id in :data:`_TIER_ORDER` for ``tier`` (including
    :data:`TIER_TRIAL`).

    Returns ``None`` for empty / unknown ``tier`` or ``runtime`` and at
    the ceiling (no rung strictly above). Never raises.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    rt = canonical_runtime(runtime)
    if not rt or rt not in ALL_RUNTIMES:
        return None
    try:
        target = _next_purchasable_tier_after(src)
        if target is None:
            return None
        return runtime_spec_at(target, rt)
    except Exception as exc:
        logger.warning("entitlements: next_tier_runtime_spec_at failed: %s", exc)
        return None


def previous_tier_runtime_spec_at(tier: str, runtime: str) -> dict | None:
    """Scalar what-if sibling of :func:`previous_tier_spec_at` projected
    onto a SINGLE runtime: the :func:`runtime_spec_at`-shape catalogue
    row for ``runtime`` evaluated on the rung below the caller-supplied
    ``tier``.

    Source-anchored mirror of :func:`next_tier_runtime_spec_at` and
    downgrade-confirmation counterpart on the runtime axis. Convenience
    for ``runtime_spec_at(_previous_purchasable_tier_before(tier),
    runtime)``.

    Accepts aliases (``claude-code`` -> ``claude_code``) via
    :func:`canonical_runtime`.

    Like :func:`next_tier_runtime_spec_at` the row matches
    :func:`runtime_spec_at(target, runtime)` for the resolved
    ``target = _previous_purchasable_tier_before(tier)`` exactly.

    Accepts any id in :data:`_TIER_ORDER` (including :data:`TIER_TRIAL`).

    Returns ``None`` for empty / unknown ``tier`` or ``runtime`` and at
    the floor (``oss`` / ``cloud_free`` as source). Never raises.
    """
    try:
        src = (tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if not src or src not in _TIER_ORDER:
        return None
    rt = canonical_runtime(runtime)
    if not rt or rt not in ALL_RUNTIMES:
        return None
    try:
        target = _previous_purchasable_tier_before(src)
        if target is None:
            return None
        return runtime_spec_at(target, rt)
    except Exception as exc:
        logger.warning(
            "entitlements: previous_tier_runtime_spec_at failed: %s", exc
        )
        return None


def tier_spec_path(from_tier: str, to_tier: str) -> list[dict] | None:
    """Arbitrary-endpoint stepwise spec-shaped path between two tiers.

    Spec-shaped sibling of :func:`tier_path` (full ``tier_diff`` per
    rung), :func:`capacity_diff_path` (capacity-only per rung),
    :func:`tier_unlocks_path` (marginal grants per rung),
    :func:`tier_locks_path` (marginal losses per rung), and
    :func:`preview_path` (cumulative ``Entitlement.to_dict`` per rung)
    -- the spec-shaped member of the ``_path`` family, the path-shaped
    sibling of :func:`tier_spec_at_batch` (which is a fixed-source what-
    if matrix over many targets) and the bulk what-if cousin of
    :func:`tier_spec_at`. Lets a pricing-comparison "compare A vs B"
    surface render the slim catalogue-shaped descriptor
    (``id``, ``label``, ``is_paid``, ``is_current``, ``rank``,
    ``unlocks_paid_runtimes``, ``retention_days``, ``channel_limit``,
    ``node_limit``, ``features``, ``runtimes``) at every rung between
    any two tiers off ONE round-trip, without folding marketing fields
    (``is_paid``, ``label``, ``unlocks_paid_runtimes``) back in from a
    separate ``/tier-catalog`` lookup the way a ``/preview-path`` row
    forces.

    Per-rung row shape matches :func:`tier_spec_at` exactly -- the same
    key set with ``is_current`` always ``False`` on walked rungs
    (``from_tier`` is excluded from the walked set, so the rung-equals-
    from-tier perspective never appears) -- so a UI that already
    renders a ``/tier-spec-at`` row needs zero new shape code to render
    a per-rung row off this path. A parity test pins this so the
    scalar what-if and path what-if cannot drift.

    Walk semantics mirror :func:`tier_path` / :func:`capacity_diff_path`
    / :func:`tier_unlocks_path` / :func:`tier_locks_path` /
    :func:`preview_path` byte-for-byte (same ``_PURCHASABLE_TIERS``
    filter + same sort key + same destination-sibling exclusion), so
    the rung ``id`` ids from this helper line up rung-for-rung against
    the rung ``tier`` ids from those five helpers -- the six paths
    walk the same rungs in the same order. Same-rank siblings strictly
    between the endpoints are both included (matching :func:`tier_path`
    's ladder shape); same-rank siblings of the destination are
    excluded so the path terminates exactly at ``to_tier`` and not at
    one of its rank peers.

    Direction semantics (all rows share the same cumulative spec
    shape; only the sequence changes):

    * ``upgrade`` (ascending) -- rows climb cumulatively from the rung
      above ``from_tier`` toward ``to_tier``; the natural "what does
      each rung above me look like" walkthrough.
    * ``downgrade`` (descending) -- rows shrink cumulatively rung by
      rung; the cancellation-walkthrough counterpart.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the cumulative spec at ``to_tier``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`tier_diff`:
    both ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- it is excluded
    from the walked intermediate rungs but is a valid endpoint via the
    lateral branch). Unknown ids on either side short-circuit to
    ``None``.

    Resolver-independent: walks the static per-tier maps via
    :func:`tier_spec_at` (which pins ``is_current`` to the hypothetical
    perspective of ``from_tier``, not the live resolved entitlement),
    so flipping enforce on yields byte-identical rows -- same property
    the rest of the ``_path`` family guarantees.

    Never raises: a resolver failure logs a warning and returns
    ``None`` so a pricing-page surface keeps rendering instead of
    breaking.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)
        if from_rank == to_rank:
            row = tier_spec_at(f, t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = tier_spec_at(f, tid)
            if row is not None:
                path.append(row)
        return path
    except Exception as exc:
        logger.warning("entitlements: tier_spec_path failed: %s", exc)
        return None


def feature_spec_path(
    from_tier: str, to_tier: str, feature: str
) -> list[dict] | None:
    """Arbitrary-endpoint stepwise single-feature spec path between two tiers.

    Single-feature sibling of :func:`tier_spec_path` (full slim spec per
    rung) and perspective-walked sibling of :func:`feature_spec_at`. Lets a
    paywall "how does THIS one feature unlock as I climb the ladder" UI
    render every rung's ``allowed`` / ``locked`` / ``entitled`` status off
    ONE round-trip without fetching the full :func:`feature_catalog_at` at
    every rung.

    Walks the same ``_PURCHASABLE_TIERS`` rungs by the same sort key and
    same destination-sibling exclusion as :func:`tier_path`,
    :func:`tier_spec_path`, :func:`capacity_diff_path`,
    :func:`tier_unlocks_path`, :func:`tier_locks_path` and
    :func:`preview_path` -- rung-for-rung byte-stable against the six
    existing ``_path`` helpers, so a UI that walks one helper's rows can
    line them up index-for-index with another helper's rows without
    re-deriving the rung sequence.

    Per-rung row shape: each row is the :func:`feature_spec_at` body
    (``id``, ``label``, ``tier``, ``tiers``, ``free``, ``allowed``,
    ``locked``, ``entitled``, ``alias``) augmented with three rung-
    identification keys -- ``rung``, ``rung_label``, ``rung_rank`` --
    naming the perspective tier the row was computed at. Dropping the
    three ``rung*`` keys yields exact byte-equality with
    :func:`feature_spec_at(rung, feature)` -- a parity test pins this so
    the scalar what-if and the path what-if cannot drift. The static
    feature-property fields (``id``, ``label``, ``tier``, ``tiers``,
    ``free``, ``alias``) stay constant across all rows; only the
    perspective-dependent fields (``allowed``, ``locked``, ``entitled``)
    vary rung by rung -- the visible "unlock boundary" the UI renders.

    Direction semantics mirror :func:`tier_spec_path` / :func:`tier_path`:

    * ``upgrade`` (ascending) -- rows climb rung by rung from the rung
      above ``from_tier`` toward ``to_tier``; the natural "what does this
      feature look like at each rung I'd climb through" walkthrough.
    * ``downgrade`` (descending) -- rows shrink rung by rung; the
      cancellation-walkthrough counterpart showing when the feature
      becomes locked again.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the spec at ``to_tier``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`tier_spec_path`:
    both tier ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- excluded from the
    walked intermediate rungs but a valid endpoint via the lateral
    branch). Unknown tier or feature ids on either side short-circuit to
    ``None``.

    Resolver-independent: walks the static per-tier maps via
    :func:`feature_spec_at` so grace vs enforce yields byte-identical
    rows -- same property the rest of the ``_path`` family guarantees.

    Never raises: a resolver failure logs a warning and returns ``None``
    so a paywall surface keeps rendering instead of breaking.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        fid = (feature or "").strip().lower()
        if not fid or fid not in ALL_FEATURES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)

        def _row(rung: str) -> dict | None:
            body = feature_spec_at(rung, fid)
            if body is None:
                return None
            return {
                "rung": rung,
                "rung_label": tier_label(rung),
                "rung_rank": _TIER_RANK.get(rung, -1),
                **body,
            }

        if from_rank == to_rank:
            row = _row(t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = _row(tid)
            if row is not None:
                path.append(row)
        return path
    except Exception as exc:
        logger.warning("entitlements: feature_spec_path failed: %s", exc)
        return None


def runtime_spec_path(
    from_tier: str, to_tier: str, runtime: str
) -> list[dict] | None:
    """Arbitrary-endpoint stepwise single-runtime spec path between two tiers.

    Runtime-axis twin of :func:`feature_spec_path` -- the single-runtime
    sibling of :func:`tier_spec_path` and perspective-walked sibling of
    :func:`runtime_spec_at`. Lets a paywall "how does THIS one runtime
    unlock as I climb the ladder" UI render every rung's ``allowed`` /
    ``locked`` / ``entitled`` status off ONE round-trip without fetching
    the full :func:`runtime_catalog_at` at every rung.

    Accepts runtime aliases (``claude-code`` -> ``claude_code``) via
    :func:`canonical_runtime` so the URL surface matches what callers
    already pass to ``/api/entitlement/required-tier``.

    Walks the same ``_PURCHASABLE_TIERS`` rungs by the same sort key and
    same destination-sibling exclusion as the rest of the ``_path``
    family -- rung-for-rung byte-stable against
    :func:`feature_spec_path`, :func:`tier_path`, :func:`tier_spec_path`,
    :func:`capacity_diff_path`, :func:`tier_unlocks_path`,
    :func:`tier_locks_path` and :func:`preview_path`.

    Per-rung row shape: each row is the :func:`runtime_spec_at` body
    (``id``, ``label``, ``free``, ``tier``, ``tiers``, ``allowed``,
    ``locked``, ``entitled``) augmented with three rung-identification
    keys -- ``rung``, ``rung_label``, ``rung_rank`` -- naming the
    perspective tier the row was computed at. Dropping the three
    ``rung*`` keys yields exact byte-equality with
    :func:`runtime_spec_at(rung, runtime)` -- a parity test pins this so
    the scalar what-if and the path what-if cannot drift.

    Direction semantics mirror :func:`feature_spec_path` /
    :func:`tier_spec_path`. Endpoint semantics match :func:`tier_path`:
    both tier ids accept any entry in :data:`_TIER_FEATURES`. Unknown
    tier or runtime ids short-circuit to ``None``. Empty / whitespace
    runtime short-circuits to ``None``.

    Resolver-independent: walks the static per-tier maps via
    :func:`runtime_spec_at` so grace vs enforce yields byte-identical
    rows.

    Never raises: a resolver failure logs a warning and returns ``None``.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None
        rt = canonical_runtime(runtime)
        if not rt or rt not in ALL_RUNTIMES:
            return None
        if f == t:
            return []
        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)

        def _row(rung: str) -> dict | None:
            body = runtime_spec_at(rung, rt)
            if body is None:
                return None
            return {
                "rung": rung,
                "rung_label": tier_label(rung),
                "rung_rank": _TIER_RANK.get(rung, -1),
                **body,
            }

        if from_rank == to_rank:
            row = _row(t)
            return [row] if row is not None else []
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            row = _row(tid)
            if row is not None:
                path.append(row)
        return path
    except Exception as exc:
        logger.warning("entitlements: runtime_spec_path failed: %s", exc)
        return None


def lock_reason_path(
    from_tier: str, to_tier: str, item, *, kind: str | None = None
) -> list[dict] | None:
    """Arbitrary-endpoint stepwise lock-row path between two tiers.

    Single-item path-walking sibling of :func:`lock_reason_at` and
    lock-row analogue of :func:`feature_spec_path` / :func:`runtime_spec_path`.
    Lets a paywall "how does THIS one lock-row evolve as I climb the
    ladder" UI render every rung's ``locked`` / ``allowed`` / ``reason``
    string off ONE round-trip without fetching the full
    :func:`lock_reasons_at_batch` payload at every rung.

    Walks the same ``_PURCHASABLE_TIERS`` rungs by the same sort key and
    same destination-sibling exclusion as :func:`tier_path`,
    :func:`tier_spec_path`, :func:`capacity_diff_path`,
    :func:`tier_unlocks_path`, :func:`tier_locks_path`, :func:`preview_path`,
    :func:`feature_spec_path` and :func:`runtime_spec_path` -- rung-for-rung
    byte-stable against the rest of the ``_path`` family, so a UI that
    walks one helper's rows can line them up index-for-index with another
    helper's rows without re-deriving the rung sequence.

    Per-rung row shape: each row is the :func:`_lock_row` body (``key``,
    ``kind``, ``reason``, ``locked``, ``allowed``, ``required_tier``,
    ``required_tier_label``, ``required_tier_rank``) augmented with three
    rung-identification keys -- ``rung``, ``rung_label``, ``rung_rank`` --
    naming the perspective tier the row was computed at. Dropping the
    three ``rung*`` keys yields exact byte-equality with a synthesised
    ``lock_reasons_at_batch`` axis row at the same rung -- a parity test
    pins this so the path what-if and the batch what-if cannot drift.

    ``kind`` follows :meth:`Entitlement.lock_reason`: ``"feature"`` /
    ``"runtime"`` / ``"channels"`` / ``"retention_days"`` / ``"nodes"``
    explicitly; ``None`` lets the helper infer ``runtime`` vs ``feature``
    from the id (capacity axes can't be inferred, so pass ``kind=`` for
    those). Runtime ids are canonicalised (``claude-code`` ->
    ``claude_code``) so the URL surface matches the rest of the
    entitlement API.

    Direction semantics mirror :func:`feature_spec_path` /
    :func:`tier_spec_path`:

    * ``upgrade`` (ascending) -- rows climb rung by rung from the rung
      above ``from_tier`` toward ``to_tier``; the natural "what does this
      lock-row look like at each rung I'd climb through" walkthrough.
    * ``downgrade`` (descending) -- rows shrink rung by rung; the
      cancellation-walkthrough counterpart showing when the item becomes
      locked again.
    * ``lateral`` (same rank, different id) -- single-row path; row
      carries the lock-row at ``to_tier``.
    * ``identity`` (``from == to``) -- empty path; no rungs to walk.

    Endpoint semantics match :func:`tier_path` / :func:`feature_spec_path`:
    both tier ids accept any entry in :data:`_TIER_FEATURES` (including
    :data:`TIER_TRIAL`, which is not purchasable -- excluded from the
    walked intermediate rungs but a valid endpoint via the lateral
    branch). Unknown ids on either side short-circuit to ``None``.
    Unknown / empty / non-positive capacity counts short-circuit to
    ``None`` rather than emitting an "always allowed" row -- matches the
    400 posture the route surfaces for malformed capacity input.

    Resolver-independent: synthesises a fresh :class:`Entitlement` per
    rung with ``grace=False`` and the per-tier capacity caps off
    :data:`_TIER_NODE_LIMIT`, mirroring :func:`lock_reason_at` /
    :func:`lock_reasons_at_batch` -- so grace vs enforce yields
    byte-identical rows.

    Never raises: a synthesis failure logs a warning and short-circuits
    to ``None`` so a paywall surface keeps rendering instead of breaking.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
        if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
            return None

        try:
            raw_item = "" if item is None else str(item).strip()
        except Exception:
            return None
        if not raw_item:
            return None
        item_lc = raw_item.lower()

        resolved_kind = kind
        if resolved_kind is None:
            if item_lc in ALL_RUNTIMES:
                resolved_kind = "runtime"
            elif item_lc in ALL_FEATURES:
                resolved_kind = "feature"
            else:
                return None
        if resolved_kind == "runtime":
            canon = canonical_runtime(item_lc)
            if not canon or canon not in ALL_RUNTIMES:
                return None
            row_key: str = canon
        elif resolved_kind == "feature":
            if item_lc not in ALL_FEATURES:
                return None
            row_key = item_lc
        elif resolved_kind in ("channels", "retention_days", "nodes"):
            try:
                n = int(raw_item)
            except (TypeError, ValueError):
                return None
            if n <= 0:
                return None
            row_key = str(n)
        else:
            return None

        if f == t:
            return []

        from_rank = _TIER_RANK.get(f, -1)
        to_rank = _TIER_RANK.get(t, -1)

        def _synth(rung: str):
            paid_feats = _TIER_FEATURES.get(rung, frozenset())
            rts = (
                (FREE_RUNTIMES | PAID_RUNTIMES)
                if rung in _TIER_PAID_RUNTIMES
                else FREE_RUNTIMES
            )
            return Entitlement(
                tier=rung,
                source="hypothetical",
                node_limit=_TIER_NODE_LIMIT.get(rung, _FREE_NODE_LIMIT),
                expiry=None,
                features=FREE_FEATURES | paid_feats,
                runtimes=rts,
                grace=False,
            )

        def _row(rung: str) -> dict:
            try:
                ent = _synth(rung)
            except Exception as exc:
                logger.warning(
                    "entitlements: lock_reason_path synth failed for %s: %s",
                    rung,
                    exc,
                )
                ent = _oss_free()
            body = _lock_row(ent, row_key, resolved_kind)
            return {
                "rung": rung,
                "rung_label": tier_label(rung),
                "rung_rank": _TIER_RANK.get(rung, -1),
                **body,
            }

        if from_rank == to_rank:
            return [_row(t)]
        ascending = to_rank > from_rank
        if ascending:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (_TIER_RANK.get(x, -1), x),
            )
        else:
            ordered = sorted(
                _PURCHASABLE_TIERS,
                key=lambda x: (-_TIER_RANK.get(x, -1), x),
            )
        path: list[dict] = []
        for tid in ordered:
            r = _TIER_RANK.get(tid, -1)
            if ascending:
                if r <= from_rank or r > to_rank:
                    continue
            else:
                if r >= from_rank or r < to_rank:
                    continue
            if r == to_rank and tid != t:
                continue
            path.append(_row(tid))
        return path
    except Exception as exc:
        logger.warning("entitlements: lock_reason_path failed: %s", exc)
        return None


def feature_spec_path_batch(
    from_tier: str, to_tier: str, features
) -> dict | None:
    """Batch sibling of :func:`feature_spec_path`: per-rung spec rows for a
    caller-supplied subset of feature ids walked between two tiers in ONE
    round-trip.

    Composes :func:`feature_spec_path` (scalar single-feature path) and
    :func:`feature_spec_at_batch` (batch what-if scalar) -- same rung
    walk as the path helper, same per-feature shape as the batch helper.
    Lets a pricing-comparison "compare A vs B, here are the 6 features I
    care about" surface render every rung for every feature off ONE call
    instead of N calls to :func:`feature_spec_path`.

    Per-feature row shape::

        {"feature": "<id>", "path": [<feature_spec_path row>, ...]}

    Each ``path`` row is byte-identical to a row from
    :func:`feature_spec_path` for the same ``(from, to, feature)`` triple
    -- a parity test pins this so the scalar and batch path helpers
    cannot drift. The rungs walked are feature-agnostic (matches
    :func:`feature_spec_path`'s ``rung_walk_invariant_across_features``
    pin), so every per-feature ``path`` has the same length and rung
    sequence.

    Shape::

        {
          "features": [
            {"feature": "<id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown": ["bogus_id", ...],
        }

    Supplied feature ids are normalised via :func:`_normalise_csv`
    (whitespace stripped, lowercased, duplicates dropped, first-seen
    order preserved). Unknown ids are echoed in ``unknown[]`` instead of
    short-circuiting -- a partially-bad caller still gets paths back for
    the valid ids alongside a list of what was dropped, matching
    :func:`feature_spec_at_batch`'s posture.

    Returns ``None`` for empty / unknown ``from_tier`` / ``to_tier``
    (caller renders "unknown tier" / 404). Identity ``from == to`` yields
    ``{"features": [...empty path per feature...], "unknown": [...]}``
    matching the singular helper's identity branch.

    Resolver-independent: delegates per-feature to
    :func:`feature_spec_path`, which walks the static per-tier maps via
    :func:`feature_spec_at` -- so grace vs enforce yields byte-identical
    rows. Never raises: per-feature failures short-circuit that feature
    into ``unknown[]`` and the rest of the batch keeps building.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
        return None
    feats = _normalise_csv(features)
    rows: list[dict] = []
    unknown: list[str] = []
    for fid in feats:
        if fid not in ALL_FEATURES:
            unknown.append(fid)
            continue
        try:
            path = feature_spec_path(f, t, fid)
        except Exception as exc:
            logger.warning(
                "entitlements: feature_spec_path_batch row %r failed: %s",
                fid,
                exc,
            )
            unknown.append(fid)
            continue
        if path is None:
            unknown.append(fid)
            continue
        rows.append({"feature": fid, "path": path})
    return {"features": rows, "unknown": unknown}


def runtime_spec_path_batch(
    from_tier: str, to_tier: str, runtimes
) -> dict | None:
    """Runtime-axis twin of :func:`feature_spec_path_batch` -- batch
    sibling of :func:`runtime_spec_path` and runtime cousin of
    :func:`runtime_spec_at_batch`.

    Per-runtime row shape::

        {"runtime": "<canonical id>", "path": [<runtime_spec_path row>, ...]}

    Each ``path`` row is byte-identical to a row from
    :func:`runtime_spec_path` for the same ``(from, to, runtime)`` triple
    -- a parity test pins this. Rungs walked are runtime-agnostic, so
    every per-runtime ``path`` has the same length and rung sequence.

    Aliases are canonicalised via :func:`canonical_runtime`
    (``claude-code`` -> ``claude_code``) and aliases that collapse to a
    canonical id already in the response are silently de-duplicated --
    same behaviour as :func:`runtime_spec_at_batch`. The per-row
    ``runtime`` value carries the canonical id, never the supplied
    alias.

    Shape::

        {
          "runtimes": [
            {"runtime": "<canonical id>", "path": [<augmented row>, ...]},
            ...
          ],
          "unknown": ["bogus_id", ...],
        }

    Returns ``None`` for empty / unknown ``from_tier`` / ``to_tier``.
    Identity ``from == to`` yields ``{"runtimes": [...empty path per
    runtime...], "unknown": [...]}`` matching the singular helper's
    identity branch.

    Never raises: per-runtime failures short-circuit that runtime into
    ``unknown[]`` (carrying the supplied alias, not a canonical id, so
    the caller can correlate against what was sent) and the rest of the
    batch keeps building.
    """
    try:
        f = (from_tier or "").strip().lower()
        t = (to_tier or "").strip().lower()
    except (AttributeError, TypeError):
        return None
    if f not in _TIER_FEATURES or t not in _TIER_FEATURES:
        return None
    rts = _normalise_csv(runtimes)
    rows: list[dict] = []
    unknown: list[str] = []
    seen: set[str] = set()
    for raw in rts:
        canon = canonical_runtime(raw)
        if not canon or canon not in ALL_RUNTIMES:
            unknown.append(raw)
            continue
        if canon in seen:
            continue
        try:
            path = runtime_spec_path(f, t, raw)
        except Exception as exc:
            logger.warning(
                "entitlements: runtime_spec_path_batch row %r failed: %s",
                raw,
                exc,
            )
            unknown.append(raw)
            continue
        if path is None:
            unknown.append(raw)
            continue
        seen.add(canon)
        rows.append({"runtime": canon, "path": path})
    return {"runtimes": rows, "unknown": unknown}
