import json
from pathlib import Path
import re
import subprocess

from flask import Flask
import pytest

from routes import context_economics


def _client(monkeypatch, payload):
    monkeypatch.setattr(context_economics, "_ls_call", lambda *args, **kwargs: payload)
    app = Flask(__name__)
    app.register_blueprint(context_economics.bp_context_economics)
    return app.test_client()


def test_unmeasured_compaction_is_not_reported_as_zero(monkeypatch):
    client = _client(monkeypatch, {
        "utilization": [],
        "compactions": [{
            "session_id": "s1",
            "trigger": "proactive",
            "tokens_before": None,
            "tokens_after": None,
            "reclaimed": None,
            "measurement_status": "unavailable",
        }],
        "overflow_sessions": [],
    })

    response = client.get("/api/context-economics")
    body = response.get_json()

    assert response.status_code == 200
    assert body["compactions"][0]["measurement_status"] == "unavailable"
    assert body["compactions"][0]["reclaimed"] is None
    assert body["summary"]["reclaimed_data_available"] is False
    assert body["summary"]["peak_pct"] is None


def test_reclaimed_summary_uses_only_observed_measurements(monkeypatch):
    client = _client(monkeypatch, {
        "utilization": [],
        "compactions": [
            {"session_id": "s1", "trigger": "proactive", "reclaimed": 120,
             "measurement_status": "observed"},
            {"session_id": "s2", "trigger": "proactive", "reclaimed": None,
             "measurement_status": "unavailable"},
        ],
        "overflow_sessions": [],
    })

    body = client.get("/api/context-economics").get_json()

    assert body["summary"]["total_reclaimed"] == 120
    assert body["summary"]["reclaimed_known_count"] == 1
    assert body["summary"]["reclaimed_data_available"] is True


@pytest.mark.parametrize("scope,utilization,compactions,peak,reclaimed", [
    (None, [], [], "Not measured", "Not measured"),
    (None, [{"pct": 0}], [{"measurement_status": "observed", "reclaimed": 0}], "0%", "0"),
    (None, [{"pct": 25.5}], [
        {"measurement_status": "observed", "reclaimed": 120},
        {"measurement_status": "unavailable", "reclaimed": 999},
    ], "25.5%", "120"),
    ("s2", [{"session_id": "s1", "pct": 90}], [
        {"session_id": "s1", "measurement_status": "observed", "reclaimed": 120},
        {"session_id": "s2", "measurement_status": "unavailable", "reclaimed": None},
    ], "Not measured", "Not measured"),
])
def test_rendered_context_summary_preserves_measurement_and_session_scope(
    scope, utilization, compactions, peak, reclaimed
):
    app_js = (Path(__file__).resolve().parents[1] / "clawmetry/static/js/app.js").read_text()
    source = re.search(r"^async function loadContextEconomics\b[\s\S]*?^\}", app_js, re.M).group()
    body = """
const vm = require('vm');
const els = {'ce-gauge-panel': {}, 'ce-summary': {}};
const ctx = {
  document: {getElementById: id => els[id] || null},
  fetch: async () => ({json: async () => (__DATA__)}),
  _ceSessionId: __SCOPE__, _ceCompactionsCache: [],
  escHtml: String, _ceFmtTokens: String, _ceShortSid: String,
  t: (key, vars, fallback) => fallback
};
vm.createContext(ctx);
vm.runInContext(__SOURCE__, ctx);
ctx.loadContextEconomics().then(() => console.log(JSON.stringify(els['ce-summary'].innerHTML)));
"""
    values = {"DATA": {"utilization": utilization, "compactions": compactions},
              "SCOPE": scope, "SOURCE": source}
    body = re.sub(r"__(DATA|SCOPE|SOURCE)__", lambda m: json.dumps(values[m[1]]), body)
    result = subprocess.run(["node", "-"], input=body, text=True, capture_output=True, timeout=15)
    assert result.returncode == 0, result.stderr
    html = json.loads(result.stdout)
    for label, expected in (("Peak window", peak), ("Tokens reclaimed", reclaimed)):
        value = re.search(re.escape(label) + r"</div><div[^>]*>([^<]+)</div>", html).group(1)
        assert value == expected, (label, value)
