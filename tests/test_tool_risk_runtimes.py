"""Per-runtime matrix: call-level risk classification + min_risk policies
must work for EVERY runtime ClawMetry ingests.

Each case below is an events-table row in the runtime's REAL persisted
shape (verified against the adapters + fixtures in the 2026-08-17
runtime-shape audit: sync.py family row builder, _parse_v3_event,
clawmetry/adapters/nemo.py, and the clawmetry-pro adapters for the paid
family). A ``min_risk: high`` policy is replayed over the row and must
fire on the risky call and stay quiet on the safe one — through the SAME
``_extract_tool_blocks`` + ``match_policy`` path the live watcher uses,
so a passing matrix means the watcher, replay, and hook gate all see that
runtime.

Documented degradations (asserted, not hidden):
  * qm persists tool_name only (no args) — name-only classification.
  * aider has no tool-call concept; grok emits no tool events yet.
  * n8n args are static node config, truncated (still classifiable).
"""
from __future__ import annotations

import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import approvals


RISKY = "rm -rf /tmp/canary"
SAFE = "git status"

HIGH_POLICY = {"name": "high-risk gate", "min_risk": "high",
               "action": "require_approval"}


def _family_row(runtime: str, tool: str, call: dict, eid: str,
                event_type: str = "tool_call") -> dict:
    """The uniform family-adapter row sync.py builds for the pro runtimes:
    ``data = {role, content, _runtime, tool_name, tool_calls: [...]}``."""
    return {
        "id": eid,
        "session_id": f"{runtime}:sess-1",
        "ts": "2026-08-17T00:00:00Z",
        "event_type": event_type,
        "data": {"role": "assistant", "content": "", "_runtime": runtime,
                 "tool_name": tool, "tool_calls": [call]},
    }


def _matrix() -> list:
    """(runtime label, risky row, safe row) triplets in real shapes."""
    cases = []

    # ── openclaw: legacy gateway/message envelope ──
    def _oc_legacy(cmd, eid):
        return {"id": eid, "session_id": "agent:main:x",
                "ts": "2026-08-17T00:00:00Z", "event_type": "message",
                "data": {"type": "message", "message": {
                    "role": "assistant", "content": [
                        {"type": "toolCall", "id": eid + "-t",
                         "name": "exec", "arguments": {"command": cmd}}]}}}
    cases.append(("openclaw-legacy", _oc_legacy(RISKY, "ol1"),
                  _oc_legacy(SAFE, "ol2")))

    # ── openclaw: v3 underscore schema (CURRENT on-disk shape) ──
    def _oc_v3(cmd, eid):
        return {"id": eid, "session_id": "agent:main:x",
                "ts": "2026-08-17T00:00:00Z",
                "event_type": "model.completed",
                "data": {"completionText": "", "modelId": "m",
                         "toolMetas": [{"id": eid + "-t", "name": "bash",
                                        "input": {"command": cmd}}]}}
    cases.append(("openclaw-v3", _oc_v3(RISKY, "ov1"), _oc_v3(SAFE, "ov2")))

    # ── openclaw: v3 top-level tool_use → tool.call row ──
    def _oc_toolcall(cmd, eid):
        return {"id": eid, "session_id": "agent:main:x",
                "ts": "2026-08-17T00:00:00Z", "event_type": "tool.call",
                "data": {"name": "bash", "id": eid + "-t",
                         "input": {"command": cmd}}}
    cases.append(("openclaw-toolcall", _oc_toolcall(RISKY, "ot1"),
                  _oc_toolcall(SAFE, "ot2")))

    # ── openclaw: embedded Claude Code sub-session (tool_use/input) ──
    def _oc_claude(cmd, eid):
        return {"id": eid, "session_id": "agent:main:x",
                "ts": "2026-08-17T00:00:00Z", "event_type": "assistant",
                "data": {"message": {"role": "assistant", "content": [
                    {"type": "tool_use", "id": eid + "-t", "name": "Bash",
                     "input": {"command": cmd}}]}}}
    cases.append(("openclaw-embedded-claude", _oc_claude(RISKY, "oc1"),
                  _oc_claude(SAFE, "oc2")))

    # ── nemoclaw: NeMo toolkit tool.call ──
    def _nemo(cmd, eid):
        return {"id": eid, "session_id": "nemoclaw:sess-1",
                "ts": "2026-08-17T00:00:00Z", "event_type": "tool.call",
                "data": {"name": "exec", "input": {"command": cmd}}}
    cases.append(("nemoclaw", _nemo(RISKY, "nm1"), _nemo(SAFE, "nm2")))

    # ── family adapters with dict args under "input" ──
    for rt, tool in [("claude_code", "Bash"), ("nanoclaw", "Bash"),
                     ("copilot", "bash"), ("antigravity", "run_command"),
                     ("deepseek_harness", "shell"), ("exo", "shell")]:
        cases.append((
            rt,
            _family_row(rt, tool, {"id": "c1", "name": tool,
                                   "input": {"command": RISKY}}, f"{rt}1"),
            _family_row(rt, tool, {"id": "c2", "name": tool,
                                   "input": {"command": SAFE}}, f"{rt}2"),
        ))

    # ── family adapters with dict args under "arguments" ──
    for rt, tool in [("goose", "shell"), ("opencode", "bash"),
                     ("deepagents", "shell"), ("qwen_code", "run_shell_command"),
                     ("pi", "bash")]:
        cases.append((
            rt,
            _family_row(rt, tool, {"id": "c1", "name": tool,
                                   "arguments": {"command": RISKY}}, f"{rt}1"),
            _family_row(rt, tool, {"id": "c2", "name": tool,
                                   "arguments": {"command": SAFE}}, f"{rt}2"),
        ))

    # ── codex: arguments as a JSON STRING (OpenAI function_call) ──
    cases.append((
        "codex",
        _family_row("codex", "shell",
                    {"id": "c1", "name": "shell",
                     "arguments": '{"command": ["bash", "-lc", "%s"]}' % RISKY},
                    "cx1"),
        _family_row("codex", "shell",
                    {"id": "c2", "name": "shell",
                     "arguments": '{"command": ["bash", "-lc", "%s"]}' % SAFE},
                    "cx2"),
    ))

    # ── picoclaw: OpenAI-nested function shape, arguments JSON string ──
    cases.append((
        "picoclaw",
        _family_row("picoclaw", "exec",
                    {"id": "c1", "type": "function",
                     "function": {"name": "exec",
                                  "arguments": '{"command": "%s"}' % RISKY}},
                    "pc1"),
        _family_row("picoclaw", "exec",
                    {"id": "c2", "type": "function",
                     "function": {"name": "exec",
                                  "arguments": '{"command": "%s"}' % SAFE}},
                    "pc2"),
    ))

    # ── hermes: verbatim OpenAI tool_calls pass-through ──
    cases.append((
        "hermes",
        _family_row("hermes", "terminal",
                    {"id": "c1", "type": "function",
                     "function": {"name": "terminal",
                                  "arguments": '{"command": "%s"}' % RISKY}},
                    "hm1"),
        _family_row("hermes", "terminal",
                    {"id": "c2", "type": "function",
                     "function": {"name": "terminal",
                                  "arguments": '{"command": "%s"}' % SAFE}},
                    "hm2"),
    ))

    # ── cursor: toolFormerData with args under "params" ──
    cases.append((
        "cursor",
        _family_row("cursor", "run_terminal_cmd",
                    {"name": "run_terminal_cmd",
                     "params": {"command": RISKY}}, "cu1"),
        _family_row("cursor", "run_terminal_cmd",
                    {"name": "run_terminal_cmd",
                     "params": {"command": SAFE}}, "cu2"),
    ))

    # ── n8n: static node parameters as arguments (truncated dict) ──
    cases.append((
        "n8n",
        _family_row("n8n", "executeCommand",
                    {"id": "c1", "name": "executeCommand",
                     "arguments": {"command": RISKY}}, "n81"),
        _family_row("n8n", "httpRequest",
                    {"id": "c2", "name": "httpRequest",
                     "arguments": {"url": "https://api.github.com"}}, "n82"),
    ))

    # ── dsh alt shape: tool calls inside a message event ──
    cases.append((
        "deepseek_harness-message",
        _family_row("deepseek_harness", "shell",
                    {"id": "c1", "name": "shell",
                     "input": {"command": RISKY}}, "dm1",
                    event_type="message"),
        _family_row("deepseek_harness", "shell",
                    {"id": "c2", "name": "shell",
                     "input": {"command": SAFE}}, "dm2",
                    event_type="message"),
    ))

    return cases


@pytest.mark.parametrize("runtime,risky_row,safe_row", _matrix(),
                         ids=[c[0] for c in _matrix()])
def test_min_risk_policy_fires_per_runtime(runtime, risky_row, safe_row):
    out = approvals.replay_policy(HIGH_POLICY, [risky_row, safe_row])
    assert out["ok"] is True, out
    assert out["scanned_tool_calls"] == 2, (
        f"{runtime}: expected 2 extracted tool calls, got "
        f"{out['scanned_tool_calls']} — extractor is blind to this shape")
    assert out["matches"] == 1, (
        f"{runtime}: expected exactly the risky call to match, got "
        f"{out['matches']} (samples: {out['samples']})")
    assert out["samples"][0]["command"].startswith("rm -rf") or \
        "rm -rf" in out["samples"][0]["command"], out["samples"]


def test_qm_name_only_degradation():
    """qm persists tool_name with NO args: classification degrades to the
    category floor (exec with unknown command = medium), so a min_risk
    medium policy still gates it while high does not false-fire."""
    row = {"id": "qm1", "session_id": "qm:s", "ts": "2026-08-17T00:00:00Z",
           "event_type": "tool_call",
           "data": {"role": "assistant", "_runtime": "qm",
                    "tool_name": "shell", "content": "ran something",
                    "tool_calls": [{"id": "c1", "name": "shell"}]}}
    med = approvals.replay_policy({"name": "med", "min_risk": "medium",
                                   "action": "require_approval"}, [row])
    high = approvals.replay_policy(HIGH_POLICY, [row])
    assert med["matches"] == 1
    assert high["matches"] == 0


def test_watcher_event_types_cover_every_matrix_shape():
    """Every event_type used by the matrix must be in the watcher's scan
    list — otherwise replay would pass while the LIVE watcher stays blind
    (the exact drift this shared-list contract exists to prevent)."""
    used = {r["event_type"] for _rt, a, b in _matrix() for r in (a, b)}
    for et in used:
        assert et in approvals._TOOL_EVENT_TYPES, et
