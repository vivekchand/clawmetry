"""Tests for the named evaluator catalogue (clawmetry/evaluators.py + the
GET /api/evaluators route).

The catalogue is NARRATIVE: it brands ClawMetry's shipped signals as a named
library. The discipline that keeps it honest is the guard test below — every
FREE entry's ``source`` MUST point at a real computed column or function, so the
catalogue can't drift away from the code that actually produces the number
("extract then judge", per FLYWHEEL 1d).

Scenarios:
  1. catalogue() returns the entries with correct tiers + status
  2. cloud-safe: catalogue_with_coverage(None) returns the catalogue, no store
  3. live-coverage attach works against a fake store
  4. per-session live-value attach reuses existing fields, never recomputes
  5. GUARD: every free evaluator's source resolves to a real column/function
  6. Pro entries are locked until a hook is registered, then report live
  7. GET /api/evaluators is cloud-safe (catalogue even with no store)
"""
from __future__ import annotations

import importlib
import os
import sys

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from clawmetry import evaluators  # noqa: E402


def test_catalogue_shape_and_tiers():
    cat = evaluators.catalogue()
    assert isinstance(cat, list) and len(cat) >= 8
    slugs = {e["slug"] for e in cat}
    # The named evaluators we promise are all present.
    for slug in (
        "agent-goal-accuracy", "agent-flow-quality", "answer-quality",
        "agent-efficiency", "agent-tool-error-detector",
        "pii-detector", "secrets-detector", "prompt-injection-detector",
        "hallucination-risk", "faithfulness",
    ):
        assert slug in slugs, f"missing evaluator {slug}"
    for e in cat:
        assert e["tier"] in ("free", "pro")
        assert e["status"] in ("live", "partial", "pro")
        assert e["category"] in (
            "quality", "reliability", "efficiency", "safety", "agent")
        assert e["description"] and not e["description"].startswith(" ")
    # Faithfulness + efficiency are PRO; goal-accuracy + answer-quality are FREE.
    by = {e["slug"]: e for e in cat}
    assert by["faithfulness"]["tier"] == "pro"
    assert by["agent-efficiency"]["tier"] == "pro"
    assert by["agent-goal-accuracy"]["tier"] == "free"
    assert by["answer-quality"]["tier"] == "free"


def test_no_emdash_or_double_dash_in_copy():
    # User-facing copy must avoid the AI-tell em-dash / double-dash.
    for e in evaluators.EVALUATOR_CATALOGUE:
        for field in ("name", "description"):
            txt = e[field]
            assert "—" not in txt, f"em-dash in {e['slug']}.{field}"
            assert "--" not in txt, f"double-dash in {e['slug']}.{field}"


def test_cloud_safe_no_store():
    payload = evaluators.catalogue_with_coverage(None)
    assert payload["evaluators"], "catalogue must render with no store"
    assert payload["coverage"] is None
    assert payload["total"] == len(payload["evaluators"])
    assert payload["free"] + payload["pro"] == payload["total"]


def test_live_coverage_attach():
    class _FakeStore:
        def query_eval_summary(self, *, window_hours=24):
            return {"total": 40, "scored": 12}

        def query_outcomes(self, *, limit=2000):
            return [{"outcome": "success"}, {"outcome": None}, {"outcome": "failed"}]

    payload = evaluators.catalogue_with_coverage(_FakeStore())
    cov = payload["coverage"]
    assert cov["sessions_in_window"] == 40
    assert cov["answer_quality_scored"] == 12
    assert cov["goal_accuracy_labelled"] == 2  # the None outcome is excluded


def test_per_session_value_attach_reuses_fields():
    session = {"outcome": "success", "eval_score": 4.5, "reliability_score": 0.8}
    cat = evaluators.catalogue()
    decorated = evaluators.attach_session_values(cat, session)
    by = {e["slug"]: e for e in decorated}
    assert by["agent-goal-accuracy"]["value"] == "success"
    assert by["answer-quality"]["value"] == 4.5
    assert by["agent-flow-quality"]["value"] == 0.8
    # A session with no faithfulness value -> None (Pro value absent).
    assert by["faithfulness"]["value"] is None


def test_guard_free_evaluator_sources_resolve():
    """Each FREE evaluator's source must point at something that REALLY exists.

    This is the anti-drift contract: a free entry can't claim to brand a signal
    we don't actually compute. ``module:symbol`` must import; ``column:table.col``
    must be a real column in the local_store schema; ``dashboard:fn`` must be a
    real dashboard symbol.
    """
    from clawmetry import local_store

    # Build the set of real sessions columns from the schema DDL + migrations.
    schema_text = "".join(
        s for s in getattr(local_store, "_DDL", [])
        if isinstance(s, str)
    )
    migration_cols = {
        f"{tbl}.{col}"
        for (tbl, col, _typ) in getattr(local_store, "_MIGRATIONS_V2", [])
    }

    for e in evaluators.EVALUATOR_CATALOGUE:
        if e["tier"] != "free":
            continue
        src = e["source"]
        if src.startswith("column:"):
            ref = src.split(":", 1)[1]  # sessions.eval_score
            tbl, col = ref.split(".", 1)
            assert (ref in migration_cols) or (col in schema_text), \
                f"{e['slug']} source column {ref} not found in schema"
        elif src.startswith("dashboard:"):
            import dashboard as _d
            sym = src.split(":", 1)[1]
            assert hasattr(_d, sym), f"{e['slug']} dashboard symbol {sym} missing"
        else:
            mod_name, sym = src.split(":", 1)
            mod = importlib.import_module(mod_name)
            assert hasattr(mod, sym), \
                f"{e['slug']} source {mod_name}:{sym} does not exist"


def test_pro_hook_locks_until_registered():
    # Fresh module state: faithfulness is locked.
    importlib.reload(evaluators)
    cat = {e["slug"]: e for e in evaluators.catalogue()}
    assert cat["faithfulness"]["locked"] is True
    assert cat["faithfulness"]["status"] == "pro"

    # Register a hook (what clawmetry-pro does) -> reports live + unlocked.
    evaluators.register_pro_evaluator("faithfulness", lambda **kw: {"score": 1.0})
    cat2 = {e["slug"]: e for e in evaluators.catalogue()}
    assert cat2["faithfulness"]["locked"] is False
    assert cat2["faithfulness"]["status"] == "live"
    assert evaluators.has_pro_hook("faithfulness")
    # Clean up shared module state for other tests.
    importlib.reload(evaluators)


def test_route_cloud_safe(monkeypatch):
    """GET /api/evaluators returns the catalogue even with no store reachable."""
    import routes.evals as evals_mod

    # Force the no-store path: daemon proxy + direct open both miss.
    import routes.local_query as lq
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None, raising=False)

    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(evals_mod.bp_evals)
    client = app.test_client()
    resp = client.get("/api/evaluators")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["evaluators"], "no-store path must still return the catalogue"
