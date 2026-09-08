"""Judge last-call status survives across processes (fix for issue #4332).

The sync daemon updates _LAST_JUDGE_STATUS in its own process; the dashboard
serves /api/evaluators from a separate process.  Before the fix, the dashboard
always saw {"ok": None, ...}.  After the fix, last_judge_status() reads the
shared file written by the daemon and returns the newer result.
"""
import json
import time

import clawmetry.eval_runner as er


def _isolate(tmp_path, monkeypatch):
    monkeypatch.setattr(er, "_EVAL_STATUS_PATH", str(tmp_path / "eval_status.json"))
    # Reset in-memory state to "unset" (simulates a fresh dashboard process)
    with er._LAST_JUDGE_LOCK:
        er._LAST_JUDGE_STATUS.update({"ok": None, "error": None, "at": None,
                                      "provider": None, "model": None})


def test_file_written_on_record(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    er._record_judge_status(True, None, "anthropic", "claude-haiku-4-5")
    data = json.loads((tmp_path / "eval_status.json").read_text())
    assert data["ok"] is True
    assert data["provider"] == "anthropic"
    assert data["model"] == "claude-haiku-4-5"
    assert data["error"] is None
    assert isinstance(data["at"], int)


def test_file_written_on_auth_failure(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    er._record_judge_status(False, "auth", "openai", "gpt-4o-mini")
    data = json.loads((tmp_path / "eval_status.json").read_text())
    assert data["ok"] is False
    assert data["error"] == "auth"
    assert data["provider"] == "openai"


def test_last_judge_status_reads_file_when_newer(tmp_path, monkeypatch):
    """Simulates daemon writing, dashboard reading from a separate process."""
    _isolate(tmp_path, monkeypatch)
    # Write status directly to file (as daemon would), bypassing in-memory dict
    ts = int(time.time() * 1000) + 5000  # future ts so it's definitely newer
    payload = {"ok": False, "error": "auth", "at": ts,
               "provider": "anthropic", "model": "claude-haiku-4-5"}
    (tmp_path / "eval_status.json").write_text(json.dumps(payload))

    # In-memory is null (fresh process). last_judge_status() should return file.
    result = er.last_judge_status()
    assert result["ok"] is False
    assert result["error"] == "auth"
    assert result["at"] == ts


def test_last_judge_status_prefers_memory_when_newer(tmp_path, monkeypatch):
    """In-memory wins when it's more recent than the file."""
    _isolate(tmp_path, monkeypatch)
    old_ts = int(time.time() * 1000) - 10000
    (tmp_path / "eval_status.json").write_text(json.dumps(
        {"ok": True, "error": None, "at": old_ts,
         "provider": "openai", "model": "gpt-4o-mini"}
    ))
    # In-memory is at a later timestamp
    with er._LAST_JUDGE_LOCK:
        er._LAST_JUDGE_STATUS.update({"ok": False, "error": "auth",
                                      "at": int(time.time() * 1000),
                                      "provider": "anthropic",
                                      "model": "claude-haiku-4-5"})
    result = er.last_judge_status()
    assert result["provider"] == "anthropic"
    assert result["ok"] is False


def test_last_judge_status_tolerates_missing_file(tmp_path, monkeypatch):
    _isolate(tmp_path, monkeypatch)
    # No file written; should return in-memory null state without raising
    result = er.last_judge_status()
    assert result["ok"] is None


def test_file_write_failure_is_silent(tmp_path, monkeypatch):
    """A bad path must not crash _record_judge_status."""
    monkeypatch.setattr(er, "_EVAL_STATUS_PATH", "/nonexistent_root/x/y/z.json")
    with er._LAST_JUDGE_LOCK:
        er._LAST_JUDGE_STATUS.update({"ok": None, "error": None, "at": None,
                                      "provider": None, "model": None})
    # Should not raise
    er._record_judge_status(True, None, "anthropic", "claude-haiku-4-5")
    # In-memory was still updated
    with er._LAST_JUDGE_LOCK:
        assert er._LAST_JUDGE_STATUS["ok"] is True
