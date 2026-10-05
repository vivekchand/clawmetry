"""A billing state cannot take away an already configured physical stop."""

import pytest

from clawmetry.trial_enforcement import allowlisted_path


@pytest.mark.parametrize('path', [
    '/robotics', '/api/robotics/control', '/api/robotics/control/stop',
    '/robotics/assets/app.js', '/robotics/assets/style.css',
    '/robotics/assets/pose.js', '/robotics/assets/playback.js',
    '/robotics/assets/hardware.json',
])
def test_established_stop_surface_survives_trial_expiry(path):
    assert allowlisted_path(path)


@pytest.mark.parametrize('path', [
    '/api/robotics/control/reset', '/api/robotics/control/stop-other',
    '/api/robotics/runs', '/api/robotics/inventory',
    '/api/robotics/runs/' + 'a' * 32 + '/events',
    '/robotics/assets/arbitrary.js',
])
def test_stop_exception_does_not_unlock_paid_data_or_restart(path):
    assert not allowlisted_path(path)
