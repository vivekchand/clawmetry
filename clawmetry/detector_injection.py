"""clawmetry/detector_injection.py: the ``prompt_injection`` Guard detector.

Defined here, registered in ``clawmetry/detectors.py`` (``DETECTOR_KINDS`` and
``_ALL_DETECTORS``), signatures in ``clawmetry/prompt_injection.py``.
REQ-GOV-PIJ-001, Factory requirement e87935d1-27e0-415f-a5f8-24bdf70accbc.

What it reads: the TEXT of tool results and of user-sourced messages in the
session's event window. That is a different input from every other detector,
which read the shape of the tool stream or tool-call arguments.

What it raises:

* ``warning`` when a tool result matches a signature: content the agent read
  is trying to give it instructions (indirect injection);
* ``info`` when only a user-sourced message matches: on a local machine that
  is usually the operator, on a chat channel it may be a third party (direct
  injection);
* ``critical`` when, after the matched content and before the next user
  prompt, the agent issued a tool call ``tool_risk`` rates high or critical:
  the shape of an injection being carried out.

Runtime-injected context (AGENTS.md, CLAUDE.md, ``<environment_context>``)
arrives as a user message on several runtimes. It is the operator's own
configuration, not a message, so it is skipped
(``clawmetry/injected_context.py``).

The finding never repeats the matched text: only signature ids, their plain
labels, the tool whose output carried them, and counts. Pure, bounded, never
raises.
"""
from __future__ import annotations

from typing import Iterable, Optional

from clawmetry import prompt_injection as _pi


def _core():
    from clawmetry import detectors as _d
    return _d


def _raw_text(data: dict, limit: int) -> str:
    """Tool-result or message text, original case, up to ``limit`` chars."""
    try:
        parts = []
        for k in ("output", "result", "content", "text", "stderr", "error", "details"):
            v = data.get(k)
            if isinstance(v, str) and v.strip():
                parts.append(v)
            elif isinstance(v, list):
                parts.append(_pi._block_text(v))
        msg = data.get("message")
        if isinstance(msg, dict):
            parts.append(_pi._block_text(msg.get("content")))
        elif isinstance(msg, str):
            parts.append(msg)
        return "\n".join(p for p in parts if p)[:limit]
    except Exception:
        return ""


def _has_tool_result_blocks(data: dict) -> bool:
    msg = data.get("message") if isinstance(data.get("message"), dict) else data
    content = msg.get("content")
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _call_risk(d, ev: dict) -> tuple:
    """(worst risk level, tool) of the tool calls one event carries."""
    from clawmetry.tool_risk import classify_tool_call
    et = str(ev.get("event_type") or "").strip().lower()
    data = d._coerce_dict(ev.get("data"))
    best = ("low", "")
    for c in d._iter_tool_calls_from_data(et, data):
        v = classify_tool_call(c.get("tool") or "", c.get("args"))
        if v["rank"] > _pi.RISK_RANK.get(best[0], 0):
            best = (v["level"], str(c.get("tool") or ""))
    return best


def prompt_injection(events: Iterable[dict], session_id: str,
                     runtime: Optional[str] = None, *,
                     thresholds: Optional[dict] = None,
                     steps: Optional[list] = None,
                     facts: Optional[dict] = None) -> Optional[dict]:
    """Flag tool output or a user-sourced message that tries to instruct the
    agent. See the module docstring for severities. Never raises."""
    try:
        d = _core()
        runtime, th, steps = d._prepare(events, steps, thresholds, runtime, session_id)
        evlist = d._chronological(events)
        try:
            from clawmetry.injected_context import human_prompt, is_injected_context
        except Exception:  # pragma: no cover - module ships with the package
            def is_injected_context(_v):  # type: ignore
                return False

            def human_prompt(_v):  # type: ignore
                return ""

        first = None          # (event index, source, tool, signatures)
        signatures: list = []
        tool_hits = 0
        user_hits = 0
        followed = None       # (level, tool) of the worst later high-risk call
        armed = False         # matched content seen in the current turn
        last_call_tool = ""
        for s in steps:
            i = s.get("i")
            if not isinstance(i, int) or not 0 <= i < len(evlist):
                continue
            kind = s.get("kind")
            ev = evlist[i] or {}
            data = d._coerce_dict(ev.get("data"))
            if kind == "tool_call":
                last_call_tool = s.get("tool") or last_call_tool
                if armed:
                    level, tool = _call_risk(d, ev)
                    if _pi.RISK_RANK.get(level, 0) >= _pi.RISK_RANK["high"]:
                        if followed is None or _pi.RISK_RANK[level] > _pi.RISK_RANK[followed[0]]:
                            followed = (level, tool)
                continue
            if kind == "tool_result" or (kind == "user" and _has_tool_result_blocks(data)):
                source = "tool_result"
                tool = str(s.get("tool") or "") or last_call_tool
            elif kind == "user":
                source = "user_message"
                tool = ""
                armed = False  # a person spoke: a new turn starts
                msg = data.get("message") if isinstance(data.get("message"), dict) else {}
                content = data.get("content") or msg.get("content") or data.get("text") or ""
                if is_injected_context(content):
                    continue
                # A person's prompt with harness context stapled to its head
                # (a system reminder, an AGENTS.md block) is scanned without it.
                text = human_prompt(content) or _pi._block_text(content)
                sigs = _pi.scan_text(text[:_pi.SCAN_CHARS])
                if not sigs:
                    continue
            else:
                continue
            if source == "tool_result":
                sigs = _pi.scan_text(_raw_text(data, _pi.SCAN_CHARS))
            if not sigs:
                continue
            armed = True
            if source == "tool_result":
                tool_hits += 1
            else:
                user_hits += 1
            for sid in sigs:
                if sid not in signatures:
                    signatures.append(sid)
            # A tool-result hit is the stronger evidence, so it is the one the
            # finding is anchored on even when a user message matched first.
            if first is None or (first[1] == "user_message" and source == "tool_result"):
                first = (i, source, tool, sigs)
        if first is None:
            return None

        idx, source, tool, first_sigs = first
        rt_label = runtime or "agent"
        where = f"{tool} output" if source == "tool_result" and tool else (
            "a tool result" if source == "tool_result" else "a user message")
        what = _pi.signature_label(first_sigs[0])
        if followed is not None:
            severity = "critical"
            title = f"{rt_label} ran a {followed[0]}-risk {followed[1] or 'command'} after {where} tried to instruct it"
        elif source == "tool_result":
            severity = "warning"
            title = f"{rt_label} read instructions hidden in {where}"
        else:
            severity = "info"
            title = f"a message to {rt_label} tried to override its instructions"
        detail = (f"Text in {where} {what}. Content the agent reads should be data, not "
                  f"orders. ")
        if followed is not None:
            detail += (f"After it, the agent ran {followed[1] or 'a command'}, rated "
                       f"{followed[0]} risk, before anyone spoke to it again. ")
        detail += ("This is a pattern match on the text, not proof the agent obeyed it. "
                   + d._stop_hint())
        return d._incident(
            "prompt_injection", session_id, runtime, severity, title, detail,
            {"source": source, "tool": tool or None,
             "signatures": signatures,
             "signature_labels": [_pi.signature_label(x) for x in signatures],
             "tool_result_matches": tool_hits, "user_message_matches": user_hits,
             "followed_by_tool": followed[1] if followed else None,
             "followed_by_risk": followed[0] if followed else None,
             "threshold": 1, "threshold_source": "static",
             "observed": ("declared injection signatures in the text of tool results "
                          "and user-sourced messages; matched text is not kept")},
            idx,
        )
    except Exception:
        return None
