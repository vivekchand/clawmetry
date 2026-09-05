"""Liveness is a question about a process, not about a transcript.

Regression suite for the "Still running" bug (2026-09-05): a Claude Code
session whose last transcript line was written at 02:34:55 was labelled
``ongoing`` at 02:35:34 and still rendered "Still running" at 12:14, with its
terminal closed and no process left. Measured on that node, 43 rows carried
the label and 3 of them were true.

The fix has two halves and both are tested here:
  * ``process_control.session_live_state`` answers from the runtime's own
    per-pid record, and keeps "I cannot tell" distinct from "it is dead".
  * ``outcome_classifier.classify_session`` takes that answer instead of
    guessing from how recently an event landed.
"""

import json
import os
import time

import pytest

from clawmetry import process_control as pc
from clawmetry.outcome_classifier import (
    LIVE_BUSY,
    LIVE_DEAD,
    LIVE_IDLE,
    OUTCOME_ONGOING,
    OUTCOME_SUCCESS,
    OUTCOME_WAITING,
    TIME_DEPENDENT_OUTCOMES,
    aggregate_outcomes,
    classify_session,
)

# ── the probe ────────────────────────────────────────────────────────────

@pytest.fixture
def claude_sessions_dir(tmp_path, monkeypatch):
    """Point the probe at a throwaway ``<dir>/sessions/`` of our own."""
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path))
    (tmp_path / "sessions").mkdir()
    # The map memoizes on (dir, mtime) for 2s; clear it between cases.
    pc._CLAUDE_MAP_CACHE.update({"key": None, "at": 0.0, "map": {}})
    yield tmp_path / "sessions"
    pc._CLAUDE_MAP_CACHE.update({"key": None, "at": 0.0, "map": {}})


def _write_record(d, *, sid, pid, status):
    (d / f"{pid}.json").write_text(json.dumps({
        "pid": pid, "sessionId": sid, "cwd": "/tmp",
        "procStart": "Fri Sep  5 02:00:00 2026", "status": status,
    }))
    pc._CLAUDE_MAP_CACHE.update({"key": None, "at": 0.0, "map": {}})


def test_no_pid_record_means_dead(claude_sessions_dir):
    """The exact shape of the bug: a session nothing on this node is running.

    claude_code removes ``<pid>.json`` when the process exits, so its absence
    is a positive statement, not missing data.
    """
    assert pc.session_live_state(
        "claude_code", "claude_code:9a3e3302-6600-4245-9334-84909cd9c3d9"
    ) == LIVE_DEAD


def test_busy_record_for_a_live_pid_is_busy(claude_sessions_dir):
    _write_record(claude_sessions_dir, sid="s-busy", pid=os.getpid(),
                  status="busy")
    assert pc.session_live_state("claude_code", "claude_code:s-busy") == LIVE_BUSY


def test_idle_record_for_a_live_pid_is_idle(claude_sessions_dir):
    """An open terminal at its prompt. Alive, but not working."""
    _write_record(claude_sessions_dir, sid="s-idle", pid=os.getpid(),
                  status="idle")
    assert pc.session_live_state("claude_code", "claude_code:s-idle") == LIVE_IDLE


def test_shell_status_counts_as_working(claude_sessions_dir):
    """``shell`` is a Bash tool call in flight — work, not waiting."""
    _write_record(claude_sessions_dir, sid="s-sh", pid=os.getpid(),
                  status="shell")
    assert pc.session_live_state("claude_code", "claude_code:s-sh") == LIVE_BUSY


def test_unknown_status_defaults_to_busy_not_idle(claude_sessions_dir):
    """A status this version does not know still means the process is up.

    Guessing ``idle`` for a working agent is the error that costs money;
    guessing ``busy`` for an idle one costs a slightly stale badge.
    """
    _write_record(claude_sessions_dir, sid="s-new", pid=os.getpid(),
                  status="some-future-state")
    assert pc.session_live_state("claude_code", "claude_code:s-new") == LIVE_BUSY


def test_stale_record_for_a_dead_pid_is_dead(claude_sessions_dir):
    """A ``<pid>.json`` can outlive its process; the pid decides."""
    dead_pid = 2 ** 22 - 1  # above any real pid on the platforms we run on
    _write_record(claude_sessions_dir, sid="s-stale", pid=dead_pid,
                  status="busy")
    assert pc.session_live_state("claude_code", "claude_code:s-stale") == LIVE_DEAD


def test_prefixed_and_bare_ids_resolve_the_same(claude_sessions_dir):
    """The store prefixes family ids; the per-pid map is keyed on the bare id.

    Passing the prefixed form straight through is how Guard's controls came to
    be inert on every family runtime (#5551) — do not regress it here.
    """
    _write_record(claude_sessions_dir, sid="s-pref", pid=os.getpid(),
                  status="busy")
    assert pc.session_live_state("claude_code", "claude_code:s-pref") == LIVE_BUSY
    assert pc.session_live_state("claude_code", "s-pref") == LIVE_BUSY
    assert pc.session_live_state("", "claude_code:s-pref") == LIVE_BUSY


def test_subagent_rows_are_unknown_not_dead(claude_sessions_dir):
    """A sub-agent has no pid of its own.

    Its parent being alive says nothing about whether the child finished, so
    the honest answer is "cannot tell" and the caller keeps its heuristic.
    """
    _write_record(claude_sessions_dir, sid="parent", pid=os.getpid(),
                  status="busy")
    assert pc.session_live_state(
        "claude_code", "claude_code:parent::agent-abc123") is None


def test_unprobeable_runtime_is_unknown_not_dead():
    """Only runtimes that publish a per-pid record can be probed.

    Answering ``dead`` for a runtime this node simply cannot see would retire
    every live session on it.
    """
    assert pc.session_live_state("codex", "codex:whatever") is None
    assert pc.session_live_state("openclaw", "abc-123") is None


def test_probe_never_raises(monkeypatch):
    def boom():
        raise RuntimeError("disk gone")
    monkeypatch.setattr(pc, "claude_code_session_map", boom)
    assert pc.session_live_state("claude_code", "claude_code:x") is None


# ── the classifier ───────────────────────────────────────────────────────

def _events(last_ts_epoch):
    """One user turn and one assistant reply — the whole 9a3e3302 transcript."""
    import datetime as _dt

    def iso(t):
        return _dt.datetime.fromtimestamp(
            t, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return [
        {"event_type": "session.started", "ts": iso(last_ts_epoch - 2)},
        {"event_type": "model.completed", "ts": iso(last_ts_epoch),
         "data": {"text": "Ready. What would you like me to do?"}},
    ]


def test_dead_process_is_never_ongoing_however_fresh_the_transcript():
    """The bug, at the classifier.

    The transcript's last line is 10 seconds old — inside the 5-minute window
    that used to be the entire test for "still running" — but the process is
    gone. A closed terminal writes a final reply and then nothing, so recency
    alone cannot tell it from an agent mid-turn.
    """
    now = time.time()
    outcome, _conf = classify_session(_events(now - 10), {}, now=now,
                                      live=LIVE_DEAD)
    assert outcome != OUTCOME_ONGOING
    assert outcome == OUTCOME_SUCCESS


def test_busy_process_is_ongoing_however_old_the_transcript():
    """The mirror failure: a live agent labelled finished.

    On the node where this was found, 12 running ``claude`` processes carried
    a "Finished" badge — a long tool call writes nothing to the transcript
    while it runs, and the recency heuristic reads that silence as an ending.
    """
    now = time.time()
    outcome, conf = classify_session(_events(now - 9 * 3600), {}, now=now,
                                     live=LIVE_BUSY)
    assert outcome == OUTCOME_ONGOING
    assert conf == pytest.approx(0.95)


def test_idle_process_says_waiting_not_still_running():
    """An open terminal at its prompt gets its own label, not "Still running".

    "Still running" on a session that is doing nothing is the reading that
    sends someone to check on an agent that is waiting for them.
    """
    now = time.time()
    outcome, conf = classify_session(_events(now - 30), {}, now=now,
                                     live=LIVE_IDLE)
    assert outcome == OUTCOME_WAITING
    assert conf == pytest.approx(0.95)


def test_no_probe_keeps_the_recent_activity_heuristic():
    """Runtimes we cannot probe must behave exactly as before."""
    now = time.time()
    fresh, conf = classify_session(_events(now - 10), {}, now=now, live=None)
    assert fresh == OUTCOME_ONGOING
    assert conf == pytest.approx(0.6)
    stale, _ = classify_session(_events(now - 9 * 3600), {}, now=now, live=None)
    assert stale != OUTCOME_ONGOING


def test_live_defaults_to_none_for_existing_callers():
    """The kwarg is additive: callers that pass nothing get the old behaviour."""
    now = time.time()
    assert classify_session(_events(now - 10), {}, now=now)[0] == OUTCOME_ONGOING


def test_idle_process_is_not_tool_call_stuck():
    """An agent blocked on a tool reports busy/shell, never idle.

    So an unanswered invocation on an idle session is a result the transcript
    never recorded, not a tool that hung — "Got stuck" would be the same
    mistake as "Still running", one label down.
    """
    import datetime as _dt
    now = time.time()

    def iso(t):
        return _dt.datetime.fromtimestamp(
            t, _dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    evs = [
        {"event_type": "session.started", "ts": iso(now - 3600)},
        {"event_type": "tool.call", "ts": iso(now - 3000),
         "data": {"name": "bash", "id": "t1"}},
    ]
    assert classify_session(evs, {}, now=now, live=LIVE_IDLE)[0] == OUTCOME_WAITING


def test_waiting_is_counted_and_excluded_from_success_rate():
    """A label with no bucket in ``aggregate_outcomes`` is counted as SUCCESS.

    That fallthrough is why every new label must be added there in the same
    change: silently, ``waiting`` would have inflated the headline rate.
    """
    agg = aggregate_outcomes([
        {"outcome": "success"}, {"outcome": "failed"},
        {"outcome": "waiting"}, {"outcome": "waiting"},
        {"outcome": "ongoing"},
    ])
    assert agg["waiting"] == 2
    assert agg["success"] == 1
    assert agg["total"] == 5
    # 1 success / (1 success + 1 failed) — neither in-flight label counts.
    assert agg["success_rate"] == pytest.approx(0.5)


def test_the_decaying_labels_are_named_for_readers_that_cache():
    """Anything that stores a label needs to know which ones expire."""
    assert TIME_DEPENDENT_OUTCOMES == {OUTCOME_ONGOING, OUTCOME_WAITING}


def test_the_id_prefix_beats_a_wrong_agent_type(claude_sessions_dir):
    """``sessions.agent_type`` is "openclaw" on rows whose id is a family one.

    Family ingest sets no agent_type, so the column defaults; the runtime only
    ever appears in the id. Trusting the argument over the prefix would make
    every family row unprobeable — and unprobeable means the old guess.
    """
    _write_record(claude_sessions_dir, sid="s-x", pid=os.getpid(), status="idle")
    assert pc.session_live_state("openclaw", "claude_code:s-x") == LIVE_IDLE


def test_a_missing_sessions_directory_is_unknown_not_dead(tmp_path, monkeypatch):
    """No directory to read is "cannot see", not "nothing is running".

    ``claude_code_session_map`` returns ``{}`` for an absent directory and for
    an empty one alike, so without this check every session on a node without
    ``~/.claude`` — a container with no mount, the hosted dashboard, a daemon
    running as another user — reports dead, and every live agent gets a
    "Finished" badge. Found by pointing the probe at an empty HOME and
    watching five busy sessions flip to Finished.
    """
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(tmp_path / "nope"))
    pc._CLAUDE_MAP_CACHE.update({"key": None, "at": 0.0, "map": {}})
    assert pc.session_live_state("claude_code", "claude_code:anything") is None


def test_an_empty_but_present_directory_still_means_dead(claude_sessions_dir):
    """The directory exists and lists nothing: that IS the answer."""
    assert pc.session_live_state("claude_code", "claude_code:gone") == LIVE_DEAD
