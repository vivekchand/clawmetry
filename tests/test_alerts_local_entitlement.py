"""Alerts must function on a self-hosted entitlement without any cloud signup
(founder 2026-07-28: "it should work in the self-hosted setup as well").

Guards the two halves: the local rules route accepts the Alerts tab's cloud
vocabulary, and the tab's tier resolution consults the local entitlement
before demanding a cloud account."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_local_rules_route_accepts_cloud_vocabulary(monkeypatch):
    import dashboard as _d
    from flask import Flask

    from routes.alerts import bp_alerts

    app = Flask(__name__)
    app.register_blueprint(bp_alerts)

    writes = []

    class _Db:
        def execute(self, q, params=()):
            writes.append((q, params))

            class _R:
                def fetchall(self):
                    return []

                def fetchone(self):
                    return None
            return _R()

        def commit(self):
            pass

        def close(self):
            pass

    import threading
    monkeypatch.setattr(_d, "_fleet_db_lock", threading.Lock(), raising=False)
    monkeypatch.setattr(_d, "_fleet_db", lambda: _Db(), raising=False)

    r = app.test_client().post("/api/alerts/rules", json={
        "alert_type": "cost_daily", "name": "Daily spend",
        "threshold_value": 50, "enabled": True, "channel_ids": [],
    })
    assert r.status_code == 200, r.get_json()
    assert r.get_json().get("ok") is True
    ins = [w for w in writes if "INSERT INTO alert_rules" in w[0]]
    assert ins, "cloud-vocabulary rule must be stored locally"
    assert ins[0][1][1] == "threshold", "cost_daily maps to the local threshold type"
    assert ins[0][1][2] == 50


def _js(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
        return fh.read()


def test_alerts_js_resolves_local_entitlement_first():
    src = _js("clawmetry/static/js/alerts.js")
    assert "fetch('/api/entitlement')" in src, \
        "resolveTier must consult the LOCAL entitlement before the cloud"
    assert "alertsState.localMode = true" in src
    assert "'/api/alerts/rules'" in src, \
        "local mode must read and write the LOCAL rules routes"
