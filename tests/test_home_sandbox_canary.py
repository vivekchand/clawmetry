"""
Cross-platform canary: monkeypatch.setenv("HOME", ...) must redirect
os.path.expanduser("~") on every OS under pytest.

On POSIX this passes without any shim.  On Windows the conftest shim
patches ntpath.expanduser so that HOME takes precedence over USERPROFILE.
If this test ever fails on Windows it means the conftest shim regressed.
"""
import os


def test_home_env_redirects_expanduser(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    assert os.path.expanduser("~") == str(tmp_path)


def test_home_env_with_subpath(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    expected = str(tmp_path / ".clawmetry")
    assert os.path.expanduser("~/.clawmetry") == expected
