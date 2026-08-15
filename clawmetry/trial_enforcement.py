"""
Trial-end hard-block layer.

Companion to :mod:`clawmetry.entitlements`. Where the entitlements resolver
answers "which tier resolved for this install", this module answers "must the
daemon refuse to serve anything except the payment / license-activation
surface right now?".

The block is off by default so a release that ships this module does NOT brick
any existing install. Operators (or a future release) flip it on with the
``CLAWMETRY_HARD_BLOCK`` environment variable — ``1`` / ``true`` / ``yes`` /
``on`` all count. When on, an install whose resolved :class:`Entitlement` is
either unpaid (OSS / cloud_free) or expired (trial past its deadline, or a
paid tier whose subscription lapsed) gets locked to the small allowlist below
until a valid signed license file lands at ``~/.clawmetry/license.key``.

The allowlist is deliberately tiny — it must cover exactly the surface the
frontend overlay needs to keep working during a block:

- ``/api/trial/*`` — status, refresh, mark-warned (this module's blueprint)
- ``/api/entitlement`` and ``/api/entitlement/refresh`` — the overlay reads
  the resolver directly so it can auto-clear the moment a license lands
- ``/api/license/*`` — CLI + UI license activation & inspection surface
- ``/api/paywall/event`` — telemetry for "user saw / clicked the block"
- ``/api/version``, ``/api/heartbeat``, ``/api/extensions`` — diagnostics an
  operator running ``clawmetry status`` needs while locked out
- ``/static/*``, ``/favicon.ico`` — the overlay script + CSS must load
- ``/`` — the dashboard shell itself, which will render the overlay on top

Everything else 402s with a JSON body carrying ``hard_blocked=True`` and the
upgrade / checkout URL, so ANY API surface (including custom third-party
consumers of ``/api/sessions`` and friends) fails closed with a machine-
readable payload the UI can react to.

Failure posture matches the rest of the entitlements engine: every helper is
defensive, never raises, and falls through to "not blocked" on internal error
so a bug in this module can never accidentally lock out a legitimate paying
customer. The block is a *positive assertion* — we only lock when we're
confident the resolver says unpaid-or-expired AND the operator has flipped
the switch.
"""

from __future__ import annotations

import logging
import os
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import for type hints only
    from clawmetry.entitlements import Entitlement

logger = logging.getLogger("clawmetry.trial_enforcement")

# Env switches. All are read at call-time (never cached) so an operator can
# toggle the block by exporting the var and hitting ``/api/entitlement/refresh``
# — no daemon restart needed. Matches ``entitlements.is_enforced``'s posture.
_HARD_BLOCK_ENV = "CLAWMETRY_HARD_BLOCK"
_HARD_BLOCK_UPGRADE_URL_ENV = "CLAWMETRY_UPGRADE_URL"
_HARD_BLOCK_CHECKOUT_URL_ENV = "CLAWMETRY_CHECKOUT_URL"
_HARD_BLOCK_ESCAPE_ENV = "CLAWMETRY_HARD_BLOCK_ESCAPE"
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})

# Free-only mode marker. Written by ``POST /api/trial/continue-free`` when an
# expired-trial user chooses to keep only the FREE_RUNTIMES (openclaw +
# nemoclaw) working rather than upgrade. Presence of this file flips the gate
# from "block everything" to "block only paid-runtime scoped requests" so
# ``openclaw`` observability keeps working; ``claude_code`` etc. still 402.
# Documented in the TrialHardBlockPaywall component of the Local Agent
# Observability blueprint (v4+ describes this fallback).
_FREE_ONLY_MARKER = os.path.expanduser("~/.clawmetry/free_only.marker")

# Paid-runtime URL prefixes the request-time gate can use to classify a
# request as paid-runtime scope even when the caller did NOT pass ``runtime=``.
# Defense-in-depth for any /api/<runtime>/ shard, present or future. Additive
# per runtime.
_PAID_URL_PREFIXES_BY_RUNTIME = {
    "claude_code": ("/api/claude_code/", "/api/claudecode/"),
    "codex": ("/api/codex/",),
    "cursor": ("/api/cursor/",),
    "aider": ("/api/aider/",),
    "goose": ("/api/goose/",),
    "opencode": ("/api/opencode/",),
    "qwen_code": ("/api/qwen_code/", "/api/qwen/"),
    "hermes": ("/api/hermes/",),
    "picoclaw": ("/api/picoclaw/",),
    "nanoclaw": ("/api/nanoclaw/",),
    "pi": ("/api/pi/",),
    "deepagents": ("/api/deepagents/",),
    "antigravity": ("/api/antigravity/",),
}

# The allowlist. Prefixes are matched with ``str.startswith``; exact paths are
# matched with ``==``. Kept intentionally small — every entry added here is a
# potential bypass, so new entries need a comment saying WHY the overlay
# needs that route reachable while locked.
_ALLOWED_PATH_PREFIXES = (
    "/api/trial/",              # this module's own status/refresh endpoints
    "/api/license/",            # activation + inspection surface
    "/api/entitlement",         # resolver read + refresh (overlay auto-clear)
    "/api/paywall/",            # "user saw the block" telemetry
    "/api/version",             # diagnostics
    "/api/heartbeat",           # cloud liveness probe
    "/api/extensions",          # "is clawmetry-pro loaded?" probe
    "/api/auth/",               # OSS auth-check + zero-click bootstrap
    "/auth",                    # legacy auth endpoint sibling of /api/auth
    "/static/",                 # overlay JS/CSS must load
    "/favicon",                 # tab icon
)
_ALLOWED_PATH_EXACT = frozenset({
    "/",                        # dashboard shell renders overlay on top
    "/robots.txt",
    "/api/entitlement",         # exact, also matched by prefix — belt & braces
    "/api/health",              # k8s / docker / cURL liveness probe
})

# Default upgrade destination when the cloud hasn't handed us a signed
# per-account checkout URL yet. The daemon overrides this from the heartbeat
# response's ``upgrade_url`` field once the cloud is reachable.
_DEFAULT_UPGRADE_URL = "https://app.clawmetry.com/upgrade"


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUE_VALUES


_HARD_BLOCK_DISABLE_VALUES = frozenset({"0", "false", "no", "off"})


def hard_block_enabled() -> bool:
    """True when the trial-end paywall is live on this install.

    **Default ON.** Founder policy (2026-08-06): trial ends → non-dismissable
    modal → payment → auto-unlock is a strict requirement, not an opt-in.
    The only escape is an explicit ``CLAWMETRY_HARD_BLOCK=0`` / ``false`` /
    ``no`` / ``off`` — kept as a support lever for the rare case of a
    legitimate paying customer whose license file corrupts mid-renewal.

    Never raises. On any parse trouble, defaults to enabled — we would
    rather leak into the payment prompt than silently keep serving an
    expired trial."""
    try:
        raw = os.environ.get(_HARD_BLOCK_ENV, "").strip().lower()
        if raw in _HARD_BLOCK_DISABLE_VALUES:
            return False
        return True
    except Exception:
        return True


def free_only_mode_enabled() -> bool:
    """True when the operator has chosen the "keep free runtimes only"
    fallback instead of upgrading. Written by ``POST /api/trial/continue-free``
    and cleared by ``POST /api/trial/exit-free``. Presence-based marker file
    at ``~/.clawmetry/free_only.marker`` so it survives daemon restarts and
    is easy to wipe by hand. Never raises."""
    try:
        return os.path.isfile(_FREE_ONLY_MARKER)
    except Exception:
        return False


def set_free_only_mode(enabled: bool) -> bool:
    """Toggle the free-only marker. Returns the resulting state. Never raises
    — a filesystem error just returns the pre-call state so the caller can
    render a "try again" message without swallowing the error silently."""
    try:
        d = os.path.dirname(_FREE_ONLY_MARKER)
        if enabled:
            try:
                os.makedirs(d, exist_ok=True)
            except Exception:
                pass
            try:
                with open(_FREE_ONLY_MARKER, "w", encoding="utf-8") as fh:
                    fh.write(str(int(time.time())))
            except Exception as exc:
                logger.warning("trial_enforcement: set_free_only_mode write "
                               "failed: %s", exc)
                return free_only_mode_enabled()
            return True
        try:
            if os.path.isfile(_FREE_ONLY_MARKER):
                os.remove(_FREE_ONLY_MARKER)
        except Exception as exc:
            logger.warning("trial_enforcement: set_free_only_mode remove "
                           "failed: %s", exc)
            return free_only_mode_enabled()
        return False
    except Exception as exc:
        logger.warning("trial_enforcement: set_free_only_mode: %s", exc)
        return free_only_mode_enabled()


def _classify_scope(path: str | None, runtime: str | None) -> str | None:
    """Return "free", "paid", or None (unknown) for the given request scope.

    The gate uses this in free-only mode to let ``openclaw`` / ``nemoclaw``
    requests through while still 402-ing every paid-runtime surface. Never
    raises — an unclassifiable request returns None and the caller falls back
    to the safe "treat as paid" branch."""
    try:
        try:
            from clawmetry.entitlements import FREE_RUNTIMES, PAID_RUNTIMES
        except Exception:
            FREE_RUNTIMES = frozenset({"openclaw", "nemoclaw"})
            PAID_RUNTIMES = frozenset()
        rt = (runtime or "").strip().lower()
        if rt:
            if rt in FREE_RUNTIMES:
                return "free"
            if rt in PAID_RUNTIMES:
                return "paid"
        if path:
            p = str(path)
            for rt_name, prefixes in _PAID_URL_PREFIXES_BY_RUNTIME.items():
                for pref in prefixes:
                    if p.startswith(pref):
                        return "paid"
        return None
    except Exception:
        return None


def _escape_hatch_active() -> bool:
    """Founder-only escape hatch. When ``CLAWMETRY_HARD_BLOCK_ESCAPE=1`` is
    set, the block is bypassed even while enabled — a documented last-resort
    for support to unbrick a legitimate paying customer whose license file
    got corrupted mid-renewal. Never raises."""
    try:
        return _env_flag(_HARD_BLOCK_ESCAPE_ENV)
    except Exception:
        return False


def _resolver_says_unpaid_or_expired(ent: "Entitlement | None") -> bool:
    """True only when this install WAS entitled (paid tier, or a trial it has
    since consumed) and has now passed its ``expiry`` timestamp -- never for
    an install that was simply never entitled in the first place (plain OSS /
    cloud_free is the permanent free tier documented in docs/ENTITLEMENTS.md,
    not a lapsed trial).

    Fail-closed only on a genuinely unreadable entitlement (``ent is None`` or
    an exception): we would rather leak into the paywall on an internal error
    than silently keep serving an install we can't positively classify. Note
    the asymmetry inside the ``trial_used`` branch -- an unparseable expiry
    there returns False, because a burnt trial with a corrupt date is far more
    likely to be our bug than a freeloader, and blocking a paying-adjacent
    user is the costlier mistake."""
    if ent is None:
        return True
    try:
        # Local Ed25519-signed license on a paid tier with no expiry, or an
        # expiry that hasn't passed → NOT blocked, we have a valid subscription.
        if getattr(ent, "source", "") == "license":
            expiry = getattr(ent, "expiry", None)
            if expiry is None:
                return False
            try:
                return time.time() > float(expiry)
            except (TypeError, ValueError):
                return True
        # Cloud plan cache: paid tier (incl. trial) + unexpired → NOT blocked.
        if getattr(ent, "is_paid", False):
            expiry = getattr(ent, "expiry", None)
            if expiry is None:
                return False  # paid + no expiry = perpetual → allow
            try:
                return time.time() > float(expiry)
            except (TypeError, ValueError):
                return True
        # Unpaid tier. Two very different populations land here and only one
        # of them may be paywalled:
        #
        #   (a) never trialed -- a fresh `pip install clawmetry` on the
        #       permanent free tier (docs/ENTITLEMENTS.md). NEVER block.
        #       (Regression fixed 2026-08-06: this used to fall through to
        #       `return True`, hard-blocking every fresh install.)
        #   (b) trial consumed and its end date passed -- the account saw the
        #       paid runtimes for 7 days and the window closed. Block, so the
        #       only ways forward are "upgrade" or "continue on free runtimes".
        #
        # ``trial_used`` is what tells them apart; it reaches us from the
        # cloud heartbeat via ``cloud_plan.json`` (see
        # ``sync._persist_cloud_plan_to_disk``). Absent that signal the value
        # is False and we fall through to (a) -- an older daemon, an offline
        # install, or a cloud that hasn't shipped the field yet all keep
        # working exactly as before rather than getting a surprise paywall.
        if getattr(ent, "trial_used", False):
            expiry = getattr(ent, "expiry", None)
            if expiry is None:
                # Trial consumed but no end date known: cannot prove it lapsed,
                # so do not block on a guess.
                return False
            try:
                return time.time() > float(expiry)
            except (TypeError, ValueError):
                return False
        return False
    except Exception as exc:
        logger.warning("trial_enforcement: resolver check failed, defaulting "
                       "to blocked: %s", exc)
        return True


def is_hard_blocked(
    ent: "Entitlement | None" = None,
    *,
    path: str | None = None,
    runtime: str | None = None,
) -> bool:
    """The core predicate. True when the daemon must refuse to serve this
    request (except the payment surface).

    Reads :func:`hard_block_enabled` and :func:`_resolver_says_unpaid_or_expired`
    together so a call site never has to compose them by hand.

    Two additional scope hints let the request-time gate honour the
    "continue with free runtimes only" fallback:

    * ``path`` — the request path (e.g. ``request.path``)
    * ``runtime`` — an explicit runtime string (e.g. ``?runtime=openclaw`` on
      the query string)

    When :func:`free_only_mode_enabled` is on AND the scope classifies as
    ``free``, the request is allowed through even if the entitlement is
    expired. Paid-runtime scoped requests still 402. Requests with no
    identifiable runtime scope fall back to the whole-app block, so the free
    fallback never accidentally unlocks a paid data surface.

    Falls through to ``False`` on internal error — we would rather leak a
    request than accidentally brick a paying customer."""
    try:
        if _escape_hatch_active():
            return False
        if not hard_block_enabled():
            return False
        if ent is None:
            try:
                from clawmetry import entitlements as _ent
                ent = _ent.get_entitlement()
            except Exception as exc:
                logger.warning("trial_enforcement: entitlement lookup failed: "
                               "%s", exc)
                return False  # fail-open: no lockout without a positive signal
        if not _resolver_says_unpaid_or_expired(ent):
            return False
        # Trial is expired / unpaid. If the operator has opted into free-only
        # mode and this specific request is scoped to a FREE_RUNTIMES surface,
        # let it through. Paid-runtime scoped requests and unknown scopes
        # remain blocked.
        if free_only_mode_enabled():
            scope = _classify_scope(path, runtime)
            if scope == "free":
                return False
        return True
    except Exception as exc:
        logger.warning("trial_enforcement: is_hard_blocked failed: %s", exc)
        return False


def allowlisted_path(path: str) -> bool:
    """True when ``path`` is one of the few routes that must keep serving
    during a block (payment + activation + diagnostics + static assets).
    See the module docstring for the full list. Never raises."""
    try:
        if not path:
            return False
        p = str(path)
        if p in _ALLOWED_PATH_EXACT:
            return True
        for prefix in _ALLOWED_PATH_PREFIXES:
            if p.startswith(prefix):
                return True
        return False
    except Exception:
        return False


# The sync daemon persists {upgrade_url, checkout_url} from each heartbeat
# here so the dashboard — a SEPARATE process whose in-memory copy of
# ``sync._TRIAL_STATE`` only ever holds the module defaults — can read the
# per-account URLs the cloud actually handed us.
_TRIAL_STATE_PATH = "~/.clawmetry/trial_state.json"


def persisted_trial_state() -> dict:
    """The daemon-persisted trial-state file (``~/.clawmetry/trial_state.json``)
    as a dict, or ``{}`` when absent/unreadable. Never raises."""
    try:
        import json
        path = os.path.expanduser(_TRIAL_STATE_PATH)
        if not os.path.isfile(path):
            return {}
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def resolved_checkout_url() -> str:
    """The signed per-account Stripe checkout URL, or ``""`` when the cloud
    hasn't handed us one yet. Env override wins (support lever), then the
    daemon-persisted heartbeat cache. Never raises."""
    try:
        checkout = os.environ.get(_HARD_BLOCK_CHECKOUT_URL_ENV, "").strip()
        if checkout:
            return checkout
        cached = persisted_trial_state().get("checkout_url")
        if isinstance(cached, str) and cached.strip():
            return cached.strip()
        return ""
    except Exception:
        return ""


def resolved_upgrade_url() -> str:
    """The URL the "Continue to payment" button points at. Prefers a signed
    per-account checkout URL the cloud handed us via heartbeat (persisted to
    ``~/.clawmetry/trial_state.json`` by the sync daemon, or mirrored into
    ``CLAWMETRY_CHECKOUT_URL``), falls back to the generic upgrade page, and
    finally to the hard-coded default. Never raises."""
    try:
        checkout = resolved_checkout_url()
        if checkout:
            return checkout
        upgrade = os.environ.get(_HARD_BLOCK_UPGRADE_URL_ENV, "").strip()
        if upgrade:
            return upgrade
        cached = persisted_trial_state().get("upgrade_url")
        if isinstance(cached, str) and cached.strip():
            return cached.strip()
        # Best-effort: also read the daemon's live cache if we happen to run
        # in the daemon process itself (fresher than the persisted file).
        try:
            from clawmetry import sync as _sync
            in_proc = getattr(_sync, "_TRIAL_STATE", {}).get("upgrade_url")
            if isinstance(in_proc, str) and in_proc.strip():
                return in_proc.strip()
        except Exception:
            pass
        return _DEFAULT_UPGRADE_URL
    except Exception:
        return _DEFAULT_UPGRADE_URL


def block_payload(ent: "Entitlement | None" = None) -> dict:
    """Machine-readable body returned with every 402 while blocked.

    Shape is stable across releases — the overlay in ``static/js/app.js``
    keys off ``hard_blocked``, ``upgrade_url``, ``tier``, ``expired``, and
    ``reason``, so adding new fields is safe but renaming existing ones
    isn't. Never raises."""
    try:
        if ent is None:
            try:
                from clawmetry import entitlements as _ent
                ent = _ent.get_entitlement()
            except Exception:
                ent = None
        tier = getattr(ent, "tier", "oss") if ent is not None else "oss"
        expired = bool(getattr(ent, "expired", False)) if ent is not None else False
        source = getattr(ent, "source", "oss") if ent is not None else "oss"
        expiry = getattr(ent, "expiry", None) if ent is not None else None
        days_left = None
        try:
            if ent is not None and hasattr(ent, "days_until_expiry"):
                days_left = ent.days_until_expiry()
        except Exception:
            days_left = None
        # A human-facing reason string the modal renders under the headline.
        if expired:
            if tier == "trial":
                reason = "Your ClawMetry trial has ended."
            else:
                reason = "Your ClawMetry subscription has expired."
        elif tier in ("oss", "cloud_free"):
            reason = "ClawMetry Pro is required to continue using this install."
        else:
            reason = "A valid ClawMetry subscription is required to continue."
        return {
            "hard_blocked": True,
            "tier": tier,
            "source": source,
            "expired": expired,
            "expiry": expiry,
            "days_until_expiry": days_left,
            "reason": reason,
            "upgrade_url": resolved_upgrade_url(),
            "checkout_url": resolved_checkout_url() or None,
            "activation_endpoint": "/api/license/activate",
            "checkout_endpoint": "/api/trial/checkout",
            "refresh_endpoint": "/api/trial/refresh-license",
            "status_endpoint": "/api/trial/status",
            "free_only_endpoint": "/api/trial/continue-free",
            "exit_free_endpoint": "/api/trial/exit-free",
            "free_only_mode": free_only_mode_enabled(),
            "free_runtimes": ["openclaw", "nemoclaw"],
        }
    except Exception as exc:
        logger.warning("trial_enforcement: block_payload failed: %s", exc)
        return {
            "hard_blocked": True,
            "reason": "A valid ClawMetry subscription is required to continue.",
            "upgrade_url": _DEFAULT_UPGRADE_URL,
            "activation_endpoint": "/api/license/activate",
            "checkout_endpoint": "/api/trial/checkout",
            "refresh_endpoint": "/api/trial/refresh-license",
            "status_endpoint": "/api/trial/status",
            "free_only_endpoint": "/api/trial/continue-free",
            "exit_free_endpoint": "/api/trial/exit-free",
            "free_only_mode": free_only_mode_enabled(),
            "free_runtimes": ["openclaw", "nemoclaw"],
        }


def warning_window_days() -> int:
    """How many days ahead of expiry the daemon sends the "trial ending" email.
    Configurable via ``CLAWMETRY_TRIAL_WARN_DAYS`` (default 2) so a founder
    who wants a longer runway can widen it without a code change."""
    try:
        raw = os.environ.get("CLAWMETRY_TRIAL_WARN_DAYS", "").strip()
        if not raw:
            return 2
        n = int(raw)
        return max(0, n)
    except Exception:
        return 2


__all__ = [
    "hard_block_enabled",
    "is_hard_blocked",
    "allowlisted_path",
    "persisted_trial_state",
    "resolved_checkout_url",
    "resolved_upgrade_url",
    "block_payload",
    "warning_window_days",
    "free_only_mode_enabled",
    "set_free_only_mode",
]
