"""Bounded, scoped investigation over persisted evidence.

AC-OBS-INV-002.1: exact evidence survives moving previews and missing retention.
AC-OBS-INV-002.2: execution outcome and cost remain independent from findings.
AC-OBS-INV-002.3: keyset pages preserve scope and expose coverage honestly.
"""
import time

from tests import test_incident_lifecycle as lifecycle

store = lifecycle.store
server = lifecycle.server
finding = lifecycle.finding
observe = lifecycle.observe


def events(store, count=12, node="node-a", runtime="codex", sid="codex:session"):
    rows = [{"id": f"{node}-{runtime}-{i}", "node_id": node, "agent_type": runtime,
             "session_id": sid, "event_type": "tool_result",
             "ts": "2026-10-02T10:00:00Z", "data": {"tool": "Bash", "is_error": True}}
            for i in range(count)]
    store.ingest_many(rows)
    store._flush_now()
    return rows


def read(store, **kwargs):
    return store.query_investigation(session_id="codex:session", runtime="codex",
                                    node_id="node-a", **kwargs)


def test_pagination_beyond_preview_and_same_timestamp_has_no_gaps(store):
    source = events(store)
    events(store, node="node-b", count=50)
    found, cursor = [], None
    for _ in range(8):
        result = read(store, limit=3, cursor=cursor)
        found.extend(row["id"] for row in result["rows"])
        assert result["coverage"]["node_reachable"] is True
        assert result["scope"] == {"node_id": "node-a", "runtime": "codex", "session_id": "codex:session"}
        cursor = result["coverage"]["next_cursor"]
        if not cursor:
            break
    assert len(found) == len(set(found)) == len(source)
    assert set(found) == {e["id"] for e in source}


def test_evidence_fetch_is_independent_of_recent_page_and_never_crosses_node(store):
    source = events(store)
    ids = sorted(e["id"] for e in source)
    episode = observe(store, finding(ids[0], at=time.time() * 1000,
                      evidence_refs=[{"event_id": ids[0]}, {"event_id": "pruned"},
                                     {"event_id": "node-b-codex-0"}]))
    events(store, count=1, node="node-b")
    result = read(store, incident_id=episode["incident_id"], limit=1)
    assert ids[0] not in [e["id"] for e in result["rows"]]
    assert [e["id"] for e in result["evidence_rows"]] == [ids[0]]
    assert set(result["coverage"]["missing_event_ids"]) == {"pruned", "node-b-codex-0"}
    assert result["coverage"]["evidence_complete"] is False
    assert result["incident"]["cost_provenance"] == "unknown"
    assert result["incident"]["spend_at_risk_usd"] is None
    assert result["execution"]["status"] == "unknown"


def test_cursor_is_bound_to_scope_and_rejects_malformed_values(store):
    events(store)
    cursor = read(store, limit=2)["coverage"]["next_cursor"]
    other = store.query_investigation(session_id="codex:session", runtime="codex",
                                      node_id="node-b", cursor=cursor)
    assert other["resync_required"] is True
    assert other["rows"] == []
    assert read(store, cursor="not-json")["resync_required"] is True


def test_ended_execution_does_not_claim_finding_recovery(store):
    episode = observe(store, finding(at=time.time() * 1000), now=time.time() * 1000)
    store.ingest_session({"session_id": "codex:session", "node_id": "node-a",
                          "agent_type": "codex", "status": "completed",
                          "ended_at": "2026-10-02T10:01:00Z"})
    result = read(store, incident_id=episode["incident_id"])
    assert result["execution"]["status"] == "completed"
    assert result["incident"]["state"] == "active"
    assert result["incident"]["recovered_at"] is None


def test_incident_identity_cannot_open_in_another_scope(store):
    episode = observe(store, node="node-b")
    result = read(store, incident_id=episode["incident_id"])
    assert result["incident"] is None
    assert result["coverage"]["incident_available"] is False
    assert result["evidence_rows"] == []


def test_old_active_evidence_is_labelled_stale_even_if_detector_is_disabled(store):
    episode = observe(store, now=time.time() * 1000)
    result = read(store, incident_id=episode["incident_id"])
    assert result["incident"]["state"] == "stale"
    assert result["incident"]["recovered_at"] is None
