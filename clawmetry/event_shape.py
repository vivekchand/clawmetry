"""clawmetry/event_shape.py: ONE normalizer for every stored event shape.

Every reader used to carry its own ladder for "who spoke, was it a tool,
which tool, did it fail" (routes/sessions.py, routes/tracing.py,
routes/reasoning.py, routes/turn_anatomy.py), and the four drifted apart:
a Claude Code ``tool_use`` block was a tool span in Tracing, a "model" step
in Turn Anatomy and invisible to Reasoning. This module is the single
answer, used both at ingest (to fill the typed ``events.role`` /
``block_kind`` / ``tool_name`` / ``is_error`` columns) and at read time.

``block_kind`` is deliberately aligned with :mod:`clawmetry.replay_schema`
kinds so a typed event column and a replay event agree on vocabulary:

    replay ``thinking``     -> block_kind ``thinking``
    replay ``tool.call``    -> block_kind ``tool_use``
    replay ``tool.result``  -> block_kind ``tool_result``
    replay ``llm.response`` -> block_kind ``text`` (role assistant)
    replay ``llm.call``     -> block_kind ``text`` (role user)

The remaining kinds are ``system`` (harness context, compaction, errors
the runtime reported about itself) and ``other`` (plumbing: session
markers, heartbeats, model changes).

Shapes covered (each has a test in tests/test_event_shape.py):

* OpenClaw v3 as normalised by ``sync._parse_v3_event`` and the legacy
  trajectory parser: ``prompt.submitted`` (``finalPromptText``),
  ``model.completed`` / ``trace.artifacts`` (``completionText`` /
  ``assistantTexts`` + ``toolMetas``), ``tool.call`` / ``tool.invoked``
  (``name`` / ``input``), ``tool.result`` / ``tool.completed``
  (``output`` / ``result`` / ``is_error``), ``context.compiled``,
  ``compaction``, ``workspace.conflict``, the ``session.*`` markers. The
  content keys may sit on ``data`` directly or under a nested ``data.data``
  (the trajectory envelope); both are read.
* Raw Claude Code transcript rows (``type`` user/assistant with the
  Anthropic message under ``data.message``: ``content`` is a string or a
  list of ``text`` / ``thinking`` / ``tool_use`` / ``tool_result`` blocks).
* The family-adapter row every pro adapter (Codex, Cursor, Gemini CLI,
  Copilot, Goose, ...) writes through ``sync.py``: ``event_type`` in
  {message, tool_call, tool_result, thinking, compaction, error, ...} with
  ``data.role`` / ``data.content`` / ``data.tool_name`` / ``data.tool_calls``
  and the error flag under ``data.extra.isError``.
* Flat Anthropic-style messages (``role`` + ``content`` + ``tool_calls``),
  and the Claude Code native-OTel intake rows (``user_prompt``,
  ``llm_call``, ``api_error``, ``waiting_on_user``).

``classify`` never raises and never fabricates: a shape it cannot place
comes back as ``role ""`` / ``block_kind "other"`` with empty text.
"""
from __future__ import annotations

import json
from typing import Any, Iterable

__all__ = [
    "typed_columns",
    "BLOCK_KINDS",
    "ROLES",
    "classify",
    "split_blocks",
    "first_user_prompt",
    "clean_prompt_text",
    "INTENT_MAX_CHARS",
]

BLOCK_KINDS = ("text", "thinking", "tool_use", "tool_result", "system", "other")
ROLES = ("user", "assistant", "system", "tool", "")

#: ``sessions.intent`` is the FULL first user prompt, but bounded: a pasted
#: log file is not an intent, and the column rides the encrypted cloud slice.
INTENT_MAX_CHARS = 4000

# Pure plumbing: never a turn, never a span. Kept in sync with the reader
# constants (routes/tracing._TRACE_PLUMBING_TYPES, turn_anatomy._PLUMBING_TYPES).
_PLUMBING = frozenset({
    "session.started", "session.ended", "session.created", "session_start",
    "session_end", "model.changed", "model_change", "thinking_level_change",
    "agent.heartbeat", "queue-operation", "custom", "custom_message",
    "permission_mode_changed", "mcp_server_connection", "auth", "attachment",
    "channel.in", "channel.out", "log", "connector.health", "talk.lifecycle",
    "local_store_over_cap", "dive_run", "cwd_change",
})

# Runtime-reported context and markers: not a speaker, but not noise either.
_SYSTEM_TYPES = frozenset({
    "context.compiled", "compaction", "workspace.conflict", "api_error",
    "api_refusal", "tool_decision", "error", "waiting_on_user",
    "assistant_response",
})

# Harness-injected wrappers that can never be a human prompt: the
# "<system-reminder>" / "<command-name>" frames and the resume preamble.
_PROMPT_SKIP_PREFIXES = ("<", "Caveat:")


# ── content helpers ────────────────────────────────────────────────────────

def _s(value: Any) -> str:
    """Best-effort string for a content fragment."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    try:
        return json.dumps(value, default=str)
    except (TypeError, ValueError):
        return str(value)


def _content_text(content: Any) -> str:
    """Join the visible text of a ``content`` field (string or block list).

    Mirrors ``routes/sessions._stringify_content`` for strings and lists of
    ``{type: text}`` blocks; non-text blocks contribute nothing here (they are
    surfaced through ``split_blocks``)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for part in content:
            if isinstance(part, dict):
                ptype = part.get("type")
                if ptype in ("text", "input_text", "output_text"):
                    t = part.get("text")
                    if isinstance(t, str) and t:
                        parts.append(t)
                elif ptype in ("thinking", "tool_use", "tool_result",
                               "redacted_thinking", "image", "document"):
                    continue
                elif "text" in part and isinstance(part.get("text"), str):
                    parts.append(part["text"])
            elif isinstance(part, str):
                parts.append(part)
        return "\n".join(parts)
    if isinstance(content, dict):
        t = content.get("text")
        if isinstance(t, str):
            return t
        return ""
    return _s(content)


def split_blocks(blocks: Any) -> dict[str, Any]:
    """Split an Anthropic-style content block list into its parts.

    Returns ``{text, thinking, thinking_blocks, tool_uses, tool_results}``
    where ``tool_uses`` is ``[{id, name, input}]`` and ``tool_results`` is
    ``[{tool_use_id, content, is_error}]``. A string is one text block.
    Never raises."""
    out: dict[str, Any] = {
        "text": "", "thinking": "", "thinking_blocks": [],
        "tool_uses": [], "tool_results": [],
    }
    if isinstance(blocks, str):
        out["text"] = blocks
        return out
    if not isinstance(blocks, list):
        return out
    texts: list[str] = []
    for b in blocks:
        if isinstance(b, str):
            if b:
                texts.append(b)
            continue
        if not isinstance(b, dict):
            continue
        bt = b.get("type")
        if bt in ("text", "input_text", "output_text"):
            t = b.get("text")
            if t:
                texts.append(t if isinstance(t, str) else _s(t))
        elif bt == "thinking":
            t = b.get("thinking")
            if t:
                out["thinking_blocks"].append(t if isinstance(t, str) else _s(t))
        elif bt == "tool_use":
            out["tool_uses"].append({
                "id": b.get("id") or "",
                "name": b.get("name") or "tool",
                "input": b.get("input") if b.get("input") is not None else {},
            })
        elif bt == "tool_result":
            out["tool_results"].append({
                "tool_use_id": b.get("tool_use_id") or "",
                "content": b.get("content"),
                "is_error": bool(b.get("is_error")),
            })
    out["text"] = "\n".join(texts)
    out["thinking"] = "\n".join(out["thinking_blocks"])
    return out


def _extra(data: dict) -> dict:
    ex = data.get("extra")
    if isinstance(ex, str) and ex:
        try:
            ex = json.loads(ex)
        except (ValueError, TypeError):
            ex = None
    return ex if isinstance(ex, dict) else {}


def _flag(*values: Any) -> bool:
    for v in values:
        if isinstance(v, bool):
            if v:
                return True
        elif isinstance(v, str):
            if v.strip().lower() in ("1", "true", "yes", "error"):
                return True
        elif isinstance(v, (int, float)) and v:
            return True
    return False


def _tool_calls_from(data: dict) -> list[dict]:
    """Family-adapter / OpenAI-style ``tool_calls`` list -> ``[{id,name,input}]``."""
    tcs = data.get("tool_calls") or data.get("tool_use")
    if not isinstance(tcs, list):
        return []
    parent_name = data.get("tool_name") or data.get("toolName") or ""
    out = []
    for tc in tcs:
        if not isinstance(tc, dict):
            continue
        fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
        name = tc.get("name") or fn.get("name") or parent_name or "tool"
        inp = tc.get("input")
        if inp is None:
            inp = tc.get("arguments")
        if inp is None:
            inp = fn.get("arguments")
        out.append({
            "id": tc.get("id") or tc.get("tool_call_id") or tc.get("tool_use_id") or "",
            "name": str(name),
            "input": inp if inp is not None else {},
        })
    return out


def _clean_tool_name(name: Any) -> str:
    n = _s(name).strip()
    if not n:
        return ""
    return n.replace("mcp__openclaw__", "")


def _empty(event_type: str = "") -> dict[str, Any]:
    return {
        "role": "", "block_kind": "other", "tool_name": "", "is_error": False,
        "text": "", "thinking": "", "thinking_blocks": [],
        "tool_uses": [], "tool_results": [], "event_type": event_type,
    }


# ── the classifier ─────────────────────────────────────────────────────────

def classify(event_type: Any, data: Any) -> dict[str, Any]:
    """Normalise one stored event into ``{role, block_kind, tool_name,
    is_error, text, thinking, ...}``.

    ``event_type`` is the stored ``events.event_type`` column; ``data`` is
    the decoded ``events.data`` payload (dict, JSON string or bytes are all
    accepted). Extra keys ``thinking_blocks``, ``tool_uses`` and
    ``tool_results`` carry the structured parts for readers that render each
    block separately (the transcript, the trace).

    Precedence when one event carries several block types (a Claude Code
    assistant turn that thinks, speaks and calls a tool): ``tool_result`` >
    ``tool_use`` > ``text`` > ``thinking``. The typed column records the
    event's most action-like part; the structured lists carry the rest.
    """
    try:
        return _classify(event_type, data)
    except Exception:  # noqa: BLE001 - a classifier bug must never drop a row
        return _empty(_s(event_type))


def _coerce_data(data: Any) -> dict:
    if isinstance(data, (bytes, bytearray)):
        try:
            data = data.decode("utf-8")
        except UnicodeDecodeError:
            return {}
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (ValueError, TypeError):
            return {}
    return data if isinstance(data, dict) else {}


def _classify(event_type: Any, data: Any) -> dict[str, Any]:
    et_raw = _s(event_type).strip()
    et = et_raw.lower()
    d = _coerce_data(data)
    out = _empty(et_raw)

    # The trajectory envelope nests content under ``data.data``; the v3
    # mapper writes both. Read the nested copy first, then the flat one.
    inner = d.get("data") if isinstance(d.get("data"), dict) else {}

    def _get(*keys: str) -> Any:
        for k in keys:
            v = inner.get(k)
            if v not in (None, "", [], {}):
                return v
        for k in keys:
            v = d.get(k)
            if v not in (None, "", [], {}):
                return v
        return None

    # Inner type when the stored row carries a coarse outer type ("brain").
    inner_type = d.get("type") if isinstance(d.get("type"), str) else ""
    it = inner_type.lower()
    if et in ("", "brain", "event") and it:
        et = it

    # ── plumbing ────────────────────────────────────────────────────────
    if et in _PLUMBING or et.startswith("daemon.") or et.startswith("session."):
        return out

    # ── runtime context / markers (role system) ─────────────────────────
    if et in _SYSTEM_TYPES or "compact" in et or et.endswith("error") \
            or et == "api_refusal":
        out["role"] = "system"
        out["block_kind"] = "system"
        if et in ("api_error", "error") or et.endswith("error"):
            out["is_error"] = True
        summary = _get("summary", "message", "error", "reason", "text")
        if isinstance(summary, str):
            out["text"] = summary
        if et == "waiting_on_user":
            out["tool_name"] = _clean_tool_name(_get("tool_name", "toolName", "tool"))
        return out

    # ── OpenClaw v3 / trajectory dotted shapes ──────────────────────────
    if et in ("prompt.submitted", "user_prompt", "prompt"):
        out["role"] = "user"
        out["block_kind"] = "text"
        out["text"] = _content_text(
            _get("finalPromptText", "text", "prompt", "promptText", "content") or ""
        )
        return out

    if et in ("model.completed", "trace.artifacts", "llm_call", "assistant_message"):
        out["role"] = "assistant"
        text = _get("completionText", "text", "assistantText", "content")
        if text is None:
            atexts = _get("assistantTexts")
            if isinstance(atexts, list):
                text = "\n".join(_content_text(a) for a in atexts if a)
            elif isinstance(atexts, str):
                text = atexts
        out["text"] = _content_text(text) if text is not None else ""
        metas = _get("toolMetas")
        if isinstance(metas, list):
            for tm in metas:
                if not isinstance(tm, dict):
                    continue
                inp = tm.get("input")
                if inp is None:
                    inp = tm.get("arguments")
                if inp is None:
                    inp = tm.get("args")
                out["tool_uses"].append({
                    "id": tm.get("id") or tm.get("toolUseId") or "",
                    "name": tm.get("name") or tm.get("tool") or "tool",
                    "input": inp if inp is not None else {},
                })
        # An assistant turn nested as a message (rare, but the v3 mapper
        # keeps ``message`` alongside for some adapters).
        msg = d.get("message") if isinstance(d.get("message"), dict) else None
        if msg is not None:
            parts = split_blocks(msg.get("content"))
            if not out["text"]:
                out["text"] = parts["text"]
            out["thinking"] = parts["thinking"]
            out["thinking_blocks"] = parts["thinking_blocks"]
            out["tool_uses"].extend(parts["tool_uses"])
        if out["tool_uses"] and not out["text"]:
            out["block_kind"] = "tool_use"
            out["tool_name"] = _clean_tool_name(out["tool_uses"][0]["name"])
        elif out["text"] or not out["thinking"]:
            out["block_kind"] = "text"
            if out["tool_uses"]:
                out["tool_name"] = _clean_tool_name(out["tool_uses"][0]["name"])
        else:
            out["block_kind"] = "thinking"
        out["is_error"] = _flag(_get("isError", "is_error"))
        return out

    if et in ("tool.call", "tool.invoked", "tool_call", "tool_use", "tool.use"):
        out["role"] = "assistant"
        out["block_kind"] = "tool_use"
        name = _get("name", "tool", "tool_name", "toolName")
        calls = _tool_calls_from(d)
        if not name and calls:
            name = calls[0]["name"]
        inp = _get("input", "arguments", "args")
        if inp is None and calls:
            inp = calls[0]["input"]
        out["tool_name"] = _clean_tool_name(name)
        if calls:
            out["tool_uses"] = calls
        else:
            out["tool_uses"] = [{
                "id": _get("id", "tool_use_id", "toolUseId") or "",
                "name": _s(name) or "tool",
                "input": inp if inp is not None else {},
            }]
        out["text"] = _content_text(_get("content") or "")
        return out

    if et in ("tool.result", "tool.completed", "tool_result", "tool_use_result",
              "tool.error", "tool_error"):
        out["role"] = "tool"
        out["block_kind"] = "tool_result"
        ex = _extra(d)
        out["tool_name"] = _clean_tool_name(
            _get("name", "tool", "tool_name", "toolName") or ex.get("toolName")
            or ex.get("tool_name") or ""
        )
        result = _get("output", "result", "content")
        out["text"] = _content_text(result) if result is not None else ""
        out["is_error"] = _flag(
            _get("is_error", "isError"), ex.get("isError"), ex.get("is_error"),
            et.endswith("error"),
        )
        if d.get("benign_error") or inner.get("benign_error"):
            out["is_error"] = False
        out["tool_results"] = [{
            "tool_use_id": _get("tool_use_id", "toolUseId") or ex.get("toolUseId")
            or ex.get("tool_use_id") or ex.get("tool_call_id") or "",
            "content": result,
            "is_error": out["is_error"],
        }]
        return out

    # ── Anthropic message (raw Claude Code row or family/flat message) ──
    msg = d.get("message") if isinstance(d.get("message"), dict) else None
    role = ""
    content: Any = None
    if msg is not None:
        role = _s(msg.get("role")).lower()
        content = msg.get("content")
    if not role:
        role = _s(d.get("role")).lower()
    if content is None:
        content = d.get("content")
    if not role and et in ("user", "assistant", "system", "tool", "human", "ai"):
        role = {"human": "user", "ai": "assistant"}.get(et, et)
    if not role and it in ("user", "assistant", "system"):
        role = it
    if role in ("human",):
        role = "user"
    if role in ("ai", "model"):
        role = "assistant"
    if role in ("tool_result", "function"):
        role = "tool"
    if role == "developer":
        role = "system"

    parts = split_blocks(content)
    calls = _tool_calls_from(d)
    if calls:
        parts["tool_uses"].extend(calls)
    ex = _extra(d)

    out["text"] = parts["text"]
    out["thinking"] = parts["thinking"]
    out["thinking_blocks"] = parts["thinking_blocks"]
    out["tool_uses"] = parts["tool_uses"]
    out["tool_results"] = parts["tool_results"]

    explicit_tool = _clean_tool_name(d.get("tool_name") or d.get("toolName") or "")
    is_err = _flag(d.get("isError"), d.get("is_error"), ex.get("isError"),
                   ex.get("is_error"))
    if d.get("benign_error"):
        is_err = False

    if et == "thinking" or (it == "thinking" and not parts["text"]):
        out["role"] = role or "assistant"
        out["block_kind"] = "thinking"
        if not out["thinking"]:
            think = d.get("thinking") if isinstance(d.get("thinking"), str) else parts["text"]
            out["thinking"] = think or ""
            out["thinking_blocks"] = [out["thinking"]] if out["thinking"] else []
            out["text"] = ""
        out["is_error"] = is_err
        return out

    if parts["tool_results"]:
        # A user-role message whose content is tool_result blocks IS the
        # tool speaking (Claude Code writes tool output this way).
        out["role"] = "tool"
        out["block_kind"] = "tool_result"
        out["tool_name"] = explicit_tool
        out["is_error"] = is_err or any(r["is_error"] for r in parts["tool_results"])
        if not out["text"]:
            out["text"] = _content_text(parts["tool_results"][0].get("content"))
        return out

    if role == "tool":
        out["role"] = "tool"
        out["block_kind"] = "tool_result"
        out["tool_name"] = explicit_tool
        out["is_error"] = is_err
        out["tool_results"] = [{
            "tool_use_id": ex.get("toolUseId") or ex.get("tool_use_id")
            or d.get("tool_use_id") or "",
            "content": content,
            "is_error": is_err,
        }]
        return out

    if parts["tool_uses"] and not parts["text"]:
        out["role"] = role or "assistant"
        out["block_kind"] = "tool_use"
        out["tool_name"] = explicit_tool or _clean_tool_name(parts["tool_uses"][0]["name"])
        out["is_error"] = is_err
        return out

    if parts["text"]:
        out["role"] = role or ("assistant" if it in ("assistant",) else "")
        out["block_kind"] = "text"
        out["tool_name"] = explicit_tool or (
            _clean_tool_name(parts["tool_uses"][0]["name"]) if parts["tool_uses"] else ""
        )
        out["is_error"] = is_err
        if out["role"] == "system":
            out["block_kind"] = "system"
        return out

    if parts["thinking"]:
        out["role"] = role or "assistant"
        out["block_kind"] = "thinking"
        out["is_error"] = is_err
        return out

    if role in ("user", "assistant", "system"):
        # A turn with a role but no renderable body (an image-only prompt,
        # an empty assistant stop). Typed, but nothing to show.
        out["role"] = role
        out["block_kind"] = "system" if role == "system" else "text"
        out["tool_name"] = explicit_tool
        out["is_error"] = is_err
        return out

    return out


# ── intent (first user prompt) ────────────────────────────────────────────

def clean_prompt_text(text: Any) -> str:
    """Whitespace-normalised prompt text, or "" when it cannot be a human
    prompt (harness wrappers such as ``<system-reminder>``, the resumed-
    session ``Caveat:`` preamble). Same rule ``session_titles`` applies, so
    the 80-char title and the full intent always come from the same turn."""
    if not isinstance(text, str):
        return ""
    stripped = text.strip()
    if not stripped or stripped.startswith(_PROMPT_SKIP_PREFIXES):
        return ""
    return "\n".join(" ".join(line.split()) for line in stripped.splitlines()).strip()


def first_user_prompt(rows: Iterable[Any], max_chars: int = INTENT_MAX_CHARS) -> str:
    """The full text of the first real user prompt in ``rows``.

    ``rows`` are stored event dicts (``event_type`` + ``data``, oldest first
    or not; the earliest by ``ts`` wins), the raw dicts a transcript batch
    hands the ingester, or adapter ``Event`` objects (``type`` / ``role`` /
    ``content``). Capped at ``max_chars`` with an ellipsis marker. "" when
    no qualifying prompt exists. Never raises."""
    best_ts: Any = None
    best = ""
    try:
        for r in rows:
            et, data, ts = _row_parts(r)
            shape = classify(et, data)
            if shape["role"] != "user" or shape["block_kind"] != "text":
                continue
            text = clean_prompt_text(shape["text"])
            if not text:
                continue
            key = _s(ts)
            if best and best_ts is not None and key and key >= best_ts:
                continue
            best, best_ts = text, key
            if not key:
                break  # unordered input: first hit wins
    except Exception:  # noqa: BLE001
        return best[:max_chars]
    if len(best) > max_chars:
        best = best[: max_chars - 3].rstrip() + "..."
    return best


def _row_parts(r: Any) -> tuple:
    if isinstance(r, dict):
        if "event_type" in r and "data" in r:
            # A stored event row (or the dict the ingester queues).
            return r.get("event_type") or "", r.get("data"), r.get("ts") or ""
        # A raw transcript line: the whole object is the payload.
        return (r.get("type") or r.get("event_type") or ""), r, \
            (r.get("timestamp") or r.get("ts") or "")
    # adapter Event dataclass
    et = getattr(r, "type", "") or "message"
    data = {
        "role": getattr(r, "role", "") or "",
        "content": getattr(r, "content", "") or "",
        "tool_name": getattr(r, "tool_name", "") or "",
    }
    return et, data, getattr(r, "ts", "") or ""


def typed_columns(event_type: Any, data: Any) -> tuple:
    """The four typed ``events`` columns for one row, in insert order:
    ``(role, block_kind, tool_name, is_error)``.

    Called by the store's row builder for EVERY new event row, so a row
    written after schema v15 carries its classification from the moment it
    is inserted; the daemon's bounded back-fill only exists for rows that
    predate v15. ``block_kind`` is never NULL on a stamped row (``other``
    when nothing fits), which is also the marker the back-fill uses to skip
    rows it has already visited.
    """
    shape = classify(event_type, data)
    return (
        shape["role"] or None,
        shape["block_kind"] or "other",
        shape["tool_name"] or None,
        bool(shape["is_error"]),
    )
