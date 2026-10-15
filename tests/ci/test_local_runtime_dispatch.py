import copy
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[2] / 'scripts/ci/local_runtime_dispatch.py')
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)
SHA, BASE = 'a' * 40, 'b' * 40
RUN = {'id': 7, 'head_sha': SHA, 'head_repository': {'full_name': bridge.SOURCE},
       'head_branch': 'feature', 'event': 'pull_request', 'status': 'completed', 'conclusion': 'success'}
STATUS = {'id': 42, 'context': bridge.CONTEXT, 'creator': {'login': 'github-actions[bot]'},
          'state': 'pending', 'description': f'CM_OSS_REQUEST:{BASE}:9:7-1'}


class BridgeTests(unittest.TestCase):
    def request(self):
        return bridge.request_from(RUN, STATUS)

    def test_status_lookup_preserves_creator_and_newest_context(self):
        with patch.object(bridge, 'api', return_value=[[{'context': 'other'}], [STATUS]]) as api:
            self.assertEqual(bridge.latest_status(SHA), STATUS)
            self.assertEqual(api.call_args.args[0], f'repos/{bridge.SOURCE}/commits/{SHA}/statuses')
            self.assertEqual(api.call_args.kwargs['query'], {'per_page': '100'})

    def test_rejects_untrusted_fork_and_malformed_markers(self):
        for change in ({'state': 'success'}, {'creator': {'login': 'someone'}},
                       {'description': 'CM_OSS_REQUEST:../../../private:9'},
                       {'description': f'CM_OSS_REQUEST:1234567890abcdef:{BASE}:9:7-1'},
                       {'description': f'CM_OSS_QUEUED:{BASE}:9:7-1'}):
            with self.subTest(change=change):
                self.assertIsNone(bridge.request_from(RUN, dict(STATUS, **change)))
        self.assertIsNone(bridge.request_from(dict(RUN, head_repository={'full_name': 'someone/fork'}), STATUS))
        self.assertIsNone(bridge.request_from(dict(RUN, head_sha='main'), STATUS))

    def test_claim_and_dispatch_preserve_exact_candidate(self):
        record = self.request()
        with patch.object(bridge, 'latest_status', return_value=STATUS), patch.object(bridge, 'api') as api:
            saves = []
            bridge.reconcile(record, [], 1000, lambda: saves.append(copy.deepcopy(record)))
            self.assertEqual(api.call_args_list[0].args[0], f'repos/{bridge.SOURCE}/statuses/{SHA}')
            body = api.call_args_list[1].kwargs['body']['client_payload']
            self.assertEqual(body['pro_sha'], SHA)
            self.assertEqual(body['base_sha'], BASE)
            self.assertEqual(body['pull_request'], 9)
            self.assertTrue(body['local_bridge'])
            self.assertEqual(body['request_id'], record['nonce'])
            self.assertEqual(saves[-1]['attempts'], 1)

    def test_marker_belongs_to_exact_producer_run_and_attempt(self):
        for run in (dict(RUN, id=8), dict(RUN, run_attempt=2)):
            self.assertIsNone(bridge.request_from(run, STATUS))
        self.assertIsNotNone(bridge.request_from(dict(RUN, run_attempt=2),
            dict(STATUS, description=f'CM_OSS_REQUEST:{BASE}:9:7-2')))

    def test_rerun_is_discovered_after_legacy_seen_run(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            bridge.save(path, {'requests': {}, 'seen': [7]})
            run = dict(RUN, run_attempt=2)
            status = dict(STATUS, description=f'CM_OSS_REQUEST:{BASE}:9:7-2')
            with patch.object(bridge, 'current_heads', return_value={'feature': SHA}), \
                    patch.object(bridge, 'runs', side_effect=[[run], []]), \
                    patch.object(bridge, 'latest_status', return_value=status), \
                    patch.object(bridge, 'api') as api:
                bridge.once(path)
                self.assertEqual(api.call_args.args[0], f'repos/{bridge.DESTINATION}/dispatches')
            state = __import__('json').loads(path.read_text())
            self.assertEqual(state['seen'], ['7:1', '7:2'])
            self.assertEqual(next(iter(state['requests'].values()))['producer_attempt'], 2)

    def test_uncertain_dispatch_does_not_duplicate_and_receipt_is_reused(self):
        record = self.request()
        record.update(claimed=True, attempts=1, last_dispatch=1000)
        status = dict(STATUS, description=bridge.queued_marker(record))
        with patch.object(bridge, 'latest_status', return_value=status), patch.object(bridge, 'api') as api:
            bridge.reconcile(record, [], 1100, lambda: None)
            api.assert_not_called()
            receipt = {'id': 123, 'display_title': bridge.title(record), 'status': 'in_progress'}
            bridge.reconcile(record, [receipt], 1500, lambda: None)
            api.assert_not_called()
            self.assertEqual(record['run_id'], 123)

    def test_real_conclusion_is_required_for_success(self):
        for conclusion, state in [('success', 'success'), ('failure', 'failure'), ('cancelled', 'failure'), ('timed_out', 'failure')]:
            with self.subTest(conclusion=conclusion):
                record = self.request()
                record['claimed'] = True
                status = dict(STATUS, description=bridge.queued_marker(record))
                receipt = {'id': 123, 'display_title': bridge.title(record), 'status': 'completed', 'conclusion': conclusion}
                with patch.object(bridge, 'latest_status', return_value=status), patch.object(bridge, 'api') as api:
                    bridge.reconcile(record, [receipt], 1000, lambda: None)
                    self.assertEqual(api.call_args.kwargs['body']['state'], state)
                    self.assertEqual(api.call_args.kwargs['body']['target_url'], f'https://github.com/{bridge.DESTINATION}/actions/runs/123')

    def test_dispatch_failure_persists_uncertainty_without_false_success(self):
        record = self.request()
        record['claimed'] = True
        status = dict(STATUS, description=bridge.queued_marker(record))
        with patch.object(bridge, 'latest_status', return_value=status), patch.object(bridge, 'api', side_effect=RuntimeError), self.assertRaises(RuntimeError):
            bridge.reconcile(record, [], 1000, lambda: None)
        self.assertEqual(record['attempts'], 1)
        self.assertEqual(record['last_dispatch'], 1000)
        self.assertNotIn('done', record)

    def test_old_request_cannot_overwrite_new_marker_on_same_sha(self):
        for claimed in (False, True):
            record = self.request()
            record['claimed'] = claimed
            with patch.object(bridge, 'latest_status', return_value=dict(STATUS, id=999)), patch.object(bridge, 'api') as api:
                bridge.reconcile(record, [], 1000, lambda: None)
                api.assert_not_called()
                self.assertEqual(record['done'], 'superseded')

    def test_retry_exhaustion_reports_failure(self):
        record = self.request()
        record.update(claimed=True, attempts=3)
        status = dict(STATUS, description=bridge.queued_marker(record))
        with patch.object(bridge, 'latest_status', return_value=status), patch.object(bridge, 'api') as api:
            bridge.reconcile(record, [], 1000, lambda: None)
            self.assertEqual(api.call_args.kwargs['body']['state'], 'failure')
            self.assertEqual(record['done'], 'failure')

    def test_state_is_atomic_and_private(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'state.json'
            bridge.save(path, {'requests': {}})
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertFalse(path.with_suffix('.tmp').exists())


    def test_automatic_superseded_candidate_never_dispatches(self):
        record = self.request()
        with patch.object(bridge, 'latest_status', return_value=STATUS), patch.object(bridge, 'api') as api:
            bridge.reconcile(record, [], 1000, lambda: None, current=False)
            api.assert_not_called()
            self.assertNotIn('done', record)
            bridge.reconcile(record, [], 1061, lambda: None, current=False)
            api.assert_called_once()
            self.assertEqual(api.call_args.args[0], f'repos/{bridge.SOURCE}/statuses/{SHA}')
            self.assertEqual(api.call_args.kwargs['body']['state'], 'failure')
            self.assertEqual(record['done'], 'superseded')

    def test_head_snapshot_race_waits_and_then_accepts_current_candidate(self):
        record = self.request()
        with patch.object(bridge, 'latest_status', return_value=STATUS), patch.object(bridge, 'api') as api:
            bridge.reconcile(record, [], 1000, lambda: None, current=False)
            bridge.reconcile(record, [], 1001, lambda: None, current=True)
            self.assertNotIn('done', record)
            self.assertNotIn('inactive_since', record)
            self.assertEqual(api.call_args.args[0], f'repos/{bridge.DESTINATION}/dispatches')

    def test_retry_replaces_old_success_with_actual_new_conclusion(self):
        record = self.request()
        record.update(manual=True, claimed=True, run_id=123, done='success', finished_attempt=1)
        target = f'https://github.com/{bridge.DESTINATION}/actions/runs/123'
        status = dict(STATUS, state='success', target_url=target)
        receipt = {'id': 123, 'display_title': bridge.title(record), 'status': 'completed',
                   'conclusion': 'failure', 'run_attempt': 2}
        with patch.object(bridge, 'latest_status', return_value=status) as latest, patch.object(bridge, 'api') as api:
            api.side_effect = [receipt, {}]
            observed = bridge.watch_reruns({'requests': {record['nonce']: record}}, {}, lambda: None)
            self.assertNotIn('done', record)
            self.assertEqual(api.call_args.kwargs['body']['state'], 'pending')
            api.side_effect = None
            latest.return_value = dict(STATUS, description=bridge.queued_marker(record))
            bridge.reconcile(record, list(observed.values()), 2000, lambda: None)
            self.assertEqual(api.call_args.kwargs['body']['state'], 'failure')
            self.assertEqual(record['done'], 'failure')
            self.assertEqual(record['finished_attempt'], 2)

    def test_old_rerun_cannot_overwrite_a_new_request_on_same_sha(self):
        record = self.request()
        record.update(manual=True, claimed=True, run_id=123, done='success')
        with patch.object(bridge, 'latest_status', return_value=STATUS), patch.object(bridge, 'api') as api:
            bridge.watch_reruns({'requests': {record['nonce']: record}}, {}, lambda: None)
            api.assert_not_called()
            self.assertEqual(record['done'], 'success')

    def test_branch_heads_are_read_from_every_graphql_page(self):
        def page(name, sha, more, cursor):
            return {'data': {'repository': {'refs': {
                'nodes': [{'name': name, 'target': {'oid': sha}}],
                'pageInfo': {'hasNextPage': more, 'endCursor': cursor}}}}}
        with patch.object(bridge, 'api', side_effect=[page('feature', SHA, True, 'next'),
                                                     page('main', BASE, False, None)]) as api:
            self.assertEqual(bridge.current_heads(), {'feature': SHA, 'main': BASE})
            self.assertEqual(api.call_args_list[1].kwargs['body']['variables']['cursor'], 'next')
            self.assertTrue(all(call.args == ('graphql',) for call in api.call_args_list))


if __name__ == '__main__':
    unittest.main()
