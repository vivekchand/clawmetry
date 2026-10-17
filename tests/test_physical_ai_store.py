"""Built-in free physical evidence on the existing daemon-owned DuckDB store."""
import json

import pytest

from clawmetry.asimov.journal import JournalWriter
from clawmetry.asimov.store import AsimovLocalStore, physical_ai_snapshot


@pytest.fixture(scope="session", autouse=True)
def server():
    yield None


@pytest.fixture
def db(tmp_path, monkeypatch):
    from clawmetry import local_store
    path = tmp_path / "physical.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(path))
    monkeypatch.setattr(local_store, "DB_PATH", path)
    store = local_store.LocalStore()
    yield store
    store.stop()


def capture(directory, *, source="jumper_native", robot_type="jumper", run_id="a" * 32, incident=None):
    writer = JournalWriter("desk-robot", source, directory=directory, environment="simulation",
                           robot_type=robot_type, run_id=run_id,
                           metadata={"task": "reminder", "robot_type": "must-not-override"})
    writer.emit("observation", {"mode": "standing", "table_margin_m": .3}, block=True)
    if incident is not None:
        writer.emit("guard.incident", incident, block=True)
    writer.close()
    return writer


def test_generic_projection_and_asimov_view_are_separate(db, tmp_path):
    directory = tmp_path / "journal"
    first = capture(directory)
    second = capture(directory, source="asimov_recording", robot_type="asimov_1", run_id="b" * 32)
    projection = AsimovLocalStore(db, initialize=True)
    assert projection.ingest(directory) == 6
    assert {r["run_id"] for r in db.query_physical_ai_runs()["runs"]} == {first.run_id, second.run_id}
    assert [r["run_id"] for r in db.query_asimov_runs()["runs"]] == [second.run_id]
    assert db.query_asimov_events(run_id=first.run_id)["events"] == []
    events = db.query_physical_ai_events(run_id=first.run_id, limit=2)
    assert len(events["events"]) == 2 and events["has_more"] and events["next_after"] == 2
    rest = db.query_physical_ai_events(run_id=first.run_id, after=2)
    assert [e["kind"] for e in rest["events"]] == ["run.ended"]
    assert events["events"][0]["data"]["robot_type"] == "jumper"
    generic = physical_ai_snapshot(db)
    assert generic["schema"] == "clawmetry.physical_ai.snapshot.v1"
    assert generic["navigation"] == [{"label": "Physical AI", "href": "/physical-ai", "view_group": "physical_ai"}]
    assert len(generic["runs"]) == 2
    assert len(projection.snapshot()["runs"]) == 1
    assert projection.snapshot()["schema"] == "clawmetry.asimov.snapshot.v1"
    assert len(json.dumps(generic).encode()) < 64 * 1024
    before = generic["runs"][-1]
    assert db.query_physical_ai_runs(limit=1)["has_more"]
    assert db.query_physical_ai_runs(before_ns=before["updated_ns"], before_run_id=before["run_id"])["runs"] == []


def test_only_new_known_guard_findings_dispatch_after_commit_without_private_text(db, tmp_path, monkeypatch):
    from clawmetry import incident_alerts
    calls = []
    def delivered(store, incident, **kwargs):
        assert store._write_lock.acquire(blocking=False), "Delivery held the daemon writer lock"
        store._write_lock.release()
        assert store._fetch("SELECT count(*) FROM asimov_events WHERE kind='guard.incident'", [])[0][0] == 1
        calls.append((incident, kwargs))
        return {"delivered": True, "delivered_via": ["banner"]}
    monkeypatch.setattr(incident_alerts, "deliver_incident", delivered)
    directory = tmp_path / "journal"
    writer = capture(directory, incident={"kind": "boundary_crossed", "severity": "info",
                                         "message": "SECRET robot prompt and measurements", "coordinates": [99,88,77]})
    projection = AsimovLocalStore(db, initialize=True)
    assert projection.ingest(directory) == 4
    assert len(calls) == 1
    incident, kwargs = calls[0]
    assert incident["severity"] == "critical" and incident["runtime"] == "jumper"
    assert incident["session_id"] == "physical_ai:" + writer.run_id
    assert "Simulation:" in incident["title"]
    assert "SECRET" not in json.dumps(calls) and "coordinates" not in json.dumps(calls)
    assert kwargs == {"source": "physical_ai"}
    assert projection.ingest(directory) == 0
    # A duplicate rotated segment retains exact evidence without re-notifying.
    (directory / (writer.run_id + ".00000001.jsonl")).write_bytes(writer.path.read_bytes())
    assert projection.ingest(directory) == 0
    assert len(calls) == 1


@pytest.mark.parametrize("source,kind", [("asimov_sdk", "boundary_crossed"),
                                         ("jumper_native", "unrecognized_source_text")])
def test_other_sources_or_unknown_findings_do_not_notify(db, tmp_path, monkeypatch, source, kind):
    from clawmetry import incident_alerts
    monkeypatch.setattr(incident_alerts, "deliver_incident", lambda *_a, **_k: pytest.fail("Unexpected notification"))
    directory = tmp_path / "journal"
    capture(directory, source=source, incident={"kind": kind})
    projection = AsimovLocalStore(db, initialize=True)
    assert projection.ingest(directory) == 4
    assert db.query_physical_ai_events(run_id="a" * 32)["events"][2]["kind"] == "guard.incident"


@pytest.mark.parametrize("robot_type", [None, "", "x" * 101, "bad\nname"])
def test_robot_type_validation_does_not_create_a_journal(tmp_path, robot_type):
    with pytest.raises(ValueError):
        JournalWriter("desk", "jumper_app", directory=tmp_path / "journal", robot_type=robot_type)
    assert not (tmp_path / "journal").exists()


def test_legacy_default_robot_type_is_unchanged(tmp_path):
    writer = JournalWriter("asimov", "asimov_sdk", directory=tmp_path / "journal")
    writer.close()
    assert json.loads(writer.path.read_text().splitlines()[0])["data"]["robot_type"] == "asimov_1"


def test_shared_queries_and_daemon_only_fallback_read_persisted_jumper(db, tmp_path, monkeypatch):
    from clawmetry import local_store, sync
    from routes import local_query
    directory = tmp_path / "journal"
    writer = capture(directory, source="jumper_app")
    projection = AsimovLocalStore(db, initialize=True)
    projection.ingest(directory)
    monkeypatch.setattr(local_query, "_store", lambda: db)
    monkeypatch.setattr(local_query, "_proxy_dispatch", lambda *_a: (_ for _ in ()).throw(RuntimeError("No proxy in test")))
    monkeypatch.setattr(local_store, "get_store", lambda **_kwargs: db)
    assert local_query._dispatch("physical_ai_runs", {"limit": 1})["runs"][0]["run_id"] == writer.run_id
    assert local_query._dispatch("physical_ai_events", {"run_id": writer.run_id, "limit": 1})["events"][0]["kind"] == "run.started"
    fallback = sync._local_dispatch_fallback("physical_ai_events", {"run_id": writer.run_id, "limit": 1, "node_id": "ignored"})
    assert fallback["events"][0]["kind"] == "run.started" and fallback["_via"] == "fallback"


@pytest.mark.parametrize("shape,args", [
    ("physical_ai_runs", {"before_run_id": "a" * 32}),
    ("physical_ai_runs", {"before_ns": 1}),
    ("physical_ai_runs", {"before_ns": "bad", "before_run_id": "a" * 32}),
    ("physical_ai_runs", {"before_ns": "1", "before_run_id": "bad"}),
    ("physical_ai_runs", {"before_ns": True, "before_run_id": "a" * 32}),
    ("physical_ai_runs", {"before_ns": 2**63, "before_run_id": "a" * 32}),
    ("physical_ai_runs", {"robot_id": {}}),
    ("physical_ai_runs", {"robot_id": ""}),
    ("physical_ai_runs", {"robot_id": "a" * 201}),
    ("physical_ai_runs", {"robot_id": "bad\nname"}),
    ("physical_ai_runs", {"limit": 101}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": "garbage"}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": True}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": 1.0}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": "١"}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": -1}),
    ("physical_ai_events", {"run_id": "a" * 32, "after": 2**63}),
    ("physical_ai_events", {"run_id": "a" * 32, "limit": 501}),
])
def test_shared_queries_reject_bad_cursors_before_proxy_or_store(monkeypatch, shape, args):
    from clawmetry import local_store, sync
    from routes import local_query
    monkeypatch.setattr(local_query, "_proxy_dispatch", lambda *_a: pytest.fail("Malformed query reached proxy"))
    monkeypatch.setattr(local_query, "_store", lambda: pytest.fail("Malformed query reached store"))
    with pytest.raises(ValueError):
        local_query._dispatch(shape, args)
    monkeypatch.setattr(local_store, "get_store", lambda **_kw: pytest.fail("Malformed fallback opened store"))
    with pytest.raises(ValueError):
        sync._local_dispatch_fallback(shape, args)


def test_shared_query_cursor_coercion_preserves_exact_large_values():
    from routes.local_query import _coerce_args
    cursor = 2**63 - 1
    assert _coerce_args("physical_ai_runs", {"before_ns": str(cursor), "before_run_id": "b" * 32}) == {
        "limit": 20, "robot_id": None, "before_ns": cursor, "before_run_id": "b" * 32}
    assert _coerce_args("physical_ai_events", {"run_id": "a" * 32, "after": str(cursor)}) == {
        "run_id": "a" * 32, "after": cursor, "limit": 200}


@pytest.mark.parametrize("method", ["query_physical_ai_runs", "query_physical_ai_events"])
def test_internal_physical_rpc_requires_daemon_token(method, monkeypatch):
    from flask import Flask
    from clawmetry import local_server
    from routes import local_query
    monkeypatch.setattr(local_server, "_token", "private-test-token")
    monkeypatch.setattr(local_query, "_store", lambda: pytest.fail("Unauthorized robot RPC read the store"))
    app = Flask(__name__)
    app.register_blueprint(local_query.bp_local_query)
    response = app.test_client().post("/__local_query__/" + method, json={"kwargs": {}})
    assert response.status_code == 401


def test_shared_notification_latch_persists_and_honors_cooldown(db, tmp_path, monkeypatch):
    from clawmetry import incident_alerts
    from clawmetry.physical_ai.alerts import dispatch
    banners = []
    monkeypatch.setattr(incident_alerts, "resolve_delivery", lambda: {"enabled": True, "channels": ["banner"]})
    monkeypatch.setattr(incident_alerts, "persist_banner", lambda *a, **kw: banners.append((a, kw)) or True)
    monkeypatch.setattr(incident_alerts, "send_desktop", lambda *_a, **_k: False)
    monkeypatch.setattr(incident_alerts, "send_cloud", lambda *_a, **_k: False)
    directory = tmp_path / "journal"
    writer = capture(directory, source="jumper_recording", incident={"kind": "boundary_crossed"})
    projection = AsimovLocalStore(db, initialize=True)
    projection.ingest(directory)
    assert len(banners) == 1
    assert "Recorded simulation:" in banners[0][0][1]
    sid = "physical_ai:" + writer.run_id
    assert db.incident_alert_last_sent(sid, "physical_ai_boundary_crossed") > 0
    event = db.query_physical_ai_events(run_id=writer.run_id)["events"][2]
    monkeypatch.setattr(incident_alerts, "_MEMO", {})
    result = dispatch(db, event)
    assert not result["delivered"] and "cooldown" in result["reason"]
    receipts = db.query_incident_alerts()
    assert receipts[0]["session_id"] == sid
    assert receipts[0]["delivered_via"] == ["banner"]
    assert len(banners) == 1
