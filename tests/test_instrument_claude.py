"""``clawmetry instrument claude`` — Claude Code native telemetry wiring (WO-57).

Requirement: Claude Code Native Telemetry (a4bd3c7e), AC-RSO-CCT-001.1,
AC-RSO-CCT-001.2, AC-RSO-CCT-001.3. Every test runs against temp paths; the
developer's real ``~/.claude/settings.json`` and marker file are never read
or written (the module takes explicit paths and an injected receiver probe).
"""
from __future__ import annotations

import json
import os

import pytest

from clawmetry import instrument_claude as ic


@pytest.fixture()
def paths(tmp_path):
    settings = tmp_path / "settings.json"
    marker = tmp_path / "hooks_installed.json"
    return str(settings), str(marker)


def _probe(port=4318, listening=True):
    return {"endpoint": f"http://127.0.0.1:{port}", "port": port,
            "listening": listening, "via": "compat_4318"}


def _read(path):
    with open(path) as f:
        return json.load(f)


def test_install_writes_block_merges_and_preserves_foreign_keys(paths):
    """AC-RSO-CCT-001.1 -- the env block lands, foreign keys survive, the
    endpoint is the probed receiver, protocol is http/json.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    with open(settings, "w") as f:
        json.dump({"env": {"MY_KEY": "keep-me"},
                   "hooks": {"PreToolUse": [{"matcher": "*", "hooks": []}]},
                   "permissions": {"allow": ["Bash(ls)"]}}, f)
    res = ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "installed", res
    data = _read(settings)
    env = data["env"]
    assert env["MY_KEY"] == "keep-me"
    assert data["hooks"] == {"PreToolUse": [{"matcher": "*", "hooks": []}]}
    assert data["permissions"] == {"allow": ["Bash(ls)"]}
    assert env["CLAUDE_CODE_ENABLE_TELEMETRY"] == "1"
    assert env["OTEL_EXPORTER_OTLP_PROTOCOL"] == "http/json"
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:4318"
    for k in ("OTEL_LOGS_EXPORTER", "OTEL_METRICS_EXPORTER", "OTEL_TRACES_EXPORTER"):
        assert env[k] == "otlp"
    assert env["CLAUDE_CODE_ENHANCED_TELEMETRY_BETA"] == "1"
    assert set(res["written"]) == set(ic.base_env("x"))
    assert res["conflicts"] == []
    assert "restart" in res["note"].lower()


def test_install_is_idempotent(paths):
    """AC-RSO-CCT-001.1 -- a second run changes nothing on disk.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    before = open(settings).read()
    res = ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "already_present", res
    assert open(settings).read() == before


def test_install_never_overwrites_a_foreign_value(paths):
    """AC-RSO-CCT-001.1 -- a key someone else set with a different value is
    reported as a conflict and left exactly as it was.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    with open(settings, "w") as f:
        json.dump({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://elsewhere.example"}}, f)
    res = ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    env = _read(settings)["env"]
    assert env["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://elsewhere.example"
    assert [c["key"] for c in res["conflicts"]] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" not in res["written"]
    # Uninstall must not touch it either: it was never ours.
    ic.uninstall(settings, marker_path=marker)
    assert _read(settings)["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://elsewhere.example"


def test_uninstall_removes_only_our_keys_and_restores_the_file(paths):
    """AC-RSO-CCT-001.1 -- uninstall leaves the file as it was, apart from
    keys we wrote whose value is still ours.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    original = {"env": {"MY_KEY": "keep-me"}, "model": "opus"}
    with open(settings, "w") as f:
        json.dump(original, f)
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    # The user edits one of OUR keys after install: that key is now theirs.
    data = _read(settings)
    data["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:9999"
    with open(settings, "w") as f:
        json.dump(data, f)
    res = ic.uninstall(settings, marker_path=marker)
    assert res["status"] == "uninstalled", res
    after = _read(settings)
    assert after["model"] == "opus"
    assert after["env"]["MY_KEY"] == "keep-me"
    assert after["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9999"
    assert [k["key"] for k in res["kept"]] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    for k in ic.base_env("x"):
        if k != "OTEL_EXPORTER_OTLP_ENDPOINT":
            assert k not in after["env"], k
    # Marker cleared: a second uninstall has nothing to do.
    assert ic.uninstall(settings, marker_path=marker)["status"] == "not_installed"


def test_uninstall_drops_env_object_it_created(paths):
    """AC-RSO-CCT-001.1 -- a settings file with no ``env`` before install
    has no ``env`` after uninstall (byte-level restore of the shape), even
    when install ran more than once in between (live-hit 2026-09-03: the
    second run saw the env object it had created and forgot it was ours).

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    with open(settings, "w") as f:
        json.dump({"model": "opus"}, f)
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    ic.uninstall(settings, marker_path=marker)
    assert _read(settings) == {"model": "opus"}


def test_content_flags_off_by_default_on_with_flag(paths):
    """AC-RSO-CCT-001.2 -- prompt/tool content flags are absent unless
    ``content=True``; raw API bodies are never written.

    AC-RSO-CCT-001.2
    """
    settings, marker = paths
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    env = _read(settings)["env"]
    for k in ic.CONTENT_ENV:
        assert k not in env, k
    assert "OTEL_LOG_RAW_API_BODIES" not in env
    res = ic.install(settings, content=True, probe=_probe(), managed={},
                     marker_path=marker)
    env = _read(settings)["env"]
    for k, v in ic.CONTENT_ENV.items():
        assert env[k] == v
    assert "OTEL_LOG_RAW_API_BODIES" not in env
    assert res["content"] is True
    # Re-running WITHOUT --content reverts to the conservative default.
    res = ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    env = _read(settings)["env"]
    for k in ic.CONTENT_ENV:
        assert k not in env, k
    assert set(res["removed"]) == set(ic.CONTENT_ENV)


def test_refuses_under_managed_settings_lock_and_leaves_file_untouched(paths, tmp_path):
    """AC-RSO-CCT-001.3 -- a managed settings file that pins the OTLP
    destination makes install refuse, naming the file and the keys, and
    the user's settings file is not written.

    AC-RSO-CCT-001.3
    """
    settings, marker = paths
    with open(settings, "w") as f:
        json.dump({"env": {"MY_KEY": "keep-me"}}, f)
    before = open(settings).read()
    managed = tmp_path / "managed-settings.json"
    with open(managed, "w") as f:
        json.dump({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://corp.example"}}, f)
    res = ic.install(settings, probe=_probe(), marker_path=marker,
                     managed_paths=[str(managed)])
    assert res["status"] == "refused", res
    assert res["reason"] == "managed_settings_lock"
    assert res["managed_path"] == str(managed)
    assert res["locked_keys"] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    assert open(settings).read() == before
    assert not os.path.exists(marker)


def test_managed_file_without_otlp_keys_does_not_lock(paths, tmp_path):
    """AC-RSO-CCT-001.3 -- a managed file that pins something unrelated is
    not a lock; install proceeds.

    AC-RSO-CCT-001.3
    """
    settings, marker = paths
    managed = tmp_path / "managed-settings.json"
    with open(managed, "w") as f:
        json.dump({"permissions": {"deny": ["Bash(rm -rf *)"]}}, f)
    res = ic.install(settings, probe=_probe(), marker_path=marker,
                     managed_paths=[str(managed)])
    assert res["status"] == "installed", res


def test_endpoint_follows_the_live_receiver(paths):
    """AC-RSO-CCT-001.1 -- when 4318 is not ours, the dashboard port is
    written; when nothing listens the command still writes and says so.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    res = ic.install(settings, probe=_probe(port=8900, listening=True),
                     managed={}, marker_path=marker)
    assert _read(settings)["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:8900"
    ic.uninstall(settings, marker_path=marker)
    res = ic.install(settings, probe=_probe(port=8900, listening=False),
                     managed={}, marker_path=marker)
    assert res["status"] == "installed"
    assert res["receiver_listening"] is False


def test_status_reports_configured_drift_and_missing(paths):
    """AC-RSO-CCT-001.1 / 001.8 -- status distinguishes "configured by us",
    "drifted" and "missing" from the marker plus the file.

    AC-RSO-CCT-001.1
    """
    settings, marker = paths
    assert ic.status(settings, marker_path=marker, probe=False)["configured"] is False
    ic.install(settings, probe=_probe(), managed={}, marker_path=marker)
    st = ic.status(settings, marker_path=marker, probe=False)
    assert st["configured"] is True
    assert st["endpoint"] == "http://127.0.0.1:4318"
    assert st["protocol"] == "http/json"
    assert st["content"] is False
    data = _read(settings)
    data["env"]["OTEL_EXPORTER_OTLP_PROTOCOL"] = "grpc"
    del data["env"]["OTEL_TRACES_EXPORTER"]
    with open(settings, "w") as f:
        json.dump(data, f)
    st = ic.status(settings, marker_path=marker, probe=False)
    assert st["configured"] is False
    assert st["drifted"] == ["OTEL_EXPORTER_OTLP_PROTOCOL"]
    assert st["missing"] == ["OTEL_TRACES_EXPORTER"]


def test_cli_rejects_unknown_target(capsys):
    assert ic.cli_main(["codex"]) == 2
    assert "unsupported target" in capsys.readouterr().err


def test_cli_help_exits_zero(capsys):
    assert ic.cli_main([]) == 0
    assert "instrument claude" in capsys.readouterr().out


def test_docs_name_the_real_variable():
    """AC-RSO-CCT-001.9 -- the enterprise guide and the OTel guide show the
    variable Claude Code actually reads, and state the protocol is required.

    AC-RSO-CCT-001.9
    """
    root = os.path.join(os.path.dirname(__file__), "..")
    ent = open(os.path.join(root, "docs", "enterprise.md")).read()
    otel = open(os.path.join(root, "docs", "OPENTELEMETRY.md")).read()
    assert "CLAUDE_CODE_ENABLE_TELEMETRY=1" in ent
    assert "CLAWMETRY_TELEMETRY=1" not in ent
    assert "no default protocol" in ent
    assert '"CLAUDE_CODE_ENABLE_TELEMETRY": "1"' in otel
    assert "clawmetry instrument claude" in otel
    for k in ic.base_env("x"):
        assert k in otel, k
