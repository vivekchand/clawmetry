"""Guard: the pro wheel's declared runtime deps actually get installed.

The pro wheel is installed with ``--no-deps`` (it comes from the license
server, not PyPI, and pip must not touch clawmetry itself). But clawmetry-pro
declares runtime dependencies, and nothing installed them, so on a provisioned
install these three PAID paths raised ImportError behind a broad except:

    clawmetry_pro/compliance/engine.py   import yaml     (Compliance Pack)
    clawmetry_pro/adapters/deepagents.py import msgpack  (DeepAgents adapter)
    clawmetry_pro/routes/nemoclaw.py     import yaml     (NeMo governance)

Found 2026-08-22 when pip's resolver warned during an unrelated upgrade:
"clawmetry-pro 0.7.9 requires msgpack>=1.0, which is not installed".
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from clawmetry.license import _install_missing_requires, _wheel_runtime_requires


def _make_wheel(tmp_path, requires):
    """A minimal but REAL wheel carrying the given Requires-Dist lines."""
    whl = tmp_path / "clawmetry_pro-0.0.1-py3-none-any.whl"
    meta = ["Metadata-Version: 2.1", "Name: clawmetry-pro", "Version: 0.0.1"]
    meta += [f"Requires-Dist: {r}" for r in requires]
    with zipfile.ZipFile(whl, "w") as zf:
        zf.writestr("clawmetry_pro/__init__.py", "")
        zf.writestr("clawmetry_pro-0.0.1.dist-info/METADATA", "\n".join(meta) + "\n")
        zf.writestr("clawmetry_pro-0.0.1.dist-info/WHEEL",
                    "Wheel-Version: 1.0\nGenerator: test\nRoot-Is-Purelib: true\nTag: py3-none-any\n")
    return str(whl)


def test_reads_the_real_pro_dependency_set(tmp_path):
    """The exact Requires-Dist set clawmetry-pro 0.7.9 ships."""
    whl = _make_wheel(tmp_path, ["clawmetry", "msgpack>=1.0", "pyyaml>=5.0"])
    reqs = _wheel_runtime_requires(whl)
    names = sorted(n for _, n in reqs)
    assert names == ["msgpack", "pyyaml"], (
        "the wheel's declared runtime deps were not recovered from METADATA"
    )


def test_clawmetry_itself_is_never_resolved(tmp_path):
    """--no-deps exists so pip cannot touch this interpreter's clawmetry."""
    whl = _make_wheel(tmp_path, ["clawmetry", "clawmetry>=0.12", "msgpack>=1.0"])
    assert all(n != "clawmetry" for _, n in _wheel_runtime_requires(whl))


def test_extras_gated_requirements_are_skipped(tmp_path):
    whl = _make_wheel(tmp_path, ['msgpack>=1.0', 'sphinx; extra == "docs"'])
    assert sorted(n for _, n in _wheel_runtime_requires(whl)) == ["msgpack"]


def test_already_satisfied_deps_trigger_no_install(tmp_path, monkeypatch):
    """pytest is installed in every environment that runs this test."""
    whl = _make_wheel(tmp_path, ["pytest"])
    called = []
    monkeypatch.setattr("clawmetry.license._pip_run",
                        lambda args: (called.append(args), (True, "installed"))[1])
    out = _install_missing_requires(whl)
    assert called == [], "reinstalled a dependency that was already present"
    assert out == ""


def test_missing_deps_are_installed(tmp_path, monkeypatch):
    """The regression: a declared dep that is absent must be installed."""
    whl = _make_wheel(tmp_path, ["clawmetry", "definitely-not-installed-pkg>=1.0"])
    called = []

    def _fake_pip(args):
        called.append(args)
        return True, "installed"

    monkeypatch.setattr("clawmetry.license._pip_run", _fake_pip)
    out = _install_missing_requires(whl)
    assert called, "a missing declared dependency was never installed"
    assert "definitely-not-installed-pkg>=1.0" in called[0]
    assert "clawmetry" not in " ".join(called[0]).replace("clawmetry.license", "")
    assert "deps installed" in out


def test_install_failure_is_reported_not_swallowed(tmp_path, monkeypatch):
    """A degraded pack must say so rather than implying it is whole."""
    whl = _make_wheel(tmp_path, ["definitely-not-installed-pkg>=1.0"])
    monkeypatch.setattr("clawmetry.license._pip_run",
                        lambda args: (False, "network unreachable"))
    out = _install_missing_requires(whl)
    assert "MISSING" in out


def test_never_raises_on_a_broken_wheel(tmp_path):
    bad = tmp_path / "not-a-wheel.whl"
    bad.write_text("garbage")
    assert _wheel_runtime_requires(str(bad)) == []
    assert _install_missing_requires(str(bad)) == ""


# --------------------------------------------------------------- wiring

def test_pip_install_wheel_actually_installs_the_declared_deps(tmp_path, monkeypatch):
    """The helper existing is not enough: the install path must CALL it.

    Without this, _install_missing_requires can be silently unwired from
    _pip_install_wheel and every unit test above still passes, which is the
    exact shape of the original bug (a declared dependency nobody installs).
    """
    import clawmetry.license as L

    whl = _make_wheel(tmp_path, ["clawmetry", "definitely-not-installed-pkg>=1.0"])
    calls = []

    def _fake_pip(args):
        calls.append(list(args))
        return True, "installed"

    monkeypatch.setattr(L, "_pip_run", _fake_pip)
    monkeypatch.setattr(L, "_site_packages_target", lambda: ("/tmp/sp", True))

    ok, detail = L._pip_install_wheel(whl)
    assert ok, detail

    joined = [" ".join(c) for c in calls]
    assert any(whl in c for c in joined), "the wheel itself was never installed"
    assert any("definitely-not-installed-pkg" in c for c in joined), (
        "_pip_install_wheel succeeded without installing the wheel's declared "
        "runtime deps: the pro pack ships incomplete and paid features die on "
        "ImportError"
    )
    # The wheel install itself must still be --no-deps.
    wheel_call = next(c for c in calls if whl in " ".join(c))
    assert "--no-deps" in wheel_call
