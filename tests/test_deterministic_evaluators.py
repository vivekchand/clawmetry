"""Tests for clawmetry/deterministic_evaluators.py (#2862).

Pins the zero-LLM, code-based eval runtime: each built-in's pass/fail
behaviour, the 0..1 score shape that lines up with the LLM-judge surface,
the runner's never-crash contract, and the best-effort event extractor.
"""
from __future__ import annotations

from clawmetry.deterministic_evaluators import (
    EvalInput,
    DeterministicEvalResult,
    BUILTIN_EVALUATORS,
    run_checks,
    eval_input_from_events,
)


def _run(slug, config, **inp):
    return run_checks(EvalInput(**inp), [{"slug": slug, "config": config}])[0]


# ── score shape ────────────────────────────────────────────────────────────────

def test_result_score_shape_pass_is_one_fail_is_zero():
    ok = _run("json-parseable", {}, output_text='{"a": 1}')
    bad = _run("json-parseable", {}, output_text="not json")
    assert ok.passed is True and ok.score == 1.0
    assert bad.passed is False and bad.score == 0.0
    # mirrors the LLM-judge 0..1 range for shared views
    assert isinstance(ok, DeterministicEvalResult)
    assert set(ok.to_dict()) == {"slug", "name", "score", "passed", "reason", "detail"}


# ── json-parseable ───────────────────────────────────────────────────────────────

def test_json_parseable():
    assert _run("json-parseable", {}, output_text='{"x":1}').passed
    assert _run("json-parseable", {}, output_text="[1, 2, 3]").passed
    assert _run("json-parseable", {}, output_text='  {"x":1}  ').passed  # stripped
    assert not _run("json-parseable", {}, output_text="hello").passed
    assert not _run("json-parseable", {}, output_text="").passed  # empty fails


# ── json-schema-match ────────────────────────────────────────────────────────────

def test_json_schema_required_keys():
    cfg = {"required_keys": ["name", "age"]}
    assert _run("json-schema-match", cfg, output_text='{"name":"a","age":3}').passed
    r = _run("json-schema-match", cfg, output_text='{"name":"a"}')
    assert not r.passed and r.detail["missing"] == ["age"]


def test_json_schema_types():
    cfg = {"required_keys": ["age"], "types": {"age": "int", "name": "str"}}
    assert _run("json-schema-match", cfg, output_text='{"age":3,"name":"a"}').passed
    r = _run("json-schema-match", cfg, output_text='{"age":"three","name":"a"}')
    assert not r.passed and r.detail["type_errors"]


def test_json_schema_bool_is_not_int():
    # JSON true must not silently satisfy an int/number type
    cfg = {"types": {"age": "int"}}
    r = _run("json-schema-match", cfg, output_text='{"age": true}')
    assert not r.passed


def test_json_schema_non_object_fails():
    r = _run("json-schema-match", {"required_keys": ["x"]}, output_text="[1,2]")
    assert not r.passed


def test_json_schema_number_accepts_int_and_float():
    cfg = {"types": {"v": "number"}}
    assert _run("json-schema-match", cfg, output_text='{"v": 3}').passed
    assert _run("json-schema-match", cfg, output_text='{"v": 3.5}').passed


# ── regex-match ──────────────────────────────────────────────────────────────────

def test_regex_match():
    assert _run("regex-match", {"pattern": r"\d{3}"}, output_text="abc 123").passed
    assert not _run("regex-match", {"pattern": r"\d{3}"}, output_text="abc").passed


def test_regex_ignore_case_and_full_match():
    assert _run("regex-match", {"pattern": "hello", "ignore_case": True},
                output_text="HELLO world").passed
    assert _run("regex-match", {"pattern": "hi", "full_match": True},
                output_text="hi").passed
    assert not _run("regex-match", {"pattern": "hi", "full_match": True},
                    output_text="hi there").passed


def test_regex_invalid_pattern_fails_gracefully():
    r = _run("regex-match", {"pattern": "(unclosed"}, output_text="x")
    assert not r.passed and "Invalid regex" in r.reason


def test_regex_missing_pattern_fails():
    assert not _run("regex-match", {}, output_text="x").passed


# ── exact-match ──────────────────────────────────────────────────────────────────

def test_exact_match_strips_by_default():
    assert _run("exact-match", {"expected": "yes"}, output_text="  yes \n").passed
    assert not _run("exact-match", {"expected": "yes"}, output_text="yes please").passed


def test_exact_match_ignore_case():
    assert _run("exact-match", {"expected": "YES", "ignore_case": True},
                output_text="yes").passed


def test_exact_match_missing_expected_fails():
    assert not _run("exact-match", {}, output_text="x").passed


# ── output-length-bounds ─────────────────────────────────────────────────────────

def test_output_length_bounds():
    assert _run("output-length-bounds", {"min_chars": 1, "max_chars": 10},
                output_text="hello").passed
    assert not _run("output-length-bounds", {"min_chars": 1}, output_text="").passed
    assert not _run("output-length-bounds", {"max_chars": 3}, output_text="toolong").passed
    # open-ended bounds
    assert _run("output-length-bounds", {"min_chars": 2}, output_text="ok").passed


# ── required-tool-args ───────────────────────────────────────────────────────────

def test_required_tool_args_present():
    inp = dict(tool_calls=[{"name": "write_file",
                            "arguments": {"path": "/x", "content": "hi"}}])
    assert _run("required-tool-args",
                {"tool": "write_file", "args": ["path", "content"]}, **inp).passed


def test_required_tool_args_missing():
    inp = dict(tool_calls=[{"name": "write_file", "arguments": {"content": "hi"}}])
    r = _run("required-tool-args", {"tool": "write_file", "args": ["path"]}, **inp)
    assert not r.passed and r.detail["missing"] == ["path"]


def test_required_tool_args_empty_value_counts_as_missing():
    inp = dict(tool_calls=[{"name": "write_file", "arguments": {"path": ""}}])
    assert not _run("required-tool-args",
                    {"tool": "write_file", "args": ["path"]}, **inp).passed


def test_required_tool_args_tool_never_called():
    r = _run("required-tool-args", {"tool": "write_file", "args": ["path"]},
             tool_calls=[{"name": "read_file", "arguments": {"path": "/x"}}])
    assert not r.passed
    # require_call=False makes an absent tool a pass
    ok = _run("required-tool-args",
              {"tool": "write_file", "args": ["path"], "require_call": False},
              tool_calls=[])
    assert ok.passed


def test_required_tool_args_checks_every_call():
    inp = dict(tool_calls=[
        {"name": "w", "arguments": {"path": "/a"}},
        {"name": "w", "arguments": {}},  # second call malformed
    ])
    r = _run("required-tool-args", {"tool": "w", "args": ["path"]}, **inp)
    assert not r.passed and r.detail["call_index"] == 1


# ── no-tool-errors ───────────────────────────────────────────────────────────────

def test_no_tool_errors():
    assert _run("no-tool-errors", {}, had_error=False).passed
    assert not _run("no-tool-errors", {}, had_error=True).passed


# ── runner contract ──────────────────────────────────────────────────────────────

def test_unknown_slug_fails_not_raises():
    results = run_checks(EvalInput(output_text="x"), [{"slug": "nope"}])
    assert len(results) == 1 and not results[0].passed
    assert "No built-in evaluator" in results[0].reason


def test_run_checks_runs_all_and_is_independent():
    inp = EvalInput(output_text='{"a":1}')
    results = run_checks(inp, [
        {"slug": "json-parseable"},
        {"slug": "output-length-bounds", "config": {"max_chars": 2}},  # fails
    ])
    assert [r.passed for r in results] == [True, False]


def test_run_checks_empty_list():
    assert run_checks(EvalInput(), []) == []


def test_builtin_catalogue_slugs_are_callable():
    for slug, fn in BUILTIN_EVALUATORS.items():
        assert callable(fn), slug
        # every built-in tolerates an empty input + empty config without raising
        out = fn(EvalInput(), {})
        assert isinstance(out, DeterministicEvalResult)
        assert out.score in (0.0, 1.0)


# ── event extractor ──────────────────────────────────────────────────────────────

def test_eval_input_from_events_dict_shape():
    events = [
        {"type": "message", "content": "first"},
        {"type": "tool_call", "tool_calls": [
            {"name": "write_file", "arguments": {"path": "/x"}}]},
        {"type": "message", "content": "final answer"},
    ]
    inp = eval_input_from_events(events)
    assert inp.output_text == "final answer"  # last non-empty wins
    assert {"name": "write_file", "arguments": {"path": "/x"}} in inp.tool_calls
    assert inp.had_error is False


def test_eval_input_from_events_detects_error():
    assert eval_input_from_events([{"type": "tool_error", "content": "boom"}]).had_error
    assert eval_input_from_events(
        [{"type": "tool_result", "extra": {"is_error": True}}]).had_error


def test_eval_input_from_events_reads_dataclass_events():
    from clawmetry.adapters.base import Event
    ev = Event(agent="openclaw", session_id="s", id="1", type="message",
               content="hi", tool_name="bash")
    inp = eval_input_from_events([ev])
    assert inp.output_text == "hi"
    assert any(c["name"] == "bash" for c in inp.tool_calls)


def test_eval_input_from_events_input_key_alias():
    # tool_use blocks use "input" rather than "arguments"
    events = [{"type": "tool_call",
               "tool_calls": [{"name": "Read", "input": {"path": "/x"}}]}]
    inp = eval_input_from_events(events)
    assert inp.tool_calls[0]["arguments"] == {"path": "/x"}
