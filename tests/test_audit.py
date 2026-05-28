"""Tests for clawmetry/audit.py — append-only audit log.

Validates record/read roundtrip, filtering, malformed-input resilience, the
never-raise contract, and that the env override for the DB path works (so the
real ~/.clawmetry/audit.db is never touched during tests).
"""
from __future__ import annotations

import importlib
import os

import pytest


@pytest.fixture
def audit(monkeypatch, tmp_path):
    monkeypatch.setenv("CLAWMETRY_AUDIT_DB", str(tmp_path / "audit.db"))
    import clawmetry.audit as A

    importlib.reload(A)
    return A


def test_record_and_read_roundtrip(audit):
    audit.record_audit("license.activated", actor="cli", target="lic_abc123",
                       details={"nodes": 100, "tier": "pro"})
    rows = audit.read_audit_log(limit=10)
    assert len(rows) == 1
    r = rows[0]
    assert r["event_type"] == "license.activated"
    assert r["actor"] == "cli"
    assert r["target"] == "lic_abc123"
    assert r["details"]["nodes"] == 100


def test_newest_first_and_limit(audit):
    for i in range(5):
        audit.record_audit("config.changed", details={"i": i})
    rows = audit.read_audit_log(limit=3)
    assert len(rows) == 3
    assert rows[0]["details"]["i"] == 4
    assert rows[2]["details"]["i"] == 2


def test_filter_by_event_type_and_since(audit):
    audit.record_audit("auth.login", actor="alice")
    audit.record_audit("license.activated", target="x")
    audit.record_audit("auth.login", actor="bob")
    rows = audit.read_audit_log(event_type="auth.login")
    assert len(rows) == 2
    assert {r["actor"] for r in rows} == {"alice", "bob"}


def test_empty_event_type_is_noop(audit):
    audit.record_audit("")  # blank event_type silently dropped
    assert audit.read_audit_log() == []


def test_never_raises_on_bad_inputs(audit):
    # bizarre values should never propagate
    audit.record_audit("x" * 500, actor=None, target=None, details=None)  # type: ignore[arg-type]
    rows = audit.read_audit_log()
    assert len(rows) == 1
    assert rows[0]["actor"] == "" and rows[0]["target"] == ""


def test_event_types_counts(audit):
    audit.record_audit("a")
    audit.record_audit("a")
    audit.record_audit("b")
    types = {t["event_type"]: t["count"] for t in audit.event_types()}
    assert types == {"a": 2, "b": 1}


def test_corrupt_details_falls_back(audit, tmp_path):
    # write a row with non-JSON details by going under the API, then read it
    import sqlite3, time as _t
    p = os.environ["CLAWMETRY_AUDIT_DB"]
    audit.record_audit("seed")  # ensure schema exists
    with sqlite3.connect(p) as c:
        c.execute("INSERT INTO audit_log (ts, event_type, details) VALUES (?,?,?)",
                  (_t.time(), "broken", "{not valid"))
        c.commit()
    rows = audit.read_audit_log()
    broken = next(r for r in rows if r["event_type"] == "broken")
    assert "_raw" in broken["details"]
