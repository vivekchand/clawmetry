"""Finite, explicit measurements shared by physical task gates and adapters."""

import math


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("A finite measurement is required")
    try:
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("A finite measurement is required")
    except OverflowError as exc:
        raise ValueError("A finite measurement is required") from exc
    return value


def vector(value, size=3):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        raise ValueError("The measurement has an unexpected dimension")
    return [number(v) for v in value]


def workspace_margin(frame, bounds_xy=None):
    """Recompute full-body clearance; a claimed scalar alone is insufficient."""
    lower = vector(frame["collision_aabb_m"]["min"])
    upper = vector(frame["collision_aabb_m"]["max"])
    table_lower = vector(frame["table_bounds_m"]["min"])
    table_upper = vector(frame["table_bounds_m"]["max"])
    if any(lo >= hi for lo, hi in zip(lower, upper)):
        raise ValueError("Robot bounds are invalid")
    if any(table_lower[i] >= table_upper[i] for i in (0, 1)):
        raise ValueError("Workspace bounds are invalid")
    if bounds_xy is not None:
        supplied = (table_lower[0], table_upper[0], table_lower[1], table_upper[1])
        if not all(math.isclose(a, b, abs_tol=1e-8, rel_tol=0) for a, b in zip(supplied, bounds_xy)):
            raise ValueError("Observed workspace differs from the authorized task")
    margin = min(lower[0] - table_lower[0], table_upper[0] - upper[0],
                 lower[1] - table_lower[1], table_upper[1] - upper[1])
    if not math.isclose(margin, number(frame["table_margin_m"]), abs_tol=1e-7, rel_tol=1e-7):
        raise ValueError("Measured bounds disagree with claimed clearance")
    return margin
