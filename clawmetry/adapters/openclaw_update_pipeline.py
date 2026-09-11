"""Update-pipeline state scanner for the OpenClaw adapter.

OpenClaw 2026.9.3's safer-update pipeline rehearses core and plugin changes in
an isolated candidate state before activation, and can recover an abandoned
update record without stopping a healthy Gateway. Those transitions appear only
in the gateway log, so an agent stuck half-activated or abandoned showed no
signal on any health surface (issue #5749).

Kept in its own module so Drift Bot can find it at the head of a short file
rather than buried deep inside the ~2,700-line adapter.

One of five gateway-log scanners, recorded together as "Gateway-log scanners:
what the harness did that the transcript never shows" in the Runtime and
Session Observability blueprint. That section carries the contracts they all
share -- no I/O of their own, ``{}`` and never raise when nothing is found,
keys additive and absent when undetected, each naming the OpenClaw version
whose behaviour it detects -- and the ADR for why these are keyword scans over
prose rather than parsers.
"""
from __future__ import annotations


def update_pipeline_state(events: list) -> dict:
    """Return update-pipeline metadata from gateway log events.

    OpenClaw 2026.9.3's safer-update pipeline (#136997, #138839, #141109,
    #141175, #141562) rehearses core/plugin changes in an isolated candidate
    state before activation and can recover abandoned update records without
    stopping a healthy Gateway.  These state transitions appear in the gateway
    log; surfacing them lets ClawMetry flag agents stuck in a half-activated or
    abandoned update state.

    Scans the already-fetched events list (no extra I/O).  Matches:
    - candidate state: msg contains "candidate" + ("update" | "activat")
    - abandoned update recovery: msg contains "abandon" + ("update" | "recover")
    - activation event: msg contains "activation" + "update"

    Returns a dict with one or more of:
    - ``updatePipelineStateDetected`` (bool): True when any update event found
    - ``updatePipelineCandidateState`` (bool): True when candidate-state found
    - ``updatePipelineAbandoned`` (bool): True when abandoned-update recovery found
    - ``updatePipelineMsg`` (str): the first matching event's msg
    - ``updatePipelineTs`` (str): the first matching event's ts, if present

    Returns ``{}`` when no update-pipeline event is found.
    Never raises (closes #5749).
    """
    try:
        if not events:
            return {}
        result: dict = {}
        for evt in events:
            if not isinstance(evt, dict):
                continue
            raw_msg = evt.get("msg", "")
            msg = str(raw_msg).lower()
            if not msg:
                continue
            is_candidate = "candidate" in msg and (
                "update" in msg or "activat" in msg
            )
            is_abandoned = "abandon" in msg and (
                "update" in msg or "recover" in msg
            )
            is_activation = "activation" in msg and "update" in msg
            if not (is_candidate or is_abandoned or is_activation):
                continue
            if not result:
                result = {
                    "updatePipelineStateDetected": True,
                    "updatePipelineMsg": str(raw_msg),
                }
                ts = evt.get("ts")
                if ts is not None:
                    result["updatePipelineTs"] = ts
            if is_candidate and not result.get("updatePipelineCandidateState"):
                result["updatePipelineCandidateState"] = True
            if is_abandoned and not result.get("updatePipelineAbandoned"):
                result["updatePipelineAbandoned"] = True
        return result
    except Exception:
        return {}


# Private alias, matching openclaw_reply_recovery: the adapter imports the
# underscore-prefixed name so its call sites read the same for every scanner.
_openclaw_update_pipeline_state = update_pipeline_state
