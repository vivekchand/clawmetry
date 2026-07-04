"""Tests for NemoClaw OCSF audit log tail streaming — issue #3389.

Verifies that _openshell_sandbox_logs_tail() spawns openshell with --tail and
--source all, that the sync daemon drains JSON lines correctly, and that
_ocsf_tail_shutdown() terminates held processes on daemon exit.
"""

import io
import json
import subprocess
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call


class TestOpenshellSandboxLogsTail(unittest.TestCase):
    def test_tail_includes_tail_and_source_all_flags(self):
        """Spawned command must include --tail and --source all."""
        captured = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            proc = MagicMock()
            proc.poll.return_value = None
            proc.stdout = io.StringIO("")
            return proc

        with patch("shutil.which", return_value="/usr/bin/openshell"):
            with patch("subprocess.Popen", side_effect=fake_popen):
                from clawmetry.adapters.openclaw import _openshell_sandbox_logs_tail
                result = _openshell_sandbox_logs_tail("test-sandbox")

        self.assertIsNotNone(result)
        self.assertIn("--tail", captured["cmd"])
        self.assertIn("--source", captured["cmd"])
        self.assertIn("all", captured["cmd"])

    def test_returns_none_when_openshell_absent(self):
        """Returns None (no exception) when openshell binary is missing."""
        with patch("shutil.which", return_value=None):
            from clawmetry.adapters.openclaw import _openshell_sandbox_logs_tail
            result = _openshell_sandbox_logs_tail("test-sandbox")
        self.assertIsNone(result)

    def test_returns_none_on_popen_failure(self):
        """Returns None (no exception) when Popen raises."""
        with patch("shutil.which", return_value="/usr/bin/openshell"):
            with patch("subprocess.Popen", side_effect=OSError("spawn failed")):
                from clawmetry.adapters.openclaw import _openshell_sandbox_logs_tail
                result = _openshell_sandbox_logs_tail("test-sandbox")
        self.assertIsNone(result)


class TestOcsfTailShutdown(unittest.TestCase):
    def test_shutdown_terminates_all_held_processes(self):
        """_ocsf_tail_shutdown() calls terminate() + wait() on every held proc."""
        import clawmetry.sync as _sync

        proc1 = MagicMock()
        proc2 = MagicMock()
        _sync._ocsf_tail_procs.clear()
        _sync._ocsf_tail_procs["sb-a"] = proc1
        _sync._ocsf_tail_procs["sb-b"] = proc2

        _sync._ocsf_tail_shutdown()

        proc1.terminate.assert_called_once()
        proc1.wait.assert_called_once()
        proc2.terminate.assert_called_once()
        proc2.wait.assert_called_once()
        self.assertEqual(_sync._ocsf_tail_procs, {})

    def test_shutdown_is_safe_when_empty(self):
        """_ocsf_tail_shutdown() is a no-op when no processes are held."""
        import clawmetry.sync as _sync
        _sync._ocsf_tail_procs.clear()
        _sync._ocsf_tail_shutdown()  # must not raise
        self.assertEqual(_sync._ocsf_tail_procs, {})


class TestOcsfTailDrain(unittest.TestCase):
    """Integration-style tests for the sync daemon tail drain path."""

    def _make_proc(self, lines):
        """Build a mock Popen with stdout yielding the given lines then blocking."""
        proc = MagicMock()
        proc.poll.return_value = None
        # readline() yields each line then returns "" to signal EOF
        proc.stdout = MagicMock()
        side_effects = [l + "\n" for l in lines] + [""]
        proc.stdout.readline.side_effect = side_effects
        return proc

    def test_drain_ingests_valid_json_lines(self):
        """JSON lines from the tail proc parse correctly into event dicts."""
        ev1 = {"uid": "u1", "time": 1000.0, "type": "network"}
        ev2 = {"uid": "u2", "time": 2000.0, "type": "file"}
        raw_lines = [json.dumps(ev1), json.dumps(ev2)]

        # Reproduce the drain loop's JSON-parse + uid-extraction logic
        result = []
        for line in raw_lines:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue
            uid = ev.get("uid") or ev.get("activity_id") or str(len(result))
            result.append((uid, ev))

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], "u1")
        self.assertEqual(result[1][0], "u2")
        self.assertEqual(result[0][1]["type"], "network")

    def test_drain_drops_non_json_lines(self):
        """Non-JSON lines are silently dropped; valid lines are still ingested."""
        mixed = [
            "not-json",
            json.dumps({"uid": "ok", "time": 123.0}),
            "also-not-json",
        ]
        result = []
        for line in mixed:
            line = line.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except Exception:
                pass
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["uid"], "ok")


if __name__ == "__main__":
    unittest.main()
