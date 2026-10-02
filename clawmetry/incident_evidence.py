"""Stable detector evidence and conservative, positive recovery proofs.

No I/O in normalization or proof construction. The daemon reconciler uses its
existing store handle; it never reads a transcript or changes a policy latch.
"""
from __future__ import annotations

import json

from clawmetry.incident_store import LIFECYCLE_KINDS, clean_refs, epoch_ms


def call_id(data, *, include_id=False):
    if not isinstance(data, dict):
        return ""
    keys = ("tool_call_id", "tool_use_id", "call_id", "toolCallId", "toolUseId",
            "gen_ai.tool.call.id", "tool.call.id") + (("id",) if include_id else ())
    for key in keys:
        value = data.get(key)
        if isinstance(value, str) and value and len(value) <= 1024:
            return value
    msg = data.get("message")
    return call_id(msg, include_id=include_id) if isinstance(msg, dict) else ""


def enrich_steps(steps, events):
    """Attach source IDs and match results by native ID before inference.

    The caller passes the SAME chronological window used to assign ``i``.
    No result is guessed to belong to the last of several pending calls.
    """
    pending = []
    by_id = {}
    for step in steps:
        ev = events[step["i"]]
        data = ev.get("data")
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (TypeError, ValueError):
                data = {}
        if not isinstance(data, dict):
            data = {}
        step["event_id"] = ev.get("id") or ""
        step["ts"] = epoch_ms(ev.get("ts"))
        step["event_type"] = ev.get("event_type") or ""
        step["span_id"] = data.get("span_id") or ""
        step["trace_id"] = data.get("trace_id") or ""
        if step["kind"] == "tool_call":
            pending.append(step)
            if step.get("tool_call_id"):
                by_id[step["tool_call_id"]] = step
        elif step["kind"] == "tool_result":
            cid = step.get("tool_call_id") or call_id(data)
            step["tool_call_id"] = cid
            match = by_id.get(cid) if cid else None
            relationship = "native" if match else "unavailable"
            if not cid:
                possible = [s for s in pending if not step["tool"] or s["tool"] == step["tool"]]
                if len(possible) == 1:
                    match, relationship = possible[0], "inferred_single_pending"
            if match:
                # The native identity is authoritative even when the result
                # mislabels the name. Keep inference explicitly labelled.
                step["tool"] = match["tool"]
                step["call_event_id"] = match["event_id"]
                step["call_args_hash"] = match["args_hash"]
                step["call_mutates"] = bool(match.get("mutates"))
                if match in pending:
                    pending.remove(match)
                if match.get("tool_call_id"):
                    by_id.pop(match["tool_call_id"], None)
            step["relationship"] = relationship
    return steps


def reference(step):
    return {k: step.get(k) for k in ("event_id", "ts", "tool_call_id", "span_id", "trace_id")}


def attach_evidence(incident, steps):
    """Resolve window-relative localization before that window moves."""
    if incident.get("kind") not in LIFECYCLE_KINDS:
        return incident
    first = incident.get("first_bad_step")
    if not isinstance(first, int):
        return incident
    selected = [s for s in steps if s["i"] >= first]
    if incident["kind"] == "repeated_tool_failure":
        tool = (incident.get("evidence") or {}).get("tool")
        selected = [s for s in selected if s["kind"] == "tool_result"
                    and s["is_error"] and (s["tool"] or "tool") == tool]
    else:
        selected = [s for s in selected if s["kind"] == "tool_call"]
        incident["evidence"]["call_signatures"] = list(dict.fromkeys(
            (s["tool"], s["args_hash"]) for s in selected))[:16]
    incident["evidence_refs"] = clean_refs([reference(s) for s in selected])
    if incident["evidence_refs"]:
        incident["first_bad_event_id"] = incident["evidence_refs"][0]["event_id"]
    return incident


def positive_recovery(episode, steps, *, before_index=None):
    """Find later positive progress; absence of a detector is never proof."""
    last = episode.get("last_evidence_at")
    if last is None:
        return None
    evidence = episode.get("evidence") or {}
    signatures = {tuple(s) for s in evidence.get("call_signatures", [])
                  if isinstance(s, (list, tuple)) and len(s) == 2}
    for step in steps:
        if (not step.get("event_id") or step.get("ts") is None or step["ts"] <= last
                or (before_index is not None and step["i"] >= before_index)):
            continue
        success = (step["kind"] == "tool_result" and not step["is_error"]
                   and step.get("outcome_known"))
        if episode["kind"] == "repeated_tool_failure":
            if success and step["tool"] and step["tool"] == evidence.get("tool"):
                return dict(reference(step), reason="tool_succeeded")
        elif episode["kind"] == "stuck_loop":
            progressed = (step["kind"] == "text" and step.get("has_text"))
            progressed = progressed or step.get("event_type") == "session.completed"
            if success and step.get("call_event_id"):
                changed = signatures and (step["tool"], step.get("call_args_hash")) not in signatures
                progressed = progressed or step.get("call_mutates") or changed
            if progressed:
                return dict(reference(step), reason="progress_observed")
    return None


def reconcile_session(store, incidents, events, steps, *, session_id, runtime,
                      node_id, completed=True, disabled=(), observed_at=None):
    """Reconcile one successfully inspected window; returns kind -> episode.

    A recovery before a newly implicated stretch closes the previous episode
    first, so recurrence in the same read window still gets a fresh identity.
    """
    if not completed or not events or not steps or not node_id:
        return {}
    enabled = LIFECYCLE_KINDS.difference(disabled)
    current = {inc["kind"]: inc for inc in incidents if inc.get("kind") in enabled}
    previous = store.query_incident_heads(session_id=session_id, runtime=runtime,
                                          node_id=node_id)
    for episode in previous:
        kind = episode["kind"]
        if kind not in enabled or episode["state"] == "recovered":
            continue
        proof = positive_recovery(episode, steps,
                                  before_index=current.get(kind, {}).get("first_bad_step"))
        if proof:
            store.recover_incident(incident_id=episode["incident_id"], recovery_ref=proof,
                                   observed_at=observed_at)
    out = {}
    for kind, inc in current.items():
        episode = store.record_incident_observation(incident=inc, node_id=node_id,
                                                    observed_at=observed_at)
        if episode:
            inc["incident_id"] = episode["incident_id"]
            inc["incident_state"] = episode["state"]
            out[kind] = episode
    return out


def reconcile_ended_sessions(store, active_session_ids, *, disabled=(), observed_at=None):
    """Recently completed sessions still need their final positive proof read.

    This does not run detectors or controls on a completed session. Bounded by
    the open-head read and the existing detector event window. Each inactive
    session is read once even if it has two open kinds.
    """
    from clawmetry import detectors
    windows = {}
    for episode in store.query_incident_heads():
        if episode["session_id"] in active_session_ids or episode["kind"] in disabled:
            continue
        key = (episode["session_id"], episode["runtime"], episode["node_id"])
        if key not in windows:
            events = store.query_incident_window(session_id=key[0], runtime=key[1], node_id=key[2])
            windows[key] = detectors.normalize_events(events) if events else []
        proof = positive_recovery(episode, windows[key])
        if proof:
            store.recover_incident(incident_id=episode["incident_id"], recovery_ref=proof,
                                   observed_at=observed_at)
