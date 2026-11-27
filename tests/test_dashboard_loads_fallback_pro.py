"""The dashboard process must make a HOME-installed clawmetry-pro importable.

Burned 2026-11-15 on a Jetson: ``curl … install.sh | bash`` as root put the Pro
wheel in the HOME fallback dir (``~/.clawmetry/pro-packages``) because the
interpreter site-packages was not writable. The sync daemon called
``ensure_pro_on_path()`` and loaded Pro fine, but the *dashboard* process never
did — so ``load_plugins()`` found nothing, ``plugin_count`` was 0, ``/robotics``
returned 404 and the Physical AI tab never appeared. Nothing was logged: a
plugin that is not importable is indistinguishable from one that is not
installed. Starting the same binary with
``PYTHONPATH=~/.clawmetry/pro-packages`` turned every one of those back on.

``ensure_pro_on_path``'s own docstring already said "Call this at
daemon/dashboard startup BEFORE plugin discovery" — the dashboard half was
never wired up.

Invariant: by the time ``dashboard`` has finished importing, the fallback dir
is on ``sys.path``, so plugin discovery can see what is installed there.
"""
import json
import os
import subprocess
import sys
import textwrap

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Run the probe in a child process: ``sys.path`` and an already-imported
# ``dashboard`` are process-global, so an in-process check would be polluted by
# whatever the rest of the suite imported first.
_PROBE = textwrap.dedent(
    """
    import json, sys
    import dashboard  # noqa: F401  -- the import is what we are testing
    from clawmetry import license as lic
    import importlib.util as _u
    print("CM_RESULT " + json.dumps({
        "fallback_on_path": lic._PRO_FALLBACK_DIR in sys.path,
        "marker_importable": _u.find_spec("cm_fake_pro") is not None,
    }))
    """
)


def _probe_with_home(home):
    """Import ``dashboard`` in a child whose HOME holds a fallback-installed
    package, and report what that child could see."""
    env = dict(os.environ)
    # ``expanduser`` reads HOME on POSIX and USERPROFILE on Windows; set both so
    # the probe looks at the temp dir on either.
    env["HOME"] = env["USERPROFILE"] = str(home)
    env.pop("PYTHONPATH", None)          # the bug's workaround — must not be the thing that passes
    env["CLAWMETRY_NO_BROWSER"] = "1"
    proc = subprocess.run([sys.executable, "-c", _PROBE], cwd=REPO_ROOT, env=env,
                          capture_output=True, text=True, timeout=180)
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("CM_RESULT ")), None)
    assert line, f"probe did not report\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr[-2000:]}"
    return json.loads(line[len("CM_RESULT "):])


def test_dashboard_import_puts_fallback_pro_on_sys_path(tmp_path):
    fallback = tmp_path / ".clawmetry" / "pro-packages" / "cm_fake_pro"
    fallback.mkdir(parents=True)
    (fallback / "__init__.py").write_text("VERSION = '9.9.9'\n", encoding="utf-8")

    result = _probe_with_home(tmp_path)

    assert result["fallback_on_path"], (
        "importing dashboard left ~/.clawmetry/pro-packages off sys.path, so a "
        "HOME-installed clawmetry-pro stays invisible to load_plugins()")
    assert result["marker_importable"], (
        "a package installed in the HOME fallback dir was not importable after "
        "the dashboard finished importing")


def test_absent_fallback_dir_is_not_added(tmp_path):
    """No fallback install, nothing invented: a non-existent dir must not be
    pushed onto sys.path, where it would shadow real imports."""
    result = _probe_with_home(tmp_path)

    assert not result["fallback_on_path"], (
        "a fallback dir that does not exist was still added to sys.path")
    assert not result["marker_importable"]


# ── the diagnostic probe must not report a fallback install as absent ────────
#
# ``clawmetry status`` and ``GET /api/extensions`` call ``probe_plugins()`` from
# processes that never ran ``load_plugins()``. Without the same path fix the
# probe reports a fallback-installed Pro as "not installed" -- which is how this
# bug was misdiagnosed in the first place.

_PROBE_ONLY = textwrap.dedent(
    """
    import json, sys
    from clawmetry import extensions as ext
    from clawmetry import license as lic
    ext.probe_plugins()
    print("CM_RESULT " + json.dumps({
        "fallback_on_path": lic._PRO_FALLBACK_DIR in sys.path,
        "marker_importable": True,
    }))
    """
)


def test_probe_plugins_puts_fallback_pro_on_sys_path(tmp_path):
    fallback = tmp_path / ".clawmetry" / "pro-packages" / "cm_fake_pro"
    fallback.mkdir(parents=True)
    (fallback / "__init__.py").write_text("VERSION = '9.9.9'\n", encoding="utf-8")

    env = dict(os.environ)
    env["HOME"] = env["USERPROFILE"] = str(tmp_path)
    env.pop("PYTHONPATH", None)
    proc = subprocess.run([sys.executable, "-c", _PROBE_ONLY], cwd=REPO_ROOT, env=env,
                          capture_output=True, text=True, timeout=180)
    line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("CM_RESULT ")), None)
    assert line, f"probe did not report\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr[-2000:]}"

    assert json.loads(line[len("CM_RESULT "):])["fallback_on_path"], (
        "probe_plugins() ran without putting ~/.clawmetry/pro-packages on "
        "sys.path, so `clawmetry status` reports a fallback-installed Pro as "
        "absent")
