"""Enforce/grace-mode contract tests for the ``per_run_waste_flags``
filter on ``GET /api/session-insight/<session_id>`` in
``routes/sessions.py``.

``per_run_waste_flags`` is a Pro-only feature (see ``PRO_ONLY_FEATURES``
in ``clawmetry/entitlements.py``), but ``/api/session-insight/<id>`` is
a MIXED endpoint: the payload combines FREE keys (``cost_usd``,
``true_cost_usd``, ``subagent_count``, ``downstream_cost_usd``,
``governance``, ``session_id``) with the PAID ``waste_flags`` +
``recommendations`` slice.

A whole-endpoint ``@gate("per_run_waste_flags")`` -- the pattern used
by ``routes/audit.py``, ``routes/infra.py`` cost-optimizer, and the
anomaly-detection / error-triage / run-compare endpoints on
``bp_sessions`` -- would blank the FREE cost/governance readout too,
which is not the intended behaviour: an OSS install still deserves to
see its true cost.

So the migration is a *filter*, not a gate:
``_apply_per_run_waste_paywall`` runs at the tail of ``api_session_insight``
and, when the install lacks ``per_run_waste_flags``, blanks the PAID
keys and inserts a ``paywall`` block for the UI.

This suite pins:

  1. **Enforce mode:** ``waste_flags`` and ``recommendations`` come back
     as ``[]``, and a ``paywall`` block with
     ``feature="per_run_waste_flags"`` +
     ``required_tier=TIER_CLOUD_PRO`` + ``tier`` + ``hint`` is
     inserted. The FREE keys (``true_cost_usd``,
     ``subagent_count``, ``governance``, ``session_id``, ...) survive.
  2. **Grace mode (default):** the filter is transparent. The payload
     is byte-equal to the pre-migration shape -- ``waste_flags`` still
     lists the fired flags, ``recommendations`` still carries the
     advice strings, and no ``paywall`` key appears.
  3. **Defensive fallthrough:** an entitlement-lookup crash never
     turns into a masked payload. The full ``waste_flags`` +
     ``recommendations`` slice reaches the caller (mirrors the
     defensive contract of :func:`clawmetry._gate.gate`).
  4. **Envelope parity:** the ``paywall`` block carries the same
     ``feature`` / ``tier`` / ``required_tier`` / ``hint`` keys as the
     shared ``@gate`` decorator's 402 body, so a front-end that
     already handles paid-feature 402s can render the same CTA off
     this block with one branch.
  5. **Wiring pin:** the tail of ``api_session_insight`` in
     ``routes/sessions.py`` still calls the filter, so a well-meaning
     revert can't silently drop the paywall.
"""
from __future__ import annotations

import importlib

import pytest
from flask import Flask


# ── fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def enforce(monkeypatch, tmp_path):
    """OSS install under ``CLAWMETRY_ENFORCE=1`` -- ``per_run_waste_flags``
    (a Pro-only feature) is NOT allowed."""
    monkeypatch.setenv("CLAWMETRY_ENFORCE", "1")
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


@pytest.fixture
def grace(monkeypatch, tmp_path):
    """Default grace mode -- every feature key passes the entitlement
    check, so the filter is transparent."""
    monkeypatch.delenv("CLAWMETRY_ENFORCE", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    import clawmetry.entitlements as e

    importlib.reload(e)
    e.invalidate()
    yield e
    e.invalidate()


def _make_app():
    from routes.sessions import bp_sessions

    app = Flask(__name__)
    app.register_blueprint(bp_sessions)
    return app


def _stub_insight_backing_data(monkeypatch, *, session_id="sess-1"):
    """Stub the two LocalStore-facing helpers that ``api_session_insight``
    calls so the test doesn't need a live DuckDB. Returns a session with
    enough waste-signal fields to make ``_derive_session_insight`` fire
    several flags (``reasoning_heavy``, ``cache_poor``, ``tools_failing``,
    ``compaction_thrash``, ``model_fallback``, ``fanned_out``,
    ``reread_tax``), so the enforce-mode blank is unambiguous.
    """
    from routes import sessions as S

    canned_session = {
        "session_id": session_id,
        "cost_usd": 2.00,
        "reasoning_cost_usd": 0.80,   # 40% of cost -> reasoning_heavy
        "cache_hit_pct": 12,           # < 40 -> cache_poor
        "cache_write_cost_usd": 0.20,  # > cache_saved -> reread_tax
        "cache_saved_usd": 0.01,
        "cache_expiry_count": 3,
        "tool_error_pct": 55,          # >= 20 -> tools_failing
        "compaction_count": 4,         # >= 2 -> compaction_thrash
        "model_mix": True,             # -> model_fallback
    }
    canned_lineage = [
        {"session_id": "child-1", "depth": 1, "cost_usd": 0.50},
        {"session_id": "child-2", "depth": 1, "cost_usd": 0.25},
    ]

    def _fake_cost_breakdown():
        return {"sessions": [canned_session]}

    def _fake_ls_call(method_name, **kwargs):
        if method_name == "query_session_lineage":
            return canned_lineage
        if method_name in ("query_approvals", "query_guardrail_events"):
            return []
        return []

    monkeypatch.setattr(S, "_try_local_store_cost_breakdown", _fake_cost_breakdown)
    monkeypatch.setattr(S, "_ls_call", _fake_ls_call)
    return canned_session, canned_lineage


# ── unit tests: the filter helper in isolation ──────────────────────────────


def test_filter_blanks_paid_slice_in_enforce_mode(enforce):
    """`_apply_per_run_waste_paywall` blanks ``waste_flags`` and
    ``recommendations``, and inserts a ``paywall`` block, when the caller
    lacks ``per_run_waste_flags`` (enforce mode + OSS tier)."""
    from routes.sessions import _apply_per_run_waste_paywall

    payload = {
        "session_id": "u",
        "cost_usd": 1.0,
        "true_cost_usd": 1.75,
        "subagent_count": 2,
        "waste_flags": ["reasoning_heavy", "cache_poor"],
        "recommendations": [
            {"flag": "reasoning_heavy", "text": "..."},
            {"flag": "cache_poor", "text": "..."},
        ],
        "governance": {"decision_count": 0, "denied_count": 0},
    }

    out = _apply_per_run_waste_paywall(payload)

    assert out["waste_flags"] == []
    assert out["recommendations"] == []
    assert out["paywall"]["feature"] == "per_run_waste_flags"
    assert out["paywall"]["required_tier"] == enforce.TIER_CLOUD_PRO
    assert out["paywall"]["tier"] == enforce.TIER_OSS
    assert isinstance(out["paywall"].get("hint"), str)
    assert out["paywall"]["hint"]

    # FREE keys survive so the OSS install still sees its true cost.
    assert out["session_id"] == "u"
    assert out["cost_usd"] == 1.0
    assert out["true_cost_usd"] == 1.75
    assert out["subagent_count"] == 2
    assert out["governance"] == {"decision_count": 0, "denied_count": 0}


def test_filter_is_transparent_in_grace_mode(grace):
    """Grace mode: the filter must not change the payload. Pins the
    default-until-enforce-release contract that current OSS installs still
    see ``waste_flags`` + ``recommendations``."""
    from routes.sessions import _apply_per_run_waste_paywall

    payload = {
        "session_id": "u",
        "cost_usd": 1.0,
        "waste_flags": ["reasoning_heavy"],
        "recommendations": [{"flag": "reasoning_heavy", "text": "..."}],
    }
    # Snapshot before applying so we can assert byte-equal after.
    before = {k: (list(v) if isinstance(v, list) else v) for k, v in payload.items()}

    out = _apply_per_run_waste_paywall(payload)

    assert "paywall" not in out
    assert out["waste_flags"] == before["waste_flags"]
    assert out["recommendations"] == before["recommendations"]


def test_filter_falls_through_when_entitlement_lookup_crashes(
    enforce, monkeypatch
):
    """If ``get_entitlement()`` itself raises, the paid slice must still
    reach the caller. Mirrors :func:`clawmetry._gate.gate`'s defensive
    contract -- a flaky entitlement read never fails closed."""
    from routes.sessions import _apply_per_run_waste_paywall

    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    payload = {
        "session_id": "u",
        "waste_flags": ["reasoning_heavy"],
        "recommendations": [{"flag": "reasoning_heavy", "text": "..."}],
    }
    out = _apply_per_run_waste_paywall(payload)

    # Defensive fallthrough: no paywall block, full paid slice preserved.
    assert "paywall" not in out
    assert out["waste_flags"] == ["reasoning_heavy"]
    assert out["recommendations"] == [
        {"flag": "reasoning_heavy", "text": "..."}
    ]


# ── end-to-end tests: hit the route via the Flask test client ───────────────


def test_endpoint_blanks_paid_slice_in_enforce_mode(enforce, monkeypatch):
    """End-to-end: ``GET /api/session-insight/<id>`` under enforce+OSS
    returns 200 with the FREE slice intact and the PAID slice blanked
    plus a paywall block. Not 402: the endpoint is a mixed FREE+PAID
    surface, so it stays 200 and only the paid keys are filtered."""
    _stub_insight_backing_data(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/session-insight/sess-1")
        assert r.status_code == 200, (
            "session-insight is a mixed FREE+PAID endpoint and MUST NOT "
            "flip to 402 on enforce -- the FREE cost/governance readout "
            "still has to reach the OSS caller."
        )
        body = r.get_json()

        # PAID slice: filtered to empty + paywall block inserted.
        assert body["waste_flags"] == []
        assert body["recommendations"] == []
        assert body["paywall"]["feature"] == "per_run_waste_flags"
        assert body["paywall"]["required_tier"] == enforce.TIER_CLOUD_PRO
        assert body["paywall"]["tier"] == enforce.TIER_OSS
        assert isinstance(body["paywall"].get("hint"), str)
        assert body["paywall"]["hint"]

        # FREE slice: survives unchanged.
        assert body["session_id"] == "sess-1"
        assert body["cost_usd"] == 2.00
        assert body["subagent_count"] == 2  # from the canned lineage
        assert body["downstream_cost_usd"] == 0.75
        assert body["true_cost_usd"] == 2.75
        assert body["governance"] == {"decision_count": 0, "denied_count": 0}


def test_endpoint_is_transparent_in_grace_mode(grace, monkeypatch):
    """End-to-end: grace mode leaves the PAID slice intact. The pre-
    migration payload shape (``waste_flags`` populated, ``recommendations``
    keyed by ``flag`` + ``text``) reaches the caller unchanged."""
    _stub_insight_backing_data(monkeypatch)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/session-insight/sess-1")
        assert r.status_code == 200
        body = r.get_json()

        # Grace mode -> no paywall block.
        assert "paywall" not in body

        # The canned session was tuned to fire six waste flags plus the
        # lineage-driven ``fanned_out`` flag. The pre-migration payload
        # returns them all.
        flags = set(body["waste_flags"])
        assert "reasoning_heavy" in flags
        assert "cache_poor" in flags
        assert "reread_tax" in flags
        assert "tools_failing" in flags
        assert "compaction_thrash" in flags
        assert "model_fallback" in flags
        assert "fanned_out" in flags

        # Every flag comes with a recommendation entry {flag, text}.
        assert body["recommendations"]
        for rec in body["recommendations"]:
            assert set(rec.keys()) == {"flag", "text"}
            assert rec["flag"] in flags
            assert isinstance(rec["text"], str) and rec["text"]


def test_endpoint_paywall_block_matches_gate_envelope_keys(enforce, monkeypatch):
    """The ``paywall`` block on the mixed endpoint must carry the *same*
    identifying keys the shared ``@gate`` decorator returns in its 402
    body (``feature``, ``tier``, ``required_tier``, ``hint``). That way a
    front-end that already renders a paid-feature CTA off ``@gate``'s 402
    body can render the same CTA off this block with one code path -- no
    special-case branch for the mixed endpoint.
    """
    from clawmetry._gate import gate as _gate

    reference_app = Flask(__name__)

    @reference_app.route("/reference")
    @_gate("per_run_waste_flags")
    def _reference_view():  # pragma: no cover - never runs in enforce mode
        return {"ok": True}

    _stub_insight_backing_data(monkeypatch)

    insight_app = _make_app()
    with reference_app.test_client() as rc, insight_app.test_client() as ic:
        ref_body = rc.get("/reference").get_json()
        act_body = ic.get("/api/session-insight/sess-1").get_json()

        # The @gate 402 body has a top-level "error"; the filter block
        # is nested under "paywall" (since the endpoint stays 200). The
        # IDENTIFYING keys (feature / tier / required_tier) must match
        # so a UI can render the same CTA off either shape. ``hint`` is
        # copy that can (and does) differ per feature -- pin only that
        # both surfaces emit a non-empty string.
        paywall = act_body["paywall"]
        for key in ("feature", "tier", "required_tier"):
            assert paywall[key] == ref_body[key], (
                f"paywall.{key} must match the shared @gate 402 body's "
                f"{key} so the UI can render one CTA off either shape"
            )
        assert set(paywall.keys()) == {"feature", "tier", "required_tier", "hint"}, (
            "paywall block must carry the same top-level keys the shared "
            "@gate 402 body does (minus 'error', which is only for the "
            "402 path) so the UI can handle both with one code path"
        )
        assert isinstance(paywall["hint"], str) and paywall["hint"]


def test_endpoint_paywall_block_defensive_fallthrough(enforce, monkeypatch):
    """If the entitlement read crashes, the endpoint must still return
    the full pre-migration payload with no paywall block -- not 500, not
    an empty waste-flags list. Mirrors the defensive contract in
    :func:`clawmetry._gate.gate`."""
    _stub_insight_backing_data(monkeypatch)

    def _explode():
        raise RuntimeError("boom")

    monkeypatch.setattr("clawmetry.entitlements.get_entitlement", _explode)

    app = _make_app()
    with app.test_client() as c:
        r = c.get("/api/session-insight/sess-1")
        assert r.status_code == 200
        body = r.get_json()
        assert "paywall" not in body
        # The full waste-flags slice still reaches the caller.
        assert isinstance(body["waste_flags"], list) and body["waste_flags"]
        assert isinstance(body["recommendations"], list) and body["recommendations"]


# ── wiring pin ──────────────────────────────────────────────────────────────


def test_api_session_insight_calls_the_paywall_filter():
    """Static-source pin: ``api_session_insight`` must call
    ``_apply_per_run_waste_paywall`` at the tail. A well-meaning revert
    that drops the call would leave the endpoint returning the full
    ``waste_flags`` + ``recommendations`` slice under enforce -- which
    grace-mode tests can't distinguish from correct behaviour. This pin
    fails loudly in that case.
    """
    import inspect

    from routes import sessions

    src = inspect.getsource(sessions.api_session_insight)
    assert "_apply_per_run_waste_paywall" in src, (
        "routes/sessions.py::api_session_insight must call "
        "_apply_per_run_waste_paywall before returning the payload so "
        "the mixed FREE+PAID endpoint filters the paid slice under "
        "enforce mode. The whole point of this migration is that this "
        "one call sits at the tail of the handler."
    )


def test_paywall_filter_helper_is_exported():
    """The helper must live at module scope on ``routes.sessions`` so
    the test suite (and any future clawmetry-pro extension) can reach
    it. Guards against a refactor that nests the helper inside another
    function and silently loses the wire."""
    from routes import sessions

    assert callable(getattr(sessions, "_apply_per_run_waste_paywall", None)), (
        "routes.sessions._apply_per_run_waste_paywall must remain a "
        "module-level callable -- the wiring pin and the unit tests "
        "reach it by that name."
    )
    assert sessions._PER_RUN_WASTE_FLAGS_FEATURE == "per_run_waste_flags"
