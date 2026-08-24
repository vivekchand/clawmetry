"""How long this node keeps event data — one answer, with its reason.

"How long do you keep my data, and can I change it?" is the first question a
security reviewer asks, and until now the honest answer was awkward: it comes
from your billing tier, and the only way to shorten it is an environment
variable you set before starting the daemon. Nothing in the product said what
the number was, nothing let an operator change it, and a value chosen that way
does not survive a reinstall.

This module makes the answer explicit and settable:

  cap        the tier's maximum (None = unlimited). A hard ceiling.
  configured what the operator chose, stored on the node (node_settings).
  env        CLAWMETRY_RETENTION_DAYS, kept for scripted/fleet installs.

The effective window is the SMALLEST of whichever are set, and never more than
the cap. Shrink-only is the whole point: an operator can always ask for less
data to be kept, and can never grant themselves more by editing a setting. So
this is safe to expose in the UI — the worst a mistake can do is delete the
user's own data sooner, which is the direction a security reviewer wants the
control to fail in.

``resolve()`` returns the number AND why, because a retention control that
shows "7 days" without saying whether that is your choice or your plan's limit
just moves the question rather than answering it.
"""
from __future__ import annotations

import logging
import os

log = logging.getLogger(__name__)

#: node_settings key holding the operator's chosen window, in days.
SETTING_KEY = "retention_days"

#: Kept for scripted installs that set it before the daemon starts.
ENV_KEY = "CLAWMETRY_RETENTION_DAYS"


def _coerce_days(raw) -> int | None:
    """A positive whole number of days, or None for anything else.

    Rejects rather than clamps: a retention control that silently reads 0 or
    -5 as "some default" is how you end up keeping more than the operator
    asked for, which is the failure direction that matters here.
    """
    if raw is None:
        return None
    try:
        text = str(raw).strip()
    except Exception:
        return None
    if not text:
        return None
    try:
        n = int(text)
    except (TypeError, ValueError):
        return None
    return n if n >= 1 else None


def _env_days() -> int | None:
    return _coerce_days(os.environ.get(ENV_KEY, ""))


def _configured_days(store) -> int | None:
    if store is None:
        return None
    try:
        return _coerce_days(store.get_node_setting(SETTING_KEY))
    except Exception:
        return None


def resolve(*, store=None, entitlement=None) -> dict:
    """The effective retention window and the reason for it.

    Returns::

        {
          "effective_days": int | None,   # None = keep everything
          "cap_days":       int | None,   # the tier ceiling
          "configured_days": int | None,  # what the operator chose
          "env_days":       int | None,   # CLAWMETRY_RETENTION_DAYS
          "source":         "configured" | "env" | "plan" | "unlimited",
          "tier":           str,
          "can_configure":  bool,         # False only when already at 1 day
          "explanation":    str,          # one sentence for the UI
        }

    Never raises: retention is a background prune and a settings panel, and
    neither is worth crashing over. On any failure it falls back to the tier
    cap, which is the conservative answer (it deletes no less than the plan
    already allowed).
    """
    tier = "unknown"
    cap = None
    try:
        if entitlement is None:
            from clawmetry.entitlements import get_entitlement
            entitlement = get_entitlement()
        tier = str(getattr(entitlement, "tier", "unknown"))
        cap = entitlement.event_retention_days()
    except Exception as exc:  # pragma: no cover - defensive
        log.debug("retention: entitlement read failed (%s)", exc)

    configured = _configured_days(store)
    env = _env_days()

    candidates = [d for d in (cap, configured, env) if d is not None]
    effective = min(candidates) if candidates else None

    if effective is None:
        source = "unlimited"
    elif configured is not None and effective == configured:
        # The operator's own choice wins the label when it is the binding
        # constraint, even if the env var happens to match — they should see
        # the setting they can actually change.
        source = "configured"
    elif env is not None and effective == env:
        source = "env"
    else:
        source = "plan"

    return {
        "effective_days": effective,
        "cap_days": cap,
        "configured_days": configured,
        "env_days": env,
        "source": source,
        "tier": tier,
        "can_configure": effective is None or effective > 1,
        "explanation": explain(effective, cap, source),
    }


def explain(effective, cap, source) -> str:
    """One sentence naming the number and what is setting it."""
    if effective is None:
        return "Event history is kept indefinitely on this node."
    days = f"{effective} day" + ("" if effective == 1 else "s")
    if source == "configured":
        extra = ""
        if cap is not None and cap > effective:
            extra = f" You chose this; your plan would allow up to {cap}."
        else:
            extra = " You chose this."
        return f"Event history older than {days} is deleted on this node.{extra}"
    if source == "env":
        return (
            f"Event history older than {days} is deleted on this node, set by "
            f"the {ENV_KEY} environment variable."
        )
    return f"Event history older than {days} is deleted on this node, set by your plan."


def set_configured_days(store, days, *, entitlement=None) -> dict:
    """Persist the operator's choice and return the new resolved state.

    ``days=None`` clears the choice and falls back to the plan. A value above
    the tier cap is accepted and stored, but resolves DOWN to the cap — the
    stored number is what the operator asked for, the resolved number is what
    actually happens, and the payload shows both so nobody is misled about
    having bought more retention by typing a bigger number.

    Raises ``ValueError`` on a value that is not a positive whole number, so a
    typo becomes an error rather than a silent reset to the default.
    """
    if days is None:
        store.set_node_setting(SETTING_KEY, None)
        return resolve(store=store, entitlement=entitlement)
    n = _coerce_days(days)
    if n is None:
        raise ValueError("retention days must be a whole number of days, 1 or more")
    store.set_node_setting(SETTING_KEY, n)
    return resolve(store=store, entitlement=entitlement)
