"""Tests for the OSS-side cleanup after Phase 4 moved 10 paid runtime
adapters to clawmetry-pro.

Verifies that:
* OSS clawmetry/adapters/ only contains the base + registry + the two
  Free runtime adapters (openclaw, nemo).
* ``clawmetry/sync.py:_FAMILY_ADAPTER_SPECS`` points at
  ``clawmetry_pro.adapters.*`` import paths.
* ``_family_adapter_classes()`` returns an empty list when
  clawmetry-pro is not installed (every import fails defensively),
  and the registry still has the Free OpenClaw adapter.
"""
from __future__ import annotations

import importlib
import sys


def test_oss_only_keeps_base_registry_openclaw_nemo():
    """The OSS adapters package must only ship the Free adapters."""
    from clawmetry import adapters as _a

    # The Free runtimes + the mechanism are still importable.
    from clawmetry.adapters import base, registry, openclaw, nemo  # noqa: F401

    # The paid adapter modules MUST NOT exist in OSS anymore.
    for name in (
        "claude_code", "codex", "cursor", "aider", "goose",
        "opencode", "qwen_code", "hermes", "picoclaw", "nanoclaw",
        "pi", "deepagents",
    ):
        try:
            importlib.import_module(f"clawmetry.adapters.{name}")
        except ImportError:
            continue
        raise AssertionError(
            f"clawmetry.adapters.{name} unexpectedly importable from OSS; "
            "it should have moved to clawmetry_pro.adapters."
        )


def test_family_adapter_specs_target_clawmetry_pro():
    """Sync's adapter discovery list must point at clawmetry-pro, not OSS."""
    from clawmetry import sync as _s

    specs = _s._FAMILY_ADAPTER_SPECS
    assert len(specs) == 12, f"expected 12 paid adapters, got {len(specs)}"
    for module_name, class_name in specs:
        assert module_name.startswith("clawmetry_pro.adapters."), (
            f"sync._FAMILY_ADAPTER_SPECS still references OSS path: "
            f"{module_name}.{class_name}"
        )


def test_family_adapter_classes_empty_when_pro_absent(monkeypatch):
    """When clawmetry-pro is not installed, _family_adapter_classes()
    returns []; each per-adapter import fails defensively and the daemon
    proceeds with the Free runtimes only."""
    monkeypatch.setitem(sys.modules, "clawmetry_pro", None)
    monkeypatch.setitem(sys.modules, "clawmetry_pro.adapters", None)
    for name in (
        "claude_code", "codex", "cursor", "aider", "goose",
        "opencode", "qwen_code", "hermes", "picoclaw", "nanoclaw",
        "pi", "deepagents",
    ):
        monkeypatch.setitem(sys.modules, f"clawmetry_pro.adapters.{name}", None)

    from clawmetry import sync as _s
    classes = _s._family_adapter_classes()
    # Empty when nothing is importable; daemon falls back to OpenClaw + NeMo.
    assert classes == []
