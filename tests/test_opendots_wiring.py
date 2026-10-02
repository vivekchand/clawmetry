"""Public wiring and mutable-native-record ingestion, without private source."""
import importlib
import json
import re
import time
from pathlib import Path

import pytest

from clawmetry.adapters.base import DetectResult, Event, Session


def test_opendots_is_paid_and_loaded_only_from_pro():
    from clawmetry import entitlements as ent, sync
    assert 'opendots' in ent.PAID_RUNTIMES
    assert 'opendots' not in ent.FREE_RUNTIMES
    assert ent.RUNTIME_LABELS['opendots'] == 'OpenDots'
    assert ('clawmetry_pro.adapters.opendots', 'OpenDotsAdapter') in sync._FAMILY_ADAPTER_SPECS
    assert sync._runtime_of_session('opendots:store:thread:id') == 'opendots'
    assert not ent.Entitlement(tier=ent.TIER_OSS, source='test', grace=False).allows_runtime('opendots')
    assert ent.Entitlement(tier=ent.TIER_PRO, source='test', grace=False,
                           runtimes=ent.ALL_RUNTIMES).allows_runtime('opendots')


def test_opendots_ui_and_snapshot_do_not_claim_usage():
    from clawmetry import sync
    src = (Path(__file__).parents[1] / 'clawmetry/static/js/app.js').read_text()
    caps = re.search(r"opendots:\s*\[(.*?)\]", src).group(1)
    assert set(re.findall(r"'([A-Z]+)'", caps)) == {'SESSIONS', 'EVENTS', 'BRAIN'}
    record = sync._build_runtime_records()['opendots']
    assert set(record['records'].values()) == {'unavailable'}
    assert record['suppress_zero']


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv('CLAWMETRY_LOCAL_STORE_PATH', str(tmp_path / 'opendots.duckdb'))
    monkeypatch.setenv('CLAWMETRY_LOCAL_FLUSH_SECS', '0.05')
    monkeypatch.setenv('CLAWMETRY_LOCAL_FLUSH_BATCH', '1')
    import clawmetry.local_store as ls
    import clawmetry.sync as sync
    importlib.reload(ls)
    ls.mark_writer_owner()
    store = ls.get_store()
    monkeypatch.setattr(sync, '_sync_allowed', lambda: True)
    monkeypatch.setattr(sync, '_openclaw_spawned_claude_ids', lambda: set())
    monkeypatch.setattr(sync, '_ingest_keepalive_heartbeat', lambda config: False)
    from clawmetry import entitlements as ent
    monkeypatch.setattr(ent, 'get_entitlement', lambda: ent.Entitlement(
        tier=ent.TIER_PRO, source='test', grace=False, runtimes=ent.ALL_RUNTIMES))
    try:
        yield sync, store
    finally:
        store.stop(flush=True)


def test_same_timestamp_content_revision_reingests_once(isolated_store, monkeypatch):
    sync, store = isolated_store
    revision = ['a' * 20]
    class Adapter:
        name = 'opendots'
        def detect(self):
            return DetectResult('opendots', 'OpenDots', True)
        def list_sessions(self, limit=50):
            return [Session(agent=self.name, id='store:thread:one', title='Call receipt',
                            started_at=1790841600, ended_at=1790841610, cost_usd=None,
                            cost_status='unavailable', extra={'ingestRevision': revision[0]})]
        def list_events(self, sid, limit=500):
            return [Event(agent=self.name, session_id=sid, id='receipt:' + revision[0],
                          type='call_receipt', ts=1790841610,
                          content='Original' if revision[0].startswith('a') else 'Late transcript')]
    monkeypatch.setattr(sync, '_family_adapter_classes', lambda: [Adapter])
    state = {}
    config = {'node_id': 'isolated-test-node'}
    assert sync.sync_family_runtimes(config, state, {}) == 1
    assert sync.sync_family_runtimes(config, state, {}) == 0
    revision[0] = 'b' * 20
    assert sync.sync_family_runtimes(config, state, {}) == 1
    assert sync.sync_family_runtimes(config, state, {}) == 0
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        rows = store._fetch("SELECT data FROM events WHERE session_id='opendots:store:thread:one'", [])
        if len(rows) == 2:
            break
        time.sleep(0.02)
    assert len(rows) == 2
    data = [json.loads(r[0]) if isinstance(r[0], (str, bytes)) else r[0] for r in rows]
    assert {r['content'] for r in data} == {'Original', 'Late transcript'}
    assert {r['_runtime'] for r in data} == {'opendots'}
