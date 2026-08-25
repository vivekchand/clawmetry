# Instrumentation overhead

> Every number on this page came out of `benchmarks/overhead.py`. You can run
> it yourself in about a minute and get a report for *your* machine:
>
> ```bash
> python -m benchmarks.overhead            # full run, ~60s
> python -m benchmarks.overhead --quick    # ~15s
> ```
>
> The raw JSON behind the table below is committed at
> [`benchmarks/results/overhead-m2pro.json`](../benchmarks/results/overhead-m2pro.json).

## The short version

| Path | Added latency to your agent | Default? |
|------|-----------------------------|----------|
| Session-file tailing (how ClawMetry observes all 26 runtimes) | **0**. Separate process, no ClawMetry code in the agent | **on** |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.45 ms** per LLM call (wall p50), +0.35 ms CPU | off |
| Pre-tool hook gates | not yet benchmarked, see [Not yet measured](#not-yet-measured) | off |
| Enforcement proxy (`clawmetry/proxy.py`) | not yet benchmarked | off |

Host cost of the daemon, off the agent's critical path:

| | Measured |
|---|---|
| Ingest throughput | 2,707 events/sec (369 µs/event) |
| Disk | 710 bytes/event → **67.7 MB per 100k events** |
| Peak RSS | 161 MB (60 MB growth over the run) |
| Context-blowout query | 14.5 ms p50 over 25k events / 50 sessions |

Measured on an Apple M2 Pro (12 cores), macOS 26.3.1, Python 3.14.6,
DuckDB 1.5.5.

## Why "agent path" and "host cost" are separate

"Instrumentation overhead" is one phrase covering two different questions,
and conflating them is how benchmarks turn into vibes.

**Agent path** is latency added to your agent's own critical path. It is the
number that decides whether observing an agent changes how it behaves. On
ClawMetry's default path this is *structurally* zero, not merely small: the
collector is a separate daemon process that tails session files the runtime
was already writing to disk. There is no ClawMetry code in your agent's
process, no wrapper around its model calls, no sidecar in its request path.
Nothing to measure, because nothing runs there.

That is an architectural claim rather than a measurement, so the harness
spends its effort on the paths where we genuinely *are* in the loop, all of
which are opt-in.

**Host cost** is CPU, memory and disk the daemon consumes while ingesting.
It is real, non-zero, and it is what actually shows up in `top`.

## The interceptor: +0.45 ms per call

The HTTP interceptor (`CLAWMETRY_INTERCEPT=1`, or `import clawmetry.track`)
monkey-patches `httpx`/`requests` so any Python agent gets per-call cost
tracking without an adapter. It is the only path that puts ClawMetry inside a
Python agent's request path.

| | p50 | p95 |
|---|---|---|
| Baseline call | 0.65 ms | |
| Instrumented call | 1.11 ms | |
| **Added (wall)** | **+0.45 ms** | +0.69 ms |
| **Added (CPU)** | **+0.35 ms** | |

Against a real model call, which takes 0.5–30 seconds:

- **0.045%** of a 1-second call
- **0.009%** of a 5-second call
- **0.002%** of a 30-second call

That work is: classify the URL, parse the request body for a model name,
parse the response body for token counts, append a JSONL line. The append
opens and closes the file per call, which is the dominant term. That is a
deliberate trade for crash-safety over throughput on a path that runs at most a few
times per second.

### How it was measured, and three ways it was wrong first

The methodology matters more than the number, so here is what the harness
does and what it corrects for. Each of these was a real bug in an earlier
draft that produced a confidently wrong figure.

**1. Separate processes, alternating order.** `interceptor.activate()` is a
one-way global monkey-patch, and there is no `deactivate()`, so the two
conditions cannot be interleaved in one process. Running them as "baseline
first, then patched" lets the second condition inherit warm import caches and
a warm CPU, and it measured *faster* despite doing strictly more work. The
first draft duly reported **negative overhead**. Now each condition gets a
fresh subprocess and the parent alternates which goes first per round.

**2. No network in the measurement.** The second draft timed real loopback
HTTP. A `http.server` round-trip on this rig has a p50 near 2 ms and a p99
past 40 ms, two orders of magnitude larger than the signal. Subtracting one
noisy millisecond distribution from another cannot resolve a microsecond
effect, and the result swung between +775 µs and −2,832 µs depending on the
percentile. The transport is now a mounted stub adapter that returns a canned
response with no I/O. `Session.send`, the function the interceptor actually
wraps, still runs in full, so the delta is exactly our work.

**3. Enough samples, and a refusal to publish noise.** At 40 calls per
condition the harness cannot separate a 0.45 ms effect from scheduler jitter.
It now takes 5,000 calls per condition across 3 rounds, disables GC inside
the measured window, and **checks that the rounds agree on the sign of the
delta**. If they disagree, it prints "below this rig's noise floor" and the
per-round spread instead of an average. A benchmark that always produces a
tidy number is not measuring anything.

Both wall-clock and CPU time are reported. On a loaded machine wall clock
carries every unrelated process on the box; CPU time is what ClawMetry
actually spends. The per-round CPU deltas on this run were 343, 351 and
339 µs, which is tight. The wall deltas were 558, 383 and 415 µs, and that
spread is the machine, not the code. Treat CPU as the reproducible figure and wall as the
honest upper bound.

## Host cost

Ingesting 25,000 realistic v3-shaped events across 50 sessions into a fresh
DuckDB:

- **2,707 events/sec**, 369 µs/event, including the durable flush
- **710 bytes/event** on disk, or 67.7 MB per 100k events, WAL included
- **161 MB peak RSS**, 8.2 s user CPU for the whole 25k-event run

For scale: a heavy day of agent work is on the order of 10k–50k events, so
the daemon's steady-state cost is seconds of CPU and tens of megabytes of
disk per day.

The context-blowout query reads that corpus in **14.5 ms p50** (58 ms p95).
That cost is paid by whoever has the dashboard open, never by the agent.

## Not yet measured

Being explicit about the gaps, because a benchmark page that implies full
coverage is the thing this page exists to avoid:

- **Pre-tool hook gates.** Where a runtime exposes a `PreToolUse`-style hook,
  ClawMetry can hold a tool call before it runs. This *is* on the agent's
  critical path and its cost is a process spawn plus a policy evaluation.
  Some of these gates are fail-closed, which makes their latency and
  reliability more consequential than the interceptor's. Not yet in the
  harness.
- **Enforcement proxy** (`clawmetry/proxy.py`, port 4100). An in-path HTTP
  proxy for budget limits and model routing. Adds a hop; unmeasured.
- **Cloud sync.** Snapshot encryption and upload run in the daemon, off the
  agent path, but the CPU cost of AES-256-GCM over a large snapshot is not
  in these figures.
- **Windows and Linux.** Every number here is from one Apple M2 Pro. Run the
  harness on your platform and send a PR adding your result JSON to
  `benchmarks/results/`. Cross-platform numbers are worth more than ours
  repeated.

## Reproducing

```bash
git clone https://github.com/clawmetry/clawmetry && cd clawmetry
pip install -e . requests
python -m benchmarks.overhead --json my-machine.json
```

No network, no config, no daemon required. Everything runs against a stub
transport and a throwaway DuckDB in a temp directory, so the numbers are
ClawMetry's own cost and not your provider's latency.
