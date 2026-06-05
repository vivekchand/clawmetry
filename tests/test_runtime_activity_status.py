"""Guards runtime activity classification (last_active + status + source).

Detecting a runtime by its on-disk data dir does NOT mean it is active: a
Cursor state.vscdb or opencode.db can sit untouched for months. The Fleet must
not present a 10-month-old Cursor history as a live "syncing" runtime, nor an
OpenClaw sub-agent as a standalone tool. `_classify_runtime` attaches:
  - last_active (epoch) from the runtime's newest data mtime
  - status: active (<7d) / idle (<30d) / stale (older) / unknown
  - source: standalone vs openclaw_subagent
"""
import os
import time

import clawmetry.sync as s


def _touch(path, age_days):
    open(path, "w").close()
    t = time.time() - age_days * 86400
    os.utime(path, (t, t))


def test_recent_native_data_is_active_standalone(tmp_path, monkeypatch):
    f = tmp_path / "claude.jsonl"
    _touch(str(f), age_days=1)
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [str(tmp_path)])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime", lambda rid: None)
    c = s._classify_runtime("claude_code")
    assert c["status"] == "active"
    assert c["source"] == "standalone"
    assert c["last_active"] and abs(c["last_active"] - os.path.getmtime(f)) < 2


def test_old_cursor_history_is_stale(tmp_path, monkeypatch):
    db = tmp_path / "state.vscdb"
    _touch(str(db), age_days=300)  # ~10 months, the real Cursor case
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [str(db)])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime", lambda rid: None)
    c = s._classify_runtime("cursor")
    assert c["status"] == "stale", c


def test_mid_age_is_idle(tmp_path, monkeypatch):
    f = tmp_path / "opencode.db"
    _touch(str(f), age_days=14)
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [str(f)])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime", lambda rid: None)
    assert s._classify_runtime("opencode")["status"] == "idle"


def test_subagent_only_is_classified_as_openclaw_subagent(tmp_path, monkeypatch):
    # No native data; activity exists only via OpenClaw sub-agent.
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime",
                        lambda rid: time.time() - 2 * 86400)
    c = s._classify_runtime("opencode")
    assert c["source"] == "openclaw_subagent"
    assert c["status"] == "active"  # 2 days


def test_standalone_wins_when_newer_than_subagent(tmp_path, monkeypatch):
    f = tmp_path / "n.jsonl"
    _touch(str(f), age_days=1)
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [str(tmp_path)])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime",
                        lambda rid: time.time() - 100 * 86400)
    assert s._classify_runtime("claude_code")["source"] == "standalone"


def test_no_data_is_unknown(monkeypatch):
    monkeypatch.setattr(s, "_runtime_data_paths", lambda rid: [])
    monkeypatch.setattr(s, "_openclaw_subagent_mtime", lambda rid: None)
    c = s._classify_runtime("aider")
    assert c["status"] == "unknown" and c["last_active"] is None


def test_heartbeat_runtimes_carry_status(monkeypatch):
    # End to end: the heartbeat detector enriches each kept runtime.
    monkeypatch.setattr(s, "_detect_runtimes_lite",
                        lambda: [{"id": "cursor", "label": "Cursor", "sessions": 5}])
    monkeypatch.setattr(s, "_detect_family_runtimes", lambda: [])
    monkeypatch.setattr(s, "_classify_runtime",
                        lambda rid: {"last_active": 123, "status": "stale", "source": "standalone"})
    out = s._detect_runtimes_for_heartbeat()
    assert out and out[0]["status"] == "stale" and out[0]["last_active"] == 123
