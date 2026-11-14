"""Import real SDK output and bounded damaged recordings without fake SDK modules."""

import json

import pytest

from clawmetry.asimov.recording import import_recording


@pytest.fixture(scope="session", autouse=True)
def server():
    """Offline imports need no dashboard or ambient credentials."""
    yield None


def state_row():
    return {
        "kind": "state",
        "t": 12345.2,
        "mode": "STAND",
        "sequence": 1,
        "fw_timestamp_us": 900000,
        "received_at": 12345.1,
        "edge_timestamp_us": 0,
        "protocol_version": 1,
        "error_flags": 0,
        "joints": [
            {"name": "L_Knee", "pos": 0.25, "vel": None, "current": 1.2, "temp": 30.0}
        ],
        "gravity": [0, 0, -1],
        "gyro": None,
        "quat": None,
        "battery": None,
        "alerts": [],
    }


def test_import_retains_source_clocks_without_guessing_epoch_and_reuses_run(tmp_path):
    """Imported source clocks and identity remain separate from current receipt.

    AC-ASIMOV-004.1: recording state, command identity and source timing are retained.
    AC-ASIMOV-004.3: replay reuses the same run and leaves its evidence unchanged.
    AC-ASIMOV-003.2: a recorded send has an unknown outcome.
    """
    source = tmp_path / "run.jsonl"
    source.write_text(
        json.dumps(state_row())
        + "\n"
        + json.dumps(
            {
                "kind": "sent",
                "t": 12345.7,
                "name": "set_velocity",
                "sequence": 4,
                "command": {"vx": 0.1, "vy": 0, "vyaw": 0},
            }
        )
        + "\n"
    )
    journal_dir = tmp_path / "journals"
    result = import_recording(source, robot_id="my-asimov", directory=journal_dir)
    path = journal_dir / (result["run_id"] + ".jsonl")
    original = path.read_bytes()
    events = [json.loads(line) for line in original.splitlines()]
    observation = next(e for e in events if e["kind"] == "observation")
    assert observation["data"]["source_timestamp_s"] == 12345.2
    assert observation["data"]["received_at_monotonic_s"] == 12345.1
    assert int(observation["wall_time_ns"]) > 10**18
    assert observation["data"]["historical"] is True
    assert "source_wall_time_ns" not in observation["data"]
    assert observation["data"]["joints"][0]["velocity_rad_s"] is None
    assert "torque" not in json.dumps(observation)
    command = next(e for e in events if e["kind"] == "command.sent")
    assert command["data"]["outcome"] == "unknown"
    assert result["source_duration_s"] == 0.5
    again = import_recording(source, robot_id="my-asimov", directory=journal_dir)
    assert again["run_id"] == result["run_id"] and again["replayed"]
    assert path.read_bytes() == original


def test_malformed_oversized_and_truncated_rows_are_visible(tmp_path):
    """Damaged lines are skipped while later valid evidence remains importable.

    AC-ASIMOV-004.2: malformed, oversized and truncated input yields incomplete status.
    """
    source = tmp_path / "bad.jsonl"
    source.write_bytes(
        b"not json\n"
        + b"x" * 70000
        + b"\n"
        + json.dumps(state_row()).encode()
        + b'\n{"kind":'
    )
    result = import_recording(source, robot_id="robot", directory=tmp_path / "journal")
    assert result["imported_records"] == 1
    assert result["skipped_records"] == 3
    assert result["incomplete"] and result["errors"]


def test_official_sdk_recording_output_imports_all_actuators(tmp_path):
    """Normalize recording output from actual SDK classes, without hardware claims.

    AC-ASIMOV-002.2: all 25 SDK actuator samples, orientation, battery and alerts survive.
    AC-ASIMOV-002.3: absent SDK measurements remain unavailable rather than becoming zero.
    AC-ASIMOV-004.1: official SDK Recording output imports directly.
    """
    import pytest

    sdk = pytest.importorskip("menlo.asimov")
    from menlo.asimov.robots import ASIMOV_1_BIPED_JOINTS

    robot = sdk.Robot(sdk.ConnectionConfig(udp=sdk.UdpConfig(host="192.0.2.1")))
    state = sdk.State(
        mode=sdk.Mode.FAULT_DAMP,
        joints=tuple(
            sdk.Joint(name, 0.2, None, None, 35.0) for name in ASIMOV_1_BIPED_JOINTS
        ),
        gravity=(0, 0, -1),
        gyro=None,
        quat=(1, 0, 0, 0),
        error_flags=3,
        alerts=(sdk.Alert(2, 0, 81.0, 80.0, 3),),
        sequence=1,
        fw_timestamp_us=1000,
        protocol_version=1,
        battery=sdk.Battery(48, -2, 70, 30, sdk.BatteryProtection(0)),
    )
    source = tmp_path / "official.jsonl"
    with robot.record(source):
        robot._on_state(state)
        robot._on_sent(
            sdk.Sent(
                name="stand",
                sequence=3,
                command=sdk.ModeCommand("stand"),
                clamped=False,
                default_timeout=0,
            )
        )
    result = import_recording(source, robot_id="robot", directory=tmp_path / "journal")
    with open(result["path"], encoding="utf-8") as fh:
        events = [json.loads(line) for line in fh]
    observation = next(e["data"] for e in events if e["kind"] == "observation")
    assert len(observation["joints"]) == 25
    assert [joint["name"] for joint in observation["joints"]] == list(
        ASIMOV_1_BIPED_JOINTS
    )
    assert all(
        joint["position_rad"] == 0.2
        and joint["velocity_rad_s"] is None
        and joint["current_amp"] is None
        and joint["temperature_c"] == 35.0
        for joint in observation["joints"]
    )
    assert observation["base"] == {
        "quaternion_wxyz": [1, 0, 0, 0],
        "angular_velocity_rad_s": None,
        "gravity_body": [0, 0, -1],
    }
    assert observation["battery"]["protection_flags"] is None
    assert observation["battery"]["voltage_v"] == 48
    assert observation["battery"]["current_amp"] == -2
    assert observation["battery"]["soc_percent"] == 70
    assert observation["battery"]["max_cell_temperature_c"] == 30
    assert observation["alerts"][0]["id"] == 2
    assert observation["alerts"][0]["severity"] == 0
    assert observation["alerts"][0]["value"] == 81.0
    assert observation["alerts"][0]["threshold"] == 80.0
    assert observation["mode"] == "FAULT_DAMP" and observation["faulted"]
