"""Recorder bounds and durable evidence ordering without a robot connection."""

import json
import os
import sys
import threading
import time

import pytest

from clawmetry.asimov.journal import MAX_EVENT_BYTES, JournalWriter


@pytest.fixture(scope="session", autouse=True)
def server():
    """Recorder tests need no dashboard or ambient credentials."""
    yield None


def rows(writer):
    return [json.loads(line) for line in writer.path.read_text().splitlines()]


def test_nanoseconds_order_and_no_silent_disk_overflow(tmp_path):
    """Recorder persistence uses the declared event schema and reports storage loss.

    AC-ASIMOV-005.2: disk overflow is bounded and visible in final status.
    AC-ASIMOV-005.4: sequence, robot identity and nanosecond strings survive writing.
    """
    writer = JournalWriter(
        "robot-a",
        "asimov_sdk",
        directory=tmp_path,
        max_bytes=4096,
        directory_bytes=8192,
    )
    for _ in range(50):
        writer.emit("observation", {"payload": "x" * 400}, block=True)
    status = writer.close()
    events = rows(writer)
    assert events[0]["kind"] == "run.started"
    assert events[-1]["kind"] == "run.ended"
    assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
    assert all(e["robot_id"] == "robot-a" for e in events)
    assert all(
        isinstance(e["wall_time_ns"], str) and int(e["wall_time_ns"]) > 10**18
        for e in events
    )
    assert writer.path.stat().st_size <= 4096
    assert status["dropped_total"] > 0 and status["incomplete"]
    assert (
        json.loads(writer.status_path.read_text())["dropped_total"]
        == status["dropped_total"]
    )


def test_queue_drops_without_blocking_the_sdk_thread(tmp_path, monkeypatch):
    """An intentionally stalled writer cannot block the SDK producer.

    AC-ASIMOV-005.1: a bounded nonblocking queue separates callbacks from disk work.
    AC-ASIMOV-005.2: queue overflow increments the durable loss count.
    """
    entered, release = threading.Event(), threading.Event()
    original = JournalWriter._write

    def blocked(self, item, terminal=False):
        if item[0] == "run.started":
            entered.set()
            release.wait(3)
        return original(self, item, terminal)

    monkeypatch.setattr(JournalWriter, "_write", blocked)
    writer = JournalWriter("robot", "asimov_sdk", directory=tmp_path, queue_size=1)
    assert entered.wait(2)
    assert writer.emit("observation", {"joints": []})
    started = time.monotonic()
    assert writer.emit("observation", {"joints": []}) is False
    assert time.monotonic() - started < 0.2
    release.set()
    assert writer.close()["dropped_total"] == 1


def test_invalid_payloads_do_not_break_following_evidence(tmp_path):
    """Rejected oversized/nonfinite evidence does not prevent a later valid row.

    AC-ASIMOV-005.2: rejected evidence remains visible as an incomplete run.
    """
    with JournalWriter("robot", "asimov_recording", directory=tmp_path) as writer:
        assert not writer.emit("observation", {"huge": "x" * MAX_EVENT_BYTES})
        assert not writer.emit("observation", {"invalid": float("nan")})
        assert writer.emit("observation", {"unknown": None})
    events = rows(writer)
    assert events[1]["data"]["unknown"] is None
    assert len(events) == 3
    assert writer.status()["incomplete"]
    with pytest.raises(ValueError, match="200"):
        JournalWriter("x" * 201, "asimov_sdk", directory=tmp_path)


def test_existing_run_cannot_be_overwritten(tmp_path):
    """Immutable journal identity cannot be overwritten with another robot.

    AC-ASIMOV-004.3: an existing run path fails visibly and preserves its bytes.
    """
    writer = JournalWriter("robot", "asimov_sdk", directory=tmp_path)
    writer.close()
    original = writer.path.read_bytes()
    with pytest.raises(FileExistsError):
        JournalWriter("other", "asimov_sdk", directory=tmp_path, run_id=writer.run_id)
    assert writer.path.read_bytes() == original


def test_an_unwritten_header_cannot_produce_an_unattributed_stream(tmp_path):
    writer = JournalWriter(
        "robot",
        "asimov_sdk",
        directory=tmp_path,
        metadata={"too_large": "x" * MAX_EVENT_BYTES},
    )
    writer.emit("observation", {"mode": "STAND"})
    status = writer.close()
    assert writer.path.read_bytes() == b""
    assert status["incomplete"] and status["written"] == 0


def test_actual_pro_parser_and_store_accept_public_asimov_evidence(
    tmp_path, monkeypatch
):
    """Optional compatibility check against the separately installed real Pro reader.

    AC-ASIMOV-006.2: real Pro ingestion reads Asimov evidence and recorder health.
    AC-ASIMOV-005.4: the existing robotics parser accepts the emitted public schema.
    """
    from clawmetry import local_store

    monkeypatch.setattr(local_store, "DB_PATH", tmp_path / "contract.duckdb")
    monkeypatch.setenv(
        "CLAWMETRY_ROBOTICS_SETTINGS_PATH", str(tmp_path / "settings.json")
    )
    store = local_store.LocalStore()
    try:
        # CI can point at an installed published Pro package without vendoring
        # private code. Append so the current interpreter keeps its own binary deps.
        source = os.environ.get("CLAWMETRY_ASIMOV_PRO_SOURCE")
        if source:
            monkeypatch.setattr(sys, "path", sys.path + [source])
            from pathlib import Path

            import clawmetry_pro

            monkeypatch.setattr(
                clawmetry_pro,
                "__path__",
                list(clawmetry_pro.__path__) + [str(Path(source) / "clawmetry_pro")],
            )
        pro = pytest.importorskip("clawmetry_pro.robotics.store")
        directory = tmp_path / "journal"
        with JournalWriter(
            "contract-robot", "asimov_sdk", directory=directory
        ) as writer:
            writer.emit(
                "observation",
                {
                    "mode": "STAND",
                    "joints": [
                        {
                            "name": "L_Knee",
                            "position_rad": 0.5,
                            "velocity_rad_s": None,
                            "current_amp": 2.0,
                            "temperature_c": None,
                        }
                    ],
                    "observation": {"L_Knee.pos": 0.5},
                },
            )
            writer._loss("Unit-test recorder loss is explicit")
        events = rows(writer)
        assert all(pro._validate(event, writer.run_id) == event for event in events)
        reader = pro.RoboticsStore(store)
        result = reader.ingest(directory)
        assert result["invalid"] == 0 and result["ingested"] == len(events)
        projected = next(
            run for run in reader.runs()["runs"] if run["run_id"] == writer.run_id
        )
        assert projected["observation"]["data"]["joints"][0]["current_amp"] == 2.0
        assert projected["start"]["data"]["source_kind"] == "asimov_sdk"
        assert projected["dropped_count"] == writer.status()["dropped_total"]
        assert projected["recorder_error"] == "Unit-test recorder loss is explicit"
        assert projected["recorder_flushed"] is True
        assert projected["guard"]["evaluation_enabled"] is False
        assert reader.ingest(directory)["ingested"] == 0
    finally:
        store.stop()
