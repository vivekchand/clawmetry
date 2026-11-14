"""Asimov acceptance at the real daemon-owned DuckDB boundary.

REQ-ASIMOV-001, 002, 004, 005 and 006: free operation, truthful telemetry,
immutable replay, bounded malformed-input handling and encrypted serialization.
These are isolated hardware-free tests, not physical robot qualification.
"""
from __future__ import annotations

import base64
import builtins
import copy
import json
import os

import pytest

from clawmetry.asimov.store import MAX_LINE, AsimovLocalStore

RUN = "a" * 32
OTHER_RUN = "b" * 32
STAMP = 1_792_086_400_123_456_789


@pytest.fixture(scope="session", autouse=True)
def server():
    """These persistence tests require no HTTP server or ambient gateway token."""
    yield None


@pytest.fixture
def db(tmp_path, monkeypatch):
    """Use LocalStore's real schema, capped connection and transaction lock."""
    from clawmetry import local_store

    path = tmp_path / "asimov.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(path))
    monkeypatch.setattr(local_store, "DB_PATH", path)
    store = local_store.LocalStore()
    yield store
    store.stop()


@pytest.fixture
def projection(db):
    return AsimovLocalStore(db, initialize=True)


def event(sequence, kind="observation", *, data=None, run_id=RUN,
          stamp=STAMP, robot_id="lab-asimov", dropped=0):
    return {"schema": "clawmetry.robotics.v1", "run_id": run_id,
            "robot_id": robot_id, "environment": "hardware", "sequence": sequence,
            "wall_time_ns": str(stamp), "monotonic_ns": str(9_007_199_254_740_999 + sequence),
            "kind": kind, "dropped_total": dropped, "data": {} if data is None else data}


def start(*, source="asimov_sdk", run_id=RUN, stamp=STAMP):
    return event(1, "run.started", run_id=run_id, stamp=stamp,
                 data={"source_kind": source, "robot_type": "asimov_1",
                       "observation_only": True, "complete_control_trace": False,
                       "validation": "sdk_only_hardware_unverified"})


def state():
    joints = [{"name": "actuator_" + str(i), "position_rad": i / 10,
               "velocity_rad_s": -i / 100, "current_amp": i / 50,
               "temperature_c": 30 + i} for i in range(25)]
    joints[4]["current_amp"] = None
    joints[7]["position_rad"] = None
    joints[18]["temperature_c"] = None
    return {"mode": "BALANCE", "joints": joints,
            "base": {"quaternion_wxyz": [1.0, 0.0, 0.0, 0.0],
                     "angular_velocity_rad_s": [0.1, None, 0.3]},
            "battery": {"voltage_v": 48.1, "current_amp": -2.3,
                        "soc_percent": 74.0, "max_cell_temperature_c": None,
                        "protection_flags": ["CHARGE_OVER_TEMP"]},
            "alerts": [{"name": "MOTOR_TEMPERATURE", "severity": "WARNING", "joint": 18}],
            "source_wall_time_ns": str(STAMP - 123_456),
            "source_sequence": 102, "fw_timestamp_us": 123_456,
            "received_at_monotonic_s": 9.5}


def write(directory, events, *, name=None):
    directory.mkdir(exist_ok=True)
    path = directory / (name or RUN + ".jsonl")
    path.write_text("".join(json.dumps(item, allow_nan=False) + "\n" for item in events))
    return path


def cursor(db, path):
    rows = db._fetch("SELECT byte_offset,discarding,invalid_count FROM asimov_cursors WHERE source=?",
                     [str(path)])
    return rows[0] if rows else None


def test_free_store_reads_real_evidence_without_pro_or_license(projection, tmp_path, monkeypatch):
    """Queries read persisted DuckDB evidence without Pro or a license.

    AC-ASIMOV-005.3
    AC-ASIMOV-001.1
    """
    from clawmetry import entitlements

    original_import = builtins.__import__

    def no_private_package(name, *args, **kwargs):
        if name == "clawmetry_pro" or name.startswith("clawmetry_pro."):
            raise AssertionError("The free Asimov read path attempted a private import")
        return original_import(name, *args, **kwargs)

    def no_license_lookup(*args, **kwargs):
        raise AssertionError("Free Asimov evidence must not require an entitlement")

    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setattr(builtins, "__import__", no_private_package)
    monkeypatch.setattr(entitlements, "get_entitlement", no_license_lookup)
    write(tmp_path, [start(), event(2, data=state())])
    assert projection.ingest(tmp_path) == 2
    run = projection.runs()["runs"][0]
    assert run["robot_id"] == "lab-asimov"
    assert run["command_outcome"] == "unknown"
    assert run["hardware_verified"] is False
    assert len(projection.events(run_id=RUN)["events"]) == 2


def test_all_25_joint_units_nulls_battery_and_source_clocks_survive(projection, tmp_path):
    """AC-002.2/3 and AC-005.4: persistence never changes measured evidence."""
    sample = state()
    write(tmp_path, [start(), event(2, data=sample)])
    projection.ingest(tmp_path)
    observed = projection.runs()["runs"][0]["observation"]
    assert observed == sample
    assert len(observed["joints"]) == 25
    assert observed["joints"][4]["current_amp"] is None
    assert observed["joints"][7]["position_rad"] is None
    assert observed["joints"][18]["temperature_c"] is None
    assert all("effort_nm" not in joint for joint in observed["joints"])
    assert "position_m" not in observed["base"]
    assert observed["battery"]["max_cell_temperature_c"] is None
    assert observed["source_wall_time_ns"] == str(STAMP - 123_456)


def test_identical_replays_deduplicate_and_conflicts_are_visible(projection, db, tmp_path):
    source = [start(), event(2, data=state())]
    path = write(tmp_path, source)
    assert projection.ingest(tmp_path) == 2
    with path.open("a") as stream:
        for item in source:
            stream.write(json.dumps(item) + "\n")
        conflict = copy.deepcopy(source[1])
        conflict["data"]["joints"][0]["position_rad"] = 999.0
        stream.write(json.dumps(conflict) + "\n")
    assert projection.ingest(tmp_path) == 0
    assert projection.runs()["runs"][0]["event_count"] == 2
    assert projection.events(run_id=RUN)["events"] == source
    assert cursor(db, path)[2] == 1


def test_failed_ingest_rolls_back_events_run_and_cursor(projection, db, tmp_path, monkeypatch):
    """AC-004.3: a failed database batch must be fully replayable."""
    path = write(tmp_path, [start(), event(2, data=state())])
    original = projection._insert

    def unavailable_database(conn, item):
        if item["sequence"] == 2:
            raise RuntimeError("injected storage failure")
        return original(conn, item)

    monkeypatch.setattr(projection, "_insert", unavailable_database)
    with pytest.raises(RuntimeError, match="injected storage failure"):
        projection.ingest(tmp_path)
    assert projection.runs()["runs"] == []
    assert projection.events(run_id=RUN)["events"] == []
    assert cursor(db, path) is None
    monkeypatch.setattr(projection, "_insert", original)
    assert projection.ingest(tmp_path) == 2
    assert cursor(db, path)[0] == path.stat().st_size


def test_malformed_line_skipped_and_truncated_record_waits_for_newline(projection, db, tmp_path):
    path = write(tmp_path, [start()])
    with path.open("ab") as stream:
        stream.write(b"not-json\n")
        stream.write(json.dumps(event(2, data=state())).encode()[:-3])
    complete_offset = len((json.dumps(start()) + "\n").encode()) + len(b"not-json\n")
    assert projection.ingest(tmp_path) == 1
    assert cursor(db, path) == (complete_offset, False, 1)
    with path.open("ab") as stream:
        stream.write(json.dumps(event(2, data=state())).encode()[-3:] + b"\n")
    assert projection.ingest(tmp_path) == 1
    assert projection.runs()["runs"][0]["observation"] == state()
    assert cursor(db, path) == (path.stat().st_size, False, 1)


def test_oversized_record_is_drained_across_passes_without_losing_next_event(projection, db, tmp_path):
    path = write(tmp_path, [start()])
    projection.ingest(tmp_path)
    with path.open("ab") as stream:
        stream.write(b"x" * (MAX_LINE * 2 + 20) + b"\n")
        stream.write((json.dumps(event(2, data=state())) + "\n").encode())
    assert projection.ingest(tmp_path, max_lines=1) == 0
    assert cursor(db, path)[1:] == (True, 1)
    for _ in range(5):
        projection.ingest(tmp_path, max_lines=1)
    assert projection.runs()["runs"][0]["event_count"] == 2
    assert cursor(db, path) == (path.stat().st_size, False, 1)


def test_numbered_rotation_and_replaced_inode_preserve_history(projection, db, tmp_path):
    path = write(tmp_path, [start()])
    segment = write(tmp_path, [event(2, data=state())], name=RUN + ".00000001.jsonl")
    assert projection.ingest(tmp_path) == 2
    replacement = write(tmp_path, [start(), event(3, "run.ended")], name="replacement")
    os.replace(replacement, path)
    assert projection.ingest(tmp_path) == 1
    assert projection.runs()["runs"][0]["event_count"] == 3
    assert projection.runs()["runs"][0]["status"] == "ended"
    assert cursor(db, segment)[0] == segment.stat().st_size
    assert [item["sequence"] for item in projection.events(run_id=RUN)["events"]] == [1, 2, 3]


def test_other_robotics_source_is_not_reclassified_as_asimov(projection, db, tmp_path):
    other = [start(source="rp1_mujoco", run_id=OTHER_RUN),
             event(2, data=state(), run_id=OTHER_RUN)]
    path = write(tmp_path, other, name=OTHER_RUN + ".jsonl")
    assert projection.ingest(tmp_path) == 0
    assert projection.runs()["runs"] == []
    assert cursor(db, path)[2] == 0
    write(tmp_path, [start(), event(2, data=state())])
    assert projection.ingest(tmp_path) == 2
    assert [run["run_id"] for run in projection.runs()["runs"]] == [RUN]


def test_imported_recordings_never_appear_live_even_when_just_recorded(projection, tmp_path, monkeypatch):
    import clawmetry.asimov.store as module

    monkeypatch.setattr(module.time, "time_ns", lambda: STAMP + 1)
    write(tmp_path, [start(source="asimov_recording"), event(2, data=state())])
    projection.ingest(tmp_path)
    run = projection.runs()["runs"][0]
    assert run["observation_age_s"] < 0.001
    assert run["status"] == "recorded"
    assert run["hardware_verified"] is False


def test_newest_sequence_wins_over_late_arriving_observation_and_lifecycle(projection, tmp_path):
    new = state()
    new["mode"] = "DAMP"
    write(tmp_path, [start(), event(5, data=new, stamp=STAMP + 100),
                     event(3, data=state(), stamp=STAMP + 200),
                     event(7, "run.ended", stamp=STAMP + 300),
                     event(6, "telemetry.restored", stamp=STAMP + 400)])
    projection.ingest(tmp_path)
    run = projection.runs()["runs"][0]
    assert run["observation"] == new
    assert run["last_sequence"] == 7
    assert run["updated_ns"] == str(STAMP + 400)
    assert run["status"] == "ended"
    assert [item["sequence"] for item in projection.events(run_id=RUN)["events"]] == [1, 3, 5, 6, 7]


def test_reopen_same_duckdb_keeps_evidence_and_tail_offset(projection, db, tmp_path):
    from clawmetry import local_store

    path = write(tmp_path, [start(), event(2, data=state())])
    projection.ingest(tmp_path)
    before = projection.events(run_id=RUN)
    db.stop()
    reopened = local_store.LocalStore()
    try:
        after = AsimovLocalStore(reopened, initialize=True)
        assert after.events(run_id=RUN) == before
        assert after.ingest(tmp_path) == 0
        with path.open("a") as stream:
            stream.write(json.dumps(event(3, "run.ended")) + "\n")
        assert after.ingest(tmp_path) == 1
        assert after.runs()["runs"][0]["status"] == "ended"
    finally:
        reopened.stop()


def test_snapshot_encrypts_losslessly_with_nanoseconds_and_no_status_credentials(projection, tmp_path):
    from clawmetry.sync import decrypt_payload, encrypt_payload

    write(tmp_path, [start(), event(2, data=state())])
    secret = "observe-token-must-not-be-exported"
    (tmp_path / (RUN + ".status.json")).write_text(json.dumps({
        "run_id": RUN, "active": False, "queued": 0, "written": 2,
        "dropped_total": 0, "errors": 0, "incomplete": False,
        "last_error": "upstream URL includes " + secret,
        "token": secret, "path": "/private/credential-bearing-recording"}))
    projection.ingest(tmp_path)
    snapshot = projection.snapshot()
    wire = json.dumps(snapshot, allow_nan=False)
    assert secret not in wire
    assert "credential-bearing-recording" not in wire
    assert snapshot["runs"][0]["started_ns"] == str(STAMP)
    assert snapshot["runs"][0]["observation"]["source_wall_time_ns"] == str(STAMP - 123_456)
    key = base64.b64encode(os.urandom(32)).decode()
    encrypted = encrypt_payload({"asimov": snapshot}, key)
    assert secret not in encrypted
    assert decrypt_payload(encrypted, key) == {"asimov": snapshot}


def test_terminal_health_keeps_drops_visible_without_a_following_sample(projection, tmp_path):
    """AC-005.2: recorder loss cannot depend on a later successful event."""
    write(tmp_path, [start(), event(2, data=state()), event(3, "run.ended")])
    (tmp_path / (RUN + ".status.json")).write_text(json.dumps({
        "run_id": RUN, "active": False, "queued": 0, "written": 3,
        "dropped_total": 19, "errors": 2, "incomplete": True, "flushed": True}))
    projection.ingest(tmp_path)
    run = projection.snapshot()["runs"][0]
    assert run["dropped_total"] == 19
    assert run["health"]["incomplete"] is True
    assert run["health"]["errors"] == 2
    assert run["status"] == "ended"
    assert projection.ingest(tmp_path) == 0
    assert projection.runs()["runs"][0]["dropped_total"] == 19


def test_real_public_writer_journal_can_be_ingested(projection, tmp_path):
    """Cross-module acceptance catches a producer/consumer schema mismatch."""
    from clawmetry.asimov.journal import JournalWriter

    writer = JournalWriter("lab-asimov", "asimov_sdk", directory=tmp_path)
    assert writer.emit("observation", state())
    writer.close()
    assert projection.ingest(tmp_path) >= 2
    run = projection.runs()["runs"][0]
    assert run["run_id"] == writer.run_id
    assert run["observation"] == state()
    assert run["status"] == "ended"


@pytest.mark.parametrize("age_s,expected", [(0.1, "live"), (10, "stale")])
def test_live_status_requires_fresh_actual_observation(projection, tmp_path, monkeypatch, age_s, expected):
    import clawmetry.asimov.store as module

    monkeypatch.setattr(module.time, "time_ns", lambda: STAMP + int(age_s * 1e9))
    write(tmp_path, [start(), event(2, data=state())])
    projection.ingest(tmp_path)
    assert projection.runs()["runs"][0]["status"] == expected


def test_telemetry_loss_is_not_hidden_by_recent_observation(projection, tmp_path, monkeypatch):
    import clawmetry.asimov.store as module

    monkeypatch.setattr(module.time, "time_ns", lambda: STAMP + 1000)
    write(tmp_path, [start(), event(2, data=state()), event(3, "telemetry.lost")])
    projection.ingest(tmp_path)
    assert projection.runs()["runs"][0]["status"] == "disconnected"


def test_rejected_input_is_visible_in_runs_and_encrypted_snapshot(projection, tmp_path):
    """AC-004.2: a skipped record is not silently presented as complete data."""
    path = write(tmp_path, [start(), event(2, data=state())])
    with path.open("ab") as stream:
        stream.write(b"broken-record\n")
        conflicting = event(2, data={"mode": "conflicting duplicate"})
        stream.write((json.dumps(conflicting) + "\n").encode())
    projection.ingest(tmp_path)
    for response in (projection.runs(), projection.snapshot()):
        health = response["runs"][0].get("health") or {}
        assert health.get("invalid_records") == 2
        assert health.get("incomplete") is True


def test_total_line_budget_applies_across_files_without_starvation(projection, tmp_path):
    """The bounded daemon pass cannot multiply its budget by active robots."""
    for number in range(1, 19):
        run_id = format(number, "032x")
        write(tmp_path, [start(run_id=run_id)], name=run_id + ".jsonl")
    for _ in range(36):
        assert projection.ingest(tmp_path, max_lines=1) <= 1
    assert len(projection.runs(limit=100)["runs"]) == 18


def test_total_byte_budget_applies_across_files(projection, db, tmp_path):
    for number in range(1, 9):
        run_id = format(number, "032x")
        write(tmp_path, [start(run_id=run_id), event(2, run_id=run_id,
              data={"payload": "x" * 50_000})], name=run_id + ".jsonl")
    budget = MAX_LINE * 2
    projection.ingest(tmp_path, max_lines=1000, max_bytes=budget)
    consumed = db._fetch("SELECT coalesce(sum(byte_offset),0) FROM asimov_cursors", [])[0][0]
    # One final bounded readline may cross the remaining-byte boundary.
    assert consumed <= budget + MAX_LINE


def test_rotated_segment_waits_for_late_header_instead_of_losing_evidence(projection, tmp_path):
    """A copied rotated segment may arrive before its run metadata file."""
    write(tmp_path, [event(2, data=state())], name=RUN + ".00000001.jsonl")
    assert projection.ingest(tmp_path) == 0
    write(tmp_path, [start()])
    projection.ingest(tmp_path)
    projection.ingest(tmp_path)
    assert projection.runs()["runs"][0]["event_count"] == 2
    assert projection.runs()["runs"][0]["observation"] == state()


@pytest.mark.parametrize("method,kwargs", [
    ("query_asimov_runs", {}),
    ("query_asimov_events", {"run_id": RUN}),
])
def test_internal_asimov_reads_require_daemon_auth_on_shared_dashboard_blueprint(
        projection, db, tmp_path, monkeypatch, method, kwargs):
    """The internal RPC path cannot bypass the public robot API's auth."""
    from flask import Flask

    from routes import local_query

    write(tmp_path, [start(), event(2, data=state())])
    projection.ingest(tmp_path)
    monkeypatch.setattr(local_query, "_store", lambda: db)
    app = Flask(__name__)
    app.register_blueprint(local_query.bp_local_query)
    response = app.test_client().post("/__local_query__/" + method, json={"kwargs": kwargs})
    assert response.status_code == 401


def test_snapshot_size_cap_cursor_does_not_skip_runs(projection, tmp_path):
    expected = set()
    for number in range(1, 10):
        run_id = format(number, "032x")
        expected.add(run_id)
        write(tmp_path, [start(run_id=run_id), event(2, run_id=run_id,
              data={"joints": state()["joints"], "extra_evidence": "x" * 20_000})],
              name=run_id + ".jsonl")
    projection.ingest(tmp_path)
    snapshot = projection.snapshot()
    first = {run["run_id"] for run in snapshot["runs"]}
    assert len(json.dumps(snapshot, separators=(",", ":")).encode()) <= 64 * 1024
    assert first
    assert snapshot["has_more"] is True
    assert snapshot["next_cursor"] is not None
    older = projection.runs(limit=100, **snapshot["next_cursor"])
    assert first | {run["run_id"] for run in older["runs"]} == expected


def test_deeply_nested_corrupt_row_does_not_poison_following_evidence(projection, tmp_path):
    """A bounded malformed JSON row must advance the cursor, not wedge all ingestion."""
    path = write(tmp_path, [start()])
    with path.open("a") as output:
        output.write('{"data":' + '[' * 12000 + '0' + ']' * 12000 + '}\n')
        output.write(json.dumps(event(2, data=state())) + '\n')
    assert projection.ingest(tmp_path) == 2
    run = projection.runs()["runs"][0]
    assert run["observation"] == state()
    assert run["health"]["invalid_records"] == 1
    assert run["health"]["incomplete"] is True


def test_snapshot_keeps_latest_24_command_and_lifecycle_events(projection, tmp_path):
    """Summary history is bounded and must state when earlier evidence is omitted."""
    events = [start()]
    sequence = 2
    expected = [events[0]]
    for number in range(35):
        command = event(sequence, "command.requested", data={"name": "set_velocity", "call_id": str(number), "outcome": "unknown"})
        events.extend([command, event(sequence + 1, "observation", data=state())])
        expected.append(command)
        sequence += 2
    ended = event(sequence, "run.ended", data={"outcome": "unknown"})
    events.append(ended)
    expected.append(ended)
    write(tmp_path, events)
    projection.ingest(tmp_path)
    snapshot = projection.snapshot()
    actual = snapshot["events"][RUN]
    assert [row["sequence"] for row in actual] == [row["sequence"] for row in expected[-24:]]
    assert all(row["kind"] != "observation" for row in actual)
    assert snapshot["trace_window"][RUN] == {"scope": "recent", "retained": 24, "truncated": True}
    assert len(json.dumps(snapshot, separators=(",", ":")).encode()) <= 64 * 1024


def test_optional_raw_telemetry_cannot_displace_snapshot_command_evidence(projection, tmp_path):
    """Raw feedback has its own local history and must not fill the command window."""
    events = [start(), event(2, "command.requested", data={"name": "stand", "outcome": "unknown"})]
    events += [event(sequence, "observation.raw", data=state()) for sequence in range(3, 35)]
    write(tmp_path, events)
    projection.ingest(tmp_path)
    snapshot = projection.snapshot()
    kinds = [row["kind"] for row in snapshot["events"][RUN]]
    assert "command.requested" in kinds
    assert "observation.raw" not in kinds


def test_snapshot_caps_large_metadata_and_command_details_across_runs(projection, tmp_path):
    for number in range(1, 10):
        run_id = format(number, "032x")
        header = start(run_id=run_id)
        header["data"]["source_metadata"] = "x" * 12_000
        write(tmp_path, [header, event(2, run_id=run_id, data=state()),
                        event(3, "command.requested", run_id=run_id,
                              data={"name": "trajectory", "detail": "x" * 40_000, "outcome": "unknown"})],
              name=run_id + ".jsonl")
    projection.ingest(tmp_path)
    snapshot = projection.snapshot()
    assert len(json.dumps(snapshot, separators=(",", ":")).encode()) <= 64 * 1024
    assert snapshot["runs"]
    assert snapshot["has_more"] is True
    assert snapshot["next_cursor"]["before_run_id"] == snapshot["runs"][-1]["run_id"]
    assert any(window["truncated"] for window in snapshot["trace_window"].values())


def test_unchanged_recorder_sidecar_is_not_reparsed_or_rewritten(projection, db, tmp_path, monkeypatch):
    """The daemon's one-second cadence must reuse unchanged recorder health."""
    from pathlib import Path

    write(tmp_path, [start(), event(2, data=state())])
    sidecar = tmp_path / (RUN + ".status.json")
    sidecar.write_text(json.dumps({"run_id": RUN, "active": False, "incomplete": False,
                                  "flushed": True, "queued": 0, "written": 2,
                                  "dropped_total": 0, "errors": 0}))
    original_read = Path.read_text
    reads, updates = [], []

    def read(path, *args, **kwargs):
        if path == sidecar:
            reads.append(path)
        return original_read(path, *args, **kwargs)

    class ConnectionSpy:
        def __init__(self, target):
            self.target = target

        def execute(self, sql, *args, **kwargs):
            if "UPDATE asimov_runs SET health_json" in sql:
                updates.append(sql)
            return self.target.execute(sql, *args, **kwargs)

        def __getattr__(self, name):
            return getattr(self.target, name)

    monkeypatch.setattr(Path, "read_text", read)
    monkeypatch.setattr(db, "_conn", ConnectionSpy(db._conn))
    projection.ingest(tmp_path)
    assert len(reads) == len(updates) == 1
    projection.ingest(tmp_path)
    projection.ingest(tmp_path)
    assert len(reads) == len(updates) == 1


def test_encrypted_snapshot_reaches_browser_renderer_without_robot_file_reads(projection, tmp_path):
    """The decrypted snapshot supplies the actual browser renderer without API reads.

    AC-ASIMOV-006.3
    This is a software contract test. Served hosted authentication and hardware
    validation remain separate delivery gates.
    """
    import shutil
    import subprocess
    from pathlib import Path

    from clawmetry.sync import decrypt_payload, encrypt_payload

    node = shutil.which("node")
    if not node:
        pytest.skip("The encrypted browser contract needs Node.js")
    write(tmp_path, [start(source="asimov_recording"), event(2, data=state()),
                    event(3, "command.sent", data={"name": "stand", "outcome": "unknown"})])
    projection.ingest(tmp_path)
    key = base64.b64encode(os.urandom(32)).decode()
    envelope = encrypt_payload({"asimov": projection.snapshot()}, key)
    decrypted = decrypt_payload(envelope, key)
    snapshot_file = tmp_path / "decrypted-asimov.json"
    snapshot_file.write_text(json.dumps(decrypted["asimov"]))
    script = Path(__file__).with_name("test_asimov_ui.js")
    completed = subprocess.run([node, str(script), str(snapshot_file)], capture_output=True,
                               text=True, timeout=15, check=False)
    assert completed.returncode == 0, completed.stderr
    assert "Persisted encrypted snapshot rendered without local API reads" in completed.stdout
