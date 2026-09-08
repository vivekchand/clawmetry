"""tests/test_trial_checkout.py

Guard tests for the direct-to-Stripe "Continue to payment" flow:

  * POST /api/trial/checkout mints a live per-account Stripe Checkout
    Session via the cloud when the node has an api_key, falls back to the
    heartbeat-cached checkout_url, then to the generic upgrade page — and
    ALWAYS answers 200 with a usable URL (the paywall CTA must never dead-end).
  * The sync daemon persists heartbeat {upgrade_url, checkout_url} to
    ~/.clawmetry/trial_state.json so the dashboard process (which cannot see
    the daemon's in-memory _TRIAL_STATE) resolves the per-account URL.
    Regression guard for the cross-process bug where resolved_upgrade_url()
    read sync._TRIAL_STATE in the dashboard process and only ever saw the
    module defaults.
  * block_payload advertises checkout_endpoint so the overlay knows where
    to ask.
"""

from __future__ import annotations

import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)


def _make_client():
    from flask import Flask
    from routes.trial import bp_trial

    app = Flask(__name__)
    app.register_blueprint(bp_trial)
    return app.test_client()


class TrialCheckoutEndpointTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="cm_checkout_")
        from clawmetry import trial_enforcement as te
        self._te = te
        self._state_path = os.path.join(self._tmp, "trial_state.json")
        self._patches = [
            mock.patch.object(te, "_TRIAL_STATE_PATH", self._state_path),
        ]
        for p in self._patches:
            p.start()
        os.environ.pop("CLAWMETRY_CHECKOUT_URL", None)
        os.environ.pop("CLAWMETRY_UPGRADE_URL", None)
        self._client = _make_client()

    def tearDown(self):
        for p in self._patches:
            p.stop()
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write_state(self, payload: dict):
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

    def test_falls_back_to_upgrade_url_with_no_account_and_no_cache(self):
        """A node that never ran `clawmetry connect` must still get a URL."""
        with mock.patch("routes.trial._local_api_key", return_value=""):
            resp = self._client.post("/api/trial/checkout")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["source"], "upgrade")
        self.assertTrue(body["url"].startswith("http"))

    def test_uses_heartbeat_cached_checkout_url(self):
        """A checkout_url the daemon persisted from a heartbeat wins over the
        generic upgrade page when the live session mint is unavailable."""
        self._write_state({"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_abc"})
        with mock.patch("routes.trial._local_api_key", return_value=""):
            resp = self._client.post("/api/trial/checkout")
        body = resp.get_json()
        self.assertEqual(body["source"], "cached")
        self.assertEqual(body["url"], "https://checkout.stripe.com/c/pay/cs_test_abc")

    def test_mints_live_session_when_account_linked(self):
        """With an api_key, the endpoint asks the cloud for a Stripe Checkout
        Session and returns its URL directly."""
        fake = io.BytesIO(json.dumps({
            "ok": True, "url": "https://checkout.stripe.com/c/pay/cs_live_123",
        }).encode())
        fake.read = fake.read  # urlopen context-manager duck type
        cm = mock.MagicMock()
        cm.__enter__.return_value = fake
        cm.__exit__.return_value = False
        with mock.patch("routes.trial._local_api_key", return_value="cm_key_x"), \
             mock.patch("urllib.request.urlopen", return_value=cm) as uo:
            resp = self._client.post("/api/trial/checkout")
        body = resp.get_json()
        self.assertEqual(body["source"], "session")
        self.assertEqual(body["url"], "https://checkout.stripe.com/c/pay/cs_live_123")
        req = uo.call_args[0][0]
        self.assertTrue(req.full_url.endswith("/api/billing/checkout-session"))
        self.assertEqual(req.get_header("X-api-key"), "cm_key_x")

    def test_cloud_failure_falls_back_not_500(self):
        """An old cloud without the endpoint (404 / network error) must fall
        back to the cached / generic URL, never surface an error."""
        self._write_state({"checkout_url": "https://checkout.stripe.com/c/pay/cs_test_fb"})
        with mock.patch("routes.trial._local_api_key", return_value="cm_key_x"), \
             mock.patch("urllib.request.urlopen", side_effect=OSError("boom")):
            resp = self._client.post("/api/trial/checkout")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertTrue(body["ok"])
        self.assertEqual(body["source"], "cached")

    def test_checkout_path_is_allowlisted_while_blocked(self):
        self.assertTrue(self._te.allowlisted_path("/api/trial/checkout"))

    def test_block_payload_advertises_checkout_endpoint(self):
        payload = self._te.block_payload(None)
        self.assertEqual(payload.get("checkout_endpoint"), "/api/trial/checkout")


class TrialStatePersistenceTest(unittest.TestCase):
    """The daemon → disk → dashboard handoff of the per-account URLs."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="cm_tstate_")
        self._state_path = os.path.join(self._tmp, "trial_state.json")

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def test_update_trial_state_persists_urls_for_dashboard_process(self):
        from clawmetry import sync
        from clawmetry import trial_enforcement as te

        with mock.patch.object(sync, "_TRIAL_STATE_FILE_PATH", self._state_path), \
             mock.patch.object(sync, "_persist_cloud_plan_to_disk"), \
             mock.patch.object(te, "_TRIAL_STATE_PATH", self._state_path):
            sync._update_trial_state({
                "sync_allowed": False,
                "plan": "trial_expired",
                "upgrade_url": "https://app.clawmetry.com/upgrade?acct=a1",
                "checkout_url": "https://checkout.stripe.com/c/pay/cs_hb_1",
            })
            self.assertTrue(os.path.isfile(self._state_path),
                            "heartbeat must persist trial_state.json")
            # The dashboard-process resolvers read the file, not sync memory.
            self.assertEqual(te.resolved_checkout_url(),
                             "https://checkout.stripe.com/c/pay/cs_hb_1")
            self.assertEqual(te.resolved_upgrade_url(),
                             "https://checkout.stripe.com/c/pay/cs_hb_1",
                             "checkout_url must win over upgrade_url")

    def test_env_override_beats_persisted_state(self):
        from clawmetry import trial_enforcement as te
        with open(self._state_path, "w", encoding="utf-8") as fh:
            json.dump({"checkout_url": "https://checkout.stripe.com/x"}, fh)
        with mock.patch.object(te, "_TRIAL_STATE_PATH", self._state_path), \
             mock.patch.dict(os.environ,
                             {"CLAWMETRY_CHECKOUT_URL": "https://support.example/fix"}):
            self.assertEqual(te.resolved_checkout_url(),
                             "https://support.example/fix")

    def test_missing_or_corrupt_state_file_is_harmless(self):
        from clawmetry import trial_enforcement as te
        with mock.patch.object(te, "_TRIAL_STATE_PATH", self._state_path):
            self.assertEqual(te.resolved_checkout_url(), "")
            with open(self._state_path, "w", encoding="utf-8") as fh:
                fh.write("{not json")
            self.assertEqual(te.persisted_trial_state(), {})


if __name__ == "__main__":
    unittest.main()
