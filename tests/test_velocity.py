"""
Token Velocity Alert tests.

Tests the token velocity detection system:
- API endpoint responses
- Alert triggering logic
- Configuration persistence
"""
import pytest
import requests


class TestVelocityAPI:
    """Test /api/velocity/* endpoints."""

    def test_velocity_status_accessible(self, api, base_url):
        """Velocity status endpoint returns expected keys."""
        r = api.get(f"{base_url}/api/velocity/status", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert 'enabled' in d
        assert 'alert_active' in d
        assert 'tokens_2min' in d
        assert 'tokens_2min_threshold' in d
        assert 'tokens_2min_pct' in d
        assert 'cost_5min' in d
        assert 'cost_5min_threshold' in d
        assert 'cost_5min_pct' in d

    def test_velocity_status_types(self, api, base_url):
        """Velocity status returns correct types."""
        d = api.get(f"{base_url}/api/velocity/status", timeout=10).json()
        assert isinstance(d['enabled'], bool)
        assert isinstance(d['alert_active'], bool)
        assert isinstance(d['tokens_2min'], (int, float))
        assert isinstance(d['tokens_2min_threshold'], (int, float))
        assert isinstance(d['tokens_2min_pct'], (int, float))
        assert isinstance(d['cost_5min'], (int, float))
        assert isinstance(d['cost_5min_threshold'], (int, float))
        assert isinstance(d['cost_5min_pct'], (int, float))

    def test_velocity_dismiss(self, api, base_url):
        """Dismiss velocity alert returns ok."""
        r = api.post(f"{base_url}/api/velocity/dismiss", timeout=10)
        assert r.status_code == 200
        d = r.json()
        assert d.get('ok') is True

    def test_velocity_dismiss_clears_alert(self, api, base_url):
        """After dismiss, alert_active should be False."""
        api.post(f"{base_url}/api/velocity/dismiss", timeout=10)
        d = api.get(f"{base_url}/api/velocity/status", timeout=10).json()
        assert d['alert_active'] is False


class TestVelocityConfig:
    """Test velocity configuration via budget config API."""

    def test_velocity_config_in_budget(self, api, base_url):
        """Budget config includes velocity settings."""
        d = api.get(f"{base_url}/api/budget/config", timeout=10).json()
        assert 'velocity_enabled' in d
        assert 'velocity_tokens_per_2min' in d
        assert 'velocity_cost_per_5min' in d

    def test_velocity_config_update(self, api, base_url):
        """Can update velocity thresholds via budget config."""
        r = api.post(f"{base_url}/api/budget/config", json={
            'velocity_tokens_per_2min': 10000,
            'velocity_cost_per_5min': 1.00,
        }, timeout=10)
        assert r.status_code == 200

        # Verify update persisted
        d = api.get(f"{base_url}/api/budget/config", timeout=10).json()
        assert float(d['velocity_tokens_per_2min']) == 10000.0
        assert float(d['velocity_cost_per_5min']) == 1.00

    def test_velocity_enable_disable(self, api, base_url):
        """Can toggle velocity alerts on/off."""
        # Disable
        api.post(f"{base_url}/api/budget/config", json={
            'velocity_enabled': False,
        }, timeout=10)
        d = api.get(f"{base_url}/api/budget/config", timeout=10).json()
        assert d['velocity_enabled'] is False

        # Re-enable
        api.post(f"{base_url}/api/budget/config", json={
            'velocity_enabled': True,
        }, timeout=10)
        d = api.get(f"{base_url}/api/budget/config", timeout=10).json()
        assert d['velocity_enabled'] is True

    def test_velocity_status_reflects_config(self, api, base_url):
        """Velocity status threshold matches config."""
        api.post(f"{base_url}/api/budget/config", json={
            'velocity_tokens_per_2min': 7500,
            'velocity_cost_per_5min': 0.75,
        }, timeout=10)
        d = api.get(f"{base_url}/api/velocity/status", timeout=10).json()
        assert d['tokens_2min_threshold'] == 7500.0
        assert d['cost_5min_threshold'] == 0.75

    def test_velocity_disabled_no_alert(self, api, base_url):
        """When velocity is disabled, no alert fires."""
        api.post(f"{base_url}/api/budget/config", json={
            'velocity_enabled': False,
        }, timeout=10)
        d = api.get(f"{base_url}/api/velocity/status", timeout=10).json()
        # Cannot be alerting if disabled
        assert d['alert_active'] is False

        # Restore
        api.post(f"{base_url}/api/budget/config", json={
            'velocity_enabled': True,
            'velocity_tokens_per_2min': 5000,
            'velocity_cost_per_5min': 0.50,
        }, timeout=10)
