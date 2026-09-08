"""CI guard against runtime-count drift in user-facing copy.

Sibling of ``test_advertised_runtimes_match_catalogue.py``: that one pins the
*set* of runtime ids, this one pins the *number* quoted in prose. Both hang off
``clawmetry/entitlements.py``.

Burned 2026-08-15: ``FREE_RUNTIMES | PAID_RUNTIMES`` had 20 entries while the
README said 14, the PyPI summary said 12 and FLYWHEEL.md said 12, over 27 stale
mentions in 16 files. Nobody noticed because every surface was edited by hand and
none of them were checked against the catalogue.
"""
from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "scripts" / "sync_runtime_count.py"


def _load_sync_module():
    spec = importlib.util.spec_from_file_location("sync_runtime_count", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def sync():
    assert SCRIPT.exists(), f"missing {SCRIPT}; the count guard cannot run"
    return _load_sync_module()


def test_script_parses_the_same_count_the_package_computes(sync):
    """The script regex-parses entitlements.py (setup.py does too, since it runs
    before the package is importable). If that parse ever diverges from the real
    ``len(ALL_RUNTIMES)``, every downstream surface is confidently wrong."""
    from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_COUNT

    assert RUNTIME_COUNT == len(ALL_RUNTIMES)
    assert sync.catalogue_count() == RUNTIME_COUNT, (
        f"scripts/sync_runtime_count.py parsed {sync.catalogue_count()} runtimes "
        f"but the catalogue has {RUNTIME_COUNT}. The frozenset literals in "
        f"entitlements.py were probably reformatted; update the regexes in the script."
    )


def test_no_surface_quotes_a_stale_runtime_count(sync):
    """Every "N runtimes" in shipped copy must equal the catalogue count."""
    drift = sync.check()
    if drift:
        detail = "\n".join(f"  {rel}:{n}: {found!r}" for rel, n, found, _ in drift)
        pytest.fail(
            f"{len(drift)} surface(s) quote a stale runtime count "
            f"(catalogue says {sync.catalogue_count()}):\n{detail}\n\n"
            f"Fix with: python3 scripts/sync_runtime_count.py"
        )


def test_pypi_summary_is_derived_not_hardcoded():
    """setup.py must compute its description, so the PyPI page cannot go stale.

    Checked by source-scan rather than by running setup.py, because importing it
    executes ``setup()``.
    """
    src = (REPO / "setup.py").read_text(encoding="utf-8")
    assert "entitlements.py" in src, "setup.py no longer reads the runtime catalogue"
    assert re.search(r"description=\(?\s*f?\"", src), "setup.py description is not an f-string"
    assert not re.search(
        r'description="ClawMetry - Real-time observability for \d+', src
    ), "setup.py hardcodes a runtime count again; derive it from entitlements.py"


def test_setup_py_description_reports_the_catalogue_count():
    """End to end: the string that reaches PyPI carries the real count."""
    from clawmetry.entitlements import RUNTIME_COUNT

    out = subprocess.run(
        [sys.executable, "setup.py", "--description"],
        cwd=REPO, capture_output=True, text=True, timeout=120,
    )
    assert out.returncode == 0, f"setup.py --description failed:\n{out.stderr[-2000:]}"
    summary = out.stdout.strip().splitlines()[-1]
    assert f"{RUNTIME_COUNT} AI agent runtimes" in summary, (
        f"PyPI summary does not carry the catalogue count {RUNTIME_COUNT}: {summary!r}"
    )


def test_readme_grid_names_every_supported_runtime():
    """A count alone is not enough: the README grid must name each runtime too.

    Burned in the same sweep: the grid listed 19 of 20 (DeepSeek Harness shipped
    to the catalogue and the landing page but never reached the README).
    """
    from clawmetry.entitlements import ALL_RUNTIMES, RUNTIME_LABELS

    readme = (REPO / "README.md").read_text(encoding="utf-8")
    # Label spelling in the README is allowed to be friendlier than the raw
    # catalogue label (e.g. "OpenAI Codex" for "Codex"), so match on the label
    # as a substring rather than requiring an exact token.
    missing = sorted(
        RUNTIME_LABELS[r] for r in ALL_RUNTIMES
        if RUNTIME_LABELS.get(r) and RUNTIME_LABELS[r] not in readme
    )
    assert not missing, (
        f"README.md never names these supported runtimes: {missing}. "
        f"Add them to the 'Works with N agent runtimes' grid."
    )
