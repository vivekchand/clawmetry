"""Stable evidence and positive recovery across moving detector windows."""
from __future__ import annotations

import pytest

from clawmetry import detectors


@pytest.fixture(scope="session", autouse=True)
def server():
    yield None


def event(i, kind="tool_call", **data):
    return {"id": f"event-{i}", "node_id": "node-a", "agent_type": "codex",
            "session_id": "codex:session", "event_type": kind,
            "ts": f"2026-10-02T10:00:{i:02d}Z", "data": data}


def detect(chronological):
    return detectors.run_all(list(reversed(chronological)), "codex:session", "codex")


def test_stable_references_resolve_original_events_after_window_moves():
    events = [event(i, tool="Read", args={"path": "same"}, call_id=f"c{i}")
              for i in range(1, 4)]
    incident = next(i for i in detect(events) if i["kind"] == "stuck_loop")
    assert [r["event_id"] for r in incident["evidence_refs"]] == ["event-1", "event-2", "event-3"]
    assert incident["evidence_refs"][0]["tool_call_id"] == "c1"
    shifted = next(i for i in detect([event(0, "user", content="hello")] + events)
                   if i["kind"] == "stuck_loop")
    assert shifted["evidence_refs"] == incident["evidence_refs"]


def test_parallel_results_follow_native_call_ids_not_last_tool():
    events = []
    for i in range(3):
        base = i * 4
        events += [event(base, tool="Bash", args={"cmd": "test"}, call_id=f"b{i}"),
                   event(base + 1, tool="Read", args={"path": "x"}, call_id=f"r{i}"),
                   event(base + 2, "tool_result", tool_call_id=f"b{i}", is_error=True),
                   event(base + 3, "tool_result", tool_call_id=f"r{i}", is_error=False)]
    failure = next(i for i in detect(events) if i["kind"] == "repeated_tool_failure")
    assert failure["evidence"]["tool"] == "Bash"
    assert [r["event_id"] for r in failure["evidence_refs"]] == ["event-2", "event-6", "event-10"]


def test_success_resets_only_its_own_tool_failure_streak():
    events = [event(i, "tool_result", tool="Bash", is_error=True) for i in range(3)]
    assert any(i["kind"] == "repeated_tool_failure" for i in detect(events))
    assert any(i["kind"] == "repeated_tool_failure" for i in detect(
        events + [event(4, "tool_result", tool="Read", is_error=False)]))
    assert not any(i["kind"] == "repeated_tool_failure" for i in detect(
        events + [event(4, "tool_result", tool="Bash", is_error=False)]))


def test_family_native_extra_identity_pairs_results_and_resets_failure_streak():
    events = []
    for i in range(4):
        cid = f"native-{i}"
        events.extend([
            event(i * 2, tool_name="exec", tool_calls=[{"id": cid, "name": "exec", "arguments": None}],
                  extra={"callId": cid}),
            event(i * 2 + 1, "tool_result", role="tool", content="",
                  extra={"callId": cid, "isError": i < 3}),
        ])
    steps = detectors.normalize_events(list(reversed(events)))
    assert len(steps) == 8
    results = [step for step in steps if step["kind"] == "tool_result"]
    assert all(step["relationship"] == "native" and step["tool"] == "exec" for step in results)
    assert [step["is_error"] for step in results] == [True, True, True, False]
    assert all(step["outcome_known"] for step in results)
    assert any(row["kind"] == "repeated_tool_failure" for row in detect(events[:6]))
    assert not any(row["kind"] == "repeated_tool_failure" for row in detect(events))


def test_unknown_parallel_result_is_not_assigned_to_most_recent_call():
    steps = detectors.normalize_events(list(reversed([
        event(1, tool="Bash", call_id="b"), event(2, tool="Read", call_id="r"),
        event(3, "tool_result", tool_call_id="not-seen", is_error=True)])))
    assert steps[-1]["tool"] == ""
    assert steps[-1]["relationship"] == "unavailable"


def test_search_cycles_with_different_arguments_are_not_loops():
    events = []
    for i in range(3):
        events += [event(i * 2, tool="Search", args={"q": f"topic-{i}"}),
                   event(i * 2 + 1, tool="Read", args={"path": f"result-{i}"})]
    assert detectors.stuck_loop(list(reversed(events)), "codex:session") is None


def test_missing_arguments_cannot_prove_identical_call_loop():
    unknown = [event(i, tool="exec", call_id=f"c{i}") for i in range(3)]
    assert detectors.stuck_loop(list(reversed(unknown)), "codex:session") is None
    explicit_empty = [event(i, tool="List", args={}, call_id=f"c{i}") for i in range(3)]
    assert detectors.stuck_loop(list(reversed(explicit_empty)), "codex:session") is not None


def test_successful_edit_test_cycles_are_progress():
    events = []
    for i in range(3):
        events += [event(i * 4, tool="Edit", args={"path": "f"}, call_id=f"e{i}"),
                   event(i * 4 + 1, "tool_result", call_id=f"e{i}", is_error=False),
                   event(i * 4 + 2, tool="Bash", args={"cmd": "test"}, call_id=f"t{i}"),
                   event(i * 4 + 3, "tool_result", call_id=f"t{i}", is_error=False)]
    assert detectors.stuck_loop(list(reversed(events)), "codex:session") is None


def test_narration_after_failed_retries_does_not_hide_or_recover_a_loop():
    from clawmetry.incident_evidence import positive_recovery
    events = []
    for i in range(3):
        events += [event(i * 3, tool="Bash", args={"cmd": "test"}, call_id=f"retry-{i}"),
                   event(i * 3 + 1, "tool_result", call_id=f"retry-{i}", is_error=True),
                   event(i * 3 + 2, "assistant", content="Trying the same command again.")]
    assert any(row["kind"] == "stuck_loop" for row in detect(events))
    steps = detectors.normalize_events(list(reversed(events)))
    episode = {"kind": "stuck_loop", "last_evidence_at": steps[-3]["ts"],
               "evidence": {"call_signatures": [["Bash", steps[-3]["args_hash"]]]}}
    assert positive_recovery(episode, steps) is None
    events += [event(9, tool="Edit", args={"path": "test"}, call_id="fix"),
               event(10, "tool_result", call_id="fix", is_error=False)]
    proof = positive_recovery(episode, detectors.normalize_events(list(reversed(events))))
    assert proof["event_id"] == "event-10"


def test_missing_result_does_not_prove_loop_recovered():
    from clawmetry.incident_evidence import positive_recovery
    episode = {"kind": "stuck_loop", "last_evidence_at": 1790935202000,
               "evidence": {"call_signatures": [["Read", "same"]]}}
    steps = detectors.normalize_events([event(4, tool="Edit", call_id="pending")])
    assert positive_recovery(episode, steps) is None


def test_narration_without_prior_failure_context_cannot_recover_a_loop():
    from clawmetry.incident_evidence import positive_recovery
    episode = {"kind": "stuck_loop", "last_evidence_at": 1790935202000,
               "evidence": {"call_signatures": [["Bash", "same"]]}}
    narration = event(10, "assistant", content="Trying the same command again.")
    # The failed result has fallen outside the bounded moving window.
    assert positive_recovery(episode, detectors.normalize_events([narration])) is None
    # A new user turn establishes context for subsequent text, even if the
    # old failed calls are no longer retained in this window.
    steps = detectors.normalize_events([narration, event(9, "user", content="Move on to the next task")])
    assert positive_recovery(episode, steps)['event_id'] == 'event-10'


def test_failed_detector_pass_and_empty_window_cannot_recover():
    from clawmetry.incident_evidence import reconcile_session
    class Store:
        def query_incidents(self, **kwargs):
            raise AssertionError("incomplete passes must not reconcile")
    assert reconcile_session(Store(), [], [], [], session_id="s", runtime="r",
                             node_id="n", completed=False) == {}
    assert reconcile_session(Store(), [], [], [], session_id="s", runtime="r",
                             node_id="n", completed=True) == {}


def test_runner_distinguishes_failed_check_from_successful_empty_check(monkeypatch):
    def repeated_tool_failure(*args, **kwargs):
        raise RuntimeError("unreadable result")
    monkeypatch.setattr(detectors, "_ALL_DETECTORS", (repeated_tool_failure, detectors.stuck_loop))
    completed = {}
    assert detectors.run_all([], "codex:session", inspection=completed) == []
    assert completed == {"repeated_tool_failure": False, "stuck_loop": True}


def test_disabled_check_cannot_recover_from_a_later_success():
    from clawmetry.incident_evidence import reconcile_session
    class Store:
        def query_incident_heads(self, **kwargs):
            return [{"incident_id": "inc_a", "kind": "repeated_tool_failure", "state": "active",
                     "last_evidence_at": 1790935200000, "evidence": {"tool": "Bash"}}]
        def recover_incident(self, **kwargs):
            raise AssertionError("disabled checks must not establish recovery")
    es = [event(10, "tool_result", tool="Bash", is_error=False)]
    assert reconcile_session(Store(), [], es, detectors.normalize_events(es),
                             session_id="codex:session", runtime="codex", node_id="node-a",
                             disabled={"repeated_tool_failure"}) == {}


def test_internal_detector_exception_is_not_reported_as_a_clean_pass():
    thresholds = detectors.resolve_thresholds('codex')
    thresholds['identical_k'] = 'invalid'
    completed = {}
    detectors.run_all([event(5, 'tool_result', tool='Bash', is_error=False)],
                      'codex:session', thresholds=thresholds, inspection=completed)
    assert completed['stuck_loop'] is False


def test_multiple_envelopes_of_one_native_call_are_not_a_loop_or_failure_streak():
    es = [event(i, tool='Read', args={'path': 'x'}, call_id='one-call') for i in range(3)]
    es += [event(i, 'tool_result', tool='Read', call_id='one-call', is_error=True) for i in range(3, 6)]
    assert not any(i['kind'] in ('stuck_loop', 'repeated_tool_failure') for i in detect(es))
    steps = detectors.normalize_events(list(reversed(es)))
    assert len([s for s in steps if s['kind'] == 'tool_call']) == 1
    assert len([s for s in steps if s['kind'] == 'tool_result']) == 1
