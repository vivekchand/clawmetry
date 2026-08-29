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
| Session-file tailing (how ClawMetry observes all 30 runtimes) | **0**. Separate process, no ClawMetry code in the agent | **on** |
| HTTP interceptor (`CLAWMETRY_INTERCEPT=1`) | **+0.44 ms** per LLM call (wall p50), +0.36 ms CPU | off |
| Pre-tool hook gate, warm cache | **+44 ms** per gated tool call, over a 36 ms interpreter floor | off |
| Pre-tool hook gate, 60s cache refresh | **+189 ms** on the one call that trips it, network-bound | off |
| Enforcement proxy (`clawmetry/proxy.py`) | **+9.7 ms** per LLM call (p50), +22 ms p95 | off |

Host cost of the daemon, off the agent's critical path:

| | Measured |
|---|---|
| Ingest throughput | 2,762 events/sec (362 µs/event) |
| Disk | 710 bytes/event → **67.7 MB per 100k events** |
| Peak RSS | 199 MB over a 25k-event run |
| Context-blowout query | 17.7 ms p50 over 25k events / 50 sessions |
| **Steady-state sync daemon** | **11.8-12.4% of one core**, sustained. See [the budget note](#the-daemon-is-over-its-own-cpu-budget) |
| Steady-state dashboard | 0.13% of one core, 32 MB RSS |

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

## The interceptor: +0.44 ms per call

The HTTP interceptor (`CLAWMETRY_INTERCEPT=1`, or `import clawmetry.track`)
monkey-patches `httpx`/`requests` so any Python agent gets per-call cost
tracking without an adapter. It is the only path that puts ClawMetry inside a
Python agent's request path.

| | p50 | p95 |
|---|---|---|
| Baseline call | 0.56 ms | |
| Instrumented call | 1.00 ms | |
| **Added (wall)** | **+0.44 ms** | +0.60 ms |
| **Added (CPU)** | **+0.36 ms** | |

Against a real model call, which takes 0.5–30 seconds:

- **0.044%** of a 1-second call
- **0.009%** of a 5-second call
- **0.001%** of a 30-second call

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

- **2,762 events/sec**, 362 µs/event, including the durable flush
- **710 bytes/event** on disk, or 67.7 MB per 100k events, WAL included
- **199 MB peak RSS**, 10.6 s user CPU for the whole 25k-event run

For scale: a heavy day of agent work is on the order of 10k–50k events, so
the daemon's steady-state cost is seconds of CPU and tens of megabytes of
disk per day.

The context-blowout query reads that corpus in **17.7 ms p50** (29 ms p95).
That cost is paid by whoever has the dashboard open, never by the agent.

## Pre-tool hook gates

This is the most consequential number on the page, because it is the only path
that can *hold* a tool call. Where a runtime exposes a `PreToolUse`-style hook,
the runtime spawns a process and waits for it before the tool executes, on
every matching call.

Most of that cost is Python starting up, which belongs to the mechanism rather
than to ClawMetry, so everything is reported against a bare-interpreter floor:

| Condition | Total | Over the floor |
|---|---|---|
| Bare interpreter (`python -c pass`) | 36 ms | the floor |
| No cloud approver configured | 53 ms | +17 ms |
| Warm policy cache | 80 ms | +44 ms |
| Policy compiled, then missed | 84 ms | +48 ms |
| **Cold cache (refetches policies)** | **225 ms** | **+189 ms** |

The first three are the steady state, and they land where the code intends:
there is a comment in `clawmetry/cli.py` asserting that a policy miss "must
cost ~40ms, not a third of a second", and at +44-48 ms over the floor it is
close to that, and nowhere near a third of a second.

**The cold-cache row is the one to know about.** The policy cache has a 60
second TTL, and when it lapses the gate fetches policies from the cloud
*inline, on the critical path*, before the tool runs. Roughly one tool call per
minute pays it. The 189 ms here is against a fast link; it is bounded by your
network and, during a cloud outage, by a timeout. It is reported separately and
never folded into a per-call average, because most of that number is not ours.

## Enforcement proxy

Routing model calls through the proxy (`clawmetry/proxy.py`, port 4100) for
budget limits, loop detection and model routing costs **+9.7 ms p50 and
+22 ms p95** per call, or 0.19% of a 5-second model call.

Measured socket-to-socket over loopback with the proxy served by waitress and
the provider replaced by a local stub. Part of that is inherent to being a
proxy rather than specific to this one: the request crosses the network stack
twice instead of once. An earlier attempt compared a Flask test client against
a real socket, which measures two different transports and nothing else.

## The daemon is over its own CPU budget

ClawMetry documents a budget for the collector: the sync daemon "idles near 0%
and averages no more than roughly 5-10% of one core". That is the right bar for
something you leave running all day.

Measured on the daemon actually running on the development machine, as a delta
of cumulative CPU time across a window rather than `ps %cpu` (which is a
decayed lifetime average and would report the first-run ingest burst instead of
the steady state):

| Window | sync daemon | dashboard |
|---|---|---|
| 100 s | **12.36% of one core** | 0.06% |
| 120 s | **11.76% of one core** | 0.13% |

RSS was flat to falling across both windows, so this is steady state and not a
startup burst. Two independent windows agree.

**That is above the stated budget**, and it is published here rather than
quietly left off the page. Caveats that belong with it, none of which change
the conclusion: this is one machine, it drives an unusually large number of
agents, and its store is correspondingly large. A quiet laptop will cost less.
But the budget as written does not carve out heavy installs, so on this machine
the daemon is out of budget and that is a bug to chase, not a footnote.

### Where it goes

FLYWHEEL says to profile before shipping anything on the ingest path, so:
`sample <pid> 8` on the running daemon puts **2,480 of 6,408 main-thread
samples (39%) inside `os.stat`**. The steady-state cost is dominated by
re-stat'ing the filesystem to find out what changed, which is what a
poll-based collector does and also the obvious thing to attack: fewer stats
per tick, a coarser scan for directories that have not moved, or a
change-notification API instead of polling.

That is a lead, not a diagnosis. It says where the time goes on this machine
and this workload; it does not yet say which scan is responsible.

Reproduce it on your own install with:

```bash
python -m benchmarks.overhead --daemon-window 120
```

It reads `ps` and never signals anything. If no daemon is running it says so
rather than inventing a figure.

## Cross-platform

The numbers above are from one Apple M2 Pro. The `Instrumentation overhead`
workflow runs the same harness on Linux, macOS and Windows and publishes each
result as an artifact. From a run on shared GitHub runners, which are slower
and noisier than a laptop you own:

| | ubuntu (EPYC 7763, 4c) | macOS (M1 virt, 3c) | windows (Intel, 4c) |
|---|---|---|---|
| Interceptor, wall p50 | +0.16 ms | +0.14 ms | +0.47 ms |
| Enforcement proxy, p50 | +3.6 ms | +4.6 ms | **+30.2 ms** |
| Hook: interpreter floor | 24 ms | 46 ms | 38 ms |
| Hook: warm cache, over floor | +25 ms | +3 ms | +26 ms |
| Hook: cold cache, over floor | +281 ms | +295 ms | +470 ms |
| Ingest | 3,183/sec | 3,346/sec | 2,610/sec |
| Disk | 770 B/event | 770 B/event | 770 B/event |

Two things stand out, and both are the point of running this anywhere but the
author's laptop:

- **The proxy costs roughly seven times more on Windows** than on Linux or
  macOS. Loopback networking and process scheduling differ enough there that a
  figure measured on a Mac does not transfer. If you run the enforcement proxy
  on Windows, budget for tens of milliseconds per call rather than single
  digits.
- **The cold-cache hook path costs 281-470 ms from CI**, against 189 ms from
  a laptop on a good connection. That is the point about it being bounded by
  the network rather than by us, demonstrated rather than asserted.

The interceptor's CPU figure is reported as **not resolvable on Windows**.
`time.process_time()` there advances only on a scheduler tick, roughly every
15.6 ms, against a sub-millisecond cost, so nearly every sample reads exactly
zero and a naive reading produces a confident, meaningless "+0.00 ms". Wall
clock is unaffected and is reported normally.

Worth recording how that guard was itself wrong first. The obvious check is to
compare the delta against `time.get_clock_info("process_time").resolution`.
On Windows that reports `1e-07`, because the counter is *denominated* in
100 ns units even though its value only changes five orders of magnitude less
often. The check passed and the harness published the zero anyway. It was
caught on the Windows CI leg, by this harness, one commit after the "fix".

The rule is now empirical rather than advertised: if most individual samples
read exactly zero, the clock did not resolve a single call, and no amount of
averaging makes it so.

## Still not measured

- **Cloud sync.** Snapshot encryption and upload run in the daemon, off the
  agent path. They sit inside the daemon CPU figure above but are not broken
  out, so how much of that 12% is AES-256-GCM over a large snapshot is not
  yet known. Given the `os.stat` result, that is the second place to look.
- **Steady-state daemon CPU on Linux and Windows.** The 12% figure is one
  macOS install. The daemon sampler needs a running daemon, which a CI runner
  does not have, so it is not in the cross-platform table.
- **Streaming responses.** Both the interceptor and the proxy were measured on
  a single non-streaming completion. A long SSE stream is parsed chunk by
  chunk, and that per-chunk cost is not in these numbers.

## Reproducing

The harness ships inside the package, so an install is enough. No clone
required:

```bash
pip install clawmetry requests
python -m benchmarks.overhead --json my-machine.json
```

Or from a checkout, if you want to benchmark a change:

```bash
git clone https://github.com/clawmetry/clawmetry && cd clawmetry
pip install -e . requests
python -m benchmarks.overhead --json my-machine.json
```

No network, no config, no daemon required. Everything runs against a stub
transport and a throwaway DuckDB in a temp directory, so the numbers are
ClawMetry's own cost and not your provider's latency.
