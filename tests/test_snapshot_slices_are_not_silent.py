"""The daemon must not HTTP-proxy to itself, and must say so when a slice is empty.

Founder report 2026-10-06. localhost:8900 showed a red banner --
"Anomaly detected: cost spike (5.4x baseline) + 3 more", a CRITICAL spike on
a $128 session -- and app.clawmetry.com showed no banner at all, because the
daemon pushed ``usage.anomalies == {}``. ``cacheTrends``, ``costComparison``,
``spendOptimization`` and ``costBreakdown`` were empty in the same snapshot.

The chain:

  1. ``routes/usage.py::_ls_get_store()`` returns ``_DaemonProxyStore``
     whenever a daemon is discoverable -- including when the caller IS the
     daemon, which is exactly the case when the daemon builds its snapshot.
  2. ``_DaemonProxyStore`` forwards to ``_proxy_dispatch``, which correctly
     refuses to self-proxy ("dispatch is in-daemon; skipping proxy") -- but
     refuses by returning None.
  3. Every ``query_*`` therefore answers None, the builders read that as "no
     store" and defer, and ``_build_usage_snapshot._safe`` turned the
     deferral into ``{}``.
  4. The hosted ``cm-cloud-usage`` interceptor reads ``{}``, falls through to
     the container's empty store, and the card renders as though the node had
     nothing to say.

Nobody could see any of it, because ``_safe`` discarded the reason. Both
halves are pinned here: the loop-break that makes the daemon read its own
store, and the logging that makes a future empty slice self-explaining.
"""

from __future__ import annotations

import logging

import pytest


@pytest.fixture()
def sync_log(monkeypatch):
    """Capture the daemon's own logger.

    ``clawmetry-sync`` sets ``propagate = False`` (sync.py), so pytest's
    caplog -- which listens on the root logger -- never sees these records.
    Attach a handler to the logger itself and return the messages.
    """
    import clawmetry.sync as sync

    seen = []

    class _Catch(logging.Handler):
        def emit(self, record):
            seen.append(record.getMessage())

    h = _Catch(level=logging.WARNING)
    sync.log.addHandler(h)
    old = sync.log.level
    sync.log.setLevel(logging.WARNING)
    yield seen
    sync.log.removeHandler(h)
    sync.log.setLevel(old)


@pytest.fixture()
def only_anomalies(monkeypatch):
    """Stub every slice but ``anomalies`` so the assertion is about this
    builder and not about whatever store the test machine happens to have."""
    import routes.sessions as sessions
    import routes.usage as usage

    for name in ("_try_local_store_cost_comparison",
                 "_try_local_store_spend_optimization",
                 "_try_local_store_usage_forecast"):
        monkeypatch.setattr(usage, name, lambda: {"stub": True})
    monkeypatch.setattr(usage, "_try_local_store_cache_trends",
                        lambda days: {"stub": True})
    monkeypatch.setattr(sessions, "_try_local_store_cost_breakdown",
                        lambda: {"stub": True})


@pytest.fixture()
def in_daemon(monkeypatch):
    """Make this process look like the daemon: local_server is running."""
    from clawmetry import local_server
    monkeypatch.setattr(local_server, "is_running", lambda: True)
    # A daemon is always discoverable to itself, which is what used to send
    # _ls_get_store down the proxy branch.
    monkeypatch.setattr("routes.local_query._cached_discovery",
                        lambda: {"port": 1, "token": "t"}, raising=False)


def test_the_daemon_reads_its_own_store_not_an_http_proxy_to_itself(in_daemon, monkeypatch):
    import routes.usage as usage
    from clawmetry import local_store

    sentinel = object()
    monkeypatch.setattr(local_store, "get_store", lambda **kw: sentinel)

    got = usage._ls_get_store()
    assert got is sentinel, (
        "the daemon proxied to itself; every query would answer None and the "
        "hosted dashboard would show empty Usage cards")
    assert not isinstance(got, usage._DaemonProxyStore)


def test_the_writer_owner_flag_alone_is_enough(monkeypatch):
    """local_store.mark_writer_owner() is the canonical "I am the daemon"
    signal and is set before local_server.start() finishes, so the loop-break
    must not depend on the query server already being up."""
    import routes.usage as usage
    from clawmetry import local_server, local_store

    monkeypatch.setattr(local_server, "is_running", lambda: False)
    monkeypatch.setattr(local_store, "is_writer_owner", lambda: True)
    monkeypatch.setattr("routes.local_query._cached_discovery",
                        lambda: {"port": 1, "token": "t"}, raising=False)
    sentinel = object()
    monkeypatch.setattr(local_store, "get_store", lambda **kw: sentinel)
    assert usage._ls_get_store() is sentinel


def test_a_dashboard_process_still_uses_the_daemon_proxy(monkeypatch):
    """The loop-break must not cost the separate-process install its proxy."""
    import routes.usage as usage
    from clawmetry import local_server, local_store

    monkeypatch.setattr(local_server, "is_running", lambda: False)
    monkeypatch.setattr(local_store, "is_writer_owner", lambda: False)
    monkeypatch.setattr("routes.local_query._cached_discovery",
                        lambda: {"port": 1, "token": "t"}, raising=False)
    assert isinstance(usage._ls_get_store(), usage._DaemonProxyStore)


def test_a_deferred_slice_says_so_in_the_log(sync_log, only_anomalies, monkeypatch):
    """A deferral is not a measurement of zero, and must never be silent."""
    import clawmetry.sync as sync
    import routes.usage as usage

    monkeypatch.setattr(usage, "_try_local_store_anomalies", lambda: None)
    out = sync._build_usage_snapshot()

    assert out["anomalies"] == {}
    msgs = " ".join(sync_log)
    assert "anomalies" in msgs and "deferred" in msgs, (
        "an empty slice stayed silent; this is the bug that hid a critical "
        "cost-spike alert from the hosted dashboard")


def test_a_raising_slice_names_the_exception(sync_log, only_anomalies, monkeypatch):
    import clawmetry.sync as sync
    import routes.usage as usage

    def boom():
        raise RuntimeError("duckdb is locked")
    monkeypatch.setattr(usage, "_try_local_store_anomalies", boom)
    out = sync._build_usage_snapshot()

    assert out["anomalies"] == {}
    msgs = " ".join(sync_log)
    assert "anomalies" in msgs and "RuntimeError" in msgs and "duckdb is locked" in msgs


def test_a_real_slice_is_passed_through_untouched(only_anomalies, monkeypatch):
    """Logging the empty case must not disturb the working one."""
    import clawmetry.sync as sync
    import routes.usage as usage

    body = {"anomalies": [{"id": 1}], "active_count": 1}
    monkeypatch.setattr(usage, "_try_local_store_anomalies", lambda: body)
    assert sync._build_usage_snapshot()["anomalies"] == body


# ---------------------------------------------------------------------------
# The cron slice read the filesystem while the dashboard read the store
# ---------------------------------------------------------------------------
#
# Same family, different mechanism. `/api/crons` answers from DuckDB
# (`_source: local_store`) and listed three jobs; `_build_cron_jobs` read
# `~/.openclaw/**/cron/jobs.json`, which does not exist on that node, and
# shipped `cronJobs: []`. The hosted Crons tab was therefore empty beside a
# node running three crons. CLAUDE.md names the rule: the store is the data
# layer features read, and a filesystem read "works locally but returns empty
# in cloud".

def test_cron_slice_prefers_the_store_the_dashboard_reads(monkeypatch):
    import clawmetry.sync as sync
    import routes.crons as crons

    monkeypatch.setattr(crons, "_try_local_store_crons", lambda: {
        "jobs": [{"id": "a", "name": "heartbeat-main", "enabled": True}],
        "_source": "local_store"})
    # No jobs.json anywhere: the file path alone would have returned [].
    monkeypatch.setattr(sync.os.path, "isfile", lambda p: False)

    jobs = sync._build_cron_jobs(None)
    assert [j["name"] for j in jobs] == ["heartbeat-main"], (
        "the hosted Crons tab would be empty beside a node running crons")


def test_cron_slice_still_falls_back_to_the_file(monkeypatch, tmp_path):
    """The gateway-managed layout that does write jobs.json must keep working."""
    import json

    import clawmetry.sync as sync
    import routes.crons as crons

    monkeypatch.setattr(crons, "_try_local_store_crons", lambda: None)
    d = tmp_path / "cron"
    d.mkdir()
    (d / "jobs.json").write_text(json.dumps(
        {"jobs": [{"id": "b", "name": "from-file", "enabled": True,
                   "schedule": {"kind": "cron", "expr": "0 3 * * *"}}]}))
    monkeypatch.setattr(sync, "_get_openclaw_dir", lambda: str(tmp_path))

    jobs = sync._build_cron_jobs(None)
    assert [j["name"] for j in jobs] == ["from-file"]


def test_a_store_read_that_raises_is_logged_not_swallowed(sync_log, monkeypatch):
    import clawmetry.sync as sync
    import routes.crons as crons

    def boom():
        raise RuntimeError("store unavailable")
    monkeypatch.setattr(crons, "_try_local_store_crons", boom)
    monkeypatch.setattr(sync.os.path, "isfile", lambda p: False)

    assert sync._build_cron_jobs(None) == []
    assert any("cron jobs could not be read" in m for m in sync_log)
