"""Execute the shipped Sessions JavaScript against asynchronous regression cases."""
import pathlib
import shutil
import subprocess

import pytest


@pytest.mark.skipif(not shutil.which("node"), reason="Node is needed for frontend tests")
def test_sessions_reader():
    result = subprocess.run(["node", str(pathlib.Path(__file__).with_suffix(".js"))], capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS:" in result.stdout
