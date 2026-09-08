"""Inputs & context: what the agent was actually given, per session.

Pure helpers that turn one ``context.compiled`` event into ``session_context``
rows. OpenClaw's trajectory recorder emits the event once per model call with
``{systemPrompt, prompt, messages, tools[], providerVisibleTools?, imagesCount,
streamStrategy, transport, transcriptLeafId}`` (the Codex runtime path emits it
with ``systemPrompt = developerInstructions``). Paid adapters emit the same
shape for their runtimes, adding a ``runtimeMeta`` dict for facts the native
store carries (cwd, model, version, permissionMode, mcpServers, contextFiles).

Design:
- Hash ONCE at ingest. The sha256 and byte size are computed over the FULL
  text before capping, so two sessions with the same system prompt share a
  fingerprint and a 300 KB prompt is still identified exactly.
- Content is redacted (``clawmetry.redaction``) and capped at ``CONTENT_CAP``
  before it rests in DuckDB. The cap is on the stored copy only.
- Never invent. A missing field produces no row; ``runtime_meta`` carries only
  what the event said.
- Label the row with the runtime that produced it (``runtime_of_event``). The
  stored ``agent_type`` is what the Inputs panel filters on, so a row labelled
  ``openclaw`` on a Claude Code session reads to the user as "nothing captured".

No runtime-specific code lives here: an adapter that wants its inputs
recorded emits the event; this module does not know which runtime it is.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

CONTENT_CAP = 64 * 1024  # bytes of stored content per row

KIND_SYSTEM_PROMPT = "system_prompt"
KIND_USER_PROMPT = "user_prompt"
KIND_TOOLS = "tools_available"
KIND_MCP = "mcp_servers"
KIND_CONTEXT_FILE = "context_file"
KIND_RUNTIME_META = "runtime_meta"
KINDS = (
    KIND_SYSTEM_PROMPT, KIND_USER_PROMPT, KIND_TOOLS,
    KIND_MCP, KIND_CONTEXT_FILE, KIND_RUNTIME_META,
)

EVENT_TYPE = "context.compiled"

# Keys that identify a context.compiled payload wherever it is nested.
_PAYLOAD_KEYS = ("systemPrompt", "prompt", "tools", "runtimeMeta")
# runtimeMeta keys that get their own rows rather than riding runtime_meta.
_META_SPLIT_KEYS = ("mcpServers", "contextFiles")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest()


def _size(text: str) -> int:
    return len(text.encode("utf-8", "ignore"))


def _redact(text: str) -> str:
    try:
        from clawmetry import redaction as _r
        return _r.redact_text(text)
    except Exception:
        return text


def _cap(text: str) -> str:
    raw = text.encode("utf-8", "ignore")
    if len(raw) <= CONTENT_CAP:
        return text
    return raw[:CONTENT_CAP].decode("utf-8", "ignore")


def _prepare(text: str) -> str:
    """Redact, then cap. Redaction first so a secret straddling the cap is
    still scrubbed rather than half-stored."""
    return _cap(_redact(text))


def _canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _as_dict(v: Any) -> dict:
    if isinstance(v, dict):
        return v
    if isinstance(v, (bytes, bytearray)):
        try:
            v = bytes(v).decode("utf-8", "ignore")
        except Exception:
            return {}
    if isinstance(v, str) and v[:1] in ("{", "["):
        try:
            parsed = json.loads(v)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    return {}


def _prompt_text(prompt: Any) -> str:
    """The user prompt as text. OpenClaw passes a string; some runtimes pass
    content blocks ``[{type:'text', text:...}]``."""
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        parts = []
        for blk in prompt:
            if isinstance(blk, str):
                parts.append(blk)
            elif isinstance(blk, dict):
                t = blk.get("text") or blk.get("content")
                if isinstance(t, str):
                    parts.append(t)
        return "\n".join(p for p in parts if p)
    if isinstance(prompt, dict):
        t = prompt.get("text") or prompt.get("content")
        return t if isinstance(t, str) else ""
    return ""


def _tool_names(tools: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(tools, list):
        return names
    for t in tools:
        n = ""
        if isinstance(t, str):
            n = t.strip()
        elif isinstance(t, dict):
            # OpenClaw: {name, description, parameters}. OpenAI-style
            # wrappers: {type:'function', function:{name,...}}.
            fn = t.get("function") if isinstance(t.get("function"), dict) else {}
            n = str(t.get("name") or fn.get("name") or "").strip()
        if n and n not in names:
            names.append(n)
    return sorted(names)


def find_payload(event: dict[str, Any]) -> dict[str, Any] | None:
    """Locate the ``{systemPrompt, prompt, tools, ...}`` dict inside a store
    shaped event. Three nestings occur in the wild:

    - trajectory sidecar line stored raw: ``data = {type, ts, ..., data: {...}}``
    - family adapter Event: ``data = {role, content, extra: {...}}``
    - a direct emit: ``data = {...}``
    """
    data = _as_dict(event.get("data"))
    for cand in (data, _as_dict(data.get("data")), _as_dict(data.get("extra"))):
        if cand and any(k in cand for k in _PAYLOAD_KEYS):
            return cand
    return None


def runtime_of_event(event: dict[str, Any]) -> str:
    """Which runtime this ``context.compiled`` event belongs to.

    The row this lands on is keyed by ``agent_type``, and the Inputs panel
    asks for it by runtime (``/api/sessions/<id>/context?runtime=claude_code``),
    so a wrong label here is indistinguishable from no data at all.

    Three sources, in descending order of how directly they were stated:

    1. ``event['agent_type']`` -- the OpenClaw trajectory reader sets it.
    2. ``data['_runtime']`` -- the family ingest stamps the adapter's own
       runtime here and sets no ``agent_type`` at all (every family event row
       in ``sync.py`` omits the column, which is why these rows read
       ``openclaw`` for Claude Code, Codex, Cursor... until 2026-09-04).
    3. the session-id prefix (``claude_code:<uuid>``), resolved by the one
       shared seam, ``waste_flags.runtime_from_session_id`` -- the same
       fallback ``detectors._runtime_of`` and the sessions list use.

    Never invents: with none of the three it returns ``openclaw``, the only
    runtime a Free install has.
    """
    declared = str(event.get("agent_type") or "").strip()
    if declared:
        return declared
    data = _as_dict(event.get("data"))
    stamped = str(data.get("_runtime") or "").strip()
    if stamped:
        return stamped
    sid = str(event.get("session_id") or "")
    if ":" in sid:
        try:
            from clawmetry.waste_flags import runtime_from_session_id
            rt = str(runtime_from_session_id(sid) or "").strip()
        except Exception:
            rt = ""
        if rt:
            return rt
    return "openclaw"


def rows_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    """Turn one store-shaped ``context.compiled`` event into session_context
    rows. Returns ``[]`` for anything that is not the event or carries none
    of the known fields. Never raises on bad input."""
    try:
        return _rows_from_event(event)
    except Exception:
        return []


def _rows_from_event(event: dict[str, Any]) -> list[dict[str, Any]]:
    if str(event.get("event_type") or "") != EVENT_TYPE:
        return []
    payload = find_payload(event)
    if payload is None:
        return []
    outer = _as_dict(event.get("data"))
    agent_type = runtime_of_event(event)
    session_id = str(event.get("session_id") or "")
    if not session_id:
        return []
    node_id = str(event.get("node_id") or "")
    ts = str(event.get("ts") or "")
    base = {
        "agent_type": agent_type,
        "session_id": session_id,
        "node_id": node_id,
        "first_ts": ts,
        "last_ts": ts,
        "source": EVENT_TYPE,
    }
    rows: list[dict[str, Any]] = []

    sp = payload.get("systemPrompt")
    if isinstance(sp, str) and sp.strip():
        rows.append(dict(base, kind=KIND_SYSTEM_PROMPT, sha256=_sha(sp),
                         size_bytes=_size(sp), content=_prepare(sp),
                         summary=_canon({"chars": len(sp)})))

    up = _prompt_text(payload.get("prompt"))
    if up.strip():
        rows.append(dict(base, kind=KIND_USER_PROMPT, sha256=_sha(up),
                         size_bytes=_size(up), content=_prepare(up),
                         summary=_canon({"chars": len(up)})))

    tools = payload.get("tools")
    names = _tool_names(tools)
    if names:
        defs = _canon(tools)
        rows.append(dict(base, kind=KIND_TOOLS, sha256=_sha(defs),
                         size_bytes=_size(defs), content=_prepare(defs),
                         summary=_canon(names)))

    meta_in = _as_dict(payload.get("runtimeMeta"))

    mcp = meta_in.get("mcpServers")
    if isinstance(mcp, list) and mcp:
        mcp_names = sorted({
            str(m.get("name") if isinstance(m, dict) else m).strip()
            for m in mcp if (m.get("name") if isinstance(m, dict) else m)
        })
        if mcp_names:
            body = _canon(mcp)
            rows.append(dict(base, kind=KIND_MCP, sha256=_sha(body),
                             size_bytes=_size(body), content=_prepare(body),
                             summary=_canon(mcp_names)))

    cfiles = meta_in.get("contextFiles")
    if isinstance(cfiles, list):
        for cf in cfiles:
            if isinstance(cf, str):
                cf = {"path": cf}
            if not isinstance(cf, dict):
                continue
            path = str(cf.get("path") or "").strip()
            if not path:
                continue
            content = cf.get("content") if isinstance(cf.get("content"), str) else None
            sha = str(cf.get("sha256") or (_sha(content) if content else _sha(path)))
            size = int(cf.get("size_bytes") or (_size(content) if content else 0))
            rows.append(dict(base, kind=KIND_CONTEXT_FILE, sha256=sha,
                             size_bytes=size,
                             content=_prepare(content) if content else None,
                             summary=path))

    meta: dict[str, Any] = {}
    for k in ("transport", "streamStrategy", "imagesCount", "transcriptLeafId"):
        if payload.get(k) not in (None, ""):
            meta[k] = payload.get(k)
    msgs = payload.get("messages")
    if isinstance(msgs, list):
        meta["messages_count"] = len(msgs)
    elif isinstance(payload.get("messagesCount"), int):
        meta["messages_count"] = payload["messagesCount"]
    if names:
        meta["tools_count"] = len(names)
    pvt = payload.get("providerVisibleTools")
    if isinstance(pvt, list):
        meta["provider_visible_tools_count"] = len(pvt)
    model = (
        payload.get("model") or meta_in.get("model")
        or outer.get("modelId") or event.get("model") or ""
    )
    if model:
        meta["model"] = str(model)
    provider = meta_in.get("provider") or outer.get("provider")
    if provider:
        meta["provider"] = str(provider)
    cwd = meta_in.get("cwd") or outer.get("workspaceDir")
    if cwd:
        meta["cwd"] = str(cwd)
    for k, v in meta_in.items():
        if k in _META_SPLIT_KEYS or k in ("model", "provider", "cwd"):
            continue
        if v in (None, "", [], {}):
            continue
        meta[k] = v
    if meta:
        body = _canon(meta)
        rows.append(dict(base, kind=KIND_RUNTIME_META, sha256=_sha(body),
                         size_bytes=_size(body), content=None, summary=body))
    return rows


def compact_raw_event_data(data: Any) -> Any:
    """Shrink a raw ``context.compiled`` payload before it rests in ``events``.

    The event carries the WHOLE conversation (``messages``) on every turn,
    which is already in the transcript; storing it again per turn is how a
    store gets to gigabytes (heartbeat rows did exactly this, #5434). The
    fingerprinted copies of the prompt and tool definitions live in
    ``session_context``; here the long fields are capped to ``CONTENT_CAP``
    and ``messages`` is replaced by its count. Non-dict input is returned
    unchanged."""
    if not isinstance(data, dict):
        return data
    out = dict(data)
    inner_key = None
    inner = out
    for nk in ("data", "extra"):
        if isinstance(out.get(nk), dict) and any(k in out[nk] for k in _PAYLOAD_KEYS):
            inner_key = nk
            inner = dict(out[nk])
            break
    if isinstance(inner.get("messages"), list):
        inner["messagesCount"] = len(inner["messages"])
        del inner["messages"]
    for k in ("systemPrompt", "prompt"):
        v = inner.get(k)
        if isinstance(v, str) and _size(v) > CONTENT_CAP:
            inner[k] = _cap(v)
            inner[k + "Truncated"] = True
    tools = inner.get("tools")
    if isinstance(tools, list) and _size(_canon(tools)) > CONTENT_CAP:
        inner["tools"] = _tool_names(tools)
        inner["toolsDefinitionsTruncated"] = True
    if inner_key:
        out[inner_key] = inner
        return out
    return inner
