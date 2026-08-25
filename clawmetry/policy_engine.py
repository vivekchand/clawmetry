"""Guard policies — turn a detector incident into an enforcement decision.

This module is the wire between two halves that already existed but never
touched: :mod:`clawmetry.detectors` (which finds agents that have gone off
track) and :mod:`clawmetry.process_control` (which can pause/stop/kill them).
Before this, the only edge between detection and action was a human noticing a
banner and pressing Stop.

**This module is pure.** ``evaluate()`` does no I/O, opens no store, sends no
signals. It takes incidents + policies + facts and returns decisions. The
daemon (``sync.py::_emit_detector_incidents``) does the reading, the
dispatching and the auditing. Keeping it pure means the whole matching
surface is unit-testable without a daemon, a DuckDB file or a live agent —
the same split ``detectors.py`` uses.

A policy row (see ``local_store.session_policy``)::

    {
      "policy_id":      str,
      "enabled":        bool,
      "scope_runtime":  str,   # "" = every runtime
      "scope_agent_id": str,   # "" = every agent
      "trigger_kind":   str,   # "" = any detector kind
      "min_severity":   "info" | "warning",
      "min_repeat":     int,   # incident count must be >= this
      "min_duration_s": int,   # session bad for at least this long
      "min_spend_usd":  float, # session cost must be >= this
      "min_spend_at_risk_usd": float,  # the FLAGGED STRETCH must be worth
                               # >= this (an estimate the detector attaches;
                               # 0 or missing means the threshold is unused)
      "action":         "monitor" | "alert" | "pause" | "stop" | "kill",
      "steps":          list,  # OPTIONAL escalation ladder, see below
    }

**Escalation ladders.** A single action fired once is not how operations
actually respond to a stuck agent — the real shape is *pause it, tell me,
give it five minutes, then kill it if it is still stuck*. ``steps`` expresses
that as an ordered list::

    "steps": [
      {"action": "pause", "after_secs": 0},
      {"action": "alert", "after_secs": 0},
      {"action": "kill",  "after_secs": 300}
    ]

Semantics, chosen so a ladder can never act faster than a plain policy:

* Step 0 fires when the policy first matches; its ``after_secs`` is ignored
  (use ``min_duration_s`` for a delay *before* the first action).
* Step *n* becomes due ``after_secs`` seconds after step *n-1* actually
  fired — not after the incident started — so a ladder measures the time the
  agent was given to recover.
* A due step only fires if the session is STILL matching this tick. That is
  what makes "kill if still stuck" mean *still stuck*: if the detector stops
  reporting, the ladder simply stops.
* Every step passes through the same three locks as a plain action. A
  ``kill`` step on a node with ``CLAWMETRY_POLICY_ENFORCE=0`` is recorded as
  a dry run exactly like a ``kill`` policy would be.
* The durable latch is per ``(session, policy, step)``, so a daemon restart
  mid-ladder resumes at the right rung instead of replaying it.

A policy with no ``steps`` is a one-step ladder built from its ``action``,
which is why every existing policy keeps behaving identically.

All thresholds are AND-ed. An unset threshold (0) never blocks a match, so a
policy with everything zeroed fires on the first matching incident.

A decision::

    {
      "policy_id":   str,
      "session_id":  str,
      "runtime":     str,
      "cwd":         str,
      "action":      str,
      "kind":        str,     # detector kind that triggered it
      "reason":      str,     # plain words, shown in the UI and audit row
      "evidence":    dict,    # the numbers that satisfied the thresholds
      "step_index":  int,     # which rung of the ladder this is (0-based)
      "step_count":  int,     # how many rungs the ladder has
      "is_final_step": bool,  # nothing escalates after this one
      "next_action": str,     # "" when this was the last rung
      "next_after_secs": int, # how long until the next rung becomes due
    }

Safety invariants enforced here (the daemon adds two more — the enforce env
flag and the one-shot latch):

* **At most one decision per session.** Several policies can match the same
  session; firing each would mean several signals at one process. The
  strongest action wins, ties broken by ``policy_id`` so the choice is
  deterministic and reproducible in tests.
* **``monitor`` is a real decision, not a skip.** It returns a decision the
  daemon records to the audit trail without acting. That is what makes
  dry-run honest: you can see exactly what *would* have fired.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

# Action ladder, weakest first. Order IS the escalation order and the
# strongest-wins comparison; do not reorder without updating the UI copy.
ACTIONS = ("monitor", "alert", "pause", "stop", "kill")
_ACTION_RANK = {name: i for i, name in enumerate(ACTIONS)}

# Actions that actually signal the agent's process. Everything below `pause`
# only writes rows. The daemon uses this to decide whether the enforce flag
# and the latch apply.
ACTUATING_ACTIONS = frozenset({"pause", "stop", "kill"})

# ``critical`` is the tier the detectors reserve for two things: an incident
# whose spend at risk crossed ``detectors.CRITICAL_SPEND_USD``, and a
# behavioural finding that outlives the session (a disabled protection, a
# recursive delete at a home root). A policy can require it, which is how you
# write "kill only the expensive or irreversible ones".
_SEVERITY_RANK = {"info": 0, "warning": 1, "critical": 2}


def action_rank(action: str) -> int:
    """Position on the escalation ladder; unknown actions sort weakest."""
    return _ACTION_RANK.get(str(action or "").strip().lower(), -1)


def is_actuating(action: str) -> bool:
    """True when the action sends a signal to a real process."""
    return str(action or "").strip().lower() in ACTUATING_ACTIONS


def _severity_rank(sev: Any) -> int:
    return _SEVERITY_RANK.get(str(sev or "warning").strip().lower(), 1)


def _incident_count(incident: Dict[str, Any]) -> int:
    """Best-effort 'how many times' number behind an incident.

    Detectors put their count under different evidence keys depending on the
    kind (a loop counts repeats, no-progress counts tool calls, a repeated
    failure counts failures). We take the largest of the known keys so one
    ``min_repeat`` threshold reads sensibly against every detector.
    """
    ev = incident.get("evidence")
    if not isinstance(ev, dict):
        return 0
    best = 0
    for key in ("repeat_count", "repeats", "total_tool_calls", "tool_calls",
                "failure_count", "failures", "count"):
        try:
            val = int(ev.get(key) or 0)
        except (TypeError, ValueError):
            continue
        if val > best:
            best = val
    return best


def _as_float(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _as_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _scope_matches(policy_value: Any, actual: Any) -> bool:
    """Empty scope means 'all'. Comparison is case-insensitive."""
    want = str(policy_value or "").strip().lower()
    if not want:
        return True
    return want == str(actual or "").strip().lower()


# A ladder longer than this is almost certainly a mistake, and each rung is a
# durable row plus a latch check per tick. Extra rungs are dropped, not
# rejected, so a bad rule degrades instead of disabling the whole policy.
MAX_LADDER_STEPS = 8

# Upper bound on a rung's delay (24h). A typo of 300000 instead of 300 would
# otherwise park a ladder forever with no sign anything was wrong.
MAX_STEP_DELAY_SECS = 86400


def normalize_steps(policy: Dict[str, Any]) -> List[Dict[str, Any]]:
    """The policy's escalation ladder as ``[{"action", "after_secs"}, ...]``.

    A policy with no usable ``steps`` becomes a ONE-step ladder built from its
    ``action``, which is what keeps every pre-ladder policy behaving exactly
    as before.

    Malformed rungs are DROPPED rather than coerced. Coercing an unrecognised
    action to a default would silently change what a rule does to someone's
    agent; dropping it means the ladder is shorter than authored, which the
    UI can show. Step 0's delay is forced to 0 (see the module docstring) and
    every delay is clamped to ``MAX_STEP_DELAY_SECS``.
    """
    fallback = str(policy.get("action") or "monitor").strip().lower()
    if fallback not in _ACTION_RANK:
        fallback = "monitor"

    raw = policy.get("steps")
    if isinstance(raw, str):
        # The store round-trips steps as JSON text; tolerate either form so a
        # policy read straight from DuckDB and one posted from the UI behave
        # identically.
        import json
        try:
            raw = json.loads(raw)
        except Exception:  # noqa: BLE001
            raw = None

    steps: List[Dict[str, Any]] = []
    if isinstance(raw, (list, tuple)):
        for entry in raw:
            if len(steps) >= MAX_LADDER_STEPS:
                break
            if not isinstance(entry, dict):
                continue
            act = str(entry.get("action") or "").strip().lower()
            if act not in _ACTION_RANK:
                continue
            delay = _as_int(entry.get("after_secs"))
            delay = max(0, min(delay, MAX_STEP_DELAY_SECS))
            steps.append({"action": act,
                          "after_secs": 0 if not steps else delay})

    if not steps:
        return [{"action": fallback, "after_secs": 0}]
    return steps


def _due_step(steps: List[Dict[str, Any]], state: Optional[Dict[str, Any]],
              now: float) -> Optional[int]:
    """Which rung, if any, should fire right now. ``None`` = nothing due.

    ``state`` is what the store knows about this ``(session, policy)`` pair:
    ``{"last_step": int, "last_fired_at": float-epoch-seconds}``. No state
    means the ladder has not started, so rung 0 is due.

    Returns None when the ladder is finished or the next rung's delay has not
    elapsed. A missing/garbage ``last_fired_at`` is treated as "just fired",
    which DELAYS the next rung rather than firing it early — the safe way to
    be wrong when the next rung might be a kill.
    """
    if not steps:
        return None
    if not isinstance(state, dict):
        return 0
    last = _as_int(state.get("last_step"))
    if state.get("last_step") is None:
        return 0
    nxt = last + 1
    if nxt >= len(steps):
        return None  # ladder exhausted
    try:
        fired_at = float(state.get("last_fired_at") or 0)
    except (TypeError, ValueError):
        fired_at = 0.0
    if fired_at <= 0:
        fired_at = float(now)  # unknown -> wait the full delay from now
    if float(now) - fired_at < float(steps[nxt]["after_secs"]):
        return None
    return nxt


def _match(policy: Dict[str, Any], incident: Dict[str, Any],
           facts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the evidence dict when `policy` matches, else None.

    Returning the evidence rather than a bool means the decision carries the
    exact numbers that satisfied each threshold, so the audit row can say
    *why* rather than just *that*.
    """
    if not policy.get("enabled", True):
        return None

    action = str(policy.get("action") or "monitor").strip().lower()
    if action not in _ACTION_RANK:
        return None  # unknown action: refuse rather than guess

    kind = str(incident.get("kind") or "").strip()
    want_kind = str(policy.get("trigger_kind") or "").strip()
    if want_kind and want_kind != kind:
        return None

    if not _scope_matches(policy.get("scope_runtime"), incident.get("runtime")):
        return None
    if not _scope_matches(policy.get("scope_agent_id"), facts.get("agent_id")):
        return None

    if _severity_rank(incident.get("severity")) < _severity_rank(
            policy.get("min_severity") or "info"):
        return None

    count = _incident_count(incident)
    min_repeat = _as_int(policy.get("min_repeat"))
    if min_repeat and count < min_repeat:
        return None

    duration_s = _as_float(facts.get("bad_for_seconds"))
    min_duration = _as_float(policy.get("min_duration_s"))
    if min_duration and duration_s < min_duration:
        return None

    spend = _as_float(facts.get("cost_usd"))
    min_spend = _as_float(policy.get("min_spend_usd"))
    if min_spend and spend < min_spend:
        return None

    # What the flagged stretch — not the whole session — is estimated to have
    # cost. The detector computes it; we carry it into the decision so the
    # audit row can answer "was acting on this worth it?" in dollars.
    spend_at_risk = _as_float(incident.get("spend_at_risk_usd"))
    min_at_risk = _as_float(policy.get("min_spend_at_risk_usd"))
    if min_at_risk and spend_at_risk < min_at_risk:
        return None

    return {
        "count": count,
        "bad_for_seconds": int(duration_s),
        "cost_usd": round(spend, 4),
        "spend_at_risk_usd": round(spend_at_risk, 4),
        "spend_basis": str(incident.get("spend_basis") or "unknown"),
        "severity": str(incident.get("severity") or "warning"),
        "thresholds": {
            "min_repeat": min_repeat,
            "min_duration_s": int(min_duration),
            "min_spend_usd": round(min_spend, 4),
            "min_spend_at_risk_usd": round(min_at_risk, 4),
            "min_severity": str(policy.get("min_severity") or "info"),
        },
    }


def _reason(policy: Dict[str, Any], incident: Dict[str, Any],
            evidence: Dict[str, Any], step_index: int = 0,
            steps: Optional[List[Dict[str, Any]]] = None) -> str:
    """Plain-words explanation, shown in the UI and stored in the audit row.

    Deliberately states the observation and the threshold it crossed, so a
    user reading it later can tell whether the policy was well-tuned. For a
    multi-rung ladder it also says which rung this is and what happens next,
    because "pause" reads very differently when the next line is "then kill
    in 5m if still stuck".
    """
    steps = steps or normalize_steps(policy)
    idx = max(0, min(int(step_index), len(steps) - 1))
    action = steps[idx]["action"]
    title = str(incident.get("title") or incident.get("kind") or "incident")
    bits: List[str] = []
    if evidence.get("count"):
        bits.append(f"{evidence['count']} events")
    if evidence.get("bad_for_seconds"):
        bits.append(f"{int(evidence['bad_for_seconds'] // 60)}m without progress")
    if evidence.get("cost_usd"):
        bits.append(f"${evidence['cost_usd']:.2f} spent")
    if evidence.get("spend_at_risk_usd"):
        # The number that decides whether this was worth acting on.
        bits.append(f"~${evidence['spend_at_risk_usd']:.2f} at risk")
    detail = ", ".join(bits) if bits else "threshold met"
    verb = "would " + action if action == "monitor" else action
    text = f"{title} ({detail}) -> {verb}"
    if len(steps) > 1:
        text += f" [step {idx + 1}/{len(steps)}]"
        if idx + 1 < len(steps):
            nxt = steps[idx + 1]
            text += (f", then {nxt['action']} in "
                     f"{_humanize_secs(int(nxt['after_secs']))} if still matching")
    return text[:400]


def _humanize_secs(secs: int) -> str:
    """``300`` -> ``5m``. Short enough to sit inside a 400-char reason."""
    secs = max(0, int(secs))
    if secs < 60:
        return f"{secs}s"
    if secs < 3600:
        return f"{secs // 60}m"
    return f"{secs // 3600}h"


def evaluate(incidents: Iterable[Dict[str, Any]],
             policies: Iterable[Dict[str, Any]],
             session_facts: Optional[Dict[str, Dict[str, Any]]] = None,
             ladder_state: Optional[Dict[str, Dict[str, Dict[str, Any]]]] = None,
             now: Optional[float] = None,
             ) -> List[Dict[str, Any]]:
    """Match incidents against policies and return at most one decision per
    session (the strongest matching action wins).

    ``session_facts`` maps ``session_id`` -> ``{"cost_usd", "bad_for_seconds",
    "runtime", "cwd", "agent_id"}``. A missing entry is treated as all-zero
    facts, which means spend/duration thresholds simply never match for that
    session rather than matching by accident.

    ``ladder_state`` maps ``session_id -> policy_id ->
    {"last_step", "last_fired_at"}`` — how far each ladder has already got,
    read from the audit table by the daemon. Omitting it means every matching
    policy is at rung 0, which is exactly the pre-ladder behaviour.

    ``now`` is the evaluation clock in epoch seconds, injected so ladder
    timing is testable without sleeping. Defaults to wall-clock.

    Pure: no I/O, no exceptions raised for bad input rows (malformed policies
    and incidents are skipped, matching the repo's never-crash-on-bad-input
    rule).
    """
    import time as _time

    facts_by_session = session_facts or {}
    state_by_session = ladder_state or {}
    clock = float(now) if now is not None else _time.time()
    policy_list = [p for p in (policies or []) if isinstance(p, dict)]
    if not policy_list:
        return []

    best_by_session: Dict[str, Dict[str, Any]] = {}

    for incident in incidents or []:
        if not isinstance(incident, dict):
            continue
        session_id = str(incident.get("session_id") or "").strip()
        if not session_id:
            continue  # an incident with no session cannot be acted on
        facts = facts_by_session.get(session_id) or {}
        session_state = state_by_session.get(session_id) or {}

        for policy in policy_list:
            evidence = _match(policy, incident, facts)
            if evidence is None:
                continue

            policy_id = str(policy.get("policy_id") or "")
            # Which rung of this policy's ladder is due right now. A ladder
            # that has finished, or whose next rung has not come round yet,
            # yields no decision at all this tick.
            steps = normalize_steps(policy)
            step_index = _due_step(steps, session_state.get(policy_id), clock)
            if step_index is None:
                continue
            step = steps[step_index]
            action = step["action"]
            is_final = step_index >= len(steps) - 1
            nxt = None if is_final else steps[step_index + 1]

            candidate = {
                "policy_id": policy_id,
                "session_id": session_id,
                "runtime": str(incident.get("runtime") or facts.get("runtime") or ""),
                "cwd": str(facts.get("cwd") or ""),
                "action": action,
                "kind": str(incident.get("kind") or ""),
                "reason": _reason(policy, incident, evidence,
                                  step_index=step_index, steps=steps),
                "evidence": evidence,
                "step_index": step_index,
                "step_count": len(steps),
                "is_final_step": is_final,
                "next_action": "" if nxt is None else nxt["action"],
                "next_after_secs": 0 if nxt is None else int(nxt["after_secs"]),
            }

            current = best_by_session.get(session_id)
            if current is None:
                best_by_session[session_id] = candidate
                continue
            # Strongest action wins; deterministic tie-break on policy_id so
            # the same inputs always produce the same decision.
            cur_rank = action_rank(current["action"])
            new_rank = action_rank(action)
            if new_rank > cur_rank or (
                    new_rank == cur_rank and policy_id < current["policy_id"]):
                best_by_session[session_id] = candidate

    # Stable output ordering: strongest first, then session id.
    return sorted(
        best_by_session.values(),
        key=lambda d: (-action_rank(d["action"]), d["session_id"]),
    )
