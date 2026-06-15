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

# Common alternative spellings that callers (custom ingest, OTLP service.name,
# CLI flags) sometimes use. Mapped to the canonical snake_case identifier so the
# gate and the labels lookup don't reject a runtime over a stray hyphen. The
# canonical id is always the value; only the keys differ.
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

# Display labels for every known feature. Mirrors the runtime label map and is
# the source of truth the dashboard reads via ``/api/features`` so the locked-
# but-visible affordance on paid features renders human-readable copy. Adding a
# feature to one of the ``*_FEATURES`` sets without a label here is safe — the
# helper falls back to the id — but a missing label trips the catalogue
# conformance test in ``tests/test_entitlements_feature_catalog.py``.
FEATURE_LABELS = {
    # Free / core observability
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
    # Starter
    "multi_runtime": "Multi-runtime",
    "fleet": "Multi-node fleet",
    "cloud_sync": "Cloud sync",
    "all_channels": "All channels",
    "approval_queue": "Approval queue",
    "budget_limits": "Budget limits",
    "per_runtime_health_timeline": "Per-runtime health timeline",
    # Pro-only
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
    # Enterprise
    "siem_export": "SIEM export",
    "sso": "SSO",
    "audit_logs": "Audit logs",
    "rbac": "RBAC",
    "air_gapped_license": "Air-gapped license",
    "custom_data_residency": "Custom data residency",
}

# Backwards-compat alias keys living inside ``PRO_ONLY_FEATURES`` that older
# callers may still import. They satisfy ``allows_feature(...)`` for the
# canonical feature they alias, but the user-facing catalog (and so the
# upgrade copy) should hide them — listing them alongside the canonical
# keys advertises feature names that aren't on /pricing anymore. The catalog
# row carries ``alias=True`` so the UI can filter them out without
# hard-coding the four ids on the frontend (a duplicate that would drift the
# next time we shuffle the PRO_ONLY set).
_ALIAS_FEATURES = frozenset(
    {"custom_alerts", "alert_webhooks", "anomaly_detection", "cost_optimizer"}
)


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
        return self.entitled_runtime(runtime)

    def entitled_runtime(self, runtime: str) -> bool:
        """Grace-INDEPENDENT: does the plan itself grant ``runtime``? This
        drives the teaser UI (#1532): a paid runtime the plan does not
        include renders a locked upgrade affordance even in grace mode,
        because without the pro package its data cannot be observed anyway
        (the adapter only auto-provisions for entitled accounts) — "allowed
        by grace" was indistinguishable from "working" and the conversion
        surface never rendered (12 paywall views in 30 days fleet-wide)."""
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

    def allows_node_count(self, current: int) -> bool:
        """Whether ``current`` registered nodes still fit under this
        entitlement's node cap. Completes the gating triad alongside
        :meth:`allows_runtime` and :meth:`allows_feature` so fleet code can
        check node-limit overflow with the same never-crash contract.

        Semantics -- chosen to match the existing helpers:

        * Grace mode (default) -- always ``True``. Wiring this into a fleet
          path therefore changes no behaviour before the enforce phase.
        * ``current <= 0`` -- always ``True``. A node count that hasn't been
          measured yet (zero/negative) should never be the thing that blocks
          a request.
        * Expired entitlement -- collapses to a single node (the OSS-free
          default), mirroring how :meth:`allows_runtime` falls back to free
          runtimes on expiry.
        * ``node_limit <= 0`` -- treated as unlimited. The license payload
          uses ``0`` (or omits ``nodes``) for Enterprise/unlimited grants;
          honoring that keeps the wire format unchanged.
        * Otherwise -- ``current <= node_limit``.

        Non-int ``current`` (e.g. a stray ``None`` from a fleet table read)
        is swallowed and returns ``True`` so a flaky read never blocks a
        request -- same posture as :func:`_gate.gate` on a flaky entitlement
        resolution.
        """
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
        """Sorted tuple of PAID runtime ids the install currently can NOT
        observe — the inverse view of :meth:`allows_runtime` restricted to
        ``PAID_RUNTIMES``. Mirrors the ``locked`` flag in
        :func:`runtime_catalog` exactly: a runtime is "locked" iff
        ``allows_runtime`` returns ``False``.

        In grace mode the gate passes everything, so the result is ``()``;
        once enforcement is on (``CLAWMETRY_ENFORCE=1``) it returns the paid
        runtimes the current tier (and non-expired state) does not unlock,
        giving the UI a one-call source for a "N runtimes locked — upgrade"
        badge without iterating ``PAID_RUNTIMES`` or re-deriving the gate.
        Free runtimes are never reported (they can never be locked).
        Never raises.
        """
        try:
            return tuple(sorted(rt for rt in PAID_RUNTIMES if not self.allows_runtime(rt)))
        except Exception:  # belt-and-suspenders: a flaky gate read must never crash a render
            return ()

    def locked_features(self) -> tuple[str, ...]:
        """Sorted tuple of PAID feature keys the install does NOT unlock —
        the inverse view of :meth:`allows_feature` restricted to
        ``PAID_FEATURES ∪ ENTERPRISE_FEATURES``.

        In grace mode every gate passes, so the result is ``()``; once
        enforcement is on it returns the paid keys the current tier (and
        non-expired state) does not grant, giving the UI a single source
        for a paywall summary off ``/api/entitlement`` without re-deriving
        feature-set membership on the frontend. Free features are never
        reported (they can never be locked). Never raises.
        """
        try:
            paid_universe = PAID_FEATURES | ENTERPRISE_FEATURES
            return tuple(sorted(f for f in paid_universe if not self.allows_feature(f)))
        except Exception:
            return ()

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

    def to_dict(self) -> dict:
        # ``retention_days`` mirrors :meth:`event_retention_days` so the
        # dashboard can render a tier-aware "we are keeping N days of history"
        # banner (and an Enterprise "unlimited / custom" pill when ``None``)
        # without re-deriving the per-tier table client-side. The daemon's
        # prune loop in ``clawmetry/sync.py`` still reads the method directly;
        # this is just the read-only API surface.
        return {
            "tier": self.tier,
            "source": self.source,
            "node_limit": self.node_limit,
            "expiry": self.expiry,
            "expired": self.expired,
            "is_paid": self.is_paid,
            "grace": self.grace,
            "enforced": not self.grace,
            "retention_days": self.event_retention_days(),
            "runtimes": sorted(self.runtimes),
            "features": sorted(self.features),
            "free_runtimes": sorted(FREE_RUNTIMES),
            "paid_runtimes": sorted(PAID_RUNTIMES),
            "all_runtimes": sorted(ALL_RUNTIMES),
            "locked_runtimes": list(self.locked_runtimes()),
            "locked_features": list(self.locked_features()),
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

# Memo of the tier we last announced on the extension bus. Drives
# :func:`_maybe_emit_change` so ``entitlement.changed`` fires on a genuine
# transition (OSS -> cloud_pro after the daemon writes a plan cache, pro ->
# oss after ``clawmetry license deactivate``) and stays quiet on the every-
# minute cache refresh that resolves to the same tier. Lock-guarded so two
# concurrent fresh resolves never double-emit the initial tier.
_last_emitted_tier: str | None = None


def _maybe_emit_change(ent: Entitlement) -> None:
    """Emit ``entitlement.changed`` to the extension bus on a tier transition.

    The first successful resolution emits with ``previous_tier=None`` so a
    listener registered before startup hears the initial tier exactly once.
    Subsequent resolutions to the same tier are no-ops, so the every-minute
    cache refresh does not spam the bus. Best-effort end-to-end: a missing
    ``clawmetry.extensions`` import or a misbehaving listener is logged at
    debug and swallowed — the resolver must never crash a request path.

    Payload::

        {"previous_tier": "<old>"|None, "tier": "<new>",
         "source": "license"|"cloud"|"oss", "is_paid": bool, "grace": bool}
    """
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
    """Resolve (and cache) the current entitlement. Cheap by design — the
    FLYWHEEL performance budget forbids a per-request network call, so the
    result is cached for ``_CACHE_TTL_SECS``. The cache also busts when the
    enforce flag flips. Never raises: any failure returns OSS-free.

    On every fresh resolution (cache miss) the resolved entitlement is fed
    through :func:`_maybe_emit_change`, which fires ``entitlement.changed``
    on the extension bus iff the tier changed since the previous emit. Cache
    hits skip the emit so the bus stays quiet on steady-state reads.
    """
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
    """Drop the cached entitlement (call after activating/removing a license)."""
    with _lock:
        _cache.update(ent=None, ts=0.0, enforce=None)


def resolution_diagnostic() -> dict:
    """Snapshot of the *inputs* that determine entitlement resolution.

    Where :func:`get_entitlement` (and ``/api/entitlement``) report the
    resolved *outputs* (tier, runtimes, features, expiry), this helper
    reports the *inputs* the resolver consulted to produce them:

    * presence (not contents) of ``~/.clawmetry/license.key``
    * presence (not contents) of ``~/.clawmetry/cloud_plan.json``
    * the raw ``CLAWMETRY_ENFORCE`` env value + the boolean it resolves to
    * cache liveness (age vs TTL, hit/miss for the next call)

    Existing operator-triage flow for "why does this install think it's on
    tier X?" required reading dashboard logs, ``ls``-ing ``~/.clawmetry``,
    and ``echo``-ing the env var by hand. This rolls those checks into one
    blob the dashboard / CLI / a tail-only operator can read uniformly.

    Side-effect-free; never reads file contents; never raises (a failed
    ``os.stat`` becomes ``present=False`` with the error string). No secrets
    are surfaced — only paths, sizes, and the resolver's view of them.
    """
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
    }
    try:
        out["is_enforced"] = is_enforced()
    except Exception as exc:  # pragma: no cover - is_enforced is a string check
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
    """Runtimes the UI should expose. In grace mode that's every known
    runtime (so nothing disappears before enforcement); once enforced it's the
    entitled set. Locked-but-visible rendering is the UI's job (Phase 5)."""
    ent = get_entitlement()
    if ent.grace:
        return sorted(ALL_RUNTIMES)
    return sorted(ent.runtimes)


def canonical_runtime(runtime: str) -> str:
    """Normalize a runtime identifier to its canonical snake_case key.

    Accepts the common alternative spellings (hyphenated, no-separator, mixed
    case) callers sometimes pass — OTLP ``service.name``, custom ingest, CLI
    flags — and resolves them to the id used in :data:`ALL_RUNTIMES`. Unknown
    identifiers are returned lower-cased unchanged so plugin runtimes still
    pass through. Empty / non-string inputs return an empty string.

    Never raises.
    """
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
    """Human-readable label for ``runtime``. Aliases (``claude-code``,
    ``qwencode``, …) resolve to the canonical id first so they render with the
    same label as the snake_case form. Falls back to the (canonicalised) id
    when unknown so unknown plugin runtimes still render with *something*."""
    rt = canonical_runtime(runtime)
    return RUNTIME_LABELS.get(rt, rt)


def feature_label(feature: str) -> str:
    """Human-readable label for ``feature``. Falls back to the id when unknown
    so plugin/extension features still render with *something*."""
    fid = (feature or "").strip().lower()
    return FEATURE_LABELS.get(fid, fid)


# Ordered tier ladder used to resolve "minimum tier that unlocks X" — the lower
# the index the cheaper the tier. Free first, then Starter, Pro, Enterprise.
_FEATURE_TIER_ORDER = (
    (TIER_OSS, FREE_FEATURES),
    (TIER_CLOUD_STARTER, STARTER_FEATURES),
    (TIER_CLOUD_PRO, PRO_ONLY_FEATURES),
    (TIER_ENTERPRISE, ENTERPRISE_FEATURES),
)


def feature_tier(feature: str) -> str:
    """The lowest tier code that unlocks ``feature``. Returns ``TIER_OSS`` for
    free features (and unknown ids — same fallback as the runtime helper, so an
    extension feature never appears mysteriously locked). Used by the UI to
    label the upgrade CTA ("Requires Starter", "Requires Pro", "Requires
    Enterprise") without hard-coding the bucket on the frontend."""
    fid = (feature or "").strip().lower()
    for tier, bucket in _FEATURE_TIER_ORDER:
        if fid in bucket:
            return tier
    return TIER_OSS


# Stable ordering rank used to sort the catalogue: free first, then by tier.
_FEATURE_TIER_RANK = {
    TIER_OSS: 0,
    TIER_CLOUD_STARTER: 1,
    TIER_CLOUD_PRO: 2,
    TIER_ENTERPRISE: 3,
}


def feature_catalog() -> list[dict]:
    """The full feature catalog with the entitlement-derived availability for
    each entry. Single source of truth the UI uses to render *every* known
    feature — including paid ones the local install does not have — so the
    locked-but-visible upgrade affordance has data to render against and the
    upgrade CTA knows which tier to advertise.

    Each entry::

        {
          "id":       "<feature>",         # canonical key
          "label":    "<Display Name>",    # falls back to id
          "tier":     "oss" | "cloud_starter" | "cloud_pro" | "enterprise",
          "free":     True | False,        # FREE_FEATURES membership
          "allowed":  True | False,        # entitlement allows using it
          "locked":   True | False,        # paid + not allowed (UI shows the lock)
          "entitled": True | False,        # grace-INDEPENDENT plan fact
        }

    Ordering: free first, then by tier rank (Starter -> Pro -> Enterprise), then
    alphabetical inside each bucket — stable so the UI list is deterministic.

    Never raises; on any resolution error every paid feature is reported as
    ``locked=False`` (grace) to match the OSS-free fallback in
    :func:`get_entitlement`.
    """
    try:
        ent = get_entitlement()
    except Exception as exc:  # never crash a catalog read
        logger.warning("entitlements: feature_catalog falling back to grace: %s", exc)
        ent = _oss_free()
    out: list[dict] = []
    for fid in sorted(ALL_FEATURES, key=lambda f: (_FEATURE_TIER_RANK.get(feature_tier(f), 9), f)):
        tier = feature_tier(fid)
        is_free = fid in FREE_FEATURES
        allowed = ent.allows_feature(fid)
        # Grace-independent plan fact — does the resolved tier itself grant
        # this feature, ignoring grace bypass? Free features are always
        # entitled; expired plans don't entitle paid features.
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
                "allowed": allowed,
                "locked": not allowed,
                # Grace-independent plan fact (#1532): lets the UI render the
                # teaser/upgrade affordance in grace mode without changing
                # what `allowed`/`locked` mean for enforcement.
                "entitled": ent.entitled_runtime(rt),
            }
        )
    return out
