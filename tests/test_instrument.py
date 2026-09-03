"""``clawmetry instrument <runtime>`` — the generic settings-file
instrumenter (WO-57).

Requirement: Claude Code Native Telemetry (a4bd3c7e), AC-RSO-CCT-001.1,
.2, .3, .8, .10. Exercised with a FIXTURE runtime profile so no vendor
values live in the public suite (the Claude Code profile is in
clawmetry-pro). Every test runs against temp paths; the developer's real
settings and marker files are never read or written.
"""
from __future__ import annotations

import json
import os

import pytest

from clawmetry import instrument as ins
from clawmetry import otel_profiles


def _base_env(endpoint):
    return {
        "ACME_ENABLE_TELEMETRY": "1",
        "OTEL_LOGS_EXPORTER": "otlp",
        "OTEL_METRICS_EXPORTER": "otlp",
        "OTEL_TRACES_EXPORTER": "otlp",
        "OTEL_EXPORTER_OTLP_PROTOCOL": "http/json",
        "OTEL_EXPORTER_OTLP_ENDPOINT": endpoint,
        "OTEL_LOG_RAW_API_BODIES": "1",   # forbidden: must never be written
    }


CONTENT = {"OTEL_LOG_USER_PROMPTS": "1", "OTEL_LOG_TOOL_DETAILS": "1"}


def _make(tmp_path, managed_dirs=None):
    return ins.JsonEnvBlockInstrumenter(
        runtime="acme_cli", label="Acme CLI",
        settings_path=str(tmp_path / "user" / "settings.json"),
        project_settings_path=os.path.join(".acme", "settings.json"),
        base_env=_base_env, content_env=CONTENT,
        managed_dirs=managed_dirs or {},
        locked_keys=("OTEL_EXPORTER_OTLP_ENDPOINT", "OTEL_EXPORTER_OTLP_HEADERS",
                     "OTEL_EXPORTER_OTLP_PROTOCOL", "ACME_ENABLE_TELEMETRY"),
        upgrade_hint="Acme CLI is a paid runtime (clawmetry.com/pricing).")


@pytest.fixture()
def env(tmp_path):
    inst = _make(tmp_path)
    marker = str(tmp_path / "hooks_installed.json")
    settings = str(tmp_path / "settings.json")
    return inst, settings, marker


def _probe(port=4318, listening=True):
    return {"endpoint": f"http://127.0.0.1:{port}", "port": port,
            "listening": listening, "via": "compat_4318"}


def _read(path):
    with open(path) as f:
        return json.load(f)


def test_install_writes_block_merges_preserves_foreign_keys_and_never_raw_bodies(env):
    """AC-RSO-CCT-001.1 / AC-RSO-CCT-001.2 -- the block lands, foreign keys
    survive, the endpoint is the probed receiver, and a forbidden key the
    profile asked for is never written.

    AC-RSO-CCT-001.1
    AC-RSO-CCT-001.2
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        json.dump({"env": {"MY_KEY": "keep-me"}, "hooks": {"PreToolUse": []}}, f)
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "installed", res
    data = _read(settings)
    assert data["env"]["MY_KEY"] == "keep-me" and data["hooks"] == {"PreToolUse": []}
    assert data["env"]["ACME_ENABLE_TELEMETRY"] == "1"
    assert data["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:4318"
    assert "OTEL_LOG_RAW_API_BODIES" not in data["env"]
    assert set(res["written"]) == set(inst.base_env("x"))
    assert res["conflicts"] == [] and "restart" in res["note"].lower()


def test_install_is_idempotent(env):
    """AC-RSO-CCT-001.1

    AC-RSO-CCT-001.1
    """
    inst, settings, marker = env
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    before = open(settings).read()
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "already_present" and open(settings).read() == before


def test_install_never_overwrites_a_foreign_value(env):
    """AC-RSO-CCT-001.1 -- a differing user value is a conflict, left alone,
    and never touched by uninstall.

    AC-RSO-CCT-001.1
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        json.dump({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "https://elsewhere.example"}}, f)
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert _read(settings)["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://elsewhere.example"
    assert [c["key"] for c in res["conflicts"]] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    inst.uninstall(settings, marker_path=marker)
    assert _read(settings)["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "https://elsewhere.example"


def test_uninstall_removes_only_our_keys_and_restores_the_shape(env):
    """AC-RSO-CCT-001.1 -- uninstall leaves the file as it was apart from our
    keys with our values; an env object we created (even across re-runs) is
    removed when empty.

    AC-RSO-CCT-001.1
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        json.dump({"env": {"MY_KEY": "keep-me"}, "model": "x"}, f)
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    data = _read(settings)
    data["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://127.0.0.1:9999"
    with open(settings, "w") as f:
        json.dump(data, f)
    res = inst.uninstall(settings, marker_path=marker)
    after = _read(settings)
    assert after["model"] == "x" and after["env"]["MY_KEY"] == "keep-me"
    assert after["env"]["OTEL_EXPORTER_OTLP_ENDPOINT"] == "http://127.0.0.1:9999"
    assert [k["key"] for k in res["kept"]] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    assert inst.uninstall(settings, marker_path=marker)["status"] == "not_installed"
    with open(settings, "w") as f:
        json.dump({"model": "x"}, f)
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    inst.uninstall(settings, marker_path=marker)
    assert _read(settings) == {"model": "x"}


def test_content_flags_off_by_default_on_with_flag(env):
    """AC-RSO-CCT-001.2

    AC-RSO-CCT-001.2
    """
    inst, settings, marker = env
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert not (set(CONTENT) & set(_read(settings)["env"]))
    res = inst.install(settings, content=True, probe=_probe(), managed={}, marker_path=marker)
    assert all(_read(settings)["env"][k] == v for k, v in CONTENT.items()) and res["content"]
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert not (set(CONTENT) & set(_read(settings)["env"])) and set(res["removed"]) == set(CONTENT)


def test_refuses_under_managed_lock_including_fragments(env, tmp_path):
    """AC-RSO-CCT-001.3 -- a managed file, or a managed-settings.d fragment,
    that pins a destination key refuses the install and leaves the file
    untouched; an unrelated managed file does not lock.

    AC-RSO-CCT-001.3
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        json.dump({"env": {"MY_KEY": "keep-me"}}, f)
    before = open(settings).read()
    mdir = tmp_path / "managed"
    (mdir / "managed-settings.d").mkdir(parents=True)
    with open(mdir / "managed-settings.d" / "10-otel.json", "w") as f:
        json.dump({"env": {"OTEL_EXPORTER_OTLP_HEADERS": "Authorization=Bearer x"}}, f)
    inst2 = _make(tmp_path, managed_dirs={"Darwin": [str(mdir)], "Linux": [str(mdir)], "Windows": [str(mdir)]})
    res = inst2.install(settings, probe=_probe(), marker_path=marker)
    assert res["status"] == "refused" and res["reason"] == "managed_settings_lock"
    assert res["locked_keys"] == ["OTEL_EXPORTER_OTLP_HEADERS"]
    assert open(settings).read() == before and not os.path.exists(marker)
    with open(mdir / "managed-settings.d" / "10-otel.json", "w") as f:
        json.dump({"permissions": {"deny": ["rm"]}}, f)
    assert inst2.install(settings, probe=_probe(), marker_path=marker)["status"] == "installed"
    assert inst2.managed_candidates("Linux")[0] == str(mdir / "managed-settings.json")


def test_user_and_project_installs_have_separate_records(env, tmp_path):
    """AC-RSO-CCT-001.1 -- per-file records: a user value in the project
    file is a conflict, uninstalling the user file leaves the project file,
    a file with no record is refused and the other install named.

    AC-RSO-CCT-001.1
    """
    inst, user, marker = env
    proj = str(tmp_path / "proj" / ".acme" / "settings.json")
    os.makedirs(os.path.dirname(proj))
    with open(proj, "w") as f:
        json.dump({"env": {"OTEL_EXPORTER_OTLP_ENDPOINT": "http://127.0.0.1:8900"}}, f)
    inst.install(user, probe=_probe(port=8900), managed={}, marker_path=marker)
    res = inst.install(proj, probe=_probe(port=4318), managed={}, marker_path=marker)
    assert [c["key"] for c in res["conflicts"]] == ["OTEL_EXPORTER_OTLP_ENDPOINT"]
    assert set(ins._read_marker_all(inst.marker_key, marker)) == {ins._norm(user), ins._norm(proj)}
    assert inst.uninstall(user, marker_path=marker)["status"] == "uninstalled"
    assert "env" not in _read(user)
    assert _read(proj)["env"]["ACME_ENABLE_TELEMETRY"] == "1"
    res = inst.uninstall(str(tmp_path / "nowhere.json"), marker_path=marker)
    assert res["status"] == "not_installed" and res["other_installs"] == [ins._norm(proj)]


def test_corrupt_files_never_crash_and_never_overwrite(env):
    """AC-RSO-CCT-001.1

    AC-RSO-CCT-001.1
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        f.write("{ not json")
    before = open(settings).read()
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "error" and res["reason"] == "settings_unreadable"
    assert open(settings).read() == before
    st = inst.status(settings, marker_path=marker, probe=False)
    assert st["configured"] is False and st["unreadable"]
    assert inst.uninstall(settings, marker_path=marker)["status"] == "not_installed"
    with open(marker, "w") as f:
        f.write("garbage")
    assert inst.status(settings, marker_path=marker, probe=False)["configured"] is False
    with open(settings, "w") as f:
        json.dump({"env": "weird"}, f)
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert res["status"] == "refused" and res["reason"] == "env_not_object"


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlinked_settings_file_is_written_through(env, tmp_path):
    """AC-RSO-CCT-001.1

    AC-RSO-CCT-001.1
    """
    inst, _, marker = env
    real = tmp_path / "dotfiles" / "settings.json"
    real.parent.mkdir()
    with open(real, "w") as f:
        json.dump({"model": "x"}, f)
    link = tmp_path / "link.json"
    os.symlink(str(real), str(link))
    assert inst.install(str(link), probe=_probe(), managed={}, marker_path=marker)["status"] == "installed"
    assert os.path.islink(str(link)) and _read(str(real))["env"]["ACME_ENABLE_TELEMETRY"] == "1"
    inst.uninstall(str(link), marker_path=marker)
    assert _read(str(real)) == {"model": "x"}


def test_unwritable_marker_and_explicit_endpoint_are_surfaced(env, tmp_path, capsys, monkeypatch):
    """AC-RSO-CCT-001.1 -- a marker that cannot be written is reported; an
    explicit endpoint that is not a ClawMetry receiver gets the honest
    message, not "start clawmetry".

    AC-RSO-CCT-001.1
    """
    inst, settings, marker = env
    bad_marker = str(tmp_path / "nodir" / "sub" / "m.json")
    os.makedirs(os.path.dirname(os.path.dirname(bad_marker)))
    with open(os.path.dirname(bad_marker), "w") as f:
        f.write("x")
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=bad_marker)
    assert res["status"] == "installed" and res["marker_written"] is False
    monkeypatch.setattr(ins, "_url_alive", lambda *a, **k: False)
    res = inst.install(settings, endpoint="https://collector.corp", managed={}, marker_path=marker)
    ins._print_install(res)
    out = capsys.readouterr().out
    assert "could not confirm a ClawMetry receiver" in out and "start `clawmetry`" not in out


def test_status_reports_any_intact_install_drift_and_missing(env, tmp_path):
    """AC-RSO-CCT-001.8

    AC-RSO-CCT-001.8
    """
    inst, _, marker = env
    user = inst.settings_path  # status() with no path starts from the user-level file
    proj = str(tmp_path / "proj" / ".acme" / "settings.json")
    os.makedirs(os.path.dirname(proj))
    inst.install(proj, probe=_probe(), managed={}, marker_path=marker)
    st = inst.status(marker_path=marker, probe=False)
    assert st["configured"] is True and st["settings_path"] == ins._norm(proj)
    inst.install(user, probe=_probe(port=8900), managed={}, marker_path=marker)
    st = inst.status(marker_path=marker, probe=False)
    assert st["settings_path"] == ins._norm(user)
    assert {i["settings_path"] for i in st["installs"]} == {ins._norm(user), ins._norm(proj)}
    data = _read(user)
    data["env"]["OTEL_EXPORTER_OTLP_PROTOCOL"] = "grpc"
    del data["env"]["OTEL_TRACES_EXPORTER"]
    with open(user, "w") as f:
        json.dump(data, f)
    st = inst.status(user, marker_path=marker, probe=False)
    assert st["configured"] is False
    assert st["drifted"] == ["OTEL_EXPORTER_OTLP_PROTOCOL"] and st["missing"] == ["OTEL_TRACES_EXPORTER"]


def test_install_requires_the_runtime_entitlement(env):
    """AC-RSO-CCT-001.10 -- ``allowed=False`` writes nothing and names the
    plan; uninstall and status keep working.

    AC-RSO-CCT-001.10
    """
    inst, settings, marker = env
    with open(settings, "w") as f:
        json.dump({"model": "x"}, f)
    res = inst.install(settings, probe=_probe(), managed={}, marker_path=marker, allowed=False)
    assert res["status"] == "upgrade_required" and "pricing" in res["message"]
    assert _read(settings) == {"model": "x"} and not os.path.exists(marker)
    inst.install(settings, probe=_probe(), managed={}, marker_path=marker)
    assert inst.uninstall(settings, marker_path=marker)["status"] == "uninstalled"


def test_cli_resolves_profiles_and_reports_unknown_runtime(tmp_path, capsys, monkeypatch):
    """AC-RSO-CCT-001.10 -- ``clawmetry instrument <runtime>`` finds the
    registered profile (by alias too) and says what to do when none is
    registered; the entitlement gates install only.

    AC-RSO-CCT-001.10
    """
    otel_profiles._reset_for_tests()
    monkeypatch.setattr(ins, "_load_profiles", lambda: None)
    assert ins.cli_main(["nope"]) == 2
    assert "no exporter profile for 'nope'" in capsys.readouterr().err
    inst = _make(tmp_path)
    otel_profiles.register(otel_profiles.OtelRuntimeProfile(
        runtime="acme_cli", aliases=("acme",), label="Acme CLI", instrumenter=inst))
    monkeypatch.setattr(ins, "runtime_allowed", lambda rt: False)
    monkeypatch.setattr(ins, "_MARKER_PATH", str(tmp_path / "m.json"))
    assert ins.cli_main(["acme"]) == 1
    assert "Not available on this plan" in capsys.readouterr().out
    monkeypatch.setattr(ins, "runtime_allowed", lambda rt: True)
    monkeypatch.setattr(ins, "_url_alive", lambda *a, **k: True)
    assert ins.cli_main(["acme", "--endpoint", "http://127.0.0.1:4318"]) == 0
    assert _read(inst.settings_path)["env"]["ACME_ENABLE_TELEMETRY"] == "1"
    assert ins.cli_main(["acme", "--status"]) == 0
    assert "configured" in capsys.readouterr().out
    assert ins.cli_main(["acme", "--uninstall"]) == 0
    assert "env" not in _read(inst.settings_path)
    assert ins.cli_main([]) == 0
    assert "acme_cli" in capsys.readouterr().out
    otel_profiles._reset_for_tests()


def test_grace_entitlement_default_and_fail_closed(monkeypatch):
    """AC-RSO-CCT-001.10

    AC-RSO-CCT-001.10
    """
    from clawmetry import entitlements as _ent
    assert ins.runtime_allowed("acme_cli") == _ent.get_entitlement().allows_runtime("acme_cli")

    def _boom(*a, **k):
        raise RuntimeError("no licence server")
    monkeypatch.setattr(_ent, "get_entitlement", _boom)
    assert ins.runtime_allowed("acme_cli") is False


def test_docs_name_the_real_variables_and_the_generic_command():
    """AC-RSO-CCT-001.9 -- the enterprise guide names the variable Claude
    Code actually reads (not the old wrong one), states the protocol is
    required, and the OTel guide documents the generic command and the
    example block.

    AC-RSO-CCT-001.9
    """
    root = os.path.join(os.path.dirname(__file__), "..")
    ent = open(os.path.join(root, "docs", "enterprise.md")).read()
    otel = open(os.path.join(root, "docs", "OPENTELEMETRY.md")).read()
    assert "CLAUDE_CODE_ENABLE_TELEMETRY=1" in ent
    assert "CLAWMETRY_TELEMETRY=1" not in ent
    assert "no default protocol" in ent
    assert "clawmetry instrument <runtime>" in otel
    assert '"OTEL_EXPORTER_OTLP_PROTOCOL": "http/json"' in otel
    assert "clawmetry-pro" in otel
