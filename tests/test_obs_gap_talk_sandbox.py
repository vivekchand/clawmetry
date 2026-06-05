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
