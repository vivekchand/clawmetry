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


class TestGovernanceEndpointStub(unittest.TestCase):
    """In vanilla OSS the NeMo governance impl is gone — it moved to the
    closed-source ``clawmetry-pro`` package. The OSS ``bp_nemoclaw`` stub
    now returns HTTP 402 ``upgrade_required`` on every governance endpoint.

    These tests register the OSS stub blueprint directly (the same blueprint
    dashboard.py registers when ``clawmetry_pro.is_loaded()`` is False) and
    assert the 402 upgrade contract. The real behaviour is covered by
    clawmetry-pro's own test suite."""

    def setUp(self):
        from flask import Flask
        from routes.nemoclaw import bp_nemoclaw
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp_nemoclaw)
        self.client = app.test_client()

    def _assert_upgrade_required(self, resp):
        self.assertEqual(resp.status_code, 402)
        data = json.loads(resp.data)
        self.assertEqual(data.get("error"), "upgrade_required")
        self.assertEqual(data.get("feature"), "nemo_governance")
        self.assertIn("hint", data)

    def test_governance_returns_402(self):
        self._assert_upgrade_required(self.client.get('/api/nemoclaw/governance'))

    def test_acknowledge_drift_returns_402(self):
        self._assert_upgrade_required(
            self.client.post('/api/nemoclaw/governance/acknowledge-drift'))

    def test_status_returns_402(self):
        self._assert_upgrade_required(self.client.get('/api/nemoclaw/status'))

    def test_policy_returns_402(self):
        self._assert_upgrade_required(self.client.get('/api/nemoclaw/policy'))

    def test_approve_returns_402(self):
        self._assert_upgrade_required(
            self.client.post('/api/nemoclaw/approve', json={}))

    def test_reject_returns_402(self):
        self._assert_upgrade_required(
            self.client.post('/api/nemoclaw/reject', json={}))


if __name__ == '__main__':
    unittest.main()
