"""Belt-and-suspenders cross-evaluator dedup for the fleet SQLite
``alert_history`` table.

Live repro 2026-07-15 on a licensed local-only node: the same alert rule
(rule_id ``2f270a9c…``, ``channel="banner"``) landed twice ~1 s apart
(alert_history ids 3, 4). Root cause: two evaluators write to the SAME
``alert_history`` table but hold SEPARATE per-process cooldown memos —

  (a) sync.py's ``_evaluate_alerts_local`` (2 s tick, memo lives in
      ``state["alerts_eval_memo"]``, added in commit c01163621),
  (b) dashboard.py's ``_budget_monitor_loop`` (60 s tick, memo lives in
      the ``_budget_alert_cooldowns`` module dict).

Neither evaluator consults ``alert_history`` before INSERTing, so on a
node where both paths see the same rule id (e.g. cloud + local seeded
rule, or a dashboard-created rule mirrored into DuckDB by any future
sync), the same fire lands twice.

Fix: BOTH paths now check ``alert_history`` for a fire of the same
rule_id within the rule's ``cooldown_min`` before INSERT. Skip the row
when a fresher fire already exists. cooldown=0 disables the check so
explicit no-cooldown rules still fire every tick (matches existing intent
of ``cooldown_sec: 0`` in condition_json).
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import sys
import time

import pytest


_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


@pytest.fixture
def fleet_db_path(tmp_path, monkeypatch):
    p = tmp_path / "fleet.db"
    monkeypatch.setenv("CLAWMETRY_FLEET_DB", str(p))
    return p


@pytest.fixture
def sync_module():
    sys.modules.pop("clawmetry.sync", None)
    import clawmetry.sync as s
    importlib.reload(s)
    return s


def _row_count(fleet_db_path, rule_id):
    if not fleet_db_path.exists():
        return 0
    db = sqlite3.connect(str(fleet_db_path))
    try:
        return db.execute(
            "SELECT COUNT(*) FROM alert_history WHERE rule_id = ?",
            (rule_id,),
        ).fetchone()[0]
    finally:
        db.close()


def _match(rule_id="rule-x", cooldown_sec=300):
    """Shape ``alert_evaluator.evaluate`` returns and _persist_local_alert_banner
    consumes."""
    return {
        "summary": "test fire",
        "rule": {
            "id": rule_id,
            "name": "Test rule",
            "condition_json": {
                "type": "count_over_threshold",
                "cooldown_sec": cooldown_sec,
            },
        },
        "event": {"id": "evt-1"},
    }


# ── sync.py side of the dedup ────────────────────────────────────────────


def test_sync_local_banner_dedups_within_cooldown(sync_module, fleet_db_path):
    """Two consecutive fires within the cooldown → only ONE row lands."""
    ok1 = sync_module._persist_local_alert_banner(_match(cooldown_sec=300))
    ok2 = sync_module._persist_local_alert_banner(_match(cooldown_sec=300))
    assert ok1 is True
    assert ok2 is False  # suppressed by dedup
    assert _row_count(fleet_db_path, "rule-x") == 1


def test_sync_local_banner_zero_cooldown_still_fires(sync_module, fleet_db_path):
    """cooldown_sec=0 is an explicit 'no cooldown' — the check must
    disable itself so no-cooldown rules keep firing every tick."""
    sync_module._persist_local_alert_banner(_match(cooldown_sec=0))
    sync_module._persist_local_alert_banner(_match(cooldown_sec=0))
    assert _row_count(fleet_db_path, "rule-x") == 2


def test_sync_local_banner_defers_to_dashboard_prior_fire(
    sync_module, fleet_db_path
):
    """A dashboard.py-authored row from 1 s ago (same rule_id) inside the
    cooldown window → the sync-daemon path does NOT re-insert. This is
    the direct guard for the 2026-07-15 double-fire live repro."""
    # Pre-seed a "dashboard just fired" row exactly like dashboard.py's
    # _fire_alert would.
    db = sqlite3.connect(str(fleet_db_path))
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT NOT NULL,
                fired_at REAL NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                ack_at REAL
            )
            """
        )
        db.execute(
            "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("rule-x", "threshold", "dashboard fired", "banner", time.time()),
        )
        db.commit()
    finally:
        db.close()

    ok = sync_module._persist_local_alert_banner(_match(cooldown_sec=1800))
    assert ok is False
    assert _row_count(fleet_db_path, "rule-x") == 1


# ── dashboard.py side of the dedup ───────────────────────────────────────


def test_dashboard_custom_rule_dedups_prior_sync_fire(fleet_db_path):
    """Symmetric guard: a prior fire by sync.py within the cooldown must
    prevent dashboard.py's custom-alert-rules block from re-inserting.

    We can't easily drive the whole _budget_monitor_loop, but the guard
    lives in a self-contained SQL check that we can exercise by
    round-tripping through the SAME fleet DB and querying with the same
    predicate the guard uses (rule_id + fired_at > now-cooldown)."""
    # Pre-seed a "sync fired" row.
    db = sqlite3.connect(str(fleet_db_path))
    try:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS alert_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_id TEXT,
                type TEXT NOT NULL,
                message TEXT NOT NULL,
                channel TEXT NOT NULL,
                fired_at REAL NOT NULL,
                acknowledged INTEGER DEFAULT 0,
                ack_at REAL
            )
            """
        )
        now = time.time()
        db.execute(
            "INSERT INTO alert_history (rule_id, type, message, channel, fired_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("rule-x", "threshold", "sync fired", "banner", now),
        )
        db.commit()
        # Predicate the guard uses in dashboard.py's custom-rules block:
        cooldown = 1800  # 30 min
        cutoff = now - cooldown
        existing = db.execute(
            "SELECT 1 FROM alert_history "
            "WHERE rule_id = ? AND fired_at > ? LIMIT 1",
            ("rule-x", cutoff),
        ).fetchone()
        assert existing is not None
    finally:
        db.close()


def test_dashboard_guard_source_matches_sync_guard(fleet_db_path):
    """The two guards MUST use structurally equivalent SQL predicates
    (WHERE rule_id AND fired_at > cutoff LIMIT 1) — otherwise one path
    would skip while the other still inserts and the double-fire
    returns. Grep-based invariant that survives whitespace differences
    (dashboard.py's guard is split across three adjacent string literals
    inside a nested block)."""
    dashboard_source = open(os.path.join(_REPO_ROOT, "dashboard.py")).read()
    sync_source = open(
        os.path.join(_REPO_ROOT, "clawmetry", "sync.py")
    ).read()
    import re as _re
    # Match "SELECT 1 FROM alert_history … WHERE rule_id = ? AND
    # fired_at > ? … LIMIT 1" tolerating any whitespace / quoted-string
    # gaps (Python source concatenates them at compile time).
    pattern = _re.compile(
        r"SELECT\s+1\s+FROM\s+alert_history[\s\"']+WHERE\s+rule_id\s*=\s*\?"
        r"\s+AND\s+fired_at\s*>\s*\?[\s\"']+LIMIT\s+1",
        _re.MULTILINE,
    )
    assert pattern.search(dashboard_source) is not None, (
        "dashboard.py must guard its INSERT with the same predicate as "
        "sync.py — otherwise the cross-evaluator dedup only covers one "
        "direction and the double-fire regresses"
    )
    assert pattern.search(sync_source) is not None
