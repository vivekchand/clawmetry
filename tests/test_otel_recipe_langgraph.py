"""LangGraph + OpenLLMetry recipe: a run is one session, checked on real exports.

REQ-OBS-OTR-001, Factory requirement
https://factory.8090.ai/project/b415065f-ab2f-4f53-8864-0c009fd098cb/requirements/0130f6a6-3f5b-448f-bd59-d8820a4d5c88
Refs vivekchand/clawmetry#5939.

The fixtures under ``tests/fixtures/otel/`` are NOT hand-written. They are the
OTLP export of ``examples/otel/langgraph/agent.py`` itself, captured with
langgraph 1.2.11, langchain-core 1.6.3, opentelemetry-instrumentation-langchain
0.62.3 and opentelemetry-sdk 1.44.0 (encoded by the SDK's own OTLP encoder,
ids written as OTLP/JSON hex, string values over 300 chars truncated):

  * ``..._thread.json``   ``agent.py --thread support-42``
  * ``..._stream.json``   ``agent.py --thread support-42 --stream``
  * ``..._nothread.json`` ``agent.py``

What that instrumentation really sends, and why this file exists: the thread
is stamped as ``gen_ai.conversation.id`` on the top ``invoke_agent`` span ONLY.
The nine spans beneath it (both model calls with all the tokens, and the tool
call) carry it as ``traceloop.association.properties.thread_id``. Before the
fix the receiver read only the conversation id, so one run became TWO
sessions: ``support-42`` with 0 tokens, and ``invoice_agent:trace:<id>`` with
all 307 tokens and the tool call. Measured on a live dashboard first.

The live half of the guard is ``scripts/verify_otel_recipe_langgraph.py``, run
by ci.yml's ``otel-recipe-langgraph`` job against a real dashboard with the
recipe's pinned dependencies.

Acceptance criteria -> tests:

  AC-OBS-OTR-001.1  test_recipe_ships_one_tool_agent_that_needs_no_key
  AC-OBS-OTR-001.2  test_ci_job_runs_the_recipe_with_pinned_versions,
                    test_thread_run_is_one_session_with_every_span
  AC-OBS-OTR-001.3  test_thread_run_is_one_session_with_every_span,
                    test_second_run_on_the_thread_joins_the_same_session
  AC-OBS-OTR-001.4  test_sent_conversation_id_wins_over_thread,
                    test_thread_wins_over_session_id_on_span_or_resource
  AC-OBS-OTR-001.5  test_no_thread_is_one_session_per_trace
  AC-OBS-OTR-001.6  test_streamed_run_matches_invoked_run
  AC-OBS-OTR-001.7  test_ci_job_proves_remote_bearer_auth
  AC-OBS-OTR-001.8  test_recipe_page_records_what_was_verified
"""

from __future__ import annotations

import copy
import importlib
import json
import os
import re

import pytest
from flask import Flask

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = os.path.join(REPO, "tests", "fixtures", "otel")
APP = "invoice_agent"
THREAD = "support-42"
RUN_TOKENS = 120 + 18 + 160 + 9  # what the recipe's stub model reports per run
PINS = {
    "langgraph": "1.2.11",
    "langchain-core": "1.6.3",
    "opentelemetry-instrumentation-langchain": "0.62.3",
    "opentelemetry-sdk": "1.44.0",
    "opentelemetry-exporter-otlp-proto-http": "1.44.0",
}


def _fixture(name: str) -> dict:
    with open(os.path.join(FIX, f"langgraph_openllmetry_0_62_3_{name}.json"), encoding="utf-8") as f:
        return json.load(f)


def _spans_of(payload: dict) -> list:
    return [s for rs in payload["resourceSpans"] for ss in rs["scopeSpans"] for s in ss["spans"]]


def _attr(span: dict, key: str):
    for a in span.get("attributes") or []:
        if a["key"] == key:
            return a["value"]
    return None


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    # Hermetic: never reach a host daemon's store.
    monkeypatch.setattr(ls, "_daemon_registered", lambda *a, **k: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    import routes.meta as meta
    importlib.reload(meta)
    a = Flask(__name__)
    a.register_blueprint(meta.bp_otel)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _post(app_obj, payload: dict) -> None:
    resp = app_obj.test_client().post("/v1/traces", data=json.dumps(payload),
                                      content_type="application/json")
    assert resp.status_code == 200, resp.data


def _sessions(ls) -> dict:
    rows = ls.get_store()._fetch(
        "SELECT session_id, agent_type, total_tokens, message_count FROM sessions"
        " WHERE agent_type = ?", [APP])
    return {r[0]: {"agent_type": r[1], "total_tokens": int(r[2] or 0),
                   "message_count": int(r[3] or 0)} for r in rows}


def _span_rows(ls) -> list:
    return ls.get_store()._fetch(
        "SELECT name, session_id, trace_id, tool_name, tokens_input, tokens_output"
        " FROM spans WHERE agent_type = ?", [APP])


# ── the fixtures really are the shape this guard is about ───────────────────

def test_fixture_is_the_split_shape_openllmetry_emits():
    """If a future capture no longer has this shape, the guard below would
    pass for the wrong reason, so pin the shape itself."""
    spans = _spans_of(_fixture("thread"))
    assert len(spans) == 10
    top = [s for s in spans if s["name"].startswith("invoke_agent")]
    assert len(top) == 1
    assert _attr(top[0], "gen_ai.conversation.id") == {"stringValue": THREAD}
    below = [s for s in spans if s is not top[0]]
    assert all(_attr(s, "gen_ai.conversation.id") is None for s in below)
    tokened = [s for s in below if _attr(s, "gen_ai.usage.input_tokens")]
    assert len(tokened) == 2
    assert all(_attr(s, "traceloop.association.properties.thread_id") == {"stringValue": THREAD}
               for s in tokened)
    assert any(_attr(s, "gen_ai.tool.name") == {"stringValue": "lookup_invoice"} for s in below)


# ── AC-OBS-OTR-001.3 / .2: one run, one session, every span ─────────────────

def test_thread_run_is_one_session_with_every_span(app):
    a, ls = app
    _post(a, _fixture("thread"))
    sessions = _sessions(ls)
    assert list(sessions) == [THREAD], (
        f"one LangGraph run was filed under {sorted(sessions)}; the top span and "
        "the spans beneath it must resolve to the thread's session")
    assert sessions[THREAD]["total_tokens"] == RUN_TOKENS
    assert sessions[THREAD]["message_count"] == 2
    rows = _span_rows(ls)
    assert len(rows) == 10
    assert {r[1] for r in rows} == {THREAD}
    assert [r[3] for r in rows if r[3]] == ["lookup_invoice"]
    assert sum(int(r[4] or 0) for r in rows) == 280
    assert sum(int(r[5] or 0) for r in rows) == 27


def test_second_run_on_the_thread_joins_the_same_session(app):
    a, ls = app
    _post(a, _fixture("thread"))
    _post(a, _fixture("stream"))  # a different trace on the same thread
    sessions = _sessions(ls)
    assert list(sessions) == [THREAD]
    assert sessions[THREAD]["total_tokens"] == 2 * RUN_TOKENS
    assert len({r[2] for r in _span_rows(ls)}) == 2


# ── AC-OBS-OTR-001.6: streaming is the same as invoke ───────────────────────

def test_streamed_run_matches_invoked_run(app):
    a, ls = app
    stream, invoke = _fixture("stream"), _fixture("thread")
    assert {s["traceId"] for s in _spans_of(stream)} != {s["traceId"] for s in _spans_of(invoke)}
    assert sorted(s["name"] for s in _spans_of(stream)) == sorted(s["name"] for s in _spans_of(invoke))
    _post(a, stream)
    sessions = _sessions(ls)
    assert list(sessions) == [THREAD]
    assert sessions[THREAD]["total_tokens"] == RUN_TOKENS
    assert [r[3] for r in _span_rows(ls) if r[3]] == ["lookup_invoice"]


# ── AC-OBS-OTR-001.5: no thread, one session per trace ──────────────────────

def test_no_thread_is_one_session_per_trace(app):
    a, ls = app
    payload = _fixture("nothread")
    assert all(_attr(s, "traceloop.association.properties.thread_id") is None
               and _attr(s, "gen_ai.conversation.id") is None for s in _spans_of(payload))
    _post(a, payload)
    trace_id = _spans_of(payload)[0]["traceId"]
    sessions = _sessions(ls)
    assert list(sessions) == [f"{APP}:trace:{trace_id}"]
    assert sessions[f"{APP}:trace:{trace_id}"]["total_tokens"] == RUN_TOKENS


# ── AC-OBS-OTR-001.4: precedence ────────────────────────────────────────────

def test_sent_conversation_id_wins_over_thread(app):
    a, ls = app
    payload = copy.deepcopy(_fixture("thread"))
    for s in _spans_of(payload):
        s["attributes"] = [x for x in s["attributes"] if x["key"] != "gen_ai.conversation.id"]
        s["attributes"].append({"key": "gen_ai.conversation.id",
                                "value": {"stringValue": "Conv-ABC"}})
    _post(a, payload)
    assert list(_sessions(ls)) == ["Conv-ABC"], "a sent conversation id must be recorded as sent"


@pytest.mark.parametrize("where", ["resource", "span"])
def test_thread_wins_over_session_id_on_span_or_resource(app, where):
    """A ``session.id`` must not pull the spans beneath the top span away from
    the conversation id the top span itself sends, whether it arrives as a
    process-wide resource attribute or is stamped on every span by the app.

    The span case is the one that matters: ``_pick`` checks span attributes
    before resource attributes per key, so if ``session.id`` were listed
    before the thread key, the children would resolve to ``session.id`` while
    the top span resolved to its conversation id, and the run would split."""
    a, ls = app
    payload = copy.deepcopy(_fixture("thread"))
    sid = {"key": "session.id", "value": {"stringValue": "app-session-7"}}
    if where == "resource":
        payload["resourceSpans"][0]["resource"]["attributes"].append(sid)
    else:
        for s in _spans_of(payload):
            s["attributes"].append(copy.deepcopy(sid))
    _post(a, payload)
    sessions = _sessions(ls)
    assert list(sessions) == [THREAD], (
        f"session.id on the {where} split or re-keyed the run: {sorted(sessions)}")
    assert sessions[THREAD]["total_tokens"] == RUN_TOKENS
    assert {r[1] for r in _span_rows(ls)} == {THREAD}


# ── AC-OBS-OTR-001.1 / .2 / .7 / .8: the recipe, its CI job, its page ───────

def test_recipe_ships_one_tool_agent_that_needs_no_key():
    src = open(os.path.join(REPO, "examples", "otel", "langgraph", "agent.py"), encoding="utf-8").read()
    assert src.count("@tool(") == 1
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" in src
    assert "LangchainInstrumentor().instrument(" in src
    assert "API_KEY" not in src, "the recipe must run with no provider key"


def _direct_pins(text: str) -> dict:
    return dict(re.findall(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)", text, flags=re.M))


def test_ci_job_runs_the_recipe_with_pinned_versions():
    example = _direct_pins(open(os.path.join(
        REPO, "examples", "otel", "langgraph", "requirements.txt"), encoding="utf-8").read())
    assert example == PINS
    lock = _direct_pins(open(os.path.join(
        REPO, ".github", "requirements", "otel-recipe-langgraph.txt"), encoding="utf-8").read())
    for name, ver in PINS.items():
        assert lock.get(name) == ver, f"CI lockfile pins {name}=={lock.get(name)}, recipe says {ver}"
    ci = open(os.path.join(REPO, ".github", "workflows", "ci.yml"), encoding="utf-8").read()
    job = ci.split("\n  otel-recipe-langgraph:\n", 1)
    assert len(job) == 2, "ci.yml has no otel-recipe-langgraph job"
    body = job[1].split("\n  # ──", 1)[0]
    assert "--require-hashes -r .github/requirements/otel-recipe-langgraph.txt" in body
    assert "scripts/verify_otel_recipe_langgraph.py" in body
    assert "continue-on-error" not in body


def test_ci_job_proves_remote_bearer_auth():
    ci = open(os.path.join(REPO, ".github", "workflows", "ci.yml"), encoding="utf-8").read()
    body = ci.split("\n  otel-recipe-langgraph:\n", 1)[1].split("\n  # ──", 1)[0]
    assert "--remote-url" in body
    verifier = open(os.path.join(REPO, "scripts", "verify_otel_recipe_langgraph.py"), encoding="utf-8").read()
    assert "Authorization=Bearer" in verifier and "!= 401" in verifier


def test_recipe_page_records_what_was_verified():
    page = open(os.path.join(REPO, "docs", "OTEL_RECIPE_LANGGRAPH.md"), encoding="utf-8").read()
    for name, ver in PINS.items():
        assert f"`{name}` | {ver}" in page, f"page does not record {name} {ver}"
    for needle in ("http/protobuf", "Authorization=Bearer", "gen_ai.conversation.id",
                   "traceloop.association.properties.thread_id", ":trace:",
                   "invoke_agent", "execute_tool", "service.name",
                   "Sessions", "Tracing", "Usage", "Guard", "cannot pause"):
        assert needle in page, f"recipe page is missing {needle!r}"
