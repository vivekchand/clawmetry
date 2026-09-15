#!/usr/bin/env python3
"""Run the LangGraph + OpenLLMetry recipe against a live ClawMetry and check it.

REQ-OBS-OTR-001 (Factory requirement 0130f6a6-3f5b-448f-bd59-d8820a4d5c88).
This is the end-to-end half of the recipe's regression guard; the hermetic
half is tests/test_otel_recipe_langgraph.py. ci.yml's otel-recipe-langgraph job
boots a dashboard, installs the recipe's hash-pinned dependencies into their
own virtualenv, and runs this script with that virtualenv's interpreter as
``--agent-python``.

What it does, each step a hard failure with a sentence saying what was missing:

1. Remote auth (AC-OBS-OTR-001.7), only with ``--remote-url`` (the dashboard
   reached through a non-loopback address, which is what a remote node is):
   an OTLP export with no token is refused with 401, and the recipe exporting
   with ``OTEL_EXPORTER_OTLP_HEADERS=Authorization=Bearer <token>`` is accepted.
2. Two runs of the agent on ONE thread, the first with ``invoke()`` and the
   second with ``stream()`` (AC-OBS-OTR-001.3, .6).
3. One run with NO thread (AC-OBS-OTR-001.5).
4. Reads everything back through the local query API only
   (``/api/local/traces`` and ``/api/local/spans``) and asserts (AC-OBS-OTR-001.2):
     * the thread's runs are one session named by the thread, holding both
       traces, each trace carrying exactly the tokens the stub model reported;
     * every span of every run joined that session (a run is never split);
     * the tool span is present by name, and its parent chain reaches the
       run's top ``invoke_agent`` span in the same trace;
     * spans are attributed to the application's service.name identity, and
       the model calls carry the model name and a derived cost;
     * the no-thread run is one session per trace, ``<app>:trace:<trace_id>``.

Stdlib only, so it runs with the dashboard's interpreter.

    python3 scripts/verify_otel_recipe_langgraph.py \\
        --url http://127.0.0.1:8900 --token ci-token \\
        --agent-python .recipe-venv/bin/python \\
        [--remote-url http://10.1.0.4:8900]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
AGENT = os.path.join(REPO, "examples", "otel", "langgraph", "agent.py")

# Must match examples/otel/langgraph/agent.py (the test pins the pair).
APP_NAME = "invoice-agent"
AGENT_TYPE = "invoice_agent"
TOOL_NAME = "lookup_invoice"
MODEL_NAME = "claude-sonnet-4-5"
RUN_INPUT_TOKENS = 120 + 160
RUN_OUTPUT_TOKENS = 18 + 9


class Failed(Exception):
    pass


def _get(base: str, path: str, token: str, **params) -> dict:
    q = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    req = urllib.request.Request(f"{base}{path}?{q}",
                                 headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _run_agent(py: str, endpoint: str, *, thread: str | None, stream: bool,
               headers: str | None, service: str) -> None:
    env = dict(os.environ)
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint
    env["OTEL_SERVICE_NAME"] = service
    env.pop("OTEL_EXPORTER_OTLP_HEADERS", None)
    if headers:
        env["OTEL_EXPORTER_OTLP_HEADERS"] = headers
    cmd = [py, AGENT]
    if thread:
        cmd += ["--thread", thread]
    if stream:
        cmd += ["--stream"]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=180)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr)
        raise Failed(f"the recipe agent exited {proc.returncode}: {' '.join(cmd[1:])}")
    # The OTLP exporter logs an export it could not deliver and still exits 0.
    if "Failed to export" in proc.stderr:
        sys.stderr.write(proc.stderr)
        raise Failed("the recipe agent could not deliver its spans to ClawMetry")


def _wait_for(fn, what: str, timeout: float = 45.0):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = fn()
        if last:
            return last
        time.sleep(1.0)
    raise Failed(f"timed out after {timeout:.0f}s waiting for {what}")


def check_remote_auth(remote: str, token: str) -> None:
    body = json.dumps({"resourceSpans": []}).encode()
    req = urllib.request.Request(f"{remote}/v1/traces", data=body, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    if code != 401:
        raise Failed(f"an export to {remote} without a token answered {code}, expected 401 "
                     "(is the address really non-loopback?)")
    print(f"ok: export to {remote} without a Bearer token is refused (401)")


def _spans(base: str, token: str, session_id: str) -> list:
    return _get(base, "/api/local/spans", token, session_id=session_id, limit=500).get("rows") or []


def _traces(base: str, token: str, session_id: str) -> list:
    return _get(base, "/api/local/traces", token, session_id=session_id, limit=100).get("rows") or []


def _check_run_shape(spans: list, trace_id: str, session_id: str) -> None:
    mine = [s for s in spans if s.get("trace_id") == trace_id]
    by_id = {s["span_id"]: s for s in mine}
    roots = [s for s in mine if s.get("name", "").startswith("invoke_agent")]
    if len(roots) != 1:
        raise Failed(f"trace {trace_id}: expected one invoke_agent top span, found {len(roots)}")
    tools = [s for s in mine if s.get("tool_name") == TOOL_NAME]
    if len(tools) != 1:
        raise Failed(f"trace {trace_id}: expected one {TOOL_NAME} tool span, found {len(tools)}")
    node, hops = tools[0], 0
    while node.get("parent_span_id") and hops < 20:
        node = by_id.get(node["parent_span_id"])
        if node is None:
            raise Failed(f"trace {trace_id}: the tool span's parent chain is broken")
        hops += 1
    if node is not roots[0]:
        raise Failed(f"trace {trace_id}: the tool span does not descend from the invoke_agent span")
    chats = [s for s in mine if s.get("model")]
    if len(chats) != 2 or any(s["model"] != MODEL_NAME for s in chats):
        raise Failed(f"trace {trace_id}: expected two model calls on {MODEL_NAME}, "
                     f"found {[s.get('model') for s in chats]}")
    if not all(float(s.get("cost_usd") or 0) > 0 for s in chats):
        raise Failed(f"trace {trace_id}: a model call has no derived cost")
    strays = [s["name"] for s in mine if s.get("session_id") != session_id]
    if strays:
        raise Failed(f"trace {trace_id}: spans outside session {session_id}: {strays}")
    wrong_app = {s.get("agent_type") for s in mine} - {AGENT_TYPE}
    if wrong_app:
        raise Failed(f"trace {trace_id}: spans attributed to {sorted(wrong_app)}, not {AGENT_TYPE}")
    print(f"ok: trace {trace_id} has {len(mine)} spans in {session_id}; "
          f"{TOOL_NAME} descends from invoke_agent in {hops} hops")


def _check_trace_totals(trace: dict) -> None:
    tin, tout = int(trace.get("tokens_input") or 0), int(trace.get("tokens_output") or 0)
    if (tin, tout) != (RUN_INPUT_TOKENS, RUN_OUTPUT_TOKENS):
        raise Failed(f"trace {trace.get('trace_id')}: tokens {tin}/{tout}, the model "
                     f"reported {RUN_INPUT_TOKENS}/{RUN_OUTPUT_TOKENS}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", required=True, help="dashboard base URL (loopback)")
    ap.add_argument("--token", required=True, help="gateway token")
    ap.add_argument("--agent-python", default=sys.executable)
    ap.add_argument("--remote-url", default=None,
                    help="the same dashboard through a non-loopback address")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    service = f"{APP_NAME}"
    thread = f"recipe-thread-{uuid.uuid4().hex[:10]}"

    try:
        endpoint, headers = base, None
        if args.remote_url:
            endpoint = args.remote_url.rstrip("/")
            headers = f"Authorization=Bearer {args.token}"
            check_remote_auth(endpoint, args.token)

        started = time.time()
        _run_agent(args.agent_python, endpoint, thread=thread, stream=False,
                   headers=headers, service=service)
        _run_agent(args.agent_python, endpoint, thread=thread, stream=True,
                   headers=headers, service=service)
        if args.remote_url:
            print(f"ok: the recipe exported to {endpoint} with a Bearer token and was accepted")

        traces = _wait_for(lambda: (lambda t: t if len(t) >= 2 else None)(_traces(base, args.token, thread)),
                           f"two traces in session {thread}")
        if len(traces) != 2:
            raise Failed(f"session {thread}: expected 2 traces (invoke + stream), found {len(traces)}")
        spans = _wait_for(lambda: _spans(base, args.token, thread), f"spans of session {thread}")
        for t in traces:
            _check_trace_totals(t)
            _check_run_shape(spans, t["trace_id"], thread)
        print(f"ok: thread {thread} is ONE session holding both runs (invoke and stream), "
              f"{2 * (RUN_INPUT_TOKENS + RUN_OUTPUT_TOKENS)} tokens")

        # No thread: one session per trace, <app>:trace:<trace_id>.
        _run_agent(args.agent_python, endpoint, thread=None, stream=False,
                   headers=headers, service=service)

        def _fresh_fallback():
            rows = _get(base, "/api/local/traces", args.token, agent_type=AGENT_TYPE,
                        limit=100).get("rows") or []
            return [r for r in rows if str(r.get("session_id") or "").startswith(f"{AGENT_TYPE}:trace:")
                    and float(r.get("start_ts") or 0) >= started - 5] or None

        fallback = _wait_for(_fresh_fallback, "the no-thread run's trace")
        if len(fallback) != 1:
            raise Failed(f"expected one per-trace session for the no-thread run, found {len(fallback)}")
        t = fallback[0]
        expect_sid = f"{AGENT_TYPE}:trace:{t['trace_id']}"
        if t["session_id"] != expect_sid:
            raise Failed(f"no-thread run filed under {t['session_id']}, expected {expect_sid}")
        _check_trace_totals(t)
        _check_run_shape(_spans(base, args.token, expect_sid), t["trace_id"], expect_sid)
        print(f"ok: the no-thread run is its own session {expect_sid}")
    except Failed as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print("PASS: LangGraph + OpenLLMetry recipe verified end to end")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
