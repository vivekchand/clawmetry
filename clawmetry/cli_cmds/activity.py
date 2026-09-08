"""`clawmetry activity` — the Brain event feed from the terminal.

    clawmetry activity [--type T] [--session SID] [--runtime R] [--since 1h] [--json]
    clawmetry activity --follow [--max-events N] [--idle-timeout S]

History reads come straight off ``query_events`` through the daemon proxy.
``--follow`` POLLS the same method (2 s cadence) and emits NDJSON with
``_meta`` / ``_end`` frames — no dashboard process required, and the stream
never hangs: idle-timeout (default 300 s), optional --max-events, Ctrl-C
exits 0 with a resumable ``next_cursor``.
"""
from __future__ import annotations

import time

from clawmetry.cli_cmds import _common as c

_POLL_SECS = 2.0


def register(sub) -> None:
    p = sub.add_parser(
        "activity",
        help="Recent agent events (reasoning, tool calls, errors); --follow to stream",
    )
    p.add_argument("--type", dest="event_type", metavar="T",
                   help="Filter by event_type (exact match, e.g. tool.call)")
    p.add_argument("--session", dest="session_id", metavar="SID",
                   help="Scope to one session id")
    c.add_runtime_flag(p)
    c.add_window_flags(p, default_since="1h")
    p.add_argument("--limit", type=int, default=100,
                   help="Max events for a history read (default 100, max 1000)")
    p.add_argument("--follow", action="store_true",
                   help="Stream new events as NDJSON (poll-based; Ctrl-C to stop)")
    p.add_argument("--max-events", type=int, default=0, metavar="N",
                   help="With --follow: stop after N events (0 = unlimited)")
    p.add_argument("--idle-timeout", type=int, default=300, metavar="S",
                   help="With --follow: stop after S seconds with no events (default 300)")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def _fetch(store, args, since, until, limit):
    return c.call(
        store, "query_events",
        session_id=args.session_id,
        event_type=args.event_type,
        since=since,
        until=until,
        runtime=args.runtime,
        exclude_daemon=True,
        limit=limit,
    )


def run(args) -> int:
    store, source = c.get_read_store()
    since, until = c.resolve_window(args)
    if args.follow:
        return _follow(store, source, args, since)

    limit = max(1, min(int(args.limit or 100), 1000))
    rows = _fetch(store, args, since, until, limit)
    rows = sorted(rows, key=lambda e: str(e.get("ts", "")))
    if args.as_json:
        c.emit_json({"events": rows, "source": source})
        return c.EXIT_OK
    for ev in rows:
        ts = str(ev.get("ts", ""))[:19]
        sid = c.short_sid(str(ev.get("session_id", "") or ""), 28)
        etype = str(ev.get("event_type", "") or "")
        print(f"{ts}  {etype:26} {sid:28} {_snippet(ev)}")
    if not rows:
        c.note("(no events in window)")
    c.note(f"{len(rows)} event(s) · source: {source}")
    return c.EXIT_OK


def _snippet(ev: dict, width: int = 90) -> str:
    from clawmetry.cli_cmds.sessions import _event_snippet
    return _event_snippet(ev, width)


def _event_key(ev: dict) -> tuple:
    return (str(ev.get("ts", "")), str(ev.get("session_id", "")),
            str(ev.get("event_type", "")))


def _follow(store, source, args, since) -> int:
    cursor = since or c.utcnow_iso()
    max_events = max(0, int(args.max_events or 0))
    idle_timeout = max(1, int(args.idle_timeout or 300))
    scope = {
        "session_id": args.session_id,
        "event_type": args.event_type,
        "runtime": args.runtime,
        "since": cursor,
    }
    c.emit_jsonl({"type": "_meta", "scope": scope, "source": source})

    emitted = 0
    last_seen_keys: set = set()
    last_event_wall = time.time()
    reason = "idle_timeout"
    try:
        while True:
            rows = _fetch(store, args, cursor, None, 500)
            rows = sorted(rows, key=lambda e: str(e.get("ts", "")))
            fresh = [e for e in rows if _event_key(e) not in last_seen_keys]
            for ev in fresh:
                c.emit_jsonl(ev)
                emitted += 1
                if max_events and emitted >= max_events:
                    reason = "max_events"
                    cursor = str(ev.get("ts") or cursor)
                    raise _Stop
            if fresh:
                last_event_wall = time.time()
                cursor = str(fresh[-1].get("ts") or cursor)
                # `since` comparisons are inclusive at second precision —
                # remember what we already emitted at the cursor timestamp
                # so the next poll doesn't duplicate it.
                last_seen_keys = {
                    _event_key(e) for e in fresh
                    if str(e.get("ts", "")) == cursor
                }
            if time.time() - last_event_wall > idle_timeout:
                reason = "idle_timeout"
                break
            time.sleep(_POLL_SECS)
    except _Stop:
        pass
    except KeyboardInterrupt:
        reason = "interrupted"
    c.emit_jsonl({"type": "_end", "reason": reason, "events": emitted,
                  "next_cursor": cursor})
    return c.EXIT_OK


class _Stop(Exception):
    pass
