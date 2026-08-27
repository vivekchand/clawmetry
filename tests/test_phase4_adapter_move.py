"""Tests for the OSS-side adapter split.

Phase 4 moved the paid runtime adapters to clawmetry-pro. Goose came back
the other way 2026-08-19 (see ``entitlements.FREE_RUNTIMES``): an
open-source runtime gets a free, open-source adapter, so `pip install
clawmetry` observes it with no account and no wheel download.

Verifies that:
* OSS clawmetry/adapters/ ships the mechanism + exactly the Free runtime
  adapters (openclaw, nemo, goose) and none of the paid ones.
* ``clawmetry/sync.py:_FAMILY_ADAPTER_SPECS`` points at
  ``clawmetry_pro.adapters.*`` for every PAID runtime, and at
  ``clawmetry.adapters.*`` for every FREE one.
* ``_family_adapter_classes()`` still yields the bundled Free adapters when
  clawmetry-pro is not installed (the paid imports fail defensively),
  and the registry still has the Free OpenClaw adapter.
"""
from __future__ import annotations

import importlib
import sys


def test_oss_only_keeps_mechanism_and_free_adapters():
    """The OSS adapters package must ship the Free adapters, and only those."""
    # The Free runtimes + the mechanism are importable from OSS.
    from clawmetry.adapters import (  # noqa: F401
        base, registry, openclaw, nemo, goose, cost,
    )

    # The paid adapter modules MUST NOT exist in OSS.
    for name in (
        "claude_code", "codex", "cursor", "aider",
        "opencode", "qwen_code", "hermes", "picoclaw", "nanoclaw",
        "pi", "deepagents", "n8n", "antigravity",
        "copilot", "grok", "qm", "deepseek_harness", "exo", "kimi",
    ):
        try:
            importlib.import_module(f"clawmetry.adapters.{name}")
        except ImportError:
            continue
        raise AssertionError(
            f"clawmetry.adapters.{name} unexpectedly importable from OSS; "
            "it should have moved to clawmetry_pro.adapters."
        )


def test_free_adapter_modules_ship_in_oss():
    """Every non-OpenClaw FREE runtime must have its adapter bundled here.

    This is the guard that keeps the promise honest: a runtime listed as
    free but whose reader only exists in the closed wheel would be
    unusable on `pip install clawmetry`, which is exactly the complaint
    that put Goose in the free tier.
    """
    from clawmetry.entitlements import FREE_RUNTIMES

    # openclaw + nemoclaw have bespoke module names; the rest map 1:1.
    module_for = {"openclaw": "openclaw", "nemoclaw": "nemo"}
    for rt in sorted(FREE_RUNTIMES):
        mod = module_for.get(rt, rt)
        importlib.import_module(f"clawmetry.adapters.{mod}")


def test_family_adapter_specs_split_by_tier():
    """Paid specs point at clawmetry-pro; free specs stay in OSS."""
    from clawmetry import sync as _s
    from clawmetry.entitlements import FREE_RUNTIMES

    specs = _s._FAMILY_ADAPTER_SPECS
    # Bump when a runtime is added. The real invariant (loader == catalogue)
    # is test_entitlements.py::test_paid_runtimes_match_family_adapter_specs;
    # this is the blunt tripwire that catches an accidental extra entry.
    assert len(specs) == 26, f"expected 26 family adapters, got {len(specs)}"

    free_specs = [s for s in specs if s[0].startswith("clawmetry.adapters.")]
    paid_specs = [s for s in specs if s[0].startswith("clawmetry_pro.adapters.")]
    assert len(free_specs) + len(paid_specs) == len(specs), (
        f"unrecognised adapter import path in {specs}"
    )

    # Every bundled family spec must be a runtime we actually advertise free.
    for module_name, class_name in free_specs:
        runtime = module_name.rsplit(".", 1)[-1]
        assert runtime in FREE_RUNTIMES, (
            f"{module_name}.{class_name} is bundled in OSS but {runtime!r} is "
            "not in FREE_RUNTIMES — a paid adapter must not ship in the open "
            "package."
        )


def test_family_adapter_classes_keeps_free_when_pro_absent(monkeypatch):
    """Without clawmetry-pro, _family_adapter_classes() still yields the
    bundled FREE adapters; every paid import fails defensively.

    This is the whole point of bundling Goose: a plain `pip install
    clawmetry` — no account, no licence, no wheel download — must still be
    able to read a Goose install.
    """
    monkeypatch.setitem(sys.modules, "clawmetry_pro", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.adapters", None)
    for name in (
        "claude_code", "codex", "cursor", "aider",
        "opencode", "qwen_code", "hermes", "picoclaw", "nanoclaw",
        "pi", "deepagents", "n8n", "antigravity",
        "copilot", "grok", "qm", "deepseek_harness", "exo", "kimi",
    ):
        monkeypatch.setitem(sys.modules, f"clawmetry_pro.adapters.{name}", None)

    from clawmetry import sync as _s
    classes = _s._family_adapter_classes()
    names = sorted(getattr(c, "name", "") for c in classes)
    # Exactly the bundled free family adapters — nothing paid leaked through.
    assert names == ["goose"], names
