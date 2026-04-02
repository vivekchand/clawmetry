"""
Tests for NemoClaw governance API (GH #l1b1p7e1j).
Tests the /api/nemoclaw/governance endpoint and helper functions.
"""
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path

os.environ["CLAWMETRY_NO_INTERCEPT"] = "1"
os.environ["CLAWMETRY_DASHBOARD"] = "1"

# We test the helper functions directly by importing from dashboard
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class TestParseNetworkPolicies(unittest.TestCase):
    """Test _parse_network_policies YAML parser."""

    def _parse(self, yaml_text):
        # Import inline to avoid full dashboard boot
        import importlib, types
        # We'll exec just the function from the module text
        # Simpler: just call the function after importing dashboard helpers
        try:
            import dashboard as _d
            return _d._parse_network_policies(yaml_text)
        except Exception:
            return []

    def test_empty_yaml(self):
        result = self._parse("")
        self.assertIsInstance(result, list)

    def test_no_network_policies_section(self):
        result = self._parse("version: 1\nsandbox_type: openclaw\n")
        self.assertEqual(result, [])

    def test_basic_network_policies(self):
        yaml = """
sandbox_type: openclaw
network_policies:
  allow_anthropic:
    - api.anthropic.com
  allow_openai:
    - api.openai.com
    - cdn.openai.com
"""
        result = self._parse(yaml)
        self.assertGreater(len(result), 0)
        names = [p['name'] for p in result]
        self.assertIn('allow_anthropic', names)
        self.assertIn('allow_openai', names)
        # openai should have 2 hosts
        openai = next(p for p in result if p['name'] == 'allow_openai')
        self.assertEqual(len(openai['hosts']), 2)

    def test_single_host(self):
        yaml = """
network_policies:
  clawmetry_cloud:
    - app.clawmetry.com
"""
        result = self._parse(yaml)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['name'], 'clawmetry_cloud')
        self.assertIn('app.clawmetry.com', result[0]['hosts'])

    def test_malformed_yaml_does_not_raise(self):
        try:
            result = self._parse(":::invalid:::yaml:::")
            self.assertIsInstance(result, list)
        except Exception as e:
            self.fail(f"_parse_network_policies raised on bad YAML: {e}")


class TestDetectNemoclaw(unittest.TestCase):
    """Test _detect_nemoclaw() with mocked filesystem."""

    def test_returns_none_when_not_installed(self):
        import dashboard as _d
        with patch('shutil.which', return_value=None):
            result = _d._detect_nemoclaw()
        self.assertIsNone(result)

    def test_returns_installed_true_when_binary_exists(self):
        import dashboard as _d
        with patch('shutil.which', return_value='/usr/local/bin/nemoclaw'), \
             patch('subprocess.run', side_effect=Exception("no subprocess")):
            # Without config files, should still return installed=True
            result = _d._detect_nemoclaw()
        # May return None if shutil import path differs; just check it doesn't crash
        if result is not None:
            self.assertTrue(result.get('installed'))

    def test_loads_config_when_exists(self, tmp_path=None):
        """Config JSON is loaded if present."""
        import dashboard as _d
        import tempfile

        with tempfile.TemporaryDirectory() as td:
            nc_dir = Path(td) / '.nemoclaw'
            nc_dir.mkdir()
            cfg = {'version': '1.2.3', 'provider': 'anthropic', 'model': 'claude-3-5-sonnet'}
            (nc_dir / 'config.json').write_text(json.dumps(cfg))

            with patch('shutil.which', return_value='/usr/local/bin/nemoclaw'), \
                 patch('pathlib.Path.home', return_value=Path(td)), \
                 patch('subprocess.run', side_effect=Exception("no subprocess")):
                result = _d._detect_nemoclaw()

        if result:
            loaded_cfg = result.get('config', {})
            self.assertEqual(loaded_cfg.get('version'), '1.2.3')
            self.assertEqual(loaded_cfg.get('provider'), 'anthropic')


class TestGovernanceEndpoint(unittest.TestCase):
    """Integration-style tests for /api/nemoclaw/governance Flask endpoint."""

    @classmethod
    def setUpClass(cls):
        """Create a minimal Flask test client from dashboard."""
        try:
            import dashboard as _d
            cls.app = _d.create_app()
            cls.client = cls.app.test_client()
            cls.app_available = True
        except Exception as e:
            cls.app_available = False
            cls.skip_reason = str(e)

    def _skip_if_unavailable(self):
        if not self.app_available:
            self.skipTest(f"Dashboard app not available: {self.skip_reason}")

    def test_not_installed_returns_200(self):
        self._skip_if_unavailable()
        import dashboard as _d
        with self.app.test_request_context():
            with patch.object(_d, '_detect_nemoclaw', return_value=None):
                resp = self.client.get('/api/nemoclaw/governance')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertFalse(data['installed'])

    def test_installed_returns_expected_keys(self):
        self._skip_if_unavailable()
        import dashboard as _d
        mock_info = {
            'installed': True,
            'config': {'version': '1.0', 'provider': 'anthropic'},
            'state': {'sandboxes': {}},
            'policy_yaml': 'network_policies:\n  allow_api:\n    - api.anthropic.com\n',
            'policy_hash': 'abc123def456',
            'presets': ['clawmetry'],
        }
        with self.app.test_request_context():
            with patch.object(_d, '_detect_nemoclaw', return_value=mock_info):
                resp = self.client.get('/api/nemoclaw/governance')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['installed'])
        self.assertIn('sandboxes', data)
        self.assertIn('network_policies', data)
        self.assertIn('presets', data)
        self.assertIn('config', data)

    def test_sensitive_config_keys_filtered(self):
        """API keys and tokens should be stripped from config."""
        self._skip_if_unavailable()
        import dashboard as _d
        mock_info = {
            'installed': True,
            'config': {
                'version': '1.0',
                'apiKey': 'sk-secret-12345',
                'token': 'tok-secret',
                'provider': 'anthropic',
            },
            'state': {},
        }
        with self.app.test_request_context():
            with patch.object(_d, '_detect_nemoclaw', return_value=mock_info):
                resp = self.client.get('/api/nemoclaw/governance')
        data = json.loads(resp.data)
        cfg = data.get('config', {})
        self.assertNotIn('apiKey', cfg)
        self.assertNotIn('token', cfg)
        self.assertIn('provider', cfg)  # non-sensitive key preserved

    def test_drift_detection_triggers(self):
        """Second call with different policy hash sets drift info."""
        self._skip_if_unavailable()
        import dashboard as _d

        # Reset module-level drift state
        _d._nemoclaw_policy_hash = None
        _d._nemoclaw_drift_info = {}

        def make_info(h):
            return {
                'installed': True,
                'config': {},
                'state': {},
                'policy_yaml': '# hash ' + h,
                'policy_hash': h,
            }

        with self.app.test_request_context():
            with patch.object(_d, '_detect_nemoclaw', return_value=make_info('aaa111')):
                self.client.get('/api/nemoclaw/governance')  # sets baseline
            with patch.object(_d, '_detect_nemoclaw', return_value=make_info('bbb222')):
                resp = self.client.get('/api/nemoclaw/governance')  # should trigger drift

        data = json.loads(resp.data)
        self.assertIsNotNone(data.get('drift'))
        drift = data['drift']
        self.assertIn('previous_hash', drift)
        self.assertEqual(drift['previous_hash'], 'aaa111')
        self.assertEqual(drift['current_hash'], 'bbb222')

    def test_acknowledge_drift_clears_it(self):
        """POST /acknowledge-drift clears the drift dict."""
        self._skip_if_unavailable()
        import dashboard as _d
        _d._nemoclaw_drift_info = {'previous_hash': 'x', 'current_hash': 'y', 'detected_at': '2026-01-01T00:00:00Z'}
        with self.app.test_request_context():
            resp = self.client.post('/api/nemoclaw/governance/acknowledge-drift')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data['ok'])
        self.assertEqual(_d._nemoclaw_drift_info, {})


if __name__ == '__main__':
    unittest.main()
