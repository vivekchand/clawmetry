"""coordinated_action: sessions that should be independent, acting in step.

Scorecard rows 5 and 11 of
https://clawmetry.com/blog/could-clawmetry-have-caught-the-hugging-face-swarm:
~1,200 agents used one Artifactory path as a message board, and 90% pivoted
to the same target within an hour. Every per-session detector saw, at most,
one agent doing something slightly odd. This file pins the fleet question.

Acceptance criteria proven here (REQ-OBS-RSO-035):

    AC-OBS-RSO-035.1  test_per_agent_paths_share_one_fingerprint, test_fingerprint_shape
    AC-OBS-RSO-035.2  test_unrelated_sessions_writing_one_unseen_prefix_fire_once,
                      test_below_the_threshold_is_quiet
    AC-OBS-RSO-035.3  test_an_orchestrator_and_its_subagents_count_once,
                      test_subagents_of_different_orchestrators_are_unrelated,
                      test_a_parent_cycle_cannot_hang_the_walk,
                      test_subagent_parents_walk_to_the_root
    AC-OBS-RSO-035.4  test_an_action_the_node_has_long_known_is_normal,
                      test_an_action_first_seen_minutes_ago_is_still_unusual,
                      test_fingerprint_memory_round_trip
    AC-OBS-RSO-035.5  test_a_node_without_a_full_window_of_memory_says_nothing
    AC-OBS-RSO-035.6  test_fleet_pass_pages_once_and_marks_every_participant,
                      test_fleet_pass_does_not_re_mark_a_session_every_tick
    AC-OBS-RSO-035.7  test_a_catch_all_policy_does_not_act_on_the_swarm,
                      test_a_policy_that_names_coordinated_action_matches
    AC-OBS-RSO-035.8  test_unrelated_sessions_writing_one_unseen_prefix_fire_once
"""
from __future__ import annotations

import importlib
import os
import sys
import time

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import detector_swarm as sw  # noqa: E402
from clawmetry import detectors  # noqa: E402
from clawmetry import policy_engine as pe  # noqa: E402

DAY_MS = 86_400_000
NOW = time.time()
NOW_MS = NOW * 1000
LONG_AGO = NOW_MS - 3 * DAY_MS
BOARD = "PUT artifactory.internal/artifactory/github-remote-cache"


def _shell(cmd: str) -> dict:
    return {"event_type": "tool_call", "ts": "2026-07-04T10:00:00",
            "data": {"tool": "Bash", "args": {"command": cmd}}}


def _fps(*cmds) -> list:
    return sw.write_fingerprints(detectors.normalize_events(
        [_shell(c) for c in reversed(cmds)]))


def _board_post(n: int) -> str:
    return (f"curl -X PUT --data-binary @msg{n}.txt "
            f"https://artifactory.internal/artifactory/github-remote-cache/zz{n}/msg")


def _swarm(n: int) -> dict:
    return {f"claude_code:s{i}": _fps(_board_post(i)) for i in range(n)}


def _run(fps, **kw):
    kw.setdefault("history", {})
    kw.setdefault("history_since_ms", LONG_AGO)
    kw.setdefault("now", NOW)
    kw.setdefault("min_families", 5)
    kw.setdefault("settle_hours", 24)
    return sw.coordinated_action(fps, **kw)


# ── fingerprints ─────────────────────────────────────────────────────────────
def test_per_agent_paths_share_one_fingerprint():
    """Each agent wrote under its own zzNN directory. The board is the prefix."""
    assert _fps(_board_post(1)) == _fps(_board_post(42)) == [
        ("PUT", "artifactory.internal", "/artifactory/github-remote-cache")]


@pytest.mark.parametrize("cmd,fp", [
    ("curl -X MKCOL https://artifactory.internal/artifactory/cache/zz1/",
     ("MKCOL", "artifactory.internal", "/artifactory/cache")),
    ("curl -d @x.json https://api.example.com/v1/items", ("POST", "api.example.com", "/*/items")),
    ("curl -T f.bin https://drop.example.net/up", ("PUT", "drop.example.net", "/up")),
    ("http PATCH https://api.example.com/items/7 a=1", ("PATCH", "api.example.com", "/items/*")),
    ("huggingface-cli upload org/ds ./x.h5", ("UPLOAD", "huggingface.co", "")),
])
def test_fingerprint_shape(cmd, fp):
    assert _fps(cmd) == [fp]


def test_reads_have_no_fingerprint():
    assert _fps("curl -fsSL https://pypi.org/simple/x/", "wget https://e.com/f") == []


# ── the fleet question ───────────────────────────────────────────────────────
def test_unrelated_sessions_writing_one_unseen_prefix_fire_once():
    out = _run(_swarm(6))
    assert len(out) == 1, "one incident per fingerprint, not per session"
    inc = out[0]
    assert inc["kind"] == "coordinated_action"
    assert inc["severity"] == "warning"
    assert inc["title"] == ("6 unrelated sessions sent PUT to "
                            "artifactory.internal/artifactory/github-remote-cache")
    assert inc["evidence"]["families"] == 6
    assert inc["evidence"]["fingerprint_key"] == BOARD
    assert inc["evidence"]["first_seen_by_node"] is None
    assert len(inc["participants"]) == 6
    assert inc["evidence"]["observed"] == "tool_arguments"
    # AC-OBS-RSO-035.8: the words a person reads say where this came from.
    assert "tool arguments" in inc["detail"]


def test_below_the_threshold_is_quiet():
    assert _run(_swarm(4)) == []


def test_an_orchestrator_and_its_subagents_count_once():
    fps = _swarm(6)
    parents = {f"s{i}": "orch" for i in range(6)}   # bare ids, as subagents stores them
    assert _run(fps, parents=parents) == []


def test_subagents_of_different_orchestrators_are_unrelated():
    fps = _swarm(6)
    parents = {f"s{i}": f"orch{i}" for i in range(6)}
    assert _run(fps, parents=parents)[0]["evidence"]["families"] == 6


def test_a_parent_cycle_cannot_hang_the_walk():
    fps = _swarm(6)
    parents = {"s0": "s1", "s1": "s0"}
    assert _run(fps, parents=parents)[0]["evidence"]["families"] == 5


def test_an_action_the_node_has_long_known_is_normal():
    assert _run(_swarm(8), history={BOARD: LONG_AGO}) == []


def test_an_action_first_seen_minutes_ago_is_still_unusual():
    """The first member of a swarm to write there must not vouch for the rest."""
    out = _run(_swarm(8), history={BOARD: NOW_MS - 10 * 60_000})
    assert len(out) == 1
    assert "first saw it 10 min ago" in out[0]["detail"]


def test_a_node_without_a_full_window_of_memory_says_nothing():
    """Day one: every action is new, and reporting that would be noise."""
    assert _run(_swarm(8), history_since_ms=None) == []
    assert _run(_swarm(8), history_since_ms=NOW_MS - 3_600_000) == []


def test_largest_fingerprint_first():
    fps = _swarm(6)
    for i in range(5):
        fps[f"claude_code:t{i}"] = _fps(f"curl -X POST https://paste.example.net/new{i}")
    out = _run(fps)
    assert [i["evidence"]["families"] for i in out] == [6, 5]


def test_never_raises_on_junk():
    assert sw.coordinated_action({"x": [None, 3]}, history_since_ms=LONG_AGO) == []
    assert sw.coordinated_action(None) == []
    assert sw.write_fingerprints([None, {"kind": "tool_call", "write_hosts": 5}]) == []


# ── kinds and policy ─────────────────────────────────────────────────────────
def test_the_fleet_kind_is_known_everywhere_but_is_not_a_session_detector():
    assert "coordinated_action" in detectors.ALL_INCIDENT_KINDS
    assert "coordinated_action" not in detectors.DETECTOR_KINDS


def _incident(kind="coordinated_action"):
    return {"kind": kind, "session_id": "cursor:1", "runtime": "cursor",
            "severity": "warning", "title": "t", "detail": "d", "evidence": {},
            "spend_at_risk_usd": 0.0, "spend_basis": "unknown"}


def _policy(trigger_kind=""):
    return {"policy_id": "p1", "enabled": True, "scope_runtime": "",
            "scope_agent_id": "", "trigger_kind": trigger_kind,
            "min_severity": "warning", "min_repeat": 0, "min_duration_s": 0,
            "min_spend_usd": 0, "min_spend_at_risk_usd": 0, "action": "pause"}


_FACTS = {"cursor:1": {"cost_usd": 1.0, "bad_for_seconds": 999,
                       "runtime": "cursor", "cwd": "/w", "agent_id": "main"}}


def test_a_catch_all_policy_does_not_act_on_the_swarm():
    """One finding lands on every participant: a rule written about one
    runaway agent must not pause forty sessions nobody asked it to."""
    assert pe.evaluate([_incident()], [_policy("")], _FACTS) == []


def test_a_policy_that_names_coordinated_action_matches():
    decisions = pe.evaluate([_incident()], [_policy("coordinated_action")], _FACTS)
    assert [d["kind"] for d in decisions] == ["coordinated_action"]


# ── the node remembers (real DuckDB) ─────────────────────────────────────────
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


def test_fingerprint_memory_round_trip(real_store):
    assert real_store.query_action_fingerprints(keys=[BOARD]) == {
        "first_seen": {}, "since": None}
    real_store.record_action_fingerprints(fingerprints=[
        (BOARD, "PUT", "artifactory.internal", "/artifactory/github-remote-cache", 6)])
    got = real_store.query_action_fingerprints(keys=[BOARD, "POST nowhere"])
    first = got["first_seen"][BOARD]
    assert abs(first - time.time() * 1000) < 60_000
    assert got["since"] == first
    real_store.record_action_fingerprints(fingerprints=[
        (BOARD, "PUT", "artifactory.internal", "/artifactory/github-remote-cache", 9)])
    assert real_store.query_action_fingerprints(keys=[BOARD])["first_seen"][BOARD] == first


def test_subagent_parents_walk_to_the_root(real_store):
    for child, parent in (("c1", "mid"), ("mid", "root"), ("c2", "root")):
        real_store._conn.execute(
            "INSERT INTO subagents (agent_type, subagent_id, parent_session_id, updated_at) "
            "VALUES ('claude_code', ?, ?, 0)", [child, parent])
    got = real_store.query_subagent_parents(session_ids=["claude_code:c1", "c2", "lonely"])
    assert got == {"c1": "mid", "mid": "root", "c2": "root"}


# ── the daemon's fleet pass ──────────────────────────────────────────────────
class _FleetStore:
    def __init__(self, first_seen=None, since=LONG_AGO, parents=None):
        self._hist = {"first_seen": dict(first_seen or {}), "since": since}
        self._parents = dict(parents or {})
        self.recorded: list = []
        self.signals: list = []

    def query_action_fingerprints(self, keys=None):
        return self._hist

    def query_subagent_parents(self, session_ids=None):
        return self._parents

    def record_action_fingerprints(self, fingerprints=None):
        self.recorded.extend(fingerprints or [])

    def ingest_loop_signal(self, **kw):
        self.signals.append(kw)


@pytest.fixture()
def delivered(monkeypatch):
    from clawmetry import incident_alerts as ia
    sent: list = []

    def _deliver(store, incident, **kw):
        sent.append(incident)
        return {"delivered": True, "delivered_via": ["banner"]}

    monkeypatch.setattr(ia, "deliver_incident", _deliver)
    return sent


def test_fleet_pass_pages_once_and_marks_every_participant(delivered):
    import clawmetry.sync as sync
    store = _FleetStore()
    out = sync._emit_fleet_incidents(store, {}, _swarm(6), NOW)
    assert len(delivered) == 1, "one message for the swarm, not six"
    assert delivered[0]["session_id"].startswith("fleet:")
    assert sorted(i["session_id"] for i in out) == sorted(_swarm(6))
    assert {s["signature"] for s in store.signals} == {"daemon_detect_coordinated_action"}
    assert len(store.signals) == 6
    assert all(s["details"]["delivered_via"] == ["banner"] for s in store.signals)
    # The node remembers what it saw, AFTER judging it.
    assert [r[0] for r in store.recorded] == [BOARD]
    assert store.recorded[0][4] == 6


def test_fleet_pass_is_quiet_on_a_known_action_and_still_remembers(delivered):
    import clawmetry.sync as sync
    store = _FleetStore(first_seen={BOARD: LONG_AGO})
    assert sync._emit_fleet_incidents(store, {}, _swarm(6), NOW) == []
    assert delivered == [] and store.signals == []
    assert [r[0] for r in store.recorded] == [BOARD]


def test_fleet_pass_does_not_re_mark_a_session_every_tick(delivered):
    import clawmetry.sync as sync
    store, state = _FleetStore(), {}
    sync._emit_fleet_incidents(store, state, _swarm(6), NOW)
    sync._emit_fleet_incidents(store, state, _swarm(6), NOW + 5)
    assert len(store.signals) == 6


def test_fleet_pass_survives_a_broken_store(delivered):
    import clawmetry.sync as sync

    class _Broken:
        def __getattr__(self, name):
            raise RuntimeError("store down")

    assert sync._emit_fleet_incidents(_Broken(), {}, _swarm(6), NOW) == []
    assert sync._emit_fleet_incidents(_FleetStore(), {}, {}, NOW) == []
