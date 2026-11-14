import importlib.util
from pathlib import Path
import tempfile
import subprocess
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('runtime_compatibility', ROOT / 'scripts/ci/runtime_compatibility.py')
ci = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ci)


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.runtimes = {'codex': {}, 'cursor': {}, 'openclaw': {}}

    def test_adapter_edit_runs_that_runtime_on_the_three_os_matrix(self):
        self.assertEqual(ci.affected_runtimes(['clawmetry_pro/adapters/codex.py'], self.runtimes), ['codex'])
        self.assertEqual(set(ci.OPERATING_SYSTEMS), {'ubuntu-latest', 'windows-latest', 'macos-latest'})

    def test_fixtures_and_alternate_test_names_select_their_runtime(self):
        paths = ['tests/fixtures/runtimes/cursor/REAL/state.vscdb', 'tests/test_adapter_codex.py']
        self.assertEqual(ci.affected_runtimes(paths, self.runtimes), ['codex', 'cursor'])
        self.assertEqual(ci.affected_runtimes(['tests/test_codex_runtime_adapter.py'], self.runtimes), ['codex'])

    def test_shared_unknown_and_new_runtime_paths_fail_open_to_full_coverage(self):
        for path in ['clawmetry_pro/__init__.py', 'pyproject.toml', 'new_module.py',
                     'clawmetry_pro/adapters/new_runtime.py']:
            with self.subTest(path=path):
                self.assertEqual(ci.affected_runtimes([path], self.runtimes), sorted(self.runtimes))

    def test_only_explicit_cosmetic_paths_skip_heavy_tests(self):
        self.assertEqual(ci.affected_runtimes(['README.md', 'CHANGELOG.md'], self.runtimes), [])
        self.assertEqual(ci.affected_runtimes(['docs/schema.md'], self.runtimes), sorted(self.runtimes))

    def test_openclaw_special_suites_narrow_and_non_python_lookalikes_do_not(self):
        for name in ci.OPENCLAW_EXTRA_TESTS:
            self.assertEqual(ci.affected_runtimes(['tests/' + name], self.runtimes), ['openclaw'])
        for name in ['test_codex_adapter_old', 'test_codex_adapter.md']:
            self.assertEqual(ci.affected_runtimes(['tests/' + name], self.runtimes), sorted(self.runtimes))

    def test_selection_and_discovery_use_identical_test_patterns(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            for name in ['test_codex_adapter.py', 'test_codex_adapter_replay.py',
                         'test_adapter_codex.py', 'test_codex_runtime_adapter.py',
                         *ci.OPENCLAW_EXTRA_TESTS]:
                path = root / 'tests' / name
                path.touch()
            for runtime in self.runtimes:
                for path in ci.runtime_tests(root, runtime):
                    relative = Path(path).relative_to(root).as_posix()
                    self.assertEqual(ci.affected_runtimes([relative], self.runtimes), [runtime])

    def test_paths_cannot_escape_checkout(self):
        for path in ['/tmp/a.py', '../a.py']:
            with self.assertRaises(ValueError):
                ci.affected_runtimes([path], self.runtimes)

    def test_catalogue_is_discovered_and_duplicate_entries_fail(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'catalogue'
            path.write_text('COUNT = 2\ncodex\tCodex\tpaid\t/x\nopenclaw\tOpenClaw\tfree\t/y\n')
            self.assertEqual(set(ci.catalogue(path)), {'codex', 'openclaw'})
            path.write_text(path.read_text() + 'codex\tCodex\tpaid\t/x\n')
            with self.assertRaises(ValueError):
                ci.catalogue(path)


class ExecutionTests(unittest.TestCase):
    def test_paid_runtime_cannot_pass_using_only_a_bundled_oss_suite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'oss/tests').mkdir(parents=True)
            (root / 'oss/tests/test_codex_adapter.py').touch()
            result = ci.run_runtime(root / 'oss', root / 'pro', 'codex', root / 'logs', require_pro_tests=True)
            self.assertEqual(result['status'], 'missing-coverage')

    def test_successful_exit_cannot_reuse_a_stale_junit_report(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'tests/test_codex_adapter.py').touch()
            (root / 'logs').mkdir()
            (root / 'logs/codex-pro.xml').write_text('<testsuite><testcase/></testsuite>')
            with mock.patch.object(ci.subprocess, 'run', return_value=mock.Mock(returncode=0)):
                self.assertEqual(ci.run_runtime(root, root, 'codex', root / 'logs')['status'], 'failed')
    def test_repository_conftests_run_in_separate_processes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for label in ['oss', 'pro']:
                (root / label / 'tests').mkdir(parents=True)
                (root / label / 'tests/test_goose_adapter.py').touch()
            def pytest(command, **kwargs):
                paths = [Path(p) for p in command if p.endswith('.py')]
                self.assertEqual({p.parents[1] for p in paths}, {kwargs['cwd']})
                report = next(p.split('=', 1)[1] for p in command if p.startswith('--junitxml='))
                Path(report).write_text('<testsuite><testcase/></testsuite>')
                return mock.Mock(returncode=0)
            with mock.patch.object(ci.subprocess, 'run', side_effect=pytest) as run:
                result = ci.run_runtime(root / 'oss', root / 'pro', 'goose', root / 'logs')
            self.assertEqual(result['status'], 'passed')
            self.assertEqual(run.call_count, 2)
    def test_junit_entity_expansion_is_rejected_for_utf8_and_utf16(self):
        xml = '<!DOCTYPE x [<!ENTITY x "private">]><testsuite><testcase>&x;</testcase></testsuite>'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'private.xml'
            for encoding in ('utf-8', 'utf-16'):
                path.write_bytes(xml.encode(encoding))
                with self.subTest(encoding=encoding), self.assertRaisesRegex(ValueError, 'DTD'):
                    ci.executed_cases(path)

    def test_junit_counts_only_executed_cases_and_rejects_malformed_reports(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'private.xml'
            path.write_text('<testsuite><testcase/><testcase><skipped/></testcase></testsuite>')
            self.assertEqual(ci.executed_cases(path), 1)
            path.write_text('<testsuite><testcase>')
            with self.assertRaises(ci.expat.ExpatError):
                ci.executed_cases(path)

    def test_private_checkout_never_persists_or_prints_credentials(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(ci.subprocess, 'run') as run, mock.patch.dict(
                    ci.os.environ, {'PRO_REPO_READ_TOKEN': 'private-value'}):
                run.return_value.returncode = 0
                result = ci.checkout_private(root / 'pro', 'a' * 40, root / 'logs')
                calls = run.call_args_list
                self.assertEqual(result, {'candidate_sha': 'a' * 40})
                for call in calls:
                    self.assertNotIn('private-value', str(call.args))
                    self.assertEqual(call.kwargs['env']['GIT_CONFIG_COUNT'], '3')
                    self.assertIn('stdout', call.kwargs)
                self.assertIn('https://github.com/vivekchand/clawmetry-pro.git', calls[1].args[0])
                self.assertNotIn('private-value', (root / 'logs/checkout.log').read_text())
                git_env = calls[-1].kwargs['env']
            # Git matches URL path components, so omitting .git from the
            # credential scope silently prevents authentication on real fetches.
            match = subprocess.run(['git', 'config', '--get-urlmatch', 'http.extraheader',
                                    'https://github.com/vivekchand/clawmetry-pro.git'],
                                   env=git_env, capture_output=True, text=True)
            self.assertEqual(match.returncode, 0)
            self.assertEqual(match.stdout.strip(), git_env['GIT_CONFIG_VALUE_0'])
            for key, expected in [('core.autocrlf', 'false'), ('core.longpaths', 'true')]:
                effective = subprocess.check_output(['git', 'config', '--get', key], env=git_env, text=True)
                self.assertEqual(effective.strip(), expected)

    def test_checkout_failure_withholds_raw_git_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with mock.patch.object(ci.subprocess, 'run') as run, mock.patch.dict(
                    ci.os.environ, {'PRO_REPO_READ_TOKEN': 'private-value'}):
                run.return_value.returncode = 1
                with self.assertRaisesRegex(ValueError, 'raw output is withheld'):
                    ci.checkout_private(root / 'pro', 'a' * 40, root / 'logs')
                self.assertEqual(run.call_count, 1)

    def test_all_skipped_suite_cannot_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'tests/test_codex_adapter.py').write_text('')
            logs = root / 'logs'
            logs.mkdir()
            def skipped(command, **kwargs):
                report = next(p.split('=', 1)[1] for p in command if p.startswith('--junitxml='))
                Path(report).write_text('<testsuites><testsuite><testcase><skipped/></testcase></testsuite></testsuites>')
                return mock.Mock(returncode=0)
            with mock.patch.object(ci.subprocess, 'run', side_effect=skipped):
                self.assertEqual(ci.run_runtime(root, root, 'codex', logs)['status'], 'unverified')

    def test_unknown_file_changes_invalidate_success_fingerprint(self):
        with mock.patch.object(ci, 'git_index') as files:
            files.return_value = ['100644 abc 0\tnew_shared_helper.py']
            before = ci.fingerprint(Path('oss'), Path('pro'))
            files.return_value = ['100644 def 0\tnew_shared_helper.py']
            self.assertNotEqual(before, ci.fingerprint(Path('oss'), Path('pro')))

    def test_missing_suite_is_a_failure_not_a_registration_only_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = ci.run_runtime(root, root, 'codex', root / 'logs')
            self.assertEqual(result['status'], 'missing-coverage')

    def test_private_failure_output_and_credentials_are_not_published(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'tests').mkdir()
            (root / 'tests/test_codex_adapter.py').write_text('')
            with mock.patch.object(ci.subprocess, 'run') as run, mock.patch.dict(
                    ci.os.environ, {'GITHUB_TOKEN': 'private-value',
                                    'GITHUB_STEP_SUMMARY': '/tmp/public-summary',
                                    'GITHUB_OUTPUT': '/tmp/public-outputs'}):
                run.return_value.returncode = 1
                result = ci.run_runtime(root, root, 'codex', root / 'logs')
                self.assertNotIn('GITHUB_TOKEN', run.call_args.kwargs['env'])
                self.assertNotIn('GITHUB_STEP_SUMMARY', run.call_args.kwargs['env'])
                self.assertNotIn('GITHUB_OUTPUT', run.call_args.kwargs['env'])
                self.assertNotIn('private-value', str(result))
                self.assertEqual(set(result), {'runtime', 'mode', 'status'})
                self.assertEqual(result['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
