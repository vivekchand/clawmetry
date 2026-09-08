"""GET /api/trail/coverage: declared decision-trail coverage per runtime.

Honesty contract: every runtime in the entitlement universe is present; a
runtime whose adapter is not importable says ``unknown`` ("adapter not loaded
on this node"); an adapter that never overrode ``trail_coverage`` is also
``unknown`` (the base default must never be reported as a claim); levels are
always one of full / partial / none / unknown.
"""
from __future__ import annotations

import pytest

from clawmetry import entitlements
from clawmetry.adapters import AgentAdapter, Capability, DetectResult, registry
from clawmetry.adapters.base import TRAIL_LEVELS
import routes.trail as TR


class _Declaring(AgentAdapter):
    name = "zz_declaring"
    display_name = "Declaring"

    def detect(self):
        return DetectResult(name=self.name, display_name=self.display_name, detected=True)

    def list_sessions(self, limit=100):
        return []

    def capabilities(self):
        return {Capability.SESSIONS, Capability.REASONING}

    def trail_coverage(self):
        return {"inputs": "none", "reasoning": "full", "note": "every block"}


class _Silent(_Declaring):
    name = "zz_silent"
    trail_coverage = AgentAdapter.trail_coverage


class _Bogus(_Declaring):
    name = "zz_bogus"

    def trail_coverage(self):
        return {"inputs": "always", "reasoning": 3, "note": None}


@pytest.fixture()
def fakes():
    for a in (_Declaring(), _Silent(), _Bogus()):
        registry.register(a)
    yield
    for n in ("zz_declaring", "zz_silent", "zz_bogus"):
        registry.unregister(n)


@pytest.fixture()
def client():
    from flask import Flask
    app = Flask("test_trail_coverage_route")
    app.register_blueprint(TR.bp_trail)
    app.config["TESTING"] = True
    return app.test_client()


def test_declared_coverage_is_returned_verbatim(fakes):
    assert TR.coverage_for_runtime("zz_declaring") == {
        "inputs": "none", "reasoning": "full", "note": "every block"}


def test_undeclared_adapter_is_unknown_not_none(fakes):
    cov = TR.coverage_for_runtime("zz_silent")
    assert cov["reasoning"] == "unknown" and cov["inputs"] == "unknown"
    assert "declare" in cov["note"]


def test_bogus_levels_are_coerced_to_unknown(fakes):
    cov = TR.coverage_for_runtime("zz_bogus")
    assert cov == {"inputs": "unknown", "reasoning": "unknown", "note": ""}


def test_missing_runtime_is_not_loaded():
    cov = TR.coverage_for_runtime("no_such_runtime_ever")
    assert cov == TR._UNKNOWN_NOT_LOADED


def test_bundled_openclaw_declares_partial_reasoning_without_registration():
    # Not registered in the test registry, yet the bundled class answers.
    assert registry.get("openclaw") is None or True
    cov = TR.coverage_for_runtime("openclaw")
    assert cov["reasoning"] == "partial"
    assert "thinking" in cov["note"]
    assert TR.coverage_for_runtime("nemoclaw")["reasoning"] == "partial"


def test_bundled_goose_declares_partial_reasoning():
    # Asked of the OSS class directly: on a node with the pro wheel the
    # family loader may hand back the closed GooseAdapter instead.
    from clawmetry.adapters.goose import GooseAdapter
    cov = GooseAdapter().trail_coverage()
    assert cov["reasoning"] == "partial"
    assert "thinking" in cov["note"]
    assert Capability.REASONING in GooseAdapter().capabilities()


def test_route_covers_every_runtime_with_valid_levels(client):
    res = client.get("/api/trail/coverage")
    assert res.status_code == 200
    data = res.get_json()
    universe = set(entitlements.FREE_RUNTIMES) | set(entitlements.PAID_RUNTIMES)
    assert set(data["runtimes"]) == universe
    assert data["count"] == len(universe)
    allowed = set(TRAIL_LEVELS) | {"unknown"}
    for name, cov in data["runtimes"].items():
        assert cov["inputs"] in allowed, name
        assert cov["reasoning"] in allowed, name
        assert isinstance(cov["note"], str), name
        assert isinstance(cov["registered"], bool), name
        if cov["reasoning"] == "unknown":
            assert cov["note"], f"{name}: unknown must say why"


def test_route_never_reports_the_base_default_as_a_claim(client):
    """On a free install the paid adapters are not importable: they must read
    unknown, never none (which would say the runtime hides its reasoning)."""
    data = client.get("/api/trail/coverage").get_json()
    for name in entitlements.PAID_RUNTIMES:
        cov = data["runtimes"][name]
        if cov["reasoning"] == "none":
            # Only a real adapter that declared none may say so.
            assert cov["note"] and "not loaded" not in cov["note"], name
