"""`clawmetry usage` — token/cost analytics from the terminal.

    clawmetry usage [--since 7d] [--runtime R] [--json]
    clawmetry usage --by model|day|team [--export csv]
    clawmetry usage --efficiency [--days 30]

Backed by the same store methods the Cost/Models tabs read through the
daemon proxy: query_aggregates, query_rollup_model_daily,
query_daily_usage_splits, query_usage_by_team, query_efficiency_rollup
(+ clawmetry.efficiency.build_efficiency_slice for the A-F grade).
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict

from clawmetry.cli_cmds import _common as c


def register(sub) -> None:
    p = sub.add_parser(
        "usage",
        help="Token + cost rollups; --by model|day|team; --efficiency for the A-F grade",
    )
    p.add_argument("--by", choices=["model", "day", "team"],
                   help="Break the rollup down by one dimension")
    p.add_argument("--efficiency", action="store_true",
                   help="Efficiency grade (A-F) + measured savings")
    p.add_argument("--days", type=int, default=30,
                   help="Window for --efficiency / --by team (default 30)")
    c.add_runtime_flag(p)
    c.add_window_flags(p, default_since="7d")
    p.add_argument("--export", choices=["csv"],
                   help="With --by: emit the table as CSV to stdout")
    c.add_output_flags(p)
    p.set_defaults(_handler=run)


def run(args) -> int:
    store, source = c.get_read_store()
    since, until = c.resolve_window(args)

    if args.efficiency:
        return _run_efficiency(store, source, args)
    if args.by == "model":
        return _run_by_model(store, source, args, since, until)
    if args.by == "day":
        return _run_by_day(store, source, args, since, until)
    if args.by == "team":
        return _run_by_team(store, source, args)
    return _run_totals(store, source, args, since, until)


def _run_totals(store, source, args, since, until) -> int:
    days = c.call(store, "query_aggregates",
                  since=since, until=until, runtime=args.runtime)
    total_tokens = sum(int(d.get("token_count") or 0) for d in days)
    total_cost = sum(float(d.get("cost_usd") or 0) for d in days)
    payload = {
        "window_since": since,
        "runtime": args.runtime,
        "total_tokens": total_tokens,
        "total_cost_usd": round(total_cost, 4),
        "daily": days,
        "source": source,
    }
    if args.as_json:
        c.emit_json(payload)
        return c.EXIT_OK
    scope = args.runtime or "all runtimes"
    print(f"tokens   {c.fmt_tokens(total_tokens)}")
    print(f"cost     {c.fmt_cost(total_cost)}")
    print(f"days     {len(days)}")
    c.note(f"scope: {scope} · window since {since} · source: {source}")
    c.note("breakdowns: --by model|day|team · grade: --efficiency")
    return c.EXIT_OK


def _emit_rows(args, rows: list[dict], columns: list[tuple[str, str, int]],
               json_key: str, source: str) -> int:
    if args.export == "csv":
        keys = [k for k, _, _ in columns]
        w = csv.DictWriter(sys.stdout, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k) for k in keys})
        return c.EXIT_OK
    if args.as_json:
        c.emit_json({json_key: rows, "source": source})
        return c.EXIT_OK
    c.print_table(rows, columns)
    c.note(f"{len(rows)} row(s) · source: {source}")
    return c.EXIT_OK


def _run_by_model(store, source, args, since, until) -> int:
    daily = c.call(store, "query_rollup_model_daily",
                   runtime=args.runtime, since=since, until=until, limit=1000)
    agg: dict = defaultdict(lambda: {"tokens": 0, "cost_usd": 0.0, "calls": 0})
    for r in daily:
        key = (r.get("runtime"), r.get("model"))
        b = agg[key]
        b["tokens"] += int(r.get("tokens_in") or 0) + int(r.get("tokens_out") or 0)
        b["cost_usd"] += float(r.get("cost_usd") or 0)
        b["calls"] += int(r.get("calls") or 0)
    rows = [
        {"runtime": rt, "model": m, "tokens": b["tokens"],
         "cost_usd": round(b["cost_usd"], 4), "calls": b["calls"]}
        for (rt, m), b in sorted(agg.items(), key=lambda kv: -kv[1]["cost_usd"])
    ]
    return _emit_rows(args, rows, [
        ("runtime", "RUNTIME", 12),
        ("model", "MODEL", 34),
        ("tokens", "TOKENS", 12),
        ("cost_usd", "COST_USD", 10),
        ("calls", "CALLS", 8),
    ], "by_model", source)


def _run_by_day(store, source, args, since, until) -> int:
    rows = c.call(store, "query_daily_usage_splits",
                  since=since, until=until, runtime=args.runtime)
    if isinstance(rows, dict):
        rows = rows.get("daily") or rows.get("days") or [rows]
    return _emit_rows(args, list(rows), [
        ("date", "DATE", 10),
        ("input_tokens", "INPUT", 12),
        ("output_tokens", "OUTPUT", 12),
        ("cache_read_tokens", "CACHE_READ", 12),
        ("cache_write_tokens", "CACHE_WRITE", 12),
    ], "daily", source)


def _run_by_team(store, source, args) -> int:
    rows = c.call(store, "query_usage_by_team",
                  window_days=max(1, int(args.days or 30)))
    return _emit_rows(args, list(rows), [
        ("team", "TEAM", 24),
        ("tokens", "TOKENS", 12),
        ("cost_usd", "COST_USD", 10),
        ("sessions", "SESSIONS", 8),
    ], "by_team", source)


def _run_efficiency(store, source, args) -> int:
    days = max(1, int(args.days or 30))
    rows = c.call(store, "query_efficiency_rollup", days=days)
    try:
        from clawmetry.efficiency import build_efficiency_slice
        slice_ = build_efficiency_slice(rows, days=days)
    except Exception as exc:
        raise c.CliError("internal", f"efficiency grading failed: {exc}", c.EXIT_ERROR)
    slice_["source"] = source
    if args.as_json:
        c.emit_json(slice_)
        return c.EXIT_OK
    grade = slice_.get("grade") or slice_.get("status") or "?"
    print(f"grade    {grade}")
    for key in ("cache_hit_rate", "cacheHitRate", "measured_savings_usd",
                "measuredSavingsUsd", "potential_savings_usd",
                "potentialSavingsUsd"):
        if key in slice_:
            print(f"{key:24} {slice_[key]}")
    by_rt = slice_.get("byRuntime") or {}
    if by_rt:
        print()
        view = [
            {"runtime": rt, "grade": (v or {}).get("grade") or "-"}
            for rt, v in sorted(by_rt.items())
        ]
        c.print_table(view, [("runtime", "RUNTIME", 14), ("grade", "GRADE", 6)])
    c.note(f"window {days}d · source: {source} · full detail: --json")
    return c.EXIT_OK
