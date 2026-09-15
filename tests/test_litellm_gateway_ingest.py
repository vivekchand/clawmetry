"""REQ-OBS-GWY-001 (#5940): a LiteLLM proxy's usage, by team and user, labelled
as the gateway's figure and never added to agent totals.

Driven by ``tests/fixtures/litellm_1_83_7/proxy_traces.json``: the OTLP export
of a REAL LiteLLM 1.83.7 proxy (Postgres-backed, two teams, two virtual keys),
converted to OTLP/JSON and trimmed to the request spans plus a few proxy
internals. ``spend_logs.json`` is LiteLLM's own ``/spend/logs`` for the same
requests. The fixture's timestamps are shifted to "now" on every load so a
7-day window never ages it out. ``.github/workflows/litellm-gateway.yml``
drives a live proxy through the same path.

Requests in the fixture, by provider response id:

* ``chatcmpl-602b6e58...`` twice: team-alpha's first request, then the same
  request answered from LiteLLM's response cache (full cost on the span,
  0 in LiteLLM's spend log).
* ``chatcmpl-c48f6ccc...``: team-beta, streamed, with a client ``traceparent``.
* ``fd76f69d-...``: team-beta, a deployment that always fails.
* ``chatcmpl-b95234b9...``: team-beta's key, body metadata claiming team-alpha.

Acceptance criteria and the tests that hold them:

AC-OBS-GWY-001.1 -- one record per proxied request, attributed to the key's team, user and key: ``test_each_proxied_request_is_one_record_attributed_to_its_key``.
AC-OBS-GWY-001.2 -- body-supplied team labels do not move a request: ``test_a_team_claimed_in_the_request_body_does_not_move_the_request``.
AC-OBS-GWY-001.3 -- models, tokens, streaming, status, timestamps and ids retained: ``test_record_keeps_models_tokens_streaming_status_and_ids``.
AC-OBS-GWY-001.4 -- gateway-reported label; unreported cost is not zero: ``test_cost_is_labelled_gateway_reported_and_unreported_cost_is_not_zero``.
AC-OBS-GWY-001.5 -- redelivery changes nothing, a separate request counts: ``test_redelivery_and_restart_change_nothing_and_a_separate_request_counts``.
AC-OBS-GWY-001.6 -- a cache replay is not charged, in either arrival order: ``test_a_cache_replay_is_not_charged_in_either_arrival_order``.
AC-OBS-GWY-001.7 -- a separate subtotal, no sessions, correlation reported: ``test_gateway_is_a_separate_subtotal_not_an_agent``, ``test_usage_by_team_route_serves_the_gateway_block_separately`` and ``test_an_azure_call_the_proxy_makes_is_not_priced_again_by_the_interceptor``.
AC-OBS-GWY-001.8 -- failed requests counted per team: ``test_failed_requests_are_counted_per_team``.
AC-OBS-GWY-001.9 -- labels are text, never markup: ``test_usage_tab_escapes_gateway_and_team_labels``.
AC-OBS-GWY-001.10 -- per-team spend agrees with LiteLLM's spend log: ``test_per_team_totals_reconcile_with_litellm_spend_log``.
"""
from __future__ import annotations

import copy
import importlib
import json
import os
import pathlib
import re
import tempfile
import time

import pytest

import dashboard as _d
from clawmetry import gateway_litellm as gw

FIX = pathlib.Path(__file__).parent / "fixtures" / "litellm_1_83_7"
ALPHA_RESPONSE = "chatcmpl-602b6e58-68d4-4752-839b-f58a1c87a119"
ALPHA_ORIGINAL_SPAN = "68497c396c6f0915"
ALPHA_REPLAY_SPAN = "5f42f4f16065b699"
BETA_STREAM_SPAN = "05fa3e4e70863399"
BETA_FAILED_SPAN = "89226925de6fdfff"
BETA_SPOOF_SPAN = "99d8cdb2e6099159"
SHARED_TRACE = "4bf92f3577b34da6a3ce929d0e0e4736"


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture()
def store(monkeypatch):
    """A private DuckDB writer wired in as the singleton the receiver resolves.
    Same isolation rules as tests/test_otlp_daemon_free_intake.py."""
    global _ls
    _ls = importlib.import_module("clawmetry.local_store")
    tmpdir = tempfile.mkdtemp(prefix="clawmetry-gwy-")
    path = os.path.join(tmpdir, "gwy.duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", path)
    _ls._reset_singleton_for_tests()
    prev_db_path = _ls.DB_PATH
    _ls.DB_PATH = pathlib.Path(path)
    st = _ls.LocalStore()
    holder = {"store": st}
    monkeypatch.setattr(_ls, "get_store", lambda read_only=False: holder["store"])
    st.holder = holder  # lets a test swap in a reopened store
    try:
        yield st
    finally:
        for s in {id(st): st, id(holder["store"]): holder["store"]}.values():
            try:
                s.stop(flush=True)
            except Exception:
                pass
        _ls.DB_PATH = prev_db_path
        _ls._reset_singleton_for_tests()


def _payload():
    """The captured export, shifted so its newest span started a minute ago."""
    data = json.loads((FIX / "proxy_traces.json").read_text())
    starts = [int(s["startTimeUnixNano"]) for s in _iter_spans(data)]
    shift = (time.time_ns() - 60 * 10**9) - max(starts)
    for s in _iter_spans(data):
        s["startTimeUnixNano"] = str(int(s["startTimeUnixNano"]) + shift)
        s["endTimeUnixNano"] = str(int(s["endTimeUnixNano"]) + shift)
    return data


def _iter_spans(data):
    for rs in data["resourceSpans"]:
        for ss in rs["scopeSpans"]:
            for s in ss["spans"]:
                yield s


def _only(data, span_ids):
    out = copy.deepcopy(data)
    for rs in out["resourceSpans"]:
        for ss in rs["scopeSpans"]:
            ss["spans"] = [s for s in ss["spans"] if s["spanId"] in span_ids]
    return out


def _span(data, span_id):
    return next(s for s in _iter_spans(data) if s["spanId"] == span_id)


def _attr(span, key):
    for a in span["attributes"]:
        if a["key"] == key:
            return next(iter(a["value"].values()))
    return None


def _set_attr(span, key, value):
    span["attributes"] = [a for a in span["attributes"] if a["key"] != key]
    if value is not None:
        typ = "doubleValue" if isinstance(value, float) else "stringValue"
        span["attributes"].append({"key": key, "value": {typ: value}})


def _post(data):
    _d._process_otlp_traces(json.dumps(data).encode(), content_type="application/json")


def _record(st, span_id):
    cols = ("team", "team_alias", "user_id", "user_email", "key_alias", "model",
            "cost_usd", "cost_source", "success", "tokens_input", "tokens_output",
            "trace_id", "response_id", "session_id", "source", "attributes")
    rows = st._fetch(
        f"SELECT {', '.join(cols)} FROM otlp_records WHERE record_id LIKE ?",
        [gw.GATEWAY_SOURCE + ":%:" + span_id],
    )
    assert len(rows) == 1, f"expected one record for span {span_id}, got {rows}"
    rec = dict(zip(cols, rows[0]))
    blob = rec["attributes"]
    if isinstance(blob, (bytes, bytearray, memoryview)):
        blob = bytes(blob).decode("utf-8")
    rec["attributes"] = json.loads(blob) if blob else {}
    return rec


def _usage(st):
    out = st.query_gateway_usage(window_days=7)
    assert out and out["available"] is True
    return out, {t["team"]: t for t in out["teams"]}


# ── AC-OBS-GWY-001.1 ─────────────────────────────────────────────────────────

def test_each_proxied_request_is_one_record_attributed_to_its_key(store):
    _post(_payload())
    n = store._fetch("SELECT COUNT(*) FROM otlp_records WHERE source = ?", [gw.GATEWAY_SOURCE])[0][0]
    assert n == 5  # the six non-request spans in the fixture produce none
    for span_id, team, email, key in (
        (ALPHA_ORIGINAL_SPAN, "team-alpha", "alice@example.test", "alpha-ci"),
        (ALPHA_REPLAY_SPAN, "team-alpha", "alice@example.test", "alpha-ci"),
        (BETA_STREAM_SPAN, "team-beta", "bob@example.test", "beta-ci"),
        (BETA_FAILED_SPAN, "team-beta", "bob@example.test", "beta-ci"),
        (BETA_SPOOF_SPAN, "team-beta", "bob@example.test", "beta-ci"),
    ):
        rec = _record(store, span_id)
        assert (rec["team"], rec["user_email"], rec["key_alias"]) == (team, email, key)
    _, teams = _usage(store)
    assert teams["team-alpha"]["team_alias"] == "Alpha"
    assert [u["user_id"] for u in teams["team-beta"]["users"]] == ["bob"]


# ── AC-OBS-GWY-001.2 ─────────────────────────────────────────────────────────

def test_a_team_claimed_in_the_request_body_does_not_move_the_request(store):
    data = _payload()
    spoof = _span(data, BETA_SPOOF_SPAN)
    # Precondition, straight from the real proxy: the caller's claim IS on the
    # span, under a name that looks authoritative.
    assert _attr(spoof, "metadata.team_id") == "team-alpha"
    assert "team-alpha" in _attr(spoof, "metadata.requester_metadata")
    _post(data)
    assert _record(store, BETA_SPOOF_SPAN)["team"] == "team-beta"
    _, teams = _usage(store)
    assert teams["team-alpha"]["requests"] == 2

    # With no authenticated team at all, the claim still does not attribute it.
    unauth = _only(_payload(), {BETA_SPOOF_SPAN})
    s = _span(unauth, BETA_SPOOF_SPAN)
    s["spanId"] = "aaaaaaaaaaaaaaaa"
    _set_attr(s, "gen_ai.response.id", "chatcmpl-no-team")
    _set_attr(s, "metadata.user_api_key_team_id", None)
    _set_attr(s, "metadata.user_api_key_team_alias", None)
    _post(unauth)
    assert _record(store, "aaaaaaaaaaaaaaaa")["team"] is None


# ── AC-OBS-GWY-001.3 ─────────────────────────────────────────────────────────

def test_record_keeps_models_tokens_streaming_status_and_ids(store):
    _post(_payload())
    rec = _record(store, BETA_STREAM_SPAN)
    a = rec["attributes"]
    assert rec["model"] == "openai/gpt-4o-mini"
    assert a["deployment_model"] == "openai/gpt-4o-mini"
    assert a["requested_model"] == "fast-alias"
    assert a["provider"] == "openai"
    assert a["streaming"] is True
    assert rec["success"] is True
    assert (rec["tokens_input"], rec["tokens_output"]) == (9, 4)
    assert rec["trace_id"] == SHARED_TRACE
    assert a["parent_span_id"] == "00f067aa0ba902b7"
    assert a["span_id"] == BETA_STREAM_SPAN
    assert rec["response_id"] == "chatcmpl-c48f6ccc-0351-418a-acc7-7f624cbf4f7e"
    assert rec["session_id"] is None
    assert _record(store, ALPHA_ORIGINAL_SPAN)["attributes"]["streaming"] is False
    # Caller-supplied end user is kept for the record, never used as the user.
    alpha = _record(store, ALPHA_ORIGINAL_SPAN)
    assert alpha["attributes"]["end_user_client_supplied"] == "end-user-7"
    assert alpha["user_id"] == "alice"
    # No key material in the stored blob: not the key hash, and no other
    # ``metadata.user_api_key_*`` value, on any request. The key is
    # identified by its alias column only.
    for span_id in (ALPHA_ORIGINAL_SPAN, ALPHA_REPLAY_SPAN, BETA_STREAM_SPAN,
                    BETA_FAILED_SPAN, BETA_SPOOF_SPAN):
        stored = _record(store, span_id)["attributes"]
        assert not {"key_hash", "project_id", "org_alias"} & set(stored), (span_id, stored)
        span = _span(_payload(), span_id)
        key_values = {str(_attr(span, k)) for k in (
            "metadata.user_api_key_hash", "metadata.user_api_key_project_id",
            "metadata.user_api_key_org_alias") if _attr(span, k)}
        assert not key_values & {str(v) for v in stored.values()}, (span_id, key_values)


# ── AC-OBS-GWY-001.4 ─────────────────────────────────────────────────────────

def test_cost_is_labelled_gateway_reported_and_unreported_cost_is_not_zero(store):
    data = _only(_payload(), {BETA_STREAM_SPAN})
    s = _span(data, BETA_STREAM_SPAN)
    for key in [a["key"] for a in s["attributes"] if a["key"].startswith("gen_ai.cost.")]:
        _set_attr(s, key, None)
    _set_attr(s, "hidden_params", json.dumps({"response_cost": None}))
    _post(data)
    rec = _record(store, BETA_STREAM_SPAN)
    assert rec["cost_usd"] is None and rec["cost_source"] == "not_reported"
    out, teams = _usage(store)
    assert out["cost_source"] == "gateway_reported" and out["currency"] == "USD"
    assert teams["team-beta"]["cost_usd"] is None
    assert teams["team-beta"]["cost_not_reported"] == 1
    assert out["totals"]["cost_usd"] is None
    # The label is the one cost vocabulary every other surface uses
    # (clawmetry/cost_basis.py): measured from what LiteLLM reported, usage
    # value at the rates LiteLLM applied, never an invoice or a contract rate.
    from clawmetry import provenance
    provenance.assert_labelled(out, "gateway usage")
    for path in ("totals.cost_usd", "teams[].cost_usd", "teams[].users[].cost_usd"):
        spend = out["provenance"][path]
        assert (spend["basis"], spend["cost_basis"]) == ("measured", "published_rate"), path
        assert "LiteLLM" in spend["rate_source"] and "does not re-price" in spend["rate_source"]
    # A null reads "not reported", not a free request.
    assert out["provenance"]["not_reported"]["cost_basis"] == "unknown"
    # The price book (#5959) speaks the same language: a gateway figure is
    # ``vendor_reported``, and the price book's own mapping of that is the
    # basis on the badge, so the two surfaces cannot drift apart.
    from clawmetry import price_book
    assert out["priced_from"] == "vendor_reported" and out["priced_from"] in price_book.PRICED_FROM
    assert out["provenance"]["totals.cost_usd"]["cost_basis"] == \
        price_book.financial_basis(out["priced_from"], 1.0)["cost_basis"]

    _post(_only(_payload(), {ALPHA_ORIGINAL_SPAN}))
    rec = _record(store, ALPHA_ORIGINAL_SPAN)
    assert rec["cost_source"] == "gateway_reported"
    assert rec["cost_usd"] == pytest.approx(1.35e-05)
    # The span row carries no cost: the gateway figure lives in the ledger only.
    assert store._fetch(
        "SELECT COUNT(*) FROM spans WHERE agent_type = ? AND cost_usd IS NOT NULL", [gw.GATEWAY_SOURCE]
    )[0][0] == 0


# ── AC-OBS-GWY-001.5 ─────────────────────────────────────────────────────────

def test_redelivery_and_restart_change_nothing_and_a_separate_request_counts(store):
    data = _payload()
    _post(data)
    first, _ = _usage(store)
    _post(data)
    again, _ = _usage(store)
    assert again["totals"] == first["totals"]

    path = str(_ls.DB_PATH)
    store.stop(flush=True)
    reopened = _ls.LocalStore()
    store.holder["store"] = reopened
    after_restart, _ = _usage(reopened)
    assert after_restart["totals"] == first["totals"]

    extra = _only(_payload(), {ALPHA_ORIGINAL_SPAN})
    s = _span(extra, ALPHA_ORIGINAL_SPAN)
    s["spanId"] = "bbbbbbbbbbbbbbbb"
    s["traceId"] = "cccccccccccccccccccccccccccccccc"
    _set_attr(s, "gen_ai.response.id", "chatcmpl-a-second-billable-attempt")
    _post(extra)
    later, teams = _usage(reopened)
    assert later["totals"]["requests"] == first["totals"]["requests"] + 1
    assert later["totals"]["cost_usd"] == pytest.approx(first["totals"]["cost_usd"] + 1.35e-05)
    assert path == str(_ls.DB_PATH)


# ── AC-OBS-GWY-001.6 ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("order", ["original_first", "replay_first"])
def test_a_cache_replay_is_not_charged_in_either_arrival_order(store, order):
    data = _payload()
    original = _only(data, {ALPHA_ORIGINAL_SPAN})
    replay = _only(data, {ALPHA_REPLAY_SPAN})
    # Precondition from the real proxy: the replay repeats the response id and
    # still reports the full model cost on its span.
    assert _attr(_span(data, ALPHA_REPLAY_SPAN), "gen_ai.response.id") == ALPHA_RESPONSE
    assert _attr(_span(data, ALPHA_REPLAY_SPAN), "gen_ai.cost.total_cost") == pytest.approx(1.35e-05)
    for batch in ((original, replay) if order == "original_first" else (replay, original)):
        _post(batch)
    _, teams = _usage(store)
    alpha = teams["team-alpha"]
    assert alpha["requests"] == 2
    assert alpha["cache_replays"] == 1
    assert alpha["cost_usd"] == pytest.approx(1.35e-05)
    assert (alpha["tokens_input"], alpha["tokens_output"]) == (10, 20)


# ── AC-OBS-GWY-001.7 ─────────────────────────────────────────────────────────

def test_gateway_is_a_separate_subtotal_not_an_agent(store):
    _post(_payload())
    assert store._fetch("SELECT COUNT(*) FROM sessions", [])[0][0] == 0
    kinds = store._fetch(
        "SELECT agent_type, COUNT(*), COUNT(session_id) FROM spans GROUP BY agent_type", [])
    assert kinds == [(gw.GATEWAY_SOURCE, 11, 0)]
    assert store.query_otlp_app_rollup() == []
    assert store.query_otlp_rollup(dimension="team") == []
    # The Agents tab (and the cloud relay of the same shape) never draws the
    # proxy as an agent node, whatever runtime filter is selected.
    for rt in (None, "all", gw.GATEWAY_SOURCE):
        graph = store.query_agent_graph(runtime=rt)
        assert graph["nodes"] == [] and graph["edges"] == [], (rt, graph)

    out, _ = _usage(store)
    assert (out["totals"]["correlated"], out["totals"]["uncorrelated"]) == (0, 5)

    # An agent that propagated its trace context to the proxy: its own span on
    # the streamed request's trace. It still becomes the agent's session (the
    # generic path is untouched) and the one gateway request is correlated.
    now = time.time_ns()
    agent = {"resourceSpans": [{
        "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "ci-agent"}}]},
        "scopeSpans": [{"scope": {"name": "ci-agent"}, "spans": [{
            "traceId": SHARED_TRACE, "spanId": "00f067aa0ba902b7", "name": "agent.turn",
            "startTimeUnixNano": str(now - 10**9), "endTimeUnixNano": str(now),
            "attributes": [],
        }]}],
    }]}
    _post(agent)
    out, _ = _usage(store)
    assert (out["totals"]["correlated"], out["totals"]["uncorrelated"]) == (1, 4)
    assert store._fetch(
        "SELECT COUNT(*) FROM sessions WHERE session_id = ?", ["ci_agent:trace:" + SHARED_TRACE]
    )[0][0] == 1
    assert [r["agent_type"] for r in store.query_otlp_app_rollup()] == ["ci_agent"]
    assert [n["agent_type"] for n in store.query_agent_graph()["nodes"]] == ["ci_agent"]


AZURE_URL = (
    "https://contoso-east.openai.azure.com/openai/deployments/prod-chat/"
    "chat/completions?api-version=2024-10-21"
)


def test_an_azure_call_the_proxy_makes_is_not_priced_again_by_the_interceptor(store, monkeypatch):
    """#5959 taught the interceptor to capture Azure OpenAI. A LiteLLM proxy
    routing to an Azure deployment makes exactly that call, so with the
    interceptor loaded in the proxy the same request would be priced three
    times: the agent's own cost, the gateway record, and the interceptor row."""
    import sys
    import types
    from clawmetry import interceptor as ci

    args = ("azure-openai", AZURE_URL, "gpt-4o-mini", 1000, 50, 12.0, 200, "httpx")
    # An ordinary app calling Azure directly: priced, as #5959 ships it.
    monkeypatch.delitem(sys.modules, ci._LITELLM_PROXY_MODULE, raising=False)
    direct = ci._build_event(*args)
    assert direct["cost_usd"] > 0 and "via_gateway" not in direct

    # The same call from inside a LiteLLM proxy: recorded, not priced, and
    # pointing at the gateway that holds the figure.
    monkeypatch.setitem(sys.modules, ci._LITELLM_PROXY_MODULE,
                        types.ModuleType(ci._LITELLM_PROXY_MODULE))
    proxied = ci._build_event(*args)
    assert "cost_usd" not in proxied
    assert proxied["via_gateway"] == gw.GATEWAY_SOURCE
    assert (proxied["deployment"], proxied["input_tokens"]) == ("prod-chat", 1000)

    # End to end: the gateway record and the interceptor row for one request.
    _post(_only(_payload(), {ALPHA_ORIGINAL_SPAN}))
    before, _ = _usage(store)
    assert before["totals"]["cost_usd"] == pytest.approx(1.35e-05)
    store.ingest_external_call(dict(proxied, host=proxied["provider"]), "node-1")
    after, _ = _usage(store)
    assert after["totals"] == before["totals"]
    assert store._fetch("SELECT COUNT(*), COALESCE(SUM(cost_usd), 0) FROM external_api_calls", []) \
        == [(1, 0.0)]
    # And neither leg reaches an agent total.
    assert store.query_otlp_app_rollup() == []
    assert store._fetch("SELECT COUNT(*) FROM sessions", [])[0][0] == 0


def test_usage_by_team_route_serves_the_gateway_block_separately(store, monkeypatch):
    from flask import Flask
    lq = importlib.import_module("routes.local_query")
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    usage_mod = importlib.import_module("routes.usage")
    app = Flask(__name__)
    app.register_blueprint(usage_mod.bp_usage)
    _post(_payload())
    body = app.test_client().get("/api/usage/by-team?window=7").get_json()
    assert body["gateway"]["available"] is True
    assert body["gateway"]["totals"]["requests"] == 5
    assert all("litellm" not in json.dumps(t) for t in body["teams"])

    monkeypatch.setattr(_ls, "get_store", lambda read_only=False: (_ for _ in ()).throw(RuntimeError("down")))
    body = app.test_client().get("/api/usage/by-team?window=7").get_json()
    assert body["gateway"] == {"available": False}


# ── AC-OBS-GWY-001.8 ─────────────────────────────────────────────────────────

def test_failed_requests_are_counted_per_team(store):
    _post(_payload())
    rec = _record(store, BETA_FAILED_SPAN)
    assert rec["success"] is False
    assert rec["cost_usd"] is None
    assert rec["attributes"]["error_type"] == "InternalServerError"
    _, teams = _usage(store)
    assert teams["team-beta"]["failed"] == 1
    assert teams["team-alpha"]["failed"] == 0
    # A failure is not "succeeded without a cost".
    assert teams["team-beta"]["cost_not_reported"] == 0


# ── AC-OBS-GWY-001.9 ─────────────────────────────────────────────────────────

def test_usage_tab_escapes_gateway_and_team_labels():
    js = (pathlib.Path(__file__).resolve().parent.parent / "clawmetry" / "static" / "js" / "app.js").read_text()
    start = js.index("function costCardText(s)")
    end = js.index("async function loadCostForecast()")
    block = js[start:end]
    # The escaper replaces all five characters that can open markup or break
    # out of an attribute.
    helper = block[:block.index("\n}\n")]
    for ch in ("&amp;", "&lt;", "&gt;", "&quot;", "&#39;"):
        assert ch in helper, ch
    assert block.index("function costCardText(s)") < block.index("async function loadUsageByTeam()")
    for needle in ("costCardText(name)", "costCardText(who + key)", "costCardText(t.label || '—')",
                   "costCardText(rts)", "notes.map(costCardText)"):
        assert needle in block, needle
    # No label, alias, email or key name is concatenated straight after a
    # piece of markup. The pre-fix card did exactly this with ``t.label``.
    raw = re.findall(
        r">'\s*\+\s*\(?\s*(?:t\.label|team\.team_alias|team\.team\b|u\.user_email|u\.user_id|u\.key_alias|name\b|who\b|rts\b)",
        block,
    )
    assert raw == [], raw


# ── AC-OBS-GWY-001.10 ────────────────────────────────────────────────────────

def test_per_team_totals_reconcile_with_litellm_spend_log(store):
    _post(_payload())
    _, teams = _usage(store)
    spend = json.loads((FIX / "spend_logs.json").read_text())
    by_team = {}
    for row in spend:
        t = by_team.setdefault(row["team_id"], {"requests": 0, "spend": 0.0, "failed": 0})
        t["requests"] += 1
        t["spend"] += row["spend"]
        t["failed"] += row["status"] == "failure"
    assert set(by_team) == set(teams)
    for team_id, theirs in by_team.items():
        ours = teams[team_id]
        assert ours["requests"] == theirs["requests"], team_id
        assert ours["failed"] == theirs["failed"], team_id
        assert abs((ours["cost_usd"] or 0.0) - theirs["spend"]) < 1e-12, (team_id, ours["cost_usd"], theirs["spend"])


# ── recognition boundaries (controls) ────────────────────────────────────────

def test_the_json_decoder_exposes_the_instrumentation_scope():
    from clawmetry.otlp_json import decode
    req = decode(json.dumps(_payload()).encode(), "traces")
    names = {ss.scope.name for rs in req.resource_spans for ss in rs.scope_spans}
    assert names == {"litellm"}


def test_spans_that_are_not_litellm_telemetry_take_the_generic_path(store):
    data = _payload()
    for rs in data["resourceSpans"]:
        for ss in rs["scopeSpans"]:
            ss["scope"]["name"] = "some-other-library"
    _post(data)
    assert store._fetch("SELECT COUNT(*) FROM otlp_records", [])[0][0] == 0
    assert store._fetch(
        "SELECT COUNT(*) FROM spans WHERE agent_type = ?", [gw.GATEWAY_SOURCE])[0][0] == 0


def test_a_litellm_sdk_call_without_proxy_auth_is_not_a_gateway_request():
    sdk = {"llm.request.type": "completion", "metadata.user_api_key_hash": "",
           "metadata.user_api_key_request_route": "", "gen_ai.cost.total_cost": 0.01}
    assert gw.is_billable_request(sdk) is False
    assert gw.ledger_record(attrs=sdk, resource_attrs={}, trace_id="t", span_id="s",
                            parent_span_id=None, start_ts=1.0, duration_ms=1.0,
                            status_code=0, received_at=1.0) is None
    assert gw.is_litellm_telemetry("litellm", {}) is False
