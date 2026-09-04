"""Fuzz-target contracts, asserted over a fixed seed corpus.

`tests/fuzz/` holds Atheris harnesses that search for inputs breaking these
contracts. Atheris is a Linux/CPython-only wheel, so it is not installed in the
normal test matrix — this module asserts the same contracts, over the inputs
that have already broken them, so a regression is caught on every PR on every
OS rather than only when someone runs the fuzzer.

Every case under "regressions" is an input that really did break the contract;
see the Findings section of tests/fuzz/README.md.
"""

import json
import os
import sys

import pytest

_FUZZ_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuzz")
if _FUZZ_DIR not in sys.path:
    sys.path.insert(0, _FUZZ_DIR)

from _contracts import OTLP_KINDS, check_event_shape, check_otlp_json  # noqa: E402

# Bodies that must be rejected as ValueError, never anything else.
OTLP_SEEDS = [
    b"",
    b"{",
    b"null",
    b"[]",
    b'"str"',
    b"123",
    b"\xff\xfe",
    b"\x00" * 32,
    # Regressions: a scalar/object/string where OTLP specifies an array. The
    # per-item isinstance guards never ran because iterating the container
    # itself raised TypeError first.
    b'{"resourceSpans": 3}',
    b'{"resourceSpans": {}}',
    b'{"resourceSpans": "x"}',
    b'{"resourceLogs": 3}',
    b'{"resourceMetrics": 3}',
    b'{"resourceSpans": [{"scopeSpans": 1}]}',
    b'{"resourceSpans": [{"scopeSpans": [{"spans": 7}]}]}',
    b'{"resourceSpans": [{"scopeSpans": [{"spans": [{"events": 1, "links": 2}]}]}]}',
    b'{"resourceSpans": [{"scopeSpans": [{"spans": [{"attributes": 5}]}]}]}',
    b'{"resourceMetrics": [{"scopeMetrics": [{"metrics": 4}]}]}',
    b'{"resourceMetrics": [{"scopeMetrics": [{"metrics": [{"sum": {"dataPoints": 9}}]}]}]}',
    b'{"resourceLogs": [{"scopeLogs": [{"logRecords": 2}]}]}',
    # Valid-but-empty shapes must decode, not raise.
    b"{}",
    b'{"resourceSpans": []}',
]


@pytest.mark.parametrize("payload", OTLP_SEEDS, ids=lambda p: repr(p)[:48])
@pytest.mark.parametrize("kind", OTLP_KINDS)
def test_otlp_json_decode_only_raises_value_error(payload, kind):
    check_otlp_json(payload, kind, None)


@pytest.mark.parametrize(
    "body",
    [
        b"not-gzip-at-all",          # regression: raised gzip.BadGzipFile (OSError)
        b"\x1f\x8b\x08\x00truncated",  # regression: raised EOFError
        b"",
        b"\x1f\x8b",
    ],
    ids=["not-gzip", "truncated", "empty", "magic-only"],
)
def test_otlp_json_gzip_errors_are_value_errors(body):
    check_otlp_json(body, "traces", "gzip")


def test_otlp_json_rejects_unknown_kind():
    from clawmetry import otlp_json

    with pytest.raises(ValueError):
        otlp_json.decode(b"{}", "not-a-signal")


EVENT_SHAPE_SEEDS = [
    None, 0, 1, -1, True, 1.5, float("nan"), "", "x", b"bytes", [], {},
    [1, 2], {"a": 1},
    {"content": "s"},
    {"content": [None]},
    {"content": [{"type": "text", "text": None}]},
    {"content": [{"type": "tool_use", "name": []}]},
    {"tool_calls": 3},
    {"tool_calls": [{"name": None}]},
    {"message": {"content": [{}]}},
    [{"type": "tool_use"}],
]


@pytest.mark.parametrize("data", EVENT_SHAPE_SEEDS, ids=lambda d: repr(d)[:40])
@pytest.mark.parametrize("event_type", [None, "", "assistant", 0, [], {}])
def test_event_shape_never_raises(event_type, data):
    check_event_shape(event_type, data)


def test_event_shape_survives_arbitrary_json_scalars():
    for raw in ("null", "0", '""', "[]", "{}", '{"content":[[[]]]}'):
        check_event_shape("assistant", json.loads(raw))
