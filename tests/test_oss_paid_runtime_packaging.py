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
with no network, no daemon, no ``clawmetry_pro`` installed — pure
filesystem + import inspection.

See also:

* ``test_advertised_runtimes_match_catalogue.py`` — pins the catalogue
  vs the marketing copy (which runtimes are advertised Free vs Paid).
  Symmetric: that guard says "every advertised runtime has an
  adapter or catalogue entry"; this one says "no paid runtime has an
  OSS adapter".

* ``test_oss_stubs_after_pro_move.py`` — pins the HTTP-route shape of
  the OSS stubs left behind after the Pro impl move. This file covers
  the adapter-packaging side of the same split.
"""
from __future__ import annotations

import ast
import importlib
import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
ADAPTERS_DIR = REPO_ROOT / "clawmetry" / "adapters"
SYNC_PATH = REPO_ROOT / "clawmetry" / "sync.py"


# ── filesystem checks ────────────────────────────────────────────────────


def test_paid_runtime_adapter_modules_absent_from_oss_tree():
    """No ``clawmetry/adapters/<paid_runtime>.py`` may exist.

    The 10 paid runtime adapters belong in the closed-source
    ``clawmetry_pro`` package and ship to entitled nodes via the
    ``clawmetry.extensions`` entry point or auto-provisioning.
    """
    from clawmetry.entitlements import PAID_RUNTIMES

    leaks = []
    for runtime in sorted(PAID_RUNTIMES):
        candidate = ADAPTERS_DIR / f"{runtime}.py"
        if candidate.exists():
            leaks.append(str(candidate.relative_to(REPO_ROOT)))

    assert not leaks, (
        f"Paid runtime adapter file(s) leaked into the OSS repo: {leaks}. "
        f"These modules must live in clawmetry-pro and load via the "
        f"clawmetry.extensions entry point — never inline in "
        f"clawmetry/adapters/."
    )


def test_adapters_dir_contains_only_plumbing_and_free_runtimes():
    """The OSS adapter dir should only contain shared plumbing plus
    one module per Free runtime."""
    plumbing = {"__init__.py", "base.py", "registry.py", "README.md"}
    # nemoclaw is exposed through the nemo.py facade (push-mode receiver
    # shares the same file). openclaw has its own module.
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


# ── source-scan checks on _FAMILY_ADAPTER_SPECS ──────────────────────────


def _parse_family_adapter_specs() -> list[tuple[str, str]]:
    """Source-parse ``_FAMILY_ADAPTER_SPECS`` from sync.py without
    importing the whole module (which pulls in DuckDB, the daemon, the
    HTTP layer, etc.). Returns a list of ``(module_path, class_name)``
    tuples. Returns ``[]`` if the constant is absent or unparseable —
    the caller decides whether that's a failure."""
    tree = ast.parse(SYNC_PATH.read_text())
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "_FAMILY_ADAPTER_SPECS" not in targets:
            continue
        if not isinstance(node.value, ast.Tuple):
            return []
        specs: list[tuple[str, str]] = []
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
    """Every entry in ``_FAMILY_ADAPTER_SPECS`` must import from the
    closed-source ``clawmetry_pro.adapters.*`` namespace. A spec rooted
    at ``clawmetry.adapters.*`` would ship the paid runtime inside the
    OSS wheel — the exact regression Phase 4 was meant to prevent."""
    specs = _parse_family_adapter_specs()
    assert specs, (
        "Could not parse _FAMILY_ADAPTER_SPECS from clawmetry/sync.py — "
        "did the constant get renamed? This guard relies on it being a "
        "tuple of (module, classname) string literals."
    )
    bad = [
        (mod, cls)
        for (mod, cls) in specs
        if not mod.startswith("clawmetry_pro.adapters.")
    ]
    assert not bad, (
        f"_FAMILY_ADAPTER_SPECS entries must live under "
        f"clawmetry_pro.adapters.* — found: {bad}. Move the impl to "
        f"clawmetry-pro and keep the spec pointing at the closed package."
    )


def test_family_adapter_specs_cover_every_paid_runtime():
    """Symmetric: every member of ``PAID_RUNTIMES`` must appear once in
    ``_FAMILY_ADAPTER_SPECS``, so a node with clawmetry-pro installed
    can detect + ingest it. Drift here means a paid runtime advertised
    on /pricing has no actual loader."""
    from clawmetry.entitlements import PAID_RUNTIMES

    specs = _parse_family_adapter_specs()
    spec_runtimes = {mod.rsplit(".", 1)[1] for (mod, _cls) in specs}
    missing = set(PAID_RUNTIMES) - spec_runtimes
    extras = spec_runtimes - set(PAID_RUNTIMES)
    assert not missing, (
        f"_FAMILY_ADAPTER_SPECS missing a row for paid runtime(s): "
        f"{sorted(missing)}. Without a spec, clawmetry-pro cannot "
        f"register the adapter at daemon start."
    )
    assert not extras, (
        f"_FAMILY_ADAPTER_SPECS references runtime(s) absent from "
        f"PAID_RUNTIMES: {sorted(extras)}. Either add them to the "
        f"catalogue or drop the spec."
    )


def test_family_adapter_specs_skip_every_free_runtime():
    """Free runtimes register directly from ``dashboard.py`` (their
    adapters live in the OSS wheel). They must NOT appear in
    ``_FAMILY_ADAPTER_SPECS`` — that would route Free registration
    through a clawmetry_pro import that fails on OSS installs."""
    from clawmetry.entitlements import FREE_RUNTIMES

    specs = _parse_family_adapter_specs()
    spec_runtimes = {mod.rsplit(".", 1)[1] for (mod, _cls) in specs}
    leaked_free = set(FREE_RUNTIMES) & spec_runtimes
    assert not leaked_free, (
        f"Free runtime(s) routed through _FAMILY_ADAPTER_SPECS: "
        f"{sorted(leaked_free)}. Free runtimes ship in the OSS wheel "
        f"and register directly — keep them out of the clawmetry_pro "
        f"family-spec table."
    )


# ── import-time surface checks ──────────────────────────────────────────


def test_clawmetry_adapters_package_exposes_no_paid_adapter_class():
    """Importing ``clawmetry.adapters`` must not surface a class named
    after a paid runtime. The package re-exports ``base``/``registry``
    only — paid adapter classes are bound at daemon-start time inside
    clawmetry-pro and registered into ``registry._adapters`` at runtime,
    never importable from the OSS namespace."""
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
        f"clawmetry.adapters exposes paid runtime adapter class(es) at "
        f"import time: {leaks}. Move them to clawmetry-pro."
    )


def test_registry_does_not_pre_register_paid_runtimes():
    """``clawmetry.adapters.registry._adapters`` must be empty (or
    contain only Free adapters) on a fresh OSS import. Paid adapters
    enter the registry via ``registry.register()`` calls from
    clawmetry-pro at daemon start — never at OSS-package import time."""
    from clawmetry.entitlements import PAID_RUNTIMES
    from clawmetry.adapters import registry as _reg

    pre_registered = [getattr(a, "name", "") for a in _reg.all_adapters()]
    paid_pre = [n for n in pre_registered if n in PAID_RUNTIMES]
    assert not paid_pre, (
        f"Paid runtime(s) pre-registered in clawmetry.adapters.registry "
        f"at import time: {paid_pre}. These must register lazily from "
        f"clawmetry-pro, not at OSS package import."
    )
