"""The hosted Cost Optimizer gets the local one's advice (REQ-OBS-CEA-023, #5934).

AC-OBS-CEA-023.9: the daemon ships the optimizer's data slice in the encrypted
snapshot (``costOptimizer``), built with the same rules as the local route, so
app.clawmetry.com can show evidence-backed experiments instead of generic
recommendations the renderer hides. Needs duckdb, so it runs in the MOAT
verifier job beside tests/test_cost_optimizer_route_honesty.py.

  AC-OBS-CEA-023.9 -> every test here
  AC-OBS-CEA-023.3 -> test_every_figure_carries_a_basis_and_every_experiment_cites_evidence,
                      test_empty_store_is_unknown_not_zero_and_names_the_connected_computer
  AC-OBS-CEA-023.4 -> test_every_figure_carries_a_basis_and_every_experiment_cites_evidence
  AC-OBS-CEA-023.5 -> test_slice_matches_the_local_route_for_the_same_store
"""

from __future__ import annotations

import ast
import importlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from flask import Flask

BEDROCK = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"
REPO = Path(__file__).resolve().parents[1]


def _today():
    return datetime.now(timezone.utc).date().isoformat()


@pytest.fixture
def store_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "5")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    monkeypatch.setattr(lq, "_DISCOVERY_PATH", str(tmp_path / "no-such-discovery.json"))
    lq._invalidate_daemon_cache()
    import routes.sessions as sessions_mod
    importlib.reload(sessions_mod)
    import routes.infra as infra_mod
    importlib.reload(infra_mod)

    real_run = infra_mod.subprocess.run

    def _run(cmd, *a, **kw):
        if cmd and cmd[0] == "llmfit":
            raise FileNotFoundError("llmfit disabled in tests")
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(infra_mod.subprocess, "run", _run)
    app = Flask(__name__)
    app.register_blueprint(infra_mod.bp_config)
    yield app, ls.get_store()
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest(store, ev_id, model, cost, tokens, second):
    store.ingest({
        "id": ev_id, "node_id": "agent+test", "agent_id": "main",
        "session_id": "sess-" + ev_id, "event_type": "assistant",
        "ts": "%sT10:00:%02d+00:00" % (_today(), second),
        "data": {"type": "assistant", "message": {"role": "assistant", "model": model}},
        "cost_usd": cost, "token_count": tokens, "model": model,
    })


def _flush(store, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def _route(app):
    r = app.test_client().get("/api/cost-optimizer")
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def test_slice_matches_the_local_route_for_the_same_store(store_app):
    from clawmetry.cost_optimizer_snapshot import build_slice

    app, store = store_app
    for i in range(4):
        _ingest(store, "b%d" % i, BEDROCK, 0.25, 1200, i)
    _flush(store)
    local = _route(app)
    hosted = build_slice(store)

    for key in ("taskRecommendations", "localAdvice", "modelUsage", "recommendationsNote",
                "todayCost", "projectedMonthlyCost", "expensiveOps"):
        assert hosted[key] == local[key], key
    assert hosted["taskRecommendations"], "four Bedrock events must yield an experiment"
    assert hosted["localAdvice"]["show"] is False
    assert "AWS Bedrock" in hosted["localAdvice"]["reason"]
    for key, entry in local["provenance"].items():
        assert hosted["provenance"][key]["basis"] == entry["basis"], key


def test_every_figure_carries_a_basis_and_every_experiment_cites_evidence(store_app):
    from clawmetry.cost_optimizer_snapshot import build_slice

    app, store = store_app
    for i in range(3):
        _ingest(store, "e%d" % i, BEDROCK, 0.5, 900, i)
    _flush(store)
    hosted = build_slice(store)
    prov = hosted["provenance"]
    for key in ("todayCost", "projectedMonthlyCost", "expensiveOps", "modelUsage"):
        assert prov.get(key, {}).get("basis") in ("measured", "derived", "estimated", "unknown"), key
    for rec in hosted["taskRecommendations"]:
        ev = rec.get("evidence") or {}
        assert ev.get("events", 0) >= 1 and ev.get("window"), rec
    blob = json.dumps(hosted)
    for banned in ("estimatedSavings", "savingsEstimate", "potentialSavings", "60-80%", "~$"):
        assert banned not in blob, banned
    # Host state stays on the computer: the cloud adds hardware from machineInfo.
    for host_only in ("system", "localModels", "ollamaInstalled", "llmfitAvailable"):
        assert host_only not in hosted, host_only


def test_empty_store_is_unknown_not_zero_and_names_the_connected_computer(store_app):
    from clawmetry.cost_optimizer_snapshot import build_slice

    _, store = store_app
    _flush(store)
    hosted = build_slice(store)
    assert hosted["todayCost"] is None and hosted["projectedMonthlyCost"] is None
    reason = hosted["provenance"]["todayCost"].get("reason") or ""
    assert hosted["provenance"]["todayCost"]["basis"] == "unknown"
    assert "connected computer" in reason
    assert "intercepted" not in reason, "the hosted slice has no interceptor ring to blame"
    assert hosted["taskRecommendations"] == [] and hosted["recommendationsNote"]


def test_daemon_ships_the_slice_in_the_snapshot(store_app):
    _, store = store_app
    for i in range(3):
        _ingest(store, "s%d" % i, BEDROCK, 0.25, 800, i)
    _flush(store)
    import clawmetry.sync as sync
    from clawmetry.cost_optimizer_snapshot import build_slice

    assert sync._build_cost_optimizer_snapshot() == build_slice(store)

    tree = ast.parse((REPO / "clawmetry" / "sync.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "sync_system_snapshot")
    shipped = {
        k.value for node in ast.walk(fn)
        if isinstance(node, ast.Dict) for k in node.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    assert "costOptimizer" in shipped


def test_local_route_wording_is_unchanged():
    from clawmetry import cost_optimizer_advice as adv

    local = json.dumps(adv.cost_provenance("local_store"))
    assert "on this computer" in local and "connected computer" not in local
    assert "intercepted" in json.dumps(adv.cost_provenance("none"))
