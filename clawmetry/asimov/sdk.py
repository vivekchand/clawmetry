"""Normalize official SDK evidence and explicitly instrument existing applications."""

import functools
import inspect
import logging
import threading
import time
import uuid

from .journal import JournalWriter, plain

LOG = logging.getLogger(__name__)
COMMAND_METHODS = (
    "stand",
    "balance",
    "damp",
    "set_velocity",
    "trajectory",
    "set_joints",
)
CALLBACKS = ("on_state", "on_alert", "on_mode_change", "on_link_lost", "_on_sent")


def normalize_state(state):
    """Retain measured units, absent values and separate source clock domains."""
    raw = plain(state)
    if (
        not isinstance(raw, dict)
        or not isinstance(raw.get("joints"), list)
        or not raw["joints"]
    ):
        raise ValueError("A state sample must contain reported joints")
    if len(raw["joints"]) > 256:
        raise ValueError("State contains too many joints")
    joints = []
    for index, joint in enumerate(raw["joints"]):
        if not isinstance(joint, dict):
            raise TypeError("A joint sample must be an object")
        joints.append(
            {
                "name": joint.get("name") or "joint_" + str(index),
                "position_rad": joint.get("pos"),
                "velocity_rad_s": joint.get("vel"),
                "current_amp": joint.get("current"),
                "temperature_c": joint.get("temp"),
            }
        )
    alerts = raw.get("alerts") or []
    if not isinstance(alerts, list):
        raise TypeError("Alerts must be a list")
    # Alert.name is a property rather than a dataclass field.
    for index, alert in enumerate(alerts):
        if not isinstance(alert, dict):
            raise TypeError("An alert must be an object")
        originals = getattr(state, "alerts", ())
        alert["name"] = (
            getattr(originals[index], "name", None)
            if index < len(originals)
            else alert.get("name")
        )
    battery = raw.get("battery")
    if battery is not None:
        if not isinstance(battery, dict):
            raise ValueError("Battery must be an object or null")
        battery = {
            "voltage_v": battery.get("voltage_v"),
            "current_amp": battery.get("current_a"),
            "soc_percent": battery.get("soc_percent"),
            "max_cell_temperature_c": battery.get("max_cell_temp_c"),
            "protection_flags": battery.get("protection"),
        }
        original = getattr(state, "battery", None)
        if original is not None:
            battery["protection_bits"] = int(original.protection)
    mode = raw.get("mode")
    data = {
        "mode": mode,
        "joints": joints,
        "observation": {j["name"] + ".pos": j["position_rad"] for j in joints},
        "base": {
            "quaternion_wxyz": raw.get("quat"),
            "angular_velocity_rad_s": raw.get("gyro"),
            "gravity_body": raw.get("gravity"),
        },
        "battery": battery,
        "alerts": alerts,
        "error_flags": raw.get("error_flags"),
        "source_sequence": raw.get("sequence"),
        "protocol_version": raw.get("protocol_version"),
        "fw_timestamp_us": raw.get("fw_timestamp_us"),
        "received_at_monotonic_s": raw.get("received_at"),
        "edge_timestamp_us": raw.get("edge_timestamp_us"),
        "source_clock": "sdk_monotonic_and_firmware; edge_timestamp_us_is_epoch_when_positive",
    }
    edge = raw.get("edge_timestamp_us")
    if isinstance(edge, int) and 0 < edge < (2**63) // 1000:
        data["source_wall_time_ns"] = str(edge * 1000)
    data["faulted"] = (
        mode in ("FAULT_DAMP", 5)
        or bool(raw.get("error_flags"))
        or any(a.get("severity") == 0 for a in alerts)
    )
    return data


class SdkObserver:
    """An opt-in context manager that never connects, closes or drives its Robot."""

    def __init__(
        self,
        robot,
        *,
        robot_id,
        journal_dir=None,
        environment="hardware",
        sample_hz=1.0,
        trace_commands=True,
        raw_hz=0.0,
        writer=None,
        source_scope="instrumented_application",
    ):
        if not (0 < sample_hz <= 10) or not (0 <= raw_hz <= 10):
            raise ValueError(
                "Sample rates must be between 0 and 10 Hz, with sampling enabled"
            )
        self.robot = robot
        self.robot_id = robot_id
        self.sample_period = 1.0 / sample_hz
        self.raw_period = 1.0 / raw_hz if raw_hz else None
        self.trace_commands = trace_commands
        self.writer = writer or JournalWriter(
            robot_id,
            "asimov_sdk",
            directory=journal_dir,
            environment=environment,
            metadata={
                "observation_only": True,
                "application_commands_traced": trace_commands,
                "source_scope": source_scope,
                "sample_hz": sample_hz,
                "raw_hz": raw_hz,
            },
        )
        self._owned_writer = writer is None
        self._installed = []
        self._entered = False
        self._sample_at = self._raw_at = float("-inf")
        self._last_signature = None
        self._sample_lock = threading.Lock()
        self._last_sequence = None
        self._last_advanced_at = None
        self._lost = False

    def _safe_emit(self, kind, data, **clocks):
        try:
            return self.writer.emit(kind, data, **clocks)
        except Exception:  # noqa: BLE001 - observation must preserve the application's control flow
            LOG.warning("Asimov evidence could not be queued")
            return False

    def _state(self, state, clocks=None):
        try:
            data = normalize_state(state)
            now = time.monotonic()
            sequence = (data["source_sequence"], data["fw_timestamp_us"])
            with self._sample_lock:
                if sequence == self._last_sequence and any(sequence):
                    return
                self._last_sequence = sequence
                self._last_advanced_at = now
                if self._lost:
                    self._safe_emit(
                        "telemetry.restored", {"source": "accepted_sdk_state"}
                    )
                    self._lost = False
                alert_identity = tuple(
                    sorted(
                        (
                            str(a.get("id")),
                            str(a.get("source_id")),
                            str(a.get("severity")),
                            str(a.get("first_set_us")),
                        )
                        for a in data["alerts"]
                    )
                )
                signature = (data["mode"], data["error_flags"], alert_identity)
                changed = signature != self._last_signature
                self._last_signature = signature
                if changed or now - self._sample_at >= self.sample_period:
                    self._safe_emit("observation", data, **(clocks or {}))
                    self._sample_at = now
                elif (
                    self.raw_period is not None
                    and now - self._raw_at >= self.raw_period
                ):
                    self._safe_emit("observation.raw", data, **(clocks or {}))
                    self._raw_at = now
        except Exception:  # noqa: BLE001 - malformed evidence must never escape an SDK callback
            self.writer._loss("Unsupported state sample was skipped")
            self._safe_emit(
                "run.health",
                {"incomplete": True, "error": "Unsupported state sample was skipped"},
            )

    def check_freshness(self, stale_after=3.0):
        """Record a gap only after an actually advancing sample becomes stale."""
        with self._sample_lock:
            age = (
                time.monotonic() - self._last_advanced_at
                if self._last_advanced_at is not None
                else None
            )
            if age is not None and age > stale_after and not self._lost:
                self._lost = True
                self._safe_emit(
                    "telemetry.lost", {"reason": "No new accepted state", "age_s": age}
                )
            return age

    def _callback_evidence(self, name, args, clocks):
        if name == "on_state":
            self._state(args[0], clocks)
        elif name == "_on_sent":
            sent = args[0]
            self._safe_emit(
                "command.sent",
                {
                    "name": sent.name,
                    "source_sequence": sent.sequence,
                    "command": plain(sent.command),
                    "clamped": sent.clamped,
                    "outcome": "unknown",
                    "evidence": "sdk_transport_accepted_for_sending",
                    "sent_at_monotonic_s": sent.sent_at,
                },
            )
        elif name == "on_alert":
            alert, transition = args
            data = plain(alert)
            data["name"] = getattr(alert, "name", None)
            self._safe_emit("alert." + str(transition), data)
        elif name == "on_mode_change":
            self._safe_emit(
                "mode.changed", {"previous": plain(args[0]), "current": plain(args[1])}
            )
        elif name == "on_link_lost":
            self._lost = True
            self._safe_emit(
                "telemetry.lost", {"reason": "SDK connection stopped receiving state"}
            )

    def _install_callback(self, name):
        original = getattr(self.robot, name, None)

        @functools.wraps(original if callable(original) else self._state)
        def wrapper(*args, **kwargs):
            clocks = {"wall_time_ns": time.time_ns(), "monotonic_ns": time.monotonic_ns()}
            try:
                return original(*args, **kwargs) if original is not None else None
            finally:
                try:
                    self._callback_evidence(name, args, clocks)
                except Exception:  # noqa: BLE001 - preserve an original callback's exception
                    self._safe_emit(
                        "run.health",
                        {"incomplete": True, "error": "Callback evidence was skipped"},
                    )

        self._replace(name, original, wrapper)

    def _replace(self, name, original, wrapper):
        had_local = name in getattr(self.robot, "__dict__", {})
        setattr(self.robot, name, wrapper)
        self._installed.append((name, original, wrapper, had_local))

    def _install_method(self, name):
        original = getattr(self.robot, name, None)
        if not callable(original):
            return

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            call_id = uuid.uuid4().hex
            try:
                parameters = dict(
                    inspect.signature(original).bind(*args, **kwargs).arguments
                )
                self._safe_emit(
                    "command.requested",
                    {
                        "call_id": call_id,
                        "name": name,
                        "parameters": plain(parameters),
                        "outcome": "unknown",
                    },
                )
            except Exception:  # noqa: BLE001 - tracing must not prevent the original SDK call
                self._safe_emit(
                    "command.requested",
                    {
                        "call_id": call_id,
                        "name": name,
                        "parameters_available": False,
                        "outcome": "unknown",
                    },
                )
            try:
                result = original(*args, **kwargs)
            except Exception as exc:
                self._safe_emit(
                    "command.failed",
                    {
                        "call_id": call_id,
                        "name": name,
                        "exception_type": type(exc).__name__,
                        "outcome": "unknown",
                    },
                )
                raise
            self._safe_emit(
                "command.returned",
                {
                    "call_id": call_id,
                    "name": name,
                    "source_sequence": getattr(result, "sequence", None),
                    "outcome": "unknown",
                },
            )
            return result

        self._replace(name, original, wrapper)

    def __enter__(self):
        if self._entered:
            raise RuntimeError("An observation context cannot be entered twice")
        self._entered = True
        try:
            for name in CALLBACKS:
                if name != "_on_sent" or self.trace_commands:
                    self._install_callback(name)
            if self.trace_commands:
                for name in COMMAND_METHODS:
                    self._install_method(name)
        except Exception:
            self.__exit__(None, None, None)
            raise
        return self

    def status(self):
        return self.writer.status()

    def __exit__(self, *exc):
        for name, original, wrapper, had_local in reversed(self._installed):
            if getattr(self.robot, name, None) is wrapper:
                if had_local:
                    setattr(self.robot, name, original)
                else:
                    delattr(self.robot, name)
        self._installed = []
        if self._owned_writer:
            self.writer.close()


def observe(robot, **kwargs):
    """Explicitly observe an existing Robot and preserve its application behavior."""
    return SdkObserver(robot, **kwargs)
