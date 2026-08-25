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
import re
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
        cpu_resolutions: list[float] = []
        per_round: list[dict[str, Any]] = []

        for r in range(rounds):
            order = ("baseline", "patched") if r % 2 == 0 else ("patched", "baseline")
            got = {mode: _run_worker(mode, n, warmup, home) for mode in order}
            for _m in order:
                _res = got[_m].get("cpu_clock_resolution_s")
                if _res:
                    cpu_resolutions.append(float(_res))
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
        # A CPU delta smaller than the clock that measured it is not a
        # measurement. Windows' process_time() advances only every ~15.6ms
        # against a per-call cost near 0.4ms, so nearly every sample reads
        # exactly zero and the raw answer is a confident 0.00ms: a free lunch
        # that does not exist.
        #
        # Do NOT trust the clock's ADVERTISED resolution for this.
        # ``time.get_clock_info("process_time").resolution`` reports 1e-07 on
        # Windows because the underlying counter is denominated in 100ns
        # units, while the value it returns only actually changes on a
        # scheduler tick five orders of magnitude coarser. Guarding on the
        # advertised figure passed the check and published the zero anyway
        # (caught on the Windows CI leg, by this harness, after the "fix").
        #
        # So measure the granularity instead of asking for it: if most
        # individual samples came back as exactly zero, the clock did not
        # resolve a single call and no amount of averaging makes it so.
        cpu_res_us = max(cpu_resolutions or [0.0]) * 1_000_000
        _all_cpu = cpu["baseline"] + cpu["patched"]
        zero_frac = (sum(1 for v in _all_cpu if v <= 0.0) / len(_all_cpu)) if _all_cpu else 1.0
        cpu_added = round(cp["p50_us"] - cb["p50_us"], 2)
        cpu_resolvable = zero_frac < 0.5
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
            "cpu": {
                "baseline": cb, "instrumented": cp,
                "added_p50_us": cpu_added if cpu_resolvable else None,
                "clock_resolution_us": round(cpu_res_us, 2),
                "zero_sample_fraction": round(zero_frac, 4),
                "resolvable": cpu_resolvable,
            },
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


# ── 1b. pre-tool hook gates: the other path that IS on the agent's ───────
#         critical path, and the only one that can hold a tool call.

_HOOK_EVENT = json.dumps({
    "session_id": "overhead-bench",
    "hook_event_name": "PreToolUse",
    "tool_name": "Bash",
    "tool_input": {"command": "ls -la /tmp"},
    "cwd": "/tmp",
})

# A policy that cannot match the Bash/ls event above, so the gate runs the
# full compile + match and then declines. This is the "cheap miss" the fast
# path was built for and the case a real user hits on almost every call.
_MISS_POLICY = {
    "name": "overhead-bench-miss",
    "enabled": True,
    "tool": "WebFetch",
    "action": "ask",
}


def _hook_home(tmp: str, *, api_key: str | None, policies: list | None) -> str:
    """Build an isolated HOME for one gate condition.

    HOME, not CLAWMETRY_HOME: the gate resolves its config as
    ``os.path.expanduser("~/.clawmetry/config.json")`` and does not consult
    CLAWMETRY_HOME, so only a home override actually isolates a run. Getting
    this wrong reads the operator's real key and silently benchmarks a
    different branch than the one you meant (it did, first time).

    The caller must set USERPROFILE as well as HOME, because that is the
    variable ``expanduser`` reads on Windows; setting only HOME there would
    quietly fall through to the real profile again.
    """
    home = os.path.join(tmp, uuid.uuid4().hex[:8])
    cm = os.path.join(home, ".clawmetry")
    os.makedirs(cm, exist_ok=True)
    if api_key:
        with open(os.path.join(cm, "config.json"), "w") as fh:
            json.dump({"api_key": api_key, "node_id": "bench-node"}, fh)
    if policies is not None:
        # A cache file younger than the 60s TTL keeps the gate off the
        # network, which is what a warm steady state looks like.
        with open(os.path.join(cm, "hooks_policy_cache.json"), "w") as fh:
            json.dump({"policies": policies}, fh)
    return home


def _time_subprocess(argv: list[str], env: dict, stdin: str,
                     n: int, warmup: int) -> list[float]:
    """Wall time of a full process launch, which is what the agent waits on."""
    import subprocess
    for _ in range(warmup):
        subprocess.run(argv, input=stdin, env=env, capture_output=True, text=True)
    out: list[float] = []
    for _ in range(n):
        t0 = time.perf_counter()
        subprocess.run(argv, input=stdin, env=env, capture_output=True, text=True)
        out.append(time.perf_counter() - t0)
    return out


def bench_hook_gate(n: int, warmup: int) -> dict[str, Any]:
    """Cost of a pre-tool gate, per gated tool call.

    Where a runtime exposes a ``PreToolUse``-style hook, ClawMetry can hold a
    tool call before it runs. Unlike the interceptor this is not optional
    plumbing a Python agent opts into: it is a process the runtime spawns and
    **waits for**, on every matching tool call, before the tool executes. It
    is therefore the most consequential number on this page.

    Reported against a bare-interpreter floor, because most of a
    process-per-call hook is Python starting up and that cost belongs to the
    mechanism rather than to us. The delta over the floor is our contribution
    and the only part we can do anything about.

    Three conditions, all measured with an isolated HOME:

      ``no_key``      no cloud approver configured. The gate reads one file,
                      finds nothing to do and returns. Today's OSS-local
                      posture, and the cheapest real path.
      ``warm_cache``  a key and a fresh on-disk policy cache. No network.
      ``policy_miss`` same, plus a policy that compiles and then does not
                      match. The "cheap miss" the fast path exists for.

      ``cold_cache``  the policy cache has passed its 60s TTL, so the gate
                      fetches policies from the cloud **inline, on the
                      critical path**, before the tool runs. Reported
                      separately and never folded into a headline per-call
                      average, because it is substantially a measure of the
                      operator's network: roughly one tool call per minute
                      pays it, and on a slow link or a cloud outage it is
                      bounded by a timeout rather than by anything here.
    """
    tmp = tempfile.mkdtemp(prefix="cm-bench-hook-")
    try:
        base_env = {k: v for k, v in os.environ.items()
                    if k not in ("CLAWMETRY_API_KEY", "CLAWMETRY_NODE_ID")}
        repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        base_env["PYTHONPATH"] = repo

        # The floor: an interpreter that does nothing. Anything a
        # process-per-call hook costs starts here.
        floor = _time_subprocess([sys.executable, "-c", "pass"], base_env, "", n, warmup)

        conditions = {
            "no_key": _hook_home(tmp, api_key=None, policies=None),
            "warm_cache": _hook_home(tmp, api_key="cm_bench_offline", policies=[]),
            "policy_miss": _hook_home(tmp, api_key="cm_bench_offline",
                                      policies=[_MISS_POLICY]),
            # No cache file at all -> stale by definition -> inline fetch.
            "cold_cache": _hook_home(tmp, api_key="cm_bench_offline",
                                     policies=None),
        }
        argv = [sys.executable, "-m", "clawmetry", "hooks", "run", "pretooluse"]
        out: dict[str, Any] = {
            "on_critical_path": True,
            "floor_bare_interpreter": _summarise(floor),
            "conditions": {},
        }
        floor_p50 = _summarise(floor)["p50_us"]
        for name, home in conditions.items():
            # HOMEDRIVE/HOMEPATH are cleared so they cannot win over
            # USERPROFILE in expanduser's Windows lookup order.
            env = dict(base_env, HOME=home, USERPROFILE=home)
            env.pop("HOMEDRIVE", None)
            env.pop("HOMEPATH", None)
            samples = _time_subprocess(argv, env, _HOOK_EVENT, n, warmup)
            summ = _summarise(samples)
            out["conditions"][name] = {
                **summ,
                "added_over_floor_p50_us": round(summ["p50_us"] - floor_p50, 2),
                # Flag the one condition whose number is mostly not ours, so
                # no reader (and no renderer) can quote it as a per-call cost.
                "network_dependent": name == "cold_cache",
            }
        return out
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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


# ── 3b. the enforcement proxy: an in-path hop for budgets and routing ────

_UPSTREAM_BODY = json.dumps({
    "id": "msg_bench", "type": "message", "role": "assistant",
    "model": "claude-opus-4-7",
    "content": [{"type": "text", "text": "ok"}],
    "usage": {"input_tokens": 1200, "output_tokens": 40},
}).encode()


def _serve_upstream() -> tuple[Any, str]:
    """A loopback stand-in for the model provider, keep-alive and NODELAY on."""
    import socket
    import threading
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

    class _Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"   # keep-alive; see the note in the worker

        def setup(self) -> None:
            super().setup()
            try:
                self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            except OSError:
                pass

        def do_POST(self) -> None:  # noqa: N802
            n = int(self.headers.get("Content-Length") or 0)
            if n:
                self.rfile.read(n)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(_UPSTREAM_BODY)))
            self.end_headers()
            self.wfile.write(_UPSTREAM_BODY)

        def log_message(self, *a: Any) -> None:
            return

    srv = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


def bench_proxy(n: int, warmup: int) -> dict[str, Any]:
    """Cost of routing model calls through the enforcement proxy.

    The proxy (``clawmetry/proxy.py``) enforces budget limits, loop detection
    and model routing by sitting in the request path, so unlike the collector
    it is unavoidably on the agent's critical path when enabled.

    **Method.** Both conditions are measured socket-to-socket over loopback,
    with the proxy served by waitress on a real port, so the comparison is
    like for like. An earlier attempt timed the proxy through Flask's test
    client against a real socket for the baseline, which compares two
    different transports and is not a measurement of anything.

    Part of the delta is inherent rather than ours: a proxy means the request
    crosses the network stack twice (client to proxy, proxy to provider)
    instead of once, and on a real deployment that second hop is the one that
    also carries the provider's own latency. What is measured here is the
    added cost with the provider replaced by a loopback stub, so the figure is
    the proxy's own work plus one extra local hop.

    Off by default (opt-in), and returns ``{"skipped": ...}`` rather than a
    guess when its dependencies are unavailable.
    """
    try:
        import requests
        import waitress  # noqa: F401
        from clawmetry.proxy import ProviderConfig, ProxyConfig, create_proxy_app
    except Exception as exc:
        return {"skipped": f"proxy deps unavailable: {exc}"}

    import socket as _socket
    import threading

    tmp = tempfile.mkdtemp(prefix="cm-bench-proxy-")
    prev_store = os.environ.get("CLAWMETRY_LOCAL_STORE_PATH")
    prev_home = os.environ.get("CLAWMETRY_HOME")
    srv = None
    try:
        # Sandbox the store. The proxy best-effort writes enforcement events
        # into DuckDB, and the daemon owns the real writer lock: pointing this
        # at a temp file keeps the benchmark away from the operator's data and
        # away from a lock it has no business touching.
        os.environ["CLAWMETRY_HOME"] = tmp
        os.environ["CLAWMETRY_LOCAL_STORE_PATH"] = os.path.join(tmp, "bench.duckdb")
        os.environ.setdefault("ANTHROPIC_API_KEY", "sk-bench-fake")

        srv, upstream = _serve_upstream()
        cfg = ProxyConfig()
        cfg.providers = {"anthropic": ProviderConfig(
            api_key_env="ANTHROPIC_API_KEY", base_url=upstream)}
        app = create_proxy_app(cfg)

        sk = _socket.socket()
        sk.bind(("127.0.0.1", 0))
        port = sk.getsockname()[1]
        sk.close()
        import waitress as _w
        threading.Thread(
            target=lambda: _w.serve(app, host="127.0.0.1", port=port,
                                    threads=4, _quiet=True),
            daemon=True).start()

        payload = {"model": "claude-opus-4-7", "max_tokens": 64,
                   "messages": [{"role": "user", "content": "benchmark " * 20}]}
        headers = {"x-api-key": "sk-bench-fake", "content-type": "application/json",
                   "anthropic-version": "2023-06-01"}
        sess = requests.Session()

        def _direct() -> None:
            sess.post(upstream + "/v1/messages", json=payload,
                      headers=headers, timeout=15)

        def _proxied() -> None:
            sess.post(f"http://127.0.0.1:{port}/v1/messages", json=payload,
                      headers=headers, timeout=15)

        for _ in range(200):   # wait for waitress to accept
            try:
                _proxied()
                break
            except Exception:
                time.sleep(0.05)
        else:
            return {"skipped": "proxy did not come up"}

        # Alternate so neither side gets only the cold half of the run.
        d1 = _time_many(_direct, n, warmup)
        p1 = _time_many(_proxied, n, warmup)
        p2 = _time_many(_proxied, n, 0)
        d2 = _time_many(_direct, n, 0)
        direct, proxied = _summarise(d1 + d2), _summarise(p1 + p2)
        added = round(proxied["p50_us"] - direct["p50_us"], 2)
        return {
            "opt_in": True,
            "on_critical_path": True,
            "method": ("socket-to-socket over loopback, proxy served by waitress, "
                       "provider replaced by a local stub; includes the extra hop "
                       "a proxy inherently adds"),
            "direct": direct,
            "proxied": proxied,
            "added_p50_us": added,
            "added_p95_us": round(proxied["p95_us"] - direct["p95_us"], 2),
            "as_pct_of_real_call": {
                "typical_5s": round(100.0 * added / 5_000_000, 4),
            },
        }
    finally:
        if srv is not None:
            srv.shutdown()
        for key, prev in (("CLAWMETRY_LOCAL_STORE_PATH", prev_store),
                          ("CLAWMETRY_HOME", prev_home)):
            if prev is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = prev
        shutil.rmtree(tmp, ignore_errors=True)


# ── 4. steady-state daemon cost, measured on a real install ──────────────

def _find_daemon_pids() -> dict[str, int]:
    """Locate the running ClawMetry daemon and dashboard, read-only.

    Matches on the command line rather than a pid file, because a pid file can
    outlive the process it names. READS ONLY: this never signals anything. A
    broad ``pkill``-shaped sweep over the same pattern has taken out a real
    user's daemon before, so this function deliberately has no way to.
    """
    found: dict[str, int] = {}
    try:
        import subprocess
        out = subprocess.check_output(["ps", "-Ao", "pid=,args="], text=True, timeout=15)
    except Exception:
        return found
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        pid_s, _, args = line.partition(" ")
        # A bare "clawmetry" substring is far too loose: on a developer box it
        # also matches browser tabs open on clawmetry URLs and a cloud-sql-proxy
        # pointed at the clawmetry database. Require an actual Python process
        # running one of our two long-lived services.
        #
        # Precision matters twice over. Short-lived CLI subcommands must not
        # match either (`clawmetry hooks run ...` fires on every gated tool
        # call, and this very harness spawns its own), because sampling a
        # process that exits mid-window yields a meaningless delta. Both
        # mistakes were live: the first version latched onto a transient pid
        # that had already gone by the second reading.
        if "python" not in args.lower():
            continue
        try:
            pid = int(pid_s)
        except ValueError:
            continue
        if ("-m clawmetry.sync" in args or "clawmetry/sync.py" in args) \
                and "sync_daemon" not in found:
            found["sync_daemon"] = pid
        elif ("dashboard.py" in args
              # The installed dashboard runs as `python -m clawmetry --port N`.
              # Anchor on the module with no subcommand after it, so the CLI
              # forms (`-m clawmetry hooks ...`, `-m clawmetry sync`) do not
              # match here.
              or re.search(r"-m\s+clawmetry(\s+--|\s*$)", args)) \
                and "dashboard" not in found:
            found["dashboard"] = pid
    return found


def _proc_cpu_rss(pid: int) -> tuple[float, float]:
    """(cumulative CPU seconds, RSS MB) for ``pid``. Raises if it is gone."""
    import subprocess
    out = subprocess.check_output(
        ["ps", "-p", str(pid), "-o", "cputime=,rss="], text=True, timeout=15).strip()
    cpu_s, rss_s = out.split(None, 1)
    secs = 0.0
    for part in cpu_s.replace("-", ":").split(":"):
        secs = secs * 60 + float(part)
    return secs, int(rss_s.strip()) / 1024.0


def bench_daemon_steady_state(window_s: float = 100.0) -> dict[str, Any]:
    """What the daemon costs while it just sits there.

    This is the number that actually matters for a sidecar you leave running,
    and it is the one a burst-of-ingest benchmark cannot tell you. It is
    measured as a **delta of cumulative CPU time across a window**, not as
    ``ps %cpu``: that column is a decayed lifetime average, so on a
    freshly-started daemon it reports the first-run ingest burst rather than
    the steady state.

    Measures the daemon already running on this machine, because a sandboxed
    daemon with an empty store is not the thing anyone cares about. That makes
    the result specific to this install's workload, which is stated rather
    than smoothed away: a machine driving many agents with a large store will
    legitimately cost more than a quiet laptop.

    Returns ``{"skipped": ...}`` when no daemon is running, rather than
    inventing a figure.
    """
    pids = _find_daemon_pids()
    if not pids:
        return {"skipped": "no running clawmetry daemon found on this machine"}

    before: dict[str, tuple[float, float]] = {}
    for name, pid in pids.items():
        try:
            before[name] = _proc_cpu_rss(pid)
        except Exception:
            pass
    if not before:
        return {"skipped": "daemon vanished before sampling started"}

    t0 = time.perf_counter()
    time.sleep(window_s)
    elapsed = time.perf_counter() - t0

    out: dict[str, Any] = {"window_s": round(elapsed, 1), "processes": {}}
    for name, (cpu0, rss0) in before.items():
        try:
            cpu1, rss1 = _proc_cpu_rss(pids[name])
        except Exception:
            # Restarted or exited mid-window: a delta across that is garbage.
            out["processes"][name] = {"skipped": "process went away mid-window"}
            continue
        used = max(0.0, cpu1 - cpu0)
        out["processes"][name] = {
            "pid": pids[name],
            "cpu_seconds_used": round(used, 3),
            "pct_of_one_core": round(100.0 * used / elapsed, 2),
            "rss_mb_start": round(rss0, 1),
            "rss_mb_end": round(rss1, 1),
        }
    return out


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
        _cpu_txt = (
            f"+{c['added_p50_us'] / 1000:.2f} ms CPU" if c.get("resolvable")
            else ("CPU not resolvable on this platform "
                  f"({c['zero_sample_fraction'] * 100:.0f}% of samples read exactly 0)")
        )
        out.append(
            f"  HTTP interceptor (opt-in)   +{w['added_p50_us'] / 1000:.2f} ms per call "
            f"(wall p50)   {_cpu_txt}"
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
    px = report.get("proxy") or {}
    if px.get("skipped"):
        out.append(f"  enforcement proxy           not measured: {px['skipped']}")
    elif px.get("added_p50_us") is not None:
        out.append("")
        out.append(
            f"  enforcement proxy (opt-in)  +{px['added_p50_us'] / 1000:.1f} ms per call "
            f"(p50)   +{px['added_p95_us'] / 1000:.1f} ms p95"
        )
        out.append(
            f"                              = {px['as_pct_of_real_call']['typical_5s']:.3f}% "
            "of a 5s model call; includes the extra hop a proxy inherently adds"
        )

    hg = report.get("hook_gate") or {}
    if hg.get("conditions"):
        fl = hg["floor_bare_interpreter"]["p50_us"] / 1000
        out.append("")
        out.append("  pre-tool hook gate (opt-in, but ON the critical path):")
        out.append(
            f"    bare interpreter floor    {fl:.0f} ms   "
            "- what any process-per-call hook costs before we do anything"
        )
        _labels = {
            "no_key": "no cloud approver",
            "warm_cache": "warm policy cache",
            "policy_miss": "policy miss",
            "cold_cache": "cold cache (refetch)",
        }
        for key, lbl in _labels.items():
            c = hg["conditions"].get(key)
            if not c:
                continue
            tag = "  <- includes a cloud round trip" if c.get("network_dependent") else ""
            out.append(
                f"    {lbl:<24}  {c['p50_us'] / 1000:5.0f} ms   "
                f"(+{c['added_over_floor_p50_us'] / 1000:.0f} ms over floor){tag}"
            )
        out.append(
            "    The refetch happens once per 60s cache window, on whichever tool"
        )
        out.append(
            "    call trips it, and is bounded by your network rather than by us."
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
    ds = report.get("daemon_steady_state") or {}
    if ds.get("skipped"):
        out.append(f"  daemon idle   not measured: {ds['skipped']}")
    elif ds.get("processes"):
        for name, pr in ds["processes"].items():
            if pr.get("skipped"):
                out.append(f"  {name:<13} not measured: {pr['skipped']}")
                continue
            out.append(
                f"  {name:<13} {pr['pct_of_one_core']:.2f}% of one core sustained "
                f"over {ds['window_s']:.0f}s, {pr['rss_mb_end']:.0f} MB RSS"
            )
        out.append(
            "                (this install's real workload, not an idle sandbox)"
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
    ap.add_argument(
        "--daemon-window", type=float, default=0.0,
        help=("also sample the RUNNING daemon's steady-state CPU for this many "
              "seconds (e.g. 100). Off by default: it costs that much wall "
              "clock and needs a daemon to be running. Read-only."))
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
    # Subprocess-per-sample, so far fewer iterations than the in-process
    # interceptor measurement: each one is a full interpreter launch.
    report["proxy"] = bench_proxy(
        n=60 if args.quick else 200, warmup=20 if args.quick else 50)
    report["hook_gate"] = bench_hook_gate(
        n=15 if args.quick else 40, warmup=3 if args.quick else 8)
    report["ingest_query"] = bench_ingest_and_query(events, sessions=50, query_n=query_n)

    if args.daemon_window > 0:
        report["daemon_steady_state"] = bench_daemon_steady_state(args.daemon_window)

    print(_render(report))
    if args.json_path:
        with open(args.json_path, "w") as fh:
            json.dump(report, fh, indent=2)
        print(f"  raw report -> {args.json_path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
