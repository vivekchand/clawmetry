"""Guard: the C6 (apply-required-checks) push path must NEVER block main.

Regression for the red-main-on-every-merge bug: when only GITHUB_TOKEN (ghs_)
is available and branch protection is not yet configured, the script used to
`sys.exit(1)` as a "forcing signal", which turned main red on every push and
hid real failures. Push-triggered runs are informational only and must exit 0.

This test fails on the old code (SystemExit code 1) and passes on the fix.
"""
import importlib.util
import os
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "apply_required_status_checks.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("apply_required_status_checks", _SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_readonly_push_path_exits_zero_when_unconfigured(monkeypatch):
    mod = _load_module()

    # Simulate the Actions push context: GITHUB_TOKEN (ghs_ = read-only), this repo,
    # and NOT a manual confirm=APPLY dispatch.
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_readonlytoken")
    monkeypatch.setenv("GITHUB_REPOSITORY", "vivekchand/clawmetry")
    monkeypatch.delenv("CONFIRM_INPUT", raising=False)

    # Branch protection is NOT configured (the exact state that reddened main).
    # Stub the network read so the test is hermetic and deterministic.
    monkeypatch.setattr(mod, "verify_required_checks_readonly", lambda *a, **k: False)

    # main() must return normally (exit 0), never raise SystemExit with a code.
    try:
        result = mod.main()
    except SystemExit as exc:  # pragma: no cover - this is the bug we guard against
        pytest.fail(f"C6 push path raised SystemExit({exc.code!r}); it must be non-blocking (exit 0).")
    assert result is None


def test_confirm_apply_with_readonly_token_still_errors(monkeypatch):
    """A manual confirm=APPLY with only GITHUB_TOKEN should still fail loudly:
    that is a real misconfiguration, distinct from the informational push path."""
    mod = _load_module()
    monkeypatch.setenv("GITHUB_TOKEN", "ghs_readonlytoken")
    monkeypatch.setenv("GITHUB_REPOSITORY", "vivekchand/clawmetry")
    monkeypatch.setenv("CONFIRM_INPUT", "APPLY")

    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code not in (0, None)
