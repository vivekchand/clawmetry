"""Regression tests for install.sh's "you're already connected" gate (2026-08-18).

Re-running ``curl -fsSL https://clawmetry.com/install.sh | bash`` on a machine
that was already installed AND linked to an account used to upgrade the wheel
and then replay the whole first-run wizard (plans, ``[1]``/``[2]``, runtime
grid) as if ClawMetry had never been set up. Everything it asked about --
account, cloud-vs-local, license -- was already on disk.

install.sh now probes that state after the upgrade, prints it back (account
email + plan, cloud sync mode, version, node) and only re-runs ``clawmetry
onboard`` when the user says yes. A machine with NO account linked keeps the
original behaviour: straight into the wizard, no prompt.

The tests source the helper block out of install.sh (between the
``CM_EXISTING_SETUP_BLOCK_START`` / ``END`` sentinels) and drive it against
fake ``$HOME``s and a stub ``clawmetry`` binary, so they exercise the real
shell + Python the installer runs -- not a paraphrase of it.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALL_SH = REPO_ROOT / "install.sh"

posix_only = pytest.mark.skipif(
    os.name != "posix", reason="install.sh is the macOS/Linux installer"
)


def _read_install_sh() -> str:
    assert INSTALL_SH.exists(), f"install.sh missing at {INSTALL_SH}"
    return INSTALL_SH.read_text()


def _helper_block() -> str:
    """The probe/print/gate helpers, extracted between the test sentinels."""
    body = _read_install_sh()
    start = body.index("# >>> CM_EXISTING_SETUP_BLOCK_START")
    end = body.index("# <<< CM_EXISTING_SETUP_BLOCK_END")
    return body[start:end]


def _write_stub_cli(home: Path, snapshot: dict | None) -> Path:
    """A fake ``clawmetry`` that answers --version / status --json and records
    an ``onboard`` invocation by touching a marker file."""
    bin_dir = home / ".clawmetry" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    stub = bin_dir / "clawmetry"
    stub.write_text(
        "#!/bin/bash\n"
        "case \"$1\" in\n"
        "  --version) echo 'clawmetry 0.12.999' ;;\n"
        f"  status) cat <<'JSON'\n{json.dumps(snapshot or {})}\nJSON\n  ;;\n"
        '  onboard) touch "$HOME/.clawmetry/onboard.ran" ;;\n'
        "esac\n"
    )
    stub.chmod(0o755)
    return stub


def _probe(home: Path, cli: Path | None = None) -> dict:
    """Run ``_cm_probe_account`` against ``home`` and return the shell vars."""
    script = (
        "set -e\n"
        "GREEN=''; BOLD=''; DIM=''; NC=''\n"
        f'INSTALL_DIR="{home}/.clawmetry"\n'
        + _helper_block()
        + f'\n_cm_probe_account "{cli or (home / "no-such-bin")}"\n'
        'echo "connected=$CM_CONNECTED|email=$CM_EMAIL|plan=$CM_PLAN'
        '|sync=$CM_SYNC|node=$CM_NODE|ver=$CM_VER|dash=$CM_DASH"\n'
    )
    env = dict(os.environ, HOME=str(home))
    env.pop("CLAWMETRY_API_KEY", None)
    env.pop("CLAWMETRY_NO_CLOUD", None)
    out = subprocess.run(
        ["bash", "-c", script], capture_output=True, text=True, env=env, timeout=60
    )
    assert out.returncode == 0, f"probe failed: {out.stderr}"
    line = [ln for ln in out.stdout.splitlines() if ln.startswith("connected=")][-1]
    return dict(kv.split("=", 1) for kv in line.split("|"))


# ── Static guards ───────────────────────────────────────────────────────────


@posix_only
def test_install_sh_syntax_is_valid() -> None:
    bash = shutil.which("bash")
    assert bash, "bash not found on PATH -- required to syntax-check install.sh"
    result = subprocess.run([bash, "-n", str(INSTALL_SH)], capture_output=True, text=True)
    assert result.returncode == 0, f"bash -n failed: {result.stderr}"


def test_sentinels_and_helpers_present() -> None:
    body = _read_install_sh()
    for needle in (
        "# >>> CM_EXISTING_SETUP_BLOCK_START",
        "# <<< CM_EXISTING_SETUP_BLOCK_END",
        "_cm_probe_account()",
        "_cm_print_existing()",
        "_cm_reonboard_gate()",
        "_cm_run_onboard()",
    ):
        assert needle in body, f"install.sh lost {needle!r}"


def test_both_onboard_paths_go_through_the_gate() -> None:
    """The early-exit (already up to date) path and the post-install path must
    both probe first -- a connected node should never be re-wizarded from
    either entry point."""
    body = _read_install_sh()
    assert body.count("_cm_probe_account \"") >= 2, (
        "both the early-exit block and the onboarding block must probe for an "
        "existing account before running the wizard"
    )
    onboarding = body[body.index("# ── Onboarding ──") :]
    assert "_cm_probe_account" in onboarding and "_cm_reonboard_gate" in onboarding
    # No-account installs keep the original unconditional wizard.
    assert "else\n    _cm_run_onboard \"$CLAWMETRY_BIN\"\n  fi" in onboarding


# ── Probe behaviour ─────────────────────────────────────────────────────────


@posix_only
def test_probe_fresh_machine_reports_not_connected(tmp_path: Path) -> None:
    home = tmp_path / "fresh"
    (home / ".clawmetry").mkdir(parents=True)
    assert _probe(home)["connected"] == "0"


@posix_only
def test_probe_local_only_without_account_is_not_connected(tmp_path: Path) -> None:
    """Local-only with no account is 'installed', not 'connected' -- it must
    still get the wizard (that user has never linked an account)."""
    home = tmp_path / "localnoacct"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps({"api_key": "", "node_id": "box-1", "local_only": True})
    )
    (home / ".clawmetry" / "nocloud").touch()
    vals = _probe(home)
    assert vals["connected"] == "0"
    assert vals["sync"] == "local-only"


@posix_only
def test_probe_placeholder_account_is_not_connected(tmp_path: Path) -> None:
    """A ``…@clawmetry.auto`` placeholder is the daemon's auto-registration,
    invisible from the user's dashboard -- do not claim they're connected."""
    home = tmp_path / "placeholder"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps(
            {
                "api_key": "cm_abc123456789",
                "node_id": "box-2",
                "account_email": "node-77@clawmetry.auto",
            }
        )
    )
    vals = _probe(home)
    assert vals["connected"] == "0"
    assert vals["email"] == ""


@posix_only
def test_probe_reads_config_files_when_cli_snapshot_unavailable(tmp_path: Path) -> None:
    """No usable CLI (too old for ``status --json``, offline, crashed): the
    probe still recovers account + plan + sync mode from disk."""
    home = tmp_path / "cloudacct"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps(
            {"api_key": "cm_abc123456789", "node_id": "box-3", "account_email": "a@b.com"}
        )
    )
    (home / ".clawmetry" / "cloud_plan.json").write_text(json.dumps({"plan": "cloud_starter"}))
    vals = _probe(home)
    assert vals["connected"] == "1"
    assert vals["email"] == "a@b.com"
    assert vals["plan"] == "Starter"
    assert vals["sync"] == "cloud"


@posix_only
def test_probe_prefers_cli_snapshot(tmp_path: Path) -> None:
    """``status --json`` is authoritative (live email/plan + local-only)."""
    home = tmp_path / "snap"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "node_id": "stale", "account_email": "old@b.com"})
    )
    cli = _write_stub_cli(
        home,
        {
            "version": "0.12.999",
            "cloud_sync": {
                "api_key_masked": "cm_abc…6789",
                "account": {"email": "founder@example.com", "plan": "cloud_pro", "placeholder": False},
                "node_id": "test-box",
                "local_only": True,
            },
        },
    )
    vals = _probe(home, cli)
    assert vals["connected"] == "1"
    assert vals["email"] == "founder@example.com"
    assert vals["plan"] == "Pro"
    assert vals["sync"] == "local-only"
    assert vals["node"] == "test-box"
    assert vals["ver"] == "0.12.999"


@posix_only
def test_probe_survives_corrupt_config(tmp_path: Path) -> None:
    """Never crash on bad input: a corrupt config degrades to 'not connected'
    (the wizard runs) instead of aborting the install."""
    home = tmp_path / "corrupt"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text("not json at all")
    assert _probe(home)["connected"] == "0"


# ── Gate behaviour (the actual onboarding decision block) ───────────────────


def _run_decision_block(home: Path, answer: bytes | None, env_extra: dict | None = None) -> str:
    """Drive install.sh's onboarding block on a pty and report whether the
    wizard ran. Returns the terminal transcript."""
    import pty
    import select
    import time

    body = _read_install_sh()
    onboarding = body[body.index('if [ "${CLAWMETRY_SKIP_ONBOARD:-}" = "1" ]') :]
    onboarding = onboarding[: onboarding.index("\nfi\n") + 4]
    script = home / "decision.sh"
    script.write_text(
        textwrap.dedent(
            f"""\
            set -e
            GREEN=''; BOLD=''; DIM=''; NC=''
            INSTALL_DIR="{home}/.clawmetry"
            CLAWMETRY_BIN="$INSTALL_DIR/bin/clawmetry"
            NEMOCLAW_DETECTED=0
            """
        )
        + _helper_block()
        + "\n"
        + onboarding
        + '\necho "MARKER-DONE"\n'
    )

    env = dict(os.environ, HOME=str(home))
    env.pop("CLAWMETRY_REONBOARD", None)
    env.pop("CLAWMETRY_SKIP_ONBOARD", None)
    env.update(env_extra or {})
    pid, fd = pty.fork()
    if pid == 0:  # child
        os.execvpe("bash", ["bash", str(script)], env)
    out, sent, deadline = b"", answer is None, time.time() + 60
    while time.time() < deadline:
        ready, _, _ = select.select([fd], [], [], 0.3)
        if ready:
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
        if not sent and b"[y/N]" in out:
            time.sleep(0.2)
            os.write(fd, answer)
            sent = True
        if b"MARKER-DONE" in out:
            break
    os.close(fd)
    try:
        os.waitpid(pid, 0)
    except Exception:
        pass
    return out.decode(errors="replace")


CONNECTED_SNAPSHOT = {
    "version": "0.12.999",
    "cloud_sync": {
        "api_key_masked": "cm_abc…6789",
        "account": {"email": "founder@example.com", "plan": "cloud_pro", "placeholder": False},
        "node_id": "test-box",
        "local_only": True,
    },
}


def _connected_home(tmp_path: Path) -> Path:
    home = tmp_path / "connected"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps(
            {
                "api_key": "cm_abc123456789",
                "node_id": "test-box",
                "account_email": "founder@example.com",
            }
        )
    )
    (home / ".clawmetry" / "nocloud").touch()
    _write_stub_cli(home, CONNECTED_SNAPSHOT)
    return home


@posix_only
def test_connected_node_shows_summary_and_keeps_setup_on_no(tmp_path: Path) -> None:
    home = _connected_home(tmp_path)
    transcript = _run_decision_block(home, b"n\n")
    assert "already connected" in transcript.lower()
    assert "founder@example.com" in transcript
    assert "Pro plan" in transcript
    assert "Local-only" in transcript
    assert "0.12.999" in transcript
    assert not (home / ".clawmetry" / "onboard.ran").exists(), (
        "answering 'n' must NOT re-run the wizard over an existing setup"
    )


@posix_only
def test_connected_node_reonboards_on_yes(tmp_path: Path) -> None:
    home = _connected_home(tmp_path)
    _run_decision_block(home, b"y\n")
    assert (home / ".clawmetry" / "onboard.ran").exists(), "'y' must run clawmetry onboard"


@posix_only
def test_bare_enter_keeps_current_setup(tmp_path: Path) -> None:
    home = _connected_home(tmp_path)
    _run_decision_block(home, b"\n")
    assert not (home / ".clawmetry" / "onboard.ran").exists()


@posix_only
def test_env_override_forces_reonboard(tmp_path: Path) -> None:
    home = _connected_home(tmp_path)
    _run_decision_block(home, None, {"CLAWMETRY_REONBOARD": "1"})
    assert (home / ".clawmetry" / "onboard.ran").exists()


@posix_only
def test_unconnected_node_runs_wizard_without_prompting(tmp_path: Path) -> None:
    """No account linked: unchanged behaviour -- onboard runs, no question."""
    home = tmp_path / "noacct"
    (home / ".clawmetry").mkdir(parents=True)
    _write_stub_cli(home, {"version": "0.12.999", "cloud_sync": None})
    transcript = _run_decision_block(home, None)
    assert "[y/N]" not in transcript, "a fresh install must not be asked to re-onboard"
    assert (home / ".clawmetry" / "onboard.ran").exists()


@posix_only
def test_summary_never_promises_a_dead_dashboard(tmp_path: Path) -> None:
    """The dashboard URL is read from server.json and verified before it is
    printed -- a hard-coded localhost:8900 is a lie on a box whose daemon
    picked another port (or where nothing is listening at all)."""
    home = tmp_path / "deaddash"
    (home / ".clawmetry").mkdir(parents=True)
    (home / ".clawmetry" / "config.json").write_text(
        json.dumps({"api_key": "cm_abc123456789", "account_email": "a@b.com"})
    )
    # A port nothing can be listening on (0 is never bound).
    (home / ".clawmetry" / "server.json").write_text(json.dumps({"port": 1}))
    assert _probe(home)["dash"] in ("", "http://localhost:8900"), (
        "the probe may only report a dashboard URL that actually answered"
    )
    body = _read_install_sh()
    assert "not running" in body, (
        "when no dashboard answers, say so instead of printing a dead link"
    )
