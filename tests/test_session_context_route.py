"""GET /api/sessions/<id>/context: DuckDB-only inputs & context endpoint.

Temp store only. Asserts the response contract the Transcripts "What the
agent was given" panel and the cloud interceptor render from: measured items
per kind with parsed tool names, the adapter's honest coverage declaration
(openclaw = full, an unknown runtime = unknown), the runtime filter, and the
400 on a path-shaped id.
"""
from __future__ import annotations

import importlib
import json

import pytest
from flask import Flask


SID = "11111111-2222-3333-4444-555555555555"


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "ctx.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    a = Flask(__name__)
    a.register_blueprint(sessions_mod.bp_sessions)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _seed(ls, sid=SID, agent_type="openclaw"):
    st = ls.get_store()
    st.ingest({
        "id": f"{sid}:ctx:1", "agent_type": agent_type, "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "context.compiled", "ts": "2026-09-04T10:00:00Z",
        "model": "claude-sonnet-4-5",
        "data": {
            "type": "context.compiled", "sessionId": sid, "workspaceDir": "/w",
            "provider": "anthropic", "modelId": "claude-sonnet-4-5",
            "data": {
                "systemPrompt": "Be careful. password: hunter2secret",
                "prompt": "ship it",
                "tools": [{"name": "read"}, {"name": "bash"}],
                "messages": [], "transport": "sdk", "streamStrategy": "auto", "imagesCount": 0,
            },
        },
    })
    st._flush_now()


def test_context_endpoint_returns_measured_items(app):
    a, ls = app
    _seed(ls)
    r = a.test_client().get(f"/api/sessions/{SID}/context")
    assert r.status_code == 200
    body = r.get_json()
    assert body["session_id"] == SID
    assert body["runtime"] == "openclaw"
    assert body["basis"] == "measured"
    assert body["coverage"]["inputs"] == "full"
    assert "context.compiled" in body["coverage"]["note"]
    kinds = {it["kind"]: it for it in body["items"]}
    assert set(kinds) == {"system_prompt", "user_prompt", "tools_available", "runtime_meta"}
    assert kinds["tools_available"]["names"] == ["bash", "read"]
    assert kinds["runtime_meta"]["meta"]["transport"] == "sdk"
    assert kinds["runtime_meta"]["meta"]["model"] == "claude-sonnet-4-5"
    sp = kinds["system_prompt"]
    assert "hunter2secret" not in sp["content"]
    assert sp["size_bytes"] == len("Be careful. password: hunter2secret".encode())
    assert len(sp["sha256"]) == 64
    assert kinds["user_prompt"]["content"] == "ship it"
    # tool definitions never ride the response as content
    assert kinds["tools_available"]["content"] is None


def test_runtime_filter_is_honoured(app):
    a, ls = app
    _seed(ls)
    c = a.test_client()
    ok = c.get(f"/api/sessions/{SID}/context?runtime=openclaw").get_json()
    assert ok["count"] == 4
    other = c.get(f"/api/sessions/{SID}/context?runtime=codex").get_json()
    assert other["count"] == 0
    assert other["runtime"] == "codex"
    # No adapter for codex in the OSS process: the coverage says unknown, not none.
    assert other["coverage"]["inputs"] in ("unknown", "none", "partial", "full")
    allv = c.get(f"/api/sessions/{SID}/context?runtime=all").get_json()
    assert allv["count"] == 4


def test_empty_session_has_honest_shape(app):
    a, _ls = app
    body = a.test_client().get("/api/sessions/no-such-session/context").get_json()
    assert body["items"] == []
    assert body["count"] == 0
    assert body["coverage"]["inputs"] in ("full", "partial", "none", "unknown")


def test_prefixed_family_id_resolves_runtime(app):
    a, ls = app
    sid = "claude_code:aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
    st = ls.get_store()
    st.ingest({
        "id": "cc:1", "agent_type": "claude_code", "node_id": "n", "agent_id": "main",
        "session_id": sid, "event_type": "context.compiled", "ts": "2026-09-04T10:00:00Z",
        "data": {"role": "", "content": "", "extra": {"tools": ["Bash"], "runtimeMeta": {"cwd": "/p"}}},
    })
    st._flush_now()
    body = a.test_client().get(f"/api/sessions/{sid}/context").get_json()
    assert body["runtime"] == "claude_code"
    assert {it["kind"] for it in body["items"]} == {"tools_available", "runtime_meta"}
    # bare id (as the transcript viewer holds it) finds the same rows
    bare = a.test_client().get("/api/sessions/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/context").get_json()
    assert bare["count"] == 2


def test_bad_session_id_is_400(app):
    a, _ls = app
    assert a.test_client().get("/api/sessions/..%2Fetc/context").status_code in (400, 404)
    assert a.test_client().get("/api/sessions/a%5Cb/context").status_code in (400, 404)


def test_shape_is_in_query_contract_and_daemon_allowlist():
    from clawmetry import query_contract as qc
    from routes import local_query as lq
    assert qc.QUERY_CONTRACT["session_context"]["status"] == qc.STATUS_LIVE
    assert qc.QUERY_CONTRACT["session_context"]["trust"] == qc.TRUST_E2E
    assert lq._SHAPES["session_context"] == "query_session_context"
    assert "query_session_context" in lq._DAEMON_METHODS
    assert lq._coerce_args("session_context", {"session_id": "s", "limit": "9999"})["limit"] == 1000
    with pytest.raises(ValueError):
        lq._coerce_args("session_context", {})


def test_adapter_seam_declares_inputs():
    from clawmetry.adapters.base import Capability, AgentAdapter
    from clawmetry.adapters.openclaw import OpenClawAdapter
    from clawmetry.adapters.nemo import NemoClawAdapter
    assert Capability.INPUTS.value == "inputs"
    assert Capability.REASONING.value == "reasoning"
    assert AgentAdapter.trail_coverage(OpenClawAdapter()) == {"inputs": "none", "reasoning": "none", "note": ""}
    oc = OpenClawAdapter().trail_coverage()
    assert oc["inputs"] == "full" and Capability.INPUTS in OpenClawAdapter().capabilities()
    nemo = NemoClawAdapter().trail_coverage()
    assert nemo["inputs"] == "none" and nemo["note"]
    assert Capability.INPUTS not in NemoClawAdapter().capabilities()


def test_locale_strings_have_no_em_dashes():
    import pathlib
    p = pathlib.Path(__file__).resolve().parents[1] / "clawmetry" / "static" / "locales" / "en.json"
    d = json.loads(p.read_text())
    inputs = {k: v for k, v in d.items() if k.startswith("inputs.")}
    assert inputs["inputs.title"] == "What the agent was given"
    assert "{runtime}" in inputs["inputs.not_exposed"]
    for k, v in inputs.items():
        assert "—" not in v and " -- " not in v, k
