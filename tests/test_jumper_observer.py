"""Built-in telemetry, boundary decisions and malformed-source qualification."""

import json
from pathlib import Path

import pytest

from clawmetry.physical_ai import DeskMonitor, JumperObserver, Request, Task, TaskGate
from clawmetry.physical_ai.adapters.jumper import normalize
from clawmetry.physical_ai.cli import main


def frame(stamp=1., **changes):
    data = {"time_s": stamp, "finite": True, "evidence_kind": "simulation",
            "position_m": [0, 0, .1], "quat_wxyz": [1, 0, 0, 0], "tilt_deg": 0.,
            "joint_positions_rad": {"left_gripper": 0., "right_hip": .2},
            "joint_velocities_rad_s": {"left_gripper": 0.},
            "joint_torques_nm": {"right_hip": .3},
            "collision_aabb_m": {"min": [-.2, -.2, 0.], "max": [.2, .2, .25]},
            "table_bounds_m": {"min": [-.86, -.58, 0.], "max": [.86, .58, 0.]},
            "table_margin_m": .38}
    data.update(changes)
    return data


def events(observer):
    return [json.loads(line) for line in Path(observer.status()["path"]).read_text().splitlines()]


def gate(**kwargs):
    return TaskGate(Task("desk", frozenset({"wave", "walk", "carry_glass"})),
                    supported_actions={"wave"}, **kwargs)


def test_named_joints_and_missing_hardware_measurements_are_not_inferred():
    result = normalize({"joint_positions_rad": {"b": 1, "a": 0}}, evidence_kind="hardware")
    assert result["joints"] == [{"name": "b", "position_rad": 1.}, {"name": "a", "position_rad": 0.}]
    assert result["base"] == {}
    assert "table_margin_m" not in result
    assert result["hardware_verified"] is False


@pytest.mark.parametrize("change", [
    {"joint_positions_rad": {"a": float("nan")}},
    {"joint_positions_rad": [0, 1]}, {"joint_positions_rad": {"a": True}},
    {"time_s": float("inf")}, {"finite": "true"}, {"base": []},
    {"joints": [{"name": "a"}, {"name": "a"}], "joint_positions_rad": {},
     "joint_velocities_rad_s": {}, "joint_torques_nm": {}},
])
def test_bad_callback_input_is_bounded_and_does_not_interrupt_robot(tmp_path, change):
    with JumperObserver("desk", environment="simulation", directory=tmp_path) as observer:
        for _ in range(20):
            assert observer.observe(frame(**change)) is None
        assert observer.observe(frame(2.)) is not None
    recorded = events(observer)
    assert sum(row["kind"] == "observation.invalid" for row in recorded) == 1
    assert sum(row["kind"] == "observation" for row in recorded) == 1


def test_read_only_and_explicit_skill_gate_with_real_receipts_distinct(tmp_path):
    with JumperObserver("desk", environment="simulation", directory=tmp_path) as observer:
        state = observer.observe(frame())
        read = observer.decide(gate(), Request("one", "desk", "wave"), state, now_s=1.)
        allowed = observer.decide(gate(controls_enabled=True), Request("two", "desk", "wave"), state, now_s=1.)
        unavailable = observer.decide(gate(controls_enabled=True), Request("three", "desk", "walk"), state, now_s=1.)
        denied = observer.decide(gate(controls_enabled=True), Request("four", "desk", "jump"), state, now_s=1.)
    assert read.status == "observed" and not read.send_to_controller
    assert allowed.status == "allowed" and allowed.send_to_controller
    assert unavailable.status == "unavailable" and denied.status == "denied"
    assert not any(row["kind"] == "controller.receipt" for row in events(observer))
    assert all(not d.physical_stop_confirmed for d in (read, allowed, unavailable, denied))


def test_hardware_cannot_enable_motion_by_reusing_simulator_gate(tmp_path):
    with JumperObserver("desk", environment="hardware", directory=tmp_path) as observer:
        state = frame(evidence_kind="hardware")
        observer.observe(state)
        decision = observer.decide(gate(controls_enabled=True), Request("one", "desk", "wave"), state, now_s=1.)
    assert decision.status == "unavailable" and not decision.send_to_controller


@pytest.mark.parametrize("changes", [
    {"table_margin_m": .5}, {"finite": False}, {"time_s": 1.2},
    {"table_bounds_m": {"min": [-1, -1, 0], "max": [1, 1, 0]}, "table_margin_m": .8},
    {"collision_aabb_m": {"min": [-.2, -.2, 0], "max": [.2, .2, 0]}},
])
def test_unverified_clearance_never_authorizes_a_request(changes):
    decision = gate(controls_enabled=True).decide(Request("one", "desk", "wave"), frame(**changes), now_s=1.)
    assert decision.status == "unknown" and not decision.send_to_controller


def test_request_id_and_authorized_scope_cannot_be_reused_or_mutated():
    actions = {"wave"}
    task = Task("desk", actions)
    actions.add("jump")
    assert "jump" not in task.actions
    subject = TaskGate(task, controls_enabled=True, supported_actions={"wave"})
    request = Request("same", "desk", "wave")
    assert subject.decide(request, frame(), now_s=1.).status == "allowed"
    assert subject.decide(request, frame(), now_s=1.).status == "denied"
    assert subject.decide(Request("other", "wrong-task", "wave"), frame(), now_s=1.).status == "denied"
    assert subject.decide(Request("object", "desk", "wave", object_id="cup"), frame(), now_s=1.).status == "denied"


def test_continuous_monitor_episodes_and_missing_telemetry(tmp_path):
    with JumperObserver("desk", environment="simulation", directory=tmp_path,
                        monitor=DeskMonitor()) as observer:
        observer.observe(frame())
        lifted = frame(1.01, position_m=[0, 0, .2], tilt_deg=50)
        observer.observe(lifted)
        observer.observe(dict(lifted, time_s=1.02))
        observer.check(2.)
        observer.check(3.)
        observer.observe(frame(3.01))
    findings = [row["data"]["kind"] for row in events(observer) if row["kind"] == "guard.incident"]
    assert findings == ["unexpected_lift", "excessive_tilt", "observation_lost"]
    assert any(row["kind"] == "observation.restored" for row in events(observer))


def test_recordings_keep_their_origin_and_never_look_like_live_danger(tmp_path, capsys):
    source = tmp_path / "frames.jsonl"
    source.write_text(json.dumps(frame()) + "\n")
    assert main(["import-recording", str(source), "--robot-id", "desk", "--environment", "simulation",
                 "--journal-dir", str(tmp_path / "journal")]) == 0
    result = json.loads(capsys.readouterr().out)
    rows = [json.loads(line) for line in Path(result["path"]).read_text().splitlines()]
    start = rows[0]
    observation = next(row["data"] for row in rows if row["kind"] == "observation")
    assert start["data"]["source_kind"] == "jumper_recording"
    assert observation["evidence_kind"] == "recording"
    assert observation["recorded_environment"] == "simulation"


def test_simulation_recording_cannot_be_relabelled_hardware(tmp_path):
    with JumperObserver("desk", environment="hardware", recording=True, directory=tmp_path) as observer:
        assert observer.observe(frame()) is None
    assert not any(row["kind"] == "observation" for row in events(observer))


def test_physical_incident_link_opens_its_own_evidence(monkeypatch):
    from clawmetry import desktop_notify
    from clawmetry.incident_alerts import _session_url
    monkeypatch.setattr(desktop_notify, "dashboard_url", lambda **kw: "http://127.0.0.1:8900/?token=old")
    assert _session_url("physical_ai:" + "a" * 32) == "http://127.0.0.1:8900/physical-ai?run=" + "a" * 32
    assert _session_url("physical_ai:../escape") == ""


def test_deeply_nested_source_row_does_not_crash_cli(tmp_path, capsys):
    source = tmp_path / "deep.jsonl"
    source.write_text("[" * 15000 + "0" + "]" * 15000 + "\n" + json.dumps(frame()) + "\n")
    assert main(["import-recording", str(source), "--robot-id", "desk", "--environment", "simulation",
                 "--journal-dir", str(tmp_path / "journal")]) == 2
    result = json.loads(capsys.readouterr().out)
    assert result["accepted_frames"] == 1 and result["invalid_frames"] == 1
    assert result["flushed"] is True


def test_status_ignores_malformed_health_files(tmp_path, capsys):
    for index, content in enumerate(("[]", "null", '{"source_kind": []}', "[" * 15000 + "0" + "]" * 15000)):
        (tmp_path / (str(index) + ".status.json")).write_text(content)
    assert main(["status", "--journal-dir", str(tmp_path)]) == 0
    assert json.loads(capsys.readouterr().out) == {"recorders": []}


def test_optional_source_clock_does_not_stall_observation_sampling(tmp_path):
    with JumperObserver("desk", environment="simulation", directory=tmp_path) as observer:
        observer.observe({"joint_positions_rad": {"a": 0}})
        observer.observe(frame(.1))
        observer.observe(frame(.2))
    observations = [e["data"] for e in events(observer) if e["kind"] == "observation"]
    assert len(observations) == 3
    assert "time_s" not in observations[0]
    assert [o.get("time_s") for o in observations[1:]] == [.1, .2]
