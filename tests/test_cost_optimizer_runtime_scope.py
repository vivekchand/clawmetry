"""The Cost Optimizer follows the runtime switcher (REQ-OBS-CEA-023).

Reported 2026-09-15: with ``?runtime=codex`` selected, the Cost Optimizer
opened under "all runtimes on <host>" and listed claude-opus-5 calls and an
"claude-opus-5 via Anthropic" experiment. The route, the local-store helper and
the hosted snapshot slice all ignored the runtime, and a scoped view could
fall back to the interceptor ring, which is not attributed to any runtime.

  AC-OBS-CEA-023.10 -> every test here
  AC-OBS-CEA-023.3 -> test_runtime_with_no_spend_is_unknown_not_another_runtimes_figures
  AC-OBS-CEA-023.9 -> test_hosted_slice_per_runtime_matches_the_scoped_route,
                      test_daemon_ships_a_slice_per_runtime
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

REPO = Path(__file__).resolve().parents[1]
CLAUDE = "claude-opus-5"
CODEX = "gpt-5-codex"


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
    store = ls.get_store()
    for i in range(4):
        _ingest(store, "cc%d" % i, "claude_code:sess-cc", CLAUDE, 1.5, 800, i)
        _ingest(store, "cx%d" % i, "codex:sess-cx", CODEX, 0.2, 600, 10 + i)
    _flush(store)
    yield app, store
    try:
        store.stop(flush=True)
    except Exception:
        pass


def _ingest(store, ev_id, session_id, model, cost, tokens, second):
    store.ingest({
        "id": ev_id, "node_id": "agent+test", "agent_id": "main",
        "session_id": session_id, "event_type": "assistant",
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


def _route(app, qs=""):
    r = app.test_client().get("/api/cost-optimizer" + qs)
    assert r.status_code == 200, r.get_data(as_text=True)
    return r.get_json()


def _models(payload):
    seen = {u.get("model") for u in payload.get("modelUsage") or []}
    seen |= {op.get("model") for op in payload.get("expensiveOps") or []}
    return seen


def test_codex_scope_shows_only_codex_spend_and_advice(store_app):
    app, _ = store_app
    body = _route(app, "?runtime=codex")
    assert body["runtime"] == "codex"
    assert body["scope"] == "Codex only, on this computer"
    assert _models(body) == {CODEX}
    assert CLAUDE not in json.dumps(body["taskRecommendations"])
    assert body["todayCost"] == pytest.approx(0.8)


def test_unscoped_view_still_covers_every_runtime(store_app):
    app, _ = store_app
    for qs in ("", "?runtime=all"):
        body = _route(app, qs)
        assert body["scope"] == "all runtimes on this computer"
        assert _models(body) == {CLAUDE, CODEX}
        assert body["todayCost"] == pytest.approx(6.8)


def test_runtime_with_no_spend_is_unknown_not_another_runtimes_figures(store_app, monkeypatch):
    app, _ = store_app
    import dashboard as _d
    # A populated interceptor ring must not leak into a runtime-scoped view.
    monkeypatch.setattr(_d, "metrics_store",
                        {"cost": [{"model": CLAUDE, "usd": 9.0, "timestamp": 1}]}, raising=False)
    body = _route(app, "?runtime=cursor")
    assert body["scope"] == "Cursor only, on this computer"
    assert body["todayCost"] is None and body["projectedMonthlyCost"] is None
    assert body["provenance"]["todayCost"]["basis"] == "unknown"
    assert body["expensiveOps"] == [] and body["taskRecommendations"] == []
    assert _models(body) == set()


def test_hosted_slice_per_runtime_matches_the_scoped_route(store_app):
    from clawmetry.cost_optimizer_snapshot import build_slice

    app, store = store_app
    local = _route(app, "?runtime=codex")
    hosted = build_slice(store, runtime="codex")
    for key in ("taskRecommendations", "localAdvice", "modelUsage", "recommendationsNote",
                "todayCost", "projectedMonthlyCost", "expensiveOps"):
        assert hosted[key] == local[key], key
    assert hosted["runtime"] == "codex"
    assert hosted["scope"] == "Codex only, on the connected computer"


def test_daemon_ships_a_slice_per_runtime(store_app):
    _, store = store_app
    import clawmetry.sync as sync
    from clawmetry.cost_optimizer_snapshot import build_slice

    by_rt = sync._build_cost_optimizer_by_runtime(["codex", "claude_code", "all", ""])
    assert set(by_rt) == {"codex", "claude_code"}
    assert by_rt["codex"] == build_slice(store, runtime="codex")
    assert _models(by_rt["claude_code"]) == {CLAUDE}

    tree = ast.parse((REPO / "clawmetry" / "sync.py").read_text(encoding="utf-8"))
    fn = next(n for n in ast.walk(tree)
              if isinstance(n, ast.FunctionDef) and n.name == "sync_system_snapshot")
    shipped = {
        k.value for node in ast.walk(fn)
        if isinstance(node, ast.Dict) for k in node.keys
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    }
    assert "costOptimizerByRuntime" in shipped


def test_dashboard_passes_the_selected_runtime():
    js = (REPO / "clawmetry" / "static" / "js" / "app.js").read_text(encoding="utf-8")
    start = js.index("function loadCostOptimizerData(")
    body = js[start:js.index("\n}\n", start)]
    assert "_cmRuntimeFilter()" in body
    assert "'/api/cost-optimizer' + " in body and "?runtime=" in body
