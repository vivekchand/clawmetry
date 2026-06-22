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


def feature_catalog() -> list[dict]:
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: feature_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    out: list[dict] = []
    for fid in sorted(ALL_FEATURES, key=lambda f: (_FEATURE_TIER_RANK.get(feature_tier(f), 9), f)):
        tier = feature_tier(fid)
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
                "tier": tier,
                "free": is_free,
                "allowed": allowed,
                "locked": (not is_free) and (not allowed),
                "entitled": entitled,
                "alias": fid in _ALIAS_FEATURES,
            }
        )
    return out


def runtime_catalog() -> list[dict]:
    try:
        ent = get_entitlement()
    except Exception as exc:
        logger.warning("entitlements: runtime_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    out: list[dict] = []
    for rt in sorted(FREE_RUNTIMES):
        out.append(
            {
                "id": rt,
                "label": runtime_label(rt),
                "free": True,
                "tier": "free",
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
                "allowed": allowed,
                "locked": not allowed,
                "entitled": ent.entitled_runtime(rt),
            }
        )
    return out


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
