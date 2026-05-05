import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from routes import autonomy, brain, sessions


def _write_jsonl(path: Path, rows):
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _user_message(ts=None):
    return {
        "type": "message",
        "timestamp": ts or datetime.now(tz=timezone.utc).isoformat(),
        "message": {
            "role": "user",
            "content": [{"type": "text", "text": "hello"}],
        },
    }


def _spawn_rows(call_id="call-1", child_key="agent:main:subagent:child-1"):
    return [
        {
            "type": "message",
            "timestamp": "2026-01-01T00:00:00Z",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolCall",
                        "id": call_id,
                        "name": "subagents",
                        "arguments": {"action": "spawn", "label": "worker", "task": "do work"},
                    }
                ],
            },
        },
        {
            "type": "message",
            "timestamp": "2026-01-01T00:00:01Z",
            "message": {
                "role": "toolResult",
                "toolName": "subagents",
                "toolCallId": call_id,
                "details": {"childSessionKey": child_key, "runId": "run-1"},
                "content": [{"type": "text", "text": "accepted"}],
            },
        },
    ]


def test_autonomy_ignores_runtime_artifact_jsonl(tmp_path):
    _write_jsonl(tmp_path / "main-session.jsonl", [_user_message()])
    _write_jsonl(
        tmp_path / "main-session.trajectory.jsonl",
        [_user_message(), _user_message()],
    )
    _write_jsonl(
        tmp_path / "main-session.checkpoint.abc.jsonl",
        [_user_message(), _user_message()],
    )

    data = autonomy._compute_autonomy(str(tmp_path))

    assert data["samples_7d"] == 1
    assert data["autonomy_ratio_7d"] == 1.0


def test_brain_history_bounds_large_file_reads_and_detects_artifacts(tmp_path):
    assert brain._brain_history_is_artifact(str(tmp_path / "a.trajectory.jsonl"))
    assert brain._brain_history_is_artifact(str(tmp_path / "a.checkpoint.abc.jsonl"))
    assert not brain._brain_history_is_artifact(str(tmp_path / "a.jsonl"))

    rows = [json.dumps({"line": i}) for i in range(200)]
    fpath = tmp_path / "large.jsonl"
    fpath.write_text("\n".join(rows) + "\n", encoding="utf-8")

    read_rows = brain._brain_history_read_head_tail(str(fpath), head_lines=3, tail_bytes=120)

    assert json.loads(read_rows[0])["line"] == 0
    assert json.loads(read_rows[1])["line"] == 1
    assert json.loads(read_rows[2])["line"] == 2
    assert json.loads(read_rows[-1])["line"] == 199
    assert len(read_rows) < len(rows)


def test_subagent_jsonl_scan_can_be_bounded_by_recent_files(tmp_path):
    older = tmp_path / "older.jsonl"
    newer = tmp_path / "newer.jsonl"
    _write_jsonl(older, _spawn_rows())
    _write_jsonl(newer, [_user_message()])

    old_ts = time.time() - 100
    new_ts = time.time()
    os.utime(older, (old_ts, old_ts))
    os.utime(newer, (new_ts, new_ts))

    assert len(sessions._scan_spawn_events_from_jsonl(str(tmp_path), max_files=None)) == 1
    assert sessions._scan_spawn_events_from_jsonl(str(tmp_path), max_files=1) == []
