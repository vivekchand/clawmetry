"""Measure what ClawMetry actually costs — on your agent, and on your machine.

Run it yourself
---------------
    python -m benchmarks.overhead              # full run, ~60s
    python -m benchmarks.overhead --quick      # ~15s
    python -m benchmarks.overhead --json out.json

No arguments, no config, no network. Everything runs against a loopback
HTTP stub and a throwaway DuckDB in a temp dir, so the numbers are ClawMetry's
own cost and not your provider's latency or your disk's mood.

Why the split matters
---------------------
"Instrumentation overhead" is one phrase covering two very different
questions, and conflating them is how benchmarks become vibes:

  **Agent path** — latency added to the agent's own critical path. This is
  the number that decides whether observability changes your agent's
  behaviour. On ClawMetry's default path it is *structurally* zero: the
  collector is a separate daemon process that tails session files the runtime
  was already writing. There is no ClawMetry code in the agent's process, no
  wrapper around its model calls, no sidecar in its request path. Zero here is
  an architectural claim, not a measurement — so this harness measures the
  paths where we *are* in the loop, which are the opt-in ones.

  **Host cost** — CPU, memory and disk the daemon consumes while ingesting.
  This is real and non-zero, and it is what actually shows up in `top`.

Reporting both, separately, with distributions rather than means, is the
whole point. A p50 hides exactly the tail that makes instrumentation
unacceptable in practice.

What is measured
----------------
  1. ``interceptor``  — added latency per LLM call when the HTTP interceptor
                        is active (opt-in: ``CLAWMETRY_INTERCEPT=1``). Patched
                        vs unpatched ``requests`` against a loopback stub.
  2. ``ingest``       — sustained events/sec into DuckDB, plus bytes on disk
                        per event.
  3. ``query``        — latency of the context-blowout read path over a
                        realistic corpus. This is a dashboard cost, paid by
                        whoever is looking at the page, never by the agent.
  4. ``host``         — peak RSS and CPU seconds for the ingest work.

Every timing reports p50 / p95 / p99 over N samples after a warmup, and the
run stamps the machine it was taken on. An unattributed benchmark number is
not evidence.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import statistics
import sys
import tempfile
import time
import uuid
from typing import Any, Callable

# Keep the package importable when run straight from a checkout.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── stats ────────────────────────────────────────────────────────────────

def _pct(values: list[float], p: float) -> float:
    """Nearest-rank percentile. Small-N safe (statistics.quantiles needs 2+
    points and interpolates, which over-smooths a 20-sample tail)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, int(round(p / 100.0 * len(ordered) + 0.5)) - 1))
    return ordered[idx]


def _summarise(samples_s: list[float]) -> dict[str, Any]:
    """Seconds -> a microsecond distribution. We report the spread because a
    mean alone cannot tell a steady 40µs tax from a 5µs tax with a 3ms GC
    stall in it, and only the second one breaks an agent."""
    us = [s * 1_000_000 for s in samples_s]
    return {
        "n": len(us),
        "p50_us": round(_pct(us, 50), 2),
        "p95_us": round(_pct(us, 95), 2),
        "p99_us": round(_pct(us, 99), 2),
        "min_us": round(min(us), 2) if us else 0.0,
        "max_us": round(max(us), 2) if us else 0.0,
        "stdev_us": round(statistics.pstdev(us), 2) if len(us) > 1 else 0.0,
    }


def _time_many(fn: Callable[[], Any], n: int, warmup: int) -> list[float]:
    """Time ``fn`` n times after ``warmup`` untimed calls. perf_counter is
    monotonic and the highest resolution clock available."""
    for _ in range(warmup):
        fn()
    out: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        out.append(time.perf_counter() - t0)
    return out


# ── machine provenance ───────────────────────────────────────────────────

def machine_spec() -> dict[str, Any]:
    """Stamp the machine. Numbers without a machine are not reproducible."""
    spec: dict[str, Any] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor() or platform.machine(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count(),
    }
    # A real CPU model name beats uname's vague answer where we can get one.
    try:
        if sys.platform == "darwin":
            import subprocess
            spec["processor"] = subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True, timeout=5,
            ).strip()
        elif sys.platform.startswith("linux"):
            with open("/proc/cpuinfo") as fh:
                for line in fh:
                    if line.lower().startswith("model name"):
                        spec["processor"] = line.split(":", 1)[1].strip()
                        break
    except Exception:
        pass  # provenance is nice-to-have; never fail a run over it
    try:
        import duckdb  # noqa: F401
        spec["duckdb"] = duckdb.__version__
    except Exception:
        spec["duckdb"] = None
    return spec


def _rusage() -> dict[str, Any]:
    """Peak RSS (MB) and CPU seconds for this process. POSIX only; Windows
    reports nulls rather than a fabricated figure."""
    try:
        import resource
    except ImportError:
        return {"peak_rss_mb": None, "cpu_user_s": None, "cpu_sys_s": None}
    ru = resource.getrusage(resource.RUSAGE_SELF)
    # ru_maxrss is bytes on macOS, kilobytes on Linux.
    div = 1024 * 1024 if sys.platform == "darwin" else 1024
    return {
        "peak_rss_mb": round(ru.ru_maxrss / div, 1),
        "cpu_user_s": round(ru.ru_utime, 3),
        "cpu_sys_s": round(ru.ru_stime, 3),
    }


# ── 1. interceptor: latency added to the agent's own model call ──────────

def _run_worker(mode: str, n: int, warmup: int, home: str) -> dict[str, list[float]]:
    """One condition, one fresh process. Returns wall and CPU seconds/call."""
    import subprocess
    proc = subprocess.run(
        [sys.executable, "-m", "benchmarks._interceptor_worker",
         "--mode", mode, "--n", str(n), "--warmup", str(warmup), "--out", home],
        capture_output=True, text=True, timeout=600,
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )
    if proc.returncode != 0:
        raise RuntimeError(f"{mode} worker failed: {proc.stderr[-500:]}")
    return json.loads(proc.stdout)


def bench_interceptor(n: int, warmup: int, rounds: int = 3) -> dict[str, Any]:
    """Cost of ClawMetry's HTTP interceptor per LLM call.

    **What is measured.** The same ``requests`` call, with and without
    ``interceptor.activate()``. The transport is a mounted stub adapter that
    returns a canned chat-completions response with no I/O, so the delta is
    exactly the work ClawMetry adds — URL classification, request-body model
    extraction, response-body token extraction, and the JSONL append — and
    not the provider's network latency, which is not ours to report.

    **Method.** Each condition runs in a fresh subprocess (the patch is
    global and irreversible), the parent alternates which goes first per
    round, GC is disabled inside the measured window, and both wall-clock and
    CPU time are recorded. Per-round deltas are reported alongside the pooled
    figure: if rounds disagree on sign, the signal is under this rig's noise
    floor and the harness says so instead of publishing an average.

    **Scope.** This path is **opt-in** (``CLAWMETRY_INTERCEPT=1`` or
    ``import clawmetry.track``). It is the only way ClawMetry enters a Python
    agent's request path. The default file-tailing path runs in a separate
    process and contributes nothing here.
    """
    try:
        import requests  # noqa: F401
    except ImportError:
        return {"skipped": "requests not installed"}

    home = tempfile.mkdtemp(prefix="cm-bench-home-")
    try:
        wall = {"baseline": [], "patched": []}
        cpu = {"baseline": [], "patched": []}
        per_round: list[dict[str, Any]] = []

        for r in range(rounds):
            order = ("baseline", "patched") if r % 2 == 0 else ("patched", "baseline")
            got = {mode: _run_worker(mode, n, warmup, home) for mode in order}
            for mode in ("baseline", "patched"):
                wall[mode].extend(got[mode]["samples_s"])
                cpu[mode].extend(got[mode]["cpu_s"])
            per_round.append({
                "round": r,
                "first": order[0],
                "wall_delta_p50_us": round(
                    _pct([v * 1e6 for v in got["patched"]["samples_s"]], 50)
                    - _pct([v * 1e6 for v in got["baseline"]["samples_s"]], 50), 2),
                "cpu_delta_p50_us": round(
                    _pct([v * 1e6 for v in got["patched"]["cpu_s"]], 50)
                    - _pct([v * 1e6 for v in got["baseline"]["cpu_s"]], 50), 2),
            })

        wb, wp = _summarise(wall["baseline"]), _summarise(wall["patched"])
        cb, cp = _summarise(cpu["baseline"]), _summarise(cpu["patched"])
        deltas = [rd["wall_delta_p50_us"] for rd in per_round]
        consistent = all(d > 0 for d in deltas) or all(d < 0 for d in deltas)

        added_wall = round(wp["p50_us"] - wb["p50_us"], 2)
        return {
            "opt_in": True,
            "env": "CLAWMETRY_INTERCEPT=1",
            "method": (
                f"{rounds} rounds x {n} calls per condition, alternating order, "
                "fresh process per condition, stub transport (no network), GC off"
            ),
            "wall": {"baseline": wb, "instrumented": wp,
                     "added_p50_us": added_wall,
                     "added_p95_us": round(wp["p95_us"] - wb["p95_us"], 2)},
            "cpu": {"baseline": cb, "instrumented": cp,
                    "added_p50_us": round(cp["p50_us"] - cb["p50_us"], 2)},
            # The only comparison that means anything to a user: what share of
            # a REAL model call this is. Expressing it against the stub call
            # instead would inflate it into a scary-looking percentage of a
            # number nobody's agent ever waits on.
            "as_pct_of_real_call": {
                "fast_1s": round(100.0 * added_wall / 1_000_000, 4),
                "typical_5s": round(100.0 * added_wall / 5_000_000, 4),
                "long_30s": round(100.0 * added_wall / 30_000_000, 4),
            },
            "per_round": per_round,
            "rounds_agree_on_sign": consistent,
            "below_noise_floor": not consistent,
        }
    finally:
        shutil.rmtree(home, ignore_errors=True)


# ── 2 + 3. ingest throughput, disk, and the read path ────────────────────

def _event(i: int, session_id: str) -> dict[str, Any]:
    """A v3-shaped assistant turn with a real usage envelope — the shape the
    context-blowout path actually reads. Synthetic shapes that do not match
    production have burned us before, so this mirrors the real one."""
    return {
        "id": f"bench-{i}-{uuid.uuid4().hex[:8]}",
        "node_id": "agent+bench-host",
        "agent_id": "main",
        "session_id": session_id,
        "event_type": "assistant",
        "ts": f"2026-08-25T{(i // 3600) % 24:02d}:{(i // 60) % 60:02d}:{i % 60:02d}.000Z",
        "data": {
            "type": "assistant",
            "version": 3,
            "model": "gpt-5-codex" if i % 2 else "claude-opus-4-7",
            "message": {
                "role": "assistant",
                "model": "gpt-5-codex" if i % 2 else "claude-opus-4-7",
                "usage": {
                    "input_tokens": 4000 + (i % 400) * 300,
                    "output_tokens": 250,
                    "cache_read_input_tokens": 1500,
                    "cache_creation_input_tokens": 300,
                },
                "content": [{"type": "text", "text": "benchmark turn " + "x" * 200}],
            },
        },
    }


def bench_ingest_and_query(events: int, sessions: int, query_n: int) -> dict[str, Any]:
    """Sustained ingest rate, bytes-on-disk per event, and read latency.

    This is **host** cost, not agent cost — it is paid by the daemon process,
    off the agent's critical path.
    """
    tmp = tempfile.mkdtemp(prefix="cm-bench-store-")
    db = os.path.join(tmp, "events.duckdb")
    prev = os.environ.get("CLAWMETRY_LOCAL_STORE_PATH")
    os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = db
    # Default flush cadence — the daemon's own. The timed window below ends
    # with an explicit flush(), so the reported rate includes the durable
    # write rather than measuring an in-memory buffer. Forcing a 10ms flush
    # here instead would understate throughput by a factor the daemon never
    # actually pays.
    try:
        import importlib
        import clawmetry.local_store as ls
        importlib.reload(ls)
        ls.mark_writer_owner()
        store = ls.get_store()

        sids = [f"bench-sess-{i}-{uuid.uuid4().hex[:6]}" for i in range(sessions)]
        batch = [_event(i, sids[i % sessions]) for i in range(events)]

        rss_before = _rusage()
        t0 = time.perf_counter()
        store.ingest_many(batch)
        try:
            store.flush()
        except Exception:
            pass
        elapsed = time.perf_counter() - t0
        rss_after = _rusage()

        # Disk: DuckDB keeps a WAL alongside the main file; count both or the
        # per-event figure understates what the user's disk actually holds.
        on_disk = 0
        for fn in os.listdir(tmp):
            try:
                on_disk += os.path.getsize(os.path.join(tmp, fn))
            except OSError:
                pass

        def read() -> None:
            store.query_context_economics(util_limit=400, compaction_limit=200)

        q = _time_many(read, query_n, warmup=2)

        return {
            "ingest": {
                "events": events,
                "sessions": sessions,
                "elapsed_s": round(elapsed, 3),
                "events_per_sec": int(events / elapsed) if elapsed > 0 else None,
                "us_per_event": round(elapsed / events * 1_000_000, 2) if events else None,
            },
            "disk": {
                "total_bytes": on_disk,
                "bytes_per_event": round(on_disk / events, 1) if events else None,
                "mb_per_100k_events": round(on_disk / events * 100_000 / 1024 / 1024, 1)
                if events else None,
            },
            "query_context_blowout": _summarise(q),
            "host": {
                "peak_rss_mb": rss_after.get("peak_rss_mb"),
                "rss_growth_mb": (
                    round(rss_after["peak_rss_mb"] - rss_before["peak_rss_mb"], 1)
                    if rss_after.get("peak_rss_mb") is not None
                    and rss_before.get("peak_rss_mb") is not None
                    else None
                ),
                "cpu_user_s": rss_after.get("cpu_user_s"),
                "cpu_sys_s": rss_after.get("cpu_sys_s"),
            },
        }
    finally:
        if prev is None:
            os.environ.pop("CLAWMETRY_LOCAL_STORE_PATH", None)
        else:
            os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = prev
        shutil.rmtree(tmp, ignore_errors=True)


# ── report ───────────────────────────────────────────────────────────────

def _render(report: dict[str, Any]) -> str:
    m = report["machine"]
    out: list[str] = []
    out.append("")
    out.append("ClawMetry instrumentation overhead")
    out.append("=" * 60)
    out.append(f"  machine : {m['processor']}")
    out.append(f"  os      : {m['platform']}")
    out.append(f"  python  : {m['python']}   duckdb: {m.get('duckdb') or 'n/a'}")
    out.append(f"  cores   : {m['cpu_count']}")
    out.append("")

    out.append("AGENT PATH — latency added to your agent's own critical path")
    out.append("-" * 60)
    out.append("  default (file tailing)      0 µs   — separate process, no")
    out.append("                                       ClawMetry code in the agent")
    ic = report.get("interceptor") or {}
    if ic.get("skipped"):
        out.append(f"  HTTP interceptor (opt-in)   skipped: {ic['skipped']}")
    elif ic.get("below_noise_floor"):
        spread = [r["wall_delta_p50_us"] for r in (ic.get("per_round") or [])]
        out.append(
            "  HTTP interceptor (opt-in)   below this rig's noise floor "
            f"(per-round deltas {spread} us)"
        )
    else:
        w, c = ic["wall"], ic["cpu"]
        pct = ic["as_pct_of_real_call"]
        out.append(
            f"  HTTP interceptor (opt-in)   +{w['added_p50_us'] / 1000:.2f} ms per call "
            f"(wall p50)   +{c['added_p50_us'] / 1000:.2f} ms CPU"
        )
        out.append(
            f"                              = {pct['typical_5s']:.3f}% of a 5s model call, "
            f"{pct['fast_1s']:.3f}% of a 1s call"
        )
        out.append(
            f"                              baseline {w['baseline']['p50_us'] / 1000:.2f} ms "
            f"-> instrumented {w['instrumented']['p50_us'] / 1000:.2f} ms "
            f"(stub transport, no network)"
        )
    out.append("")

    iq = report.get("ingest_query") or {}
    ing, disk, q, host = (
        iq.get("ingest", {}), iq.get("disk", {}),
        iq.get("query_context_blowout", {}), iq.get("host", {}),
    )
    out.append("HOST COST — what the daemon costs your machine, off the agent path")
    out.append("-" * 60)
    if ing:
        out.append(
            f"  ingest        {ing['events_per_sec']:,} events/sec "
            f"({ing['us_per_event']} µs/event, {ing['events']:,} events)"
        )
    if disk:
        out.append(
            f"  disk          {disk['bytes_per_event']} bytes/event  "
            f"({disk['mb_per_100k_events']} MB per 100k events)"
        )
    if q:
        out.append(
            f"  blowout query {q['p50_us'] / 1000:.1f} ms p50   "
            f"{q['p95_us'] / 1000:.1f} ms p95   (dashboard read, not agent path)"
        )
    if host.get("peak_rss_mb") is not None:
        out.append(
            f"  memory        {host['peak_rss_mb']} MB peak RSS   "
            f"cpu {host.get('cpu_user_s')}s user / {host.get('cpu_sys_s')}s sys"
        )
    out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__ and __doc__.split("\n")[0])
    ap.add_argument("--quick", action="store_true", help="fewer samples, ~15s")
    ap.add_argument("--json", dest="json_path", help="also write the raw report here")
    args = ap.parse_args()

    # The interceptor measurement needs its own, much larger sample count.
    # Its signal is a few hundred microseconds against a sub-millisecond
    # call, so a handful of samples cannot separate it from scheduler noise —
    # at 40 calls the harness (correctly) refuses to publish a figure at all.
    # These calls have no I/O, so they are cheap to take in bulk.
    icept_n = 2_000 if args.quick else 5_000
    icept_warmup = 200 if args.quick else 500
    icept_rounds = 2 if args.quick else 3
    events = 5_000 if args.quick else 25_000
    query_n = 5 if args.quick else 15

    report: dict[str, Any] = {
        "schema": 1,
        "machine": machine_spec(),
        "config": {
            "interceptor_calls_per_condition": icept_n,
            "interceptor_warmup": icept_warmup,
            "interceptor_rounds": icept_rounds,
            "ingest_events": events,
        },
    }
    report["interceptor"] = bench_interceptor(icept_n, icept_warmup, icept_rounds)
    report["ingest_query"] = bench_ingest_and_query(events, sessions=50, query_n=query_n)

    print(_render(report))
    if args.json_path:
        with open(args.json_path, "w") as fh:
            json.dump(report, fh, indent=2)
        print(f"  raw report -> {args.json_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
