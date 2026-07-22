"""Tests for the runtime-scoped OSS-stub 402 body builder.

Pins the wire shape that :func:`clawmetry._paywall.upgrade_required_body_for_runtime`
returns. The shape must stay in lockstep with what
:func:`clawmetry._gate.require_runtime` emits inline so a dashboard that
already handles a ``require_runtime`` 402 can handle a stub-blueprint 402
with the same code path.

Companion to :mod:`tests.test_paywall_body` (the feature-side twin).
"""
from __future__ import annotations

import importlib

import pytest


@pytest.fixture
def ent_grace(monkeypatch, tmp_path):
    """Reload entitlements with HOME pointed at an empty tmp_path so the
    resolver collapses to the OSS-free entitlement deterministically."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


# ── shape ──────────────────────────────────────────────────────────────────


def test_body_shape_matches_require_runtime(ent_grace):
    """The 402 body must carry the same five keys ``require_runtime``
    produces so frontends can branch on either path with one handler."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("claude_code")
    assert set(body.keys()) == {
        "error",
        "runtime",
        "tier",
        "required_tier",
        "hint",
    }
    assert body["error"] == "upgrade_required"
    assert body["runtime"] == "claude_code"


def test_body_uses_runtime_key_not_feature_key(ent_grace):
    """The body carries ``runtime`` -- ``feature`` is reserved for the
    feature-side twin so a stub can't ambiguously report both."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("codex")
    assert "runtime" in body
    assert "feature" not in body


# ── canonicalisation ───────────────────────────────────────────────────────


def test_body_canonicalises_dash_alias(ent_grace):
    """``claude-code`` is a common alias for ``claude_code``; the body
    surfaces the canonical id so the UI never renders the dashed form."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("claude-code")
    assert body["runtime"] == "claude_code"


def test_body_canonicalises_case_and_whitespace(ent_grace):
    """Trailing whitespace / uppercase are normalised so a caller reading
    the runtime out of an HTTP header doesn't have to pre-clean it."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("  CLAUDE_CODE  ")
    assert body["runtime"] == "claude_code"


def test_body_preserves_unknown_runtime_verbatim(ent_grace):
    """A future / typo runtime key that isn't in the catalogue collapses to
    ``required_tier=None`` but the input is echoed back (lower-cased) so the
    UI can still surface the failing key for diagnostics."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("totally_unknown_runtime_xyz")
    assert body["runtime"] == "totally_unknown_runtime_xyz"
    assert body["required_tier"] is None
    assert body["error"] == "upgrade_required"


# ── required_tier resolution ───────────────────────────────────────────────


def test_body_required_tier_starter_runtime(ent_grace):
    """Every paid runtime unlocks at Cloud Starter under the current
    catalogue -- the body echoes that so the UI renders the Starter CTA."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    for rt in ("claude_code", "codex", "cursor", "aider", "goose"):
        body = upgrade_required_body_for_runtime(rt)
        assert body["required_tier"] == ent_grace.TIER_CLOUD_STARTER, rt


def test_body_required_tier_matches_min_tier_for_runtime(ent_grace):
    """The body's ``required_tier`` byte-equals :func:`min_tier_for_runtime`
    output for every runtime in ``PAID_RUNTIMES`` -- if this ever diverges
    the shared body is silently drifting from the canonical resolver."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    for rt in ent_grace.PAID_RUNTIMES:
        body = upgrade_required_body_for_runtime(rt)
        assert body["required_tier"] == ent_grace.min_tier_for_runtime(rt), rt


def test_body_required_tier_free_runtime_is_none(ent_grace):
    """Free runtimes don't have an upgrade target -- ``required_tier`` is
    ``None`` so the UI can short-circuit instead of rendering a CTA, matching
    how the feature-side twin treats free feature keys."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    for rt in ent_grace.FREE_RUNTIMES:
        body = upgrade_required_body_for_runtime(rt)
        assert body["required_tier"] is None, rt


# ── tier reflects install ──────────────────────────────────────────────────


def test_body_tier_reflects_current_install(ent_grace):
    """Free / OSS installs report ``tier="oss"`` so the UI knows where the
    user starts from when rendering the upgrade delta."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("claude_code")
    assert body["tier"] == ent_grace.TIER_OSS


# ── hint ───────────────────────────────────────────────────────────────────


def test_body_default_hint_used_when_omitted(ent_grace):
    """Omitting ``hint`` falls back to the default ('install clawmetry-pro
    or use Cloud') copy so stubs that don't care about the wording don't
    have to inline a string."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("claude_code")
    assert "clawmetry-pro" in body["hint"]
    assert body["hint"]


def test_body_custom_hint_overrides_default(ent_grace):
    """A runtime-specific hint overrides the default so a runtime whose
    upgrade CTA has different copy (per-runtime landing pages, etc.) can
    swap it in."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime(
        "claude_code", hint="Claude Code observability ships in Pro."
    )
    assert body["hint"] == "Claude Code observability ships in Pro."


def test_body_default_hint_is_runtime_flavoured(ent_grace):
    """Default hint is the runtime-flavoured default, not the feature default
    -- otherwise the UI copy leaks 'feature' language onto a runtime CTA."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("claude_code")
    assert "runtime" in body["hint"].lower()


# ── never-raise ────────────────────────────────────────────────────────────


def test_body_swallows_canonical_runtime_errors(monkeypatch):
    """If ``canonical_runtime`` raises the body still serialises with the
    caller-supplied lowered / trimmed key -- the builder owns the never-raise
    contract regardless of what the entitlements catalogue does."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body_for_runtime

    def explode(_rt):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "canonical_runtime", explode)
    body = upgrade_required_body_for_runtime("Claude_Code")
    assert body["error"] == "upgrade_required"
    assert body["runtime"] == "claude_code"


def test_body_swallows_min_tier_resolver_errors(monkeypatch):
    """If the canonical tier resolver raises, the helper still produces a
    well-formed body with ``required_tier=None`` rather than 500-ing the
    request."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body_for_runtime

    def explode(_rt):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "min_tier_for_runtime", explode)
    body = upgrade_required_body_for_runtime("claude_code")
    assert body["error"] == "upgrade_required"
    assert body["runtime"] == "claude_code"
    assert body["required_tier"] is None


def test_body_swallows_get_entitlement_errors(monkeypatch):
    """If ``get_entitlement`` itself raises, ``tier`` falls back to ``oss``
    rather than crashing the request path."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body_for_runtime

    def explode(*_a, **_kw):
        raise RuntimeError("boom")

    monkeypatch.setattr(ent, "get_entitlement", explode)
    body = upgrade_required_body_for_runtime("claude_code")
    assert body["tier"] == "oss"
    assert body["error"] == "upgrade_required"


def test_body_swallows_missing_min_tier_helper(monkeypatch):
    """A stubbed-out entitlements module without ``min_tier_for_runtime``
    still yields a valid body -- ``required_tier`` collapses to ``None``
    rather than raising ``AttributeError``."""
    import clawmetry.entitlements as ent
    from clawmetry._paywall import upgrade_required_body_for_runtime

    monkeypatch.delattr(ent, "min_tier_for_runtime")
    body = upgrade_required_body_for_runtime("claude_code")
    assert body["required_tier"] is None
    assert body["error"] == "upgrade_required"


def test_body_empty_runtime_key_still_serialises(ent_grace):
    """Empty / whitespace-only runtime keys don't crash; the body is
    well-formed with an empty runtime id and ``required_tier=None`` -- the
    caller can then decide whether to log or fall back."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime("")
    assert body["error"] == "upgrade_required"
    assert body["runtime"] == ""
    assert body["required_tier"] is None


def test_body_none_runtime_key_still_serialises(ent_grace):
    """A caller that passed ``None`` (a header the client omitted) gets a
    well-formed body, not a ``TypeError``."""
    from clawmetry._paywall import upgrade_required_body_for_runtime

    body = upgrade_required_body_for_runtime(None)  # type: ignore[arg-type]
    assert body["error"] == "upgrade_required"
    assert body["runtime"] == ""
    assert body["required_tier"] is None


# ── shape parity with require_runtime ──────────────────────────────────────


def test_body_shape_parity_with_require_runtime(ent_grace):
    """The body's key set matches what :func:`_gate.require_runtime` returns
    inline -- if the two ever diverge the dashboard's runtime 402 handler
    needs a second code path."""
    from flask import Flask

    from clawmetry._gate import require_runtime
    from clawmetry._paywall import upgrade_required_body_for_runtime

    # Force enforce so require_runtime actually returns the 402 body.
    import clawmetry.entitlements as e

    e.invalidate()
    app = Flask(__name__)

    @app.route("/probe/<rt>")
    def probe(rt):
        import os

        os.environ["CLAWMETRY_ENFORCE"] = "1"
        import clawmetry.entitlements as _e

        importlib.reload(_e)
        _e.invalidate()
        blocked = require_runtime(rt)
        assert blocked is not None
        return blocked

    try:
        with app.test_client() as c:
            r = c.get("/probe/claude_code")
        assert r.status_code == 402
        gate_body = r.get_json()
    finally:
        import os as _os

        _os.environ.pop("CLAWMETRY_ENFORCE", None)
        importlib.reload(e)
        e.invalidate()

    stub_body = upgrade_required_body_for_runtime("claude_code")
    # The key set must match; values can differ (default hints differ per
    # variant so the wording is site-appropriate).
    assert set(stub_body.keys()) == set(gate_body.keys())
