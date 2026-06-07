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

# Display labels for every known runtime. Mirrors ``_CM_RT_LABEL`` in
# ``clawmetry/static/js/app.js`` so the dashboard and the API agree on what to
# call each runtime in human-readable copy. The frontend falls back to the
# runtime id when a label is missing, so adding a runtime to ``PAID_RUNTIMES``
# without a label here is safe — but please add one.
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

# Starter-tier features (Starter and above). Each key maps to a feature that
# /pricing puts in the Starter card. Routes that implement these features call
# Entitlement.allows_feature(<key>) and return HTTP 402 in enforce mode.
STARTER_FEATURES = frozenset(
    {
        "multi_runtime",                  # Claude Code, Codex, Cursor, Aider, Goose, opencode, Qwen, Hermes
        "fleet",                          # multi-node fleet view
        "cloud_sync",                     # E2E-encrypted snapshot push to ClawMetry Cloud
        "all_channels",                   # all 21 channel adapters (Free is limited to 3)
        "approval_queue",                 # block tool calls by policy
        "budget_limits",                  # budget limits + alerts
        "per_runtime_health_timeline",    # the Overview sparkline
    }
)

# Pro-only features (Pro and above, NOT Starter). These are the "this product
# earns its keep at production scale" features per /pricing.
PRO_ONLY_FEATURES = frozenset(
    {
        "per_run_waste_flags",      # runaway / cold cache / bloated context heuristics
        "per_run_compare",          # A vs B side-by-side with deltas
        "error_triage",             # resolve / mute known errors
        "self_evolve",              # Self-Evolve findings + Fix-with-AI
        "asset_registry",           # skills, prompts, workflows promotion lifecycle
        "eval_suite",               # LLM-as-judge scoring
        "tool_policy",              # tool catalog policy + pre-execution gate
        "otel_export",              # moved from ENTERPRISE → Pro per /pricing
        "custom_webhooks",          # custom webhooks + PagerDuty + OpsGenie sinks
        "custom_runtime_ingest",    # custom runtime HTTP ingest API
        # Kept-for-backwards-compat aliases that older callers may import:
        "custom_alerts",
        "alert_webhooks",
        "anomaly_detection",
        "cost_optimizer",
    }
)

# All paid features (Starter ∪ Pro-only).
PAID_FEATURES = STARTER_FEATURES | PRO_ONLY_FEATURES

# Enterprise-only features (a strict superset on top of paid).
ENTERPRISE_FEATURES = frozenset(
    {
        "siem_export",            # NEW: Splunk / QRadar / ArcSight / Elastic
        "sso",                    # SAML / OIDC / Okta / Google / Azure AD
        "audit_logs",             # the audit-log API; the hash chain itself is Free, always on
        "rbac",                   # RBAC + teams + workspace scoping
        "air_gapped_license",     # offline license verification
        "custom_data_residency",  # NEW: choose where data lives (US / EU / Asia / on-prem)
    }
)

ALL_FEATURES = FREE_FEATURES | PAID_FEATURES | ENTERPRISE_FEATURES

# Per-tier paid feature grants (free features are always included on top).
_TIER_FEATURES = {
    TIER_OSS: frozenset(),
    TIER_CLOUD_FREE: frozenset(),
    TIER_TRIAL: PAID_FEATURES,                          # trial gets full Pro feature set
    TIER_CLOUD_STARTER: STARTER_FEATURES,               # explicit Starter slice
    TIER_CLOUD_PRO: PAID_FEATURES,                      # Starter + Pro-only
    TIER_PRO: PAID_FEATURES,                            # self-hosted Pro mirrors cloud Pro
    TIER_ENTERPRISE: PAID_FEATURES | ENTERPRISE_FEATURES,
}

# Per-tier event retention in days. None = unlimited / custom (Enterprise).
# Read by the daemon's prune loop in clawmetry/sync.py.
_TIER_RETENTION_DAYS = {
    TIER_OSS: 7,
    TIER_CLOUD_FREE: 7,
    TIER_TRIAL: 30,
    TIER_CLOUD_STARTER: 30,
    TIER_CLOUD_PRO: 90,
    TIER_PRO: 90,
    TIER_ENTERPRISE: None,
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

    def event_retention_days(self) -> int | None:
        """Days of event history this tier may keep. ``None`` means unlimited
        / custom (Enterprise). The daemon's prune loop in ``clawmetry/sync.py``
        reads this; if a customer override is set in env (``CLAWMETRY_RETENTION_DAYS``),
        the daemon prefers the env value when it's <= the tier cap (so users
        can voluntarily shrink, never silently expand).

        Per-tier values (see ``_TIER_RETENTION_DAYS``):
            Free / OSS:       7
            Starter / Trial: 30
            Pro / Self-host: 90
            Enterprise:      None  (custom)
        """
        return _TIER_RETENTION_DAYS.get(self.tier, 7)

    def allows_retention_window(self, days: int | None) -> bool:
        """Whether the install may query / keep a retention window of ``days``
        days of history.

        Sibling to :meth:`allows_runtime`, :meth:`allows_feature`, and the
        ``allows_node_count`` axis — gives the frontend (history-range toggles
        like "7 / 30 / 90 / all") and the daemon's prune loop a single
        canonical check, so neither has to re-derive tier→cap math.

        Semantics:

        * Grace mode: always ``True`` (no current behaviour changes pre-enforce).
        * ``days <= 0``: ``True`` — asking for zero history is trivially fine
          regardless of tier.
        * Expired entitlement: ``False`` for any positive window.
        * Enterprise (``event_retention_days() is None``): ``True`` for any
          finite or ``None`` (unlimited) request.
        * ``days is None`` (request unlimited) on a finite-cap tier: ``False``.
        * Otherwise: ``days <= cap``.
        """
        if self.grace:
            return True
        if days is not None and days <= 0:
            return True
        if self.expired:
            return False
        cap = self.event_retention_days()
        if cap is None:  # Enterprise: unlimited
            return True
        if days is None:  # caller asked for unlimited; only Enterprise grants it
            return False
        return days <= cap

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
    """Resolve a self-hosted entitlement from ``~/.clawmetry/license.key`` via
    the Ed25519 license client. An absent/forged/expired key yields None, so an
    unverified file can never grant access. Never raises."""
    try:
        if not os.path.isfile(_LICENSE_PATH):
            return None
        from clawmetry import license as _lic  # late import avoids import cycle

        return _lic.load_license(_LICENSE_PATH)
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


def runtime_label(runtime: str) -> str:
    """Human-readable label for ``runtime``. Falls back to the id when unknown
    so unknown plugin runtimes still render with *something*."""
    rt = (runtime or "").strip().lower()
    return RUNTIME_LABELS.get(rt, rt)


def runtime_catalog() -> list[dict]:
    """The full runtime catalog with the entitlement-derived availability for
    each entry. Single source of truth the UI uses to render *every* known
    runtime — including paid ones with zero local sessions — so the locked-
    but-visible upgrade affordance has data to render against.

    Each entry:
        {
          "id":       "<runtime>",         # canonical key
          "label":    "<Display Name>",    # falls back to id
          "free":     True | False,        # FREE_RUNTIMES membership
          "allowed":  True | False,        # entitlement allows observing it
          "locked":   True | False,        # paid + not allowed (UI shows 🔒)
        }

    Ordering: free runtimes first (alphabetical), then paid runtimes
    (alphabetical) — stable so the UI dropdown is deterministic.

    Never raises; on any resolution error every paid runtime is reported as
    ``locked=False`` (grace) to match the OSS-free fallback in
    :func:`get_entitlement`.
    """
    try:
        ent = get_entitlement()
    except Exception as exc:  # never crash a catalog read
        logger.warning("entitlements: runtime_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    out: list[dict] = []
    for rt in sorted(FREE_RUNTIMES):
        out.append(
            {
                "id": rt,
                "label": runtime_label(rt),
                "free": True,
                "allowed": True,
                "locked": False,
            }
        )
    for rt in sorted(PAID_RUNTIMES):
        allowed = ent.allows_runtime(rt)
        out.append(
            {
                "id": rt,
                "label": runtime_label(rt),
                "free": False,
                "allowed": allowed,
                "locked": not allowed,
            }
        )
    return out
