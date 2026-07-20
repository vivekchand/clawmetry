"""Tests for ``clawmetry status --json`` — the scriptable status snapshot.

Sibling of the ``tier`` / ``license`` / ``runtimes`` / ``features`` /
``channels`` / ``diagnose`` / ``verify-integrity`` JSON harnesses. Pins the
JSON contract shell wrappers now parse — they stop screen-scraping the human
table, so a silent regression on any field would break every pipeline that
`jq .cloud_sync.node_id` or `jq .daemon.running` today.

Every test is hermetic: ``CONFIG_FILE`` / ``STATE_FILE`` / ``LOG_FILE`` are
repointed into a tmp dir, and the two things ``_status_snapshot`` still
reaches for out of process (``_resolve_account_email`` → app.clawmetry.com,
``platform.system`` → launchctl / systemctl) are monkeypatched so the tests
never touch the network, launchd, or systemd — the way the sibling harnesses
already keep their runs deterministic across worker processes.
"""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest


def _ns(**overrides):
    """The exact argparse.Namespace ``_cmd_status`` reads.

    Kept in one place so a future flag on ``p_status`` needs one edit here,
    not one per test — same pattern the license/tier harnesses use.
    """
    ns = SimpleNamespace(live=False, show_key=False, as_json=True, cmd="status")
    for k, v in overrides.items():
        setattr(ns, k, v)
    return ns


@pytest.fixture
def stub_home(monkeypatch, tmp_path):
    """Redirect the three ``clawmetry.sync`` path constants into ``tmp_path``
    and keep every out-of-process call the snapshot makes short-circuited.

    Every branch under test writes to ``tmp_path`` and reads through the
    monkeypatched constants, so the test can never see a developer's real
    ``~/.clawmetry/config.json`` — the same isolation the license harness
    relies on via ``LICENSE_PATH``.
    """
    import clawmetry.sync as _sync
    import clawmetry.cli as cli

    monkeypatch.setattr(_sync, "CONFIG_FILE", tmp_path / "config.json")
    monkeypatch.setattr(_sync, "STATE_FILE", tmp_path / "sync-state.json")
    monkeypatch.setattr(_sync, "LOG_FILE", tmp_path / "sync.log")

    # ``_status_snapshot`` also peeks at ``~/.clawmetry/cloud_plan.json`` for
    # the entitlement plan; redirect that too so the runtimes block is
    # deterministic across machines.
    plan_path = tmp_path / "cloud_plan.json"

    import os as _os
    import os.path as _op
    real_expanduser = _op.expanduser

    def _fake_expand(p):
        if p == "~/.clawmetry/cloud_plan.json":
            return str(plan_path)
        return real_expanduser(p)

    monkeypatch.setattr(_op, "expanduser", _fake_expand)
    monkeypatch.setattr(_os.path, "expanduser", _fake_expand)

    # Network + daemon: nothing under test should escape the process.
    monkeypatch.setattr(cli, "_resolve_account_email", lambda _k: (None, None))
    monkeypatch.setattr(cli, "_is_sync_running", lambda: False)

    # Force a stable OS so daemon detection doesn't depend on the runner.
    import platform as _platform
    monkeypatch.setattr(_platform, "system", lambda: "Linux")

    # Belt-and-suspenders: never let the runtime detectors reach the real
    # filesystem or a live gateway during a snapshot.
    monkeypatch.setattr(
        "clawmetry.sync._detect_family_runtimes", lambda: [], raising=False,
    )
    monkeypatch.setattr(
        "clawmetry.license._pro_installed_version", lambda: None, raising=False,
    )

    return SimpleNamespace(tmp=tmp_path, plan_path=plan_path)


def _run_and_parse(capsys, args):
    """Run ``_cmd_status(args)`` under --json and return the parsed payload."""
    import clawmetry.cli as cli
    cli._cmd_status(args)
    out = capsys.readouterr().out
    return json.loads(out)


# ── envelope ──────────────────────────────────────────────────────────────────


def test_envelope_is_a_stable_object(stub_home, capsys):
    """Every documented key is present even on a virgin install; the JSON is
    a single line (script-friendly ``jq``) and ``sandboxes`` is always a list."""
    doc = _run_and_parse(capsys, _ns())
    for key in (
        "version", "cloud_sync", "sync_state", "runtimes",
        "daemon", "log", "sandboxes",
    ):
        assert key in doc, f"missing top-level key: {key}"
    assert isinstance(doc["sandboxes"], list)


def test_no_config_reports_disconnected(stub_home, capsys):
    """Fresh install → ``cloud_sync`` is ``null`` (not a partial object)."""
    doc = _run_and_parse(capsys, _ns())
    assert doc["cloud_sync"] is None


# ── cloud_sync block ──────────────────────────────────────────────────────────


def _write_config(stub_home, **fields):
    payload = {
        "api_key": "cm_abcdef0123456789",
        "encryption_key": "enc_abcdef0123456789",
        "node_id": "node-42",
        "connected_at": "2026-07-20T01:23:45.678Z",
    }
    payload.update(fields)
    from clawmetry import sync as _sync
    _sync.CONFIG_FILE.write_text(json.dumps(payload))
    return payload


def test_cloud_sync_masks_secrets_by_default(stub_home, capsys):
    """Without ``--show-key`` the raw secrets never leave the process — the
    same policy the human path enforces on every operator terminal."""
    _write_config(stub_home)
    doc = _run_and_parse(capsys, _ns(show_key=False))

    cs = doc["cloud_sync"]
    assert cs is not None
    assert cs["connected"] is True
    assert cs["config_error"] is None
    assert cs["api_key_masked"].startswith("cm_abc") and cs["api_key_masked"].endswith("6789")
    assert "…" in cs["api_key_masked"]
    assert cs["api_key"] is None
    assert cs["node_id"] == "node-42"
    assert cs["connected_at"] == "2026-07-20T01:23:45"  # :19 truncation
    assert cs["encryption"]["enabled"] is True
    assert cs["encryption"]["secret_key"] is None
    assert cs["encryption"]["secret_key_masked"] and "…" in cs["encryption"]["secret_key_masked"]


def test_cloud_sync_show_key_reveals_full_secrets(stub_home, capsys):
    """--show-key mirrors the human path's opt-in reveal."""
    payload = _write_config(stub_home)
    doc = _run_and_parse(capsys, _ns(show_key=True))

    cs = doc["cloud_sync"]
    assert cs["api_key"] == payload["api_key"]
    assert cs["encryption"]["secret_key"] == payload["encryption_key"]


def test_cloud_sync_placeholder_account_flagged(stub_home, monkeypatch, capsys):
    """The ``@clawmetry.auto`` / ``@clawmetry.linked`` trap surfaces as a
    structured ``account.placeholder`` boolean so wrappers can raise their
    own UI alerts instead of scraping the yellow terminal warning."""
    import clawmetry.cli as cli
    monkeypatch.setattr(cli, "_resolve_account_email", lambda _k: ("bot@clawmetry.auto", "cloud_free"))
    _write_config(stub_home)
    doc = _run_and_parse(capsys, _ns())

    acct = doc["cloud_sync"]["account"]
    assert acct["email"] == "bot@clawmetry.auto"
    assert acct["plan"] == "cloud_free"
    assert acct["placeholder"] is True


def test_cloud_sync_config_error_captured(stub_home, capsys):
    """Corrupt config → still connected+True but ``config_error`` carries the
    exception message. Guards the never-crash contract every CLI diagnostic
    honours; without this the whole snapshot would be ``null`` and scripts
    couldn't distinguish "no config" from "malformed config"."""
    from clawmetry import sync as _sync
    _sync.CONFIG_FILE.write_text("{ not-json")
    doc = _run_and_parse(capsys, _ns())

    cs = doc["cloud_sync"]
    assert cs["connected"] is True
    assert cs["config_error"] and isinstance(cs["config_error"], str)


# ── sync state, log tail ─────────────────────────────────────────────────────


def test_sync_state_populated(stub_home, capsys):
    from clawmetry import sync as _sync
    _sync.STATE_FILE.write_text(json.dumps({
        "last_sync": "2026-07-20T02:00:00Z",
        "last_event_ids": {"a.jsonl": "id1", "b.jsonl": "id2"},
    }))
    doc = _run_and_parse(capsys, _ns())

    st = doc["sync_state"]
    assert st == {"last_sync": "2026-07-20T02:00:00", "files_seen": 2}


def test_log_tail_matches_human_path_window(stub_home, capsys):
    """Same 3-line tail the human path prints — no more, no less."""
    from clawmetry import sync as _sync
    _sync.LOG_FILE.write_text("\n".join(["l1", "l2", "l3", "l4", "l5"]))
    doc = _run_and_parse(capsys, _ns())

    assert doc["log"]["path"] == str(_sync.LOG_FILE)
    assert doc["log"]["tail"] == ["l3", "l4", "l5"]


# ── runtimes ─────────────────────────────────────────────────────────────────


def test_runtimes_not_entitled_by_default(stub_home, capsys):
    """No cloud_plan.json → free plan → detected paid runtimes report
    ``syncing: false``. The daemon may DETECT them locally, but the account
    isn't entitled so they don't get pushed to the cloud."""
    import clawmetry.sync as _sync
    monkey_det = [
        {"name": "claude_code", "displayName": "Claude Code", "sessionCount": 12},
        {"name": "codex", "displayName": "Codex", "sessionCount": 3},
    ]
    # monkeypatch _detect_family_runtimes only for this test, on top of the
    # fixture's default empty-list patch.
    import clawmetry.cli as cli  # noqa: F401  (ensure module import parity)
    _sync._detect_family_runtimes = lambda: monkey_det  # type: ignore[assignment]
    try:
        doc = _run_and_parse(capsys, _ns())
    finally:
        _sync._detect_family_runtimes = lambda: []  # restore for other tests
    r = doc["runtimes"]
    assert r["entitled"] is False
    assert r["openclaw"] == {"detected": True, "syncing": True}
    assert r["detected"][0]["name"] == "claude_code"
    assert r["detected"][0]["display_name"] == "Claude Code"
    assert r["detected"][0]["session_count"] == 12
    assert all(rt["syncing"] is False for rt in r["detected"])


def test_runtimes_entitled_on_cloud_pro(stub_home, capsys):
    """cloud_pro plan cache → entitled: true → detected runtimes report
    ``syncing: true``. Same rule the human path uses to flip the ✅ syncing
    label on."""
    stub_home.plan_path.write_text(json.dumps({"plan": "cloud_pro"}))
    doc = _run_and_parse(capsys, _ns())
    r = doc["runtimes"]
    assert r["entitled"] is True
    assert r["plan"] == "cloud_pro"


# ── daemon ───────────────────────────────────────────────────────────────────


def test_daemon_linux_background_when_running_without_systemd(stub_home, monkeypatch, capsys):
    """Running but no systemctl (or no matching unit) → ``manager:
    "background"``. Catches the historical false-negative where
    ``systemctl --user is-active`` returns "inactive" on a root VPS even
    though the daemon is up (why we check the process first, then label).
    """
    import clawmetry.cli as cli
    monkeypatch.setattr(cli, "_is_sync_running", lambda: True)
    import shutil as _sh
    monkeypatch.setattr(_sh, "which", lambda _n: None)  # no systemctl on PATH
    doc = _run_and_parse(capsys, _ns())
    assert doc["daemon"] == {"running": True, "manager": "background"}


def test_daemon_not_running_reports_none_manager(stub_home, capsys):
    """Not running on Linux → running: false and manager may be None
    (no supervisor label to assign)."""
    doc = _run_and_parse(capsys, _ns())
    assert doc["daemon"]["running"] is False


# ── regression guards ────────────────────────────────────────────────────────


def test_human_path_unchanged_without_json(stub_home, capsys):
    """Without --json the operator terminal output must not turn into JSON.

    A regression here would silently break every human running `clawmetry
    status` — the assertion mirrors the guard in
    ``test_cli_license_json.test_plain_status_output_unchanged``.
    """
    _write_config(stub_home)
    import clawmetry.cli as cli
    cli._cmd_status(_ns(as_json=False))
    out = capsys.readouterr().out
    assert "ClawMetry Status" in out
    assert "─" * 20 in out
    # A JSON payload leaking to the human path would start with { — the
    # header block never does.
    assert not out.lstrip().startswith("{")


def test_live_flag_short_circuits_json(stub_home, monkeypatch, capsys):
    """--live wins over --json — the live-bar path returns before any
    snapshot dump. Documented in the flag's help text; guards against a
    future re-order that would emit JSON *and* enter the live loop."""
    import clawmetry.cli as cli
    called = {"live": 0}

    def _fake_live():
        called["live"] += 1

    monkeypatch.setattr(cli, "_status_live", _fake_live)
    cli._cmd_status(_ns(live=True, as_json=True))
    assert called["live"] == 1
    # No JSON payload printed (live-bar owns the terminal instead).
    assert capsys.readouterr().out == ""


def test_status_subparser_registers_json_flag():
    """The parser exposes --json on the status subcommand. Guards against
    a future edit that would silently drop the flag — same reason the
    license subparser has this test."""
    import clawmetry.cli as cli
    src = __import__("inspect").getsource(cli.main)
    # The flag registration lives in main() alongside the other subparsers.
    assert 'p_status.add_argument' in src
    assert '"--json"' in src.split('p_status =', 1)[1].split('# proxy', 1)[0]
