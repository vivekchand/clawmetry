"""OpenClaw v3 chat turns must reach the Brain feed (cloud + device).

Live-confirmed bug (2026-07-07): a node with a real conversation showed
"No brain activity events found" on the cloud Activity tab. Root cause:
``_parse_v3_event`` normalises v3 conversations into
``prompt.submitted{finalPromptText}`` / ``model.completed{completionText,
assistantTexts, toolMetas}`` rows — but ``_brain_row_renderable`` only knew
``content``/``text``/``tool_calls`` (so every ``model.completed`` was
dropped) and ``prompt.submitted`` sat on the blanket skip list (so the user
side vanished too). A pure-chat v3 session therefore contributed ZERO brain
events, and ``_rows_to_brain_events`` forwarded no ``message`` block for the
cloud ``transformEvents`` to render even when rows slipped through.

The row fixtures below are copied from a LIVE node's DuckDB (via the
daemon's ``__local_query__`` proxy), not hand-invented — per FLYWHEEL
"synthetic tests pass while real data flunks".
"""
from __future__ import annotations

import os
import sys

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import sync  # noqa: E402


# ── Live-captured rows (openclaw v3 node, session "diag") ───────────────────

MODEL_COMPLETED = {
    "id": "e1",
    "session_id": "openclaw:diag",
    "event_type": "model.completed",
    "ts": "2026-07-07T13:28:35.000Z",
    "data": {
        "_v3_type": "message",
        "assistantTexts": ["DIAG-OK.\n\nHey — I just came online."],
        "completionText": "DIAG-OK.\n\nHey — I just came online.",
        "modelId": "gpt-5.5",
        "provider": "openai",
        "timestamp": "2026-07-07T13:28:35.000Z",
        "stopReason": "stop",
    },
}

PROMPT_SUBMITTED = {
    "id": "e2",
    "session_id": "openclaw:diag",
    "event_type": "prompt.submitted",
    "ts": "2026-07-07T13:28:28.640Z",
    "data": {
        "_v3_type": "message",
        "data": {"finalPromptText": "Say DIAG-OK"},
        "finalPromptText": "Say DIAG-OK",
        "timestamp": "2026-07-07T13:28:28.640Z",
        "type": "prompt.submitted",
    },
}

MODEL_COMPLETED_TOOLS_ONLY = {
    "id": "e3",
    "session_id": "openclaw:diag",
    "event_type": "model.completed",
    "ts": "2026-07-07T13:29:00.000Z",
    "data": {
        "_v3_type": "message",
        "completionText": "",
        "assistantTexts": [],
        "toolMetas": [{"id": "t1", "name": "exec", "input": {"cmd": "ls"}}],
        "timestamp": "2026-07-07T13:29:00.000Z",
    },
}

PLUMBING_ROWS = [
    {"id": "p1", "event_type": "session.started", "ts": "t",
     "data": {"_v3_type": "session", "cwd": "/data", "id": "diag"}},
    {"id": "p2", "event_type": "model.changed", "ts": "t",
     "data": {"_v3_type": "model_change", "modelId": "gpt-5.5"}},
    {"id": "p3", "event_type": "custom", "ts": "t",
     "data": {"customType": "model-snapshot", "data": {"modelId": "gpt-5.5"}}},
    # prompt.submitted WITHOUT any printable text stays plumbing
    {"id": "p4", "event_type": "prompt.submitted", "ts": "t",
     "data": {"type": "prompt.submitted", "timestamp": "t"}},
]


def test_model_completed_is_renderable():
    assert sync._brain_row_renderable(MODEL_COMPLETED) is True


def test_prompt_submitted_with_text_is_renderable():
    # the user's half of a v3 conversation must not be skipped as plumbing
    assert sync._brain_row_renderable(PROMPT_SUBMITTED) is True


def test_tool_only_completion_is_renderable():
    assert sync._brain_row_renderable(MODEL_COMPLETED_TOOLS_ONLY) is True


def test_plumbing_rows_stay_hidden():
    for row in PLUMBING_ROWS:
        assert sync._brain_row_renderable(row) is False, row["event_type"]


def test_blob_carries_transform_events_contract():
    """The pushed blob must hold the {type:'message', message:{role,content[]}}
    shape the cloud transformEvents role-branches render — its empty-detail
    fallback DROPS anything else."""
    out = sync._rows_to_brain_events(
        [MODEL_COMPLETED, PROMPT_SUBMITTED, MODEL_COMPLETED_TOOLS_ONLY])
    assert len(out) == 3
    a, u, t = out
    assert a["type"] == "message" and a["message"]["role"] == "assistant"
    assert a["message"]["content"][0] == {
        "type": "text", "text": MODEL_COMPLETED["data"]["completionText"]}
    assert u["message"]["role"] == "user"
    assert u["message"]["content"][0]["text"] == "Say DIAG-OK"
    blocks = t["message"]["content"]
    assert blocks and blocks[0]["type"] == "tool_use"
    assert blocks[0]["name"] == "exec"
    # session id stamped bare (drops the runtime: namespace)
    assert a["sessionId"] == "diag"


def test_existing_message_block_untouched():
    """Rows that already carry a message block (claude_code etc.) keep it."""
    row = {"id": "c1", "event_type": "message", "ts": "t", "session_id": "s",
           "data": {"type": "message",
                    "message": {"role": "assistant",
                                "content": [{"type": "text", "text": "hi"}]}}}
    assert sync._brain_row_renderable(row) is True
    out = sync._rows_to_brain_events([row])
    assert out[0]["message"]["content"][0]["text"] == "hi"
