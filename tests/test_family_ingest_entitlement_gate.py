"""Live per-runtime entitlement gate in sync_family_runtimes (2026-08-06):
`_family_adapter_classes()` keeps successfully importing an already-installed
clawmetry-pro wheel forever -- nothing uninstalls it -- so a lapsed trial (or
an account that was never entitled) kept ingesting NEW paid-runtime sessions
indefinitely once the wheel had landed once. Nothing re-checked entitlement
per ingest cycle; the daemon relied only on the coarse `_sync_allowed()`
cloud-relay-pause flag, which defaults to allowed. This pins the fix:
sync_family_runtimes must skip an adapter whose runtime
entitlements.allows_runtime() denies (e.g. an EXPIRED trial), and must NOT
skip one it allows (default grace mode, non-expired).

Pure-unit, isolated DuckDB: fake adapter classes report detected=True and a
trivial session so the fix's effect (0 events ingested for a denied runtime
vs >0 for an allowed one) is directly observable without clawmetry-pro.
"""
from __future__ import annotations

import importlib
import time
from types import SimpleNamespace

import pytest


@pytest.fixture
def sync_with_isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    importlib.reload(sync)
    monkeypatch.setattr(ls, "_daemon_registered", lambda: False)
    monkeypatch.delenv("CLAWMETRY_ROLE", raising=False)
    yield sync, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _fake_adapter_class(runtime_name, sessions_mock):
    class _Adapter:
        name = runtime_name

        def detect(self):
            return SimpleNamespace(detected=True)

        def list_sessions(self, limit=None):
            return sessions_mock(limit=limit)

    _Adapter.__name__ = f"Fake_{runtime_name}"
    return _Adapter


def _run(sync, classes, ent):
    from unittest.mock import patch
    from clawmetry import entitlements as entmod

    with patch.object(sync, "_family_adapter_classes", return_value=classes), \
         patch.object(sync, "_sync_allowed", return_value=True), \
         patch.object(sync, "_openclaw_spawned_claude_ids", return_value=set()), \
         patch.object(entmod, "get_entitlement", return_value=ent):
        return sync.sync_family_runtimes({"node_id": "n", "api_key": "k"}, {}, {})


def test_expired_trial_blocks_paid_runtime_ingest(sync_with_isolated_store):
    """The gate must short-circuit BEFORE list_sessions() is ever called --
    an expired trial should not even attempt to read the runtime's data."""
    sync, ls = sync_with_isolated_store
    from unittest.mock import MagicMock
    from clawmetry.entitlements import Entitlement, TIER_TRIAL

    expired_trial = Entitlement(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() - 86400, grace=True,
    )
    sessions_mock = MagicMock(return_value=[])
    classes = [_fake_adapter_class("claude_code", sessions_mock)]
    n_events = _run(sync, classes, expired_trial)
    assert n_events == 0
    sessions_mock.assert_not_called()


def test_active_trial_allows_paid_runtime_ingest(sync_with_isolated_store):
    """A non-expired trial must reach list_sessions() -- the gate only ever
    denies on an actually-expired (or unentitled, enforce-mode) resolution."""
    sync, ls = sync_with_isolated_store
    from unittest.mock import MagicMock
    from clawmetry.entitlements import Entitlement, TIER_TRIAL

    active_trial = Entitlement(
        tier=TIER_TRIAL, source="license", node_limit=1,
        expiry=time.time() + 86400, grace=True,
    )
    sessions_mock = MagicMock(return_value=[])
    classes = [_fake_adapter_class("claude_code", sessions_mock)]
    _run(sync, classes, active_trial)
    sessions_mock.assert_called_once()


def test_default_grace_mode_allows_ingest_pre_expiry(sync_with_isolated_store):
    """A plain OSS/free entitlement (no license, no cloud plan) has no
    expiry at all -- grace mode passes it through, matching today's
    documented default-on behavior for every non-expired install."""
    sync, ls = sync_with_isolated_store
    from unittest.mock import MagicMock
    from clawmetry.entitlements import Entitlement, TIER_OSS

    oss = Entitlement(tier=TIER_OSS, source="oss", node_limit=1, expiry=None, grace=True)
    sessions_mock = MagicMock(return_value=[])
    classes = [_fake_adapter_class("claude_code", sessions_mock)]
    _run(sync, classes, oss)
    sessions_mock.assert_called_once()
