"""`clawmetry sessions` — list sessions; drill into one with facets.

    clawmetry sessions [--active] [--runtime R] [--limit N] [--json]
    clawmetry sessions <SID> [--transcript|--cost|--errors|--lineage|--journey|--export {json,md}]

Read-only. Backed by the daemon-proxy store methods the Sessions tab uses:
query_sessions_table, query_events, query_cost_split_with_subagents,
query_session_errors, query_session_lineage,
query_session_model_journey_with_subagents.
"""
from __future__ import annotations

from clawmetry.cli_cmds import _common as c


def register(sub) -> None:
    p = sub.add_parser(
        "sessions",
        help="List agent sessions, or inspect one (transcript, cost, errors, lineage)",
    )
    p.add_argument("session_id", nargs="?", metavar="SID",
                   help="Session id (or unique prefix) to inspect")
    p.add_argument("--active", action="store_true",
                   help="Only sessions currently marked active")
    c.add_runtime_flag(p)
    p.add_argument("--limit", type=int, default=50,
                   help="Max rows (default 50, max 1000)")
    c.add_window_flags(p)
    # Facets (pure reads; mutually exclusive with each other).
    facet = p.add_mutually_exclusive_group()
    facet.add_argument("--transcript", action="store_true",
                       help="Event-level transcript of the session")
    facet.add_argument("--cost", action="store_true",
                       help="Cost split incl. sub-agents")
    facet.add_argument("--errors", action="store_true", help="Error events")
    facet.add_argument("--lineage", action="store_true",
                       help="Sub-agent lineage tree")
    facet.add_argument("--journey", action="store_true",
                       help="Model journey (mid-session model switches)")
    facet.add_argument("--export", choices=["json", "md"],
                       help="Full bundle (summary+transcript+cost+errors) to stdout")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def _runtime_of(row: dict) -> str:
    """Runtime id for a session row — the session-id prefix before ``:`` when
    present, else the adapter's agent_type (mirrors sync._runtime_of_session;
    the sessions table's agent_type says which ADAPTER ingested the row, which
    is 'openclaw' even for claude_code:-prefixed family sessions)."""
    sid = str(row.get("session_id", "") or "")
    if ":" in sid:
        return sid.split(":", 1)[0]
    return str(row.get("agent_type") or "openclaw")


def _load_rows(store, args, limit: int = 1000):
    rows = c.call(store, "query_sessions_table", limit=limit)
    if getattr(args, "runtime", None):
        rows = [r for r in rows if _runtime_of(r) == args.runtime]
    return rows


def _resolve(store, args, sid: str) -> dict:
    rows = _load_rows(store, args)
    exact = [r for r in rows if r.get("session_id") == sid]
    if exact:
        return exact[0]
    prefixed = [r for r in rows if str(r.get("session_id", "")).startswith(sid)]
    if len(prefixed) == 1:
        return prefixed[0]
    if len(prefixed) > 1:
        raise c.CliError(
            "bad_request",
            f"session prefix {sid!r} is ambiguous ({len(prefixed)} matches); "
            "use more characters",
            c.EXIT_USAGE,
        )
    raise c.CliError("not_found", f"no session matching {sid!r}", c.EXIT_NOT_FOUND)


def run(args) -> int:
    store, source = c.get_read_store()
    if args.session_id:
        return _run_detail(store, source, args)
    return _run_list(store, source, args)


def _run_list(store, source, args) -> int:
    limit = max(1, min(int(args.limit or 50), 1000))
    since, _until = c.resolve_window(args)
    rows = _load_rows(store, args, limit=max(limit, 200))
    if args.active:
        rows = [r for r in rows if str(r.get("status", "")).lower() == "active"]
    if since:
        rows = [r for r in rows if str(r.get("last_active_at") or "") >= since]
    rows = rows[:limit]
    if args.as_json:
        c.emit_json({"sessions": rows, "source": source})
        return c.EXIT_OK
    view = [
        {
            "session_id": c.short_sid(str(r.get("session_id", "")), 44),
            "runtime": _runtime_of(r),
            "status": r.get("status"),
            "title": r.get("title"),
            "tokens": c.fmt_tokens(r.get("total_tokens")),
            "cost": c.fmt_cost(r.get("cost_usd")),
            "last_active": str(r.get("last_active_at") or "")[:19],
        }
        for r in rows
    ]
    c.print_table(view, [
        ("session_id", "SESSION", 44),
        ("runtime", "RUNTIME", 12),
        ("status", "STATUS", 8),
        ("tokens", "TOKENS", 8),
        ("cost", "COST", 10),
        ("last_active", "LAST ACTIVE", 19),
        ("title", "TITLE", 40),
    ])
    c.note(f"{len(view)} session(s) · source: {source}")
    return c.EXIT_OK


def _facet_payload(store, args, sid: str) -> tuple[str, object]:
    since, until = c.resolve_window(args)
    if args.transcript:
        return "transcript", c.call(
            store, "query_events",
            session_id=sid, since=since, until=until, limit=2000,
        )
    if args.cost:
        return "cost", c.call(
            store, "query_cost_split_with_subagents", session_id=sid,
        )
    if args.errors:
        return "errors", c.call(
            store, "query_session_errors", session_id=sid, limit=200,
        )
    if args.lineage:
        return "lineage", c.call(
            store, "query_session_lineage", session_id=sid,
        )
    if args.journey:
        return "journey", c.call(
            store, "query_session_model_journey_with_subagents", session_id=sid,
        )
    return "", None


def _run_detail(store, source, args) -> int:
    row = _resolve(store, args, args.session_id)
    sid = row["session_id"]

    if args.export:
        bundle = {
            "session": row,
            "transcript": c.call(store, "query_events", session_id=sid, limit=5000),
            "cost": c.call(store, "query_cost_split_with_subagents", session_id=sid),
            "errors": c.call(store, "query_session_errors", session_id=sid, limit=200),
            "source": source,
        }
        if args.export == "json":
            c.emit_json(bundle)
        else:
            _print_markdown_bundle(bundle)
        return c.EXIT_OK

    facet, payload = _facet_payload(store, args, sid)
    if facet:
        if args.as_json:
            c.emit_json({facet: payload, "session_id": sid, "source": source})
            return c.EXIT_OK
        _print_facet_human(facet, payload)
        c.note(f"session {sid} · source: {source}")
        return c.EXIT_OK

    # Default detail: the session row + cost headline. Human view shows the
    # DERIVED runtime (session-id prefix rule) — agent_type says which
    # adapter ingested the row and stays in --json only, so the detail and
    # list views tell one story.
    if args.as_json:
        c.emit_json({"session": row, "source": source})
        return c.EXIT_OK
    print(f"{'runtime':16} {_runtime_of(row)}")
    for key in ("session_id", "status", "title", "started_at",
                "last_active_at", "ended_at", "message_count"):
        if row.get(key) not in (None, ""):
            print(f"{key:16} {row.get(key)}")
    print(f"{'total_tokens':16} {c.fmt_tokens(row.get('total_tokens'))}")
    print(f"{'cost_usd':16} {c.fmt_cost(row.get('cost_usd'))}")
    c.note("facets: --transcript --cost --errors --lineage --journey --export json|md")
    return c.EXIT_OK


def _event_snippet(ev: dict, width: int = 100) -> str:
    data = ev.get("data")
    if isinstance(data, dict):
        # Family tool_call events: show the tool + its key argument, not the
        # raw envelope dict.
        calls = data.get("tool_calls")
        if isinstance(calls, list) and calls:
            parts = []
            for blk in calls[:3]:
                if not isinstance(blk, dict):
                    continue
                inp = blk.get("input") or {}
                arg = ""
                if isinstance(inp, dict):
                    arg = str(
                        inp.get("file_path") or inp.get("command")
                        or inp.get("path") or inp.get("pattern") or ""
                    )
                parts.append(f"{blk.get('name', 'tool')}({arg})" if arg
                             else str(blk.get("name", "tool")))
            return " ".join(parts)[:width]
        if data.get("tool_name"):
            return str(data["tool_name"])[:width]
        for key in ("text", "content", "message", "error", "tool", "name"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                return v.strip()[:width]
        return str({k: data[k] for k in list(data)[:3]})[:width]
    return str(data or "")[:width]


def _print_facet_human(facet: str, payload) -> None:
    if facet == "transcript":
        events = sorted(payload or [], key=lambda e: str(e.get("ts", "")))
        for ev in events:
            ts = str(ev.get("ts", ""))[:19]
            print(f"{ts}  {str(ev.get('event_type', '') or ''):24} {_event_snippet(ev)}")
        if not events:
            c.note("(no events)")
        return
    if facet == "errors":
        for ev in payload or []:
            ts = str(ev.get("ts", ""))[:19]
            print(f"{ts}  {str(ev.get('event_type', '') or ''):24} {_event_snippet(ev)}")
        if not payload:
            c.note("(no errors)")
        return
    # cost / lineage / journey: structured dicts/lists — render as indented JSON
    # (still data → stdout; these shapes vary too much for a fixed table).
    if payload in ([], {}):
        c.note(f"(no {facet} rows recorded for this session)")
        return
    import json as _json
    print(_json.dumps(payload, indent=2, default=str))


def _print_markdown_bundle(bundle: dict) -> None:
    row = bundle["session"]
    print(f"# Session {row.get('session_id')}")
    print()
    for key in ("agent_type", "status", "title", "started_at", "last_active_at"):
        if row.get(key):
            print(f"- **{key}**: {row.get(key)}")
    print(f"- **total_tokens**: {row.get('total_tokens')}")
    print(f"- **cost_usd**: {row.get('cost_usd')}")
    print()
    print("## Transcript")
    for ev in sorted(bundle.get("transcript") or [], key=lambda e: str(e.get("ts", ""))):
        print(f"- `{str(ev.get('ts', ''))[:19]}` **{ev.get('event_type', '')}** "
              f"{_event_snippet(ev, 200)}")
    errors = bundle.get("errors") or []
    if errors:
        print()
        print("## Errors")
        for ev in errors:
            print(f"- `{str(ev.get('ts', ''))[:19]}` {_event_snippet(ev, 200)}")
