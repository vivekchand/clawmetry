"""Tests for /api/usage/cache-trends — prompt-cache hit-rate analytics (GH #851)."""

import json
import os
import tempfile
import time
import unittest
from unittest.mock import patch


class TestCacheTrends(unittest.TestCase):
    """Drive the endpoint with a synthetic JSONL transcript."""

    @classmethod
    def setUpClass(cls):
        try:
            import argparse
            import dashboard as _d
            # detect_config registers blueprints onto the module-level Flask app.
            # It expects a namespace with the standard CLI fields populated.
            already_registered = any(
                "cache-trends" in str(rule) for rule in _d.app.url_map.iter_rules()
            )
            if not already_registered:
                ns = argparse.Namespace(
                    workspace=None,
                    log_dir=None,
                    sessions_dir=None,
                    name=None,
                    openclaw_dir=None,
                    data_dir=None,
                )
                _d.detect_config(ns)
            cls.app = _d.app
            cls.client = cls.app.test_client()
            cls.app_available = True
        except Exception as e:
            cls.app_available = False
            cls.skip_reason = str(e)

    def _skip_if_unavailable(self):
        if not self.app_available:
            self.skipTest(f"Dashboard app not available: {self.skip_reason}")

    def _write_session(self, sessions_dir, sid, events):
        path = os.path.join(sessions_dir, f"{sid}.jsonl")
        with open(path, "w") as f:
            for ev in events:
                f.write(json.dumps(ev) + "\n")
        return path

    def _msg_event(self, ts_iso, model, input_tok, output_tok, cache_read, cache_write):
        return {
            "type": "message",
            "timestamp": ts_iso,
            "message": {
                "model": model,
                "usage": {
                    "input": input_tok,
                    "output": output_tok,
                    "cacheRead": cache_read,
                    "cacheWrite": cache_write,
                    "totalTokens": input_tok + output_tok + cache_read + cache_write,
                    "cost": {
                        "input": input_tok * 3e-6,
                        "output": output_tok * 15e-6,
                        "cacheRead": cache_read * 0.3e-6,
                        "cacheWrite": cache_write * 3.75e-6,
                        "total": (
                            input_tok * 3e-6
                            + output_tok * 15e-6
                            + cache_read * 0.3e-6
                            + cache_write * 3.75e-6
                        ),
                    },
                },
            },
        }

    def test_returns_expected_shape(self):
        self._skip_if_unavailable()
        import dashboard as _d

        with tempfile.TemporaryDirectory() as tmp:
            now = time.time()
            today_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now))
            self._write_session(
                tmp,
                "sess-cached",
                [
                    self._msg_event(today_iso, "claude-sonnet-4-5", 100, 200, 5000, 500),
                    self._msg_event(today_iso, "claude-sonnet-4-5", 50, 80, 4000, 0),
                ],
            )
            with patch.object(_d, "_get_sessions_dir", return_value=tmp):
                resp = self.client.get("/api/usage/cache-trends?days=7")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)

        # Required top-level keys
        for key in ("days", "daily", "by_model", "totals", "recommendations"):
            self.assertIn(key, data)
        self.assertEqual(data["days"], 7)
        self.assertEqual(len(data["daily"]), 7)

        # Per-day rows have a date and the expected metric keys
        for row in data["daily"]:
            self.assertIn("date", row)
            for k in (
                "input_tokens",
                "cache_read_tokens",
                "cache_write_tokens",
                "cache_hit_ratio_pct",
                "est_savings_usd",
            ):
                self.assertIn(k, row)

        # by_model contains the model we synthesised
        models = [m["model"] for m in data["by_model"]]
        self.assertIn("claude-sonnet-4-5", models)

        totals = data["totals"]
        self.assertEqual(totals["input_tokens"], 150)
        self.assertEqual(totals["cache_read_tokens"], 9000)
        # cache_hit = 9000 / (150 + 9000) ≈ 98.4%
        self.assertGreater(totals["cache_hit_ratio_pct"], 95.0)
        self.assertGreater(totals["est_savings_usd"], 0)

    def test_empty_sessions_dir_returns_zeroed_window(self):
        self._skip_if_unavailable()
        import dashboard as _d

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_d, "_get_sessions_dir", return_value=tmp):
                resp = self.client.get("/api/usage/cache-trends?days=3")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data["days"], 3)
        self.assertEqual(len(data["daily"]), 3)
        self.assertEqual(data["totals"]["cache_read_tokens"], 0)
        self.assertEqual(data["by_model"], [])
        self.assertTrue(any("No cache-eligible" in r for r in data["recommendations"]))

    def test_days_param_clamped(self):
        self._skip_if_unavailable()
        import dashboard as _d

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(_d, "_get_sessions_dir", return_value=tmp):
                resp_low = self.client.get("/api/usage/cache-trends?days=0")
                resp_high = self.client.get("/api/usage/cache-trends?days=999")
                resp_bad = self.client.get("/api/usage/cache-trends?days=abc")
        self.assertEqual(json.loads(resp_low.data)["days"], 1)
        self.assertEqual(json.loads(resp_high.data)["days"], 90)
        # bad value falls back to default 14
        self.assertEqual(json.loads(resp_bad.data)["days"], 14)

    def test_low_hit_ratio_yields_stabilise_tip(self):
        self._skip_if_unavailable()
        import dashboard as _d

        with tempfile.TemporaryDirectory() as tmp:
            now = time.time()
            today_iso = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(now))
            # Mostly fresh input, almost no cache reads → low hit ratio
            self._write_session(
                tmp,
                "sess-cold",
                [self._msg_event(today_iso, "claude-haiku-4-5", 10000, 500, 100, 200)],
            )
            with patch.object(_d, "_get_sessions_dir", return_value=tmp):
                resp = self.client.get("/api/usage/cache-trends?days=7")
        data = json.loads(resp.data)
        self.assertLess(data["totals"]["cache_hit_ratio_pct"], 30.0)
        joined = " ".join(data["recommendations"]).lower()
        self.assertIn("stabilise", joined)


if __name__ == "__main__":
    unittest.main()
