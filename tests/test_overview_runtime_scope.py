"""The Home (Overview) tab follows the runtime switcher, card by card.

Burned 2026-09-15 on the hosted dashboard with Codex selected: System Health
still listed OpenClaw's "Gateway :18789" (the snapshot names it a bare
"Gateway", which the OpenClaw-name filter missed), Run Health drew a
``claude_code`` row, and the 30-day activity, "How independent is your agent?",
Anomaly Detection, Reliability and session-quality cards all counted every
runtime on the node. The snapshot's Run Health slice had no Codex row at all,
because the newest 60 sessions on that node were all Claude Code.
"""
from __future__ import annotations

import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

import pytest
from flask import Flask

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO not in sys.path:
    sys.path.insert(0, _REPO)

_APP_JS = os.path.join(_REPO, "clawmetry", "static", "js", "app.js")


def _src(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _function_body(src, header):
    start = src.index(header)
    nxt = re.search(r"\n(?:async )?function ", src[start + len(header):])
    return src[start: start + len(header) + (nxt.start() if nxt else len(src))]


def _fake_waste_flags(monkeypatch):
    from clawmetry import waste_flags as wf

    monkeypatch.setattr(wf, "runtime_from_session_id",
                        lambda sid: str(sid).split(":", 1)[0] if ":" in str(sid) else "openclaw")
    monkeypatch.setattr(wf, "compute_signals_from_events", lambda events: {})
    monkeypatch.setattr(wf, "compute_flags", lambda signals: [])
    monkeypatch.setattr(wf, "event_is_real_error", lambda e: False)
    monkeypatch.setattr(wf, "severity_from_counts", lambda errors, flags: "green")


# ── /api/activity-heatmap ────────────────────────────────────────────────────


@pytest.fixture
def overview_client(monkeypatch):
    import routes.overview as ov

    today = datetime.now().strftime("%Y-%m-%dT10:00:00")
    rows = [
        {"session_id": "codex:1", "started_at": today, "token_count": 10, "cost_usd": 0.1},
        {"session_id": "claude_code:2", "started_at": today, "token_count": 20, "cost_usd": 0.2},
        {"session_id": "0b8f2c1e-openclaw", "started_at": today, "token_count": 30, "cost_usd": 0.3},
    ]
    monkeypatch.setattr(ov, "_ls_call", lambda method, **kw: list(rows))
    app = Flask(__name__)
    app.register_blueprint(ov.bp_overview)
    return app.test_client()


def _heatmap_totals(body):
    return (sum(d["sessions"] for d in body["days"]), sum(d["tokens"] for d in body["days"]))


def test_heatmap_counts_only_the_selected_runtime(overview_client):
    body = overview_client.get("/api/activity-heatmap?runtime=codex").get_json()
    assert body["runtime"] == "codex"
    assert _heatmap_totals(body) == (1, 10)


def test_heatmap_without_a_runtime_counts_every_runtime(overview_client):
    body = overview_client.get("/api/activity-heatmap").get_json()
    assert body["runtime"] == "all"
    assert _heatmap_totals(body) == (3, 60)


def test_heatmap_nemoclaw_counts_openclaw_adapter_sessions(overview_client):
    body = overview_client.get("/api/activity-heatmap?runtime=nemoclaw").get_json()
    assert _heatmap_totals(body) == (1, 30)


# ── /api/health-timeline ─────────────────────────────────────────────────────


def test_health_timeline_route_keeps_only_the_selected_runtime(monkeypatch):
    import routes.local_query as lq
    import routes.overview as ov

    _fake_waste_flags(monkeypatch)
    calls = []

    def fake_proxy(method, **kw):
        calls.append((method, kw))
        if method == "query_sessions":
            # The loud runtime owns the newest rows, the quiet one is older.
            return [{"session_id": f"claude_code:{i}", "started_at": f"2026-09-15T10:{i:02d}"}
                    for i in range(8)] + [{"session_id": "codex:a", "started_at": "2026-09-14T09:00"}]
        return []

    monkeypatch.setattr(lq, "local_store_via_daemon", fake_proxy)
    ov._health_timeline_cache.update(ts=0.0, value=None, key=None)
    app = Flask(__name__)
    app.register_blueprint(ov.bp_overview)
    body = app.test_client().get("/api/health-timeline?runtime=codex&session_limit=2").get_json()
    assert [r["runtime"] for r in body["runtimes"]] == ["codex"]
    assert body["runtime"] == "codex"
    # It read past the node's newest two sessions to find this runtime's.
    assert ("query_sessions", {"limit": 20}) in calls


# ── daemon snapshot: every runtime gets a Run Health row ─────────────────────


class _TimelineStore:
    def __init__(self):
        self.event_reads = 0

    def query_sessions(self, limit=60):
        return [{"session_id": f"claude_code:{i}", "started_at": f"2026-09-15T10:{i:02d}:00",
                 "cost_usd": 0.1} for i in range(limit)]

    def query_recent_sessions_by_runtime(self, per_runtime=2, max_runtimes=40):
        return [{"runtime": "codex", "session_id": "codex:old", "last_ms": 1},
                {"runtime": "claude_code", "session_id": "claude_code:0", "last_ms": 2}]

    def query_events(self, session_id=None, limit=500):
        self.event_reads += 1
        if session_id == "codex:old":
            return [{"ts": "2026-09-01T09:05:00", "cost_usd": 0.5},
                    {"ts": "2026-09-01T09:00:00", "cost_usd": 0.25}]
        return []


def test_snapshot_timeline_includes_a_quiet_runtime(monkeypatch):
    from clawmetry import local_store as ls
    from clawmetry import sync

    _fake_waste_flags(monkeypatch)
    store = _TimelineStore()
    monkeypatch.setattr(ls, "get_store", lambda *a, **k: store)
    sync._health_timeline_memo.update(ts=0.0, key=None, value=None)

    out = sync._build_health_timeline(session_limit=5)
    rows = {r["runtime"]: r["dots"] for r in out["runtimes"]}
    assert set(rows) == {"claude_code", "codex"}
    # claude_code:0 came back from both queries and is drawn once.
    assert len(rows["claude_code"]) == 5
    (dot,) = rows["codex"]
    assert dot["started_at"] == "2026-09-01T09:00:00"
    assert dot["cost_usd"] == pytest.approx(0.75)

    reads = store.event_reads
    sync._build_health_timeline(session_limit=5)
    assert store.event_reads == reads, "a second cycle inside the TTL re-read every session"


def test_autonomy_by_runtime_is_reused_within_its_ttl(monkeypatch):
    from clawmetry import sync

    calls = []
    monkeypatch.setattr(sync, "_build_autonomy_snapshot",
                        lambda runtime=None: calls.append(runtime) or {"score": 0.5, "runtime": runtime})
    sync._autonomy_by_rt_memo.update(ts=0.0, keys=None, value={})

    out = sync._build_autonomy_by_runtime(["codex", "claude_code"])
    assert set(out) == {"codex", "claude_code"}
    assert out["codex"]["runtime"] == "codex"
    sync._build_autonomy_by_runtime(["claude_code", "codex"])
    assert sorted(calls) == ["claude_code", "codex"]
    sync._build_autonomy_by_runtime(["codex"])
    assert calls[-1] == "codex" and len(calls) == 3


# ── /api/autonomy?runtime= ───────────────────────────────────────────────────


@pytest.fixture
def autonomy_app(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(tmp_path / "events.duckdb"))
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_SECS", "0.05")
    monkeypatch.setenv("CLAWMETRY_LOCAL_FLUSH_BATCH", "1")
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_READ", "1")
    import clawmetry.local_store as ls
    importlib.reload(ls)
    import routes.local_query as lq
    importlib.reload(lq)
    monkeypatch.setattr(lq, "local_store_via_daemon", lambda *a, **k: None)
    monkeypatch.setattr(lq, "_read_discovery", lambda: None)
    monkeypatch.setattr(lq, "_cached_discovery", lambda: None)
    import routes.autonomy as aut
    importlib.reload(aut)
    a = Flask(__name__)
    a.register_blueprint(aut.bp_autonomy)
    yield a, ls
    try:
        ls.get_store().stop(flush=True)
    except Exception:
        pass


def _ingest_user_turn(store, eid, sid, ts):
    store.ingest({
        "id": eid, "node_id": "agent+test", "agent_id": "main", "session_id": sid,
        "event_type": "user", "ts": datetime.fromtimestamp(ts, tz=timezone.utc).isoformat(),
        "data": {"message": {"role": "user", "content": eid}},
        "cost_usd": None, "token_count": None, "model": None,
    })


def _wait_flush(store, t=2.0):
    deadline = time.monotonic() + t
    while time.monotonic() < deadline:
        if store.health()["ring_depth"] == 0:
            return
        time.sleep(0.02)


def test_autonomy_counts_only_the_selected_runtimes_turns(autonomy_app):
    app, ls = autonomy_app
    store = ls.get_store()
    now = time.time()
    _ingest_user_turn(store, "cx-1", "codex:s1", now - 900)
    _ingest_user_turn(store, "cx-2", "codex:s1", now - 600)
    for i in range(3):
        _ingest_user_turn(store, f"cc-{i}", f"claude_code:s{i}", now - 1200 - i * 60)
    _wait_flush(store)
    client = app.test_client()
    assert client.get("/api/autonomy").get_json()["samples_7d"] == 5
    codex = client.get("/api/autonomy?runtime=codex").get_json()
    assert codex["runtime"] == "codex"
    assert codex["samples_7d"] == 2


def test_autonomy_for_a_runtime_with_no_turns_is_empty_not_node_wide(autonomy_app):
    app, ls = autonomy_app
    store = ls.get_store()
    _ingest_user_turn(store, "cc-1", "claude_code:s1", time.time() - 600)
    _wait_flush(store)
    body = app.test_client().get("/api/autonomy?runtime=cursor").get_json()
    assert body["score"] is None
    assert body["samples_7d"] == 0
    assert body["runtime"] == "cursor"


# ── /api/evals/summary?runtime= ──────────────────────────────────────────────


def test_eval_summary_scopes_to_the_runtime(tmp_path, monkeypatch):
    db_path = tmp_path / "clawmetry.duckdb"
    monkeypatch.setenv("CLAWMETRY_LOCAL_STORE_PATH", str(db_path))
    from clawmetry import local_store
    monkeypatch.setattr(local_store, "DB_PATH", db_path)
    monkeypatch.setattr(local_store, "_STORE", None, raising=False)
    store = local_store.LocalStore()
    now_iso = datetime.now(timezone.utc).isoformat()
    with store._write_lock:
        for sid in ("codex:a", "claude_code:b", "c0ffee-openclaw"):
            store._conn.execute(
                """
                INSERT INTO sessions
                  (agent_type, session_id, node_id, agent_id, started_at,
                   last_active_at, ended_at, status, total_tokens, updated_at)
                VALUES ('openclaw', ?, 'node-x', 'main', ?, ?, ?, 'completed', 1, ?)
                """,
                [sid, now_iso, now_iso, now_iso, int(time.time() * 1000)],
            )
    for sid, score in (("codex:a", 5.0), ("claude_code:b", 1.0), ("c0ffee-openclaw", 3.0)):
        store.persist_eval_score(session_id=sid, score=score, reason="r", judge_model="m",
                                 scored_at=1, rubric="default")
    assert store.query_eval_summary(window_hours=24)["scored"] == 3
    codex = store.query_eval_summary(window_hours=24, runtime="codex")
    assert (codex["scored"], codex["total"], codex["avg_score"]) == (1, 1, 5.0)
    assert store.query_eval_summary(window_hours=24, runtime="openclaw")["avg_score"] == 3.0
    assert store.query_eval_summary(window_hours=24, runtime="nemoclaw")["avg_score"] == 3.0
    assert store.query_eval_summary(window_hours=24, runtime="cursor")["total"] == 0


def test_eval_summary_route_passes_and_echoes_the_runtime(monkeypatch):
    import routes.evals as ev

    seen = {}

    def fake(method, **kw):
        seen.update(kw)
        return {"avg_score": 4.0, "total": 1, "scored": 1, "p50": 4.0, "p10": 4.0, "window_hours": 24}

    monkeypatch.setattr(ev, "_store_via_daemon_or_direct", fake)
    app = Flask(__name__)
    app.register_blueprint(ev.bp_evals)
    body = app.test_client().get("/api/evals/summary?window=24h&runtime=codex").get_json()
    assert seen.get("runtime") == "codex"
    assert body["runtime"] == "codex"
    seen.clear()
    body = app.test_client().get("/api/evals/summary?window=24h").get_json()
    assert "runtime" not in seen
    assert body["runtime"] == "all"


# ── frontend ─────────────────────────────────────────────────────────────────


def test_system_health_drops_the_hosted_gateway_pill_off_openclaw():
    body = _function_body(_src(_APP_JS), "async function loadSystemHealth()")
    seg = body[body.index("var services = "):body.index("var channels = ")]
    assert "/^gateway$/i" in seg
    assert "18789" in seg


def test_cards_ask_for_the_selected_runtime():
    src = _src(_APP_JS)
    heat = _function_body(src, "async function loadActivityHeatmap()")
    assert "'/api/activity-heatmap' + q" in heat
    assert "data.runtime !== rt" in heat
    auto = _function_body(src, "async function loadAutonomy()")
    assert "fetchJsonWithTimeout(_auUrl, 5000)" in auto
    ev = _function_body(src, "async function loadEvalSummary()")
    assert "'/api/evals/summary?window=24h' + _evQ" in ev
    assert "data.runtime !== _evRt" in ev


def test_anomaly_panel_keeps_only_the_runtimes_sessions():
    body = _function_body(_src(_APP_JS), "async function loadAnomalyPanel()")
    scope = body[body.index("var _anScoped"):body.index("var active = ")]
    assert "_cmRuntimeOf({session_id: sk}) === _anRt" in scope
    assert "baselines = {};" in scope


def test_reliability_card_is_hidden_under_a_runtime():
    body = _function_body(_src(_APP_JS), "async function loadReliabilityCard()")
    assert "_relCard.style.display = _relScoped ? 'none' : ''" in body
    assert body.index("if (_relScoped) return;") < body.index("/api/reliability")


def test_runtime_switch_is_not_swallowed_by_the_loadall_coalesce():
    body = _function_body(_src(_APP_JS), "function _cmApplyRuntimeSelection(val)")
    assert body.index("_loadAllLastFinishedMs = 0") < body.index("switchTab(_cmCurrentTab)")


@pytest.mark.skipif(not shutil.which("node"), reason="node not installed")
def test_run_health_renders_only_the_selected_runtime_under_node():
    fn = _function_body(_src(_APP_JS), "async function loadHealthTimeline()")
    script = fn + """
var CURRENT, URL;
function _cmRuntimeFilter() { return CURRENT; }
function escapeHtmlSafe(s) { return String(s); }
var els;
var document = { getElementById: function (id) { return els[id]; } };
function fetch(url) {
  URL = url;
  var rows = [{runtime: 'claude_code', dots: [{severity: 'red'}]},
              {runtime: 'codex', dots: [{severity: 'green'}]},
              {runtime: 'openclaw', dots: [{severity: 'green'}]}];
  return Promise.resolve({ok: true, json: function () { return Promise.resolve({runtimes: rows}); }});
}
(async function () {
  var out = {};
  for (var rt of ['codex', 'cursor', 'nemoclaw', 'all']) {
    CURRENT = rt;
    els = {'health-timeline-card': {style: {display: 'none'}}, 'health-timeline-body': {innerHTML: ''}};
    await loadHealthTimeline();
    out[rt] = {url: URL, shown: els['health-timeline-card'].style.display !== 'none',
               html: els['health-timeline-body'].innerHTML};
  }
  console.log(JSON.stringify(out));
})();
"""
    res = subprocess.run(["node", "-e", script], capture_output=True, text=True, timeout=30)
    assert res.returncode == 0, res.stderr
    out = json.loads(res.stdout)
    assert out["codex"]["url"] == "/api/health-timeline?runtime=codex"
    assert out["codex"]["shown"] and "codex" in out["codex"]["html"]
    assert "claude_code" not in out["codex"]["html"]
    assert not out["cursor"]["shown"]
    assert "openclaw" in out["nemoclaw"]["html"] and "claude_code" not in out["nemoclaw"]["html"]
    assert out["all"]["url"] == "/api/health-timeline"
    assert "claude_code" in out["all"]["html"] and "codex" in out["all"]["html"]
