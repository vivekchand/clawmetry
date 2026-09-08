"""`clawmetry progress` — is the agent actually getting anywhere?

    clawmetry progress [SID] [--since 1h] [--json]

Two signals, one command:
  * ``query_forward_progress`` — tokens per state-delta per session. A high
    ratio means burning tokens without producing new state (new tools, new
    files, new outcomes).
  * ``query_recent_loop_signals`` — the proxy's loop detector (repeated
    near-identical calls).

The self-improve hook: an agent that sees its own ratio spike + a loop
signal should stop brute-forcing and change strategy.
"""
from __future__ import annotations

from clawmetry.cli_cmds import _common as c


def register(sub) -> None:
    p = sub.add_parser(
        "progress",
        help="Forward-progress score + loop signals (is the agent spinning?)",
    )
    p.add_argument("session_id", nargs="?", metavar="SID",
                   help="Scope to one session id (or prefix)")
    c.add_window_flags(p, default_since="1h")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def run(args) -> int:
    store, source = c.get_read_store()
    since, until = c.resolve_window(args)

    fp_kwargs = {"since": since, "until": until}
    if args.session_id:
        fp_kwargs["session_id"] = args.session_id
    rows = c.call(store, "query_forward_progress", **fp_kwargs)

    # since window → minutes for the loop-signal store (its native filter).
    since_minutes = 60
    if since:
        try:
            from datetime import datetime
            dt = datetime.strptime(since[:19], "%Y-%m-%dT%H:%M:%S")
            since_minutes = max(1, int((datetime.utcnow() - dt).total_seconds() // 60))
        except ValueError:
            pass
    loops = c.call(store, "query_recent_loop_signals",
                   limit=20, since_minutes=since_minutes)
    if args.session_id:
        loops = [sig for sig in loops
                 if str(sig.get("session_id", "")).startswith(args.session_id)]

    payload = {
        "window_since": since,
        "sessions": rows,
        "loop_signals": loops,
        "source": source,
    }
    if args.as_json:
        c.emit_json(payload)
        return c.EXIT_OK

    view = [
        {
            "session": c.short_sid(str(r.get("session_id", "")), 40),
            "tokens": c.fmt_tokens(r.get("tokens")),
            "deltas": r.get("state_deltas"),
            "ratio": f"{float(r.get('ratio') or 0):,.0f}",
        }
        for r in sorted(rows, key=lambda r: -float(r.get("ratio") or 0))
    ]
    c.print_table(view, [
        ("session", "SESSION", 40),
        ("tokens", "TOKENS", 8),
        ("deltas", "STATE-DELTAS", 12),
        ("ratio", "TOK/DELTA", 10),
    ])
    if not rows:
        c.note("(no sessions with billable tokens in window)")
    if loops:
        print()
        print(f"loop signals ({len(loops)}):")
        for sig in loops:
            print(f"  {c.short_sid(str(sig.get('session_id', '') or '?'), 36)}  "
                  f"{sig.get('pattern') or sig.get('kind') or 'loop'}  "
                  f"count={sig.get('count', '?')}")
    else:
        c.note("no loop signals in window")
    c.note(f"high TOK/DELTA = spinning · window since {since} · source: {source}")
    return c.EXIT_OK
