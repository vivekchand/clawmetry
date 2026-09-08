"""Prompt-cache tokens must be read under BOTH GenAI spellings (#5685).

The OpenTelemetry GenAI semantic conventions spell the cache counters with
a dot before the noun -- ``gen_ai.usage.cache_read.input_tokens`` -- and an
exporter emits that spelling as soon as it opts in with
``OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental``, which is what
the OTel migration guidance tells people to set.

ClawMetry read only the underscore spelling, so those spans reported ZERO
cached tokens. That is not a display gap. On a long agent session cache
reads are usually the majority of input tokens and are billed at a
fraction of the full input rate, so a zero leaves the cache-aware cost
path with nothing to be aware of and the session's cost is simply wrong.

Both spellings are live in the wild, so both are read -- and a span
carrying both must be counted once, not summed.
"""
import pytest

pytest.importorskip(
    "opentelemetry.proto.collector.trace.v1.trace_service_pb2",
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)

from opentelemetry.proto.collector.trace.v1 import trace_service_pb2  # noqa: E402
from opentelemetry.proto.common.v1 import common_pb2  # noqa: E402
from opentelemetry.proto.resource.v1 import resource_pb2  # noqa: E402
from opentelemetry.proto.trace.v1 import trace_pb2  # noqa: E402

import dashboard as _d  # noqa: E402


def _kv(key, s=None, i=None):
    v = common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    return common_pb2.KeyValue(key=key, value=v)


BASE = [
    _kv("gen_ai.operation.name", s="chat"),
    _kv("gen_ai.request.model", s="claude-opus-5"),
    _kv("gen_ai.usage.input_tokens", i=1240),
    _kv("gen_ai.usage.output_tokens", i=312),
]


def _row_for(extra_attrs):
    """The DuckDB row the live mapper builds for one GenAI span."""
    span = trace_pb2.Span(
        name="anthropic.chat",
        kind=3,
        span_id=b"\x01" * 8,
        trace_id=b"\x02" * 16,
        start_time_unix_nano=1_757_300_000_000_000_000,
        end_time_unix_nano=1_757_300_002_000_000_000,
    )
    span.attributes.extend(BASE + extra_attrs)
    resource = resource_pb2.Resource()
    resource.attributes.extend([_kv("service.name", s="my-engine")])
    req = trace_service_pb2.ExportTraceServiceRequest(
        resource_spans=[trace_pb2.ResourceSpans(
            resource=resource,
            scope_spans=[trace_pb2.ScopeSpans(spans=[span])],
        )]
    )

    captured = []

    class _Store:
        def put_span(self, span=None, **_kw):
            captured.append(span)

        def __getattr__(self, _name):        # tolerate any other call
            return lambda *a, **k: None

    import clawmetry.local_store as _ls
    _real = _ls.get_store
    _ls.get_store = lambda *a, **k: _Store()
    try:
        _d._process_otlp_traces(req.SerializeToString())
    finally:
        _ls.get_store = _real
    assert captured, "the mapper wrote no span row"
    return captured[0]


def _cost(row):
    """The derived cost for this span.

    Cache counters are not stored as columns -- they feed
    ``estimate_event_cost_usd`` -- so the cost IS the observable effect,
    and it is also the thing the bug got wrong. Asserting on it means
    these tests fail for the reason a user would notice.
    """
    cost = row.get("cost_usd")
    assert cost is not None, (
        "the mapper derived no cost for a token-bearing GenAI span, so "
        "this suite cannot observe the cache counters at all"
    )
    return round(float(cost), 6)


#: The same span with no cache attributes at all. Every cache reading has
#: to move the cost away from this, or it was not read.
NO_CACHE_COST = None


def test_current_semconv_dotted_spelling_is_read():
    """The regression this file exists for."""
    global NO_CACHE_COST
    NO_CACHE_COST = _cost(_row_for([]))

    dotted = _cost(_row_for([
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
        _kv("gen_ai.usage.cache_creation.input_tokens", i=400),
    ]))
    assert dotted != NO_CACHE_COST, (
        f"cost came out {dotted} with 9000 cache-read and 400 cache-write "
        f"tokens on the CURRENT GenAI semantic convention spelling -- "
        f"identical to a span with no cache attributes at all "
        f"({NO_CACHE_COST}). Any exporter that opted in to "
        "gen_ai_latest_experimental has its cached tokens read as zero, "
        "and cache reads are usually the majority of a long session's "
        "input."
    )


def test_both_spellings_derive_the_same_cost():
    """The two spellings mean the same thing, so they must cost the same.
    This is the assertion that would have caught the bug: before the fix
    the dotted form silently priced as an uncached call."""
    dotted = _cost(_row_for([
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
        _kv("gen_ai.usage.cache_creation.input_tokens", i=400),
    ]))
    underscore = _cost(_row_for([
        _kv("gen_ai.usage.cache_read_input_tokens", i=9000),
        _kv("gen_ai.usage.cache_creation_input_tokens", i=400),
    ]))
    assert dotted == underscore, (
        f"dotted spelling priced at {dotted}, underscore at {underscore}. "
        "They describe the same tokens."
    )


def test_underscore_spelling_still_works():
    """The earlier spelling is still emitted widely; it must not have moved."""
    with_cache = _cost(_row_for([
        _kv("gen_ai.usage.cache_read_input_tokens", i=9000),
    ]))
    without = _cost(_row_for([]))
    assert with_cache != without


def test_both_spellings_present_are_counted_once():
    """``_pick`` takes the first non-None, so an exporter emitting both
    forms must not have them summed into double the cached tokens."""
    both = _cost(_row_for([
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
        _kv("gen_ai.usage.cache_read_input_tokens", i=9000),
    ]))
    one = _cost(_row_for([
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
    ]))
    doubled = _cost(_row_for([
        _kv("gen_ai.usage.cache_read.input_tokens", i=18000),
    ]))
    assert both == one, f"the two spellings were summed: {both} vs {one}"
    assert both != doubled, "sanity: 9000 and 18000 must price differently"


def test_an_explicit_cost_still_wins_over_the_derived_one():
    """Deriving a cost is a fallback for token-only spans. An exporter
    that states its own cost must keep it, cache attributes or not."""
    row = _row_for([
        _kv("gen_ai.usage.cost_usd", s="0.5"),
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
    ])
    assert abs(float(row["cost_usd"]) - 0.5) < 1e-9, row.get("cost_usd")


@pytest.mark.parametrize("spelling", [
    "gen_ai.usage.cache_read.input_tokens",
    "gen_ai.usage.cache_read_input_tokens",
    "gen_ai.usage.cache_creation.input_tokens",
    "gen_ai.usage.cache_creation_input_tokens",
])
def test_every_declared_spelling_is_named_in_the_mapper(spelling):
    """Drift guard. A rename would otherwise pass the behavioural tests
    above by accident, and silently dropping an attribute is exactly how
    the cache counters became zero in the first place."""
    import pathlib

    src = pathlib.Path(_d.__file__).resolve()
    assert f'"{spelling}"' in src.read_text(), (
        f"{spelling} is no longer read by dashboard.py. If that is "
        "deliberate, delete the case here too."
    )


# ── the OTLP logs lane ──────────────────────────────────────────────────

def test_delegated_cursor_lane_reads_the_semconv_spellings(monkeypatch):
    """The same bug, one lane over.

    Cursor cloud-agent usage arrives as OTel *log* records and is filed
    against the delegating agent. That lane already carried cache
    counters, but only under Cursor's own attribute names and a bare
    ``cache_read_tokens`` -- so a cloud agent exporting standard GenAI
    semconv had its cached tokens dropped there too, with the same
    consequence for cost.
    """
    pytest.importorskip("opentelemetry.proto.collector.logs.v1.logs_service_pb2")
    from opentelemetry.proto.collector.logs.v1 import logs_service_pb2
    from opentelemetry.proto.logs.v1 import logs_pb2

    recorded = []
    monkeypatch.setattr(
        _d, "_delegated_record_otel",
        lambda agent_id, tin, tout, cr, cw, model, ts: recorded.append(
            {"cache_read": cr, "cache_write": cw}),
    )
    monkeypatch.setattr(_d, "_delegated_is_agent_id", lambda sid: True)

    rec = logs_pb2.LogRecord(time_unix_nano=1_757_300_000_000_000_000)
    rec.event_name = "cursor.api_request"
    rec.attributes.extend([
        _kv("gen_ai.conversation.id", s="bc-abc123"),
        _kv("gen_ai.request.model", s="claude-opus-5"),
        _kv("gen_ai.usage.input_tokens", i=1240),
        _kv("gen_ai.usage.output_tokens", i=312),
        _kv("gen_ai.usage.cache_read.input_tokens", i=9000),
        _kv("gen_ai.usage.cache_creation.input_tokens", i=400),
    ])
    req = logs_service_pb2.ExportLogsServiceRequest(resource_logs=[
        logs_pb2.ResourceLogs(scope_logs=[logs_pb2.ScopeLogs(log_records=[rec])])
    ])
    _d._process_otlp_logs(req.SerializeToString())

    assert recorded, "the delegated lane recorded nothing for this record"
    assert recorded[0]["cache_read"] == 9000, (
        f"cache_read came through as {recorded[0]['cache_read']!r}. A Cursor "
        "cloud agent on standard GenAI semconv loses its cached tokens."
    )
    assert recorded[0]["cache_write"] == 400
