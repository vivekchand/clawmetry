"""Unit tests for the openclaw/nemoclaw observability-gap fixes that are pure
filesystem/parse functions (no DuckDB, so they run anywhere — the store-backed
ingest paths are exercised by the existing sync/ingest suites).

Covers:
- #2604 parse_talk_lifecycle_line — talk attrs live in a NESTED positional arg
  (tslog), not top-level; the parser must find them wherever tslog put them.
- #2684 _read_nemoclaw_sandbox_routing — per-sandbox model routing must match
  the harness getSandboxInferenceConfig switch (compatible-anthropic-endpoint
  with the default api routes to the MANAGED 'inference' provider).
- #2608 _model_router_fingerprint — parse git:<sha> from the fingerprint file.
"""
import json
import os
import sys
import types

import pytest

from clawmetry.sync import parse_talk_lifecycle_line, _read_nemoclaw_sandbox_routing
from clawmetry.adapters.openclaw import _model_router_fingerprint


# -- #2604 talk parser -------------------------------------------------------

def test_talk_parser_reads_nested_positional_attrs():
    # tslog: o["0"] is the binding prefix, o["1"] is the logged attrs object.
    rec = json.dumps({
        "0": {"subsystem": "talk"},
        "1": {"sessionId": "s1", "talkEventType": "session.start",
              "talkMode": "voice", "talkTransport": "webrtc",
              "talkBrain": "gpt-realtime", "talkProvider": "openai",
              "talkFinal": True, "talkDurationMs": 1200, "talkByteLength": 4096},
        "_meta": {"name": "{\"subsystem\":\"talk\"}", "date": "2026-06-05T00:00:00Z"},
        "message": "talk event session.start",
    })
    r = parse_talk_lifecycle_line(rec)
    assert r is not None
    assert r["event_type"] == "session.start"
    assert r["session_id"] == "s1"
    assert r["mode"] == "voice" and r["transport"] == "webrtc"
    assert r["duration_ms"] == 1200 and r["byte_length"] == 4096
    assert r["final"] is True


def test_talk_parser_handles_json_string_positional():
    rec = json.dumps({"0": "{\"subsystem\":\"talk\"}",
                      "1": "{\"sessionId\":\"s2\",\"talkEventType\":\"tool.error\"}"})
    r = parse_talk_lifecycle_line(rec)
    assert r and r["session_id"] == "s2" and r["event_type"] == "tool.error"


def test_talk_parser_back_compatible_with_top_level():
    r = parse_talk_lifecycle_line(json.dumps(
        {"talkEventType": "session.end", "sessionId": "s3", "time": "t"}))
    assert r and r["session_id"] == "s3" and r["event_type"] == "session.end"


def test_talk_parser_rejects_non_talk_and_garbage():
    assert parse_talk_lifecycle_line(json.dumps({"message": "hi"})) is None
    assert parse_talk_lifecycle_line(json.dumps({"message": "talkative user"})) is None
    assert parse_talk_lifecycle_line("not json") is None
    assert parse_talk_lifecycle_line("") is None


# -- #2684 sandbox routing ---------------------------------------------------

@pytest.fixture
def nemoclaw_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    (tmp_path / ".nemoclaw").mkdir()
    return tmp_path


def _write_sandboxes(home, sandboxes, default=None):
    payload = {"sandboxes": sandboxes}
    if default:
        payload["defaultSandbox"] = default
    (home / ".nemoclaw" / "sandboxes.json").write_text(json.dumps(payload))


def test_sandbox_routing_matches_harness_switch(nemoclaw_home):
    _write_sandboxes(nemoclaw_home, {
        "a": {"provider": "openai-api", "model": "gpt-5"},
        "b": {"provider": "compatible-anthropic-endpoint", "model": "claude-x"},
        "c": {"provider": "compatible-anthropic-endpoint", "model": "claude-y",
              "preferredInferenceApi": "anthropic-messages"},
        "d": {"provider": "anthropic-prod", "model": "claude-z"},
        "e": {"provider": "some-future-provider", "model": "m"},
    }, default="a")
    by = {r["sandbox"]: r for r in _read_nemoclaw_sandbox_routing()}
    assert by["a"]["providerKey"] == "openai"
    # compatible-anthropic-endpoint + default api -> MANAGED inference (not anthropic)
    assert by["b"]["providerKey"] == "inference"
    # only an explicit non-default api makes it a real anthropic route
    assert by["c"]["providerKey"] == "anthropic"
    assert by["d"]["providerKey"] == "anthropic"
    assert by["e"]["providerKey"] == "inference"  # unknown -> managed default
    assert by["a"]["isDefault"] is True and by["b"]["isDefault"] is False


def test_sandbox_routing_missing_file_returns_empty(nemoclaw_home):
    assert _read_nemoclaw_sandbox_routing() == []


def test_sandbox_routing_malformed_is_skipped(nemoclaw_home):
    (nemoclaw_home / ".nemoclaw" / "sandboxes.json").write_text("{ not json")
    assert _read_nemoclaw_sandbox_routing() == []


# -- #2608 model-router fingerprint ------------------------------------------

def test_model_router_fingerprint_parses_git_sha(tmp_path, monkeypatch):
    venv = tmp_path / "mrv"
    venv.mkdir()
    (venv / ".nemoclaw-source-fingerprint").write_text(
        "git:0123456789abcdef0123456789abcdef01234567\n")
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(venv))
    out = _model_router_fingerprint()
    assert out["modelRouterFingerprintKind"] == "git"
    assert out["modelRouterSourceSha"] == "0123456789ab"
    assert out["modelRouterFingerprint"].startswith("git:")


def test_model_router_fingerprint_absent_returns_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("NEMOCLAW_MODEL_ROUTER_VENV", str(tmp_path / "nope"))
    assert _model_router_fingerprint() == {}


# -- #2795 model-router proxy liveness ---------------------------------------

def test_model_router_port_parsed_from_cmdline(monkeypatch):
    # No need to spawn a real process — feed a fake /proc-style cmdline scan.
    import clawmetry.adapters.openclaw as oc

    class _FakeProc:
        def __init__(self, cmd):
            self.info = {"cmdline": cmd}

    fake = [
        _FakeProc(["node", "server.js"]),
        _FakeProc(["model-router", "proxy", "--port", "48123"]),
    ]
    fake_psutil = types.SimpleNamespace(process_iter=lambda fields: fake)
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    assert oc._discover_model_router_port() == 48123


def test_model_router_port_supports_equals_form(monkeypatch):
    import clawmetry.adapters.openclaw as oc

    class _FakeProc:
        def __init__(self, cmd):
            self.info = {"cmdline": cmd}

    fake = [_FakeProc(["model-router", "proxy", "--port=44550"])]
    fake_psutil = types.SimpleNamespace(process_iter=lambda fields: fake)
    monkeypatch.setitem(sys.modules, "psutil", fake_psutil)
    assert oc._discover_model_router_port() == 44550


def test_model_router_live_running_when_health_ok(monkeypatch):
    import clawmetry.adapters.openclaw as oc
    monkeypatch.setattr(oc, "_discover_model_router_port", lambda: 49000)
    monkeypatch.setattr(oc, "_model_router_health_ok", lambda port: True)
    out = oc._model_router_live()
    assert out == {"modelRouterPort": 49000, "modelRouterRunning": True}


def test_model_router_live_crashed_router_is_distinguishable(monkeypatch):
    # Process discoverable (port known) but /health and TCP both fail → a
    # crashed/wedged router reads as NOT running, the whole point of #2795.
    import clawmetry.adapters.openclaw as oc
    monkeypatch.setattr(oc, "_discover_model_router_port", lambda: 49001)
    monkeypatch.setattr(oc, "_model_router_health_ok", lambda port: False)
    out = oc._model_router_live()
    assert out == {"modelRouterPort": 49001, "modelRouterRunning": False}


def test_model_router_live_absent_returns_not_running(monkeypatch):
    import clawmetry.adapters.openclaw as oc
    monkeypatch.setattr(oc, "_discover_model_router_port", lambda: None)
    assert oc._model_router_live() == {"modelRouterRunning": False}


def test_model_router_health_ok_probes_real_localhost_server():
    # Spin up a tiny HTTP server that answers 200 on /health and assert the
    # probe (and its TCP fallback) report it as up.
    import http.server
    import threading
    from clawmetry.adapters.openclaw import _model_router_health_ok

    class _H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            code = 200 if self.path == "/health" else 404
            self.send_response(code)
            self.end_headers()

        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), _H)
    port = srv.server_address[1]
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()
    try:
        assert _model_router_health_ok(port) is True
    finally:
        srv.shutdown()


def test_model_router_health_ok_false_when_nothing_listening():
    from clawmetry.adapters.openclaw import _model_router_health_ok
    # Port 0 is never a live listener; probe must fail closed, not raise.
    assert _model_router_health_ok(0) is False


# -- #2682 nemoclaw catalog dispatch span unwrap -----------------------------

def test_catalog_dispatch_span_unwraps_real_tool():
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [{"type": "message", "timestamp": "2026-06-05T00:00:00Z",
               "message": {"role": "assistant", "content": [
                   {"type": "tool_use", "id": "t1", "name": "tool_call",
                    "input": {"name": "Read", "arguments": {"path": "/x"}}},
                   {"type": "tool_use", "id": "t2", "name": "Bash",
                    "input": {"command": "ls"}},
                   {"type": "tool_use", "id": "t3", "name": "tool_search",
                    "input": {"q": "grep"}},
               ]}}]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    by = {s["tool_name"]: s for s in spans if s.get("tool_name")}
    # tool_call -> real dispatched tool (Read), tagged both dispatch + guardrail
    assert "Read" in by, "tool_call should be unwrapped to its real dispatched tool"
    assert by["Read"]["attributes"]["nemoclaw.dispatched_tool"] == "Read"
    assert by["Read"]["attributes"]["nemoclaw.catalog_guardrail"] is True
    assert by["Read"]["name"] == "tool.Read"
    # ordinary tool -> no nemoclaw attributes
    assert by["Bash"]["attributes"] is None
    # other catalog meta-tools -> guardrail tag only (not a dispatcher)
    assert by["tool_search"]["attributes"] == {"nemoclaw.catalog_guardrail": True}


# -- #2733 tool_result details fold-back -------------------------------------

def test_tool_result_details_attach_to_originating_tool_span():
    """NemoClaw nemoClawBuildToolResult emits structured `details` on the
    result block in the user-role message. The span builder must look the
    matching tool_use_id up and fold details + is_error + text onto the
    pre-existing tool span via Event.extra-shaped attributes.
    """
    from clawmetry.adapters.openclaw import OpenClawAdapter
    catalog_payload = {
        "tools": [{"name": "Read", "schema": {"path": "str"}}],
        "matched": 1,
    }
    events = [
        {"type": "session", "version": "v1", "timestamp": "1700000000"},
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-1", "name": "tool_search",
              "input": {"q": "read"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-1",
              "is_error": False,
              "content": [{"type": "text", "text": '{"matched":1}'}],
              "details": catalog_payload},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    tool_spans = [s for s in spans if s.get("tool_name") == "tool_search"]
    assert len(tool_spans) == 1, "exactly one tool_search span expected"
    ts_span = tool_spans[0]
    attrs = ts_span["attributes"]
    assert attrs["tool.result_present"] is True
    assert attrs["tool.result_is_error"] is False
    assert attrs["tool.result_details"] == catalog_payload
    assert attrs["tool.result_details_keys"] == ["matched", "tools"]
    assert attrs["tool.result_text"] == '{"matched":1}'
    # End-timestamp is stamped to the result's clock.
    assert ts_span["end_ts"] == 1700000002.0


def test_orphan_tool_result_is_silently_skipped():
    """A tool_result whose tool_use_id never appeared upstream must not crash
    the span builder, and must not produce a phantom span."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "ghost",
              "details": {"x": 1}, "content": "ignored"},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    assert spans == []


def test_tool_result_without_details_still_marks_result_present():
    """Native (non-NemoClaw) tools omit `details`. We still want to flag that
    the result arrived so consumers can distinguish in-flight from completed
    tool calls."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-9", "name": "Bash",
              "input": {"command": "ls"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-9",
              "content": "file1\nfile2\n"},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    bash = next(s for s in spans if s.get("tool_name") == "Bash")
    attrs = bash["attributes"]
    assert attrs["tool.result_present"] is True
    assert "tool.result_details" not in attrs
    assert "tool.result_details_keys" not in attrs
    assert "tool.result_is_error" not in attrs
    assert attrs["tool.result_text"] == "file1\nfile2\n"


def test_tool_result_camelcase_tool_use_id_alias_supported():
    """JS-side emitters sometimes carry the camelCase variant (toolUseId).
    Accept both so we don't lose results from harness JSON shape drift."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-77", "name": "Edit",
              "input": {"file_path": "/x"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "toolUseId": "tu-77",
              "details": {"applied": True}},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    edit = next(s for s in spans if s.get("tool_name") == "Edit")
    assert edit["attributes"]["tool.result_details"] == {"applied": True}


# -- #2731 MCP tool_result non-text content blocks ---------------------------

def test_tool_result_content_types_capture_non_text_blocks():
    """OpenClaw's MCP path materializes tool_result content arrays that may
    include resource_link, resource, audio, or malformed-image blocks
    alongside text. The span builder must record every block type that
    appears so downstream Tracing/Event.extra can tell a text-only result
    from one that carried a resource or audio payload."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-1", "name": "mcp__docs__fetch",
              "input": {"id": "rfc-7807"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-1",
              "content": [
                  {"type": "text", "text": "fetched 1 doc"},
                  {"type": "resource_link", "uri": "https://example/rfc7807",
                   "title": "Problem Details"},
              ]},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    tool_span = next(s for s in spans if s.get("tool_name") == "mcp__docs__fetch")
    attrs = tool_span["attributes"]
    assert attrs["tool.result_content_types"] == ["resource_link", "text"]
    assert attrs["tool.result_text"] == "fetched 1 doc"


def test_tool_result_coercion_metadata_surfaces_original_type():
    """When the harness materializes a non-text MCP block at the boundary
    (e.g. an audio block coerced into a text-safe wrapper), it preserves
    the original block type on the coerced block. Capture {from, to} pairs
    so consumers can tell raw text apart from a coerced payload."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-2", "name": "mcp__media__play",
              "input": {"track": "x"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-2",
              "content": [
                  {"type": "text",
                   "text": "[audio omitted]",
                   "coerced_from": "audio"},
                  {"type": "text",
                   "text": "[image omitted]",
                   "originalType": "image"},
              ]},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    tool_span = next(s for s in spans if s.get("tool_name") == "mcp__media__play")
    attrs = tool_span["attributes"]
    assert attrs["tool.result_coercions"] == [
        {"from": "audio", "to": "text"},
        {"from": "image", "to": "text"},
    ]
    assert attrs["tool.result_content_types"] == ["text"]
    assert attrs["tool.result_text"] == "[audio omitted][image omitted]"


def test_tool_result_resource_and_audio_only_blocks_visible():
    """A tool_result with no text blocks (purely resource + audio) still
    surfaces a content-types list; the text accumulator stays absent."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-3", "name": "mcp__bundle__pull",
              "input": {}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-3",
              "content": [
                  {"type": "resource", "uri": "file:///x.bin"},
                  {"type": "audio", "source": {"mime_type": "audio/wav"}},
              ]},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    tool_span = next(s for s in spans if s.get("tool_name") == "mcp__bundle__pull")
    attrs = tool_span["attributes"]
    assert attrs["tool.result_content_types"] == ["audio", "resource"]
    assert "tool.result_text" not in attrs


def test_tool_result_string_content_does_not_emit_content_types():
    """Pre-existing native-tool shape (content is a plain string, not a
    block list) must not pick up a content_types attribute — that field
    only describes block-array results."""
    from clawmetry.adapters.openclaw import OpenClawAdapter
    events = [
        {"type": "message", "timestamp": "1700000001",
         "message": {"role": "assistant", "content": [
             {"type": "tool_use", "id": "tu-4", "name": "Bash",
              "input": {"command": "ls"}},
         ]}},
        {"type": "message", "timestamp": "1700000002",
         "message": {"role": "user", "content": [
             {"type": "tool_result", "tool_use_id": "tu-4",
              "content": "file1\nfile2\n"},
         ]}},
    ]
    spans = OpenClawAdapter._build_spans_from_events(events, "s1")
    bash = next(s for s in spans if s.get("tool_name") == "Bash")
    attrs = bash["attributes"]
    assert "tool.result_content_types" not in attrs
    assert "tool.result_coercions" not in attrs
    assert attrs["tool.result_text"] == "file1\nfile2\n"
