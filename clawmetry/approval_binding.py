"""Strict invocation identity shared by approval readers and writers.

The digest covers complete arguments, never a preview or canonical tool
category. Invalid or unbounded input has no identity and cannot yield a
reused grant. This module has no I/O or dependencies outside the stdlib.
"""
from __future__ import annotations

import hashlib
import json
import math
from typing import Any, Optional

VERSION = 1
MAX_BYTES = 1024 * 1024
MAX_NODES = 10000
MAX_DEPTH = 32


def _json_value(value: Any, budget: list, depth: int = 0) -> None:
    budget[0] -= 1
    if type(value) is str:
        budget[1] -= len(value)
    elif type(value) in (dict, list):
        budget[1] -= 2
    elif value is None or type(value) in (int, bool, float):
        budget[1] -= len(str(value))
    if budget[0] < 0 or budget[1] < 0 or depth > MAX_DEPTH:
        raise ValueError("approval input exceeds inspection limits")
    if value is None or type(value) in (bool, int, str):
        if isinstance(value, str) and len(value) > MAX_BYTES:
            raise ValueError("approval string exceeds inspection limits")
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) is list:
        for item in value:
            _json_value(item, budget, depth + 1)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("approval object keys must be strings")
            _json_value(key, budget, depth + 1)
            _json_value(item, budget, depth + 1)
        return
    raise ValueError("approval input must contain finite JSON values")


def action_digest(runtime: str, session_id: str, tool_name: str,
                  tool_input: Any, cwd: str = "", tool_use_id: str = "",
                  source: str = "pretooluse-hook", kind: str = "policy",
                  invocation_id: str = "") -> Optional[str]:
    """Versioned identity, or None when the invocation cannot be inspected.

    Object-key order is irrelevant. Array order, JSON types, exact tool name,
    argument contents and context remain significant. No string coercion,
    float extensions, lossy truncation or caller-defined serialization occurs.
    """
    try:
        fields = (runtime, session_id, tool_name, cwd, tool_use_id, source, kind, invocation_id)
        if any(type(value) is not str for value in fields) or not tool_name:
            return None
        if type(tool_input) is not dict:
            return None
        value = dict(version=VERSION, runtime=runtime, session_id=session_id,
                     tool_name=tool_name, tool_input=tool_input, cwd=cwd,
                     tool_use_id=tool_use_id, source=source, kind=kind)
        if invocation_id:
            value["invocation_id"] = invocation_id
        _json_value(value, [MAX_NODES, MAX_BYTES])
        encoded = json.dumps(value, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True, allow_nan=False).encode("utf-8")
        if len(encoded) > MAX_BYTES:
            return None
        return "v%d:%s" % (VERSION, hashlib.sha256(encoded).hexdigest())
    except (TypeError, ValueError, OverflowError, RecursionError):
        return None


def pending_deadline(response: dict, started: float, current: Optional[float],
                     max_budget_s: float = 60) -> float:
    """Missing budgets stop the wait. Valid budgets never exceed the native limit."""
    try:
        budget = float(response.get("wait_budget_s"))
        if math.isfinite(budget) and budget > 0:
            proposed = started + min(budget, max(0, max_budget_s))
            return min(current, proposed) if current is not None else proposed
    except (TypeError, ValueError, OverflowError):
        pass
    return started
