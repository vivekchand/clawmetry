"""Unit tests for scripts/canary_verify.py.

Pins two behaviours that were missing when the first two P0 canary alarms fired:

1. ``trace`` must be in SUBCOMMANDS — the surface gap that let 0.12.760 ship
   without verifying the ``clawmetry trace`` entry point at all.

2. ``verify()`` must retry on "No matching distribution" before giving up —
   the CDN propagation race that turned a healthy release into a false P0.

These tests should fail on the pre-#5133 code (no retry, no ``trace``).

closes #5119
"""

from __future__ import annotations

import importlib.util
import os
from unittest.mock import patch

import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(REPO_ROOT, "scripts", "canary_verify.py")


def _load():
    spec = importlib.util.spec_from_file_location("canary_verify", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def cv():
    return _load()


# ── subcommand surface ───────────────────────────────────────────────────────


def test_trace_in_subcommands(cv):
    """Regression for the surface gap: canary must verify ``clawmetry trace``."""
    assert "trace" in cv.SUBCOMMANDS


def test_core_subcommands_present(cv):
    for sub in ("status", "sync", "connect", "uninstall", "trace"):
        assert sub in cv.SUBCOMMANDS, f"'{sub}' missing from SUBCOMMANDS"


# ── CDN retry logic ─────────────────────────────────────────────────────────


def _make_mock_run(fail_attempts: int):
    """Return a (mock_run, pip_call_counter) pair.

    The mock fails the first ``fail_attempts`` pip install calls with the
    "No matching distribution" error that CDN propagation lag produces, then
    succeeds. All other _run calls (venv create, import checks, --help) pass.
    """
    pip_calls = [0]

    def mock_run(cmd, timeout=300):
        is_pip_install = len(cmd) >= 3 and "pip" in cmd and "install" in cmd
        if is_pip_install:
            pip_calls[0] += 1
            if pip_calls[0] <= fail_attempts:
                return 1, "No matching distribution found for clawmetry==0.0.1"
            return 0, "Successfully installed clawmetry-0.0.1"
        return 0, "ok"

    return mock_run, pip_calls


def test_retries_once_on_cdn_miss(cv):
    """verify() must succeed when the first pip attempt misses the CDN."""
    mock_run, pip_calls = _make_mock_run(fail_attempts=1)

    with patch.object(cv, "_run", side_effect=mock_run), patch("time.sleep"):
        failures = cv.verify("0.0.1", verbose=False)

    assert failures == [], f"Expected no failures but got: {failures}"
    assert pip_calls[0] == 2, f"Expected 2 pip attempts, got {pip_calls[0]}"


def test_fails_after_max_retries(cv):
    """verify() must return a failure after 5 consecutive CDN misses."""
    mock_run, pip_calls = _make_mock_run(fail_attempts=5)

    with patch.object(cv, "_run", side_effect=mock_run), patch("time.sleep"):
        failures = cv.verify("0.0.1", verbose=False)

    assert any("FAILED" in f for f in failures), (
        f"Expected a pip FAILED entry in failures but got: {failures}"
    )
    assert pip_calls[0] == 5, f"Expected 5 pip attempts, got {pip_calls[0]}"


def test_succeeds_immediately_when_cdn_ready(cv):
    """verify() must not retry when the first pip install succeeds."""
    mock_run, pip_calls = _make_mock_run(fail_attempts=0)

    with patch.object(cv, "_run", side_effect=mock_run), patch("time.sleep"):
        failures = cv.verify("0.0.1", verbose=False)

    assert failures == [], f"Expected no failures but got: {failures}"
    assert pip_calls[0] == 1, f"Expected 1 pip attempt, got {pip_calls[0]}"
