"""`clawmetry update --unattended` must defer to the daemon's update policy.

Bug pinned here: the desktop shell's 6h auto-upgrade path shelled the venv's
`clawmetry update`, which was a bare `pip install --upgrade clawmetry` that
read neither CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS nor CLAWMETRY_AUTO_UPDATE —
so a desktop install silently ignored the operator's stability window and
kill switch that the daemon's own updater (routes/update_check.py) honors.
The fix adds `--unattended`, which routes target selection through the very
same policy helpers (no duplicated semantics) and pins the pip install to
the newest aged-in release.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import clawmetry.cli as cli  # noqa: E402
import routes.update_check as uc  # noqa: E402


def _iso(hours_ago):
    return (
        datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    ).isoformat().replace("+00:00", "Z")


def _pypi_payload(latest, releases_spec):
    """releases_spec: {version: hours_ago}."""
    return {
        "info": {"version": latest},
        "releases": {
            ver: [{"upload_time_iso_8601": _iso(ago)}]
            for ver, ago in releases_spec.items()
        },
    }


class _FakeResp:
    def __init__(self, payload):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch_pypi(monkeypatch, payload):
    import urllib.request

    monkeypatch.setattr(
        urllib.request, "urlopen", lambda req, timeout=10: _FakeResp(payload)
    )


def _arm(monkeypatch):
    """Explicitly re-arm auto-update so the test is deterministic even on a
    CI runner (where the implicit CI disable would otherwise kick in)."""
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "1")


# ── kill switch ──────────────────────────────────────────────────────────────

def test_kill_switch_blocks_unattended_before_any_network(monkeypatch):
    monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", "0")
    import urllib.request

    def _boom(*a, **k):
        raise AssertionError("PyPI must not be contacted when the kill switch is on")

    monkeypatch.setattr(urllib.request, "urlopen", _boom)
    target, reason = cli._unattended_update_target("0.12.500")
    assert target is None
    assert "kill switch" in reason.lower() or "disabled" in reason.lower()


def test_richer_falsy_values_block_unattended(monkeypatch):
    # The daemon's parser accepts false/no/off, not just the literal "0".
    for val in ("false", "no", "off", "FALSE"):
        monkeypatch.setenv("CLAWMETRY_AUTO_UPDATE", val)
        target, _ = cli._unattended_update_target("0.12.500")
        assert target is None, val


def test_ci_environment_implicitly_blocks_unattended(monkeypatch):
    monkeypatch.delenv("CLAWMETRY_AUTO_UPDATE", raising=False)
    monkeypatch.setenv("CI", "true")
    target, _ = cli._unattended_update_target("0.12.500")
    assert target is None


# ── stability window ─────────────────────────────────────────────────────────

def test_min_age_window_pins_newest_aged_in_release(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setenv("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", "48")
    _patch_pypi(monkeypatch, _pypi_payload("0.12.518", {
        "0.12.500": 200, "0.12.510": 60, "0.12.518": 2,
    }))
    target, reason = cli._unattended_update_target("0.12.500")
    # 0.12.518 is the absolute latest but only 2h old; 0.12.510 has aged in.
    assert target == "0.12.510"
    assert "0.12.510" in reason


def test_min_age_window_installs_nothing_when_all_too_fresh(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.setenv("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", "48")
    _patch_pypi(monkeypatch, _pypi_payload("0.12.518", {
        "0.12.500": 200, "0.12.514": 20, "0.12.518": 2,
    }))
    target, reason = cli._unattended_update_target("0.12.500")
    assert target is None
    assert "stability window" in reason


def test_default_zero_window_targets_latest(monkeypatch):
    _arm(monkeypatch)
    monkeypatch.delenv("CLAWMETRY_AUTOUPDATE_MIN_AGE_HOURS", raising=False)
    _patch_pypi(monkeypatch, _pypi_payload("0.12.518", {
        "0.12.500": 200, "0.12.518": 0.01,
    }))
    target, _ = cli._unattended_update_target("0.12.500")
    assert target == "0.12.518"


def test_policy_reuses_daemon_helpers_not_a_copy(monkeypatch):
    """Drift guard: the CLI must consult routes/update_check.py's selection
    logic, so a future policy change there automatically applies here."""
    _arm(monkeypatch)
    _patch_pypi(monkeypatch, _pypi_payload("0.12.518", {"0.12.518": 100}))
    sentinel = {"called": False}

    def _fake_newest(releases, current, min_age):
        sentinel["called"] = True
        return "9.9.9"

    monkeypatch.setattr(uc, "_newest_aged_in_version", _fake_newest)
    target, _ = cli._unattended_update_target("0.12.500")
    assert sentinel["called"]
    assert target == "9.9.9"


def test_policy_import_failure_fails_closed(monkeypatch):
    """If the policy helpers cannot be evaluated, an unattended run must
    install NOTHING (never more than the policy allows)."""
    import builtins

    real_import = builtins.__import__

    def _blocked(name, *a, **k):
        if name.startswith("routes.update_check") or name == "routes":
            raise ImportError("simulated broken install")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", _blocked)
    target, reason = cli._unattended_update_target("0.12.500")
    assert target is None
    assert "policy unavailable" in reason.lower()


# ── _cmd_update wiring ───────────────────────────────────────────────────────

def _run_recorder(monkeypatch, returncode=0, stdout=""):
    import subprocess

    calls = []

    def _fake_run(cmd, **kw):
        calls.append(cmd)
        return SimpleNamespace(returncode=returncode, stdout=stdout, stderr="")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    return calls


def test_cmd_update_unattended_skip_runs_no_pip(monkeypatch, capsys):
    calls = _run_recorder(monkeypatch)
    monkeypatch.setattr(
        cli, "_unattended_update_target",
        lambda current: (None, "Unattended updates disabled (test)"),
    )
    cli._cmd_update(SimpleNamespace(unattended=True))
    assert calls == []
    assert "disabled" in capsys.readouterr().out.lower()


def test_cmd_update_unattended_pins_target_version(monkeypatch):
    from dashboard import __version__ as current

    # Report the current version back from the post-install probe so the
    # command takes the quiet "already latest" branch (no daemon restart).
    calls = _run_recorder(monkeypatch, returncode=0, stdout=current + "\n")
    monkeypatch.setattr(
        cli, "_unattended_update_target",
        lambda cur: ("0.12.999", "Unattended target: v0.12.999"),
    )
    cli._cmd_update(SimpleNamespace(unattended=True))
    pip_cmd = calls[0]
    assert "clawmetry==0.12.999" in pip_cmd
    assert "clawmetry" not in pip_cmd[pip_cmd.index("clawmetry==0.12.999") + 1:]


def test_cmd_update_plain_still_upgrades_unpinned(monkeypatch):
    from dashboard import __version__ as current

    calls = _run_recorder(monkeypatch, returncode=0, stdout=current + "\n")

    def _no_policy(cur):
        raise AssertionError("plain update must not consult unattended policy")

    monkeypatch.setattr(cli, "_unattended_update_target", _no_policy)
    cli._cmd_update(SimpleNamespace(unattended=False))
    assert "clawmetry" in calls[0]


def test_real_parser_wires_unattended_into_cmd_update(monkeypatch):
    """The desktop shell shells `clawmetry update --unattended`; if the flag
    ever disappears from the real parser, every desktop install would trip
    the shell's one-shot compat fallback and silently run policy-free
    upgrades forever."""
    captured = {}
    monkeypatch.setattr(
        cli, "_cmd_update", lambda args=None: captured.setdefault("args", args)
    )
    monkeypatch.setattr(sys, "argv", ["clawmetry", "update", "--unattended"])
    cli.main()
    assert getattr(captured["args"], "unattended", False) is True
