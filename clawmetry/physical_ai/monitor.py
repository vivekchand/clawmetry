"""Continuous local robot observations and explicit notification receipts.

These checks do not detect people, classify malicious intent, or confirm a
physical stop. A lift alert means the measured base rose relative to its initial
height; it is not proof that someone picked the robot up.
"""
from __future__ import annotations

import math


def _number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("A finite number is required")
    try:
        if not math.isfinite(value):
            raise ValueError("A finite number is required")
    except OverflowError as error:
        raise ValueError("A finite number is required") from error
    return float(value)


def _vector(value):
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("Three finite coordinates are required")
    return [_number(item) for item in value]


class DeskMonitor:
    """Emit one alert per hazard episode, using fresh full-body collision bounds.

    Call with the source clock, including during observation interruptions.
    Use a new monitor per run. Supply a known baseline if startup height is not
    representative; otherwise the first valid observation establishes it.
    """

    def __init__(self, *, baseline_height_m=None, movement_authorized=False,
                 edge_margin_m=.12, lift_threshold_m=.06, tilt_threshold_deg=35., max_age_s=.15, evidence_kind="simulation"):
        if type(movement_authorized) is not bool:
            raise ValueError("Movement authorization must be an explicit boolean")
        if evidence_kind not in ("simulation", "hardware", "recording"):
            raise ValueError("Unknown evidence kind")
        self.evidence_kind = evidence_kind
        self.baseline_height_m = None if baseline_height_m is None else _number(baseline_height_m)
        self.movement_authorized = movement_authorized
        self.edge_margin_m = _number(edge_margin_m)
        self.lift_threshold_m = _number(lift_threshold_m)
        self.tilt_threshold_deg = _number(tilt_threshold_deg)
        self.max_age_s = _number(max_age_s)
        if min(self.edge_margin_m, self.lift_threshold_m, self.max_age_s) <= 0 or not 0 < self.tilt_threshold_deg <= 180:
            raise ValueError("Monitor thresholds must be positive and tilt must not exceed 180 degrees")
        self._active = set()
        self._last_now = None
        self._last_observed = None

    def _alert(self, kind, severity, message, now, *, outcome="observed", **measurements):
        return {"type": kind, "severity": severity, "message": message,
                "time_s": now, "evidence_kind": self.evidence_kind, "outcome": outcome,
                "physical_stop_confirmed": False, "measurements": measurements}

    def _lost(self, now):
        if "observation_lost" in self._active:
            return []
        self._active.add("observation_lost")
        return [self._alert("observation_lost", "warning",
                           "Fresh robot observations are unavailable. The robot outcome is unknown.",
                           now, outcome="unknown")]

    def update(self, snapshot: dict | None, now_s: float) -> list[dict]:
        now = None
        try:
            now = _number(now_s)
            if now < 0 or (self._last_now is not None and now < self._last_now):
                raise ValueError("Source clock moved backward")
            self._last_now = now
            if not isinstance(snapshot, dict) or snapshot.get("finite") is not True or snapshot.get("evidence_kind") != self.evidence_kind:
                raise ValueError("A valid robot observation is required")
            stamp = _number(snapshot["time_s"])
            if not 0 <= now - stamp < self.max_age_s:
                raise ValueError("Observation is stale or from the future")
            if self._last_observed is not None and stamp < self._last_observed:
                raise ValueError("Observation clock moved backward")
            position = _vector(snapshot["position_m"])
            tilt = _number(snapshot["tilt_deg"])
            if not 0 <= tilt <= 180:
                raise ValueError("Invalid measured tilt")
            lower = _vector(snapshot["collision_aabb_m"]["min"])
            upper = _vector(snapshot["collision_aabb_m"]["max"])
            table_lower = _vector(snapshot["table_bounds_m"]["min"])
            table_upper = _vector(snapshot["table_bounds_m"]["max"])
            if any(lo >= hi for lo, hi in zip(lower, upper)) or any(table_lower[i] >= table_upper[i] for i in (0, 1)):
                raise ValueError("Invalid collision or table bounds")
            margin = min(lower[0] - table_lower[0], table_upper[0] - upper[0],
                         lower[1] - table_lower[1], table_upper[1] - upper[1])
            if not math.isclose(margin, _number(snapshot["table_margin_m"]), rel_tol=1e-7, abs_tol=1e-7):
                raise ValueError("Full-body margin disagrees with the measured bounds")
        except (KeyError, TypeError, ValueError, OverflowError):
            return self._lost(now)

        self._last_observed = stamp
        if self.baseline_height_m is None:
            self.baseline_height_m = position[2]
        alerts = []
        if "observation_lost" in self._active:
            self._active.remove("observation_lost")
            alerts.append(self._alert("observation_restored", "info",
                                      "Fresh robot observations resumed. Review the missing interval separately.", now))
        conditions = {
            "boundary_approach": (margin < self.edge_margin_m, "warning",
                                  "The observed robot body is approaching the tabletop boundary.", {"table_margin_m": margin}),
            "boundary_crossed": (margin < 0, "critical",
                                 "The observed robot body extends beyond the tabletop boundary.", {"table_margin_m": margin}),
            "unexpected_lift": (not self.movement_authorized and position[2] - self.baseline_height_m > self.lift_threshold_m,
                                "warning", "The observed robot base rose unexpectedly. Lifting or removal needs review.",
                                {"base_height_m": position[2], "baseline_height_m": self.baseline_height_m}),
            "excessive_tilt": (tilt > self.tilt_threshold_deg, "critical",
                               "The observed robot tilt exceeds the configured limit.", {"tilt_deg": tilt}),
        }
        for kind, (active, severity, message, measurements) in conditions.items():
            if active and kind not in self._active:
                self._active.add(kind)
                alerts.append(self._alert(kind, severity, message, now, **measurements))
            elif not active:
                self._active.discard(kind)
        return alerts
