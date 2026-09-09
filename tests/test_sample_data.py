"""Sample-mode guards (#5715).

The sample exists so a fresh install is never an empty product. That only
holds if three things stay true, and each one has failed at least once while
this was being built:

1. The "stuck" session must trip a **real** detector. Nothing in the fixture
   declares it stuck; it is a tool stream that genuinely loops. If a threshold
   moves and it stops firing, the demo silently stops demonstrating anything —
   so that is a test failure, not a quiet regression.
2. The healthy long run must come back **clean**. It first shipped tripping
   ``rate_limited``, because the session was *about* rate limiting and the
   detector scans reply text for "rate limit". A reference "this is fine"
   session carrying an incident badge teaches the exact opposite lesson.
3. Sample mode must never point at the real store, and must never proxy to a
   running daemon — that would serve the user's own sessions under a banner
   claiming they are synthetic.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from clawmetry import detectors, sample_data  # noqa: E402


def _events_for(session_id, events):
    """Store order is newest-first; build_dataset yields oldest-first."""
    return list(reversed([e for e in events if e["session_id"] == session_id]))


@pytest.fixture(scope="module")
def dataset():
    return sample_data.build_dataset()


def test_dataset_is_wellformed(dataset) -> None:
    sessions, events = dataset
    assert len(sessions) == 3
    assert len(events) > 30
    ids = {s["session_id"] for s in sessions}
    assert {e["session_id"] for e in events} == ids
    # Ids must be stable, or a rebuild duplicates instead of upserting.
    again_s, again_e = sample_data.build_dataset()
    assert [e["id"] for e in events] == [e["id"] for e in again_e]
    # Every event carries what local_store.ingest() requires.
    for e in events:
        for key in ("id", "node_id", "event_type", "ts"):
            assert e.get(key), f"event missing {key}: {e}"


def test_every_row_is_labelled_as_sample(dataset) -> None:
    sessions, events = dataset
    for s in sessions:
        assert s["title"].startswith(sample_data.SAMPLE_TITLE_PREFIX), s["title"]
        assert s["node_id"] == sample_data.SAMPLE_NODE_ID
    for e in events:
        assert e["node_id"] == sample_data.SAMPLE_NODE_ID


def test_stuck_session_trips_a_real_detector(dataset) -> None:
    """Guard 1. The incident is earned by the tool stream, not annotated."""
    sessions, events = dataset
    stuck = next(s for s in sessions if s["session_id"] == "sample-stuck-0001")
    incidents = detectors.run_all(
        _events_for(stuck["session_id"], events), stuck["session_id"], "openclaw",
        facts={"cost_usd": stuck["cost_usd"], "session_seconds": 5400},
    )
    kinds = {i.get("kind") for i in incidents}
    assert "stuck_loop" in kinds, (
        "the sample's looping session no longer trips stuck_loop -- either the "
        f"thresholds moved or the fixture drifted. Fired: {sorted(kinds)}"
    )


def test_healthy_and_short_sessions_are_clean(dataset) -> None:
    """Guard 2. The contrast case is the whole point of shipping three."""
    sessions, events = dataset
    for sid in ("sample-healthy-0002", "sample-quick-0003"):
        s = next(x for x in sessions if x["session_id"] == sid)
        incidents = detectors.run_all(
            _events_for(sid, events), sid, "openclaw",
            facts={"cost_usd": s["cost_usd"], "session_seconds": 9000},
        )
        assert not incidents, (
            f"{sid} is the 'this run is fine' reference and must carry no "
            f"incident, but fired: {[i.get('kind') for i in incidents]}"
        )


def test_healthy_session_is_a_long_run(dataset) -> None:
    """'Many tool calls' must not be what distinguishes the two sessions, or
    the demo teaches that busy == broken."""
    sessions, events = dataset
    healthy = _events_for("sample-healthy-0002", events)
    stuck = _events_for("sample-stuck-0001", events)
    n_healthy = len([e for e in healthy if e["event_type"] == "tool_call"])
    n_stuck = len([e for e in stuck if e["event_type"] == "tool_call"])
    assert n_healthy >= 8, n_healthy
    assert n_stuck >= 8, n_stuck


def test_one_tool_call_shape_per_event(dataset) -> None:
    """A row carrying BOTH ``tool_name`` and a ``tool_calls`` array is counted
    twice by the normaliser, with different argument hashes -- which is what
    stopped stuck_loop from firing the first time round."""
    _sessions, events = dataset
    for e in events:
        if e["event_type"] != "tool_call":
            continue
        data = e["data"]
        assert not (data.get("tool_name") and data.get("tool_calls")), (
            f"event {e['id']} carries two tool-call shapes"
        )
        steps = detectors.normalize_events([e])
        calls = [s for s in steps if s["kind"] == "tool_call" and s["tool"]]
        assert len(calls) == 1, f"event {e['id']} normalised to {len(calls)} calls"


def test_sample_store_is_not_the_real_store() -> None:
    """Guard 3a. A stray --sample must not be able to reach real data."""
    from clawmetry import local_store
    sample_path = sample_data.sample_db_path()
    assert sample_path != local_store.DB_PATH or "sample" in str(local_store.DB_PATH)
    assert "sample" in str(sample_path)
    assert sample_path.name != "clawmetry.duckdb"


def test_is_sample_mode_reads_the_environment(monkeypatch) -> None:
    monkeypatch.delenv("CLAWMETRY_SAMPLE", raising=False)
    assert sample_data.is_sample_mode() is False
    for truthy in ("1", "true", "TRUE", "yes", "on"):
        monkeypatch.setenv("CLAWMETRY_SAMPLE", truthy)
        assert sample_data.is_sample_mode() is True, truthy
    monkeypatch.setenv("CLAWMETRY_SAMPLE", "0")
    assert sample_data.is_sample_mode() is False


def test_enable_sample_mode_points_the_store_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAWMETRY_SAMPLE", raising=False)
    monkeypatch.delenv("CLAWMETRY_LOCAL_STORE_PATH", raising=False)
    import importlib
    importlib.reload(sample_data)
    path = sample_data.enable_sample_mode()
    assert os.environ["CLAWMETRY_SAMPLE"] == "1"
    assert os.environ["CLAWMETRY_LOCAL_STORE_PATH"] == str(path)
    assert path.parent.is_dir()


def test_content_is_synthetic(dataset) -> None:
    """No real path, host or user should be reachable from the fixture."""
    _sessions, events = dataset
    home = os.path.expanduser("~")
    blob = repr(events)
    assert home not in blob
    assert "/Users/" not in blob
    assert "/home/" not in blob
