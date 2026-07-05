"""Regression tests for issue #3526.

OpenClaw 2026.7.1 introduced event-driven cron runs (#92037, #98755):
  - 'on-exit' schedule kind wakes an agent when a watched command exits
  - session-targeted cron runs can detach from the triggering session

The gateway stamps `cronScheduleKind` (e.g. "on-exit") and `cronDetachedRun`
(bool) on sessions spawned by these cron types.  Before this fix,
list_sessions() never read those fields, so on-exit/detached sessions were
indistinguishable from ordinary cron deliveries.
"""

import clawmetry.adapters.openclaw as ocmod
from clawmetry.adapters.openclaw import OpenClawAdapter


class _FakeDash:
    def __init__(self, extra_fields=None):
        self._fields = extra_fields or {}

    def _get_sessions(self):
        record = {"sessionId": "sess-cron-exit"}
        record.update(self._fields)
        return [record]


def test_list_sessions_surfaces_cron_schedule_kind(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"cronScheduleKind": "on-exit"})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert len(sessions) == 1
    assert sessions[0].extra.get("cronScheduleKind") == "on-exit", (
        "list_sessions() must surface cronScheduleKind from the gateway record"
    )


def test_list_sessions_surfaces_cron_trigger_kind_alias(monkeypatch):
    """cronTriggerKind is accepted as an alias when cronScheduleKind is absent."""
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"cronTriggerKind": "on-exit"})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("cronScheduleKind") == "on-exit", (
        "cronTriggerKind alias must be accepted when cronScheduleKind is missing"
    )


def test_list_sessions_surfaces_cron_detached_run(monkeypatch):
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"cronDetachedRun": True})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("cronDetachedRun") is True, (
        "list_sessions() must surface cronDetachedRun from the gateway record"
    )


def test_list_sessions_surfaces_cron_detached_alias(monkeypatch):
    """cronDetached is accepted as an alias when cronDetachedRun is absent."""
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"cronDetached": True})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert sessions[0].extra.get("cronDetachedRun") is True, (
        "cronDetached alias must be accepted when cronDetachedRun is missing"
    )


def test_list_sessions_omits_fields_when_absent(monkeypatch):
    """Extra keys must not appear for ordinary sessions without these fields."""
    monkeypatch.setattr(
        ocmod, "_d",
        lambda: _FakeDash({"cronDeliveryTarget": True}),
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    assert "cronScheduleKind" not in sessions[0].extra, (
        "cronScheduleKind must not appear when not in gateway record"
    )
    assert "cronDetachedRun" not in sessions[0].extra, (
        "cronDetachedRun must not appear when not in gateway record"
    )


def test_list_sessions_coerces_detached_run_to_bool(monkeypatch):
    """Non-bool truthy values must be coerced to bool."""
    monkeypatch.setattr(
        ocmod, "_d", lambda: _FakeDash({"cronDetachedRun": 1})
    )
    sessions = OpenClawAdapter().list_sessions(limit=10)
    val = sessions[0].extra.get("cronDetachedRun")
    assert val is True, (
        "cronDetachedRun must be coerced to bool, got %r" % val
    )
