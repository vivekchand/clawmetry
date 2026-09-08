"""
`clawmetry login` + `--turn-on-cloud-sync` / `--turn-off-cloud-sync` tests.

The toggles are a pure flip of the ~/.clawmetry/nocloud marker — the daemon
checks is_cloud_disabled() on every cloud POST, so no restart is involved.
OFF must keep the account key (only `disconnect` removes it) AND must call
the cloud to purge every trace of the account's telemetry so the fleet page
shows zero data immediately. The help text must advertise all of it
(explicit product requirement).
"""
from __future__ import annotations

import sys

import pytest

from clawmetry import cli
from clawmetry import config as cm_config


@pytest.fixture()
def marker(tmp_path, monkeypatch):
    path = tmp_path / "nocloud"
    monkeypatch.setattr(cm_config, "NOCLOUD_MARKER_PATH", str(path))
    monkeypatch.delenv("CLAWMETRY_NO_CLOUD", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))  # isolate ~/.clawmetry reads
    # Every "OFF" test opts out of the real network purge by default —
    # tests that specifically exercise the purge stub it explicitly.
    monkeypatch.setenv("CLAWMETRY_TOGGLE_SKIP_PURGE", "1")
    # Never bounce a real daemon from a test.
    monkeypatch.setattr(cli, "_kick_daemon_for_toggle", lambda: None)
    return path


def test_turn_off_creates_marker_and_keeps_config(marker, tmp_path, capsys):
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_test", "node_id": "n1"}')
    rc = cli._cmd_cloud_toggle(False)
    assert rc == 0
    assert marker.is_file()
    assert cm_config.is_cloud_disabled()
    # the login/key must survive the toggle (that's the disconnect difference)
    assert "cm_test" in cfg.read_text()
    out = capsys.readouterr().out
    assert "OFF" in out
    assert "--turn-on-cloud-sync" in out


def test_turn_on_removes_marker(marker, tmp_path, capsys):
    marker.write_text("x")
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_test"}')
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 0
    assert not marker.exists()
    assert not cm_config.is_cloud_disabled()
    assert "ON" in capsys.readouterr().out


def test_turn_on_without_login_points_to_login(marker, capsys):
    marker.write_text("x")
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 0
    assert not marker.exists()
    assert "clawmetry login" in capsys.readouterr().out


def test_turn_on_warns_when_env_forces_local(marker, monkeypatch, capsys):
    monkeypatch.setenv("CLAWMETRY_NO_CLOUD", "1")
    rc = cli._cmd_cloud_toggle(True)
    assert rc == 1
    assert "CLAWMETRY_NO_CLOUD" in capsys.readouterr().out


def test_toggle_flags_dispatch_from_main(marker, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["clawmetry", "--turn-off-cloud-sync"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    assert marker.is_file()
    monkeypatch.setattr(sys, "argv", ["clawmetry", "--turn-on-cloud-sync"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    assert not marker.exists()


def test_login_subcommand_registered(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["clawmetry", "login", "--help"])
    with pytest.raises(SystemExit) as e:
        cli.main()
    assert e.value.code == 0
    out = capsys.readouterr().out.lower()
    assert "usage: clawmetry login" in out
    assert "signup" in out


def test_help_text_advertises_cloud_commands():
    import dashboard

    for token in (
        "login",
        "connect",
        "disconnect",
        "doctor",
        "--turn-on-cloud-sync",
        "--turn-off-cloud-sync",
    ):
        assert token in dashboard.HELP_TEXT, token


# ── purge-on-toggle-off ────────────────────────────────────────────────────

def test_turn_off_purges_cloud_data_with_account_key(marker, tmp_path,
                                                     monkeypatch, capsys):
    """OFF must call the cloud purge with the account key AND write the marker.
    The purge is best-effort — the marker + local-only guarantee stands even
    if the network fails, but on the happy path we tell the user what was
    deleted so they trust the switch.
    """
    monkeypatch.delenv("CLAWMETRY_TOGGLE_SKIP_PURGE", raising=False)
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_purge_target", "node_id": "n1"}')

    seen = {}

    def _fake_purge(api_key, **kw):
        seen["api_key"] = api_key
        return (True, "deleted 42 row(s) across 7 table(s)")

    monkeypatch.setattr(cli, "_purge_cloud_data", _fake_purge)
    rc = cli._cmd_cloud_toggle(False)
    assert rc == 0
    assert seen["api_key"] == "cm_purge_target"
    assert marker.is_file()
    assert "cm_purge_target" in cfg.read_text(), "account key must survive"
    out = capsys.readouterr().out
    assert "Cloud data purged" in out
    assert "42 row" in out


def test_turn_off_surfaces_purge_failure_but_still_local_only(marker, tmp_path,
                                                               monkeypatch, capsys):
    """A network / cloud error must not undo the local-only flip. The user
    gets a retry hint; the marker is still on disk and the daemon is still
    kicked."""
    monkeypatch.delenv("CLAWMETRY_TOGGLE_SKIP_PURGE", raising=False)
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_offline", "node_id": "n1"}')
    monkeypatch.setattr(cli, "_purge_cloud_data",
                        lambda k, **kw: (False, "network error: cloud down"))

    rc = cli._cmd_cloud_toggle(False)
    assert rc == 0
    assert marker.is_file()
    out = capsys.readouterr().out
    assert "did not complete" in out
    assert "network error" in out
    assert "Retry" in out or "retry" in out


def test_turn_off_without_account_skips_purge(marker, tmp_path,
                                              monkeypatch, capsys):
    """No account linked → nothing to purge; still writes the marker."""
    monkeypatch.delenv("CLAWMETRY_TOGGLE_SKIP_PURGE", raising=False)
    called = []
    monkeypatch.setattr(cli, "_purge_cloud_data",
                        lambda k, **kw: called.append(k) or (True, ""))

    # config.json exists but has no api_key
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"node_id": "n1"}')
    rc = cli._cmd_cloud_toggle(False)
    assert rc == 0
    assert marker.is_file()
    assert called == [], "must not call purge with no account key"


def test_turn_off_kicks_daemon(marker, tmp_path, monkeypatch):
    """The daemon must be bounced so an in-flight snapshot upload can't
    outrace the marker check that gates the next POST."""
    kicked = []
    monkeypatch.setattr(cli, "_kick_daemon_for_toggle",
                        lambda: kicked.append(True))
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_kick"}')
    cli._cmd_cloud_toggle(False)
    assert kicked == [True]


def test_purge_cloud_data_posts_confirm_and_bearer(monkeypatch):
    """Wire-shape guard: the request must be POST + JSON confirm token +
    Bearer auth against /api/account/purge-data on the resolved ingest URL."""
    import json as _json
    import io as _io

    from clawmetry import cli as cli_mod

    captured = {}

    class _FakeResp:
        def __init__(self, payload):
            self._payload = _json.dumps(payload).encode()

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["headers"] = dict(req.header_items())
        captured["body"] = req.data
        return _FakeResp({"ok": True,
                          "purged": {"events": 3, "sessions": 2},
                          "cache_deleted": 0,
                          "kept": ["users", "stripe"]})

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.delenv("CLAWMETRY_ENDPOINT", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)

    ok, msg = cli_mod._purge_cloud_data("cm_wireshape_key")
    assert ok, msg
    assert "5 row" in msg  # 3 + 2
    assert captured["method"] == "POST"
    assert captured["url"].endswith("/api/account/purge-data")
    assert captured["url"].startswith("https://ingest.clawmetry.com")
    # Header names come back title-cased through urllib.
    lower_headers = {k.lower(): v for k, v in captured["headers"].items()}
    assert lower_headers.get("authorization") == "Bearer cm_wireshape_key"
    assert lower_headers.get("content-type") == "application/json"
    assert _json.loads(captured["body"].decode()) == {"confirm": "PURGE_DATA"}


def test_purge_cloud_data_skips_self_hosted_endpoint(monkeypatch):
    """Self-hosted deployments own the data plane — the managed-cloud purge
    endpoint is not theirs to call."""
    from clawmetry import cli as cli_mod
    calls = []
    monkeypatch.setenv("CLAWMETRY_ENDPOINT", "https://self.hosted.example.com")
    monkeypatch.setattr("urllib.request.urlopen",
                        lambda *a, **kw: calls.append(True))
    ok, msg = cli_mod._purge_cloud_data("cm_any_key")
    assert ok
    assert "self-hosted" in msg
    assert calls == []


def test_purge_cloud_data_falls_back_to_per_node_on_old_cloud(monkeypatch,
                                                              tmp_path):
    """A cloud that predates /api/account/purge-data returns 404. We keep
    the user's expectation ('data gone from cloud') by falling back to the
    per-node DELETE so at least the visible fleet row disappears."""
    import json as _json
    import urllib.error as _ue
    from clawmetry import cli as cli_mod

    calls = []

    class _FakeResp:
        def __init__(self, payload):
            self._payload = _json.dumps(payload).encode()

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def _fake_urlopen(req, timeout=None):
        calls.append((req.full_url, req.get_method()))
        if "/api/account/purge-data" in req.full_url:
            raise _ue.HTTPError(req.full_url, 404, "Not Found", {}, None)
        return _FakeResp({"ok": True, "purged": {"events": 5, "nodes": 1}})

    monkeypatch.setattr("urllib.request.urlopen", _fake_urlopen)
    monkeypatch.delenv("CLAWMETRY_ENDPOINT", raising=False)
    monkeypatch.delenv("CLAWMETRY_INGEST_URL", raising=False)

    # per-node fallback reads node_id from ~/.clawmetry/config.json
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = tmp_path / ".clawmetry" / "config.json"
    cfg.parent.mkdir(parents=True)
    cfg.write_text('{"api_key": "cm_old_cloud", "node_id": "the-only-node"}')
    from clawmetry import sync as sync_mod
    monkeypatch.setattr(sync_mod, "CONFIG_FILE", cfg)

    ok, msg = cli_mod._purge_cloud_data("cm_old_cloud")
    assert ok, msg
    assert "per-node fallback" in msg
    assert any(url.endswith("/api/cloud/nodes/the-only-node") and method == "DELETE"
               for url, method in calls)
