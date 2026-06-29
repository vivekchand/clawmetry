"""Tests for #3390 -- _is_docker_runtime_down surfaces Docker daemon health
into DetectResult.meta as dockerRuntimeDown.
"""
import shutil
import subprocess

from clawmetry.adapters.openclaw import _is_docker_runtime_down


def test_docker_down_when_info_fails(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/docker")
    fake = type("R", (), {"returncode": 1})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    assert _is_docker_runtime_down() is True


def test_docker_healthy(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/docker")
    fake = type("R", (), {"returncode": 0})()
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: fake)
    assert _is_docker_runtime_down() is False


def test_docker_absent_returns_none(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: None)
    assert _is_docker_runtime_down() is None


def test_docker_exception_returns_none(monkeypatch):
    monkeypatch.setattr(shutil, "which", lambda _cmd: "/usr/bin/docker")
    monkeypatch.setattr(
        subprocess, "run",
        lambda *a, **kw: (_ for _ in ()).throw(OSError("timeout")),
    )
    assert _is_docker_runtime_down() is None
