"""Tests for the cron-list heartbeat-piggyback cache push (closes
clawmetry-cloud#948 — cloud Crons tab fix).

Epic #1032 removed the cloud's events-table read for the cron job list and
left a comment claiming "data now flows via heartbeat-piggyback / DuckDB
relay" — but that relay was never wired. This module covers the OSS half:
the daemon proactively pushes the user's cron job list to the cloud cache
on every heartbeat so the cloud Crons tab paints from cache (mirrors the
existing brain / memory / cron_runs cache pushes).

Coverage:
  1. Happy path: seeded ``crons`` rows -> one cache_push entry, key shape
     ``crons:{owner_hash}:{node_id}``, ttl=21600, encrypted blob (no
     plaintext leak).
  2. Empty store: no rows -> no push (cloud falls back to ``cache_pending``).
  3. Missing encryption key: never push plaintext.
  4. Round-trip: blob decrypts to ``{jobs: [...], _shape: 'crons_list'}``
     with the same per-job shape ``/api/crons`` returns.
  5. send_heartbeat wires the push into the outgoing /ingest/heartbeat body.
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


# ── Fixtures ───────────────────────────────────────────────────────────────


@pytest.fixture
def sync_with_seeded_crons(tmp_path, monkeypatch):
    """Reload `clawmetry.sync` + `clawmetry.local_store` against a fresh
    DuckDB seeded with a couple of cron jobs in the shape `sync_crons`
    writes via `ingest_cron`. Yields (sync_module, config, seeded_jobs)."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    store = ls.get_store()
    seeded = [
        {
            "cron_id":     "remind-water-drink",
            "agent_type":  "openclaw",
            "name":        "Drink water reminder",
            "schedule":    '{"kind": "interval", "interval": "2h"}',
            "enabled":     True,
            "last_run_at": "1747526400000",
            "last_status": "ok",
            "next_run_at": "1747533600000",
            "task":        "remind me to drink water",
            "lastDurationMs":      1200,
            "lastError":           "",
            "consecutiveFailures": 0,
        },
        {
            "cron_id":     "daily-standup",
            "agent_type":  "openclaw",
            "name":        "Daily standup digest",
            "schedule":    '{"kind": "at", "at": "09:00"}',
            "enabled":     False,
            "last_run_at": "1747440000000",
            "last_status": "error",
            "next_run_at": "1747526400000",
            "task":        "summarise yesterday's commits",
            "lastDurationMs":      18000,
            "lastError":           "gateway timeout",
            "consecutiveFailures": 2,
        },
    ]
    for cron in seeded:
        store.ingest_cron(cron)

    config = {
        "node_id":         "node-cron-test",
        "api_key":         "cm_cron_test_token",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config, seeded

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


@pytest.fixture
def sync_with_empty_crons(tmp_path, monkeypatch):
    """Fresh DuckDB with no crons rows — fresh-install / zero-crons case."""
    monkeypatch.setenv(
        "CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb")
    )
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")

    sys.modules.pop("clawmetry.local_store", None)
    sys.modules.pop("clawmetry.sync", None)

    import clawmetry.local_store as ls
    importlib.reload(ls)
    import clawmetry.sync as s
    importlib.reload(s)

    config = {
        "node_id":         "node-empty",
        "api_key":         "cm_cron_test_token",
        "encryption_key":  s.generate_encryption_key(),
    }

    yield s, config

    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


# ── 1. happy path: seeded rows -> one cache_push entry ─────────────────────


def test_build_crons_cache_pushes_returns_one_entry(sync_with_seeded_crons):
    s, config, seeded = sync_with_seeded_crons
    pushes = s._build_crons_cache_pushes(config)

    assert isinstance(pushes, list)
    assert len(pushes) == 1
    entry = pushes[0]

    # Key shape: crons:{owner_hash}:{node_id} — must match the cloud
    # read path (clawmetry-cloud routes/cloud.py:api_cloud_crons).
    expected_owner = s._owner_hash_for_token(config["api_key"])
    assert entry["key"] == f"crons:{expected_owner}:node-cron-test"

    assert entry["ttl_s"] == s.CRONS_CACHE_TTL_SEC == 21600

    # Encrypted blob: base64url string, plaintext markers absent.
    blob = entry["blob"]
    assert isinstance(blob, str) and len(blob) > 0
    assert "Drink water" not in blob
    assert "remind-water-drink" not in blob
    assert "gateway timeout" not in blob


# ── 2. empty store: no push ────────────────────────────────────────────────


def test_build_crons_cache_pushes_empty_store_returns_empty(sync_with_empty_crons):
    s, config = sync_with_empty_crons
    pushes = s._build_crons_cache_pushes(config)
    assert pushes == [], (
        "no crons rows -> no push so cloud can distinguish "
        "cache-pending vs zero-crons via cache miss"
    )


# ── 3. missing encryption key: never push plaintext ────────────────────────


def test_no_encryption_key_no_push(sync_with_seeded_crons):
    s, config, _ = sync_with_seeded_crons
    cfg_no_key = dict(config)
    cfg_no_key["encryption_key"] = None
    pushes = s._build_crons_cache_pushes(cfg_no_key)
    assert pushes == [], "must not push when encryption key is unset"


# ── 4. round-trip: blob decrypts to the crons_list browser shape ───────────


def test_pushed_blob_decrypts_to_crons_list_shape(sync_with_seeded_crons):
    s, config, seeded = sync_with_seeded_crons
    pushes = s._build_crons_cache_pushes(config)
    assert len(pushes) == 1

    decoded = s.decrypt_payload(pushes[0]["blob"], config["encryption_key"])
    assert isinstance(decoded, dict)
    assert decoded["_shape"] == "crons_list"
    assert decoded["_source"] == "local_store"
    assert decoded["count"] == len(seeded)

    jobs = decoded["jobs"]
    assert isinstance(jobs, list)
    assert len(jobs) == len(seeded)

    by_id = {j["id"]: j for j in jobs}
    # Both seeded jobs round-tripped with the gateway-shape fields the
    # dashboard JS reads from `snap.cronJobs`.
    water = by_id["remind-water-drink"]
    assert water["name"] == "Drink water reminder"
    assert water["enabled"] is True
    # schedule JSON-string decoded to dict, kind preserved.
    assert isinstance(water["schedule"], dict)
    assert water["schedule"]["kind"] == "interval"
    # State fields hoisted from the row columns.
    assert water["state"]["lastStatus"] == "ok"
    assert water["state"]["lastRunAtMs"] == 1747526400000
    assert water["state"]["nextRunAtMs"] == 1747533600000
    # Extras carried through from the data blob.
    assert water["state"]["lastDurationMs"] == 1200
    assert water["state"].get("consecutiveFailures", 0) == 0

    standup = by_id["daily-standup"]
    assert standup["enabled"] is False
    assert standup["state"]["lastStatus"] == "error"
    assert standup["state"]["lastError"] == "gateway timeout"
    assert standup["state"]["consecutiveFailures"] == 2


# ── 5. send_heartbeat attaches the crons push to the outgoing payload ──────


def test_send_heartbeat_attaches_crons_cache_pushes(sync_with_seeded_crons, monkeypatch):
    """End-to-end: the cron-list push must arrive in the `/ingest/heartbeat`
    POST body so the cloud's _accept_cache_pushes can write it to Redis."""
    s, config, _ = sync_with_seeded_crons
    captured = {}

    def fake_post(path, payload, api_key, timeout=45):
        if path == "/ingest/heartbeat":
            captured["payload"] = payload
            return {"sync_allowed": True, "pending_queries": []}
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr(s, "_post", fake_post)
    monkeypatch.setattr(s.time, "sleep", lambda *a, **kw: None)

    assert s.send_heartbeat(config) is True
    payload = captured["payload"]
    pushes = payload.get("cache_pushes", [])

    cron_entries = [p for p in pushes
                    if isinstance(p, dict)
                    and p.get("key", "").startswith("crons:")
                    and p.get("key", "").endswith(":node-cron-test")]
    assert len(cron_entries) == 1, (
        "crons cache_push must land in the heartbeat payload alongside any "
        "brain/memory/alert/approvals pushes"
    )
    entry = cron_entries[0]
    assert entry["ttl_s"] == s.CRONS_CACHE_TTL_SEC
    assert isinstance(entry["blob"], str) and len(entry["blob"]) > 0
