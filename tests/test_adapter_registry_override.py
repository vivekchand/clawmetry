"""Tests for the adapter-registry override contract.

The open-core plugin model depends on this: a clawmetry-pro plugin registers
its closed adapter at import time, and OSS must let it win rather than clobber
it with the bundled adapter. These lock the two behaviours that guarantee that:
later-registration-wins (override by name) and get()-after-register.
"""
from __future__ import annotations

from clawmetry.adapters import base, registry


class _FakeAdapter(base.AgentAdapter):
    def __init__(self, name, tag):
        self.name = name
        self.display_name = name
        self.tag = tag

    def detect(self):
        return base.DetectResult(name=self.name, display_name=self.display_name, detected=True)

    def list_sessions(self, limit: int = 100):
        return []

    def capabilities(self):
        return set()


def test_later_registration_overrides_by_name():
    name = "test_runtime_override"
    registry.register(_FakeAdapter(name, "bundled"))
    assert registry.get(name).tag == "bundled"
    # a plugin registering the same name later must win (closed adapter override)
    registry.register(_FakeAdapter(name, "plugin"))
    assert registry.get(name).tag == "plugin"
    registry.unregister(name)


def test_get_absent_is_none_so_oss_knows_to_register():
    # OSS's skip-if-present guard relies on get() being None when no plugin
    # has claimed the runtime.
    assert registry.get("definitely_not_registered_xyz") is None
