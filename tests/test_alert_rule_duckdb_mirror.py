"""The cross-evaluator rule mirror must land, and must never claim it did.

A node runs two alert evaluators over two stores: the dashboard's in-process
loop reads the fleet SQLite DB, and the daemon's ``alert_evaluator`` reads
DuckDB. Until PR #4903 nothing bridged them — ``ingest_alert_rule`` was only
ever called from the cloud pending-action relay — so a rule created from the
Alerts tab on a no-cloud node was evaluated by nobody.

The subtle half is the reporting. ``ingest_alert_rule`` returns None, and
``local_store_via_daemon`` ALSO returns None when the proxy call failed, so
"no exception" is not evidence the write landed. Caught live: against a
daemon running an older wheel (whose allowlist has no ``ingest_alert_rule``)
the first implementation reported ``mirrored: true`` for a write that never
happened — and fell back to opening a writer handle from the dashboard
process, the brick-lock hazard, where DuckDB let the row land somewhere the
daemon would never read.
"""

import pytest

from routes import alerts


class _FakeStore:
    def __init__(self):
        self.rules = {}

    def ingest_alert_rule(self, rule):
        self.rules[str(rule["id"])] = rule

    def delete_alert_rule(self, rule_id):
        return 1 if self.rules.pop(str(rule_id), None) else 0

    def query_alert_rules(self, **kw):
        return list(self.rules.values())


@pytest.fixture
def daemon(monkeypatch):
    """A reachable daemon proxy backed by an in-memory store."""
    store = _FakeStore()

    def _via_daemon(method, **kwargs):
        return getattr(store, method)(**kwargs)

    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", _via_daemon)
    return store


@pytest.fixture
def dead_daemon(monkeypatch):
    """A daemon that rejects the call — an older wheel whose allowlist has no
    ``ingest_alert_rule``. local_store_via_daemon swallows that and returns
    None, exactly like 'daemon not running'."""
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)

    import clawmetry.local_server as ls
    monkeypatch.setattr(ls, "is_running", lambda: False)


def _mirror(rule_id="r1", alert_type="error_rate"):
    return alerts._mirror_rule_to_duckdb(
        rule_id, alert_type=alert_type, threshold=5, runtime="all",
        channels=[], cooldown_min=30, enabled=True, name="Tool failures",
    )


def test_mirror_lands_in_duckdb(daemon):
    assert _mirror() is True
    assert "r1" in daemon.rules


def test_mirror_preserves_cloud_vocabulary(daemon):
    """alert_evaluator reads condition_json's alert_type via its legacy map.

    Mirroring the LOCAL type instead would land a rule the daemon cannot
    interpret — a mirror that exists but still never fires.
    """
    _mirror(alert_type="eval_score_below")
    cond = daemon.rules["r1"]["condition_json"]
    assert cond["alert_type"] == "eval_score_below"
    assert cond["threshold_value"] == 5
    assert cond["runtime"] == "all"


def test_mirror_reports_false_when_the_write_did_not_land(dead_daemon):
    """The live regression: a rejected proxy call must not read as success."""
    assert _mirror() is False


def test_mirror_never_opens_a_writer_from_the_dashboard(monkeypatch):
    """Only the daemon may hold the DuckDB writer lock.

    Opening one from the dashboard process is the documented brick-lock
    hazard, and where DuckDB permits it the row lands in a handle the daemon
    never reads. So: no proxy and not the daemon => give up, don't write.
    """
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)

    import clawmetry.local_server as ls
    monkeypatch.setattr(ls, "is_running", lambda: False)

    opened = []

    import clawmetry.local_store as ls_mod
    monkeypatch.setattr(ls_mod, "get_store",
                        lambda *a, **k: opened.append(True) or _FakeStore())

    assert _mirror() is False
    assert not opened, (
        "opened a DuckDB handle from the dashboard process while the daemon "
        "owns the writer lock"
    )


def test_unmirror_removes_the_rule(daemon):
    _mirror()
    assert "r1" in daemon.rules
    assert alerts._unmirror_rule_from_duckdb("r1") is True
    assert "r1" not in daemon.rules


def test_evaluator_only_types_are_the_ones_mirrored():
    """Only types the daemon's evaluator actually implements get mirrored.

    Mirroring a type the in-process loop owns would put two evaluators on one
    rule; mirroring one neither implements would just relocate a zombie.
    """
    from clawmetry import alert_evaluator

    for t in alerts._EVALUATOR_ONLY:
        assert t in alert_evaluator._LEGACY_ALERT_TYPE_MAP, (
            f"{t} is mirrored to the daemon, but alert_evaluator has no "
            f"mapping for it — the mirrored rule would never fire."
        )
        assert t not in alerts._CLOUD_TO_LOCAL, (
            f"{t} is both mirrored and locally evaluated — two evaluators "
            f"would run one rule."
        )


def test_repair_remirrors_a_rule_the_old_daemon_rejected(daemon, monkeypatch):
    """Close the upgrade-skew window.

    A new dashboard can write a rule that an old daemon refuses (its method
    allowlist predates the bridge). Once the daemon catches up, nothing would
    otherwise ever mirror that rule — it would stay inert forever, which is
    the exact defect this change exists to remove, arriving by a later route.
    """
    monkeypatch.setattr(alerts, "_MIRROR_REPAIRED", set())
    assert "stranded" not in daemon.rules

    alerts._repair_missing_mirrors([{
        "id": "stranded", "alert_type": "error_rate", "threshold": 5,
        "runtime": "all", "channels": '["banner"]', "cooldown_min": 30,
        "enabled": 1,
    }])
    assert "stranded" in daemon.rules


def test_repair_is_attempted_once_per_rule(daemon, monkeypatch):
    """It repairs an upgrade window, so it must not run on every page load."""
    monkeypatch.setattr(alerts, "_MIRROR_REPAIRED", set())
    calls = []
    real = alerts._mirror_rule_to_duckdb
    monkeypatch.setattr(alerts, "_mirror_rule_to_duckdb",
                        lambda *a, **k: calls.append(1) or real(*a, **k))
    rule = {"id": "once", "alert_type": "error_rate", "threshold": 5,
            "runtime": "all", "channels": "[]", "cooldown_min": 30,
            "enabled": 1}
    alerts._repair_missing_mirrors([rule])
    alerts._repair_missing_mirrors([rule])
    assert len(calls) == 1


def test_repair_ignores_locally_evaluated_rules(daemon, monkeypatch):
    """Mirroring a rule the in-process loop owns would double-evaluate it."""
    monkeypatch.setattr(alerts, "_MIRROR_REPAIRED", set())
    alerts._repair_missing_mirrors([{
        "id": "local", "alert_type": "daily_spend", "threshold": 50,
        "runtime": "all", "channels": "[]", "cooldown_min": 30, "enabled": 1,
    }])
    assert "local" not in daemon.rules


def test_repair_does_nothing_when_the_store_is_unreadable(monkeypatch):
    """An unreadable store must not be read as 'nothing is mirrored'."""
    monkeypatch.setattr(alerts, "_MIRROR_REPAIRED", set())
    monkeypatch.setattr(alerts, "_duckdb_rule_ids", lambda: None)
    called = []
    monkeypatch.setattr(alerts, "_mirror_rule_to_duckdb",
                        lambda *a, **k: called.append(1))
    alerts._repair_missing_mirrors([{
        "id": "x", "alert_type": "error_rate", "threshold": 5,
        "runtime": "all", "channels": "[]", "cooldown_min": 30, "enabled": 1,
    }])
    assert not called
