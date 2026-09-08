"""
routes/trail.py -- decision-trail coverage, declared per runtime.

The "Trail" triad (inputs the agent was given, the reasoning behind each
action, the outcome) is only as honest as the runtime formats behind it. Each
adapter declares what its runtime exposes via ``AgentAdapter.trail_coverage``
(``{inputs, reasoning, note}``, levels full / partial / none) and this module
answers "what can ClawMetry show for runtime X?" from those declarations so
the UI can label an empty slot "not exposed by <runtime>" instead of leaving
a gap that reads as lost data.

Endpoints (bp_trail):
  GET /api/trail/coverage   -- every runtime in entitlements FREE|PAID with its
                               declared coverage, or ``unknown`` when the
                               adapter is not importable on this node.

Static data, no store reads, cloud-safe.
"""

from __future__ import annotations

import importlib
import inspect

from flask import Blueprint, jsonify

from clawmetry.adapters.base import AgentAdapter, TRAIL_LEVELS

bp_trail = Blueprint("trail", __name__)

_UNKNOWN_NOT_LOADED = {
    "inputs": "unknown",
    "reasoning": "unknown",
    "note": "adapter not loaded on this node",
}
_UNKNOWN_UNDECLARED = {
    "inputs": "unknown",
    "reasoning": "unknown",
    "note": "adapter does not declare trail coverage",
}

# Adapters bundled with the OSS wheel, by runtime name. Registered only when
# detect() finds the runtime, but their coverage is a property of the format,
# so an absent runtime still gets a real answer here.
_BUNDLED_MODULES = {
    "openclaw": "clawmetry.adapters.openclaw",
    "nemoclaw": "clawmetry.adapters.nemo",
    "goose": "clawmetry.adapters.goose",
}

# Fallback instances (not from the registry) cached per runtime: constructing
# an adapter is cheap but not free, and coverage never changes at runtime.
_fallback_cache: dict = {}


def _instance_from_module(mod_name: str, runtime: str):
    try:
        mod = importlib.import_module(mod_name)
    except Exception:
        return None
    for _, obj in inspect.getmembers(mod, inspect.isclass):
        if (obj is not AgentAdapter and issubclass(obj, AgentAdapter)
                and getattr(obj, "name", "") == runtime):
            try:
                return obj()
            except Exception:
                return None
    return None


def _adapter_for(runtime: str):
    """Registered adapter first (a licensed plugin may override the bundled
    one); else a fresh instance of the family/bundled class; else None."""
    try:
        from clawmetry.adapters import registry
        inst = registry.get(runtime)
        if inst is not None:
            return inst
    except Exception:
        pass
    if runtime in _fallback_cache:
        return _fallback_cache[runtime]
    inst = None
    try:
        from clawmetry.sync import _family_adapter_classes
        for cls in _family_adapter_classes():
            if getattr(cls, "name", "") == runtime:
                try:
                    inst = cls()
                except Exception:
                    inst = None
                break
    except Exception:
        inst = None
    if inst is None and runtime in _BUNDLED_MODULES:
        inst = _instance_from_module(_BUNDLED_MODULES[runtime], runtime)
    _fallback_cache[runtime] = inst
    return inst


def _normalise(cov) -> dict:
    """Coerce an adapter's answer into the contract; a bad level becomes
    ``unknown`` rather than a fabricated ``full``."""
    if not isinstance(cov, dict):
        return dict(_UNKNOWN_UNDECLARED)
    out = {}
    for key in ("inputs", "reasoning"):
        lvl = cov.get(key)
        out[key] = lvl if lvl in TRAIL_LEVELS else "unknown"
    note = cov.get("note", "")
    out["note"] = note if isinstance(note, str) else ""
    return out


def coverage_for_runtime(runtime: str) -> dict:
    """``{inputs, reasoning, note}`` for one runtime name. Never raises."""
    runtime = (runtime or "").strip().lower()
    adapter = _adapter_for(runtime) if runtime else None
    if adapter is None:
        return dict(_UNKNOWN_NOT_LOADED)
    # An adapter that never overrode the base method has not declared
    # anything; the base default reads "none", which would be a claim.
    impl = getattr(type(adapter), "trail_coverage", None)
    if impl is None or impl is AgentAdapter.trail_coverage:
        return dict(_UNKNOWN_UNDECLARED)
    try:
        return _normalise(adapter.trail_coverage())
    except Exception:
        return dict(_UNKNOWN_UNDECLARED)


def coverage_all() -> dict:
    """Coverage for every runtime in the entitlement universe."""
    from clawmetry import entitlements
    names = set(entitlements.FREE_RUNTIMES) | set(entitlements.PAID_RUNTIMES)
    out = {}
    for name in sorted(names):
        cov = coverage_for_runtime(name)
        try:
            from clawmetry.adapters import registry
            registered = registry.get(name) is not None
        except Exception:
            registered = False
        cov["registered"] = registered
        out[name] = cov
    return out


@bp_trail.route("/api/trail/coverage")
def api_trail_coverage():
    runtimes = coverage_all()
    return jsonify({
        "levels": list(TRAIL_LEVELS) + ["unknown"],
        "count": len(runtimes),
        "runtimes": runtimes,
    })
