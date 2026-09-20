"""Inputs & context emit helper shared by the runtime adapters.

This lives in OSS because the Free runtime adapters bundled here need it
(``clawmetry/adapters/qwen_code.py``). ``clawmetry_pro.adapters._inputs``
carries the same implementation for the paid adapters. CI cannot see that
repo, so ``tests/test_adapter_inputs_helper.py`` pins the contract both copies
must satisfy -- export surface, event shape, and the id-stability rule ingest
dedupes on -- rather than claiming to diff them. Same arrangement as
``clawmetry/adapters/cost.py``.

The OSS daemon stores what an agent was GIVEN (system prompt, first user
prompt, tool definitions, MCP servers, context files, runtime setup) from
``context.compiled`` events (``clawmetry/session_context.py``). OpenClaw's
trajectory recorder emits that event natively; paid adapters emit the same
shape here so the OSS ingest needs no runtime-specific code.

Contract (keys inside ``Event.extra``; every key optional, empties dropped):

    systemPrompt: str          verbatim text the runtime persisted
    prompt:       str          the first user request
    tools:        list         tool NAMES (str) or definitions ({name, ...})
    runtimeMeta:  dict         cwd, model, provider, version, permissionMode,
                               mcpServers [{name,...}], contextFiles
                               [{path, size_bytes?, sha256?}], plus any other
                               fact the native store states

HONESTY: pass only what the native store actually holds. A missing field is
a missing key, never a placeholder. ``tools`` is the tool CATALOGUE when the
runtime writes one; when only invoked tool names are known pass those and say
so in ``trail_coverage()['note']`` (the verdict is then ``partial``).

The event id is stable per (session, payload fingerprint) so a re-read of the
same store does not multiply rows: the OSS store dedupes ``events`` on id and
bumps ``session_context.turns`` for a recurring fingerprint.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from clawmetry.adapters.base import Capability, Event

EVENT_TYPE = "context.compiled"

# ``Capability.INPUTS`` only exists on OSS wheels that carry the Trail seam.
# ``None`` on an older wheel: adapters add it to capabilities() only when set.
CAP_INPUTS = getattr(Capability, "INPUTS", None)
CAP_REASONING = getattr(Capability, "REASONING", None)


def _clean_meta(meta: dict | None) -> dict:
    out: dict = {}
    for k, v in (meta or {}).items():
        if v is None or v == "" or v == [] or v == {}:
            continue
        out[str(k)] = v
    return out


def _clean_tools(tools: Iterable | None) -> list:
    out: list = []
    seen: set = set()
    for t in tools or ():
        if isinstance(t, str):
            n = t.strip()
            if n and n not in seen:
                seen.add(n)
                out.append(n)
        elif isinstance(t, dict):
            n = str(t.get("name") or "").strip()
            if n and n not in seen:
                seen.add(n)
                out.append(t)
    return out


def context_event(
    agent: str,
    session_id: str,
    ts: float,
    *,
    system_prompt: str | None = None,
    prompt: str | None = None,
    tools: Iterable | None = None,
    runtime_meta: dict | None = None,
    source: str = "",
) -> Event | None:
    """Build the ``context.compiled`` Event, or ``None`` when there is nothing
    to say. ``source`` names the native field(s) the payload came from and
    rides in ``extra.source`` so a reader can trace each fact to disk."""
    payload: dict[str, Any] = {}
    if isinstance(system_prompt, str) and system_prompt.strip():
        payload["systemPrompt"] = system_prompt
    if isinstance(prompt, str) and prompt.strip():
        payload["prompt"] = prompt
    clean_tools = _clean_tools(tools)
    if clean_tools:
        payload["tools"] = clean_tools
    meta = _clean_meta(runtime_meta)
    if meta:
        payload["runtimeMeta"] = meta
    if not payload:
        return None
    fp = hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8", "ignore")
    ).hexdigest()[:16]
    if source:
        payload["source"] = source
    try:
        ts_f = float(ts or 0.0)
    except (TypeError, ValueError):
        ts_f = 0.0
    return Event(
        agent=agent,
        session_id=session_id,
        id=f"ctx:{session_id}:{fp}",
        type=EVENT_TYPE,
        ts=ts_f,
        role="",
        content="",
        extra=payload,
    )


def prepend_context(events: list[Event], ctx: Event | None) -> list[Event]:
    """Put the context event first, stamped no later than the first event so
    the timeline reads 'given this, then it did that'. Returns ``events``
    unchanged when ``ctx`` is None."""
    if ctx is None:
        return events
    if events:
        try:
            first_ts = min(float(getattr(e, "ts", 0) or 0) for e in events if getattr(e, "ts", 0))
        except ValueError:
            first_ts = 0.0
        if first_ts and (not ctx.ts or ctx.ts > first_ts):
            ctx.ts = first_ts
    return [ctx] + list(events)


def with_inputs(caps: set) -> set:
    """Add ``Capability.INPUTS`` to a capability set when the OSS wheel has it."""
    if CAP_INPUTS is not None:
        caps.add(CAP_INPUTS)
    return caps
