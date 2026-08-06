"""tests/test_trial_hard_block.py

Guard test for the trial-end hard-block gate (clawmetry/trial_enforcement.py
+ dashboard.py before_request). Kept intentionally lightweight so it does
not need the full pytest server fixture — spins the Flask app up in-process
via test_client() and drives the gate through env-var toggling.

The class of bug this catches (2026-08-06 audit):
  * A regression that lets an unpaid / expired install through to /api/*
    (would leak the paid runtime observability surface to a lapsed user).
  * A regression that 402s a paying customer with a valid signed license
    (would brick every legitimate self-hosted install).
  * A regression that breaks the allowlist (would prevent the paywall
    overlay from loading its own status endpoint and permanently strand
    the user with no way to activate a license).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
import unittest

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)


class TrialHardBlockGateTest(unittest.TestCase):
    """Behaviour tests for the hard-block gate. Each test manages its own
    ``CLAWMETRY_HARD_BLOCK`` state so the ordering doesn't matter."""

    @classmethod
    def setUpClass(cls):
        # Redirect ~/.clawmetry to a tmp dir so the test never touches the
        # developer's real license or cloud-plan cache.
        cls._tmp = tempfile.mkdtemp(prefix="cm_hbtest_")
        cls._prev_home = os.environ.get("HOME")
        os.environ["HOME"] = cls._tmp
        # Register the app once — subsequent tests reuse the same test_client.
        import dashboard  # noqa: E402  (test-scoped import)
        ns = argparse.Namespace(
            log_dir=None, data_dir=None, workspace=None, memory_dir=None,
            sessions_dir=None, name=None, openclaw_dir=None,
        )
        try:
            dashboard.detect_config(ns)
        except Exception:
            # detect_config is idempotent in practice; a second call in the
            # same process raises "blueprint already registered". Fine for
            # this test — the app is already set up.
            pass
        cls._client = dashboard.app.test_client()

    @classmethod
    def tearDownClass(cls):
        if cls._prev_home is not None:
            os.environ["HOME"] = cls._prev_home
        else:
            os.environ.pop("HOME", None)
        try:
            shutil.rmtree(cls._tmp)
        except Exception:
            pass

    def _invalidate(self):
        from clawmetry import entitlements
        entitlements.invalidate()

    def test_default_is_enabled(self):
        """Founder policy: block is default-ON. Only an explicit opt-out
        env value disables it."""
        os.environ.pop("CLAWMETRY_HARD_BLOCK", None)
        from clawmetry import trial_enforcement as te
        self.assertTrue(te.hard_block_enabled(),
                        "hard_block_enabled must default to True")

        for opt in ("0", "false", "no", "off", "FALSE", "Off"):
            os.environ["CLAWMETRY_HARD_BLOCK"] = opt
            self.assertFalse(te.hard_block_enabled(),
                             f"hard_block_enabled({opt!r}) must be False")

        for on in ("1", "true", "yes", "on", "anything-else"):
            os.environ["CLAWMETRY_HARD_BLOCK"] = on
            self.assertTrue(te.hard_block_enabled(),
                            f"hard_block_enabled({on!r}) must be True")

        os.environ.pop("CLAWMETRY_HARD_BLOCK", None)

    def test_allowlist_stays_reachable_when_blocked(self):
        """Every path in the paywall overlay's dependency chain must stay
        reachable while blocked, or the user has no way to activate."""
        os.environ["CLAWMETRY_HARD_BLOCK"] = "1"
        self._invalidate()
        try:
            for path in ("/", "/api/trial/status", "/api/entitlement",
                         "/api/license/status", "/api/paywall/event",
                         "/api/version"):
                resp = self._client.get(path)
                self.assertNotEqual(
                    resp.status_code, 402,
                    f"{path} should NEVER 402 while blocked (allowlist)")
        finally:
            os.environ["CLAWMETRY_HARD_BLOCK"] = "0"
            self._invalidate()

    def test_non_allowlisted_returns_402_with_correct_body(self):
        """A blocked install must 402 non-allowlisted paths with the shape
        the overlay JS keys off."""
        os.environ["CLAWMETRY_HARD_BLOCK"] = "1"
        self._invalidate()
        try:
            resp = self._client.get("/api/sessions")
            self.assertEqual(
                resp.status_code, 402,
                "/api/sessions must 402 when hard-blocked; got "
                f"{resp.status_code}")
            self.assertEqual(
                resp.headers.get("X-Clawmetry-Trial-Blocked"), "1",
                "X-Clawmetry-Trial-Blocked header missing")
            body = resp.get_json() or {}
            self.assertIs(body.get("hard_blocked"), True,
                          "body.hard_blocked must be True")
            self.assertIn("upgrade_url", body,
                          "body.upgrade_url must be present")
            self.assertIn("activation_endpoint", body,
                          "body.activation_endpoint must be present")
            self.assertIn("refresh_endpoint", body,
                          "body.refresh_endpoint must be present")
        finally:
            os.environ["CLAWMETRY_HARD_BLOCK"] = "0"
            self._invalidate()

    def test_optout_lets_traffic_through(self):
        """The support opt-out (CLAWMETRY_HARD_BLOCK=0) must bypass the
        block even when the resolver would say unpaid/expired."""
        os.environ["CLAWMETRY_HARD_BLOCK"] = "0"
        self._invalidate()
        try:
            resp = self._client.get("/api/sessions")
            self.assertNotEqual(
                resp.status_code, 402,
                "/api/sessions must NOT 402 when CLAWMETRY_HARD_BLOCK=0")
        finally:
            self._invalidate()

    def test_entitlement_payload_carries_hard_blocked(self):
        """Entitlement.to_dict must include hard_blocked so the overlay can
        read the flag off /api/entitlement (same payload it already polls)."""
        from clawmetry import entitlements
        self._invalidate()
        d = entitlements.get_entitlement().to_dict()
        self.assertIn("hard_blocked", d,
                      "Entitlement.to_dict must expose 'hard_blocked'")
        self.assertIsInstance(d["hard_blocked"], bool)


if __name__ == "__main__":
    unittest.main()
