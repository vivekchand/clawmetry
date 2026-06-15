"""CI guard against paid runtime adapters leaking back into the OSS repo.

Phase 4 of the open-core split (PR #2335) moved the 10 paid runtime
adapters out of ``clawmetry/adapters/`` and into the closed-source
``clawmetry_pro`` package. ``clawmetry/sync.py::_FAMILY_ADAPTER_SPECS``
now imports them by absolute path (``clawmetry_pro.adapters.<runtime>``)
and the imports fail gracefully on OSS-only installs.

Nothing today PINS that invariant. A future PR that naively re-adds
``clawmetry/adapters/claude_code.py`` (or flips a spec from
``clawmetry_pro.adapters.*`` back to ``clawmetry.adapters.*``) would
ship the paid runtime in the public wheel and bypass the licence gate.

These tests catch that class of regression before it lands. They run
with no network, no daemon, no ``clawmetry_pro`` installed -- pure
filesystem + import inspection.
"""
from __future__ import annotations

import ast
import importlib
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTERS_DIR = REPO_ROOT / "clawmetry" / "adapters"
SYNC_PATH = REPO_ROOT / "clawmetry" / "sync.py"


def test_paid_runtime_adapter_modules_absent_from_oss_tree():
    """No ``clawmetry/adapters/<paid_runtime>.py`` may exist."""
    from clawmetry.entitlements import PAID_RUNTIMES

    leaks = []
    for runtime in sorted(PAID_RUNTIMES):
        candidate = ADAPTERS_DIR / f"{runtime}.py"
        if candidate.exists():
            leaks.append(str(candidate.relative_to(REPO_ROOT)))

    assert not leaks, (
        f"Paid runtime adapter file(s) leaked into the OSS repo: {leaks}. "
        f"These modules must live in clawmetry-pro and load via the "
        f"clawmetry.extensions entry point -- never inline in "
        f"clawmetry/adapters/."
    )


def test_adapters_dir_contains_only_plumbing_and_free_runtimes():
    """The OSS adapter dir should only contain shared plumbing plus Free runtimes."""
    plumbing = {"__init__.py", "base.py", "registry.py", "README.md"}
    free_runtime_files = {"openclaw.py", "nemo.py"}
    allowed = plumbing | free_runtime_files

    from clawmetry.entitlements import PAID_RUNTIMES

    actual = {
        p.name
        for p in ADAPTERS_DIR.iterdir()
        if p.name != "__pycache__" and not p.name.startswith(".")
    }
    paid_leaks = {
        n for n in actual - allowed if n.removesuffix(".py") in PAID_RUNTIMES
    }
    assert not paid_leaks, (
        f"Paid runtime adapter file(s) found in clawmetry/adapters/: "
        f"{sorted(paid_leaks)}. These belong in clawmetry-pro."
    )


def _parse_family_adapter_specs() -> list:
    """Source-parse ``_FAMILY_ADAPTER_SPECS`` from sync.py without importing it."""
    tree = ast.parse(SYNC_PATH.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "_FAMILY_ADAPTER_SPECS" not in targets:
            continue
        if not isinstance(node.value, ast.Tuple):
            return []
        specs = []
        for elt in node.value.elts:
            if not isinstance(elt, ast.Tuple) or len(elt.elts) != 2:
                continue
            mod_node, cls_node = elt.elts
            if not (isinstance(mod_node, ast.Constant) and isinstance(cls_node, ast.Constant)):
                continue
            specs.append((str(mod_node.value), str(cls_node.value)))
        return specs
    return []


def test_family_adapter_specs_only_reference_clawmetry_pro():
    """Every entry in ``_FAMILY_ADAPTER_SPECS`` must import from ``clawmetry_pro.adapters.*``."""
    specs = _parse_family_adapter_specs()
    assert specs, (
        "Could not parse _FAMILY_ADAPTER_SPECS from clawmetry/sync.py -- "
        "did the constant get renamed?"
    )
    bad = [
        (mod, cls)
        for (mod, cls) in specs
        if not mod.startswith("clawmetry_pro.adapters.")
    ]
    assert not bad, (
        f"_FAMILY_ADAPTER_SPECS entries must live under "
        f"clawmetry_pro.adapters.* -- found: {bad}."
    )


def test_family_adapter_specs_cover_every_paid_runtime():
    """Every member of ``PAID_RUNTIMES`` must appear in ``_FAMILY_ADAPTER_SPECS``."""
    from clawmetry.entitlements import PAID_RUNTIMES

    specs = _parse_family_adapter_specs()
    spec_runtimes = {mod.rsplit(".", 1)[1] for (mod, _cls) in specs}
    missing = set(PAID_RUNTIMES) - spec_runtimes
    extras = spec_runtimes - set(PAID_RUNTIMES)
    assert not missing, (
        f"_FAMILY_ADAPTER_SPECS missing a row for paid runtime(s): "
        f"{sorted(missing)}."
    )
    assert not extras, (
        f"_FAMILY_ADAPTER_SPECS references runtime(s) absent from "
        f"PAID_RUNTIMES: {sorted(extras)}."
    )


def test_family_adapter_specs_skip_every_free_runtime():
    """Free runtimes must NOT appear in ``_FAMILY_ADAPTER_SPECS``."""
    from clawmetry.entitlements import FREE_RUNTIMES

    specs = _parse_family_adapter_specs()
    spec_runtimes = {mod.rsplit(".", 1)[1] for (mod, _cls) in specs}
    leaked_free = set(FREE_RUNTIMES) & spec_runtimes
    assert not leaked_free, (
        f"Free runtime(s) routed through _FAMILY_ADAPTER_SPECS: "
        f"{sorted(leaked_free)}."
    )


def test_clawmetry_adapters_package_exposes_no_paid_adapter_class():
    """Importing ``clawmetry.adapters`` must not surface a paid-adapter class."""
    from clawmetry.entitlements import PAID_RUNTIMES

    adapters_pkg = importlib.import_module("clawmetry.adapters")
    surfaced = set(dir(adapters_pkg))
    leaks = []
    for runtime in sorted(PAID_RUNTIMES):
        camel = "".join(part.capitalize() for part in runtime.split("_"))
        for candidate in (f"{camel}Adapter", f"{camel}ClawAdapter"):
            if candidate in surfaced:
                leaks.append(candidate)
    assert not leaks, (
        f"clawmetry.adapters exposes paid runtime adapter class(es): {leaks}."
    )


def test_registry_does_not_pre_register_paid_runtimes():
    """``clawmetry.adapters.registry`` must not pre-register paid runtimes."""
    from clawmetry.entitlements import PAID_RUNTIMES
    from clawmetry.adapters import registry as _reg

    pre_registered = [getattr(a, "name", "") for a in _reg.all_adapters()]
    paid_pre = [n for n in pre_registered if n in PAID_RUNTIMES]
    assert not paid_pre, (
        f"Paid runtime(s) pre-registered in clawmetry.adapters.registry: {paid_pre}."
    )
