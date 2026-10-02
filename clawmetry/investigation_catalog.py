"""Bounded persisted session discovery and the entitled error-group seam.

Filters apply before limits. Aggregates describe the returned window only;
the private extension computes fingerprints and never writes resolution state.
"""
from __future__ import annotations

import time


class InvestigationCatalogMixin:
    def query_session_catalog(self, *, node_id=None, runtime=None, session_id=None, limit=100):
        from clawmetry.activity_store import _scope, _where
        from clawmetry.local_store import _runtime_of_session_id
        scope = _scope(node_id, runtime, session_id)
        where, params = _where(scope)
        lim = max(1, min(int(limit), 200))
        cols = ('session_id', 'node_id', 'agent_type', 'title', 'status', 'outcome',
                'started_at', 'last_active_at', 'ended_at')
        rows = self._fetch('SELECT ' + ','.join(cols) + ' FROM sessions WHERE ' + where +
                           ' ORDER BY updated_at DESC,session_id LIMIT ?', [*params, lim + 1])
        result = []
        for values in rows[:lim]:
            row = dict(zip(cols, values))
            fallback = row['agent_type']
            if fallback in ('main', 'subagent', 'cron', '', None):
                fallback = 'openclaw'
            row['runtime'] = _runtime_of_session_id(row['session_id'], fallback)
            if row['ended_at'] and row['status'] in (None, '', 'active', 'running'):
                row['status'] = 'ended'
            result.append(row)
        return {'schema_version': 1, 'scope': scope, 'rows': result,
                'coverage': {'source': 'persisted_sessions', 'limit': lim,
                             'truncated': len(rows) > lim, 'node_reachable': True}}

    def query_error_groups(self, *, node_id=None, runtime=None, session_id=None, days=7, limit=500):
        from clawmetry import entitlements, extensions
        from clawmetry.activity_store import _scope, _where
        from clawmetry.local_store import _EVENT_COLS, _row_to_event
        from clawmetry.retention import resolve
        scope = _scope(node_id, runtime, session_id)
        body = {'schema_version': 1, 'scope': scope, 'rows': [], 'available': False}
        # Gate here as well as on the route: encrypted daemon reads use this
        # same method without passing through the dashboard's Flask decorator.
        if not entitlements.get_entitlement().allows_feature('error_triage'):
            return dict(body, error='upgrade_required', reason='Error grouping requires an entitled plan.')
        extensions.load_plugins()
        days, lim = max(1, min(int(days), 90)), max(1, min(int(limit), 1000))
        now = int(time.time() * 1000)
        retention_days = resolve(store=self)['effective_days']
        cutoff = now - min(days, retention_days if retention_days is not None else days) * 86_400_000
        where, params = _where(scope)
        # Payload bytes are capped before materialization. Omitted bodies are
        # explicit, unique observations, never normalized partial messages.
        columns = ["CASE WHEN octet_length(data)<=65536 THEN data ELSE NULL END" if c == 'data' else c
                   for c in _EVENT_COLS]
        cols = [*_EVENT_COLS, 'tool_name', 'body_omitted']
        source = self._fetch('SELECT ' + ','.join(columns) +
                            ',tool_name,COALESCE(octet_length(data)>65536,FALSE) FROM events '
                            f'WHERE {where} AND created_at>=? AND created_at<=? '
                            "AND (is_error=TRUE OR event_type LIKE 'error.%' OR event_type LIKE '%.failed') "
                            'ORDER BY created_at DESC,id DESC LIMIT ?', [*params, cutoff, now, lim + 1])
        rows = [_row_to_event(row, cols) for row in source[:lim]]
        ids = [row['id'] for row in rows]
        resolved = {}
        if ids:
            markers = self._fetch('SELECT event_id,resolved_at FROM resolved_errors WHERE event_id IN (' +
                                  ','.join('?' for _ in ids) + ')', ids)
            resolved = {eid: {'resolved_at': at} for eid, at in markers}
        groups = extensions.call('investigations.error_groups', {'rows': rows, 'resolved': resolved})
        if not isinstance(groups, dict):
            return dict(body, error='extension_unavailable', reason='Update the paid extension on this node to read error groups.')
        return dict(body, **groups, available=True, coverage={
            'node_reachable': True, 'source': 'persisted_errors', 'from_ms': cutoff, 'to_ms': now,
            'requested_days': days, 'retention_days': retention_days, 'limit': lim,
            'truncated': len(source) > lim, 'events_scanned': len(rows),
            'counts_basis': 'selected_window_only',
            'error_basis': 'typed_error_flag_or_explicit_error_event',
            'omitted_body_count': sum(bool(row.get('body_omitted')) for row in rows),
        })
