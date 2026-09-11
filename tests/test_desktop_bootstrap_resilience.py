"""The desktop shell's FIRST install must survive a hostile Windows.

Field failure 2026-08-29: a Windows 11 machine (dual-stack home network,
IPv6-first) showed "PyPI install failed. See bootstrap.log." on every
launch, forever. The bootstrap had exactly one pip attempt, no retry, no
--no-input (a keyring prompt in a windowless app hangs until the 300s
timeout), no pip self-upgrade (a stale bundled pip can't pick current
wheels), logged only stderr[:2000] (pip's resolver explains itself on
stdout), and — the brick — treated `venv/Scripts/python.exe` *existing*
as the venv being usable. On Windows that file is a launcher resolving
the base interpreter through pyvenv.cfg: a Store-Python update or a
python.org minor upgrade relocates the base, the launcher keeps existing,
and every pip run fails identically on every relaunch until someone
manually deletes the venv.

Properties under test:

  1. A venv whose python cannot run is detected as broken (existence is
     not health) and bootstrap() rebuilds it instead of dead-ending.
  2. The pip install retries once with a cold cache, and always carries
     --no-input / --prefer-binary.
  3. pip failure output is classified into an actionable message that
     includes nothing generic for the known failure families.
  4. A log line that the Windows locale codepage cannot encode does not
     raise (the old `except OSError` missed UnicodeEncodeError).
"""
from __future__ import annotations

import re
import subprocess
import sys
import sysconfig
import threading
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

import desktop.app as dapp  # noqa: E402


def _sup(tmp_path):
    """A real RuntimeSupervisor over a temp runtime dir (no __init__:
    these tests drive bootstrap-path methods directly)."""
    runtime = tmp_path / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    sup = dapp.RuntimeSupervisor.__new__(dapp.RuntimeSupervisor)
    sup.port = 8999
    sup.statuses = []
    sup.on_status = sup.statuses.append
    sup.proc = None
    sup.runtime = runtime
    sup.venv = runtime / "venv"
    sup.stamp_file = runtime / "last-upgrade.json"
    sup.heal_file = runtime / "version-heal.json"
    sup.log_file = runtime / "bootstrap.log"
    sup.instance_file = runtime / "app-instance.json"
    sup._last_sync_start = 0.0
    sup.shutting_down = threading.Event()
    sup._pending_drift = None
    sup._last_tick = 0.0
    sup._tick_count = 0
    return sup


def _break_venv(sup):
    """Reproduce the Windows base-interpreter-upgrade brick: the venv
    python still exists on disk but can no longer run."""
    vpy = sup._venv_python()
    cfg = sup.venv / "pyvenv.cfg"
    if cfg.exists():
        cfg.write_text(cfg.read_text().replace("home = ", "home = /nonexistent-"))
    vpy.unlink()
    vpy.write_text("#!/nonexistent/python\n")
    vpy.chmod(0o755)
    assert vpy.exists()


# ── 1. health check + rebuild ────────────────────────────────────────────


def test_missing_venv_is_not_runnable(tmp_path):
    assert not _sup(tmp_path)._venv_is_runnable()


def test_broken_venv_is_detected_and_rebuilt(tmp_path):
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py, "no bootstrap python on this machine"
    assert sup._create_venv(py)
    assert sup._venv_is_runnable()

    _break_venv(sup)
    assert not sup._venv_is_runnable(), (
        "a venv python that exists but cannot run must fail the health "
        "check — existence was the check that bricked Windows installs"
    )
    assert sup._create_venv(py), "rebuild over the broken venv must succeed"
    assert sup._venv_is_runnable()


def test_bootstrap_rebuilds_broken_venv_instead_of_dead_ending(tmp_path, monkeypatch):
    """End-to-end over bootstrap() with pip stubbed out (no network):
    broken venv in, runnable clawmetry out."""
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py
    assert sup._create_venv(py)
    _break_venv(sup)

    calls = []

    def fake_pip():
        calls.append(True)
        # what a successful pip install leaves behind
        exe = sup._venv_clawmetry()
        exe.parent.mkdir(parents=True, exist_ok=True)
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o755)
        return 0, "Successfully installed clawmetry"

    monkeypatch.setattr(sup, "_pip_install_clawmetry", fake_pip)
    assert sup.bootstrap() is True
    assert calls, "bootstrap must reach the install after rebuilding"
    assert sup._venv_is_runnable(), "the venv must have been rebuilt runnable"


# ── 2. pip attempt shape ─────────────────────────────────────────────────


def test_pip_install_retries_with_cold_cache_and_safe_flags(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    seen = []

    def fake_run(argv, timeout):
        seen.append(argv)
        rc = 1
        # self-upgrade of pip succeeds; first clawmetry attempt fails;
        # the cold-cache attempt succeeds.
        if argv[-1] == "pip" or "--no-cache-dir" in argv:
            rc = 0
        return subprocess.CompletedProcess(argv, rc, stdout="", stderr="boom")

    monkeypatch.setattr(sup, "_run_child", fake_run)
    rc, _out = sup._pip_install_clawmetry()
    assert rc == 0
    install_attempts = [a for a in seen if a[-1] == "clawmetry"]
    assert len(install_attempts) == 2, "one retry, no more"
    assert "--no-cache-dir" in install_attempts[1], "retry must bypass the cache"
    for a in install_attempts:
        assert "--no-input" in a, "windowless app: pip must never prompt"
        # On Windows nothing may ever compile (no MSVC on user machines —
        # field failure 2026-08-29: cffi<2 had no cp314 wheel and pip fell
        # back to an sdist that demanded Visual C++); elsewhere wheels are
        # preferred but a source build is allowed to succeed.
        import platform as _plat
        if _plat.system() == "Windows":
            assert "--only-binary=:all:" in a, "Windows must be wheels-only"
        else:
            assert "--prefer-binary" in a, "never build from sdist when a wheel exists"


def test_pip_install_gives_up_after_two_attempts(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    seen = []

    def fake_run(argv, timeout):
        seen.append(argv)
        return subprocess.CompletedProcess(
            argv, 0 if argv[-1] == "pip" else 1, stdout="resolver said no", stderr="")

    monkeypatch.setattr(sup, "_run_child", fake_run)
    rc, out = sup._pip_install_clawmetry()
    assert rc != 0
    assert len([a for a in seen if a[-1] == "clawmetry"]) == 2
    assert "resolver said no" in out, "stdout must be part of the reported output"


# ── 3. failure classification ────────────────────────────────────────────


@pytest.mark.parametrize(
    "snippet,expect",
    [
        ("Error: No Python at 'C:\\Python312\\python.exe'", "broken"),
        ("ERROR: No matching distribution found for clawmetry", "python.org"),
        ("SSLError(SSLCertVerificationError: certificate verify failed)", "proxy"),
        ("Connection to pypi.org timed out. (connect timeout=20)", "pypi.org"),
        ("PermissionError: [WinError 5] Access is denied", "antivirus"),
        ("distutils.compilers.errors.PlatformError: Microsoft Visual C++ 14.0 "
         "or greater is required.", "update ClawMetry"),
        ("ERROR: Failed to build 'cffi' when getting requirements to build "
         "wheel\n  Getting requirements to build wheel did not run successfully.",
         "update ClawMetry"),
    ],
)
def test_pip_failures_classify_to_actionable_hints(snippet, expect):
    hint = dapp.RuntimeSupervisor._explain_pip_failure(snippet)
    assert expect.lower() in hint.lower()
    assert "bootstrap.log" not in hint, "the status line names the full log path"


def test_unknown_pip_failure_still_points_at_the_log():
    assert "log" in dapp.RuntimeSupervisor._explain_pip_failure("???").lower()


# Field failure #5628: a Windows machine on Python **3.11** was told
# "Python too old ... install python.org Python 3.11+". Two defects made
# that the only advice it could give:
#   1. `_bootstrap_python`'s probe enforces the 3.9 floor, so pip is only
#      ever reached on an interpreter that already passed it — "too old"
#      is unreachable from bootstrap(), and blaming it is always wrong.
#   2. pip words an index it could not READ exactly like an interpreter
#      PyPI has no wheels for ("No matching distribution found"), and the
#      no_distribution branch ran before the TLS/network ones, so a
#      blocked proxy, a captive portal and an intercepted TLS handshake
#      all landed on that same misleading hint.
# The snippets below are pip's REAL output, captured by pointing pip at a
# refused port, a 404 index and a self-signed index (pip 26.1.2).

_REFUSED = (
    "WARNING: Retrying (Retry(total=0)) after connection broken by "
    "'NewConnectionError(\"HTTPConnection(host=\'127.0.0.1\', port=9): "
    "Failed to establish a new connection: [Errno 61] Connection "
    "refused\")': /simple/clawmetry/\n"
    "ERROR: Could not find a version that satisfies the requirement "
    "clawmetry (from versions: none)\n"
    "ERROR: No matching distribution found for clawmetry"
)
_SELF_SIGNED = (
    "WARNING: Retrying after connection broken by "
    "'SSLError(SSLCertVerificationError(\'certificate is not "
    "trusted\'))': /simple/clawmetry/\n"
    "Could not fetch URL https://mirror.corp/simple/clawmetry/: There "
    "was a problem confirming the ssl certificate - skipping\n"
    "ERROR: Could not find a version that satisfies the requirement "
    "clawmetry (from versions: none)\n"
    "ERROR: No matching distribution found for clawmetry"
)
_EMPTY_MIRROR = (
    "ERROR: Could not find a version that satisfies the requirement "
    "clawmetry (from versions: none)\n"
    "ERROR: No matching distribution found for clawmetry"
)
_NO_WHEEL = (
    "ERROR: Could not find a version that satisfies the requirement "
    "duckdb!=1.4.5,>=0.10 (from clawmetry) (from versions: 0.9.0, 0.10.0)\n"
    "ERROR: No matching distribution found for duckdb!=1.4.5,>=0.10"
)


@pytest.mark.parametrize(
    "snippet,code",
    [
        # "(from versions: none)" = the index yielded no candidates at
        # all, so transport evidence in the same output IS the cause.
        (_REFUSED, "network"),
        (_SELF_SIGNED, "tls_intercepted"),
        # No transport evidence: the index answered and carries nothing.
        (_EMPTY_MIRROR, "no_distribution"),
        # A real candidate list: the index answered fine and nothing in
        # it fits this interpreter. This is the only true no_distribution.
        (_NO_WHEEL, "no_distribution"),
    ],
)
def test_unreadable_index_is_not_reported_as_no_distribution(snippet, code):
    assert dapp.RuntimeSupervisor._classify_pip_failure(snippet) == code


def test_no_hint_ever_blames_the_python_version_for_no_distribution():
    """The 3.9 floor is enforced before pip runs, so a hint that tells the
    user their Python is too old can only ever be wrong (#5628)."""
    for code, hint in dapp._PIP_FAILURE_HINTS.items():
        low = hint.lower()
        assert "too old" not in low, (
            f"{code} blames the interpreter's version, which "
            "_bootstrap_python already proved is >= 3.9"
        )


def test_blocked_index_hint_talks_about_the_network_not_python():
    hint = dapp.RuntimeSupervisor._explain_pip_failure(_REFUSED).lower()
    assert "proxy" in hint or "connectivity" in hint
    assert "python" not in hint, (
        "a refused index is not the interpreter's fault; naming Python "
        "here is what sent a 3.11 user to reinstall 3.11"
    )


# ── 4. logging must never kill the boot thread ───────────────────────────


def test_log_survives_unencodable_characters(tmp_path):
    sup = _sup(tmp_path)
    sup._log("pip said: ✓ — ünïcode \u2713")
    assert "ünïcode" in sup.log_file.read_text(encoding="utf-8")


# ── 5. the cffi pin must stay split per interpreter ──────────────────────
#
# setup.py pins cffi<2 on Python 3.9 only (cffi 2.0.0 SIGSEGVs py3.9, #5108,
# and cffi 2.1+ requires >=3.10 so it ships no cp39 wheels) and cffi>=2 from
# 3.10 up (cffi 1.x ships NO cp314 wheels, so an unconditional <2 forces an
# MSVC source build on end-user Windows — the 2026-08-29 field failure).
# Both halves are load-bearing; collapsing them back to a bare "cffi<2"
# re-bricks every Windows install on a current python.org Python.
#
# The boundary sits at 3.10, not 3.14, because that is where the two py3.9
# reasons stop applying. Holding 3.10-3.13 at cffi<2 capped cryptography at
# 46.0.0 (46.0.1+ needs cffi>=2.0.0 on 3.9+) and so kept nine published
# advisories open on the interpreters most installs run. Moving the boundary
# back up would silently reopen them.


def test_cffi_pin_is_split_per_interpreter():
    setup_src = (REPO_ROOT / "setup.py").read_text(encoding="utf-8")
    assert 'cffi<2; python_version < "3.10"' in setup_src
    assert 'cffi>=2; python_version >= "3.10"' in setup_src
    import re
    bare = re.search(r"""['"]cffi<2['"]""", setup_src)
    assert bare is None, "an unmarked cffi<2 would have no cp314 wheel"


def test_cryptography_floor_tracks_the_cffi_boundary():
    """Wherever cffi>=2 is allowed, cryptography must be advisory-clean.

    The two pins are coupled: cryptography 46.0.1+ requires cffi>=2.0.0 on
    3.9+, so a cffi<2 band caps cryptography at 46.0.0 no matter what floor
    is written. Raising the cffi boundary without raising the cryptography
    floor to match would leave the newer band pinned to a version whose
    advisories are fixed and reachable.
    """
    setup_src = (REPO_ROOT / "setup.py").read_text(encoding="utf-8")
    assert 'cryptography>=50.0.0; python_version >= "3.10"' in setup_src
    assert (
        'cryptography>=46.0.0; python_full_version >= "3.9.2" '
        'and python_version < "3.10"' in setup_src
    )
    assert 'cryptography>=3.0; python_full_version < "3.9.2"' in setup_src


# ── 6. field-failure reporting (AC-FFR-001) ──────────────────────────────
#
# When bootstrap fails hard, the ONLY thing that leaves the machine is a
# closed dict of aggregate facts: failure family, platform, which Python
# the bootstrap found. The 2026-08-29 cffi/MSVC failure was diagnosed
# from a photographed screen because nothing carried even that much.

FAILURE_PAYLOAD_KEYS = {
    "install_id", "event", "stage", "session_id", "failure_class",
    "bootstrap_python", "desktop_version", "os", "os_version", "arch",
}


@pytest.mark.parametrize(
    "snippet,code",
    [
        ("Error: No Python at 'C:\\Python312\\python.exe'", "broken_runtime"),
        ("Microsoft Visual C++ 14.0 or greater is required.", "compiler_demand"),
        ("ERROR: No matching distribution found for clawmetry", "no_distribution"),
        ("SSLError(SSLCertVerificationError)", "tls_intercepted"),
        ("Connection to pypi.org timed out.", "network"),
        ("PermissionError: [WinError 5] Access is denied", "permissions"),
        ("something novel exploded", "pip_unknown"),
    ],
)
def test_pip_failures_classify_to_closed_codes(snippet, code):
    assert dapp.RuntimeSupervisor._classify_pip_failure(snippet) == code
    # every code renders a hint — the enum and the hint table move together
    assert dapp._PIP_FAILURE_HINTS[code]


def test_failure_payload_is_a_closed_dict_of_aggregates(tmp_path, monkeypatch):
    monkeypatch.setattr(dapp, "_install_id", lambda: "0123456789abcdef0123456789abcdef")
    p = dapp.bootstrap_failure_payload("sess-1", "compiler_demand", "3.14")
    assert set(p) == FAILURE_PAYLOAD_KEYS, (
        "the payload is a CLOSED contract — a new key is a new disclosure "
        "and must be added here and in the blueprint deliberately"
    )
    assert p["stage"] == "bootstrap_failed"
    assert p["failure_class"] == "compiler_demand"
    assert p["bootstrap_python"] == "3.14"
    import os as _os
    for k, v in p.items():
        s = str(v)
        assert _os.sep not in s and "/" not in s and "\\" not in s, (
            f"{k} carries a path-like value: {s!r} — paths never leave the machine"
        )
        assert _os.environ.get("USER", "\x00") not in s or not _os.environ.get("USER")


def test_failure_payload_clamps_hostile_values(monkeypatch):
    monkeypatch.setattr(dapp, "_install_id", lambda: "x")
    p = dapp.bootstrap_failure_payload("s", "A" * 200, "9" * 50)
    assert len(p["failure_class"]) <= 40
    assert len(p["bootstrap_python"]) <= 8


def test_failure_ping_respects_optout(monkeypatch):
    sent = []
    monkeypatch.setattr(dapp, "_telemetry_optout", lambda: True)
    monkeypatch.setattr(dapp.threading, "Thread",
                        lambda **kw: sent.append(kw) or _FakeThread())
    assert dapp.bootstrap_failure_ping("s", "network", "3.12") is False
    assert not sent, "opted-out machines send nothing (AC-FFR-001.2)"


class _FakeThread:
    def start(self):
        pass


def test_failure_ping_fires_when_allowed(monkeypatch):
    captured = {}

    def fake_thread(**kw):
        captured.update(kw)
        return _FakeThread()

    monkeypatch.setattr(dapp, "_telemetry_optout", lambda: False)
    monkeypatch.setattr(dapp, "_read_config", lambda: {})
    monkeypatch.setattr(dapp, "_app_base", lambda cfg: "https://app.example")
    monkeypatch.setattr(dapp, "_install_id", lambda: "abc123")
    monkeypatch.setattr(dapp.threading, "Thread", fake_thread)
    assert dapp.bootstrap_failure_ping("sess", "compiler_demand", "3.14") is True
    payload = captured["args"][0]
    assert payload["failure_class"] == "compiler_demand"
    assert payload["session_id"] == "sess"
    assert captured["target"] is dapp._post_open_ping


def test_failure_ping_skips_selfhosted(monkeypatch):
    # an enterprise/self-hosted endpoint means _app_base returns None —
    # the deployment's data never phones the managed cloud
    monkeypatch.setattr(dapp, "_telemetry_optout", lambda: False)
    monkeypatch.setattr(dapp, "_read_config", lambda: {"endpoint": "https://own"})
    assert dapp.bootstrap_failure_ping("s", "network", "") is False


def test_bootstrap_records_failure_class_on_pip_failure(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py
    assert sup._create_venv(py)
    monkeypatch.setattr(
        sup, "_pip_install_clawmetry",
        lambda: (1, "Microsoft Visual C++ 14.0 or greater is required."))
    assert sup.bootstrap() is False
    assert sup.failure_class == "compiler_demand"


def test_bootstrap_reports_a_blocked_index_as_network(tmp_path, monkeypatch):
    """The class bootstrap() stamps is what the field report carries, so
    the #5628 fix has to survive the whole wiring — not just the
    classifier in isolation. A refused index must reach the report as
    `network`, and the splash must not mention Python."""
    sup = _sup(tmp_path)
    py = dapp._bootstrap_python()
    assert py
    assert sup._create_venv(py)
    seen = []
    monkeypatch.setattr(sup, "on_status", seen.append)
    monkeypatch.setattr(sup, "_pip_install_clawmetry", lambda: (1, _REFUSED))
    assert sup.bootstrap() is False
    assert sup.failure_class == "network"
    shown = " ".join(seen).lower()
    assert "install failed" in shown
    assert "python 3.11+" not in shown, (
        "the splash told a 3.11 machine to install 3.11+ (#5628)"
    )


# ── 6b. provide an interpreter, do not ask for one ───────────────────────
#
# Python is a dependency the shell installs, not a prerequisite it asks
# for — that is already how a machine with NO python is handled, and a
# machine whose python has no usable wheels is the same problem one step
# later. #5628 is what asking looks like from the user's side: a Python
# 3.11 machine told to install Python 3.11+.
#
# The pinned interpreter is deliberately NOT the newest one. Wheel
# coverage lags a Python release, so "install the latest Python" is the
# failure mode, not the fix (2026-08-29: python.org 3.14 had no cffi
# cp314 wheel, pip fell back to an sdist and demanded MSVC).

_NO_WHEEL_FOR_INTERPRETER = (
    "ERROR: Could not find a version that satisfies the requirement "
    "duckdb!=1.4.5,>=0.10 (from clawmetry) (from versions: 0.9.0, 0.10.0)\n"
    "ERROR: No matching distribution found for duckdb!=1.4.5,>=0.10"
)


def _windows(monkeypatch):
    monkeypatch.setattr(dapp.platform, "system", lambda: "Windows")


def test_pinned_interpreter_is_not_the_latest_python():
    """A regression guard on the pin itself: the shell must name one
    known-good minor, and the winget id and install dir must agree with
    it or `_known_good_python()` cannot find what winget put down."""
    minor = dapp.KNOWN_GOOD_PYTHON_MINOR
    assert re.fullmatch(r"3\.\d+", minor)
    assert dapp.KNOWN_GOOD_PYTHON_WINGET_ID == f"Python.Python.{minor}"
    assert dapp.KNOWN_GOOD_PYTHON_DIRNAME == "Python" + minor.replace(".", "")
    # Nothing user-facing may send someone to fetch the newest Python.
    # Keyed on what the sentence ASKS ("install ... python"), not on the
    # download host: the rule is about the version a user ends up with,
    # whatever page they get it from.
    for code, hint in dapp._PIP_FAILURE_HINTS.items():
        low = hint.lower()
        assert "latest python" not in low, code
        if "install" in low and "python" in low:
            assert minor in hint, (
                f"{code} asks the user to install Python without naming "
                f"the pinned {minor}; a range invites the newest "
                f"interpreter, which is the one most likely to have no "
                f"wheels"
            )


def test_no_wheel_failure_installs_a_supported_python_and_retries(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    _windows(monkeypatch)
    sup.bootstrap_python_version = "3.14"
    installed = []
    monkeypatch.setattr(dapp, "_winget_install_python",
                        lambda log: installed.append(True))
    # winget "puts down" the pinned interpreter
    good = "C:\\Users\\x\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
    monkeypatch.setattr(dapp, "_known_good_python",
                        lambda: good if installed else None)
    rebuilt = []
    monkeypatch.setattr(sup, "_create_venv",
                        lambda py: rebuilt.append(py) or True)
    monkeypatch.setattr(sup, "_pip_install_clawmetry", lambda: (0, "ok"))

    rc, out = sup._retry_on_known_good_python(1, _NO_WHEEL_FOR_INTERPRETER)
    assert rc == 0, "a supported interpreter was available; pip must be retried"
    assert installed, "the shell must install Python itself, not ask the user"
    assert rebuilt == [good], (
        "the retry must use the PINNED interpreter by path — re-probing "
        "would hit the `py` launcher, which resolves to the newest "
        "interpreter: the one that has no wheels"
    )
    assert sup.bootstrap_python_version == dapp.KNOWN_GOOD_PYTHON_MINOR


@pytest.mark.parametrize("output", [
    _REFUSED,                                    # network
    _SELF_SIGNED,                                # tls_intercepted
    "PermissionError: [WinError 5] Access is denied",
])
def test_no_python_is_installed_when_python_is_not_the_problem(
        output, tmp_path, monkeypatch):
    """A blocked proxy, an intercepted handshake and an AV-blocked folder
    are not fixed by a new interpreter. Downloading ~30 MB of Python to
    fail identically is the kind of thing that reads as broken software.
    This is also why the #5628 classifier fix has to land first: before
    it, a refused index WAS `no_distribution` and would have triggered
    this install."""
    sup = _sup(tmp_path)
    _windows(monkeypatch)
    monkeypatch.setattr(dapp, "_winget_install_python",
                        lambda log: pytest.fail("installed Python for "
                                                "a non-interpreter failure"))
    monkeypatch.setattr(dapp, "_known_good_python",
                        lambda: pytest.fail("probed for an interpreter"))
    assert sup._retry_on_known_good_python(1, output) == (1, output)


def test_retry_failure_reports_the_interpreter_that_actually_ran(
        tmp_path, monkeypatch):
    """Field failure #5711: telemetry showed 'no_distribution' on Windows
    py3.11 while the pinned interpreter is 3.12, which only happens if the
    retry engaged, rebuilt on 3.12, failed again, and the failure was
    classified from THAT output while bootstrap_python_version still said
    the pre-retry interpreter. Once the venv is rebuilt on the pinned
    interpreter, every pip run from then on — success or failure — is
    against that interpreter, and the reported version must say so."""
    sup = _sup(tmp_path)
    _windows(monkeypatch)
    sup.bootstrap_python_version = "3.11"
    good = "C:\\Users\\x\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
    monkeypatch.setattr(dapp, "_winget_install_python", lambda log: None)
    monkeypatch.setattr(dapp, "_known_good_python", lambda: good)
    monkeypatch.setattr(sup, "_create_venv", lambda py: True)
    still_broken = (
        "ERROR: Could not find a version that satisfies the requirement "
        "clawmetry>=0.12.826\n"
        "ERROR: No matching distribution found for clawmetry>=0.12.826"
    )
    monkeypatch.setattr(sup, "_pip_install_clawmetry",
                        lambda: (1, still_broken))

    rc, out = sup._retry_on_known_good_python(1, _NO_WHEEL_FOR_INTERPRETER)

    assert rc == 1
    assert out == still_broken
    assert sup.bootstrap_python_version == dapp.KNOWN_GOOD_PYTHON_MINOR, (
        "the retry ran on the pinned interpreter, so the reported version "
        "must reflect that even though the retry also failed — otherwise "
        "the field-failure report blames the wrong Python"
    )


def test_no_retry_when_already_on_the_pinned_interpreter(tmp_path, monkeypatch):
    """Nothing left to try, so do not download Python to reinstall the
    interpreter we are already running on."""
    sup = _sup(tmp_path)
    _windows(monkeypatch)
    sup.bootstrap_python_version = dapp.KNOWN_GOOD_PYTHON_MINOR
    monkeypatch.setattr(dapp, "_winget_install_python",
                        lambda log: pytest.fail("reinstalled the same Python"))
    assert sup._retry_on_known_good_python(
        1, _NO_WHEEL_FOR_INTERPRETER) == (1, _NO_WHEEL_FOR_INTERPRETER)


def test_original_failure_survives_when_no_interpreter_can_be_provided(
        tmp_path, monkeypatch):
    """winget is missing or blocked (a locked-down machine): the user
    must still get the accurate hint for the ORIGINAL failure, not a
    silent success or a different error."""
    sup = _sup(tmp_path)
    _windows(monkeypatch)
    monkeypatch.setattr(dapp, "_winget_install_python", lambda log: None)
    monkeypatch.setattr(dapp, "_known_good_python", lambda: None)
    monkeypatch.setattr(sup, "_pip_install_clawmetry",
                        lambda: pytest.fail("retried with no interpreter"))
    rc, out = sup._retry_on_known_good_python(1, _NO_WHEEL_FOR_INTERPRETER)
    assert (rc, out) == (1, _NO_WHEEL_FOR_INTERPRETER)
    assert sup._classify_pip_failure(out) == "no_distribution"


def test_interpreter_retry_is_windows_only(tmp_path, monkeypatch):
    """macOS ships /usr/bin/python3 and Linux has a package manager; the
    shell does not install interpreters there, and `_known_good_python`
    has no meaningful path to look in."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(dapp, "_winget_install_python",
                        lambda log: pytest.fail("ran winget off Windows"))
    assert sup._retry_on_known_good_python(
        1, _NO_WHEEL_FOR_INTERPRETER) == (1, _NO_WHEEL_FOR_INTERPRETER)


def test_known_good_python_falls_back_to_py_launcher_for_system_install(
        tmp_path, monkeypatch):
    """Python 3.12 installed system-wide (not at the per-user LOCALAPPDATA
    path) is found via 'py -3.12' and returned.  Covers machines where winget
    installs to a non-standard location or the user ran the python.org
    installer in system/all-users mode."""
    _windows(monkeypatch)
    # Per-user path is absent: point LOCALAPPDATA at a dir with no Python3x.
    monkeypatch.setenv("LOCALAPPDATA", "/no-such-localappdata")
    # Suppress the Windows-only creationflags that don't exist on Linux.
    monkeypatch.setattr(dapp, "_win_subprocess_kwargs", lambda: {})

    # A real file for Path(path).exists() to find.
    system_exe = str(tmp_path / "python.exe")
    (tmp_path / "python.exe").write_text("")

    import subprocess as _sp

    def fake_run(cmd, **kwargs):
        if (len(cmd) >= 3
                and cmd[1] == f"-{dapp.KNOWN_GOOD_PYTHON_MINOR}"
                and "-c" in cmd):
            return _sp.CompletedProcess(cmd, 0, system_exe + "\n", "")
        return _sp.CompletedProcess(cmd, 1, "", "not found")

    monkeypatch.setattr(dapp.shutil, "which",
                        lambda name: "/usr/bin/py" if name == "py" else None)
    monkeypatch.setattr(dapp.subprocess, "run", fake_run)

    result = dapp._known_good_python()
    assert result == system_exe, (
        "when the LOCALAPPDATA path is absent, _known_good_python() must "
        "probe 'py -3.12' to find a system-wide Python 3.12"
    )


def test_known_good_python_skips_py_launcher_when_absent(monkeypatch):
    """If the py launcher is not on PATH, the fallback is skipped and
    _known_good_python() returns None without spawning any subprocess."""
    _windows(monkeypatch)
    monkeypatch.setenv("LOCALAPPDATA", "/no-such-localappdata")
    monkeypatch.setattr(dapp, "_win_subprocess_kwargs", lambda: {})
    monkeypatch.setattr(dapp.shutil, "which", lambda name: None)
    called = []
    monkeypatch.setattr(dapp.subprocess, "run",
                        lambda *a, **k: called.append(a) or None)
    result = dapp._known_good_python()
    assert result is None
    assert not called, "subprocess.run must not be called when py is absent"


def test_probe_caches_interpreter_version(tmp_path):
    cache = tmp_path / "bootstrap-python.json"
    py = dapp._bootstrap_python(cache)
    assert py
    v = dapp._bootstrap_python_version(cache)
    assert v and len(v.split(".")) == 2, f"cache must carry major.minor, got {v!r}"


def test_version_reader_tolerates_legacy_cache(tmp_path):
    cache = tmp_path / "bootstrap-python.json"
    cache.write_text('{"python": "/usr/bin/python3"}')
    assert dapp._bootstrap_python_version(cache) == ""
    assert dapp._bootstrap_python_version(None) == ""


def test_probe_caches_interpreter_platform_tag(tmp_path):
    """bootstrap.log must be able to say WHICH interpreter pip resolved
    for. The version alone cannot: win32 has no duckdb wheel at any
    Python version, so "3.11" was never enough to diagnose #5628."""
    cache = tmp_path / "bootstrap-python.json"
    assert dapp._bootstrap_python(cache)
    tag = dapp._bootstrap_python_platform(cache)
    assert tag and tag == sysconfig.get_platform()[:24]


def test_platform_reader_tolerates_legacy_and_hostile_cache(tmp_path):
    cache = tmp_path / "bootstrap-python.json"
    cache.write_text('{"python": "/usr/bin/python3"}')
    assert dapp._bootstrap_python_platform(cache) == ""
    cache.write_text('{"platform": "win-amd64; rm -rf /"}')
    assert dapp._bootstrap_python_platform(cache) == ""
    assert dapp._bootstrap_python_platform(None) == ""


# ── 6c. a pip "success" that installed an ancient release (#5639) ────────
#
# Without a version floor, `pip install --upgrade clawmetry` does not
# FAIL when a dependency has no wheel for the interpreter — it backtracks
# clawmetry ITSELF until the graph resolves. Measured against live PyPI
# on py3.11 with the --only-binary=:all: this shell uses on Windows:
#
#   win32     -> clawmetry 0.12.163   (from before duckdb was a dep)
#   win_arm64 -> clawmetry 0.12.793
#   win_amd64 -> clawmetry 0.12.827   (current)
#
# Nothing errors. The dist-info is complete, the entry point exists, the
# splash clears, and the machine runs a 664-release-old ClawMetry — a
# failure no field report can see, because from the shell's side the
# install succeeded. Worse than the failure it replaced.


def test_version_tuple_orders_releases_numerically():
    """0.12.9 vs 0.12.10 is why this is not a string compare — and the
    floor check and the dist-info picker must agree about "older"."""
    assert dapp._version_tuple("0.12.9") < dapp._version_tuple("0.12.10")
    assert dapp._version_tuple("0.12.163") < dapp._version_tuple("0.12.827")
    assert dapp._version_tuple("dev") is None
    assert dapp._version_tuple("") is None
    assert dapp._version_tuple("1.0.0rc1") is None


def test_pip_requirement_is_floored_at_the_bundle_version(monkeypatch):
    """The bundle's own stamp is the floor: this shell was BUILT at that
    release, so PyPI demonstrably has it. `>=` and not `==` on purpose —
    pip may still backtrack for a legitimate reason (a propagation race
    right after a release), just never past the shell's own age."""
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "0.12.826")
    assert dapp._pip_requirement() == "clawmetry>=0.12.826"


def test_pip_requirement_is_bare_for_an_unstamped_dev_build(monkeypatch):
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "dev")
    assert dapp._pip_requirement() == "clawmetry"


def test_pip_install_passes_the_floor_on_every_attempt(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "0.12.826")
    seen = []

    def fake(argv, timeout):
        seen.append(argv)
        return subprocess.CompletedProcess(argv, 1, "", "boom")

    monkeypatch.setattr(sup, "_run_child", fake)
    sup._pip_install_clawmetry()
    installs = [a for a in seen if "install" in a and "--upgrade" in a
                and "pip" not in a[-1:]]
    targets = [a[-1] for a in installs]
    assert targets, "no pip install attempt was made"
    assert all(t == "clawmetry>=0.12.826" for t in targets), (
        f"a bare `clawmetry` lets pip backtrack past the floor: {targets}"
    )


def test_warm_launch_does_not_trust_an_install_older_than_the_shell(
        tmp_path, monkeypatch):
    """The heal for machines ALREADY stranded. A backtracked install is
    COMPLETE, so the warm-launch short-circuit accepted it and booted an
    ancient ClawMetry on every relaunch, permanently."""
    sup = _sup(tmp_path)
    exe = sup._venv_clawmetry()
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("stub")
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "0.12.826")
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "0.12.163")
    # Falling through to the install path is the observable behaviour;
    # with no usable python that path ends in no_python.
    monkeypatch.setattr(dapp, "_bootstrap_python", lambda cache_file=None: None)
    monkeypatch.setattr(dapp.platform, "system", lambda: "Linux")
    assert sup.bootstrap() is False
    assert sup.failure_class == "no_python"


def test_warm_launch_still_trusts_a_current_install(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    exe = sup._venv_clawmetry()
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("stub")
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "0.12.826")
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "0.12.827")
    monkeypatch.setattr(dapp, "_bootstrap_python", lambda cache_file=None: (
        pytest.fail("healthy warm launch must not probe interpreters")))
    assert sup.bootstrap() is True


def test_old_version_heal_is_latched_to_one_attempt(tmp_path, monkeypatch):
    """The heal reruns pip on the boot path, and on Windows a floored
    failure now provisions an interpreter — so a check that fired every
    launch would mean a pip run (and possibly a winget install) on every
    launch of a machine it cannot fix. One attempt per stranded version,
    then the launch proceeds: a ClawMetry that is behind still beats a
    shell that will not open."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "0.12.826")
    assert sup._is_stranded_on_an_old_version("0.12.163") is True
    assert sup._is_stranded_on_an_old_version("0.12.163") is False, (
        "the same stranded version must not re-trigger the heal"
    )
    # A DIFFERENT stranded version is a new situation and gets its turn.
    assert sup._is_stranded_on_an_old_version("0.12.200") is True


def test_unstamped_build_never_strands(tmp_path, monkeypatch):
    """A developer checkout has no stamp, so there is no floor to compare
    against — it must not start reinstalling on every launch."""
    sup = _sup(tmp_path)
    monkeypatch.setattr(dapp, "_desktop_version", lambda: "dev")
    assert sup._is_stranded_on_an_old_version("0.12.163") is False


@pytest.mark.parametrize("script", ["install.ps1", "install-clawmetry.ps1"])
def test_windows_installers_verify_the_dependency_set(script):
    """The CLI installers take the same `--only-binary=:all:` path and so
    inherit the same silent backtrack. They have no bundle stamp to floor
    against, so they check the result FUNCTIONALLY instead: a release old
    enough to have been backtracked to does not carry today's dependency
    set. Threshold-free, and it stays correct as that set changes."""
    text = (REPO_ROOT / script).read_text(encoding="utf-8")
    assert "import clawmetry, duckdb, cryptography" in text, (
        f"{script} does not verify that the install it just made can "
        f"actually import its dependencies (#5639)"
    )
    body = text.split("import clawmetry, duckdb, cryptography", 1)[1]
    assert "exit 1" in body, f"{script} detects the bad install but continues"


# ── 7. an exe stub is not an install (package-corpse recovery) ───────────
#
# Live field case 2026-08-29, second failure of the day on the same
# machine: the watcher's in-place `clawmetry update` fired seconds after
# a release, pip uninstalled the old package and failed to install the
# new one while the daemon held clawmetry.exe open. Result: an exe stub
# with no clawmetry module. The warm-launch short-circuit trusted the
# stub, so every relaunch showed "Daemon did not come up" forever, and
# the watcher shelled the corpse to update itself every 60s forever.


def test_warm_launch_requires_a_complete_install(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    exe = sup._venv_clawmetry()
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("stub")
    # no dist-info anywhere -> the install is a corpse
    monkeypatch.setattr(sup, "_get_installed_version", lambda: None)
    # prove bootstrap FALLS THROUGH to the install path rather than
    # trusting the stub: with no usable python it must fail with
    # no_python (the old code returned True here and bricked relaunches)
    monkeypatch.setattr(dapp, "_bootstrap_python", lambda cache_file=None: None)
    monkeypatch.setattr(dapp.platform, "system", lambda: "Linux")
    assert sup.bootstrap() is False
    assert sup.failure_class == "no_python"


def test_warm_launch_stays_fast_when_install_is_complete(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    exe = sup._venv_clawmetry()
    exe.parent.mkdir(parents=True, exist_ok=True)
    exe.write_text("stub")
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "1.2.3")

    def boom(cache_file=None):
        raise AssertionError("healthy warm launch must not probe interpreters")

    monkeypatch.setattr(dapp, "_bootstrap_python", boom)
    assert sup.bootstrap() is True


def test_corpse_heal_reinstalls_only_on_the_corpse_signature(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    calls = []
    monkeypatch.setattr(sup, "_pip_install_clawmetry",
                        lambda: calls.append(1) or (0, "ok"))

    monkeypatch.setattr(sup, "_get_installed_version", lambda: None)
    sup._heal_package_corpse("Connection to pypi.org timed out")
    assert not calls, "transient update failures must not trigger reinstalls"

    sup._heal_package_corpse("ModuleNotFoundError: No module named 'clawmetry'")
    assert len(calls) == 1, "the corpse signature must trigger a reinstall"


def test_corpse_heal_noops_when_package_is_actually_present(tmp_path, monkeypatch):
    sup = _sup(tmp_path)
    calls = []
    monkeypatch.setattr(sup, "_pip_install_clawmetry",
                        lambda: calls.append(1) or (0, "ok"))
    monkeypatch.setattr(sup, "_get_installed_version", lambda: "1.2.3")
    sup._heal_package_corpse("No module named 'somethingelse'")
    assert not calls
