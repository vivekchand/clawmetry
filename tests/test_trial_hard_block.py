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

    @staticmethod
    def _plan_path():
        """The path the RESOLVER actually reads.

        ``entitlements._CLOUD_PLAN_CACHE`` is expanded at import time, so if
        any earlier test in the session imported the module under a different
        HOME it is pinned to that old directory. Deriving the path from
        ``$HOME`` here instead would write somewhere the resolver never looks
        — the test then passes alone and fails in the full suite, which is
        exactly how it behaved before this was fixed."""
        from clawmetry import entitlements
        return entitlements._CLOUD_PLAN_CACHE

    def _write_cloud_plan(self, **fields):
        """Stamp the cloud-plan cache (what the daemon writes from the
        heartbeat) and drop the resolver cache so the next request sees it."""
        import json
        p = self._plan_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            json.dump(fields, fh)
        self._invalidate()

    def _clear_cloud_plan(self):
        try:
            os.remove(self._plan_path())
        except OSError:
            pass
        self._invalidate()

    def test_never_trialed_install_is_never_blocked(self):
        """A fresh ``pip install clawmetry`` with no license and no trial is
        the permanent free tier, NOT a lapsed one. Blocking it would brick
        every new install on day one (the 2026-08-06 regression)."""
        os.environ["CLAWMETRY_HARD_BLOCK"] = "1"
        self._clear_cloud_plan()
        try:
            resp = self._client.get("/api/sessions")
            self.assertNotEqual(
                resp.status_code, 402,
                "a never-trialed install must NEVER be hard-blocked")
        finally:
            os.environ["CLAWMETRY_HARD_BLOCK"] = "0"
            self._clear_cloud_plan()

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
        the overlay JS keys off.

        "Blocked" means a CONSUMED trial whose end date has passed —
        ``trial_used`` + a past ``expiry``, exactly what the daemon writes
        into cloud_plan.json from the heartbeat's users.trial_used /
        users.trial_end. An empty HOME is a never-trialed install and is
        deliberately NOT blocked (see
        test_never_trialed_install_is_never_blocked)."""
        import time as _t
        os.environ["CLAWMETRY_HARD_BLOCK"] = "1"
        self._write_cloud_plan(
            plan="cloud_free", node_limit=1,
            expiry=_t.time() - 2 * 86400.0,
            trial_end=_t.time() - 2 * 86400.0,
            trial_used=True,
        )
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
            # Clear the lapsed-trial cache too, or it leaks into every test
            # that runs after this one in the shared temp HOME.
            self._clear_cloud_plan()

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
