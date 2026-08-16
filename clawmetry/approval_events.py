"""The public seam between approvals and whoever delivers them.

Everything that pauses an agent is open source: the policy engine
(``clawmetry/approvals.py``), the Claude Code pre-tool gate
(``clawmetry/claude_code_gate.py``), the hook receivers (``routes/hooks.py``)
and the queue (``routes/policy.py``). Everything that *pages a human about
it* — per-runtime routing, the channel senders, the inbound decision poller,
the signed decision links — is a paid feature and ships in ``clawmetry-pro``.

This module is the boundary. The OSS side imports only from here, so it
never names a module that may not be installed, and the paid side attaches
by registering handlers through ``clawmetry.extensions``.

Two shapes, matching the two things OSS needs:

``notify_*``  ANNOUNCE (fire-and-forget, via ``extensions.emit``)
    "an approval parked" / "an approval resolved". OSS does not care
    whether anyone was listening — the row is already in DuckDB and the
    Approvals tab already renders it. Delivery is strictly additive.

``mirror_*``  ASK (via ``extensions.call``, which returns a value)
    "should I arm the permission-prompt mirror for this runtime, and how
    long does the human get?" OSS cannot proceed without the answer, so
    these carry a SAFE default for the unlicensed case: mirroring off.

    That default is what makes losing a license safe. With no paid package
    the mirror hook is never installed, so the node sits in its pre-mirror
    state — the runtime's own terminal prompt — rather than keeping a hook
    pointed at a feature that stopped answering. And if a stale hook does
    survive a downgrade, the receiver's existing contract already covers
    it: no answer means ``ask``, which IS the terminal prompt.

Handler convention (same as the runtime gate handlers in approvals.py):
``None`` means "no opinion, try the next handler" and is indistinguishable
from not being registered. A handler that means "no" returns ``False``.
"""
from __future__ import annotations

import logging

from clawmetry import extensions

logger = logging.getLogger("clawmetry.approval_events")

#: An approval just parked and is waiting on a human.
#: Payload: ``{id, runtime, kind, tool_name, command, cwd, policy,
#: requestor_session_id}``.
APPROVAL_PENDING = "approval.pending"

#: A pending approval was decided. Payload: ``{id, decision, resolver}``.
#: Lets a destination that can edit its own message (chat) swap live
#: Approve/Deny controls for the verdict, so two people cannot race the
#: same call from two surfaces.
APPROVAL_RESOLVED = "approval.resolved"

#: "Should the permission-prompt mirror be armed for this runtime?"
#: Payload: ``{runtime}``. Answer: bool. Default when unanswered: False.
MIRROR_WANTED = "approval.mirror.wanted"

#: "How long does the human get before the runtime's own prompt takes
#: over?" Payload: ``{runtime}``. Answer: int seconds. Default: 180.
MIRROR_WINDOW = "approval.mirror.window"

#: Fallback mirror window when nothing answers. Only reachable when a
#: handler answers MIRROR_WANTED true but not this — a mis-registered
#: plugin — so it is deliberately short rather than generous.
DEFAULT_MIRROR_WINDOW_S = 180

#: The sync daemon finished starting its own workers. Payload:
#: ``{node_id}``. A delivery layer that needs a long-lived thread — an
#: inbound chat poller, say — starts it here rather than having the daemon
#: import it by name, so an install without the paid package simply has
#: nothing listening.
DAEMON_READY = "daemon.workers.ready"


def daemon_ready(node_id: str | None = None) -> None:
    """Called once by the sync daemon when its workers are up."""
    try:
        _ensure_local_handlers()
        extensions.emit(DAEMON_READY, {"node_id": node_id})
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("daemon.workers.ready emit failed: %s", exc)


# ── announce ───────────────────────────────────────────────────────────────

def notify_pending(approval: dict) -> None:
    """Announce a parked approval. Never raises, never blocks materially.

    The delivering handler is expected to hand its own fan-out to a thread;
    this call sits in the pre-tool gate's request path, where a slow vendor
    must never become an agent stall.
    """
    try:
        _ensure_local_handlers()
        extensions.emit(APPROVAL_PENDING, dict(approval or {}))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("approval.pending emit failed: %s", exc)


def notify_resolved(approval_id: str, decision: str, resolver: str = "") -> None:
    """Announce that a pending approval was decided."""
    try:
        _ensure_local_handlers()
        extensions.emit(APPROVAL_RESOLVED, {
            "id": str(approval_id or ""),
            "decision": str(decision or ""),
            "resolver": str(resolver or ""),
        })
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("approval.resolved emit failed: %s", exc)


# ── ask ────────────────────────────────────────────────────────────────────

def mirror_wanted(runtime: str = "claude_code") -> bool:
    """Should the runtime's OWN permission prompts be mirrored?

    False whenever nothing answers — an OSS install with no paid package
    behaves exactly as it did before the mirror existed.
    """
    try:
        _ensure_local_handlers()
        return bool(extensions.call(MIRROR_WANTED, {"runtime": runtime},
                                    default=False))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("approval.mirror.wanted call failed: %s", exc)
        return False


def mirror_window_s(runtime: str = "claude_code") -> int:
    """Seconds the human gets before the runtime's own prompt takes over.

    Clamped here rather than at the handler so a plugin cannot hand back a
    window shorter than a human can answer, or one that outlives the
    session it is blocking.
    """
    try:
        _ensure_local_handlers()
        raw = extensions.call(MIRROR_WINDOW, {"runtime": runtime},
                              default=DEFAULT_MIRROR_WINDOW_S)
        return max(30, min(int(raw), 3600))
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("approval.mirror.window call failed: %s", exc)
        return DEFAULT_MIRROR_WINDOW_S


# ── no local implementation ────────────────────────────────────────────────
# The delivery impl lives in clawmetry-pro and attaches by registering
# handlers at plugin-load time. Nothing to do here: with no handler
# registered every function above returns its safe default, which is the
# correct behaviour for an install without the paid package.
#
# Kept as a no-op (rather than deleting the call sites) so this module is
# the ONLY place that would ever need to know about a local implementation
# again — e.g. if a future OSS-side default delivery is added.

def _ensure_local_handlers() -> None:
    return None
