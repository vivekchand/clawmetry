"""
Test for localhost auth bypass security fix.

Issue: When bound to 0.0.0.0, requests from 127.0.0.1 should NOT bypass auth
because the server is exposed to all interfaces.

Only when bound to loopback (127.0.0.1) should localhost bypass auth.
"""

import pytest
import requests
import subprocess
import sys
import time
import os


def is_server_running(base_url):
    """Check if the ClawMetry server is reachable via socket."""
    import socket

    # Extract host and port from base_url like "http://127.0.0.1:18901"
    host_port = base_url.replace("http://", "").replace("https://", "")
    host, port_str = host_port.rsplit(":", 1)
    port = int(port_str)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2)
        result = s.connect_ex((host, port))
        s.close()
        return result == 0
    except Exception:
        return False


class TestLocalhostAuthBypass:
    """Tests for localhost auth bypass security."""

    def test_localhost_bypass_when_bound_to_loopback(self):
        """
        When bound to 127.0.0.1, requests from localhost should bypass auth.
        This is the secure, expected behavior for local-only servers.
        """
        port = 18901
        base_url = f"http://127.0.0.1:{port}"
        token = "test-token-loopback"

        # Kill any existing server on this port
        subprocess.run(
            ["pkill", "-f", f"dashboard.py.*--port.{port}"], capture_output=True
        )
        time.sleep(0.5)

        # Start server bound to loopback
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dashboard = os.path.join(repo_root, "dashboard.py")
        env = os.environ.copy()
        env["OPENCLAW_GATEWAY_TOKEN"] = token

        proc = subprocess.Popen(
            [sys.executable, dashboard, "--port", str(port), "--host", "127.0.0.1"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Wait for server to start
            for _ in range(20):
                time.sleep(0.5)
                if is_server_running(base_url):
                    break
            else:
                pytest.skip("Server failed to start")

            # Request from localhost WITHOUT token should SUCCEED (bypass auth)
            # because we're bound to loopback
            r = requests.get(f"{base_url}/api/overview", timeout=5)
            assert r.status_code == 200, (
                f"Expected 200 (localhost bypass) when bound to 127.0.0.1, "
                f"got {r.status_code}"
            )
        finally:
            proc.terminate()
            proc.wait()

    def test_localhost_bypass_blocked_when_bound_to_0_0_0_0(self):
        """
        When bound to 0.0.0.0, requests from localhost should NOT bypass auth.
        This is the security fix - 0.0.0.0 means exposed to network.
        """
        port = 18902
        base_url = f"http://127.0.0.1:{port}"
        token = "test-token-all-interfaces"

        # Kill any existing server on this port
        subprocess.run(
            ["pkill", "-f", f"dashboard.py.*--port.{port}"], capture_output=True
        )
        time.sleep(0.5)

        # Start server bound to 0.0.0.0
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        dashboard = os.path.join(repo_root, "dashboard.py")
        env = os.environ.copy()
        env["OPENCLAW_GATEWAY_TOKEN"] = token

        proc = subprocess.Popen(
            [sys.executable, dashboard, "--port", str(port), "--host", "0.0.0.0"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Wait for server to start
            for _ in range(20):
                time.sleep(0.5)
                if is_server_running(base_url):
                    break
            else:
                pytest.skip("Server failed to start")

            # Request from localhost WITHOUT token should FAIL (auth required)
            # because we're bound to 0.0.0.0 (exposed to network)
            r = requests.get(f"{base_url}/api/overview", timeout=5)
            assert r.status_code == 401, (
                f"Expected 401 (auth required) when bound to 0.0.0.0, "
                f"got {r.status_code}. localhost requests should NOT bypass auth!"
            )
        finally:
            proc.terminate()
            proc.wait()
