"""`clawmetry waste` — the re-read tax, from the terminal.

    clawmetry waste [--session SID] [--since 7d] [--json]

Aggregates ``query_recent_read_tool_calls`` rows (one per Read-tool
invocation: {ts, session_id, file_path}) into the number an agent can act
on mid-task: which files it read more than once, per session. A file read
14 times is context the agent already paid for 13 times.
"""
from __future__ import annotations

from collections import Counter

from clawmetry.cli_cmds import _common as c


def register(sub) -> None:
    p = sub.add_parser(
        "waste",
        help="Re-read tax: files read repeatedly in the same session",
    )
    p.add_argument("--session", dest="session_id", metavar="SID",
                   help="Scope to one session id (or unique prefix)")
    c.add_window_flags(p, default_since="7d")
    p.add_argument("--top", type=int, default=15,
                   help="Show the N worst offenders (default 15)")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def run(args) -> int:
    store, source = c.get_read_store()
    since, _until = c.resolve_window(args)
    rows = c.call(store, "query_recent_read_tool_calls", since=since, limit=50_000)

    sid_filter = args.session_id
    if sid_filter:
        rows = [r for r in rows
                if str(r.get("session_id", "")).startswith(sid_filter)]

    per_pair: Counter = Counter()
    for r in rows:
        fp = r.get("file_path")
        sid = r.get("session_id")
        if fp and sid:
            per_pair[(sid, fp)] += 1

    rereads = [
        {"session_id": sid, "file_path": fp, "reads": n, "wasted_reads": n - 1}
        for (sid, fp), n in per_pair.items() if n > 1
    ]
    rereads.sort(key=lambda r: -r["wasted_reads"])
    total_reads = sum(per_pair.values())
    wasted = sum(r["wasted_reads"] for r in rereads)
    summary = {
        "window_since": since,
        "total_reads": total_reads,
        "wasted_reads": wasted,
        "reread_ratio": round(wasted / total_reads, 3) if total_reads else 0.0,
        "files_reread": len(rereads),
        "sessions_affected": len({r["session_id"] for r in rereads}),
        "top": rereads[: max(1, int(args.top or 15))],
        "source": source,
    }
    if args.as_json:
        c.emit_json(summary)
        return c.EXIT_OK

    print(f"reads          {total_reads}")
    print(f"wasted reads   {wasted}  (same file re-read in the same session)")
    print(f"reread ratio   {summary['reread_ratio']:.0%}" if total_reads else "reread ratio   0%")
    print(f"files reread   {summary['files_reread']}")
    print()
    view = [
        {
            "reads": r["reads"],
            "session": c.short_sid(str(r["session_id"]), 30),
            "file": r["file_path"],
        }
        for r in summary["top"]
    ]
    c.print_table(view, [
        ("reads", "READS", 6),
        ("session", "SESSION", 30),
        ("file", "FILE", 80),
    ])
    c.note(f"window since {since} · source: {source}")
    if wasted:
        c.note("tip: read a file once, keep notes; use offset-ranged reads for big files")
    return c.EXIT_OK
