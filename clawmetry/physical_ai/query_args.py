"""Strict shared arguments for persisted Physical AI queries, with no Flask dependency."""
import re


def coerce_query_args(shape, raw):
    def integer(name, default, lo, hi):
        value = raw.get(name, default)
        if value is None and default is None:
            return None
        if type(value) is int:
            number = value
        elif isinstance(value, str) and len(value) <= 19 and re.fullmatch(r"[0-9]+", value):
            number = int(value)
        else:
            raise ValueError("physical_ai requires decimal integer arguments")
        if not lo <= number <= hi:
            raise ValueError("physical_ai integer argument out of bounds")
        return number
    if shape == "physical_ai_runs":
        before_ns = integer("before_ns", None, 0, 2**63 - 1)
        before_run_id = raw.get("before_run_id")
        if (before_ns is None) != (before_run_id is None):
            raise ValueError("physical_ai_runs requires a complete run cursor")
        if before_run_id is not None and (not isinstance(before_run_id, str) or not re.fullmatch(r"[0-9a-f]{32}", before_run_id)):
            raise ValueError("physical_ai_runs requires a valid run cursor")
        robot_id = raw.get("robot_id")
        if robot_id is not None and (not isinstance(robot_id, str) or not 1 <= len(robot_id) <= 200 or any(ord(c) < 32 for c in robot_id)):
            raise ValueError("physical_ai_runs requires a valid robot filter")
        return {"limit": integer("limit", 20, 1, 100),
                "robot_id": robot_id, "before_ns": before_ns,
                "before_run_id": before_run_id}
    if shape == "physical_ai_events":
        if not isinstance(raw.get("run_id"), str) or not re.fullmatch(r"[0-9a-f]{32}", raw["run_id"]):
            raise ValueError("physical_ai_events requires a valid run_id")
        return {"run_id": raw["run_id"],
                "after": integer("after", 0, 0, 2**63 - 1),
                "limit": integer("limit", 200, 1, 500)}
    raise ValueError("Unknown physical query shape")
