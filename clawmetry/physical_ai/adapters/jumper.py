"""Read-only Jumper telemetry bridge using the shared local robotics journal.

Accepts named SI-unit measurements from the robot/application host. It never
connects to motor topics, loads policies, installs SDKs, or sends commands.
"""

from __future__ import annotations

from dataclasses import asdict
import logging
import time

from clawmetry.asimov.journal import JournalWriter, plain
from ..measurements import number, vector

LOG = logging.getLogger(__name__)
SOURCES = {"simulation": "jumper_native", "hardware": "jumper_app"}


def normalize(frame, *, evidence_kind):
    """Keep explicit named measurements; never infer unavailable world state.

    A hardware bridge must supply joint names from its own layout.json, since
    policy and DDS wire order are distinct. No fixed numeric joint ordering is
    assumed. Torque is labelled by its host-provided provenance.
    """
    if not isinstance(frame, dict):
        raise ValueError("A Jumper frame must be an object")
    frame_kind = frame.get("evidence_kind", evidence_kind)
    if frame_kind != evidence_kind and not (evidence_kind == "recording" and frame_kind in ("hardware", "simulation")):
        raise ValueError("The frame evidence kind differs from this recorder")
    result = {"evidence_kind": evidence_kind, "hardware_verified": False,
              "physical_stop_confirmed": False, "joints": [], "base": {}}
    if evidence_kind == "recording":
        result["recorded_environment"] = frame_kind if frame_kind != "recording" else "unknown"
    if "time_s" in frame:
        stamp = number(frame["time_s"])
        if stamp < 0:
            raise ValueError("The source clock must be nonnegative")
        result["time_s"] = stamp
    # Boolean finite=false is preserved as an invalid-state finding, not
    # converted into a reassuring successful observation.
    if "finite" in frame:
        if type(frame["finite"]) is not bool:
            raise ValueError("Frame validity must be an explicit boolean")
        result["finite"] = frame["finite"]
    fields = {"joint_positions_rad": "position_rad",
              "joint_velocities_rad_s": "velocity_rad_s",
              "joint_torques_nm": "effort_nm"}
    named = {}
    for source, target in fields.items():
        values = frame.get(source, {})
        if not isinstance(values, dict) or len(values) > 128:
            raise ValueError("Joint measurements must be bounded and named")
        for name, value in values.items():
            if not isinstance(name, str) or not name or len(name) > 100:
                raise ValueError("A bounded joint name is required")
            named.setdefault(name, {"name": name})[target] = number(value)
    if "joints" in frame:
        joints = frame["joints"]
        if not isinstance(joints, list) or len(joints) > 128 or named:
            raise ValueError("Use one explicit named joint representation")
        for joint in joints:
            if not isinstance(joint, dict):
                raise ValueError("Each joint must be named")
            name = joint.get("name")
            if not isinstance(name, str) or not name or len(name) > 100 or name in named:
                raise ValueError("Joint names must be bounded and unique")
            named[name] = {"name": name}
            for key in ("position_rad", "velocity_rad_s", "effort_nm", "temperature_c"):
                if key in joint and joint[key] is not None:
                    named[name][key] = number(joint[key])
    result["joints"] = list(named.values())
    raw_base = frame.get("base", {})
    if not isinstance(raw_base, dict):
        raise ValueError("Base state must be an object")
    for source, target, size in (("position_m", "position_m", 3),
                                  ("quat_wxyz", "quaternion_wxyz", 4),
                                  ("base_velocity_m_s", "linear_velocity_m_s", 3),
                                  ("angular_velocity_rad_s", "angular_velocity_rad_s", 3)):
        value = frame.get(source, raw_base.get(target))
        if value is not None:
            result["base"][target] = vector(value, size)
    for key in ("position_m", "tilt_deg", "table_margin_m", "table_bounds_m", "collision_aabb_m"):
        if key in frame:
            if key == "position_m":
                result[key] = vector(frame[key])
            elif key in ("tilt_deg", "table_margin_m"):
                result[key] = number(frame[key])
            else:
                result[key] = {"min": vector(frame[key]["min"]), "max": vector(frame[key]["max"])}
    if "position_m" in result["base"]:
        result["position_m"] = result["base"]["position_m"]
    for key in ("mode", "task_id", "torque_source"):
        if key in frame:
            if not isinstance(frame[key], str) or len(frame[key]) > 200:
                raise ValueError("State labels must be bounded text")
            result[key] = frame[key]
    if not named and not result["base"] and "finite" not in result:
        raise ValueError("Frame contains no supported robot measurements")
    return plain(result)


class JumperObserver:
    """Attach to a host's telemetry callback; the normal daemon discovers it.

    The producer supplies source-clock time. Observation-only by construction:
    decide() returns a decision but invokes no controller. The application must
    explicitly enable its simulator gate and record real controller receipts.
    """

    def __init__(self, robot_id, *, environment="hardware", directory=None,
                 monitor=None, sample_interval_s=.1, recording=False, **journal_options):
        if environment not in SOURCES or type(recording) is not bool:
            raise ValueError("Choose an explicit hardware or simulation source")
        interval = number(sample_interval_s)
        if not 0 <= interval <= 60:
            raise ValueError("Observation interval must be between zero and 60 seconds")
        self.evidence_kind = "recording" if recording else environment
        self.environment = environment
        if monitor is not None and monitor.evidence_kind != self.evidence_kind:
            raise ValueError("The monitor and observer must describe the same evidence")
        self.monitor, self.sample_interval_s = monitor, interval
        self.latest = None
        self._last_sample = None
        self._sample_uses_source_clock = None
        self._invalid = False
        metadata = dict(journal_options.pop("metadata", {}) or {})
        metadata.update(observation_only=True, controls_available=False,
                        evidence_kind=self.evidence_kind, units="SI", world_state_inferred=False)
        self.writer = JournalWriter(
            robot_id, "jumper_recording" if recording else SOURCES[environment],
            directory=directory, environment=environment, robot_type="jumper",
            metadata=metadata, **journal_options,
        )

    @property
    def run_id(self):
        return self.writer.run_id

    def emit(self, kind, data, **options):
        """Record host evidence without network access or controller effects."""
        return self.writer.emit(kind, data, **options)

    def observe(self, frame, *, now_s=None, block=False):
        """Return normalized state, or None on bad input; never crash a callback."""
        try:
            if self.evidence_kind == "recording" and isinstance(frame, dict):
                declared = frame.get("evidence_kind")
                if declared in ("hardware", "simulation") and declared != self.environment:
                    raise ValueError("The recording origin differs from the chosen environment")
            normalized = normalize(frame, evidence_kind=self.evidence_kind)
            stamp = normalized.get("time_s")
            if stamp is not None and self.latest is not None:
                previous = self.latest.get("time_s")
                if previous is not None and stamp < previous:
                    raise ValueError("Observation clock moved backward; start a new run")
            now = number(now_s if now_s is not None else stamp) if stamp is not None or now_s is not None else None
        except (ValueError, TypeError, KeyError, OverflowError):
            if not self._invalid:
                LOG.warning("Rejected invalid Jumper telemetry; measurements are unavailable")
                self.emit("observation.invalid", {"reason": "invalid_measurements", "evidence_kind": self.evidence_kind})
            self._invalid = True
            if self.monitor is not None and now_s is not None:
                self._incidents(self.monitor.update(None, now_s))
            return None
        self.latest = normalized
        self._invalid = False
        sample_clock = stamp if stamp is not None else time.monotonic()
        uses_source_clock = stamp is not None
        if (self._last_sample is None or uses_source_clock != self._sample_uses_source_clock
                or sample_clock - self._last_sample >= self.sample_interval_s - 1e-9):
            self.emit("observation", normalized, block=block)
            self._last_sample = sample_clock
            self._sample_uses_source_clock = uses_source_clock
        if self.monitor is not None and now is not None:
            self._incidents(self.monitor.update(normalized, now))
        return normalized

    def _incidents(self, findings):
        for finding in findings:
            data = dict(finding)
            data["kind"] = data.pop("type", data.get("kind", "unknown"))
            kind = "observation.restored" if data["kind"] == "observation_restored" else "guard.incident"
            self.emit(kind, data)

    def check(self, now_s):
        """A host heartbeat can identify missing observations on its own clock."""
        if self.monitor is not None:
            self._incidents(self.monitor.update(self.latest, now_s))

    def decide(self, gate, request, observation=None, *, now_s):
        """Record a task decision; hardware actuation is unavailable here."""
        self.emit("command.requested", dict(asdict(request), evidence_kind=self.evidence_kind))
        decision = gate.decide(request, self.latest if observation is None else observation, now_s=now_s)
        # The built-in adapter has no qualified hardware command transport.
        if self.evidence_kind != "simulation" and decision.send_to_controller:
            from ..governance import Decision
            decision = Decision(request.request_id, request.task_id, request.action,
                                "unavailable", "Hardware commands are not supported by this observer")
        self.emit("guard.decision", dict(decision.to_dict(), evidence_kind=self.evidence_kind))
        if decision.status in ("denied", "unknown"):
            self.emit("guard.incident", {"kind": "task_denied", "severity": "warning",
                                        "request_id": request.request_id, "task_id": request.task_id,
                                        "evidence_kind": self.evidence_kind, "physical_stop_confirmed": False})
        return decision

    def status(self):
        return self.writer.status()

    def close(self):
        self.writer.close()

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        self.close()
