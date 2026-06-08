"""
clawmetry/deterministic_evaluators.py — cheap, code-based checks on sessions.

Companion to the LLM-as-judge surface (``clawmetry/eval_runner.py``, #1619):
where the judge spends an LLM call to score *quality*, these evaluators run a
deterministic Python check in milliseconds with **zero LLM cost** to catch
*structural* failures — malformed JSON, a missing required tool argument, an
answer that is empty or runaway-long, a regex/exact mismatch. (#2862)

Why both: the LLM judge is overkill for "did the agent return parseable JSON?"
or "did the `create_file` call include a `path`?". Those are pass/fail facts a
regex or a `json.loads` answers for free. Deterministic checks complement the
judge — they do not replace it — and their scores share the same 0..1 shape so
they flow into the same eval views (a 1.0 pass / 0.0 fail).

Design rules:
  * **Pure + storage-agnostic.** Each evaluator is a function of an
    :class:`EvalInput` (the normalized output text + tool calls + error flag)
    and a small ``config`` dict. No DuckDB, no network, no clock — so they are
    trivially unit-testable and safe to run inline on a live session.
  * **Never raises.** A check that hits bad input returns a failing
    :class:`DeterministicEvalResult` with a human reason, never an exception —
    a broken check must not take down the eval pass.
  * **Built-ins are FREE-tier.** They run on the user's box over local data and
    cost nothing, so they ship in OSS (no entitlement gate).

Public API:
    EvalInput(output_text=..., tool_calls=[...], had_error=False)
    eval_input_from_events(events) -> EvalInput        # best-effort extractor
    BUILTIN_EVALUATORS: dict[str, callable]
    run_checks(eval_input, checks) -> list[DeterministicEvalResult]
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Callable

log = logging.getLogger("clawmetry.deterministic_evaluators")


# ── Normalized input + result shapes ────────────────────────────────────────────


@dataclass
class EvalInput:
    """What a deterministic check looks at, decoupled from storage.

    ``output_text`` is the agent's final/assistant text. ``tool_calls`` is a
    list of ``{"name": str, "arguments": dict}`` (other keys ignored).
    ``had_error`` flags whether any tool result / event errored.
    """

    output_text: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    had_error: bool = False


@dataclass
class DeterministicEvalResult:
    """One check's verdict on one session.

    ``score`` is ``1.0`` for pass / ``0.0`` for fail so it lines up with the
    LLM-judge 0..1 score. ``passed`` is the same fact as a bool for callers
    that prefer it. ``detail`` carries small machine-readable context (the
    offending value, the missing keys, …) for the UI.
    """

    slug: str
    name: str
    score: float
    passed: bool
    reason: str
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _passed(slug: str, name: str, reason: str, **detail: Any) -> DeterministicEvalResult:
    return DeterministicEvalResult(slug=slug, name=name, score=1.0, passed=True,
                                   reason=reason, detail=detail)


def _failed(slug: str, name: str, reason: str, **detail: Any) -> DeterministicEvalResult:
    return DeterministicEvalResult(slug=slug, name=name, score=0.0, passed=False,
                                   reason=reason, detail=detail)


# ── Built-in evaluators ─────────────────────────────────────────────────────────
#
# Each takes (eval_input, config) and returns a DeterministicEvalResult. Keep
# them small, total (never raise), and free of side effects.


_JSON_TYPES: dict[str, type | tuple[type, ...]] = {
    "str": str, "string": str,
    "int": int, "integer": int,
    "float": float,
    "number": (int, float),
    "bool": bool, "boolean": bool,
    "list": list, "array": list,
    "dict": dict, "object": dict,
    "null": type(None),
}


def _parse_json(text: str):
    """Return (ok, value_or_None). ``bool`` is excluded from int below by the
    caller's type table where it matters; here we just parse."""
    try:
        return True, json.loads(text)
    except (ValueError, TypeError):
        return False, None


def eval_json_parseable(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when the output parses as JSON. The cheapest structural check there
    is — agents asked for JSON routinely emit prose or fenced code instead."""
    slug, name = "json-parseable", config.get("name") or "Output is valid JSON"
    text = (inp.output_text or "").strip()
    if not text:
        return _failed(slug, name, "Output was empty.")
    ok, _ = _parse_json(text)
    if ok:
        return _passed(slug, name, "Output parsed as JSON.")
    return _failed(slug, name, "Output did not parse as JSON.",
                   sample=text[:120])


def eval_json_schema_match(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when the output is a JSON object with the required keys (and, if
    declared, the right types).

    Config: ``required_keys`` (list[str]), ``types`` (dict[str, typename]).
    This is a deliberately small schema check — required-key + scalar-type —
    not a full JSON-Schema engine; that is what makes it free and dependency-
    less.
    """
    slug, name = "json-schema-match", config.get("name") or "Output matches schema"
    required = list(config.get("required_keys") or [])
    types = dict(config.get("types") or {})
    ok, val = _parse_json((inp.output_text or "").strip())
    if not ok:
        return _failed(slug, name, "Output did not parse as JSON.")
    if not isinstance(val, dict):
        return _failed(slug, name, f"Expected a JSON object, got {type(val).__name__}.")
    missing = [k for k in required if k not in val]
    if missing:
        return _failed(slug, name, f"Missing required key(s): {', '.join(missing)}.",
                       missing=missing)
    bad_types: list[str] = []
    for key, typename in types.items():
        if key not in val:
            continue
        expected = _JSON_TYPES.get(str(typename).lower())
        if expected is None:
            continue
        v = val[key]
        # JSON has no separate bool/int, but Python's bool is an int subclass;
        # treat a bool as NOT matching int/number to avoid silent passes.
        if expected in (int, (int, float)) and isinstance(v, bool):
            bad_types.append(f"{key} (got bool, want {typename})")
            continue
        if not isinstance(v, expected):
            bad_types.append(f"{key} (got {type(v).__name__}, want {typename})")
    if bad_types:
        return _failed(slug, name, f"Type mismatch: {'; '.join(bad_types)}.",
                       type_errors=bad_types)
    return _passed(slug, name, "Output is a JSON object matching the schema.")


def eval_regex_match(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when ``pattern`` is found in the output. Config: ``pattern`` (str,
    required), ``ignore_case`` (bool), ``full_match`` (bool — anchor the whole
    string instead of search)."""
    slug, name = "regex-match", config.get("name") or "Output matches pattern"
    pattern = config.get("pattern")
    if not pattern:
        return _failed(slug, name, "No regex pattern configured.")
    flags = re.IGNORECASE if config.get("ignore_case") else 0
    try:
        rx = re.compile(pattern, flags)
    except re.error as e:
        return _failed(slug, name, f"Invalid regex: {e}.")
    text = inp.output_text or ""
    hit = rx.fullmatch(text) if config.get("full_match") else rx.search(text)
    if hit:
        return _passed(slug, name, "Output matched the pattern.", pattern=pattern)
    return _failed(slug, name, "Output did not match the pattern.", pattern=pattern)


def eval_exact_match(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when the output equals ``expected``. Config: ``expected`` (str,
    required), ``strip`` (bool, default True), ``ignore_case`` (bool)."""
    slug, name = "exact-match", config.get("name") or "Output equals expected"
    if "expected" not in config:
        return _failed(slug, name, "No expected value configured.")
    expected = str(config["expected"])
    actual = inp.output_text or ""
    if config.get("strip", True):
        expected, actual = expected.strip(), actual.strip()
    if config.get("ignore_case"):
        expected, actual = expected.lower(), actual.lower()
    if actual == expected:
        return _passed(slug, name, "Output matched exactly.")
    return _failed(slug, name, "Output did not match the expected value.",
                   sample=(inp.output_text or "")[:120])


def eval_output_length_bounds(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when the output length (characters) is within bounds. Config:
    ``min_chars`` (int), ``max_chars`` (int) — either may be omitted. Catches
    empty answers and runaway generations alike."""
    slug, name = "output-length-bounds", config.get("name") or "Output length in bounds"
    length = len(inp.output_text or "")
    lo = config.get("min_chars")
    hi = config.get("max_chars")
    if lo is not None and length < int(lo):
        return _failed(slug, name, f"Output too short: {length} < {lo} chars.",
                       length=length, min_chars=int(lo))
    if hi is not None and length > int(hi):
        return _failed(slug, name, f"Output too long: {length} > {hi} chars.",
                       length=length, max_chars=int(hi))
    return _passed(slug, name, f"Output length {length} within bounds.", length=length)


def eval_required_tool_args(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when every call to ``tool`` supplied all ``args``. Config: ``tool``
    (str, required), ``args`` (list[str], required), ``require_call`` (bool,
    default True — fail if the tool was never called).

    Catches the classic malformed tool call (e.g. a ``write_file`` with no
    ``path``) that the LLM judge would burn a call to notice."""
    slug, name = "required-tool-args", config.get("name") or "Required tool args present"
    tool = config.get("tool")
    required = list(config.get("args") or [])
    if not tool or not required:
        return _failed(slug, name, "No tool/args configured.")
    calls = [c for c in (inp.tool_calls or [])
             if isinstance(c, dict) and c.get("name") == tool]
    if not calls:
        if config.get("require_call", True):
            return _failed(slug, name, f"Tool '{tool}' was never called.", tool=tool)
        return _passed(slug, name, f"Tool '{tool}' not called (not required).", tool=tool)
    for idx, call in enumerate(calls):
        args = call.get("arguments")
        if not isinstance(args, dict):
            return _failed(slug, name,
                           f"Call #{idx + 1} to '{tool}' had no arguments object.",
                           tool=tool, call_index=idx)
        missing = [a for a in required if a not in args or args[a] in (None, "")]
        if missing:
            return _failed(slug, name,
                           f"Call #{idx + 1} to '{tool}' missing arg(s): "
                           f"{', '.join(missing)}.",
                           tool=tool, call_index=idx, missing=missing)
    return _passed(slug, name, f"All {len(calls)} call(s) to '{tool}' had required args.",
                   tool=tool, call_count=len(calls))


def eval_no_tool_errors(inp: EvalInput, config: dict) -> DeterministicEvalResult:
    """Pass when the session recorded no tool/turn error. Config: none."""
    slug, name = "no-tool-errors", config.get("name") or "No tool errors"
    if inp.had_error:
        return _failed(slug, name, "Session recorded a tool/turn error.")
    return _passed(slug, name, "No tool/turn errors recorded.")


# slug → evaluator function. The slug is what a check config references.
BUILTIN_EVALUATORS: dict[str, Callable[[EvalInput, dict], DeterministicEvalResult]] = {
    "json-parseable": eval_json_parseable,
    "json-schema-match": eval_json_schema_match,
    "regex-match": eval_regex_match,
    "exact-match": eval_exact_match,
    "output-length-bounds": eval_output_length_bounds,
    "required-tool-args": eval_required_tool_args,
    "no-tool-errors": eval_no_tool_errors,
}


# ── Runner ───────────────────────────────────────────────────────────────────────


def run_checks(eval_input: EvalInput, checks: list[dict]) -> list[DeterministicEvalResult]:
    """Run a list of check configs against one input.

    Each check is ``{"slug": <builtin slug>, "config": {...}}`` (``config``
    optional). An unknown slug yields a failing result rather than raising, and
    an evaluator that itself throws is caught and reported as a failure, so one
    bad check never aborts the pass.
    """
    results: list[DeterministicEvalResult] = []
    for check in checks or []:
        slug = (check or {}).get("slug")
        config = (check or {}).get("config") or {}
        fn = BUILTIN_EVALUATORS.get(slug)
        if fn is None:
            results.append(_failed(slug or "unknown",
                                   config.get("name") or "Unknown evaluator",
                                   f"No built-in evaluator named '{slug}'."))
            continue
        try:
            results.append(fn(eval_input, config))
        except Exception as e:  # defensive: a check must never crash the pass
            log.warning("deterministic eval '%s' raised: %s", slug, e)
            results.append(_failed(slug, config.get("name") or slug,
                                   f"Evaluator errored: {e}."))
    return results


# ── Best-effort extraction from unified events ──────────────────────────────────


def eval_input_from_events(events: list) -> EvalInput:
    """Build an :class:`EvalInput` from a session's unified ``Event`` list.

    Best-effort and tolerant of either ``Event`` dataclass instances or their
    ``to_dict()`` shape:
      * ``output_text`` — the last non-empty event ``content`` (the agent's
        latest textual output); falls back to the most recent content seen.
      * ``tool_calls`` — flattened from each event's ``tool_calls`` (and a
        single ``tool_name`` when present).
      * ``had_error`` — any event whose type contains "error" or whose extra
        marks ``is_error``/``isError`` true.
    """
    def _get(obj, key, default=None):
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)

    output_text = ""
    tool_calls: list[dict[str, Any]] = []
    had_error = False
    for ev in events or []:
        etype = str(_get(ev, "type", "") or "")
        content = _get(ev, "content", "") or ""
        if content:
            output_text = content  # last non-empty wins (latest output)
        for tc in (_get(ev, "tool_calls", None) or []):
            if isinstance(tc, dict):
                tool_calls.append({"name": tc.get("name"),
                                   "arguments": tc.get("arguments") or tc.get("input") or {}})
        tname = _get(ev, "tool_name", "") or ""
        if tname:
            tool_calls.append({"name": tname, "arguments": {}})
        extra = _get(ev, "extra", None) or {}
        if "error" in etype.lower():
            had_error = True
        if isinstance(extra, dict) and (extra.get("is_error") or extra.get("isError")):
            had_error = True
    return EvalInput(output_text=output_text, tool_calls=tool_calls, had_error=had_error)
