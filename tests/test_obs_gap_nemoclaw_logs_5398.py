"""Tests for nemoclaw live-follow gateway log gap — issue #5398.

Verifies that _openshell_sandbox_logs_tail() merges the OCSF audit stream
with the container gateway log for non-terminal sandboxes, and that terminal
sandboxes still get only the plain OCSF proc.
"""

import io
import os
import sys
import types
import unittest
from unittest.mock import MagicMock, patch, call


def _make_popen(lines=None):
    """Return a mock Popen whose stdout yields ``lines`` then EOF."""
    proc = MagicMock()
    proc.poll.return_value = None
    if lines is None:
        proc.stdout = io.StringIO("")
    else:
        proc.stdout = io.StringIO("\n".join(lines) + "\n")
    return proc


class TestLiveTailGatewayLogMerge(unittest.TestCase):
    """_openshell_sandbox_logs_tail merges gateway log for non-terminal sandboxes."""

    def _run(self, phase_info, gw_log_override=None, gw_files=None, popen_side_effects=None):
        """Helper: run _openshell_sandbox_logs_tail under controlled conditions."""
        import importlib
        # Force fresh import so patching lands cleanly.
        if "clawmetry.adapters.openclaw" in sys.modules:
            del sys.modules["clawmetry.adapters.openclaw"]
        spawned = []

        def fake_popen(cmd, **kwargs):
            p = _make_popen()
            spawned.append(cmd)
            return p

        env_patch = {}
        if gw_log_override is not None:
            env_patch["OPENSHELL_GATEWAY_LOG"] = gw_log_override

        with patch("shutil.which", return_value="/usr/bin/openshell"), \
             patch("subprocess.Popen", side_effect=fake_popen), \
             patch.dict(os.environ, env_patch, clear=False), \
             patch(
                 "clawmetry.adapters.openclaw._openshell_sandbox_phase_policy",
                 return_value=phase_info,
             ), \
             patch(
                 "clawmetry.adapters.openclaw._gateway_log_files",
                 return_value=gw_files or [],
             ):
            from clawmetry.adapters.openclaw import _openshell_sandbox_logs_tail
            result = _openshell_sandbox_logs_tail("test-sandbox")

        return result, spawned

    def test_non_terminal_sandbox_container_log_spawns_sandbox_exec(self):
        """Non-terminal sandbox with no host log → spawns sandbox exec tail."""
        result, spawned = self._run(
            phase_info={"sandboxRuntimeKind": "container"},
            gw_log_override=None,
            gw_files=[],
        )
        self.assertIsNotNone(result)
        # Two procs spawned: OCSF + sandbox exec.
        self.assertEqual(len(spawned), 2)
        ocsf_cmd = spawned[0]
        gw_cmd = spawned[1]
        self.assertIn("--tail", ocsf_cmd)
        self.assertIn("--source", ocsf_cmd)
        self.assertIn("sandbox", gw_cmd)
        self.assertIn("exec", gw_cmd)
        self.assertIn("/tmp/gateway.log", gw_cmd)
        # Result should be a _MergedProc (not a plain Mock).
        from clawmetry.adapters.openclaw import _MergedProc
        self.assertIsInstance(result, _MergedProc)

    def test_non_terminal_sandbox_host_log_uses_tail_f(self):
        """Non-terminal sandbox with host-side log → spawns plain tail -f."""
        result, spawned = self._run(
            phase_info={"sandboxRuntimeKind": "container"},
            gw_log_override=None,
            gw_files=["/tmp/openclaw/openclaw-2026-08-31.log"],
        )
        self.assertEqual(len(spawned), 2)
        gw_cmd = spawned[1]
        self.assertIn("tail", gw_cmd[0])
        self.assertIn("-f", gw_cmd)
        self.assertIn("/tmp/openclaw/openclaw-2026-08-31.log", gw_cmd)

    def test_non_terminal_sandbox_env_override_uses_tail_f(self):
        """Non-terminal sandbox with OPENSHELL_GATEWAY_LOG → spawns tail -f on that path."""
        result, spawned = self._run(
            phase_info={"sandboxRuntimeKind": "container"},
            gw_log_override="/custom/gateway.log",
        )
        self.assertEqual(len(spawned), 2)
        gw_cmd = spawned[1]
        self.assertIn("tail", gw_cmd[0])
        self.assertIn("-f", gw_cmd)
        self.assertIn("/custom/gateway.log", gw_cmd)

    def test_terminal_sandbox_only_ocsf_proc(self):
        """Terminal sandbox → only the OCSF proc is spawned (no merge)."""
        result, spawned = self._run(
            phase_info={"sandboxRuntimeKind": "terminal"},
        )
        self.assertIsNotNone(result)
        # Only the OCSF Popen — no second proc.
        self.assertEqual(len(spawned), 1)
        self.assertIn("--tail", spawned[0])
        # Not a _MergedProc.
        from clawmetry.adapters.openclaw import _MergedProc
        self.assertNotIsInstance(result, _MergedProc)

    def test_empty_phase_info_treated_as_non_terminal(self):
        """Empty phase_info (openshell absent) → non-terminal path taken."""
        result, spawned = self._run(
            phase_info={},
            gw_files=[],
        )
        # '' != 'terminal', so sandbox exec is attempted.
        self.assertEqual(len(spawned), 2)

    def test_returns_none_when_openshell_absent(self):
        """Returns None gracefully when openshell binary is missing."""
        if "clawmetry.adapters.openclaw" in sys.modules:
            del sys.modules["clawmetry.adapters.openclaw"]
        with patch("shutil.which", return_value=None):
            from clawmetry.adapters.openclaw import _openshell_sandbox_logs_tail
            result = _openshell_sandbox_logs_tail("test-sandbox")
        self.assertIsNone(result)


class TestMergedProc(unittest.TestCase):
    """_MergedProc correctly multiplexes two proc streams."""

    def _make_proc_with_lines(self, lines):
        proc = MagicMock()
        proc.poll.return_value = None
        proc.stdout = io.StringIO("\n".join(lines) + "\n")
        return proc

    def test_poll_none_while_any_child_alive(self):
        """poll() returns None while at least one child is running."""
        from clawmetry.adapters.openclaw import _MergedProc
        p1 = MagicMock()
        p2 = MagicMock()
        p1.poll.return_value = None   # still alive
        p2.poll.return_value = 0      # exited
        p1.stdout = io.StringIO("")
        p2.stdout = io.StringIO("")
        merged = _MergedProc([p1, p2])
        self.assertIsNone(merged.poll())

    def test_poll_zero_when_all_exited(self):
        """poll() returns 0 when all children have exited."""
        from clawmetry.adapters.openclaw import _MergedProc
        p1 = MagicMock()
        p2 = MagicMock()
        p1.poll.return_value = 1
        p2.poll.return_value = 0
        p1.stdout = io.StringIO("")
        p2.stdout = io.StringIO("")
        merged = _MergedProc([p1, p2])
        self.assertEqual(merged.poll(), 0)

    def test_terminate_calls_all_children(self):
        """terminate() propagates to every wrapped proc."""
        from clawmetry.adapters.openclaw import _MergedProc
        p1 = MagicMock()
        p2 = MagicMock()
        p1.stdout = io.StringIO("")
        p2.stdout = io.StringIO("")
        merged = _MergedProc([p1, p2])
        merged.terminate()
        p1.terminate.assert_called_once()
        p2.terminate.assert_called_once()

    def test_wait_calls_all_children(self):
        """wait() propagates to every wrapped proc."""
        from clawmetry.adapters.openclaw import _MergedProc
        p1 = MagicMock()
        p2 = MagicMock()
        p1.stdout = io.StringIO("")
        p2.stdout = io.StringIO("")
        merged = _MergedProc([p1, p2])
        merged.wait()
        p1.wait.assert_called_once()
        p2.wait.assert_called_once()

    def test_stdout_merges_lines_from_both_procs(self):
        """Lines from both procs appear in merged stdout."""
        import time
        from clawmetry.adapters.openclaw import _MergedProc
        p1 = self._make_proc_with_lines(["line-from-ocsf"])
        p2 = self._make_proc_with_lines(["line-from-gw"])
        merged = _MergedProc([p1, p2])
        # Give the pump threads a moment to drain.
        time.sleep(0.2)
        collected = []
        # Non-blocking read until EOF or no more data.
        merged.stdout.reconfigure(errors="replace")  # type: ignore[attr-defined]
        # Read what's available (EOF arrives when both pumps finish and write end closes).
        import select
        deadline = time.monotonic() + 2.0
        while time.monotonic() < deadline:
            rlist, _, _ = select.select([merged.stdout], [], [], 0.05)
            if rlist:
                line = merged.stdout.readline()
                if not line:
                    break
                collected.append(line.strip())
            elif len(collected) >= 2:
                break
        self.assertIn("line-from-ocsf", collected)
        self.assertIn("line-from-gw", collected)


if __name__ == "__main__":
    unittest.main()
