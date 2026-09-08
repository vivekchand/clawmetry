"""Flow trace assembly for the Harness Engineering tab (REQ-HB-006).

Builds one session's observed path as stations and hops, strictly from
recorded rows: DuckDB event rows plus the session's sub-agent rows. The
assembler never draws an inferred box; a station type appears only when the
events actually support it, and station types the harness does not record
are reported in ``coverage`` using the house vocabulary rather than guessed
into the diagram (Blueprint: "Flow traces are observed, never inferred").

Pure functions; routes/bench.py owns store access.
"""

from __future__ import annotations

import json
import time
from typing import Any

from clawmetry.quality_signals import normalize_events

_MAX_HOPS = 200
_LIVE_WINDOW_SECS = 300


def _num(v: Any, default: float = 0.0) -> float:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return default
    return default if f != f else f


def _epoch_of(v: Any) -> float | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        f = float(v)
        return f / 1000.0 if f > 1e11 else f
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        try:
            return float(v)
        except (TypeError, ValueError):
            return None


def _decode_sub_row(row: dict) -> dict[str, Any]:
    data = row.get("data")
    if isinstance(data, (bytes, bytearray)):
        try:
            data = json.loads(data.decode("utf-8", "replace"))
        except Exception:
            data = {}
    elif isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    if not isinstance(data, dict):
        data = {}
    return {
        "id": row.get("subagent_id") or "",
        "kind": data.get("kind") or "subagent",
        "label": data.get("label") or data.get("displayName") or row.get("task") or "",
        "status": row.get("status") or "",
        "model": data.get("model") or "",
        "cost_usd": round(_num(row.get("cost_usd")), 4),
        "tokens": int(_num(row.get("token_count"))),
        "spawned_at": row.get("spawned_at"),
        "ended_at": row.get("ended_at"),
    }


def build_flow_trace(
    session_row: dict | None,
    event_rows: list[dict] | None,
    subagent_rows: list[dict] | None,
    *,
    runtime: str = "",
    now: float | None = None,
) -> dict[str, Any]:
    """Assemble the station/hop trace for one session."""
    session_row = session_row if isinstance(session_row, dict) else {}
    rows = [r for r in (event_rows or []) if isinstance(r, dict)]
    # The store returns events newest-first; a trace walks oldest-first.
    # Sort here rather than trusting the caller (a reversed input once
    # rendered a reply with negative end-to-end latency).
    rows.sort(key=lambda r: (_epoch_of(r.get("ts")) is None,
                             _epoch_of(r.get("ts")) or 0.0))
    now_ts = time.time() if now is None else now

    hops: list[dict[str, Any]] = []
    models: dict[str, dict[str, Any]] = {}
    tools: dict[str, dict[str, Any]] = {}
    first_user_ts: float | None = None
    last_assistant_ts: float | None = None
    context_pct_last: float | None = None

    for idx, raw in enumerate(rows):
        norm_list = normalize_events([raw])
        if not norm_list:
            continue
        ev = norm_list[0]
        receipt = {"i": idx, "ts": raw.get("ts"), "event_type": raw.get("event_type")}
        model = str(raw.get("model") or "").strip()
        cost = _num(raw.get("cost_usd"))
        tokens = int(_num(raw.get("token_count")))

        if ev.kind == "message" and ev.role == "user" and first_user_ts is None:
            first_user_ts = ev.ts
            hops.append({"type": "origin", "ts": raw.get("ts"), "receipt": receipt})
        if model:
            m = models.setdefault(model, {"model": model, "turns": 0,
                                          "cost_usd": 0.0, "tokens": 0})
            m["turns"] += 1
            m["cost_usd"] += cost
            m["tokens"] += tokens
            hops.append({
                "type": "model_turn", "model": model, "ts": raw.get("ts"),
                "cost_usd": round(cost, 4), "tokens": tokens, "receipt": receipt,
            })
        if ev.kind in ("tool_call", "tool_result") and ev.tool_name:
            t = tools.setdefault(ev.tool_name, {"tool": ev.tool_name, "calls": 0,
                                                "errors": 0, "recovered": 0})
            if ev.kind == "tool_call":
                t["calls"] += 1
            if ev.is_error and not ev.benign_error:
                t["errors"] += 1
            hops.append({
                "type": "tool", "tool": ev.tool_name, "ts": raw.get("ts"),
                "error": bool(ev.is_error and not ev.benign_error),
                "receipt": receipt,
            })
        if ev.kind == "message" and ev.is_assistant:
            last_assistant_ts = ev.ts

    truncated = len(hops) > _MAX_HOPS
    if truncated:
        hops = hops[-_MAX_HOPS:]

    subs = [_decode_sub_row(r) for r in (subagent_rows or []) if isinstance(r, dict)]
    deferred = [s for s in subs if s["kind"] in ("workflow", "cron")]
    spawned = [s for s in subs if s["kind"] not in ("workflow", "cron")]

    stations: list[dict[str, Any]] = []
    if first_user_ts is not None:
        stations.append({"id": "origin", "type": "origin", "state": "observed"})
    stations.append({
        "id": "session", "type": "session", "state": "observed",
        "runtime": runtime,
        "title": session_row.get("title") or "",
        "turns": int(_num(session_row.get("message_count"))),
    })
    for m in models.values():
        m["cost_usd"] = round(m["cost_usd"], 4)
        stations.append({"id": "model:" + m["model"], "type": "model",
                         "state": "observed", **m})
    for t in tools.values():
        stations.append({"id": "tool:" + t["tool"], "type": "tool",
                         "state": "observed", **t})
    for s in spawned:
        stations.append({"id": "subagent:" + s["id"], "type": "subagent",
                         "state": "observed", **s})
    for s in deferred:
        stations.append({"id": "deferred:" + s["id"], "type": "deferred",
                         "state": "observed", **s})
    if last_assistant_ts is not None:
        latency = None
        if first_user_ts is not None and last_assistant_ts >= first_user_ts:
            latency = round(last_assistant_ts - first_user_ts, 1)
        stations.append({"id": "reply", "type": "reply", "state": "observed",
                         "latency_secs": latency})

    # Coverage: station types this trace could not observe. Whether that is
    # "recorded nothing this session" or "the harness cannot record it" is a
    # per-runtime capability question; the tab renders both as fog and shows
    # the note. We only assert what the rows show.
    unobserved = []
    if first_user_ts is None:
        unobserved.append({"type": "origin", "state": "supported_none_seen"})
    if not models:
        unobserved.append({"type": "model", "state": "supported_none_seen"})
    if not tools:
        unobserved.append({"type": "tool", "state": "supported_none_seen"})
    if not subs:
        unobserved.append({"type": "subagent", "state": "supported_none_seen"})
    if not deferred:
        unobserved.append({"type": "deferred", "state": "supported_none_seen"})

    last_active = _epoch_of(session_row.get("last_active_at"))
    status = str(session_row.get("status") or "").lower()
    live = status in ("active", "ongoing", "running") or (
        last_active is not None and (now_ts - last_active) < _LIVE_WINDOW_SECS
    )

    return {
        "schema": 1,
        "session_id": session_row.get("session_id") or (rows[0].get("session_id") if rows else ""),
        "runtime": runtime,
        "live": bool(live),
        "event_count": len(rows),
        "stations": stations,
        "hops": hops,
        "hops_truncated": truncated,
        "unobserved": unobserved,
        "context_pct_last": context_pct_last,
    }
