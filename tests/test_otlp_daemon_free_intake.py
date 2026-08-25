"""WO-7 — daemon-free OTLP intake.

The receiver at ``/v1/logs`` is the path an org uses when it will NOT install a
per-machine daemon: one config value (``OTEL_EXPORTER_OTLP_ENDPOINT``), pushed
by MDM, reviewed once. Before this work order it was a prototype that stamped
``time.time()`` on every record, extracted no identity, and wrote only to an
in-memory cache that a restart erased.

Each test here pins one of the five fixes, plus the honesty properties that
make the numbers safe to bill against:

1. the record's OWN timestamp is stored (batched / backfilled delivery)
2. identity (user / email / org / session) and rollup dims (team / repo)
3. rows land in DuckDB and survive a store restart
4. tool_decision / tool_result become tool events the detectors can read
5. the enterprise ingest image ships opentelemetry-proto (never a 501)

plus: a retried OTLP batch does not double-count spend, a REJECTED permission
prompt is not recorded as a tool call, and absent tool arguments are not
hashed into a fake "identical calls" loop.
"""
import os
import tempfile
import time

import pytest

pytest.importorskip(
    "opentelemetry.proto.collector.logs.v1.logs_service_pb2",
    reason="opentelemetry-proto not installed (pip install clawmetry[otel])",
)

from opentelemetry.proto.collector.logs.v1 import logs_service_pb2  # noqa: E402
from opentelemetry.proto.logs.v1 import logs_pb2  # noqa: E402
from opentelemetry.proto.common.v1 import common_pb2  # noqa: E402

import dashboard as _d  # noqa: E402
from clawmetry import local_store as _ls  # noqa: E402


# ── fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_seen_ids():
    """The metrics-cache dedup set is module state that outlives one test.
    Left dirty, a later test posting an identical payload would be silently
    deduped and its assertion would fail for a reason nothing points at."""
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    yield
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()


@pytest.fixture()
def store(monkeypatch):
    """A private DuckDB writer for one test, wired in as the singleton the
    handler resolves. Never touches the developer's real store."""
    import pathlib

    tmpdir = tempfile.mkdtemp(prefix="clawmetry-wo7-")
    path = os.path.join(tmpdir, "wo7.duckdb")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", path)
    _ls._reset_singleton_for_tests()
    # DB_PATH is module state, resolved at import. Restore it on the way out:
    # leaving it pointed at this test's scratch file makes the NEXT test file
    # open a store it did not create, which is how one test's fixture becomes
    # another test's mystery failure.
    prev_db_path = _ls.DB_PATH
    _ls.DB_PATH = pathlib.Path(path)
    st = _ls.LocalStore()
    monkeypatch.setattr(_ls, "_store_rw", st, raising=False)
    monkeypatch.setattr(_ls, "get_store", lambda read_only=False: st)
    try:
        yield st
    finally:
        try:
            st.stop(flush=True)
        except Exception:
            pass
        _ls.DB_PATH = prev_db_path
        _ls._reset_singleton_for_tests()


def _kv(key, s=None, i=None, d=None, b=None):
    v = common_pb2.AnyValue()
    if s is not None:
        v.string_value = s
    elif i is not None:
        v.int_value = i
    elif d is not None:
        v.double_value = d
    elif b is not None:
        v.bool_value = b
    return common_pb2.KeyValue(key=key, value=v)


# Identity exactly as Claude Code emits it, per record.
def _identity(session_id="sess-wo7"):
    return [
        _kv("session.id", s=session_id),
        _kv("user.id", s="u-42"),
        _kv("user.email", s="dana@acme.example"),
        _kv("organization.id", s="org-acme"),
    ]


# Team / repo as an org sets them via OTEL_RESOURCE_ATTRIBUTES.
def _resource(repo="git@github.com:acme/payments-api.git", team="platform"):
    return [
        _kv("service.name", s="claude-code"),
        _kv("team.id", s=team),
        _kv("repository", s=repo),
        _kv("host.name", s="mac-of-dana"),
    ]


def _export(records, resource_attrs=None):
    scope = logs_pb2.ScopeLogs(log_records=records)
    res = logs_pb2.ResourceLogs(scope_logs=[scope])
    res.resource.attributes.extend(resource_attrs or _resource())
    return logs_service_pb2.ExportLogsServiceRequest(
        resource_logs=[res]
    ).SerializeToString()


def _api_request(when_ns, session_id="sess-wo7", cost=4.10):
    rec = logs_pb2.LogRecord(time_unix_nano=when_ns)
    rec.event_name = "claude_code.api_request"
    rec.attributes.extend(_identity(session_id) + [
        _kv("model", s="claude-opus-4-8"),
        _kv("cost_usd", d=cost),
        _kv("input_tokens", i=1500),
        _kv("output_tokens", i=300),
        _kv("duration_ms", d=820.0),
    ])
    return rec


def _tool_decision(when_ns, tool, decision="accept", session_id="sess-wo7"):
    rec = logs_pb2.LogRecord(time_unix_nano=when_ns)
    rec.event_name = "claude_code.tool_decision"
    rec.attributes.extend(_identity(session_id) + [
        _kv("tool_name", s=tool),
        _kv("decision", s=decision),
        _kv("source", s="config"),
    ])
    return rec


def _tool_result(when_ns, tool, success=True, error="", session_id="sess-wo7"):
    rec = logs_pb2.LogRecord(time_unix_nano=when_ns)
    rec.event_name = "claude_code.tool_result"
    attrs = _identity(session_id) + [
        _kv("tool_name", s=tool),
        _kv("success", b=success),
        _kv("duration_ms", d=120.0),
    ]
    if error:
        attrs.append(_kv("error", s=error))
    rec.attributes.extend(attrs)
    return rec


# ── Fix 1: honour the record's own timestamp ────────────────────────────────

def test_batched_delivery_keeps_its_own_timestamps(store):
    """A batch delivered now, describing work from six hours ago, must land
    six hours ago. The prototype stamped time.time() on every record, so any
    daily rollup over a retried or buffered export was silently wrong."""
    six_hours_ago = time.time() - 6 * 3600
    _d._process_otlp_logs(_export([_api_request(int(six_hours_ago * 1e9))]))

    rows = store.query_otlp_records(session_id="sess-wo7")
    assert len(rows) == 1
    assert abs(rows[0]["ts"] - six_hours_ago) < 1.0, rows[0]["ts"]
    # And receipt time is kept separately, not conflated with it.
    assert rows[0]["received_at"] - rows[0]["ts"] > 5 * 3600


def test_observed_time_is_used_when_the_record_has_no_event_time(store):
    """Exporters may set only observedTimeUnixNano. Falling through to
    receipt time there is the same misdating bug in a different coat."""
    observed = time.time() - 3600
    rec = _api_request(0)
    rec.observed_time_unix_nano = int(observed * 1e9)
    _d._process_otlp_logs(_export([rec]))

    rows = store.query_otlp_records(session_id="sess-wo7")
    assert abs(rows[0]["ts"] - observed) < 1.0


def test_metrics_cache_gets_the_record_timestamp_too(store, monkeypatch):
    """The live tiles read the in-memory cache; if only the DuckDB row is
    correctly dated, today's tile still counts yesterday's spend."""
    captured = []
    monkeypatch.setattr(
        _d, "_add_metric", lambda cat, e: captured.append((cat, e))
    )
    when = time.time() - 2 * 3600
    _d._process_otlp_logs(_export([_api_request(int(when * 1e9))]))
    cost = next(e for c, e in captured if c == "cost")
    assert abs(cost["timestamp"] - when) < 1.0


# ── Fix 2: identity extraction ──────────────────────────────────────────────

def test_identity_is_extracted_from_the_record_and_the_resource(store):
    _d._process_otlp_logs(_export([_api_request(int(time.time() * 1e9))]))
    row = store.query_otlp_records(session_id="sess-wo7")[0]

    assert row["user_id"] == "u-42"
    assert row["user_email"] == "dana@acme.example"
    assert row["org_id"] == "org-acme"
    assert row["session_id"] == "sess-wo7"
    assert row["team"] == "platform"
    # An ssh remote, an https URL and a checkout path must land on one key,
    # or a per-repo rollup fragments into three rows for one repo.
    assert row["repo"] == "payments-api"
    assert row["agent_type"] == "claude_code"
    assert row["node_id"] == "mac-of-dana"
    # The raw value is not thrown away.
    assert row["attributes"]["repo_raw"].endswith("payments-api.git")


@pytest.mark.parametrize("raw,expected", [
    ("git@github.com:acme/payments-api.git", "payments-api"),
    ("https://github.com/acme/payments-api", "payments-api"),
    ("/Users/dana/src/payments-api", "payments-api"),
    ("payments-api", "payments-api"),
    ("", None),
])
def test_repo_key_normalisation(raw, expected):
    assert _d._otlp_repo_key(raw) == expected


# ── Fix 3: it survives a restart ────────────────────────────────────────────

def test_rows_survive_a_store_restart(store, monkeypatch, tmp_path):
    """The acceptance criterion the in-memory cache could never meet."""
    _d._process_otlp_logs(_export([_api_request(int(time.time() * 1e9))]))
    db_path = str(_ls.DB_PATH)
    store.stop(flush=True)

    reopened = _ls.LocalStore(read_only=True)
    try:
        rows = reopened.query_otlp_records(session_id="sess-wo7")
        assert len(rows) == 1
        assert rows[0]["cost_usd"] == pytest.approx(4.10)
        assert os.path.exists(db_path)
    finally:
        reopened.stop(flush=False)


def test_a_retried_batch_does_not_double_count_spend(store):
    """OTLP delivery is at-least-once. An exporter that misses our 200 resends
    the batch, and spend that doubles on a network blip is worse than none."""
    payload = _export([_api_request(int(time.time() * 1e9))])
    _d._process_otlp_logs(payload)
    _d._process_otlp_logs(payload)
    _d._process_otlp_logs(payload)

    rows = store.query_otlp_records(session_id="sess-wo7")
    assert len(rows) == 1
    total = sum(r["cost_usd"] or 0 for r in rows)
    assert total == pytest.approx(4.10)


# ── Fix 4: tool events reach the detectors ──────────────────────────────────

def test_tool_records_become_tool_events(store):
    now = time.time()
    recs = [
        _tool_decision(int((now - 30) * 1e9), "Bash"),
        _tool_result(int((now - 29) * 1e9), "Bash", success=False,
                     error="command not found: pytest"),
    ]
    _d._process_otlp_logs(_export(recs))

    events = store.query_events(session_id="sess-wo7", limit=50)
    types = {e["event_type"] for e in events}
    assert "tool_call" in types and "tool_result" in types, types
    result = next(e for e in events if e["event_type"] == "tool_result")
    assert result["data"]["tool"] == "Bash"
    assert result["data"]["is_error"] is True


def test_trajectory_detectors_fire_on_the_otlp_path(store):
    """The point of mapping tool events: a session that fails the same tool
    over and over is visible on a deployment with no daemon on any machine."""
    from clawmetry import detectors

    now = time.time()
    recs = []
    for i in range(8):
        recs.append(_tool_decision(int((now - 60 + i * 2) * 1e9), "Bash"))
        recs.append(
            _tool_result(int((now - 59 + i * 2) * 1e9), "Bash", success=False,
                         error="command not found: pytest")
        )
    _d._process_otlp_logs(_export(recs))

    events = store.query_events(session_id="sess-wo7", limit=200)
    incident = detectors.repeated_tool_failure(events, "sess-wo7", "claude_code")
    assert incident is not None, "repeated tool failures went unseen"
    assert incident["kind"] == "repeated_tool_failure"


def test_unknown_tool_arguments_do_not_fabricate_a_loop(store):
    """This path usually carries no tool arguments. Hashing "no args" to one
    constant would make five Reads of five different files look like the agent
    repeating itself — a false alarm on someone's real work."""
    from clawmetry import detectors

    now = time.time()
    recs = [
        _tool_decision(int((now - 30 + i) * 1e9), "Read") for i in range(10)
    ]
    _d._process_otlp_logs(_export(recs))

    events = store.query_events(session_id="sess-wo7", limit=200)
    steps = [e for e in events if e["event_type"] == "tool_call"]
    assert len(steps) == 10
    hashes = {
        detectors._args_hash(e["data"].get("args")) for e in steps
    }
    assert len(hashes) == 10, "identical arg hashes would read as a loop"
    assert detectors.stuck_loop(events, "sess-wo7", "claude_code") is None


def test_a_rejected_permission_is_not_a_tool_call(store):
    """The tool never ran. Counting it as a call tells the no-progress
    detector the agent acted, when it was blocked waiting for a human."""
    now = time.time()
    _d._process_otlp_logs(_export([
        _tool_decision(int(now * 1e9), "Bash", decision="reject"),
    ]))
    events = store.query_events(session_id="sess-wo7", limit=50)
    assert [e for e in events if e["event_type"] == "tool_call"] == []
    # The decision itself is still on the record, for the audit trail.
    row = store.query_otlp_records(session_id="sess-wo7")[0]
    assert row["decision"] == "reject"


# ── The payoff: a rollup from the ingested rows alone ───────────────────────

def test_rollup_by_team_and_repo(store):
    now = time.time()
    _d._process_otlp_logs(_export(
        [_api_request(int(now * 1e9), session_id="s1", cost=4.0)],
        resource_attrs=_resource(repo="acme/payments-api", team="platform"),
    ))
    _d._process_otlp_logs(_export(
        [_api_request(int(now * 1e9), session_id="s2", cost=1.5)],
        resource_attrs=_resource(repo="acme/web", team="growth"),
    ))
    _d._process_otlp_logs(_export(
        [_api_request(int(now * 1e9), session_id="s3", cost=2.5)],
        resource_attrs=_resource(repo="acme/payments-api", team="platform"),
    ))

    by_team = {r["key"]: r for r in store.query_otlp_rollup(dimension="team")}
    assert by_team["platform"]["cost_usd"] == pytest.approx(6.5)
    assert by_team["platform"]["sessions"] == 2
    assert by_team["growth"]["cost_usd"] == pytest.approx(1.5)

    by_repo = {r["key"]: r for r in store.query_otlp_rollup(dimension="repo")}
    assert by_repo["payments-api"]["cost_usd"] == pytest.approx(6.5)
    assert by_repo["web"]["tokens"] == 1800

    by_person = {
        r["key"]: r for r in store.query_otlp_rollup(dimension="user_email")
    }
    assert by_person["dana@acme.example"]["records"] == 3


def test_rollup_rejects_an_unknown_dimension(store):
    with pytest.raises(ValueError):
        store.query_otlp_rollup(dimension="cost_usd; DROP TABLE events")


# ── Fix 5: the enterprise image can never answer 501 ────────────────────────

def test_enterprise_image_ships_the_otlp_protobuf_dependency():
    """deploy/self-hosted/docker-compose.yml builds the root Dockerfile. A
    receiver that answers 501 until someone remembers `pip install
    clawmetry[otel]` is not a receiver an org can point 500 machines at."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dockerfile = open(os.path.join(root, "Dockerfile")).read()
    assert "opentelemetry-proto" in dockerfile
    assert "protobuf" in dockerfile

    compose = open(
        os.path.join(root, "deploy", "self-hosted", "docker-compose.yml")
    ).read()
    assert "context: ../.." in compose, "compose must build that Dockerfile"


def test_receiver_is_reachable_without_a_daemon(store, monkeypatch):
    """No store at all (a first boot before DuckDB is ready) must not 500 the
    receiver — the exporter would retry forever and the org would see drops."""
    monkeypatch.setattr(
        _ls, "get_store", lambda read_only=False: (_ for _ in ()).throw(
            RuntimeError("no store")
        )
    )
    _d._process_otlp_logs(_export([_api_request(int(time.time() * 1e9))]))


# ── Hybrid installs: the daemon wins, nothing is counted twice ──────────────

def test_a_session_the_daemon_already_owns_is_not_duplicated(store):
    """A machine can have BOTH the daemon and the org's OTEL config. The same
    session then arrives twice — read from the transcript, and pushed by the
    runtime. Spend that doubles because two collectors both did their job is
    worse than spend that is missing."""
    now = time.time()
    # The daemon got there first: a transcript-derived event for this session.
    store.ingest({
        "id": "daemon-evt-1",
        "node_id": "mac-of-dana",
        "agent_type": "claude_code",
        "session_id": "sess-wo7",
        "event_type": "tool_call",
        "ts": "2026-08-25T10:00:00+00:00",
        "cost_usd": 4.10,
        "data": {"tool": "Bash", "args": {"command": "pytest"}},
    })
    store._flush_now()

    _d._process_otlp_logs(_export([
        _api_request(int(now * 1e9)),
        _tool_decision(int(now * 1e9), "Bash"),
    ]))

    events = store.query_events(session_id="sess-wo7", limit=50)
    assert [e for e in events if str(e["id"]).startswith("otlp:")] == []
    assert sum(e.get("cost_usd") or 0 for e in events) == pytest.approx(4.10)

    # The identity ledger still records everything — the org rollup does not
    # lose a machine just because that machine also runs a daemon.
    rows = store.query_otlp_records(session_id="sess-wo7")
    assert len(rows) == 2


def test_a_daemon_free_session_still_gets_its_events(store):
    """The control for the test above: with no daemon rows, the events land."""
    now = time.time()
    _d._process_otlp_logs(_export([
        _api_request(int(now * 1e9)),
        _tool_decision(int(now * 1e9), "Bash"),
    ]))
    events = store.query_events(session_id="sess-wo7", limit=50)
    assert [e for e in events if str(e["id"]).startswith("otlp:")]
    assert sum(e.get("cost_usd") or 0 for e in events) == pytest.approx(4.10)


def test_a_retried_batch_does_not_double_the_live_tiles_either(store, monkeypatch):
    """The DuckDB ledger dedups on the record id, but a person looks at the
    tile, not the table. Both have to hold, or the receiver reports a spike
    that is really the network retrying."""
    captured = []
    monkeypatch.setattr(
        _d, "_add_metric", lambda cat, e: captured.append((cat, e))
    )
    payload = _export([_api_request(int(time.time() * 1e9))])
    _d._process_otlp_logs(payload)
    _d._process_otlp_logs(payload)

    costs = [e for c, e in captured if c == "cost"]
    assert len(costs) == 1, f"retry counted {len(costs)} times in the tiles"
    assert costs[0]["usd"] == pytest.approx(4.10)


def test_the_cache_dedup_set_stays_bounded(monkeypatch):
    """A receiver that runs for a month must not grow a set forever."""
    monkeypatch.setattr(_d, "_OTLP_SEEN_MAX", 10)
    _d._otlp_seen_ids.clear()
    _d._otlp_seen_order.clear()
    for i in range(50):
        assert _d._otlp_seen(f"rec-{i}") is False
    assert len(_d._otlp_seen_ids) <= 10
    assert len(_d._otlp_seen_order) <= 10
    # The newest is still remembered; the oldest has aged out, which is the
    # trade: a bounded guard, not a permanent ledger.
    assert _d._otlp_seen("rec-49") is True
    assert _d._otlp_seen("rec-0") is False
