"""One condition of the interceptor benchmark, in its own process.

Why a subprocess
----------------
``interceptor.activate()`` is a one-way global monkey-patch — there is no
``deactivate()`` — so the two conditions cannot be interleaved inside a
single process. Running them as "baseline first, then patched" instead
produces a well-known artifact: the second condition inherits warm import
caches and a warm CPU and can measure *faster* despite doing strictly more
work. The first draft of this harness had exactly that bug and duly reported
negative overhead. Each condition now gets a fresh process, and the parent
alternates their order across rounds.

Why no socket
-------------
The interceptor's cost is CPU: classify the URL, parse the request body for
a model name, parse the response body for token counts, append a JSONL line.
The network round-trip is the *provider's* cost, not ours, and including it
only injects noise — a loopback ``http.server`` round-trip on this rig has a
p50 near 2ms and a p99 past 40ms, which is two to three orders of magnitude
larger than the thing being measured. Subtracting one noisy millisecond
distribution from another cannot resolve a microsecond signal.

So the transport is replaced with a mounted adapter that returns a canned
response with no I/O at all. ``Session.send`` — the function the interceptor
actually wraps — still runs in full, so the measured delta is exactly the
work ClawMetry adds and nothing else. The number to compare it against is a
real model call, which is 0.5–30 *seconds*.

Emits one line of JSON on stdout: ``{"samples_s": [...]}``.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# A realistic chat-completions response, so the interceptor takes its real
# token/model extraction path rather than bailing out early on a shape it
# does not recognise.
_RESPONSE_BODY = json.dumps({
    "id": "chatcmpl-bench",
    "object": "chat.completion",
    "model": "gpt-4o-mini",
    "choices": [{
        "index": 0,
        "message": {"role": "assistant", "content": "ok " * 40},
        "finish_reason": "stop",
    }],
    "usage": {"prompt_tokens": 1200, "completion_tokens": 40, "total_tokens": 1240},
}).encode()

# An LLM URL, so the interceptor runs the full cost-tracking branch. A
# non-LLM URL takes a much cheaper path and would understate the overhead.
_URL = "https://api.openai.com/v1/chat/completions"


def _make_session():
    """A requests Session whose transport is a no-I/O stub."""
    import requests
    from requests.adapters import BaseAdapter
    from requests.models import Response
    from requests.structures import CaseInsensitiveDict

    class _MockAdapter(BaseAdapter):
        def send(self, request, **kwargs):  # noqa: D102
            r = Response()
            r.status_code = 200
            r._content = _RESPONSE_BODY
            r.headers = CaseInsensitiveDict({
                "Content-Type": "application/json",
                "Content-Length": str(len(_RESPONSE_BODY)),
            })
            r.url = str(request.url)
            r.request = request
            return r

        def close(self):  # noqa: D102
            return None

    sess = requests.Session()
    sess.mount("https://", _MockAdapter())
    sess.mount("http://", _MockAdapter())
    return sess


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("baseline", "patched"), required=True)
    ap.add_argument("--n", type=int, default=2000)
    ap.add_argument("--warmup", type=int, default=200)
    ap.add_argument("--out", required=True, help="temp CLAWMETRY_HOME for the event sink")
    args = ap.parse_args()

    # Sandbox the event sink. The interceptor resolves its output as
    # ``$CLAWMETRY_HOME/intercepted.jsonl``, so pointing CLAWMETRY_HOME at a
    # temp dir is what keeps a benchmark run out of the operator's real
    # ~/.clawmetry. Set it for BOTH conditions so neither inherits a
    # different environment than the other.
    os.environ["CLAWMETRY_HOME"] = args.out

    if args.mode == "patched":
        from clawmetry import interceptor
        interceptor.activate()

    sess = _make_session()
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": "benchmark prompt " * 20}],
    }

    def call() -> None:
        sess.post(_URL, json=payload, timeout=10)

    for _ in range(args.warmup):
        call()

    # GC mid-run shows up as a fat tail that belongs to neither condition.
    # Disable it for the measured window; both conditions get the same deal.
    import gc
    gc.collect()
    gc.disable()
    try:
        samples: list[float] = []
        cpu: list[float] = []
        for _ in range(args.n):
            c0 = time.process_time()
            t0 = time.perf_counter()
            call()
            samples.append(time.perf_counter() - t0)
            cpu.append(time.process_time() - c0)
    finally:
        gc.enable()

    # Wall clock is what a user feels; CPU time is what ClawMetry actually
    # spends. On a loaded machine wall clock carries every unrelated process
    # on the box, so the CPU figure is the reproducible one and the wall
    # figure is the honest upper bound. Report both rather than picking the
    # flattering one.
    # Report the CPU clock's granularity alongside the samples. On Windows
    # process_time() ticks at roughly 15.6ms, which is far coarser than the
    # per-call cost being measured, so nearly every sample reads as exactly
    # zero and the delta comes out at a confident, meaningless 0.00ms. The
    # parent uses this to say "not resolvable on this platform" instead of
    # publishing a free lunch.
    sys.stdout.write(json.dumps({
        "samples_s": samples,
        "cpu_s": cpu,
        "cpu_clock_resolution_s": time.get_clock_info("process_time").resolution,
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
