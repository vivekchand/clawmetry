#!/usr/bin/env python3
"""Drive a REAL LiteLLM proxy into a real ClawMetry dashboard and check the
Usage answer against LiteLLM's own spend log (REQ-OBS-GWY-001, issue #5940).

Run by ``.github/workflows/litellm-gateway.yml``. Standard library only, so it
runs in the dashboard's environment and talks to both services over HTTP; the
proxy lives in its own virtualenv.

Two phases:

``drive``
    Creates two teams, two users and one virtual key each through LiteLLM's
    management API, then sends: an ordinary request, the same request again
    (answered from LiteLLM's response cache), a second distinct request, a
    streamed request carrying a W3C ``traceparent``, a request to a deployment
    that always fails (with retries configured), and a request whose body
    claims the OTHER team in ``metadata``. It posts one agent span on the
    streamed request's trace, as an agent that propagated its trace context
    would. Then it waits for ``/api/usage/by-team`` to show every request and
    asserts the gateway block, reconciling each team's spend with LiteLLM's
    ``/spend/logs`` and printing the residual. The gateway block is saved.

``after-restart``
    Run after the dashboard process is restarted: the same block must come
    back unchanged from the store.

Exit code 0 on success; any mismatch raises with the figures that disagree.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _local_url(port: int) -> str:
    """Return a loopback URL from a port number; the host is never caller-supplied."""
    return "http://127.0.0.1:" + str(port)


TEAMS = {
    "team-alpha": {"alias": "Alpha", "user": "alice", "email": "alice@example.test", "key_alias": "alpha-ci"},
    "team-beta": {"alias": "Beta", "user": "bob", "email": "bob@example.test", "key_alias": "beta-ci"},
}
# The streamed request's trace, shared with the agent span posted below.
SHARED_TRACE = "4bf92f3577b34da6a3ce929d0e0e4736"
EXPECTED_REQUESTS = 6


def _http(method: str, url: str, *, headers=None, body=None, timeout=60, raw=False):
    data = None
    hdrs = dict(headers or {})
    if body is not None:
        data = json.dumps(body).encode()
        hdrs.setdefault("content-type", "application/json")
    req = urllib.request.Request(url, data=data, method=method, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = resp.read()
            return resp.status, (payload if raw else _json(payload))
    except urllib.error.HTTPError as e:
        payload = e.read()
        return e.code, (payload if raw else _json(payload))


def _json(payload: bytes):
    try:
        return json.loads(payload or b"null")
    except ValueError:
        return payload.decode("utf-8", "replace")


def _admin(args, path, body):
    status, out = _http(
        "POST", args.proxy + path, body=body,
        headers={"Authorization": "Bearer " + args.master_key},
    )
    if status != 200:
        raise SystemExit(f"LiteLLM {path} failed: {status} {out}")
    return out


def _chat(args, key, body, extra_headers=None, expect=200):
    headers = {"Authorization": "Bearer " + key}
    headers.update(extra_headers or {})
    status, out = _http("POST", args.proxy + "/v1/chat/completions",
                        headers=headers, body=body, raw=True)
    if status != expect:
        raise SystemExit(f"chat {body.get('model')} returned {status}, expected {expect}: {out[:300]!r}")
    return out


def _usage(args):
    status, out = _http(
        "GET", args.dashboard + "/api/usage/by-team?window=7",
        headers={"Authorization": "Bearer " + args.token},
    )
    if status != 200 or not isinstance(out, dict):
        return None
    return out


def _wait_for_requests(args, want, timeout=120):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        last = _usage(args)
        gw = (last or {}).get("gateway") or {}
        if gw.get("available") and (gw.get("totals") or {}).get("requests", 0) >= want:
            # One more export may still be in flight; take a second read and
            # require it to agree, so a half-flushed batch is not asserted on.
            time.sleep(6)
            again = _usage(args)
            if again and again.get("gateway") == gw:
                return again
        time.sleep(3)
    raise SystemExit(f"gateway usage never reached {want} requests: {json.dumps(last)[:2000]}")


def _post_agent_span(args):
    now = time.time_ns()
    body = {"resourceSpans": [{
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "ci-agent"}}]},
        "scopeSpans": [{"scope": {"name": "ci-agent"}, "spans": [{
            "traceId": SHARED_TRACE, "spanId": "00f067aa0ba902b7", "name": "agent.turn",
            "startTimeUnixNano": str(now - 2_000_000_000), "endTimeUnixNano": str(now),
            "attributes": [{"key": "gen_ai.operation.name", "value": {"stringValue": "invoke_agent"}}],
        }]}],
    }]}
    status, out = _http("POST", args.dashboard + "/v1/traces", body=body)
    if status != 200:
        raise SystemExit(f"agent span POST failed: {status} {out}")


def _spend_by_team(args):
    status, rows = _http("GET", args.proxy + "/spend/logs",
                         headers={"Authorization": "Bearer " + args.master_key})
    if status != 200 or not isinstance(rows, list):
        raise SystemExit(f"/spend/logs failed: {status} {rows}")
    out = {}
    for r in rows:
        t = out.setdefault(r.get("team_id"), {"requests": 0, "spend": 0.0, "failed": 0})
        t["requests"] += 1
        t["spend"] += float(r.get("spend") or 0.0)
        if r.get("status") == "failure":
            t["failed"] += 1
    return out


def _check(cond, message):
    if not cond:
        raise SystemExit("ASSERTION FAILED: " + message)
    print("  ok  " + message)


def drive(args):
    keys = {}
    for team_id, t in TEAMS.items():
        _admin(args, "/team/new", {"team_id": team_id, "team_alias": t["alias"]})
        _admin(args, "/user/new", {"user_id": t["user"], "user_email": t["email"]})
        keys[team_id] = _admin(args, "/key/generate", {
            "team_id": team_id, "user_id": t["user"], "key_alias": t["key_alias"],
        })["key"]

    alpha, beta = keys["team-alpha"], keys["team-beta"]
    msg = lambda text: [{"role": "user", "content": text}]  # noqa: E731
    _chat(args, alpha, {"model": "fast-alias", "messages": msg("alpha one"), "user": "end-user-7"})
    _chat(args, alpha, {"model": "fast-alias", "messages": msg("alpha one"), "user": "end-user-7"})
    _chat(args, alpha, {"model": "fast-alias", "messages": msg("alpha two")})
    _chat(args, beta, {"model": "fast-alias", "messages": msg("beta stream"), "stream": True},
          extra_headers={"traceparent": f"00-{SHARED_TRACE}-00f067aa0ba902b7-01"})
    _chat(args, beta, {"model": "broken-alias", "messages": msg("beta fail")}, expect=500)
    _chat(args, beta, {"model": "fast-alias", "messages": msg("beta claims alpha"),
                       "metadata": {"team_id": "team-alpha", "user_api_key_team_id": "team-alpha"}})
    _post_agent_span(args)

    d = _wait_for_requests(args, EXPECTED_REQUESTS)
    gw = d["gateway"]
    teams = {t["team"]: t for t in gw["teams"]}
    spend = _spend_by_team(args)

    print("\nReconciliation, ClawMetry gateway block vs LiteLLM /spend/logs (same requests):")
    print(f"  {'team':<12} {'requests':>8} {'litellm':>8} {'spend (ClawMetry)':>18} {'spend (LiteLLM)':>16} {'residual':>12}")
    for team_id in TEAMS:
        ours, theirs = teams.get(team_id) or {}, spend.get(team_id) or {}
        residual = (ours.get("cost_usd") or 0.0) - theirs.get("spend", 0.0)
        print(f"  {team_id:<12} {ours.get('requests', 0):>8} {theirs.get('requests', 0):>8} "
              f"{(ours.get('cost_usd') or 0.0):>18.10f} {theirs.get('spend', 0.0):>16.10f} {residual:>12.2e}")
    print()

    _check(gw["cost_source"] == "gateway_reported" and gw["currency"] == "USD",
           "spend is labelled gateway-reported, in USD")
    spend_label = (gw.get("provenance") or {}).get("teams[].cost_usd") or {}
    _check(spend_label.get("cost_basis") == "published_rate" and spend_label.get("basis") == "measured"
           and "LiteLLM" in (spend_label.get("rate_source") or ""),
           "spend carries the shared cost label: usage value at the rates LiteLLM applied, not an invoice")
    _check(set(teams) == set(TEAMS), f"exactly the two teams appear: {sorted(map(str, teams))}")
    for team_id, t in TEAMS.items():
        _check(abs((teams[team_id]["cost_usd"] or 0.0) - spend[team_id]["spend"]) < 1e-9,
               f"{team_id} spend matches LiteLLM's spend log")
        _check(teams[team_id]["requests"] == spend[team_id]["requests"],
               f"{team_id} request count matches LiteLLM's spend log")
        users = teams[team_id]["users"]
        _check(len(users) == 1 and users[0]["user_email"] == t["email"] and users[0]["key_alias"] == t["key_alias"],
               f"{team_id} is attributed to {t['email']} on key {t['key_alias']}")
    _check(teams["team-alpha"]["requests"] == 3,
           "the request whose body claimed team-alpha stayed with its key's team")
    _check(teams["team-alpha"]["cache_replays"] == 1, "the cached replay is counted once")
    _check(teams["team-beta"]["failed"] == 1 and teams["team-alpha"]["failed"] == 0,
           "the failed request is counted against team-beta only")
    _check(gw["totals"]["correlated"] == 1 and gw["totals"]["uncorrelated"] == EXPECTED_REQUESTS - 1,
           "one request shares a trace with the agent span; the rest are reported uncorrelated")
    _check(all("litellm" not in " ".join(r.get("runtimes") or []) for r in d.get("teams") or []),
           "the gateway does not appear as an agent runtime in the agent totals")

    with open(args.snapshot, "w") as f:
        json.dump(gw, f, indent=1, sort_keys=True)
    print(f"\nsaved gateway block to {args.snapshot}")


def after_restart(args):
    with open(args.snapshot) as f:
        before = json.load(f)
    d = None
    deadline = time.time() + 60
    while time.time() < deadline and d is None:
        d = _usage(args)
        if d is None:
            time.sleep(2)
    if d is None:
        raise SystemExit("dashboard did not answer after restart")
    _check(d["gateway"] == before, "after a restart the stored gateway block is unchanged")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("phase", choices=["drive", "after-restart"])
    p.add_argument("--dashboard-port", type=int, dest="dashboard_port",
                   default=int(os.environ.get("CLAWMETRY_PORT", "8900")))
    p.add_argument("--token", default=os.environ.get("CLAWMETRY_TOKEN", "ci-test-token"))
    p.add_argument("--proxy-port", type=int, dest="proxy_port",
                   default=int(os.environ.get("LITELLM_PORT", "4000")))
    p.add_argument("--master-key", default=os.environ.get("LITELLM_MASTER_KEY", "sk-master-test"))
    p.add_argument("--snapshot", default="litellm-gateway-block.json")
    args = p.parse_args(argv)
    args.dashboard = _local_url(args.dashboard_port)
    args.proxy = _local_url(args.proxy_port)
    (drive if args.phase == "drive" else after_restart)(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
