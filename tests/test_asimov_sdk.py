"""Exercise instrumentation with actual official SDK classes and an offline wire."""

import dataclasses
import json
import time

import pytest

sdk = pytest.importorskip("menlo.asimov")

from clawmetry.asimov import observe
from clawmetry.asimov.sdk import normalize_state


@pytest.fixture(scope="session", autouse=True)
def server():
    """SDK unit tests use only the documented offline transport seam."""
    yield None


def sample(sequence=1):
    from menlo.asimov.robots import ASIMOV_1_BIPED_JOINTS

    return sdk.State(
        mode=sdk.Mode.STAND,
        joints=tuple(sdk.Joint(n, 0.0, None, 2.0, None) for n in ASIMOV_1_BIPED_JOINTS),
        gravity=(0, 0, -1),
        gyro=None,
        quat=None,
        error_flags=0,
        alerts=(),
        sequence=sequence,
        fw_timestamp_us=sequence * 10000,
        protocol_version=1,
    )


class OfflineWire:
    """SDK's Transport protocol seam; no network or robot is represented by this wire."""

    kind = "udp"
    endpoint = "offline-sdk-unit-test"
    capabilities = frozenset({"drive", "state"})
    default_outcome_timeout = 0.0

    def __init__(self):
        self.sent = []
        self.closed = 0

    def subscribe_state(self, callback):
        self.on_state = callback

    def subscribe_outcome(self, callback):
        pass

    def subscribe_controller_change(self, callback):
        pass

    def open(self):
        self.on_state(sample())

    def close(self):
        self.closed += 1

    def send(self, command):
        self.sent.append(command)
        return len(self.sent)


def test_actual_sdk_returns_exceptions_callbacks_and_ownership(tmp_path):
    """Exercise synchronous instrumentation through the actual SDK and offline wire.

    AC-ASIMOV-003.1: requests, returns and exceptions preserve application semantics.
    AC-ASIMOV-003.2: sent command evidence remains unknown, not acknowledged movement.
    AC-ASIMOV-003.3: instance methods are wrapped only inside the explicit context.
    """
    wire = OfflineWire()
    robot = sdk.Robot(wire)
    robot.open()
    states = []

    def callback(state):
        states.append(state)
        return "application-result"

    robot.on_state = callback
    original_stand = robot.stand
    assert "stand" not in robot.__dict__
    with observe(robot, robot_id="robot", journal_dir=tmp_path) as recorder:
        assert robot.on_state(sample(2)) == "application-result"
        sent = robot.stand(wait=False)
        assert isinstance(sent, sdk.Sent)
        assert sent.command is wire.sent[-1]
        assert sent.outcome is None
        with pytest.raises(ValueError):
            robot.set_velocity(vx=float("nan"))
        assert robot.connected and wire.closed == 0
    assert robot.on_state is callback and robot.stand == original_stand
    assert "stand" not in robot.__dict__
    assert wire.closed == 0 and robot.connected
    assert len(wire.sent) == 1
    events = [
        json.loads(line) for line in recorder.writer.path.read_text().splitlines()
    ]
    assert {
        "command.requested",
        "command.returned",
        "command.failed",
        "command.sent",
    } <= {e["kind"] for e in events}
    assert all(
        e["data"].get("outcome", "unknown") == "unknown"
        for e in events
        if e["kind"].startswith("command.")
    )
    robot.close()


@pytest.mark.parametrize(
    "marker,records_failure",
    [
        (KeyboardInterrupt(), False),
        (SystemExit(13), False),
        (ValueError("ordinary application failure"), True),
    ],
)
def test_process_control_exceptions_propagate_without_failure_recording(
    tmp_path, monkeypatch, marker, records_failure
):
    """Process-control signals bypass recording after the original method raises.

    AC-ASIMOV-003.1: signal and ordinary-error exception objects keep their identity.

    A deliberately raising method on an actual SDK Robot tests wrapper behavior
    without opening a transport or issuing any robot command.
    """
    robot = sdk.Robot(sdk.ConnectionConfig(udp=sdk.UdpConfig(host="192.0.2.1")))

    def original():
        raise marker

    monkeypatch.setattr(robot, "stand", original)
    recorded = []
    with observe(robot, robot_id="robot", journal_dir=tmp_path) as recorder:
        monkeypatch.setattr(
            recorder, "_safe_emit", lambda kind, data, **clocks: recorded.append(kind)
        )
        with pytest.raises(type(marker)) as caught:
            robot.stand()
        assert caught.value is marker
        expected = (
            ["command.requested", "command.failed"]
            if records_failure
            else ["command.requested"]
        )
        assert recorded == expected
    assert robot.stand is original


def test_original_callback_exception_survives_and_new_callbacks_are_not_clobbered(
    tmp_path,
):
    """Application callbacks retain their return/exception and replacement ownership.

    AC-ASIMOV-003.1: original callback failures are propagated unchanged.
    """
    robot = sdk.Robot(sdk.ConnectionConfig(udp=sdk.UdpConfig(host="192.0.2.1")))
    marker = ValueError("original callback failure")

    def original(state):
        raise marker

    robot.on_state = original
    with observe(robot, robot_id="robot", journal_dir=tmp_path) as recorder:
        with pytest.raises(ValueError) as exc:
            robot.on_state(sample())
        assert exc.value is marker
        replacement = lambda s: None
        robot.on_state = replacement
    assert robot.on_state is replacement
    assert recorder.status()["written"] >= 3


def test_duplicate_samples_do_not_refresh_freshness_and_faults_bypass_sample_bucket(
    tmp_path,
):
    """A repeated source sample cannot pretend telemetry advanced.

    AC-ASIMOV-002.4: nonadvancing state records a gap and a later sample restores it.
    AC-ASIMOV-002.3: missing velocity/orientation stay null while current keeps amp units.
    """
    robot = sdk.Robot(sdk.ConnectionConfig(udp=sdk.UdpConfig(host="192.0.2.1")))
    with observe(
        robot, robot_id="robot", journal_dir=tmp_path, trace_commands=False
    ) as recorder:
        first = sample()
        robot.on_state(first)
        advanced_at = recorder._last_advanced_at
        robot.on_state(first)
        assert recorder._last_advanced_at == advanced_at
        recorder._last_advanced_at = time.monotonic() - 10
        assert recorder.check_freshness() >= 10
        robot.on_state(
            dataclasses.replace(sample(2), mode=sdk.Mode.FAULT_DAMP, error_flags=1)
        )
    events = [
        json.loads(line) for line in recorder.writer.path.read_text().splitlines()
    ]
    assert len([e for e in events if e["kind"] == "observation"]) == 2
    assert {"telemetry.lost", "telemetry.restored"} <= {e["kind"] for e in events}
    data = normalize_state(first)
    assert data["joints"][0]["velocity_rad_s"] is None
    assert data["joints"][0]["current_amp"] == 2.0
    assert data["base"]["quaternion_wxyz"] is None
