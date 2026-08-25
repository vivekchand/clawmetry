"""The session phase model: one state machine, every runtime.

Every surface that answers *what needs me right now* used to derive liveness
its own way. The sessions list called a session live if its transcript file was
written recently, the fleet view keyed off heartbeats, and each adapter decided
for itself whether a quiet transcript meant "finished" or "still going". That is
how one session reads as running on one tab and dead on another, and it is why
a Claude Code session and a Codex session cannot be put in one ordering.

This module is the vocabulary they all project onto. It is *pure*: no
filesystem, no store, no ambient clock. Everything it needs is passed in, so
the whole state machine is testable without a runtime installed.

Two rules carry the honesty of the model, and both fail towards "less alive"
rather than "more":

- **Absent is not the same as calm.** Where the observed data cannot establish
  a phase, :func:`resolve` returns ``None``. It never returns ``idle``, because
  a runtime we cannot see would otherwise be reported as a runtime with nothing
  happening -- the same failure as reading silence as health.
- **Activeness is an allowlist.** :func:`is_active` answers from
  :data:`ACTIVE_PHASES`. A phase nobody has mapped yet (including one added by a
  later change and not declared here) is *not* active, rather than being
  silently treated as a running agent.

Every verdict carries a ``basis`` naming how it was reached, so a reader can
tell a phase the adapter asserted from one derived from a timestamp -- the same
discipline as Guard's ``threshold_source`` and ``spend_basis``.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

# ── The coarse vocabulary every adapter must produce ───────────────────────
PHASE_WAITING = "waiting"   # blocked on a person: a permission ask, a question
PHASE_WORKING = "working"   # the agent is doing something right now
PHASE_IDLE = "idle"         # alive, nothing happening, nobody blocked
PHASE_ENDED = "ended"       # terminal; see the end reason for which kind

PHASES = (PHASE_WAITING, PHASE_WORKING, PHASE_IDLE, PHASE_ENDED)

# The allowlist. Membership is declared, never derived by exclusion, so adding
# a phase without deciding what it means leaves it inactive instead of live.
# ``idle`` is deliberately OUT: a session with nothing happening is alive but is
# not an agent doing work, and every consumer of "active" so far means the
# latter. A consumer that wants "not ended" should ask for that.
ACTIVE_PHASES = frozenset({PHASE_WAITING, PHASE_WORKING})

# ── The fine-grained status richer adapters add on top ─────────────────────
# Surfaces render the PHASE and enrich with the status where one is present, so
# a thin adapter never needs special-casing. Each status projects onto exactly
# one phase; a status that is not in this table projects onto nothing.
STATUS_TO_PHASE = {
    "thinking": PHASE_WORKING,
    "tool_use": PHASE_WORKING,
    "responding": PHASE_WORKING,
    "compacting": PHASE_WORKING,
    "permission_requested": PHASE_WAITING,
}

STATUSES = tuple(STATUS_TO_PHASE)

# ── Why a session ended ────────────────────────────────────────────────────
# The shared reasons. A runtime that states its own reason keeps it verbatim
# (``user_stopped``, ``max_turns``, ``turn_aborted:interrupted``, ...) -- these
# are filled in only where the runtime says nothing, so no adapter's account of
# what happened is ever overwritten by ours.
END_SESSION_END = "session-end"  # the session concluded
END_STALE = "stale"              # no activity for long enough to call it over
END_DEAD_PID = "dead-pid"        # the process backing it is gone
END_ARCHIVED = "archived"        # the runtime moved it out of the live set

END_REASONS = (END_SESSION_END, END_STALE, END_DEAD_PID, END_ARCHIVED)

# Native reasons whose *kind* we can state. Anything else an adapter writes is
# classified as a plain session-end: the runtime asserted an end, and we do not
# invent a category for a word we do not recognise.
_END_REASON_KINDS = {
    END_SESSION_END: END_SESSION_END,
    END_STALE: END_STALE,
    END_DEAD_PID: END_DEAD_PID,
    END_ARCHIVED: END_ARCHIVED,
    "archived": END_ARCHIVED,
    "stale": END_STALE,
}

# ── Recency windows ────────────────────────────────────────────────────────
# A session touched within the working window is working; one quiet for longer
# than the stale window was abandoned rather than finished.
#
# These are NOT new numbers. They are the windows ``sync._session_liveness``
# has been bucketing sessions into as active / idle / ended, moved here so
# there is one definition of "recent" instead of a second one invented beside
# it -- which is the disease this whole module exists to cure. ``sync.py``
# imports them from here; changing them changes both, on purpose.
DEFAULT_WORKING_SECS = 120.0
DEFAULT_STALE_SECS = 600.0


def _env_secs(name: str, default: float) -> float:
    """Read a positive float from the environment. Bad input keeps the default
    (never crash on bad input), and the read happens per call so a test or an
    operator can change it without re-importing."""
    try:
        raw = os.environ.get(name, "").strip()
        if not raw:
            return default
        val = float(raw)
        return val if val > 0 else default
    except (TypeError, ValueError):
        return default


def working_window_secs() -> float:
    return _env_secs("CLAWMETRY_PHASE_WORKING_SECS", DEFAULT_WORKING_SECS)


def stale_window_secs() -> float:
    return _env_secs("CLAWMETRY_PHASE_STALE_SECS", DEFAULT_STALE_SECS)


@dataclass(frozen=True)
class PhaseVerdict:
    """What :func:`resolve` decided, and how.

    ``phase`` is ``None`` when the observed data could not establish one --
    which is a real answer, not a missing one. ``basis`` names the route taken:

    ``adapter``          the adapter asserted the phase itself
    ``status``           projected from the adapter's fine-grained status
    ``asserted-end``     the runtime stated a reason the session ended
    ``dead-pid``         the process backing the session is gone
    ``archived``         the runtime moved the session out of its live set
    ``recency``          derived from how long ago the session was last active
    ``unmapped-phase``   the adapter sent a phase this module does not know
    ``unmapped-status``  the adapter sent a status with no phase projection
    ``no-signal``        nothing observable to decide on
    """

    phase: str | None
    status: str | None = None
    end_reason: str = ""
    basis: str = "no-signal"

    @property
    def active(self) -> bool:
        return is_active(self.phase)


def normalize_phase(phase: object) -> str | None:
    """Return a known phase, or ``None``. Unknown input is not coerced."""
    if not phase:
        return None
    val = str(phase).strip().lower()
    return val if val in PHASES else None


def normalize_status(status: object) -> str | None:
    """Return the status as written, lowercased, or ``None`` if empty.

    Deliberately does NOT drop an unknown status: an adapter reporting
    ``permission_denied`` is telling us something true, and the projection --
    not this function -- is where an unmapped value stops being trusted.
    """
    if not status:
        return None
    val = str(status).strip().lower()
    return val or None


def phase_for_status(status: object) -> str | None:
    """Project a fine-grained status onto its coarse phase.

    Pure and total: a status with no mapping returns ``None`` so it flows into
    "not active" rather than into whichever phase happened to be first.
    """
    val = normalize_status(status)
    if val is None:
        return None
    return STATUS_TO_PHASE.get(val)


def is_active(phase: object) -> bool:
    """Is this phase one where an agent is live and this session is in play?

    Answered from :data:`ACTIVE_PHASES` only. ``None``, ``idle``, ``ended`` and
    anything unrecognised are all not active -- including a phase added to
    :data:`PHASES` later and never declared here, which is the point.
    """
    if not phase:
        return False
    return str(phase).strip().lower() in ACTIVE_PHASES


def end_reason_kind(end_reason: object) -> str:
    """Classify an end reason into the shared vocabulary.

    A runtime's own words are preserved everywhere else; this is for a consumer
    that needs the category. An unrecognised but non-empty reason is a
    ``session-end``: the runtime asserted an end, and inventing a finer
    category for a word we do not know would be a guess dressed as a fact.
    """
    if not end_reason:
        return ""
    val = str(end_reason).strip().lower()
    if not val:
        return ""
    if val in _END_REASON_KINDS:
        return _END_REASON_KINDS[val]
    # ``turn_aborted:interrupted`` and friends: the prefix carries the meaning.
    head = val.split(":", 1)[0]
    return _END_REASON_KINDS.get(head, END_SESSION_END)


def resolve(
    *,
    now: float,
    phase: object = None,
    status: object = None,
    end_reason: object = "",
    last_activity_at: float | None = None,
    started_at: float | None = None,
    archived: bool = False,
    pid: object = None,
    pid_alive=None,
    working_secs: float | None = None,
    stale_secs: float | None = None,
) -> PhaseVerdict:
    """Decide a session's phase from what was actually observed.

    Precedence, strongest evidence first:

    1. **The adapter said so.** A phase it asserts is taken as given -- it can
       see its own runtime and we cannot. An assertion outside the vocabulary
       is refused rather than coerced, so a typo reads as unknown.
    2. **A fine-grained status.** Projected through :func:`phase_for_status`.
       An unmapped status yields no phase (see the module docstring).
    3. **An asserted end beats recency.** A runtime that stated why a session
       ended is right even if the file was touched a second ago -- the same
       precedence the OpenClaw ingest already applies.
    4. **A dead process.** Only when the caller supplied both a pid and a way
       to check it; we never shell out from here.
    5. **Archived.** The runtime moved it out of its live set.
    6. **Recency.** Within the working window it is working; beyond the stale
       window it has been abandoned; in between it is idle.

    With no timestamp and nothing asserted the answer is ``None`` with basis
    ``no-signal``. ``last_activity_at`` falls back to ``started_at`` because a
    session observed once, at its start, has exactly one thing known about it.
    """
    explicit = normalize_phase(phase)
    if phase and explicit is None:
        # Sent something, but not something we know. Refuse it loudly-in-data.
        return PhaseVerdict(None, normalize_status(status),
                            str(end_reason or ""), "unmapped-phase")
    norm_status = normalize_status(status)
    reason = str(end_reason or "").strip()

    if explicit is not None:
        return PhaseVerdict(explicit, norm_status, reason, "adapter")

    if norm_status is not None:
        projected = phase_for_status(norm_status)
        if projected is not None:
            return PhaseVerdict(projected, norm_status, reason, "status")
        return PhaseVerdict(None, norm_status, reason, "unmapped-status")

    if reason:
        return PhaseVerdict(PHASE_ENDED, None, reason, "asserted-end")

    if pid and callable(pid_alive):
        try:
            if not pid_alive(int(pid)):
                return PhaseVerdict(PHASE_ENDED, None, END_DEAD_PID, "dead-pid")
        except (TypeError, ValueError):
            pass  # unusable pid is no evidence either way

    if archived:
        return PhaseVerdict(PHASE_ENDED, None, END_ARCHIVED, "archived")

    last = last_activity_at or started_at or 0.0
    try:
        last = float(last or 0.0)
    except (TypeError, ValueError):
        last = 0.0
    if last <= 0:
        return PhaseVerdict(None, None, "", "no-signal")

    work = working_secs if working_secs is not None else working_window_secs()
    stale = stale_secs if stale_secs is not None else stale_window_secs()
    # A last-activity in the future is clock skew between the node writing the
    # transcript and the process reading it. Treat it as "just now" rather than
    # letting a negative age fall through to a stale verdict.
    age = max(0.0, float(now) - last)
    if age <= work:
        return PhaseVerdict(PHASE_WORKING, None, "", "recency")
    if age <= stale:
        return PhaseVerdict(PHASE_IDLE, None, "", "recency")
    return PhaseVerdict(PHASE_ENDED, None, END_STALE, "recency")
