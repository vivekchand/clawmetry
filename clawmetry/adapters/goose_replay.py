"""Replay-event mapper for Goose (#4813, clawmetry-pro#134).

Maps one Goose session out of ``sessions.db`` into the canonical
``clawmetry.replay_schema`` stream the sync daemon writes to the
``replay_events`` table and ``/api/replay-tree/<session_id>`` groups.

What the session store exposes, and what this mapper does with it:

* ``sessions.goose_mode`` is the session's permission mode (``auto``,
  ``approve``, ``smart_approve``, ``chat``). It is one value per session,
  the mode the session last ran in, not a history. It becomes the leading
  ``mode.changed`` event. A database without the column reports
  ``unknown``.
* ``sessions.session_type = 'scheduled'`` or a ``schedule_id`` marks a
  session the cron scheduler started. The mode event then carries
  ``collaboration: "cron"`` and, when ``schedule.json`` names the job, its
  cron expression.
* ``sessions.recipe_json`` is the reusable workflow the session ran. It
  becomes one ``workflow.start`` with the recipe steps in the payload. A
  session without a recipe emits no ``workflow.*`` event.
* ``messages.content_json`` blocks become ``llm.call`` (user text),
  ``llm.response`` (assistant text), ``thinking``, ``tool.call`` and
  ``tool.result``.

Goose has no sub-agent transcripts in this store, so no event carries a
``parent_span_id``. Approval decisions are not stored either, so no
``approval.*`` event is emitted.

Message timestamps are whole seconds and the store orders rows by
``(ts, span_id)``, so every span id embeds the zero-padded message row id
and block index. Rows in the same second then keep transcript order.
"""
from __future__ import annotations

import json
import sqlite3
from typing import Any

_AGENT = "goose"
_TEXT_CAP = 4000
_STEP_CAP = 50

# ``sessions.goose_mode`` -> canonical permission. ``auto`` runs every tool
# without asking; ``approve`` and ``smart_approve`` ask before a tool runs.
# ``chat`` (no tool use) has no canonical equivalent and stays ``unknown``;
# the native value always rides in the payload.
_GOOSE_MODE_MAP = {
    "auto": "yolo",
    "approve": "default",
    "smart_approve": "default",
}


def _cap(text: Any, cap: int = _TEXT_CAP) -> str:
    if not isinstance(text, str):
        return ""
    return text if len(text) <= cap else text[:cap]


def _cap_value(value: Any, cap: int = _TEXT_CAP) -> Any:
    """Keep a JSON value as is when small, else a truncated JSON string."""
    if value is None:
        return None
    try:
        encoded = json.dumps(value, default=str)
    except (TypeError, ValueError):
        return _cap(str(value), cap)
    return value if len(encoded) <= cap else encoded[:cap]


def _names(items: Any, *keys: str) -> list[str]:
    """Names out of a list of strings or dicts, or the keys of a dict."""
    if isinstance(items, dict):
        items = list(items.keys())
    if not isinstance(items, list):
        return []
    out: list[str] = []
    for item in items[:_STEP_CAP]:
        name: Any = item
        if isinstance(item, dict):
            name = next((item.get(k) for k in keys if item.get(k)), None)
        if isinstance(name, str) and name.strip():
            out.append(name.strip()[:200])
    return out


def recipe_payload(recipe_json: Any) -> dict[str, Any] | None:
    """The ``workflow.start`` payload for a ``sessions.recipe_json`` value.

    The recipe shape differs between Goose versions, so every field is
    optional: ``title`` or ``name``; a recipe nested under a ``recipe``
    key; extensions, parameters and sub-recipes as strings or as objects.
    Parameter VALUES are never read (``user_recipe_values_json`` is not
    touched), only the declared keys. Returns ``None`` when the value is
    empty or not a JSON object. Never raises.
    """
    if not recipe_json:
        return None
    try:
        data = (json.loads(recipe_json) if isinstance(recipe_json, str)
                else recipe_json)
    except (TypeError, ValueError):
        return None
    if isinstance(data, dict) and isinstance(data.get("recipe"), dict):
        data = data["recipe"]
    if not isinstance(data, dict) or not data:
        return None
    steps: list[dict[str, str]] = []
    for kind in ("instructions", "prompt"):
        text = data.get(kind)
        if isinstance(text, str) and text.strip():
            steps.append({"kind": kind, "text": _cap(text.strip())})
    for text in _names(data.get("activities"), "text", "name", "title"):
        steps.append({"kind": "activity", "text": text})
    for name in _names(data.get("sub_recipes") or data.get("subRecipes"),
                       "name", "path"):
        steps.append({"kind": "sub_recipe", "name": name})
    title = data.get("title") or data.get("name")
    return {
        "workflow": "recipe",
        "title": _cap(title, 120) if isinstance(title, str) else "",
        "description": _cap(data.get("description"), 400),
        "version": str(data.get("version") or ""),
        "steps": steps[:_STEP_CAP],
        "extensions": _names(data.get("extensions"), "name", "type"),
        "parameters": _names(data.get("parameters"), "key", "name"),
    }


def _mode_event_parts(row: sqlite3.Row, schedule_jobs: dict) -> tuple[dict, dict]:
    """``(mode, payload)`` for the leading ``mode.changed`` event."""
    keys = row.keys()
    raw = row["goose_mode"] if "goose_mode" in keys else None
    raw = raw.strip().lower() if isinstance(raw, str) else ""
    mode: dict[str, Any] = {"permission": _GOOSE_MODE_MAP.get(raw, "unknown")}
    payload: dict[str, Any] = {
        "goose_mode": raw,
        "source": ("sessions.goose_mode" if raw
                   else "this Goose database has no goose_mode column"),
    }
    session_type = row["session_type"] if "session_type" in keys else ""
    schedule_id = row["schedule_id"] if "schedule_id" in keys else None
    if session_type == "scheduled" or schedule_id:
        mode["collaboration"] = "cron"
        payload["trigger"] = "cron"
        if isinstance(schedule_id, str) and schedule_id:
            payload["schedule_id"] = schedule_id
            cron = (schedule_jobs.get(schedule_id) or {}).get("cron")
            if cron:
                payload["cron"] = cron
    return mode, payload


def iter_replay_events(db_path: str, session_id: str, limit: int = 5000):
    """Yield canonical replay events for one Goose session.

    Opens ``sessions.db`` read-only, reads the session row and its
    messages, and closes the connection before the first event is yielded.
    An unknown session, a missing database or a query error yields
    nothing. Never raises.
    """
    from clawmetry.adapters import goose as _g

    try:
        budget = max(0, int(limit))
    except (TypeError, ValueError):
        budget = 5000
    if budget <= 0:
        return
    conn = _g._open_ro(db_path)
    if conn is None:
        return
    try:
        row = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            return
        messages = conn.execute(
            "SELECT id, role, content_json, created_timestamp, tokens "
            "FROM messages WHERE session_id = ? "
            "ORDER BY created_timestamp ASC, id ASC LIMIT ?",
            (session_id, budget),
        ).fetchall()
    except sqlite3.Error as exc:
        _g.logger.warning("Goose replay query failed: %s", exc)
        return
    finally:
        conn.close()

    keys = row.keys()
    prefix = f"{_AGENT}:{session_id}"
    model = _g._model_from_config(
        row["model_config_json"] if "model_config_json" in keys else None,
        row["provider_name"] if "provider_name" in keys else None)
    first_msg_ts = _g._parse_ts(messages[0]["created_timestamp"]) if messages else 0.0
    created = _g._parse_ts(row["created_at"] if "created_at" in keys else None)
    # The header events must not sort after the first message.
    start_ts = min(t for t in (created, first_msg_ts) if t) if (
        created or first_msg_ts) else 0.0

    def mk(kind, span, ts, payload, *, mode=None):
        ev: dict[str, Any] = {
            "ts": ts, "kind": kind, "span_id": f"{prefix}:{span}",
            "parent_span_id": None, "session_id": session_id,
            "runtime": _AGENT, "payload": payload,
        }
        if mode is not None:
            ev["mode"] = mode
        return ev

    def stream():
        try:
            jobs = _g._schedule_jobs(db_path)
        except Exception:
            jobs = {}
        mode, mode_payload = _mode_event_parts(row, jobs)
        yield mk("mode.changed", "0mode", start_ts, mode_payload, mode=mode)
        recipe = recipe_payload(
            row["recipe_json"] if "recipe_json" in keys else None)
        if recipe is not None:
            yield mk("workflow.start", "0recipe", start_ts, recipe)

        for msg in messages:
            role = msg["role"] or ""
            ts = _g._parse_ts(msg["created_timestamp"])
            base = f"m{int(msg['id']):010d}"
            blocks = _g._decode_blocks(msg["content_json"])
            text = _g._text_of_blocks(blocks)
            # The message text goes first so a turn opens before its tools.
            if text and role == "assistant":
                payload: dict[str, Any] = {
                    "role": "assistant", "text": _cap(text), "model": model}
                tokens = _g._int_or_zero(msg["tokens"])
                if tokens:
                    payload["usage"] = {"total_tokens": tokens}
                yield mk("llm.response", f"{base}:a", ts, payload)
            elif text:
                yield mk("llm.call", f"{base}:a", ts,
                         {"role": role or "user", "text": _cap(text)})
            for idx, block in enumerate(blocks):
                btype = block.get("type")
                span = f"{base}:b{idx:03d}"
                call_id = str(block.get("id") or "")
                if btype == "thinking":
                    think = block.get("thinking")
                    if isinstance(think, str) and think.strip():
                        yield mk("thinking", f"{span}:thinking", ts,
                                 {"text": _cap(think), "model": model})
                elif btype == "toolRequest":
                    call = block.get("toolCall")
                    call = call if isinstance(call, dict) else {}
                    value = call.get("value")
                    value = value if isinstance(value, dict) else {}
                    meta = block.get("_meta")
                    meta = meta if isinstance(meta, dict) else {}
                    yield mk("tool.call", f"{span}:call", ts, {
                        "tool": str(value.get("name") or "unknown"),
                        "call_id": call_id,
                        "args": _cap_value(value.get("arguments")),
                        "extension": str(meta.get("goose_extension") or ""),
                    })
                elif btype == "toolResponse":
                    result = block.get("toolResult")
                    result = result if isinstance(result, dict) else {}
                    value = result.get("value")
                    value = value if isinstance(value, dict) else {}
                    yield mk("tool.result", f"{span}:result", ts, {
                        "call_id": call_id,
                        "output": _cap(_g._tool_result_text(result)),
                        "status": str(result.get("status") or ""),
                        "is_error": bool(value.get("isError")),
                    })

    try:
        for ev in stream():
            if budget <= 0:
                return
            budget -= 1
            yield ev
    except Exception as exc:  # a bad row never sinks the replay
        _g.logger.warning("Goose replay of %s stopped: %s", session_id, exc)
