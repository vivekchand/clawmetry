"""Tests for the numbat NDJSON mapper (clawmetry/numbat_ingest.py) and its
store round-trip.

numbat (Perplexity's agent-EDR) emits NDJSON findings / enforcement
decisions; ClawMetry ingests them via a daemon file tail (sync_numbat_events)
and POST /api/numbat/ingest. Both share one mapper — these tests pin its
contract: record routing, id determinism (dedupe on replay), canonical
session-id prefixing, schema-version pinning, and the security/guardrail
table round-trip.
"""

from __future__ import annotations

import importlib
import json

import pytest

from clawmetry import numbat_ingest as ni


def _finding(**over):
    rec = {
        "schema_version": "0.2.0",
        "record_type": "finding",
        "run_id": "run-20260801T000000.000000000-abcdef0123456789",
        "finding_id": "fnd-0123456789abcdef01234567",
        "detected_at": "2026-08-01T10:00:05Z",
        "timestamp": "2026-08-01T09:59:58.123Z",
        "rule_id": "exec.agent_runtime_bypass_flags",
        "rule_version": "1.2",
        "severity": "high",
        "title": "Agent launched with permission checks bypassed",
        "source_agent": "claude-code",
        "source_type": "hook",
        "session_id": "11111111-2222-3333-4444-555555555555",
        "observed_command": "claude --dangerously-skip-permissions",
        "cited_event_ids": ["evt-1"],
    }
    rec.update(over)
    return rec


def _enforcement(**over):
    rec = {
        "schema_version": "0.2.0",
        "record_type": "enforcement",
        "decision_id": "enf-0123456789abcdef01234567",
        "decision": "deny",
        "mode": "enforce",
        "reason": "enforce_rule_match",
        "deny_rule_id": "exec.reverse_shell",
        "rule_ids": ["exec.reverse_shell"],
        "source_agent": "codex",
        "session_id": "sess-9",
        "timestamp": "2026-08-01T11:00:00Z",
    }
    rec.update(over)
    return rec


def _ndjson(*recs):
    return "\n".join(json.dumps(r) for r in recs) + "\n"


# ── parse_records ──────────────────────────────────────────────────────────

def test_parse_skips_blank_and_malformed_lines():
    text = "\n" + json.dumps(_finding()) + "\nnot json\n[1,2]\n"
    records, bad = ni.parse_records(text)
    assert len(records) == 1
    assert bad == 2  # "not json" + non-dict JSON


# ── map_records routing ────────────────────────────────────────────────────

def test_finding_routes_to_security_and_shadow():
    mapped = ni.map_records([_finding()], node_id="node-1")
    assert len(mapped["security_events"]) == 1
    assert len(mapped["shadow_events"]) == 1
    assert mapped["guardrail_events"] == []

    sec = mapped["security_events"][0]
    assert sec["id"] == "numbat_fnd-0123456789abcdef01234567"
    assert sec["type"] == "numbat_finding"
    assert sec["severity"] == "high"
    assert sec["rule_id"] == "exec.agent_runtime_bypass_flags"
    # event's own timestamp preferred over detected_at; normalized to seconds
    assert sec["ts"] == "2026-08-01T09:59:58"
    # canonical session id: kebab source_agent → snake runtime prefix
    assert sec["session_id"] == "claude_code:11111111-2222-3333-4444-555555555555"
    assert sec["snippet"] == "claude --dangerously-skip-permissions"

    shadow = mapped["shadow_events"][0]
    assert shadow["event_type"] == "numbat_finding"
    assert shadow["node_id"] == "node-1"
    assert shadow["agent_type"] == "claude_code"
    data = json.loads(shadow["data"])
    assert data["rule_id"] == "exec.agent_runtime_bypass_flags"


def test_enforcement_routes_to_guardrail():
    mapped = ni.map_records([_enforcement()], node_id="node-1")
    assert len(mapped["guardrail_events"]) == 1
    gr = mapped["guardrail_events"][0]
    assert gr["id"] == "numbat_enf-0123456789abcdef01234567"
    assert gr["rule_name"] == "exec.reverse_shell"
    assert gr["verdict"] == "deny"
    assert gr["action"] == "blocked"
    assert gr["session_id"] == "codex:sess-9"


def test_no_override_enforcement_is_monitored_not_blocked():
    rec = _enforcement(
        decision="no_override", mode="monitor", reason="monitor_mode",
        deny_rule_id=None,
    )
    gr = ni.map_records([rec])["guardrail_events"][0]
    assert gr["verdict"] == "no_override"
    assert gr["action"] == "monitor_mode"
    assert gr["rule_name"] == "exec.reverse_shell"  # falls back to rule_ids[0]


def test_event_records_skipped_by_design():
    ev = {"schema_version": "0.2.0", "record_type": "event", "event_id": "evt-1"}
    mapped = ni.map_records([ev])
    assert mapped["skipped_events"] == 1
    assert mapped["security_events"] == []


def test_unknown_schema_version_counted_not_ingested():
    mapped = ni.map_records([_finding(schema_version="0.3.0")])
    assert mapped["skipped_schema"] == 1
    assert mapped["security_events"] == []


def test_indicator_and_scan_summary_counted_as_other():
    recs = [
        {"schema_version": "0.2.0", "record_type": "indicator", "type": "domain"},
        {"schema_version": "0.2.0", "record_type": "scan_summary", "status": "complete"},
    ]
    mapped = ni.map_records(recs)
    assert mapped["skipped_other"] == 2


def test_ids_deterministic_across_replays():
    """numbat duplicates batches on retry; the mapped ids must be stable so
    the store's upsert dedupes replays."""
    a = ni.map_records([_finding()], node_id="n")
    b = ni.map_records([_finding()], node_id="n")
    assert a["security_events"][0]["id"] == b["security_events"][0]["id"]
    assert a["shadow_events"][0]["id"] == b["shadow_events"][0]["id"]


def test_no_node_id_omits_shadow_rows():
    mapped = ni.map_records([_finding()])
    assert mapped["shadow_events"] == []
    assert len(mapped["security_events"]) == 1  # finding itself still ingested


def test_unknown_agent_snake_cased_for_attribution():
    rec = _finding(source_agent="kimi-code", session_id="s1")
    sec = ni.map_records([rec])["security_events"][0]
    assert sec["session_id"] == "kimi_code:s1"


def test_bad_severity_normalized_to_info():
    sec = ni.map_records([_finding(severity="apocalyptic")])["security_events"][0]
    assert sec["severity"] == "info"


# ── store round-trip ───────────────────────────────────────────────────────

@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    s = ls.LocalStore()
    s.start()
    yield s
    s.stop(flush=False)


def test_round_trip_and_replay_dedupe(store):
    records, bad = ni.parse_records(_ndjson(_finding(), _enforcement()))
    assert bad == 0
    mapped = ni.map_records(records, node_id="node-1")

    # Ingest twice — replays must not create new rows.
    for _ in range(2):
        for sec in mapped["security_events"]:
            store.ingest_security_event(sec)
        for gr in mapped["guardrail_events"]:
            store.ingest_guardrail_event(gr)

    sec_rows = store.query_security_events(limit=10)
    assert len(sec_rows) == 1
    assert sec_rows[0]["rule_id"] == "exec.agent_runtime_bypass_flags"
    assert sec_rows[0]["severity"] == "high"

    gr_rows = store.query_guardrail_events(limit=10)
    assert len(gr_rows) == 1
    assert gr_rows[0]["verdict"] == "deny"
    assert gr_rows[0]["action"] == "blocked"


def test_severity_filter_serves_dashboard_query(store):
    recs = [_finding(), _finding(finding_id="fnd-low", severity="low")]
    mapped = ni.map_records(recs)
    for sec in mapped["security_events"]:
        store.ingest_security_event(sec)
    highs = store.query_security_events(severity="high", limit=10)
    assert [r["id"] for r in highs] == ["numbat_fnd-0123456789abcdef01234567"]
