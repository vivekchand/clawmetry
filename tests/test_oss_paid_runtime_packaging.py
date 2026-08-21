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
    plumbing = {"__init__.py", "base.py", "registry.py", "README.md", "cost.py"}
    free_runtime_files = {"openclaw.py", "nemo.py", "goose.py"}
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


def test_family_adapter_specs_route_paid_to_pro_and_free_to_oss():
    """Import path must match tier — this is the licence gate, in one line.

    A PAID runtime pointed at ``clawmetry.adapters.*`` would ship the paid
    adapter in the public wheel and bypass the gate entirely; that is the
    regression this file exists to catch and it stays fatal.

    A FREE runtime pointed at ``clawmetry_pro.adapters.*`` is the mirror-image
    bug and is equally fatal: the runtime would be advertised as free while its
    only reader sat behind a licence-gated wheel download, which is precisely
    the complaint that moved Goose into the free tier
    (``aaif-goose/goose#11282``).
    """
    from clawmetry.entitlements import FREE_RUNTIMES, PAID_RUNTIMES

    specs = _parse_family_adapter_specs()
    assert specs, (
        "Could not parse _FAMILY_ADAPTER_SPECS from clawmetry/sync.py -- "
        "did the constant get renamed?"
    )

    paid_in_oss, free_in_pro, unknown = [], [], []
    for mod, cls in specs:
        runtime = mod.rsplit(".", 1)[1]
        if mod.startswith("clawmetry_pro.adapters."):
            if runtime in FREE_RUNTIMES:
                free_in_pro.append((mod, cls))
        elif mod.startswith("clawmetry.adapters."):
            if runtime not in FREE_RUNTIMES:
                paid_in_oss.append((mod, cls))
        else:
            unknown.append((mod, cls))

    assert not paid_in_oss, (
        f"PAID runtime adapter(s) routed through the OSS package: "
        f"{paid_in_oss}. These must import from clawmetry_pro.adapters.* or "
        f"the paid adapter ships in the public wheel and the licence gate is "
        f"bypassed."
    )
    assert not free_in_pro, (
        f"FREE runtime adapter(s) routed through the closed wheel: "
        f"{free_in_pro}. A free runtime whose only reader needs a licence "
        f"download is not free — bundle it in clawmetry/adapters/."
    )
    assert not unknown, (
        f"_FAMILY_ADAPTER_SPECS entries must live under clawmetry_pro.adapters.* "
        f"(paid) or clawmetry.adapters.* (free) -- found: {unknown}."
    )
    # Sanity: the paid side is still the overwhelming majority, so a bulk
    # find/replace that flipped every row to the OSS path cannot pass.
    assert set(PAID_RUNTIMES) & {m.rsplit(".", 1)[1] for m, _ in specs}


def test_family_adapter_specs_cover_every_paid_runtime():
    """Every member of ``PAID_RUNTIMES`` must appear in ``_FAMILY_ADAPTER_SPECS``."""
    from clawmetry.entitlements import FREE_RUNTIMES, PAID_RUNTIMES

    specs = _parse_family_adapter_specs()
    spec_runtimes = {mod.rsplit(".", 1)[1] for (mod, _cls) in specs}
    missing = set(PAID_RUNTIMES) - spec_runtimes
    # openclaw / nemoclaw register directly in dashboard.py rather than through
    # the family loop, so the free side is a subset here, not an equality.
    extras = spec_runtimes - set(PAID_RUNTIMES) - set(FREE_RUNTIMES)
    assert not missing, (
        f"_FAMILY_ADAPTER_SPECS missing a row for paid runtime(s): "
        f"{sorted(missing)}."
    )
    assert not extras, (
        f"_FAMILY_ADAPTER_SPECS references runtime(s) in neither "
        f"PAID_RUNTIMES nor FREE_RUNTIMES: {sorted(extras)}."
    )


def test_free_runtime_specs_have_a_bundled_module():
    """A free runtime in the specs must have its adapter file in this repo.

    Pairs with the routing test above: that one proves the import *path*
    claims OSS, this one proves the file is actually there to import.
    """
    from clawmetry.entitlements import FREE_RUNTIMES

    specs = _parse_family_adapter_specs()
    for mod, cls in specs:
        if not mod.startswith("clawmetry.adapters."):
            continue
        runtime = mod.rsplit(".", 1)[1]
        assert runtime in FREE_RUNTIMES, (mod, cls)
        assert (ADAPTERS_DIR / f"{runtime}.py").exists(), (
            f"{mod}.{cls} is declared in _FAMILY_ADAPTER_SPECS but "
            f"clawmetry/adapters/{runtime}.py does not exist."
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
