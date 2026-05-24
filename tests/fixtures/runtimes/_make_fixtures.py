"""Generate NanoClaw + PicoClaw session JSONL fixtures.

NanoClaw and PicoClaw share the OpenClaw filesystem layout exactly
(`~/.<runtime>/agents/main/sessions/<id>.jsonl`), so the wire format
is identical. The only differences this fixture captures are runtime-flavour
details that surface in user-visible session metadata:

  - the `cwd` (workspace path embedded in the first session record)
  - the runtime tag attached to model_change events (where present)
  - which model is plausibly running (PicoClaw runs on $10 hardware so
    the fixture uses a smaller local model; NanoClaw is a container
    runtime so it uses a hosted Claude model).
"""
from __future__ import annotations

import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))


def _emit(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        for line in lines:
            fh.write(json.dumps(line) + "\n")


def _session(runtime, sid, cwd, model, total_input, total_output, cost):
    """Minimal but realistic session matching v3 wire format."""
    ts_base_ms = 1778625331119
    ts = "2026-05-12T22:35:31.119296Z"
    return [
        {
            "type": "session",
            "version": 3,
            "id": sid,
            "timestamp": ts,
            "cwd": cwd,
        },
        {
            "type": "model_change",
            "id": "modelchg-1",
            "parentId": None,
            "timestamp": ts,
            "provider": "anthropic" if runtime == "nanoclaw" else "ollama",
            "modelId": model,
        },
        {
            "type": "message",
            "id": "msg-user-1",
            "parentId": None,
            "timestamp": ts,
            "message": {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"hello from {runtime}"}
                ],
                "timestamp": ts_base_ms,
            },
        },
        {
            "type": "message",
            "id": "msg-asst-1",
            "parentId": None,
            "timestamp": ts,
            "message": {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "Working on it."},
                    {
                        "type": "tool_use",
                        "id": "toolu_01compat",
                        "name": "bash",
                        "input": {"command": "echo compat"},
                    },
                ],
                "api": "anthropic-messages",
                "provider": "anthropic" if runtime == "nanoclaw" else "ollama",
                "model": model,
                "usage": {
                    "input": total_input,
                    "output": total_output,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                    "totalTokens": total_input + total_output,
                    "cost": {
                        "input": cost * 0.4,
                        "output": cost * 0.6,
                        "cacheRead": 0,
                        "cacheWrite": 0,
                        "total": cost,
                    },
                },
                "stopReason": "tool_use",
                "timestamp": ts_base_ms,
            },
        },
        {
            "type": "tool_use_result",
            "id": "toolres-1",
            "parentId": None,
            "timestamp": ts,
            "tool_use_id": "toolu_01compat",
            "content": [{"type": "text", "text": "compat\n"}],
            "is_error": False,
        },
        {
            "type": "message",
            "id": "msg-asst-2",
            "parentId": None,
            "timestamp": ts,
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": "done"}],
                "api": "anthropic-messages",
                "provider": "anthropic" if runtime == "nanoclaw" else "ollama",
                "model": model,
                "usage": {
                    "input": 30,
                    "output": 5,
                    "cacheRead": 0,
                    "cacheWrite": 0,
                    "totalTokens": 35,
                    "cost": {
                        "input": cost * 0.1,
                        "output": cost * 0.05,
                        "cacheRead": 0,
                        "cacheWrite": 0,
                        "total": cost * 0.15,
                    },
                },
                "stopReason": "end_turn",
                "timestamp": ts_base_ms,
            },
        },
    ]


def main():
    # NanoClaw — container runtime, hosted model.
    nano_sid = "nano-7f3c1f8a-aaaa-4444-bbbb-cccccccccccc"
    _emit(
        os.path.join(ROOT, "nanoclaw", "agents", "main", "sessions", f"{nano_sid}.jsonl"),
        _session(
            runtime="nanoclaw",
            sid=nano_sid,
            cwd="/workspace/.nanoclaw/workspace",
            model="claude-opus-4-7",
            total_input=120,
            total_output=42,
            cost=0.00495,
        ),
    )

    # PicoClaw — $10 hardware, local model.
    pico_sid = "pico-1a2b3c4d-5555-4666-9777-888888888888"
    _emit(
        os.path.join(ROOT, "picoclaw", "agents", "main", "sessions", f"{pico_sid}.jsonl"),
        _session(
            runtime="picoclaw",
            sid=pico_sid,
            cwd="/home/pi/.picoclaw/workspace",
            model="llama3.2:3b",
            total_input=80,
            total_output=24,
            cost=0.0,
        ),
    )


if __name__ == "__main__":
    main()
