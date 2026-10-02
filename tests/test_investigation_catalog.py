"""Scoped discovery and entitled grouping use persisted, bounded records.

AC-OBS-INV-003.1: group inputs are scoped before window limits.
AC-OBS-INV-003.2: grouping preserves event-specific resolution.
AC-OBS-INV-005.1: CLI extensions reuse exact session discovery and read scope.
"""
import time
from types import SimpleNamespace

from tests import test_incident_lifecycle as lifecycle
from tests.test_investigation_reads import events, read

server = lifecycle.server
store = lifecycle.store


def test_selected_event_fetches_outside_page_but_never_outside_scope(store):
    source = events(store)
    chosen = min(row['id'] for row in source)
    answer = read(store, limit=1, event_id=chosen)
    assert chosen not in [r['id'] for r in answer['rows']]
    assert [r['id'] for r in answer['evidence_rows']] == [chosen]
    assert answer['selected_event_ids'] == [chosen]
    events(store, count=1, node='node-b')
    answer = read(store, event_id='node-b-codex-0')
    assert answer['evidence_rows'] == []
    assert answer['coverage']['missing_event_ids'] == ['node-b-codex-0']


def test_catalog_scopes_before_limit_and_discovers_canonical_runtime(store):
    store.ingest_session({'session_id': 'codex:wanted', 'agent_type': 'main', 'node_id': 'a',
                          'title': 'Useful run', 'status': 'active', 'ended_at': '2026-10-02T10:00:00Z'})
    for i in range(5):
        store.ingest_session({'session_id': f'other-{i}', 'agent_type': 'openclaw', 'node_id': 'a'})
    answer = store.query_session_catalog(runtime='codex', node_id='a', limit=1)
    assert answer['rows'][0]['session_id'] == 'codex:wanted'
    assert answer['rows'][0]['runtime'] == 'codex'
    assert answer['rows'][0]['status'] == 'ended'
    assert answer['coverage']['truncated'] is False
    assert store.query_session_catalog(node_id='b')['rows'] == []


def test_error_read_gate_precedes_extension_and_sql(store, monkeypatch):
    from clawmetry import entitlements, extensions
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_feature=lambda name: False))
    monkeypatch.setattr(extensions, 'load_plugins', lambda: (_ for _ in ()).throw(AssertionError()))
    result = store.query_error_groups()
    assert result['available'] is False and result['error'] == 'upgrade_required'


def test_error_group_inputs_scoped_capped_and_resolution_is_exact(store, monkeypatch):
    from clawmetry import entitlements, extensions
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_feature=lambda name: True))
    monkeypatch.setattr(extensions, 'load_plugins', lambda: None)
    seen = []
    def group(name, payload):
        seen.append(payload)
        return {'rows': [], 'events_counted': len(payload['rows'])}
    monkeypatch.setattr(extensions, 'call', group)
    events(store, count=4)
    events(store, count=8, node='node-b')
    store.mark_error_resolved('node-a-codex-3')
    before = store.query_resolved_errors()
    result = store.query_error_groups(node_id='node-a', runtime='codex', limit=2)
    assert result['available'] is True and result['events_counted'] == 2
    assert result['coverage']['truncated'] is True
    assert all(r['node_id'] == 'node-a' for r in seen[0]['rows'])
    assert 'node-a-codex-3' in seen[0]['resolved']
    assert store.query_resolved_errors() == before
    assert result['coverage']['counts_basis'] == 'selected_window_only'
    # Missing paid implementation is unavailable, never an empty successful read.
    monkeypatch.setattr(extensions, 'call', lambda *a: None)
    assert store.query_error_groups()['error'] == 'extension_unavailable'


def test_error_window_excludes_older_events_and_large_bodies_stay_explicit(store, monkeypatch):
    from clawmetry import entitlements, extensions
    monkeypatch.setattr(entitlements, 'get_entitlement', lambda: SimpleNamespace(allows_feature=lambda name: True))
    monkeypatch.setattr(extensions, 'load_plugins', lambda: None)
    seen = []
    monkeypatch.setattr(extensions, 'call', lambda name, payload: seen.append(payload) or {'rows': []})
    events(store, count=2)
    store._conn.execute('UPDATE events SET created_at=? WHERE id=?',
                        [int(time.time() * 1000) - 9 * 86400000, 'node-a-codex-0'])
    store._conn.execute('UPDATE events SET data=? WHERE id=?',
                        [b'x' * 70000, 'node-a-codex-1'])
    result = store.query_error_groups(days=7)
    assert result['coverage']['events_scanned'] == 1
    assert result['coverage']['omitted_body_count'] == 1
    assert seen[0]['rows'][0]['body_omitted'] is True
    assert not seen[0]['rows'][0]['data']


def test_cli_seam_preserves_arguments_and_legacy_session_grammar(monkeypatch):
    from clawmetry import extensions
    from clawmetry.cli_cmds import _common, dispatch
    calls = []
    monkeypatch.setattr(extensions, 'load_plugins', lambda: None)
    monkeypatch.setattr(extensions, 'call', lambda name, payload: calls.append((name, payload)) or 0)
    assert dispatch(['sessions', 'watch', 'codex:s', '--json']) == 0
    assert calls == [('cli.sessions', {'argv': ['watch', 'codex:s', '--json']})]
    monkeypatch.setattr(_common, 'build_parser', lambda: SimpleNamespace(
        parse_args=lambda args: SimpleNamespace(_handler=lambda parsed: 6)))
    assert dispatch(['sessions', 'codex:s', '--transcript']) == 6
    assert len(calls) == 1


def test_cli_missing_extension_reports_gate_without_loading_dashboard(monkeypatch, capsys):
    from clawmetry import extensions
    from clawmetry.cli_cmds import dispatch
    monkeypatch.setattr(extensions, 'load_plugins', lambda: None)
    monkeypatch.setattr(extensions, 'call', lambda *args: None)
    assert dispatch(['sessions', 'list', '--json']) == 4
    output = capsys.readouterr()
    assert not output.out and 'upgrade_required' in output.err
