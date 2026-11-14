"""Verify authority and media subscription decisions against the real SDK seam."""

import asyncio
import base64
import json
import os
import subprocess
import sys
import types
from pathlib import Path

import pytest

from clawmetry.asimov.observer import data_only_client_class, observe_live, require_sdk


@pytest.fixture(scope="session", autouse=True)
def server():
    """Authority unit tests make no robot or dashboard connection."""
    yield None


def token(can_publish):
    claims = {"sub": "sdk-observer", "video": {"canPublishData": can_publish}}
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    return "header." + body + ".signature"


def test_optional_sdk_error_is_actionable_when_missing(monkeypatch):
    """Missing optional SDK has an installation and recording-import explanation.

    AC-ASIMOV-001.2: a live-only dependency error explains the usable offline path.
    """
    import builtins

    original = builtins.__import__

    def missing(name, *args, **kwargs):
        if name == "menlo":
            raise ImportError("not installed")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", missing)
    with pytest.raises(RuntimeError, match="import-recording"):
        require_sdk()


def test_observer_import_below_live_python_floor_stays_optional(monkeypatch, tmp_path):
    """A simulated old-version guard is evaluated only on an explicit live call.

    AC-ASIMOV-001.2: offline import remains available without optional SDK imports.
    AC-ASIMOV-006.4: importing the observer does not evaluate the live-only Python floor.

    This checks guard placement; the separate grammar test covers Python 3.8 syntax.
    """
    import builtins
    import importlib

    from clawmetry.asimov import observer
    from clawmetry.asimov.recording import import_recording

    original = builtins.__import__

    def optional_forbidden(name, *args, **kwargs):
        if name.split(".")[0] in {"menlo", "livekit", "numpy"}:
            raise AssertionError(
                "An offline operation imported an optional robot dependency"
            )
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", optional_forbidden)
    monkeypatch.setattr(sys, "version_info", (3, 8, 20, "final", 0))
    assert importlib.reload(observer) is observer
    source = tmp_path / "offline.jsonl"
    source.write_text(
        json.dumps(
            {
                "kind": "state",
                "mode": "STAND",
                "t": 123,
                "joints": [{"name": "L_Knee", "pos": 0.1}],
                "alerts": [],
            }
        )
        + "\n"
    )
    result = import_recording(
        source, robot_id="offline", directory=tmp_path / "journal"
    )
    assert result["imported_records"] == 1
    with pytest.raises(RuntimeError, match="Python 3.12 or newer"):
        observer.require_sdk()


def test_data_only_observer_uses_no_media_callbacks_and_rejects_publication_tokens():
    pytest.importorskip("menlo.asimov")
    from menlo.asimov.transport._livekit_client import _LiveKitClient

    cls = data_only_client_class()
    assert issubclass(cls, _LiveKitClient)
    instances = []

    class Room:
        def __init__(self):
            self.events = []
            instances.append(self)

        def on(self, name, callback):
            self.events.append(name)

        async def connect(self, url, credential, options):
            self.options = options

    rtc = types.SimpleNamespace(Room=Room, RoomOptions=lambda **kwargs: kwargs)
    client = cls("ws://unit-test", "robot-room", token=token(False))
    asyncio.run(client._join(rtc, token(False)))
    assert instances[0].options == {"auto_subscribe": False}
    assert "track_subscribed" not in instances[0].events
    assert "data_track_published" in instances[0].events
    for authority in (True, None, "false"):
        with pytest.raises(RuntimeError, match="Observe token"):
            asyncio.run(client._join(rtc, token(authority)))
    assert len(instances) == 1


def test_control_credential_rejected_before_any_robot_connection(monkeypatch, tmp_path):
    sdk = pytest.importorskip("menlo.asimov")
    monkeypatch.setattr(
        sdk.ManagerConfig, "check", lambda self: types.SimpleNamespace(role="control")
    )
    monkeypatch.setattr(
        sdk.ManagerConfig,
        "resolve",
        lambda self: pytest.fail("No grant should resolve"),
    )
    with pytest.raises(ValueError, match="Observe credential"):
        observe_live(
            manager_url="http://unit.invalid",
            credential="test-only",
            directory=tmp_path,
        )
    assert list(tmp_path.iterdir()) == []


def test_missing_credentials_offer_recording_without_connecting(monkeypatch, tmp_path):
    """The actual SDK resolves an isolated empty store without inventing a robot.

    AC-ASIMOV-001.3: absent credentials offer the recording command without network access.
    """
    pytest.importorskip("menlo.asimov")
    import urllib.request

    monkeypatch.setenv("MENLO_HOME", str(tmp_path / "empty-menlo"))
    for name in (
        "MENLO_MANAGER_URL",
        "MENLO_CREDENTIAL",
        "MENLO_UDP_HOST",
        "MENLO_ROBOT",
    ):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda *a, **k: pytest.fail("No credential means no network connection"),
    )
    journal = tmp_path / "journal"
    with pytest.raises(ValueError, match="import-recording FILE --robot-id NAME"):
        observe_live(directory=journal)
    assert not journal.exists()


def test_observe_workflow_receives_real_sdk_state_without_motion(monkeypatch, tmp_path):
    """Exercise Observe orchestration with the actual SDK and an offline wire.

    AC-ASIMOV-002.1: Observe authority receives state without any transport command.

    Manager replies and the transport are isolated unit seams, not hardware evidence.
    The separate data-only test checks the actual client's JWT/media decisions.
    """
    sdk = pytest.importorskip("menlo.asimov")
    from tests.test_asimov_sdk import OfflineWire

    wire = OfflineWire()
    wire.kind = "livekit"
    wire.capabilities = frozenset({"state"})
    monkeypatch.setattr(
        sdk.ManagerConfig,
        "check",
        lambda self: sdk.ManagerGrant(
            url="ws://offline",
            room="MENLO-UNIT",
            identity="sdk-observe-unit",
            role="observe",
        ),
    )
    monkeypatch.setattr(
        sdk.ManagerConfig,
        "resolve",
        lambda self: sdk.LiveKitConfig(
            url="ws://offline", room="MENLO-UNIT", token=token(False)
        ),
    )

    def transport_factory(url, room, **kwargs):
        from menlo.asimov.transport._livekit_client import _LiveKitClient

        assert isinstance(kwargs["client"], _LiveKitClient)
        assert kwargs["media_timeout"] == 0.0
        assert room == "MENLO-UNIT"
        return wire

    monkeypatch.setattr(sdk, "LiveKitTransport", transport_factory)
    status = observe_live(
        manager_url="http://offline.invalid",
        credential="unit-observe-only",
        directory=tmp_path,
        duration=0.01,
    )
    events = [
        json.loads(line) for line in Path(status["path"]).read_text().splitlines()
    ]
    assert len([e for e in events if e["kind"] == "observation"]) == 1
    assert events[0]["data"]["observation_only"] is True
    assert events[0]["data"]["credential_role"] == "observe"
    assert events[0]["data"]["media_subscribed"] is False
    assert wire.sent == [] and wire.closed == 1
    assert events[-1]["kind"] == "run.ended"


def test_core_cli_fastpath_imports_no_optional_sdk_or_paid_package(tmp_path):
    """A fresh interpreter needs no site packages for Asimov import/status.

    AC-ASIMOV-001.2: ordinary Asimov status/import commands run without Menlo.
    AC-ASIMOV-006.4: core CLI import does not pull SDK, numerical or media libraries.
    """
    script = r"""
import importlib.abc
import sys
class OptionalImportsForbidden(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'menlo', 'livekit', 'numpy', 'clawmetry_pro', 'duckdb', 'dashboard'}:
            raise AssertionError('Unexpected optional import: ' + fullname)
sys.meta_path.insert(0, OptionalImportsForbidden())
from clawmetry import cli
sys.argv = ['clawmetry', 'asimov'] + sys.argv[1:]
cli.main()
"""
    completed = subprocess.run(
        [sys.executable, "-S", "-c", script, "status", "--journal-dir", str(tmp_path)],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": ".", "CLAWMETRY_INTERCEPT": "0"},
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout) == {"recorders": []}
    source = tmp_path / "offline.jsonl"
    source.write_text(
        json.dumps(
            {
                "kind": "state",
                "mode": "STAND",
                "t": 12345,
                "joints": [{"name": "L_Knee", "pos": 0.1}],
                "alerts": [],
            }
        )
        + "\n"
    )
    imported = subprocess.run(
        [
            sys.executable,
            "-S",
            "-c",
            script,
            "import-recording",
            str(source),
            "--robot-id",
            "offline-robot",
            "--journal-dir",
            str(tmp_path / "journal"),
        ],
        cwd=Path(__file__).resolve().parents[1],
        env={**os.environ, "PYTHONPATH": ".", "CLAWMETRY_INTERCEPT": "0"},
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    assert json.loads(imported.stdout)["imported_records"] == 1


def test_collector_package_keeps_core_python_38_grammar():
    """The collector modules retain the base package's syntax floor.

    AC-ASIMOV-006.4: each collector module parses using Python 3.8 grammar.
    """
    import ast

    root = Path(__file__).resolve().parents[1] / "clawmetry" / "asimov"
    for name in (
        "__init__.py",
        "cli.py",
        "journal.py",
        "recording.py",
        "sdk.py",
        "observer.py",
    ):
        ast.parse((root / name).read_text(), filename=name, feature_version=(3, 8))
